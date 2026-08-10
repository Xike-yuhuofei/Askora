"""EXEC-024 fixed EPUB release gate through the real Book-to-Learning owners."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models  # noqa: F401
from app.application.book_learning import BookLearningApplication
from app.contracts.activity_lifecycle import StartLearningActivityV1
from app.contracts.adaptive import TeachingContextV03
from app.contracts.assessment import AssessmentItemV1, AssistanceSnapshot
from app.core.database import Base
from app.domains.content_knowledge import CONTENT_RECORD_KEY
from app.domains.content_knowledge.publication import replay_persisted_knowledge_publication
from app.domains.teaching_policy import TeachingPolicyKernel
from app.infrastructure.adaptive_records import AdaptiveContractRepository
from app.models.adaptive import TeachingContextRecord
from app.models.assessment import AssessmentItem
from app.models.ledger import LearningEventRecord
from app.models.user import User, UserRole, UserStatus
from app.services.activity_lifecycle import ActivityLifecycleService
from app.services.assessment.canonical_service import CanonicalAssessmentService
from app.services.assessment.diagnostic_bootstrap import PrerequisiteDiagnosticService
from app.services.documents.document_service import DocumentService
from app.services.kt.canonical_projector import CanonicalLearnerProjectorService
from app.services.llm.model_router import ModelRouter
from app.services.policy_runtime import (
    default_policy_activation,
    default_policy_bundle,
    load_policy_runtime_profile,
)
from app.services.storage.local_storage import LocalFileStorage
from tests.fixtures.minimal_epub import book_to_learning_epub

NOW = datetime(2026, 8, 8, 23, 30, tzinfo=timezone.utc)


@pytest.fixture
async def book_e2e_db(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'book-e2e.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session, tmp_path
    await engine.dispose()


def _independent() -> AssistanceSnapshot:
    return AssistanceSnapshot(
        hint_level=0,
        assistance_class="none",
        source_visible=False,
        answer_visible=False,
        response_revision=1,
        response_time_ms=1_000,
    )


@pytest.mark.asyncio
async def test_exec024_fixed_epub_closes_to_second_canonical_teaching_action(
    book_e2e_db,
    monkeypatch,
) -> None:
    """D06-AC-001..010 / G0..G6 without model, truth, or tutor shortcuts."""

    async def forbid_online_model(*_args, **_kwargs):
        raise AssertionError("EXEC024_REPLAY_OR_BOOTSTRAP_MUST_NOT_CALL_ONLINE_MODEL")

    monkeypatch.setattr(ModelRouter, "chat_completion_with_fallback", forbid_online_model)
    db, tmp_path = book_e2e_db
    user = User(
        id=str(uuid4()),
        pseudonym_id="exec024-fixed-epub",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    await db.commit()
    documents = DocumentService(db)
    documents.storage = LocalFileStorage(str(tmp_path / "documents"))
    document = await documents.upload_document(
        user.pseudonym_id,
        "askora-structured-learning.epub",
        book_to_learning_epub(),
    )
    await documents.process_document(document.id)
    await db.refresh(document)
    record = document.moderation_details[CONTENT_RECORD_KEY]
    revision = record["revisions"][0]

    # G1: the production process retains structure, replayable anchors, published
    # knowledge/relation, and rebuildable retrieval projection inputs.
    assert revision["document_ir"]["structure_hash"]
    assert len(revision["document_ir"]["node_ids"]) >= 2
    assert len(revision["semantic_units"]) >= 2
    published_units = {
        item["canonical_name"]: item
        for item in revision["knowledge_units"]
        if item["status"] == "published"
    }
    assert {"Foundations", "Replay"} <= set(published_units)
    relation = next(
        item
        for item in revision["relations"]
        if item["prerequisite_id"] == published_units["Foundations"]["knowledge_unit_id"]
        and item["target_knowledge_unit_id"] == published_units["Replay"]["knowledge_unit_id"]
    )
    assert relation["strength"] == "hard"
    assert relation["status"] == "published"
    target_span = next(
        item for item in revision["source_spans"] if "prerequisite for Replay" in item["text"]
    )
    replayed_span = await documents.replay_source_span(document.id, target_span["span_id"])
    assert replayed_span is not None
    assert replayed_span.status == "EXACT"
    publication_replay = replay_persisted_knowledge_publication(revision)
    assert publication_replay["knowledge_units"] == revision["knowledge_units"]
    assert publication_replay["relations"] == revision["relations"]
    await documents.process_document(document.id)
    await db.refresh(document)
    assert len(document.moderation_details[CONTENT_RECORD_KEY]["revisions"]) == 1

    policy_records = AdaptiveContractRepository(db)
    await policy_records.publish_policy_bundle(default_policy_bundle())
    await policy_records.activate_policy_bundle(default_policy_activation())
    app = BookLearningApplication(db)
    correlation_id = uuid4()

    # G2: the learner supplies natural language only; SYS06 derives exact mapping
    # and subgraph refs, then SYS04/SYS03 resolve the unknown prerequisite.
    created = await app.create_goal_candidate(
        user=user,
        document_id=UUID(document.id),
        intent="我想掌握 Replay，并能解释它为什么必须验证 source locator",
        weekly_time_budget_minutes=60,
        idempotency_key="exec024:goal:create",
        correlation_id=correlation_id,
        now=NOW,
    )
    goal_id = UUID(created.payload["goal"]["goal_id"])
    await app.confirm_goal(
        user=user,
        goal_id=goal_id,
        confirmed_by_user=True,
        idempotency_key="exec024:goal:confirm",
        correlation_id=correlation_id,
        now=NOW,
    )
    mapped = await app.map_goal(
        user=user,
        goal_id=goal_id,
        idempotency_key="exec024:goal:map",
        correlation_id=correlation_id,
        now=NOW,
    )
    duplicate_mapping = await app.map_goal(
        user=user,
        goal_id=goal_id,
        idempotency_key="exec024:goal:map",
        correlation_id=correlation_id,
        now=NOW,
    )
    assert duplicate_mapping.payload == mapped.payload
    mapping = mapped.payload["mapping"]
    subgraph = mapped.payload["subgraph"]
    target_id = UUID(published_units["Replay"]["knowledge_unit_id"])
    prerequisite_id = UUID(published_units["Foundations"]["knowledge_unit_id"])
    assert str(target_id) in mapping["selected_target_ids"]
    assert str(prerequisite_id) in subgraph["included_prerequisite_ids"]

    diagnostic_item_id = uuid5(NAMESPACE_URL, "askora:exec024:foundations-item")
    db.add(
        AssessmentItem(
            id=str(diagnostic_item_id),
            knowledge_point_id=str(prerequisite_id),
            subject="book",
            item_type="fill_blank",
            difficulty=3,
            grade_level=0,
            question_text="Type foundations",
            options=[],
            correct_answer="foundations",
            explanation="grader-only exact answer",
            cognitive_level="apply",
            common_misconceptions=[],
            is_active=True,
            version="1.0",
        )
    )
    await db.flush()
    started = await app.start_diagnostic(
        user=user,
        mapping_id=UUID(mapping["mapping_id"]),
        mapping_version=mapping["mapping_version"],
        subgraph_id=UUID(subgraph["subgraph_id"]),
        subgraph_version=subgraph["version"],
        target_knowledge_unit_id=target_id,
        max_attempts=3,
        idempotency_key="exec024:diagnostic:start",
        correlation_id=correlation_id,
        now=NOW,
    )
    need = started.payload["need"]
    diagnosed = await app.submit_diagnostic_response(
        user=user,
        need_id=UUID(need["need_id"]),
        expected_need_version=need["version"],
        response="foundations",
        assistance=_independent(),
        idempotency_key="exec024:diagnostic:answer",
        correlation_id=correlation_id,
        now=NOW,
    )
    assert diagnosed.payload["assessment_result"]["correctness"] == "correct"
    assert diagnosed.payload["learner_state"]["mastery_estimate_refs"]
    diagnostic_replay = await PrerequisiteDiagnosticService(
        db,
        learner_projector=CanonicalLearnerProjectorService(db),
    ).replay_need(
        user=user,
        need_id=UUID(diagnosed.payload["need"]["need_id"]),
        version=diagnosed.payload["need"]["version"],
    )
    assert diagnostic_replay.model_dump(mode="json") == diagnosed.payload["need"]

    # G3: existing planner consumes only the published scope and emits a real activity.
    planned = await app.generate_plan(
        user=user,
        need_id=UUID(diagnosed.payload["need"]["need_id"]),
        idempotency_key="exec024:plan:generate",
        correlation_id=correlation_id,
        now=NOW,
    )
    selected = await app.select_next_activity(
        user=user,
        goal_id=goal_id,
        idempotency_key="exec024:activity:select",
        correlation_id=correlation_id,
        now=NOW,
    )
    plan = planned.payload["plan"]
    activity = selected.payload["activity"]
    published_ids = {
        UUID(item["knowledge_unit_id"])
        for item in revision["knowledge_units"]
        if item["status"] == "published" and item["evidence_span_ids"]
    }
    assert {UUID(item) for item in activity["knowledge_unit_ids"]} <= published_ids
    assert plan["knowledge_graph_version"] == ",".join(mapping["knowledge_graph_versions"])

    # G4: first and second turns share the existing SYS05/SYS02/SYS08 path.
    lifecycle = await ActivityLifecycleService(db).get(
        user=user,
        activity_id=UUID(activity["activity_id"]),
        correlation_id=correlation_id,
    )
    await ActivityLifecycleService(db).start(
        user=user,
        command=StartLearningActivityV1(
            activity_id=UUID(activity["activity_id"]),
            expected_state_version=lifecycle.data.state.version,
            idempotency_key="exec024:activity:start",
        ),
        correlation_id=correlation_id,
        now=NOW,
    )
    session_id = uuid4()
    first = await app.start_teaching_round(
        user=user,
        goal_id=goal_id,
        plan_id=UUID(plan["plan_id"]),
        plan_version=plan["version"],
        activity_id=UUID(activity["activity_id"]),
        session_id=session_id,
        turn_id="exec024-turn-1",
        learner_text="请先帮助我理解 Replay。",
        idempotency_key="exec024:teaching:first",
        correlation_id=correlation_id,
        now=NOW,
    )
    assert first.evidence_bundle.items
    assert all(item.allowed_use != "grader_only" for item in first.evidence_bundle.items)
    assistance_event = await db.scalar(
        select(LearningEventRecord).where(
            LearningEventRecord.event_type == "ActualAssistanceRecorded",
            LearningEventRecord.aggregate_id == str(first.teaching_action.action_id),
        )
    )
    assert assistance_event is not None
    assert assistance_event.producer_system == "SYS08"

    # A fresh no-hint formative Attempt is recorded by SYS04, then only SYS03
    # projects the resulting evidence into a new canonical MasteryEstimate.
    activity_knowledge_id = UUID(activity["knowledge_unit_ids"][0])
    formative_item = AssessmentItemV1(
        item_id=uuid5(NAMESPACE_URL, "askora:exec024:formative-replay"),
        version="1.0",
        knowledge_unit_id=activity_knowledge_id,
        item_type="exact",
        prompt="Type replay",
        answer_key="replay",
        difficulty=0.3,
    )
    scored = await CanonicalAssessmentService(db).score_submission_with_attempt(
        item=formative_item,
        user_id=UUID(user.id),
        response="replay",
        assistance=_independent(),
        idempotency_key="exec024:formative:first",
        correlation_id=str(correlation_id),
    )
    estimate = await CanonicalLearnerProjectorService(db).project_assessment(
        attempt=scored.attempt,
        result=scored.result,
        knowledge_unit_id=activity_knowledge_id,
        source_event_ids=[UUID(assistance_event.event_id)],
        dimension="routine_application",
        novelty="near_variant",
        item_difficulty=formative_item.difficulty,
        correlation_id=str(correlation_id),
    )
    assert estimate is not None
    assert estimate.source_evidence_ids

    second = await app.start_teaching_round(
        user=user,
        goal_id=goal_id,
        plan_id=UUID(plan["plan_id"]),
        plan_version=plan["version"],
        activity_id=UUID(activity["activity_id"]),
        session_id=session_id,
        turn_id="exec024-turn-2",
        learner_text="我完成了独立检查，请继续。",
        idempotency_key="exec024:teaching:second",
        correlation_id=correlation_id,
        now=NOW,
    )
    assert second.teaching_action.action_id != first.teaching_action.action_id
    assert second.teaching_action.teaching_context_ref != first.teaching_action.teaching_context_ref
    # Production HOLD: the second canonical decision goes through the
    # SequentialTeachingPolicy (BookLearningApplication -> facade). The held
    # decision still emits a fresh immutable TeachingAction/DecisionTrace envelope
    # with a complete anti-oscillation payload and the exact previous action ref.
    second_trace = second.decision_trace_v03
    assert second_trace is not None
    assert second_trace.previous_teaching_action_ref is not None
    assert second_trace.previous_teaching_action_ref.entity_id == str(
        first.teaching_action.action_id
    )
    assert second_trace.behavior_policy_type == "DETERMINISTIC"
    second_anti = second_trace.anti_oscillation_decision
    assert second_anti is not None
    # The fresh correct assessment passes minimum dwell (>=2 material
    # opportunities), but the kernel still proposes the same legal candidate, so
    # anti-oscillation correctly HOLDS rather than oscillating.
    assert second_anti["decision"] == "HOLD"
    assert second_anti["reason_code"] == "HOLD_SAME_LEGAL_CANDIDATE"
    assert second_anti["evidence_opportunities_since_transition"] >= 2
    assert second_trace.material_evidence_refs is not None
    assert len(second_trace.material_evidence_refs) >= 2
    second_context = await db.get(
        TeachingContextRecord,
        second.teaching_action.teaching_context_ref.entity_id,
    )
    assert second_context is not None
    context_source_ids = {item["entity_id"] for item in second_context.payload["source_refs"]}
    assert str(estimate.estimate_id) in context_source_ids

    # A further production turn after the HOLD: with the same canonical evidence
    # already observed, no new material opportunity appears and the policy must
    # continue to hold deterministically (no direct-kernel second+ bypass).
    third = await app.start_teaching_round(
        user=user,
        goal_id=goal_id,
        plan_id=UUID(plan["plan_id"]),
        plan_version=plan["version"],
        activity_id=UUID(activity["activity_id"]),
        session_id=session_id,
        turn_id="exec024-turn-3",
        learner_text="请继续。",
        idempotency_key="exec024:teaching:third",
        correlation_id=correlation_id,
        now=NOW,
    )
    third_trace = third.decision_trace_v03
    assert third_trace is not None
    assert third_trace.previous_teaching_action_ref is not None
    assert third_trace.previous_teaching_action_ref.entity_id == str(
        second.teaching_action.action_id
    )
    third_anti = third_trace.anti_oscillation_decision
    assert third_anti is not None
    assert third_anti["decision"] == "HOLD"
    assert str(third_anti["reason_code"]).startswith("HOLD_")

    # Replay uses pinned exact context/bundle/profile and remains deterministic
    # while the online model entry is patched to fail.
    first_context_record = await db.get(
        TeachingContextRecord,
        first.teaching_action.teaching_context_ref.entity_id,
    )
    assert first_context_record is not None
    replayed_policy = TeachingPolicyKernel().decide(
        context=TeachingContextV03.model_validate(first_context_record.payload),
        bundle=default_policy_bundle(),
        profile=load_policy_runtime_profile(),
    )
    assert replayed_policy.action == first.teaching_action
    assert {item.owner_system for item in second.owner_refs} >= {
        "SYS02",
        "SYS05",
        "SYS06",
        "SYS08",
    }

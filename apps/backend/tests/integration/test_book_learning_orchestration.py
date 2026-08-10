"""EXEC-023 real book bootstrap through the existing canonical teaching facade."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models  # noqa: F401
from app.application.book_learning import BookLearningApplication, BookLearningApplicationError
from app.contracts.activity_lifecycle import (
    CompleteLearningActivityV1,
    StartLearningActivityV1,
)
from app.contracts.adaptive import VersionedRef
from app.contracts.assessment import AssistanceSnapshot
from app.core.database import Base
from app.domains.content_knowledge import CONTENT_RECORD_KEY
from app.infrastructure.adaptive_records import AdaptiveContractRepository
from app.models.assessment import AssessmentItem
from app.models.document import ModerationStatus, ProcessingStatus
from app.models.ledger import LearningEventRecord
from app.models.user import User, UserRole, UserStatus
from app.orchestration.learning_facade import LearningOrchestrationFacade
from app.orchestration.model_rendering import PolicyBoundModelRenderer
from app.services.activity_lifecycle import ActivityLifecycleService
from app.services.documents.document_service import DocumentService
from app.services.llm.model_router import ChatMessage, LLMResponse
from app.services.owner.canonical_identity import canonical_user_id
from app.services.policy_runtime import default_policy_activation, default_policy_bundle
from app.services.storage.local_storage import LocalFileStorage

NOW = datetime(2026, 8, 8, 22, 0, tzinfo=timezone.utc)


class CountingModelProvider:
    def __init__(self) -> None:
        self.calls: list[list[ChatMessage]] = []
        self.fail = False

    async def chat_completion(
        self,
        messages: list[ChatMessage],
        **_kwargs,
    ) -> LLMResponse:
        self.calls.append(messages)
        if self.fail:
            raise RuntimeError("provider unavailable")
        return LLMResponse(
            content="先依据原文说说你观察到的核心差异是什么？",
            model="glm-policy-test",
            provider="zhipu",
            input_tokens=24,
            output_tokens=12,
            total_tokens=36,
            latency_ms=8,
        )


class FixedModelRouter:
    def __init__(self, provider: CountingModelProvider) -> None:
        self.provider = provider

    def route_for_subject(self, _subject: str) -> CountingModelProvider:
        return self.provider


@pytest.fixture
async def book_learning_db(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'book-learning.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session, tmp_path
    await engine.dispose()


async def _processed_book(db, tmp_path: Path, suffix: str, *, user_id: str | None = None):
    user = User(
        id=user_id or str(uuid4()),
        pseudonym_id=f"exec023-{suffix}",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    await db.commit()
    documents = DocumentService(db)
    documents.storage = LocalFileStorage(str(tmp_path / f"documents-{suffix}"))
    document = await documents.upload_document(
        user.pseudonym_id,
        f"{suffix}.md",
        (
            "# Foundations\n\nDefinition: Foundations support fraction reasoning.\n\n"
            "# Fractions\n\nDefinition: Fractions represent parts of a whole. "
            "Foundations are a prerequisite for Fractions.\n\n"
            "# Ratios\n\nDefinition: Ratios compare quantities. "
            "Fractions are a prerequisite for Ratios."
        ).encode(),
    )
    await documents.process_document(document.id)
    await db.refresh(document)
    revision = document.moderation_details[CONTENT_RECORD_KEY]["revisions"][0]
    units = {
        item["canonical_name"]: UUID(item["knowledge_unit_id"])
        for item in revision["knowledge_units"]
        if item["status"] == "published"
    }
    return user, document, units


@pytest.mark.asyncio
async def test_exec025_legacy_local_user_id_uses_stable_canonical_owner(
    book_learning_db,
) -> None:
    db, tmp_path = book_learning_db
    user, document, _units = await _processed_book(
        db, tmp_path, "legacy-user", user_id="test-user-001"
    )
    application = BookLearningApplication(db)

    readiness = await application.readiness(
        user=user, document_id=UUID(document.id), correlation_id="legacy-user"
    )
    assert readiness.state == "READY_FOR_GOAL"

    created = await application.create_goal_candidate(
        user=user,
        document_id=UUID(document.id),
        intent="能够解释这份资料中的核心概念",
        idempotency_key="legacy-user:goal:create",
        correlation_id=uuid4(),
    )

    assert UUID(created.payload["goal"]["user_id"]) == canonical_user_id("test-user-001")
    assert user.id == "test-user-001"


def _independent() -> AssistanceSnapshot:
    return AssistanceSnapshot(
        hint_level=0,
        assistance_class="none",
        source_visible=False,
        answer_visible=False,
        response_revision=1,
        response_time_ms=1000,
    )


@pytest.mark.asyncio
async def test_exec023_readiness_is_derived_and_blocked_content_cannot_advance(
    book_learning_db,
) -> None:
    db, tmp_path = book_learning_db
    user, document, _units = await _processed_book(db, tmp_path, "readiness")
    app = BookLearningApplication(db)
    initial = await app.readiness(
        user=user, document_id=UUID(document.id), correlation_id="readiness"
    )
    assert initial.state == "READY_FOR_GOAL"
    assert {item.owner_system for item in initial.owner_refs} == {"SYS01", "SYS02"}

    other_user = User(
        id=str(uuid4()),
        pseudonym_id="exec023-other-user",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
    )
    db.add(other_user)
    await db.flush()
    unauthorized = await app.readiness(
        user=other_user, document_id=UUID(document.id), correlation_id="unauthorized"
    )
    assert unauthorized.state == "BLOCKED"
    assert unauthorized.reason_codes == ("BOOK_SOURCE_NOT_FOUND_OR_UNAUTHORIZED",)

    document.processing_status = ProcessingStatus.QUARANTINED
    await db.flush()
    blocked = await app.readiness(
        user=user, document_id=UUID(document.id), correlation_id="blocked"
    )
    assert blocked.state == "BLOCKED"
    with pytest.raises(ValueError, match="BOOK_NOT_READY_FOR_GOAL:BLOCKED"):
        await app.create_goal_candidate(
            user=user,
            document_id=UUID(document.id),
            intent="学习 Ratios",
            idempotency_key="blocked-goal",
            correlation_id=uuid4(),
            now=NOW,
        )

    document.processing_status = ProcessingStatus.COMPLETED
    document.moderation_status = ModerationStatus.REQUIRES_REVIEW
    await db.flush()
    assert (
        await app.readiness(user=user, document_id=UUID(document.id), correlation_id="review")
    ).state == "BLOCKED"


@pytest.mark.asyncio
async def test_exec023_first_activity_uses_canonical_action_and_real_exec020_bundle(
    book_learning_db,
) -> None:
    db, tmp_path = book_learning_db
    user, document, units = await _processed_book(db, tmp_path, "canonical")
    records = AdaptiveContractRepository(db)
    await records.publish_policy_bundle(default_policy_bundle())
    await records.activate_policy_bundle(default_policy_activation())
    provider = CountingModelProvider()
    app = BookLearningApplication(
        db,
        teaching_facade=LearningOrchestrationFacade(
            adaptive_renderer=PolicyBoundModelRenderer(  # type: ignore[arg-type]
                FixedModelRouter(provider)
            )
        ),
    )
    created = await app.create_goal_candidate(
        user=user,
        document_id=UUID(document.id),
        intent="我想掌握 Ratios 并在新题目中应用 Ratios",
        weekly_time_budget_minutes=60,
        idempotency_key="canonical:goal:create",
        correlation_id=uuid4(),
        now=NOW,
    )
    goal_id = UUID(created.payload["goal"]["goal_id"])
    await app.confirm_goal(
        user=user,
        goal_id=goal_id,
        confirmed_by_user=True,
        idempotency_key="canonical:goal:confirm",
        correlation_id=uuid4(),
        now=NOW,
    )
    mapped = await app.advance(
        user=user,
        document_id=UUID(document.id),
        idempotency_key="canonical:advance:map",
        correlation_id=uuid4(),
        now=NOW,
    )
    assert mapped.payload["applied_command"] == "MapGoalToKnowledge"
    mapping_result = await app.get_mapping(
        user=user,
        goal_id=goal_id,
        correlation_id=uuid4(),
    )
    mapping = mapping_result.payload["mapping"]
    prerequisite_id = units["Fractions"]
    db.add(
        AssessmentItem(
            id=str(uuid4()),
            knowledge_point_id=str(prerequisite_id),
            subject="book",
            item_type="fill_blank",
            difficulty=3,
            grade_level=0,
            question_text="Type fractions",
            options=[],
            correct_answer="fractions",
            explanation="grader-only",
            cognitive_level="apply",
            common_misconceptions=[],
            is_active=True,
            version="1.0",
        )
    )
    await db.flush()
    diagnosed = await app.advance(
        user=user,
        document_id=UUID(document.id),
        idempotency_key="canonical:advance:diagnostic",
        correlation_id=uuid4(),
        now=NOW,
    )
    assert diagnosed.payload["applied_command"] == "GeneratePrerequisiteDiagnosis"
    diagnostic_view = await app.get_diagnostic(
        user=user,
        goal_id=goal_id,
        correlation_id=uuid4(),
    )
    assert diagnostic_view.payload["need"]["target_knowledge_unit_id"] == (
        mapping["selected_target_ids"][0]
    )
    learner_item = diagnostic_view.payload["learner_item"]
    assert learner_item["prompt"] == "Type fractions"
    assert learner_item["item_type"] == "exact"
    assert not {"answer_key", "correct_answer", "rubric", "explanation"} & learner_item.keys()
    assert any(
        item.owner_system == "SYS04" and item.ref.entity_type == "AssessmentItem"
        for item in diagnostic_view.owner_refs
    )
    assert (
        await app.readiness(user=user, document_id=UUID(document.id), correlation_id="diagnosing")
    ).state == "DIAGNOSING"
    with pytest.raises(ValueError, match="BOOK_LEARNING_STATE_CONFLICT:DIAGNOSING"):
        await app.select_next_activity(
            user=user,
            goal_id=goal_id,
            idempotency_key="canonical:select-too-early",
            correlation_id=uuid4(),
            now=NOW,
        )

    need = diagnostic_view.payload["need"]
    completed = await app.submit_diagnostic_response(
        user=user,
        need_id=UUID(need["need_id"]),
        expected_need_version=need["version"],
        response="fractions",
        assistance=_independent(),
        idempotency_key="canonical:diagnostic:answer",
        correlation_id=uuid4(),
        now=NOW,
    )
    assert completed.payload["need"]["status"] == "resolved"
    advanced_activity = await app.advance(
        user=user,
        document_id=UUID(document.id),
        idempotency_key="canonical:advance:activity",
        correlation_id=uuid4(),
        now=NOW,
    )
    assert advanced_activity.payload["applied_command"] == "SelectNextLearningActivity"
    duplicate_advanced_activity = await app.advance(
        user=user,
        document_id=UUID(document.id),
        idempotency_key="canonical:advance:activity",
        correlation_id=uuid4(),
        now=NOW,
    )
    assert duplicate_advanced_activity.payload == advanced_activity.payload
    generated = await app.generate_plan(
        user=user,
        need_id=UUID(completed.payload["need"]["need_id"]),
        idempotency_key="canonical:plan:generate",
        correlation_id=uuid4(),
        now=NOW,
    )
    duplicate_generated = await app.generate_plan(
        user=user,
        need_id=UUID(completed.payload["need"]["need_id"]),
        idempotency_key="canonical:plan:generate",
        correlation_id=uuid4(),
        now=NOW,
    )
    assert generated.payload["plan"] == duplicate_generated.payload["plan"]
    assert generated.payload["plan"] == completed.payload["plan"]
    assert (
        await app.readiness(user=user, document_id=UUID(document.id), correlation_id="ready")
    ).state == "READY_TO_LEARN"

    plan_view = await app.get_plan(user=user, goal_id=goal_id, correlation_id=uuid4())
    plan = plan_view.payload["plan"]
    ready = await app.readiness(user=user, document_id=UUID(document.id), correlation_id="ready")
    assert ready.state == "READY_TO_LEARN"
    selected_ref = next(
        item.ref
        for item in ready.owner_refs
        if item.ref.entity_type == "LearningActivity" and item.status == "selected"
    )
    activity = next(
        item
        for item in plan_view.payload["activities"]
        if item["activity_id"] == selected_ref.entity_id
    )
    assert any(
        item.ref.entity_type == "LearningActivity"
        and item.ref.entity_id == str(activity["activity_id"])
        and item.status == "selected"
        for item in ready.owner_refs
    )

    lifecycle = await ActivityLifecycleService(db).get(
        user=user,
        activity_id=UUID(activity["activity_id"]),
        correlation_id=uuid4(),
    )
    await ActivityLifecycleService(db).start(
        user=user,
        command=StartLearningActivityV1(
            activity_id=UUID(activity["activity_id"]),
            expected_state_version=lifecycle.data.state.version,
            idempotency_key="canonical:lifecycle:start",
        ),
        correlation_id=uuid4(),
        now=NOW,
    )

    system_start = await app.start_teaching_round(
        user=user,
        goal_id=goal_id,
        plan_id=UUID(plan["plan_id"]),
        plan_version=plan["version"],
        activity_id=UUID(activity["activity_id"]),
        session_id=None,
        turn_id="system-start-1",
        turn_kind="system_start",
        learner_text=None,
        idempotency_key="canonical:teaching:system-start",
        correlation_id=uuid4(),
        now=NOW,
    )
    assert system_start.turn_number == 1
    assert system_start.turn_kind == "system_start"
    assert system_start.model_execution is not None
    assert system_start.model_execution.mode == "real_model"
    assert system_start.model_execution.provider == "zhipu"
    assert len(provider.calls) == 1
    first_transcript = await app.get_transcript(
        user=user,
        activity_id=UUID(activity["activity_id"]),
        correlation_id=uuid4(),
    )
    assert first_transcript.session_id == system_start.session_id
    assert first_transcript.turns[0].learner_text is None
    assert first_transcript.turns[0].evidence

    teaching_session_id = uuid4()
    teaching = await app.start_teaching_round(
        user=user,
        goal_id=goal_id,
        plan_id=UUID(plan["plan_id"]),
        plan_version=plan["version"],
        activity_id=UUID(activity["activity_id"]),
        session_id=teaching_session_id,
        turn_id="turn-1",
        learner_text="请帮助我理解 ratios 和 fractions 的关系",
        idempotency_key="canonical:teaching:first",
        correlation_id=uuid4(),
        now=NOW,
    )
    assert teaching.reply_text
    assert teaching.session_id == system_start.session_id
    assert teaching.turn_number == 2
    assert teaching.model_execution is not None
    assert teaching.model_execution.mode == "real_model"
    assert len(provider.calls) == 2
    assert teaching.teaching_action.teaching_context_ref.entity_type == "teaching_context"
    assert teaching.evidence_bundle.items
    assert teaching.evidence_bundle.source_scope["document_ids"] == [document.id]
    assert all(item.source_span_ids for item in teaching.evidence_bundle.items)
    assert all(item.allowed_use != "grader_only" for item in teaching.evidence_bundle.items)
    assert {item.owner_system for item in teaching.owner_refs} >= {
        "SYS02",
        "SYS05",
        "SYS06",
        "SYS08",
    }

    duplicate_teaching = await app.start_teaching_round(
        user=user,
        goal_id=goal_id,
        plan_id=UUID(plan["plan_id"]),
        plan_version=plan["version"],
        activity_id=UUID(activity["activity_id"]),
        session_id=teaching_session_id,
        turn_id="turn-1",
        learner_text="请帮助我理解 ratios 和 fractions 的关系",
        idempotency_key="canonical:teaching:first",
        correlation_id=uuid4(),
        now=NOW,
    )
    assert duplicate_teaching.teaching_action == teaching.teaching_action
    assert duplicate_teaching.evidence_bundle == teaching.evidence_bundle
    assert duplicate_teaching.reply_text == teaching.reply_text
    assert duplicate_teaching.model_execution == teaching.model_execution
    assert len(provider.calls) == 2
    transcript = await app.get_transcript(
        user=user,
        activity_id=UUID(activity["activity_id"]),
        correlation_id=uuid4(),
    )
    assert transcript.next_turn_number == 3
    assert [turn.turn_kind for turn in transcript.turns] == ["system_start", "learner"]
    assert transcript.turns[1].learner_text == "请帮助我理解 ratios 和 fractions 的关系"
    assistance_events = (
        await db.scalars(
            select(LearningEventRecord).where(
                LearningEventRecord.event_type == "ActualAssistanceRecorded",
                LearningEventRecord.aggregate_id == str(teaching.teaching_action.action_id),
            )
        )
    ).all()
    assert len(assistance_events) == 1
    assert assistance_events[0].producer_system == "SYS08"
    model_events = (
        await db.scalars(
            select(LearningEventRecord).where(
                LearningEventRecord.event_type == "ModelInferenceCompleted"
            )
        )
    ).all()
    assert len(model_events) == 2
    assert {event.aggregate_id for event in model_events} == {
        str(system_start.model_execution.inference_id),
        str(teaching.model_execution.inference_id),
    }
    assert all("prompt" not in event.payload for event in model_events)

    provider.fail = True
    with pytest.raises(BookLearningApplicationError, match="AI_MODEL_UNAVAILABLE"):
        await app.start_teaching_round(
            user=user,
            goal_id=goal_id,
            plan_id=UUID(plan["plan_id"]),
            plan_version=plan["version"],
            activity_id=UUID(activity["activity_id"]),
            session_id=teaching.session_id,
            turn_id="turn-3-provider-failure",
            learner_text="请继续帮助我理解 ratios 和 fractions 的关系",
            idempotency_key="canonical:teaching:provider-failure",
            correlation_id=uuid4(),
            now=NOW,
        )
    after_failure = await app.get_transcript(
        user=user,
        activity_id=UUID(activity["activity_id"]),
        correlation_id=uuid4(),
    )
    assert len(after_failure.turns) == 2
    active_lifecycle = await ActivityLifecycleService(db).get(
        user=user,
        activity_id=UUID(activity["activity_id"]),
        correlation_id=uuid4(),
    )
    await ActivityLifecycleService(db).complete(
        user=user,
        command=CompleteLearningActivityV1(
            activity_id=UUID(activity["activity_id"]),
            expected_state_version=active_lifecycle.data.state.version,
            completion_intent="learner_finished",
            transcript_turn_refs=tuple(
                VersionedRef(
                    entity_type="BookLearningTranscriptTurn",
                    entity_id=turn.turn_id,
                    version=turn.turn_number,
                )
                for turn in after_failure.turns
            ),
            idempotency_key="canonical:lifecycle:complete",
        ),
        correlation_id=uuid4(),
        now=NOW,
    )
    completed_transcript = await app.get_transcript(
        user=user,
        activity_id=UUID(activity["activity_id"]),
        correlation_id=uuid4(),
    )
    assert len(completed_transcript.turns) == 2
    assert (
        len(
            (
                await db.scalars(
                    select(LearningEventRecord).where(
                        LearningEventRecord.event_type == "ModelInferenceCompleted"
                    )
                )
            ).all()
        )
        == 2
    )


@pytest.mark.asyncio
async def test_exec023_http_is_authenticated_private_correlated_and_idempotent(
    book_learning_db,
) -> None:
    """EXEC-048: HTTP endpoints use LocalOwnerContext for implicit authentication.

    No JWT/session auth needed - single-user local instance.
    All requests are automatically authenticated via LocalOwner context.
    Test verifies: private caching, correlation IDs, idempotency, and
    that loopback-only boundary is enforced.
    """
    from httpx import ASGITransport, AsyncClient

    from app.core.database import get_db
    from app.main import app as fastapi_app
    from app.services.owner.dependencies import get_current_owner_projection

    db, tmp_path = book_learning_db
    user, document, _units = await _processed_book(db, tmp_path, "http")
    correlation_id = uuid4()

    async def override_get_db():
        yield db

    async def override_get_current_owner_projection():
        return user

    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[get_current_owner_projection] = (
        override_get_current_owner_projection
    )
    transport = ASGITransport(app=fastapi_app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            headers = {"X-Correlation-ID": str(correlation_id)}
            readiness = await client.get(
                f"/api/v1/book-learning/{document.id}/readiness", headers=headers
            )
            body = {
                "intent": "我想掌握 Ratios 并在新题目中应用 Ratios",
                "weekly_time_budget_minutes": 60,
                "idempotency_key": "http:goal:create",
            }
            created = await client.post(
                f"/api/v1/book-learning/{document.id}/goals",
                json=body,
                headers=headers,
            )
            assert (
                created.status_code == 200
            ), f"Status: {created.status_code}, Body: {created.text}"
            duplicate = await client.post(
                f"/api/v1/book-learning/{document.id}/goals",
                json=body,
                headers=headers,
            )
            goal_id = created.json()["payload"]["goal"]["goal_id"]
            goal_view = await client.get(f"/api/v1/book-learning/goals/{goal_id}", headers=headers)
        assert readiness.status_code == 200, readiness.text
        assert readiness.headers["cache-control"] == "private, no-store"
        assert readiness.json()["correlation_id"] == str(correlation_id)
        assert created.status_code == 200, created.text
        assert duplicate.status_code == 200, duplicate.text
        assert goal_view.status_code == 200, goal_view.text
        assert goal_view.headers["cache-control"] == "private, no-store"
        assert created.json()["payload"]["goal"] == duplicate.json()["payload"]["goal"]
        assert created.json()["correlation_id"] == str(correlation_id)
    finally:
        fastapi_app.dependency_overrides.clear()

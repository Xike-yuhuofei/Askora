"""EXEC-022 real SYS04 -> SYS03 -> existing SYS06 diagnostic bootstrap."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models  # noqa: F401
from app.contracts.assessment import AssistanceSnapshot
from app.core.database import Base
from app.domains.assessment import ScoringUnavailableError
from app.domains.content_knowledge import CONTENT_RECORD_KEY
from app.infrastructure.learning_records import LearnerModelRepository
from app.models.assessment import (
    AssessmentItem,
    CanonicalAssessmentResultRecord,
    LearnerEvidenceRecord,
    MasteryEstimateRecord,
)
from app.models.user import User, UserRole, UserStatus
from app.services.assessment.diagnostic_bootstrap import PrerequisiteDiagnosticService
from app.services.documents.document_service import DocumentService
from app.services.kt.canonical_projector import CanonicalLearnerProjectorService
from app.services.learning_goals import LearningGoalService
from app.services.storage.local_storage import LocalFileStorage

NOW = datetime(2026, 8, 8, 20, 0, tzinfo=timezone.utc)


@pytest.fixture
async def diagnostic_db(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'diagnostic.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session, tmp_path
    await engine.dispose()


async def _bootstrap(db, tmp_path: Path, suffix: str):
    user = User(
        id=str(uuid4()),
        pseudonym_id=f"exec022-{suffix}",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    await db.commit()
    documents = DocumentService(db)
    documents.storage = LocalFileStorage(str(tmp_path / f"documents-{suffix}"))
    document = await documents.upload_document(
        user.pseudonym_id,
        f"diagnostic-{suffix}.md",
        (
            "# Foundations\n\nDefinition: Foundations support fraction reasoning.\n\n"
            "# Fractions\n\nFoundations are a prerequisite for Fractions.\n\n"
            "# Ratios\n\nFractions are a prerequisite for Ratios."
        ).encode(),
    )
    await documents.process_document(document.id)
    await db.refresh(document)
    revision = document.moderation_details[CONTENT_RECORD_KEY]["revisions"][0]
    unit_ids = {
        item["canonical_name"]: UUID(item["knowledge_unit_id"])
        for item in revision["knowledge_units"]
        if item["status"] == "published"
    }
    goal_service = LearningGoalService(db)
    candidate = await goal_service.create_candidate(
        user=user,
        intent="我想掌握 Ratios 并在新题目中应用 Ratios",
        source_document_ids=(UUID(document.id),),
        idempotency_key=f"{suffix}:goal:create",
        correlation_id=uuid4(),
        created_at=NOW,
        weekly_time_budget_minutes=60,
    )
    goal = await goal_service.confirm_goal(
        user=user,
        goal_id=candidate.goal_id,
        idempotency_key=f"{suffix}:goal:confirm",
        correlation_id=uuid4(),
        confirmed_at=NOW,
        confirmed_by_user=True,
    )
    decision = await goal_service.map_goal(
        user=user,
        goal_id=goal.goal_id,
        idempotency_key=f"{suffix}:goal:map",
        correlation_id=uuid4(),
        created_at=NOW,
    )
    assert decision.mapping.selected_target_ids == (unit_ids["Ratios"],)
    assert decision.subgraph is not None
    return user, goal, decision, unit_ids


def _add_item(db, *, item_id: UUID, knowledge_unit_id: UUID, answer: str) -> None:
    db.add(
        AssessmentItem(
            id=str(item_id),
            knowledge_point_id=str(knowledge_unit_id),
            subject="book",
            item_type="fill_blank",
            difficulty=3,
            grade_level=0,
            question_text=f"Type {answer}",
            options=[],
            correct_answer=answer,
            explanation="grader-only",
            cognitive_level="apply",
            common_misconceptions=[],
            is_active=True,
            version="1.0",
        )
    )


def _independent() -> AssistanceSnapshot:
    return AssistanceSnapshot(
        hint_level=0,
        assistance_class="none",
        source_visible=False,
        answer_visible=False,
        response_revision=1,
        response_time_ms=1000,
    )


def _diagnostic_service(db, **kwargs) -> PrerequisiteDiagnosticService:
    return PrerequisiteDiagnosticService(
        db,
        learner_projector=CanonicalLearnerProjectorService(db),
        **kwargs,
    )


@pytest.mark.asyncio
async def test_exec022_unknown_to_real_diagnostic_success_skips_ancestor_and_replans(
    diagnostic_db,
) -> None:
    db, tmp_path = diagnostic_db
    user, _goal, decision, unit_ids = await _bootstrap(db, tmp_path, "success")
    _add_item(
        db,
        item_id=uuid4(),
        knowledge_unit_id=unit_ids["Fractions"],
        answer="fractions",
    )
    _add_item(
        db,
        item_id=uuid4(),
        knowledge_unit_id=unit_ids["Foundations"],
        answer="foundations",
    )
    await db.commit()
    service = _diagnostic_service(db)
    started = await service.create_need(
        user=user,
        mapping_id=decision.mapping.mapping_id,
        mapping_version=decision.mapping.mapping_version,
        subgraph_id=decision.subgraph.subgraph_id,
        subgraph_version=decision.subgraph.version,
        target_knowledge_unit_id=unit_ids["Ratios"],
        max_attempts=3,
        idempotency_key="success:diagnostic:start",
        correlation_id=uuid4(),
        created_at=NOW,
    )
    assert started.need.current_knowledge_unit_id == unit_ids["Fractions"]
    assert started.need.unknown_ids == tuple(
        sorted((unit_ids["Foundations"], unit_ids["Fractions"]), key=str)
    )
    assert started.plan is not None
    assert any(item.type == "diagnostic" for item in started.activities)

    completed = await service.submit_response(
        user=user,
        need_id=started.need.need_id,
        expected_need_version=started.need.version,
        response="fractions",
        assistance=_independent(),
        idempotency_key="success:response:1",
        correlation_id=uuid4(),
        submitted_at=NOW,
    )
    assert completed.assessment_result is not None
    assert completed.assessment_result.correctness == "correct"
    assert completed.need.status == "resolved"
    assert completed.need.stop_reason == "ALL_DECISION_RELEVANT_PREREQUISITES_RESOLVED"
    assert unit_ids["Foundations"] in completed.need.unknown_ids
    assert unit_ids["Fractions"] in completed.need.sufficient_current_evidence_ids
    assert completed.learner_state.version == started.learner_state.version + 1
    assert completed.plan is not None
    assert completed.plan.version == started.plan.version + 1

    duplicate = await service.submit_response(
        user=user,
        need_id=started.need.need_id,
        expected_need_version=started.need.version,
        response="fractions",
        assistance=_independent(),
        idempotency_key="success:response:1",
        correlation_id=uuid4(),
        submitted_at=NOW,
    )
    assert duplicate.need == completed.need
    result_count = await db.scalar(
        select(func.count()).select_from(CanonicalAssessmentResultRecord)
    )
    evidence_count = await db.scalar(select(func.count()).select_from(LearnerEvidenceRecord))
    mastery_count = await db.scalar(select(func.count()).select_from(MasteryEstimateRecord))
    assert result_count == evidence_count == mastery_count == 1
    assert (
        await service.replay_need(
            user=user, need_id=completed.need.need_id, version=completed.need.version
        )
        == completed.need
    )


@pytest.mark.asyncio
async def test_exec022_failure_descends_and_budget_preserves_unknown(diagnostic_db) -> None:
    db, tmp_path = diagnostic_db
    user, _goal, decision, unit_ids = await _bootstrap(db, tmp_path, "failure")
    _add_item(
        db,
        item_id=uuid4(),
        knowledge_unit_id=unit_ids["Fractions"],
        answer="fractions",
    )
    _add_item(
        db,
        item_id=uuid4(),
        knowledge_unit_id=unit_ids["Foundations"],
        answer="foundations",
    )
    await db.commit()
    service = _diagnostic_service(db)
    started = await service.create_need(
        user=user,
        mapping_id=decision.mapping.mapping_id,
        mapping_version=decision.mapping.mapping_version,
        subgraph_id=decision.subgraph.subgraph_id,
        subgraph_version=decision.subgraph.version,
        target_knowledge_unit_id=unit_ids["Ratios"],
        max_attempts=2,
        idempotency_key="failure:diagnostic:start",
        correlation_id=uuid4(),
        created_at=NOW,
    )
    descended = await service.submit_response(
        user=user,
        need_id=started.need.need_id,
        expected_need_version=1,
        response="wrong",
        assistance=_independent(),
        idempotency_key="failure:response:1",
        correlation_id=uuid4(),
        submitted_at=NOW,
    )
    assert descended.need.status == "active"
    assert descended.need.current_knowledge_unit_id == unit_ids["Foundations"]
    assert unit_ids["Fractions"] in descended.need.unmet_ids
    assert descended.plan is not None
    assert any(item.type == "prerequisite_remediation" for item in descended.activities)

    exhausted = await service.submit_response(
        user=user,
        need_id=descended.need.need_id,
        expected_need_version=2,
        response="wrong",
        assistance=_independent(),
        idempotency_key="failure:response:2",
        correlation_id=uuid4(),
        submitted_at=NOW,
    )
    assert exhausted.need.stop_reason == "REMEDIATION_REQUIRED"
    assert unit_ids["Foundations"] in exhausted.need.unmet_ids
    assert exhausted.need.attempts_used == exhausted.need.max_attempts

    budget_user, _goal, budget_decision, budget_ids = await _bootstrap(db, tmp_path, "budget")
    _add_item(
        db,
        item_id=uuid4(),
        knowledge_unit_id=budget_ids["Fractions"],
        answer="fractions",
    )
    await db.commit()
    budget_start = await service.create_need(
        user=budget_user,
        mapping_id=budget_decision.mapping.mapping_id,
        mapping_version=budget_decision.mapping.mapping_version,
        subgraph_id=budget_decision.subgraph.subgraph_id,
        subgraph_version=budget_decision.subgraph.version,
        target_knowledge_unit_id=budget_ids["Ratios"],
        max_attempts=1,
        idempotency_key="budget:diagnostic:start",
        correlation_id=uuid4(),
        created_at=NOW,
    )
    budget_stop = await service.submit_response(
        user=budget_user,
        need_id=budget_start.need.need_id,
        expected_need_version=budget_start.need.version,
        response="wrong",
        assistance=_independent(),
        idempotency_key="budget:response:1",
        correlation_id=uuid4(),
        submitted_at=NOW,
    )
    assert budget_stop.need.stop_reason == "DIAGNOSTIC_BUDGET_EXHAUSTED"
    assert budget_ids["Foundations"] in budget_stop.need.unknown_ids


class _FailingAssessment:
    async def score_submission_with_attempt(self, **_kwargs):
        raise ScoringUnavailableError("grader unavailable")


@pytest.mark.asyncio
async def test_exec022_no_item_system_failure_and_answer_exposure_preserve_boundary(
    diagnostic_db,
) -> None:
    db, tmp_path = diagnostic_db
    user, _goal, decision, unit_ids = await _bootstrap(db, tmp_path, "boundaries")
    service = _diagnostic_service(db)
    no_item = await service.create_need(
        user=user,
        mapping_id=decision.mapping.mapping_id,
        mapping_version=decision.mapping.mapping_version,
        subgraph_id=decision.subgraph.subgraph_id,
        subgraph_version=decision.subgraph.version,
        target_knowledge_unit_id=unit_ids["Ratios"],
        max_attempts=2,
        idempotency_key="boundaries:no-item",
        correlation_id=uuid4(),
        created_at=NOW,
    )
    assert no_item.need.stop_reason == "NO_VALID_ASSESSMENT_ITEM"
    assert no_item.need.unknown_ids

    _add_item(
        db,
        item_id=uuid4(),
        knowledge_unit_id=unit_ids["Fractions"],
        answer="fractions",
    )
    await db.commit()
    failing = _diagnostic_service(db, assessment_service=_FailingAssessment())
    failed_start = await failing.create_need(
        user=user,
        mapping_id=decision.mapping.mapping_id,
        mapping_version=decision.mapping.mapping_version,
        subgraph_id=decision.subgraph.subgraph_id,
        subgraph_version=decision.subgraph.version,
        target_knowledge_unit_id=unit_ids["Ratios"],
        max_attempts=2,
        idempotency_key="boundaries:system:start",
        correlation_id=uuid4(),
        created_at=NOW,
    )
    system_blocked = await failing.submit_response(
        user=user,
        need_id=failed_start.need.need_id,
        expected_need_version=failed_start.need.version,
        response="wrong",
        assistance=_independent(),
        idempotency_key="boundaries:system:response",
        correlation_id=uuid4(),
        submitted_at=NOW,
    )
    assert system_blocked.need.stop_reason == "SYSTEM_BLOCKED"
    assert await db.scalar(select(func.count()).select_from(LearnerEvidenceRecord)) == 0

    exposed_start = await service.create_need(
        user=user,
        mapping_id=decision.mapping.mapping_id,
        mapping_version=decision.mapping.mapping_version,
        subgraph_id=decision.subgraph.subgraph_id,
        subgraph_version=decision.subgraph.version,
        target_knowledge_unit_id=unit_ids["Ratios"],
        max_attempts=2,
        idempotency_key="boundaries:exposed:start",
        correlation_id=uuid4(),
        created_at=NOW,
    )
    exposed = await service.submit_response(
        user=user,
        need_id=exposed_start.need.need_id,
        expected_need_version=exposed_start.need.version,
        response="fractions",
        assistance=AssistanceSnapshot(
            hint_level=4,
            assistance_class="full_solution",
            source_visible=True,
            answer_visible=True,
            response_revision=1,
            response_time_ms=1000,
        ),
        idempotency_key="boundaries:exposed:response",
        correlation_id=uuid4(),
        submitted_at=NOW,
    )
    assert exposed.assessment_result is not None
    assert exposed.assessment_result.independence == "answer_exposed"
    assert exposed.need.stop_reason == "LOW_CONFIDENCE_REQUIRES_REVIEW"
    estimate = await LearnerModelRepository(db).latest_mastery(
        user_id=UUID(user.id), knowledge_unit_id=unit_ids["Fractions"]
    )
    assert estimate is not None
    assert estimate.independent_success_count == 0
    assert estimate.effective_evidence_weight == 0.0

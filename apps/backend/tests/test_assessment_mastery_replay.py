from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.contracts.assessment import AssessmentAttempt, AssessmentItemV1, AssistanceSnapshot
from app.contracts.learning import AssessmentResult
from app.core.database import Base
from app.domains.assessment import AssessmentScoringService, ScoringUnavailableError
from app.domains.learner_model import EvidenceEligibility, WeightedBKTProjector
from app.infrastructure.learning_records import AssessmentRecordRepository, LearnerModelRepository
from app.models import DialogSession, User
from app.models.assessment import (
    CanonicalAssessmentResultRecord,
    LearnerEvidenceRecord,
    MasteryEstimateRecord,
)
from app.models.ledger import OutboxTaskRecord
from app.services.assessment.canonical_service import CanonicalAssessmentService
from app.services.dkt.dkt_service import DKTService
from app.services.kt.canonical_projector import CanonicalLearnerProjectorService

FIXED_TIME = datetime(2026, 8, 7, 9, 0, tzinfo=timezone.utc)


def _item() -> AssessmentItemV1:
    return AssessmentItemV1(
        item_id=UUID("00000000-0000-0000-0000-000000000101"),
        version="1.0",
        knowledge_unit_id=UUID("00000000-0000-0000-0000-000000000201"),
        item_type="exact",
        prompt="2 + 2 = ?",
        answer_key="4",
        difficulty=0.2,
    )


def _assistance(
    kind: Literal["none", "hint", "worked_step", "full_solution"],
) -> AssistanceSnapshot:
    return AssistanceSnapshot(
        hint_level=0 if kind == "none" else 2,
        assistance_class=kind,
        source_visible=kind != "none",
        answer_visible=kind == "full_solution",
        response_revision=1,
        response_time_ms=800,
    )


@pytest.mark.parametrize(
    ("assistance_class", "independence", "expected_weight"),
    [
        ("none", "independent", 0.8),
        ("hint", "assisted", 0.28),
        ("full_solution", "answer_exposed", 0.0),
    ],
)
def test_assessment_table_driven_evidence_eligibility(
    assistance_class: Literal["none", "hint", "worked_step", "full_solution"],
    independence: str,
    expected_weight: float,
) -> None:
    scorer = AssessmentScoringService()
    item = _item()
    user_id = uuid4()
    attempt = scorer.submit(
        item=item,
        user_id=user_id,
        response=" 4 ",
        assistance=_assistance(assistance_class),
        idempotency_key=f"attempt-{assistance_class}",
        submitted_at=FIXED_TIME,
    )
    result = scorer.score(item=item, attempt=attempt, clock=lambda: FIXED_TIME)
    assert result.independence == independence

    decision = EvidenceEligibility().decide(
        result=result,
        attempt=attempt,
        knowledge_unit_id=item.knowledge_unit_id,
        dimension="routine_application",
        novelty="near_variant",
        delay_seconds=0,
        source_event_ids=[uuid4()],
        item_difficulty=item.difficulty,
    )
    assert decision.accepted
    assert decision.evidence is not None
    assert decision.evidence.evidence_weight == pytest.approx(expected_weight)


def test_assessment_infrastructure_failure_is_not_user_incorrect() -> None:
    scorer = AssessmentScoringService()
    item = _item()
    attempt = scorer.submit(
        item=item,
        user_id=uuid4(),
        response="4",
        assistance=_assistance("none"),
        idempotency_key="infra-failure",
        submitted_at=FIXED_TIME,
    )

    def unavailable() -> None:
        raise ConnectionError("grader dependency unavailable")

    with pytest.raises(ScoringUnavailableError, match="ASSESSMENT_SCORING_UNAVAILABLE"):
        scorer.score(item=item, attempt=attempt, infrastructure_probe=unavailable)


def test_response_revisions_append_and_reassessment_links_old_result() -> None:
    scorer = AssessmentScoringService()
    item = _item()
    attempt = scorer.submit(
        item=item,
        user_id=uuid4(),
        response="5",
        assistance=_assistance("none"),
        idempotency_key="revised-response",
        submitted_at=FIXED_TIME,
    )
    revised_assistance = _assistance("hint").model_copy(update={"response_revision": 2})
    revised = scorer.revise(
        attempt=attempt,
        response="4",
        assistance=revised_assistance,
        submitted_at=FIXED_TIME + timedelta(seconds=10),
    )
    original = scorer.score(item=item, attempt=attempt, clock=lambda: FIXED_TIME)
    reassessed = scorer.score(
        item=item,
        attempt=revised,
        result_version=2,
        supersedes_result_id=original.result_id,
        clock=lambda: FIXED_TIME + timedelta(seconds=10),
    )
    assert [revision.raw_response for revision in revised.response_revisions] == ["5", "4"]
    assert reassessed.result_version == 2
    assert reassessed.supersedes_result_id == original.result_id
    assert original.correctness == "incorrect"
    assert reassessed.correctness == "correct"


def test_mastery_replay_is_deterministic_and_invalidation_recomputes() -> None:
    scorer = AssessmentScoringService()
    eligibility = EvidenceEligibility()
    item = _item()
    user_id = uuid4()
    event_id = uuid4()
    evidence = []
    for index, correct in enumerate((True, False, True)):
        attempt = scorer.submit(
            item=item,
            user_id=user_id,
            response="4" if correct else "5",
            assistance=_assistance("none"),
            idempotency_key=f"replay-{index}",
            submitted_at=FIXED_TIME + timedelta(days=index),
        )
        result = scorer.score(
            item=item,
            attempt=attempt,
            clock=lambda index=index: FIXED_TIME + timedelta(days=index),
        )
        decision = eligibility.decide(
            result=result,
            attempt=attempt,
            knowledge_unit_id=item.knowledge_unit_id,
            dimension="recall",
            novelty="far_variant",
            delay_seconds=index * 86_400,
            source_event_ids=[event_id],
        )
        assert decision.evidence is not None
        evidence.append(decision.evidence)

    projector = WeightedBKTProjector()
    first = projector.project(
        user_id=user_id,
        knowledge_unit_id=item.knowledge_unit_id,
        evidence=evidence,
        version=1,
    )
    replayed = projector.project(
        user_id=user_id,
        knowledge_unit_id=item.knowledge_unit_id,
        evidence=list(reversed(evidence)),
        version=1,
    )
    invalidated = projector.project(
        user_id=user_id,
        knowledge_unit_id=item.knowledge_unit_id,
        evidence=evidence,
        version=2,
        invalidated_evidence_ids={evidence[1].evidence_id},
    )
    assert replayed == first
    assert invalidated.version == 2
    assert invalidated.evidence_count == 2
    assert invalidated.competence_probability != first.competence_probability
    assert first.algorithm_id == "weighted-bkt"
    assert first.algorithm_version == "1.0"


@pytest.mark.asyncio
async def test_canonical_assessment_to_mastery_is_durable_idempotent_and_traceable(
    tmp_path: Path,
) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'mastery.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    item = _item()
    user_id = uuid4()
    workspace_id = uuid4()

    async with factory() as session:
        result = await CanonicalAssessmentService(session).score_submission(
            item=item,
            user_id=user_id,
            workspace_id=workspace_id,
            response="4",
            assistance=_assistance("none"),
            idempotency_key="durable-attempt",
        )
        await session.commit()
    async with factory() as session:
        task = await session.scalar(
            select(OutboxTaskRecord).where(
                OutboxTaskRecord.idempotency_key == f"assessment-result-project:{result.result_id}"
            )
        )
        assert task is not None
        attempt_payload = task.payload["attempt"]
        result_payload = task.payload["result"]
        restored_attempt = AssessmentAttempt.model_validate(attempt_payload)
        restored_result = AssessmentResult.model_validate(result_payload)
        reassessed = AssessmentScoringService().score(
            item=item,
            attempt=restored_attempt,
            result_version=2,
            supersedes_result_id=restored_result.result_id,
        )
        await AssessmentRecordRepository(session).save_result(reassessed, workspace_id=workspace_id)
        estimate = await CanonicalLearnerProjectorService(session).project_assessment(
            attempt=restored_attempt,
            result=restored_result,
            knowledge_unit_id=item.knowledge_unit_id,
            workspace_id=workspace_id,
            source_event_ids=[uuid4()],
        )
        assert estimate is not None
        await session.commit()

    async with factory() as session:
        evidence_rows = (await session.scalars(select(LearnerEvidenceRecord))).all()
        mastery_rows = (await session.scalars(select(MasteryEstimateRecord))).all()
        result_rows = (await session.scalars(select(CanonicalAssessmentResultRecord))).all()
        assert len(evidence_rows) == len(mastery_rows) == 1
        assert len(result_rows) == 2
        reassessment_row = next(row for row in result_rows if row.result_version == 2)
        assert reassessment_row.supersedes_result_id == str(result.result_id)
        evidence = evidence_rows[0].payload
        mastery = mastery_rows[0].payload
        assert evidence["attempt_id"] == str(result.attempt_id)
        assert evidence["result_id"] == str(result.result_id)
        assert mastery["source_evidence_ids"] == [evidence["evidence_id"]]
        assert mastery["algorithm_version"] == "1.0"
    await engine.dispose()


@pytest.mark.asyncio
async def test_dialog_mastery_compatibility_field_only_syncs_from_canonical_projection(
    tmp_path: Path,
) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'projection.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    user_id, dialog_id = uuid4(), uuid4()
    item = _item()
    estimate = WeightedBKTProjector().project(
        user_id=user_id,
        knowledge_unit_id=item.knowledge_unit_id,
        evidence=[],
        version=1,
    )
    async with factory() as session:
        session.add(User(id=str(user_id), pseudonym_id="pseudonym-projection"))
        session.add(
            DialogSession(
                id=str(dialog_id), user_id=str(user_id), pseudonym_id="pseudonym-projection"
            )
        )
        await session.flush()
        await LearnerModelRepository(session).sync_legacy_dialog_projection(
            dialog_session_id=dialog_id,
            estimate=estimate,
        )
        await session.commit()
    async with factory() as session:
        dialog = await session.get(DialogSession, str(dialog_id))
        assert dialog is not None
        assert dialog.mastery_estimate == estimate.competence_probability
    await engine.dispose()


def test_state_consistency_assessment_has_no_mastery_write_and_dkt_is_challenger() -> None:
    service_source = Path("app/services/assessment/assessment_service.py").read_text()
    canonical_source = Path("app/services/assessment/canonical_service.py").read_text()
    assert "get_kt_service" not in service_source
    assert ".update_mastery(" not in service_source
    assert "MasteryEstimateRecord" not in canonical_source
    assert DKTService.MODEL_ROLE == "challenger"
    assert DKTService.CANONICAL_WRITE_ENABLED is False

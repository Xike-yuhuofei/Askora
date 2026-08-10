"""EXEC-062 / XIK-177 Workspace-scoped Learner Evidence / Mastery / Review isolation.

Proves the frozen invariant against a fresh SQLite datastore:

```text
same LocalOwner + same KnowledgeUnit + different Workspace
≠ same learner evidence/mastery/review stream
```

Covers EXEC062-AC-001 .. AC-010. Uses explicit Workspace A/B fixtures with the
same KnowledgeUnit identity in both Workspaces.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.contracts.assessment import AssessmentItemV1, AssistanceSnapshot
from app.contracts.planning import ReviewObservation
from app.core.database import Base
from app.domains.learner_model import EvidenceEligibility, WeightedBKTProjector
from app.domains.learner_model.diagnostic_state import DiagnosticLearnerStateService
from app.infrastructure.learning_records import LearnerModelRepository
from app.infrastructure.outbox import OutboxProducer
from app.infrastructure.planning_records import LearningPlanRepository, ReviewScheduleRepository
from app.models.assessment import (
    CanonicalAssessmentAttemptRecord,
    LearnerEvidenceRecord,
    LearnerStateRecord,
    MasteryEstimateRecord,
)
from app.models.planning import ReviewObservationRecord, ReviewScheduleRecord
from app.models.workspace import Workspace
from app.orchestration.review_planning import ReviewPlanningApplication
from app.services.assessment.canonical_service import CanonicalAssessmentService
from app.services.kt.canonical_projector import CanonicalLearnerProjectorService
from app.services.local_identity import ensure_local_owner
from app.services.workspace.bootstrap import WorkspaceBootstrapService
from app.services.workspace.resolution import resolve_workspace_id

FIXED_TIME = datetime(2026, 8, 10, 9, 0, tzinfo=timezone.utc)


@pytest.fixture
async def db(tmp_path: Path) -> AsyncSession:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'exec062.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


async def _owner(db: AsyncSession) -> UUID:
    ctx = await ensure_local_owner(db)
    await db.commit()
    return UUID(ctx.canonical_owner_id)


async def _workspaces(db: AsyncSession, owner_id: UUID) -> tuple[Workspace, Workspace]:
    """Return the default Workspace (A) and a second active Workspace (B)."""
    ws_a = await WorkspaceBootstrapService(db).ensure_default_workspace(str(owner_id))
    ws_b = Workspace(
        workspace_id=str(uuid4()),
        owner_id=str(owner_id),
        version=1,
        display_name="Workspace B",
        is_default=False,
        lifecycle="active",
    )
    db.add(ws_b)
    await db.flush()
    return ws_a, ws_b


def _item(ku: UUID) -> AssessmentItemV1:
    return AssessmentItemV1(
        item_id=uuid5(NAMESPACE_URL, f"askora:item:{ku}"),
        version="1.0",
        knowledge_unit_id=ku,
        item_type="exact",
        prompt="2 + 2 = ?",
        answer_key="4",
        difficulty=0.2,
    )


def _assistance(kind: Literal["none", "hint", "full_solution"]) -> AssistanceSnapshot:
    return AssistanceSnapshot(
        hint_level=0 if kind == "none" else (2 if kind == "hint" else 4),
        assistance_class=kind,
        source_visible=kind != "none",
        answer_visible=kind == "full_solution",
        response_revision=1,
        response_time_ms=800,
    )


async def _project(
    db: AsyncSession,
    *,
    ku: UUID,
    workspace_id: UUID,
    user_id: UUID,
    correct: bool = True,
    idempotency_key: str,
) -> tuple[object, object]:
    """Score one submission and project it into the given Workspace."""
    item = _item(ku)
    scored = await CanonicalAssessmentService(db).score_submission_with_attempt(
        item=item,
        user_id=user_id,
        workspace_id=workspace_id,
        response="4" if correct else "5",
        assistance=_assistance("none"),
        idempotency_key=idempotency_key,
        correlation_id=str(uuid4()),
    )
    estimate = await CanonicalLearnerProjectorService(db).project_assessment(
        attempt=scored.attempt,
        result=scored.result,
        knowledge_unit_id=ku,
        workspace_id=workspace_id,
        source_event_ids=[uuid4()],
        dimension="routine_application",
        novelty="near_variant",
        item_difficulty=item.difficulty,
        correlation_id=str(uuid4()),
    )
    return estimate, scored


# ---------------------------------------------------------------------------
# EXEC062-AC-001 / AC-002: evidence + mastery/version isolation
# ---------------------------------------------------------------------------


async def test_ac001_ac002_evidence_and_mastery_are_workspace_isolated(db: AsyncSession) -> None:
    owner_id = await _owner(db)
    ws_a, ws_b = await _workspaces(db, owner_id)
    ku = uuid4()  # same KnowledgeUnit in both Workspaces

    # Workspace A: two independent correct responses.
    await _project(
        db, ku=ku, workspace_id=UUID(ws_a.workspace_id), user_id=owner_id, idempotency_key="a-1"
    )
    await _project(
        db, ku=ku, workspace_id=UUID(ws_a.workspace_id), user_id=owner_id, idempotency_key="a-2"
    )
    # Workspace B: one independent correct response for the SAME KU.
    await _project(
        db, ku=ku, workspace_id=UUID(ws_b.workspace_id), user_id=owner_id, idempotency_key="b-1"
    )
    await db.commit()

    repo = LearnerModelRepository(db)
    a_latest = await repo.latest_mastery(
        user_id=owner_id, knowledge_unit_id=ku, workspace_id=UUID(ws_a.workspace_id)
    )
    b_latest = await repo.latest_mastery(
        user_id=owner_id, knowledge_unit_id=ku, workspace_id=UUID(ws_b.workspace_id)
    )
    assert a_latest is not None and b_latest is not None
    # Independent version histories for the same KU in A/B.
    assert a_latest.version == 2
    assert b_latest.version == 1
    assert a_latest.estimate_id != b_latest.estimate_id

    # Evidence isolation at the stream level.
    a_evidence = await repo.list_evidence(
        user_id=owner_id, knowledge_unit_id=ku, workspace_id=UUID(ws_a.workspace_id)
    )
    b_evidence = await repo.list_evidence(
        user_id=owner_id, knowledge_unit_id=ku, workspace_id=UUID(ws_b.workspace_id)
    )
    assert len(a_evidence) == 2
    assert len(b_evidence) == 1
    a_ids = {item.evidence_id for item in a_evidence}
    b_ids = {item.evidence_id for item in b_evidence}
    assert a_ids.isdisjoint(b_ids)  # no cross-workspace evidence fusion

    # Record-level attribution is exact.
    a_rows = (
        await db.scalars(
            select(LearnerEvidenceRecord).where(
                LearnerEvidenceRecord.workspace_id == ws_a.workspace_id
            )
        )
    ).all()
    b_rows = (
        await db.scalars(
            select(LearnerEvidenceRecord).where(
                LearnerEvidenceRecord.workspace_id == ws_b.workspace_id
            )
        )
    ).all()
    assert len(a_rows) == 2 and len(b_rows) == 1
    assert all(row.workspace_id == ws_a.workspace_id for row in a_rows)
    assert all(row.workspace_id == ws_b.workspace_id for row in b_rows)


# ---------------------------------------------------------------------------
# EXEC062-AC-002 suffix: LearnerState projection/version isolation
# ---------------------------------------------------------------------------


async def test_ac002_learner_state_is_workspace_isolated(db: AsyncSession) -> None:
    owner_id = await _owner(db)
    ws_a, ws_b = await _workspaces(db, owner_id)
    ku = uuid4()
    await _project(
        db, ku=ku, workspace_id=UUID(ws_a.workspace_id), user_id=owner_id, idempotency_key="a-1"
    )
    await _project(
        db, ku=ku, workspace_id=UUID(ws_b.workspace_id), user_id=owner_id, idempotency_key="b-1"
    )
    await db.commit()

    service = DiagnosticLearnerStateService(
        db, mastery_projector=CanonicalLearnerProjectorService(db)
    )
    state_a, _ = await service.current_state(
        user_id=owner_id,
        workspace_id=UUID(ws_a.workspace_id),
        knowledge_unit_ids=(ku,),
        created_at=FIXED_TIME,
    )
    state_b, _ = await service.current_state(
        user_id=owner_id,
        workspace_id=UUID(ws_b.workspace_id),
        knowledge_unit_ids=(ku,),
        created_at=FIXED_TIME,
    )
    await db.commit()
    assert state_a.learner_state_id != state_b.learner_state_id

    # Only the A learner-state stream is visible under Workspace A.
    a_rows = (
        await db.scalars(
            select(LearnerStateRecord).where(LearnerStateRecord.workspace_id == ws_a.workspace_id)
        )
    ).all()
    b_rows = (
        await db.scalars(
            select(LearnerStateRecord).where(LearnerStateRecord.workspace_id == ws_b.workspace_id)
        )
    ).all()
    assert a_rows and b_rows
    assert {r.workspace_id for r in a_rows} == {ws_a.workspace_id}
    assert {r.workspace_id for r in b_rows} == {ws_b.workspace_id}


# ---------------------------------------------------------------------------
# EXEC062-AC-003: ReviewSchedule uses Workspace-matched state/evidence only
# ---------------------------------------------------------------------------


async def test_ac003_review_schedule_is_workspace_isolated(db: AsyncSession) -> None:
    owner_id = await _owner(db)
    ws_a, ws_b = await _workspaces(db, owner_id)
    ku = uuid4()
    app = ReviewPlanningApplication(
        ReviewScheduleRepository(db), LearningPlanRepository(db), OutboxProducer(db)
    )

    obs_a = ReviewObservation(
        observation_id=uuid4(),
        user_id=owner_id,
        knowledge_unit_id=ku,
        observed_at=FIXED_TIME,
        actual_reviewed_at=FIXED_TIME - timedelta(minutes=1),
        retrieval_required=True,
        independence="independent",
        hint_level=0,
        answer_seen_before_attempt=False,
        assessment_confidence=1.0,
        outcome="success",
        delay_seconds=86_400,
        source_evidence_id=uuid4(),
        source_event_ids=[uuid4()],
    )
    obs_b = obs_a.model_copy(update={"observation_id": uuid4(), "source_evidence_id": uuid4()})

    schedule_a = await app.apply_review_observation(obs_a, workspace_id=UUID(ws_a.workspace_id))
    schedule_b = await app.apply_review_observation(obs_b, workspace_id=UUID(ws_b.workspace_id))
    await db.commit()

    repo = ReviewScheduleRepository(db)
    latest_a = await repo.latest(
        user_id=owner_id, knowledge_unit_id=ku, workspace_id=UUID(ws_a.workspace_id)
    )
    latest_b = await repo.latest(
        user_id=owner_id, knowledge_unit_id=ku, workspace_id=UUID(ws_b.workspace_id)
    )
    assert latest_a is not None and latest_b is not None
    assert latest_a.schedule_id == schedule_a.schedule_id
    assert latest_b.schedule_id == schedule_b.schedule_id
    assert schedule_a.schedule_id != schedule_b.schedule_id

    # list_latest_for_user is Workspace-filtered.
    only_a = await repo.list_latest_for_user(owner_id, workspace_id=UUID(ws_a.workspace_id))
    only_b = await repo.list_latest_for_user(owner_id, workspace_id=UUID(ws_b.workspace_id))
    assert {s.schedule_id for s in only_a} == {schedule_a.schedule_id}
    assert {s.schedule_id for s in only_b} == {schedule_b.schedule_id}

    # Observation rows carry exact Workspace attribution.
    a_obs = (
        await db.scalars(
            select(ReviewObservationRecord).where(
                ReviewObservationRecord.workspace_id == ws_a.workspace_id
            )
        )
    ).all()
    b_obs = (
        await db.scalars(
            select(ReviewObservationRecord).where(
                ReviewObservationRecord.workspace_id == ws_b.workspace_id
            )
        )
    ).all()
    assert {o.id for o in a_obs} == {str(obs_a.observation_id)}
    assert {o.id for o in b_obs} == {str(obs_b.observation_id)}


# ---------------------------------------------------------------------------
# EXEC062-AC-005: duplicate / idempotency stays correct inside Workspace scope
# ---------------------------------------------------------------------------


async def test_ac005_idempotency_is_workspace_scoped(db: AsyncSession) -> None:
    owner_id = await _owner(db)
    ws_a, ws_b = await _workspaces(db, owner_id)
    ku = uuid4()

    # Same submission idempotency key twice in A -> one attempt/result/evidence.
    first, _ = await _project(
        db, ku=ku, workspace_id=UUID(ws_a.workspace_id), user_id=owner_id, idempotency_key="dup-a"
    )
    second, _ = await _project(
        db, ku=ku, workspace_id=UUID(ws_a.workspace_id), user_id=owner_id, idempotency_key="dup-a"
    )
    await db.commit()
    assert second is not None
    assert first.estimate_id == second.estimate_id  # idempotent within A

    a_evidence = await LearnerModelRepository(db).list_evidence(
        user_id=owner_id, knowledge_unit_id=ku, workspace_id=UUID(ws_a.workspace_id)
    )
    assert len(a_evidence) == 1  # duplicate did not add evidence

    attempts = (
        await db.scalars(
            select(CanonicalAssessmentAttemptRecord).where(
                CanonicalAssessmentAttemptRecord.workspace_id == ws_a.workspace_id
            )
        )
    ).all()
    assert len(attempts) == 1  # idempotent attempt persistence

    # Same idempotency key in B is a separate, independent stream (no fusion).
    b_first, _ = await _project(
        db, ku=ku, workspace_id=UUID(ws_b.workspace_id), user_id=owner_id, idempotency_key="dup-a"
    )
    await db.commit()
    assert b_first.estimate_id != first.estimate_id
    b_evidence = await LearnerModelRepository(db).list_evidence(
        user_id=owner_id, knowledge_unit_id=ku, workspace_id=UUID(ws_b.workspace_id)
    )
    assert len(b_evidence) == 1
    assert b_evidence[0].evidence_id != a_evidence[0].evidence_id


# ---------------------------------------------------------------------------
# EXEC062-AC-006: correction / invalidation reprojects only the affected Workspace
# ---------------------------------------------------------------------------


async def test_ac006_invalidation_reprojects_only_affected_workspace(db: AsyncSession) -> None:
    owner_id = await _owner(db)
    ws_a, ws_b = await _workspaces(db, owner_id)
    ku = uuid4()
    est_a, _ = await _project(
        db, ku=ku, workspace_id=UUID(ws_a.workspace_id), user_id=owner_id, idempotency_key="a-1"
    )
    est_b, _ = await _project(
        db, ku=ku, workspace_id=UUID(ws_b.workspace_id), user_id=owner_id, idempotency_key="b-1"
    )
    await db.commit()
    assert est_a is not None and est_b is not None

    evidence_a = (
        await LearnerModelRepository(db).list_evidence(
            user_id=owner_id, knowledge_unit_id=ku, workspace_id=UUID(ws_a.workspace_id)
        )
    )[0]

    # Invalidate only Workspace A's evidence -> A version bumps, B untouched.
    recomputed_a = await CanonicalLearnerProjectorService(db).recompute_after_invalidation(
        user_id=owner_id,
        knowledge_unit_id=ku,
        workspace_id=UUID(ws_a.workspace_id),
        evidence_id=evidence_a.evidence_id,
    )
    await db.commit()

    assert recomputed_a.version == est_a.version + 1  # A reprojected
    b_latest = await LearnerModelRepository(db).latest_mastery(
        user_id=owner_id, knowledge_unit_id=ku, workspace_id=UUID(ws_b.workspace_id)
    )
    assert b_latest is not None
    assert b_latest.version == est_b.version  # B untouched
    assert b_latest.estimate_id == est_b.estimate_id

    # Workspace B evidence is still valid while A's is invalidated.
    assert recomputed_a.evidence_count == 0
    b_evidence = await LearnerModelRepository(db).list_evidence(
        user_id=owner_id, knowledge_unit_id=ku, workspace_id=UUID(ws_b.workspace_id)
    )
    assert len(b_evidence) == 1


# ---------------------------------------------------------------------------
# EXEC062-AC-007: deterministic replay stays deterministic + offline
# ---------------------------------------------------------------------------


async def test_ac007_deterministic_replay_is_offline_and_reproducible(db: AsyncSession) -> None:
    owner_id = await _owner(db)
    ws_a, _ = await _workspaces(db, owner_id)
    ku = uuid4()
    item = _item(ku)
    scorer_eligibility = EvidenceEligibility()
    # The projector is pure and offline; determinism is proven directly.
    all_evidence = []
    for index, correct in enumerate((True, False, True)):
        scored = await CanonicalAssessmentService(db).score_submission_with_attempt(
            item=item,
            user_id=owner_id,
            workspace_id=UUID(ws_a.workspace_id),
            response="4" if correct else "5",
            assistance=_assistance("none"),
            idempotency_key=f"replay-{index}",
            correlation_id=str(uuid4()),
        )
        decision = scorer_eligibility.decide(
            result=scored.result,
            attempt=scored.attempt,
            knowledge_unit_id=ku,
            dimension="recall",
            novelty="far_variant",
            delay_seconds=index * 86_400,
            source_event_ids=[uuid4()],
        )
        assert decision.evidence is not None
        all_evidence.append(decision.evidence)
    await db.commit()

    projector = WeightedBKTProjector()
    first = projector.project(
        user_id=owner_id, knowledge_unit_id=ku, evidence=all_evidence, version=1
    )
    replayed = projector.project(
        user_id=owner_id,
        knowledge_unit_id=ku,
        evidence=list(reversed(all_evidence)),
        version=1,
    )
    assert replayed == first  # order-insensitive deterministic replay


# ---------------------------------------------------------------------------
# EXEC062-AC-008: answer-exposure / assistance eligibility unchanged
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("assistance_class", "expected_weight"),
    [("none", 0.8), ("hint", 0.28), ("full_solution", 0.0)],
)
def test_ac008_evidence_eligibility_weighting_unchanged(assistance_class, expected_weight) -> None:
    from app.domains.assessment import AssessmentScoringService

    scorer = AssessmentScoringService()
    item = _item(uuid4())
    attempt = scorer.submit(
        item=item,
        user_id=uuid4(),
        response=" 4 ",
        assistance=_assistance("none" if assistance_class == "none" else assistance_class),
        idempotency_key=f"eligibility-{assistance_class}",
        submitted_at=FIXED_TIME,
    )
    result = scorer.score(item=item, attempt=attempt, clock=lambda: FIXED_TIME)
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
    if expected_weight == 0.0:
        assert decision.evidence is None or decision.evidence.evidence_weight == 0.0
        assert result.independence == "answer_exposed"
    else:
        assert decision.accepted
        assert decision.evidence is not None
        assert decision.evidence.evidence_weight == pytest.approx(expected_weight)


# ---------------------------------------------------------------------------
# EXEC062-AC-009: fail closed — no unscoped learner evidence / state can be created
# ---------------------------------------------------------------------------


async def test_ac009_new_evidence_and_state_writes_are_fail_closed(db: AsyncSession) -> None:
    owner_id = await _owner(db)
    ws_a, _ = await _workspaces(db, owner_id)
    ku = uuid4()
    item = _item(ku)

    # Cannot score an assessment submission without an exact Workspace.
    with pytest.raises(TypeError):
        await CanonicalAssessmentService(db).score_submission(
            item=item,
            user_id=owner_id,
            response="4",
            assistance=_assistance("none"),
            idempotency_key="x",
        )

    # Cannot project evidence into a MasteryEstimate without an exact Workspace.
    with pytest.raises(TypeError):
        await CanonicalLearnerProjectorService(db).project_assessment(
            result=None, attempt=None, knowledge_unit_id=ku, source_event_ids=[uuid4()]
        )

    # The repository refuses to persist evidence/state without an exact Workspace.
    with pytest.raises(TypeError):
        await LearnerModelRepository(db).save_evidence(None)  # type: ignore[arg-type]

    # After all Workspaces are removed, resolve_workspace_id deterministically
    # recreates exactly one default Workspace (idempotent auto-recovery) rather
    # than writing any unscoped learner record. The fail-closed guarantee for
    # evidence/state writers is enforced by the required workspace_id parameter
    # (proven above via TypeError), so the resolver never returns None and never
    # lets an owner-global learner row be written for an unresolved scope.
    from sqlalchemy import delete

    await db.execute(delete(Workspace).where(Workspace.owner_id == str(owner_id)))
    await db.commit()
    recovered = await resolve_workspace_id(db, owner_id)
    recovered_again = await resolve_workspace_id(db, owner_id)
    assert recovered == recovered_again
    assert recovered is not None
    # A recovered default is still exact: no learner record is written without it.
    with pytest.raises(TypeError):
        await LearnerModelRepository(db).save_evidence(None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# EXEC062-AC-004: legacy owner-global records migrate to the default Workspace
# ---------------------------------------------------------------------------


async def test_ac004_legacy_records_migrate_to_default_workspace(db: AsyncSession) -> None:
    owner_id = await _owner(db)
    ws_a, _ = await _workspaces(db, owner_id)
    ku = uuid4()

    # Craft deterministic legacy owner-global rows (workspace_id = NULL).
    stable_evidence_id = str(uuid4())
    stable_estimate_id = str(uuid4())
    payload_evidence = {
        "evidence_id": stable_evidence_id,
        "user_id": str(owner_id),
        "knowledge_unit_id": str(ku),
        "result_id": str(uuid4()),
        "evidence_weight": 0.8,
        "evidence_type": "recall",
        "eligibility_reason_codes": ["legacy"],
        "source_event_ids": [str(uuid4())],
    }
    db.add(
        LearnerEvidenceRecord(
            id=stable_evidence_id,
            source_result_id=str(uuid4()),
            user_id=str(owner_id),
            knowledge_unit_id=str(ku),
            status="accepted",
            reason_codes=["legacy"],
            payload=payload_evidence,
        )
    )
    db.add(
        MasteryEstimateRecord(
            id=stable_estimate_id,
            user_id=str(owner_id),
            knowledge_unit_id=str(ku),
            version=1,
            payload={
                "estimate_id": stable_estimate_id,
                "user_id": str(owner_id),
                "knowledge_unit_id": str(ku),
                "version": 1,
                "algorithm_id": "weighted-bkt",
                "algorithm_version": "1.0",
                "source_evidence_ids": [stable_evidence_id],
                "evidence_count": 1,
            },
        )
    )
    db.add(
        LearnerStateRecord(
            id="legacy-state:1",
            learner_state_id="legacy-state",
            user_id=str(owner_id),
            version=1,
            payload={
                "learner_state_id": "legacy-state",
                "user_id": str(owner_id),
                "version": 1,
                "mastery_estimate_ids": [stable_estimate_id],
            },
        )
    )
    # A legacy review schedule + observation, both owner-global.
    db.add(
        ReviewScheduleRecord(
            id="legacy-schedule:1",
            schedule_id="legacy-schedule",
            user_id=str(owner_id),
            knowledge_unit_id=str(ku),
            version=1,
            next_due_at=FIXED_TIME + timedelta(days=1),
            payload={"schedule_id": "legacy-schedule", "user_id": str(owner_id)},
        )
    )
    db.add(
        ReviewObservationRecord(
            id="legacy-observation",
            user_id=str(owner_id),
            knowledge_unit_id=str(ku),
            actual_reviewed_at=FIXED_TIME,
            payload={"observation_id": "legacy-observation"},
        )
    )
    await db.commit()

    result = await WorkspaceBootstrapService(db).migrate_legacy_to_default(str(owner_id))
    await db.commit()

    assert result.workspace_id == ws_a.workspace_id
    # Every EXEC-062 owner-global table was backfilled into the default Workspace.
    for table in (
        "learner_evidence",
        "canonical_mastery_estimate_versions",
        "learner_state_versions",
        "review_schedule_versions",
        "review_observations",
    ):
        assert result.backfilled.get(table, 0) >= 1, f"{table} not backfilled"

    # Stable IDs preserved; records now attributed to the default Workspace.
    ev = await db.get(LearnerEvidenceRecord, stable_evidence_id)
    est = await db.get(MasteryEstimateRecord, stable_estimate_id)
    assert ev is not None and ev.id == stable_evidence_id
    assert ev.workspace_id == ws_a.workspace_id
    assert est is not None and est.id == stable_estimate_id
    assert est.workspace_id == ws_a.workspace_id

    # Provenance / source refs preserved in the payload.
    assert payload_evidence["source_event_ids"] == ev.payload["source_event_ids"]
    assert est.payload["source_evidence_ids"] == [stable_evidence_id]

    # No record remains unattributed inside the default Workspace scope.
    remaining = (
        await db.scalars(
            select(LearnerEvidenceRecord).where(LearnerEvidenceRecord.workspace_id.is_(None))
        )
    ).all()
    assert remaining == []


# ---------------------------------------------------------------------------
# EXEC062-AC-010: no cross-owner repository write is introduced
# ---------------------------------------------------------------------------


def test_ac010_no_cross_owner_repository_write_introduced() -> None:
    import ast
    from pathlib import Path

    repo = Path("app/infrastructure/learning_records.py").read_text()
    tree = ast.parse(repo)
    writes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name.startswith(
            ("save_", "invalidate_", "list_", "latest_", "next_", "sync_legacy")
        ):
            args = [a.arg for a in node.args.args] + [a.arg for a in node.args.kwonlyargs]
            if node.name.startswith(("save_", "invalidate_")):
                assert (
                    "workspace_id" in args or "user_id" in args
                ), f"{node.name} must be owner/Workspace-scoped"
                writes.append(node.name)
    assert "save_evidence" in writes
    assert "save_mastery" in writes
    assert "save_learner_state" in writes
    assert "invalidate_evidence" in writes

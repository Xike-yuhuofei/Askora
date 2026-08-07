from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.contracts import (
    DecisionAlgorithm,
    DecisionExperiment,
    DecisionInput,
    DecisionTrace,
    EventActor,
    EventContext,
    EventPrivacy,
    EventProvenance,
    EventTrace,
    LearningEventEnvelope,
)


def make_event(
    *,
    aggregate_id: UUID | None = None,
    aggregate_version: int = 1,
    sequence: int = 1,
    idempotency_key: str | None = None,
    correlation_id: UUID | None = None,
) -> LearningEventEnvelope:
    now = datetime.now(timezone.utc)
    return LearningEventEnvelope(
        event_id=uuid4(),
        event_type="ResponseSubmitted",
        aggregate_type="Attempt",
        aggregate_id=aggregate_id or uuid4(),
        aggregate_version=aggregate_version,
        sequence=sequence,
        occurred_at=now,
        recorded_at=now,
        idempotency_key=idempotency_key or f"event:{uuid4()}",
        correlation_id=correlation_id or uuid4(),
        actor=EventActor(actor_type="learner", actor_id="local-user"),
        context=EventContext(user_id=uuid4(), knowledge_unit_ids=[], content_revision_ids=[]),
        payload={"assistance_snapshot": {"answer_visible": False}},
        provenance=EventProvenance(source="domain"),
        trace=EventTrace(trace_id="trace-ledger"),
        privacy=EventPrivacy(
            classification="personal",
            external_processing=False,
            retention_class="core_learning",
        ),
    )


def make_decision(*, entity_id: UUID | None = None, version: int = 1) -> DecisionTrace:
    return DecisionTrace(
        decision_id=uuid4(),
        decision_type="TeachingActionSelected",
        owner_system="teaching_policy",
        inputs=[
            DecisionInput(
                entity_type="LearnerState", entity_id=entity_id or uuid4(), version=version
            )
        ],
        candidates=[{"action": "hint"}, {"action": "practice"}],
        selected={"action": "practice"},
        constraints=[{"kind": "hard", "answer_exposure_max": 2}],
        reason_codes=["TEACH_PRACTICE_READY"],
        confidence=None,
        algorithm=DecisionAlgorithm(
            algorithm_id="teaching-policy",
            algorithm_version="1.0",
            model_inference_ids=[],
            prompt_versions=[],
        ),
        experiment=DecisionExperiment(),
        created_at=datetime.now(timezone.utc),
        correlation_id=uuid4(),
        trace_id="trace-decision-ledger",
    )

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.contracts.planning import ReviewObservation
from app.domains.review_scheduler import ReviewScheduler, project_due

NOW = datetime(2026, 8, 7, 10, 0, tzinfo=timezone.utc)


def _observation(
    *,
    independence: str = "independent",
    outcome: str = "success",
    answer_seen: bool = False,
) -> ReviewObservation:
    return ReviewObservation(
        observation_id=uuid4(),
        user_id=uuid4(),
        knowledge_unit_id=uuid4(),
        observed_at=NOW,
        actual_reviewed_at=NOW - timedelta(minutes=2),
        retrieval_required=True,
        independence=independence,
        hint_level=0 if independence == "independent" else 2,
        answer_seen_before_attempt=answer_seen,
        assessment_confidence=1.0,
        outcome=outcome,
        delay_seconds=86_400,
        source_evidence_id=uuid4(),
        source_event_ids=[uuid4()],
    )


def test_review_independent_recall_and_answer_exposed_update_differently() -> None:
    scheduler = ReviewScheduler()
    independent = _observation()
    exposed = independent.model_copy(
        update={
            "observation_id": uuid4(),
            "independence": "answer_exposed",
            "answer_seen_before_attempt": True,
            "hint_level": 3,
        }
    )
    assisted = independent.model_copy(
        update={"observation_id": uuid4(), "independence": "assisted", "hint_level": 2}
    )
    independent_result = scheduler.update(observation=independent, prior=None, version=1)
    assisted_result = scheduler.update(observation=assisted, prior=None, version=1)
    exposed_result = scheduler.update(observation=exposed, prior=None, version=1)
    assert independent_result.schedule.stability > assisted_result.schedule.stability
    assert assisted_result.schedule.evidence_quality == pytest.approx(0.35)
    assert independent_result.schedule.stability > exposed_result.schedule.stability
    assert independent_result.schedule.next_due_at > exposed_result.schedule.next_due_at
    assert independent_result.schedule.evidence_quality == 1.0
    assert exposed_result.schedule.evidence_quality == 0.0
    assert exposed_result.schedule.last_valid_retrieval_at is None


def test_review_failure_shortens_interval_and_model_failure_falls_back() -> None:
    scheduler = ReviewScheduler()
    first = scheduler.update(observation=_observation(), prior=None, version=1).schedule
    failure = _observation(outcome="failure").model_copy(
        update={"user_id": first.user_id, "knowledge_unit_id": first.knowledge_unit_id}
    )
    failed = scheduler.update(observation=failure, prior=first, version=2)
    fallback = scheduler.update(
        observation=_observation(),
        prior=None,
        version=1,
        parameters={"broken": -1.0},
    )
    assert failed.schedule.stability < first.stability
    assert "RETRIEVAL_FAILURE_SHORTENED" in failed.reason_codes
    assert fallback.schedule.memory_model == "simple-exponential"
    assert "MEMORY_MODEL_FALLBACK" in fallback.reason_codes


def test_review_scheduler_and_due_projection_are_deterministic_without_row_mutation() -> None:
    scheduler = ReviewScheduler()
    observation = _observation()
    first = scheduler.update(observation=observation, prior=None, version=1)
    replayed = scheduler.update(observation=observation, prior=None, version=1)
    before = first.schedule.model_dump()
    due = project_due(first.schedule, at=first.schedule.next_due_at + timedelta(days=2))
    assert replayed == first
    assert due.status == "overdue"
    assert due.recommended_due_at == first.schedule.next_due_at
    assert first.schedule.model_dump() == before
    assert observation.actual_reviewed_at != first.schedule.next_due_at


def test_review_desired_retention_is_versioned_and_clamped() -> None:
    result = ReviewScheduler().update(
        observation=_observation(),
        prior=None,
        version=1,
        desired_retention=0.999,
    )
    assert result.schedule.desired_retention == pytest.approx(0.95)
    assert "DESIRED_RETENTION_CLAMPED" in result.reason_codes

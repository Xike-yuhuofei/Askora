"""Strict public contract coverage for SYS06-ACT-AC-002."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.contracts.activity_lifecycle import (
    CompleteLearningActivityV1,
    LearningActivityStateV1,
    StartLearningActivityV1,
)


def test_activity_lifecycle_contract_is_strict_and_versioned() -> None:
    activity_id = uuid4()
    command = StartLearningActivityV1(
        activity_id=activity_id,
        expected_state_version=1,
        idempotency_key="start-1",
    )
    assert command.schema_version == "1.0"

    state = LearningActivityStateV1(
        activity_id=activity_id,
        version=1,
        plan_id=uuid4(),
        plan_version=1,
        status="planned",
        transition_reason="ACTIVITY_CREATED_FROM_PLAN",
        actor_type="system",
        correlation_id=uuid4(),
        created_at=datetime.now(timezone.utc),
    )
    assert state.previous_status is None

    with pytest.raises(ValidationError):
        StartLearningActivityV1.model_validate(
            {
                **command.model_dump(mode="json"),
                "target_status": "active",
            }
        )


def test_completion_requires_explicit_transcript_ref() -> None:
    with pytest.raises(ValidationError):
        CompleteLearningActivityV1(
            activity_id=uuid4(),
            expected_state_version=2,
            completion_intent="learner_finished",
            transcript_turn_refs=(),
            idempotency_key="complete-1",
        )

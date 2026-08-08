"""EXEC-023 public contract and explicit readiness-state tests."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.contracts.adaptive import VersionedRef
from app.contracts.book_learning import BookLearningOwnerRefV1, BookLearningReadinessV1


def test_exec023_readiness_contract_accepts_only_frozen_states_and_exact_refs() -> None:
    states = (
        "PROCESSING",
        "CONTENT_PARTIAL",
        "READY_FOR_GOAL",
        "GOAL_CONFIRMATION_REQUIRED",
        "DIAGNOSIS_REQUIRED",
        "DIAGNOSING",
        "PLAN_READY",
        "READY_TO_LEARN",
        "BLOCKED",
    )
    ref = BookLearningOwnerRefV1(
        owner_system="SYS06",
        ref=VersionedRef(entity_type="LearningPlan", entity_id=str(uuid4()), version=1),
        status="active",
    )
    for state in states:
        result = BookLearningReadinessV1(
            document_id=uuid4(),
            state=state,
            owner_refs=(ref,),
            reason_codes=("EXACT_OWNER_STATE",),
            next_commands=(),
            generated_at=datetime.now(timezone.utc),
            correlation_id="exec023",
        )
        assert result.state == state

    with pytest.raises(ValidationError):
        BookLearningReadinessV1(
            document_id=uuid4(),
            state="READY_BY_UI",
            owner_refs=(ref,),
            reason_codes=("INVALID",),
            next_commands=(),
            generated_at=datetime.now(timezone.utc),
            correlation_id="exec023",
        )


def test_exec023_readiness_requires_reason_codes() -> None:
    with pytest.raises(ValidationError):
        BookLearningReadinessV1(
            document_id=uuid4(),
            state="BLOCKED",
            owner_refs=(),
            reason_codes=(),
            next_commands=(),
            generated_at=datetime.now(timezone.utc),
            correlation_id="exec023",
        )

"""EXEC-023 public contract and explicit readiness-state tests."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.contracts.adaptive import VersionedRef
from app.contracts.book_learning import (
    BookLearningOwnerRefV1,
    BookLearningReadinessV1,
    LearnerVisibleDiagnosticItemV1,
    StartBookTeachingRequestV1,
)


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


def test_exec025_learner_visible_diagnostic_contract_has_no_grader_fields() -> None:
    """UI02B1-AC-005: the public learner item cannot serialize grader-only data."""

    item = LearnerVisibleDiagnosticItemV1(
        item_ref=VersionedRef(
            entity_type="AssessmentItem",
            entity_id="11111111-1111-4111-8111-111111111111",
            version="1.0",
        ),
        need_id="22222222-2222-4222-8222-222222222222",
        need_version=2,
        item_type="multiple_choice",
        prompt="Which statement is supported by the source?",
        options=("A", "B"),
    )
    payload = item.model_dump(mode="json")

    assert payload["prompt"].startswith("Which")
    assert payload["options"] == ["A", "B"]
    assert not {"answer_key", "correct_answer", "rubric", "explanation"} & payload.keys()


def test_exec026_system_start_has_no_client_owned_hidden_text() -> None:
    common = {
        "goal_id": uuid4(),
        "plan_id": uuid4(),
        "plan_version": 1,
        "activity_id": uuid4(),
        "turn_id": "system-start-1",
        "turn_kind": "system_start",
        "idempotency_key": "exec026:system-start",
    }
    request = StartBookTeachingRequestV1(**common)
    assert request.learner_text is None

    with pytest.raises(ValidationError, match="system_start text is server-owned"):
        StartBookTeachingRequestV1(**common, learner_text="hidden prompt")


def test_exec026_learner_turn_requires_real_text() -> None:
    with pytest.raises(ValidationError, match="learner turn requires learner_text"):
        StartBookTeachingRequestV1(
            goal_id=uuid4(),
            plan_id=uuid4(),
            plan_version=1,
            activity_id=uuid4(),
            turn_id="learner-1",
            turn_kind="learner",
            learner_text="  ",
            idempotency_key="exec026:learner-empty",
        )

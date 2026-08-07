"""SYS05-owned independent-validation obligation state transitions."""

from __future__ import annotations

from uuid import NAMESPACE_URL, uuid5

from app.contracts.adaptive import (
    AssessmentAttemptV03,
    AssessmentResultV03,
    AssistanceState,
    VersionedRef,
)
from app.domains.teaching_policy.models import (
    IndependentValidationRecord,
    ValidationObligationStatus,
)


def _attempt_ref(attempt: AssessmentAttemptV03) -> VersionedRef:
    return VersionedRef(
        entity_type="assessment_attempt",
        entity_id=str(attempt.attempt_id),
        version=attempt.attempt_schema_version,
    )


def _result_ref(result: AssessmentResultV03) -> VersionedRef:
    return VersionedRef(
        entity_type="assessment_result",
        entity_id=str(result.result_id),
        version=result.result_version,
    )


def advance_validation_obligation(
    current: IndependentValidationRecord | None,
    *,
    attempt: AssessmentAttemptV03,
    result: AssessmentResultV03,
) -> IndependentValidationRecord | None:
    """Create/satisfy only from accepted actual-assistance assessment facts."""

    attempt_ref = _attempt_ref(attempt)
    result_ref = _result_ref(result)
    if result.attempt_id != attempt.attempt_id:
        return current

    independent_success = (
        result.passed is True
        and result.reviewer_result == "accepted"
        and attempt.assistance.assistance_state is AssistanceState.INDEPENDENT
        and result.assistance.assistance_state is AssistanceState.INDEPENDENT
    )
    if current is not None and current.status is ValidationObligationStatus.REQUIRED:
        fresh = (
            attempt.submitted_at > current.created_at
            and attempt_ref.entity_id != current.source_attempt_ref.entity_id
        )
        if independent_success and fresh:
            payload = current.model_dump()
            payload.update(
                {
                    "status": ValidationObligationStatus.SATISFIED,
                    "satisfied_at": result.created_at,
                    "satisfying_attempt_ref": attempt_ref,
                    "satisfying_result_ref": result_ref,
                    "reason_codes": (
                        *current.reason_codes,
                        "FRESH_INDEPENDENT_VALIDATION_ACCEPTED",
                    ),
                }
            )
            return IndependentValidationRecord.model_validate(payload)
        return current

    if current is not None:
        return current

    experienced_states = {
        attempt.assistance.assistance_state,
        result.assistance.assistance_state,
    }
    exposed_success = (
        result.passed is True
        and result.reviewer_result == "accepted"
        and bool(experienced_states & {AssistanceState.ASSISTED, AssistanceState.ANSWER_EXPOSED})
    )
    if not exposed_success:
        return None
    state = (
        AssistanceState.ANSWER_EXPOSED
        if AssistanceState.ANSWER_EXPOSED in experienced_states
        else AssistanceState.ASSISTED
    )
    obligation_id = uuid5(
        NAMESPACE_URL,
        f"askora:validation:{attempt.attempt_id}:{result.result_id}:{state.value}",
    )
    return IndependentValidationRecord(
        obligation_id=obligation_id,
        status=ValidationObligationStatus.REQUIRED,
        created_at=result.created_at,
        source_attempt_ref=attempt_ref,
        source_result_ref=result_ref,
        assistance_state=state,
        reason_codes=(f"{state.value}_SUCCESS_REQUIRES_INDEPENDENT_VALIDATION",),
    )

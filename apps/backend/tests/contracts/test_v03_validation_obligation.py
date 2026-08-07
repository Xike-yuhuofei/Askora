from __future__ import annotations

from app.contracts.adaptive import AssistanceState
from app.domains.teaching_policy.models import ValidationObligationStatus
from app.domains.teaching_policy.validation_obligation import advance_validation_obligation
from tests.fixtures.v03_policy_factory import make_assessment_pair


def test_assisted_success_creates_but_does_not_satisfy_obligation() -> None:
    attempt, result = make_assessment_pair(
        name="assisted", assistance_state=AssistanceState.ASSISTED
    )
    obligation = advance_validation_obligation(None, attempt=attempt, result=result)
    assert obligation is not None
    assert obligation.status is ValidationObligationStatus.REQUIRED
    assert obligation.assistance_state is AssistanceState.ASSISTED
    assert obligation.satisfying_attempt_ref is None

    retry_attempt, retry_result = make_assessment_pair(
        name="assisted-retry",
        assistance_state=AssistanceState.ASSISTED,
        seconds_after_base=120,
    )
    unchanged = advance_validation_obligation(
        obligation, attempt=retry_attempt, result=retry_result
    )
    assert unchanged == obligation


def test_answer_exposed_success_creates_required_obligation() -> None:
    attempt, result = make_assessment_pair(
        name="answer-exposed", assistance_state=AssistanceState.ANSWER_EXPOSED
    )
    obligation = advance_validation_obligation(None, attempt=attempt, result=result)
    assert obligation is not None
    assert obligation.status is ValidationObligationStatus.REQUIRED
    assert obligation.assistance_state is AssistanceState.ANSWER_EXPOSED


def test_only_fresh_independent_accepted_result_satisfies_obligation() -> None:
    source_attempt, source_result = make_assessment_pair(
        name="source-assisted", assistance_state=AssistanceState.ASSISTED
    )
    obligation = advance_validation_obligation(None, attempt=source_attempt, result=source_result)
    assert obligation is not None

    stale_attempt, stale_result = make_assessment_pair(
        name="stale-independent",
        assistance_state=AssistanceState.INDEPENDENT,
        seconds_after_base=30,
    )
    assert (
        advance_validation_obligation(obligation, attempt=stale_attempt, result=stale_result)
        == obligation
    )

    fresh_attempt, fresh_result = make_assessment_pair(
        name="fresh-independent",
        assistance_state=AssistanceState.INDEPENDENT,
        seconds_after_base=180,
    )
    satisfied = advance_validation_obligation(
        obligation, attempt=fresh_attempt, result=fresh_result
    )
    assert satisfied is not None
    assert satisfied.status is ValidationObligationStatus.SATISFIED
    assert satisfied.satisfying_attempt_ref is not None
    assert satisfied.satisfying_result_ref is not None
    assert fresh_result.assessment_confidence != fresh_result.diagnosis.diagnostic_confidence


def test_assistance_snapshot_mismatch_fails_conservative() -> None:
    attempt, _ = make_assessment_pair(
        name="mismatch-attempt", assistance_state=AssistanceState.ASSISTED
    )
    _, independent_result = make_assessment_pair(
        name="mismatch-result", assistance_state=AssistanceState.INDEPENDENT
    )
    result_payload = independent_result.model_dump()
    result_payload["attempt_id"] = attempt.attempt_id
    result = type(independent_result).model_validate(result_payload)
    obligation = advance_validation_obligation(None, attempt=attempt, result=result)
    assert obligation is not None
    assert obligation.status is ValidationObligationStatus.REQUIRED
    assert obligation.assistance_state is AssistanceState.ASSISTED

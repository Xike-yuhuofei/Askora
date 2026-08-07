from __future__ import annotations

from datetime import timedelta

import pytest

from app.contracts.adaptive import (
    AssistanceState,
    InteractionMove,
    StrategyFamily,
    ValidationObligation,
)
from app.domains.teaching_policy.evidence import EvidenceSignal, EvidenceSignalKind
from app.domains.teaching_policy.kernel import TeachingPolicyKernel
from app.domains.teaching_policy.models import PolicyRuntimeProfile, SequentialPolicyState
from app.domains.teaching_policy.sequential import SequentialTeachingPolicy
from app.domains.teaching_policy.time_source import FixedTimeSource
from app.domains.teaching_policy.validation_obligation import advance_validation_obligation
from tests.fixtures.v03_policy_factory import (
    NOW,
    load_cases,
    load_profile,
    make_assessment_pair,
    make_bundle,
    make_context,
    ref,
    with_previous_action,
)


def signal(
    kind: EvidenceSignalKind, name: str, *, delay_seconds: int | None = None
) -> EvidenceSignal:
    attributes = {}
    if delay_seconds is not None:
        attributes["delay_started_at"] = (NOW - timedelta(seconds=delay_seconds)).isoformat()
    material_kind = kind not in {
        EvidenceSignalKind.CHAT_TURN,
        EvidenceSignalKind.WORDING_VARIATION,
        EvidenceSignalKind.RERENDER,
        EvidenceSignalKind.SAME_CONTEXT_REEVALUATION,
        EvidenceSignalKind.WALL_CLOCK_DRIFT,
    }
    return EvidenceSignal(
        signal_id=name,
        kind=kind,
        evidence_ref=ref("evidence", name) if material_kind else None,
        occurred_at=NOW,
        attributes=attributes,
    )


def initial_state(case: dict[str, object], profile: PolicyRuntimeProfile) -> SequentialPolicyState:
    decision = TeachingPolicyKernel().decide(
        context=make_context(case), bundle=make_bundle(profile), profile=profile
    )
    return SequentialPolicyState(
        previous_action=decision.action,
        previous_trace=decision.trace,
        evidence_opportunities_since_transition=0,
    )


@pytest.mark.parametrize("case", load_cases("sequential_replay.json"), ids=lambda c: c["case_id"])
def test_fixed_sequential_replay_fixtures(case: dict[str, object]) -> None:
    profile = load_profile()
    state = initial_state(case["initial"], profile)  # type: ignore[arg-type]
    context = with_previous_action(
        make_context(case["next"]),  # type: ignore[arg-type]
        state.previous_action,
    )
    signals = tuple(
        signal(EvidenceSignalKind(kind), f"{case['case_id']}-{index}")
        for index, kind in enumerate(case["signals"])  # type: ignore[arg-type]
    )
    policy = SequentialTeachingPolicy(FixedTimeSource(NOW))
    first = policy.decide(
        context=context,
        bundle=make_bundle(profile),
        profile=profile,
        state=state,
        signals=signals,
    )
    second = policy.decide(
        context=context,
        bundle=make_bundle(profile),
        profile=profile,
        state=state,
        signals=signals,
    )
    assert first == second
    assert first.decision.action.strategy_family is StrategyFamily(str(case["expected_family"]))
    assert first.transition_reason_code == case["expected_reason"]
    assert first.decision.trace.anti_oscillation_decision is not None


def test_minimum_dwell_counts_evidence_opportunities_not_turns() -> None:
    profile = load_profile()
    state = initial_state({"case_id": "dwell-start", "mastery": 0.2}, profile)
    policy = SequentialTeachingPolicy(FixedTimeSource(NOW))
    context_one = with_previous_action(
        make_context({"case_id": "dwell-one", "mastery": 0.4, "assisted_success": True}),
        state.previous_action,
    )
    held = policy.decide(
        context=context_one,
        bundle=make_bundle(profile),
        profile=profile,
        state=state,
        signals=(signal(EvidenceSignalKind.ASSESSMENT_RESULT, "assessment-one"),),
    )
    assert held.transition_reason_code == "HOLD_MINIMUM_DWELL_EVIDENCE_OPPORTUNITY"
    assert held.next_state.evidence_opportunities_since_transition == 1

    context_two = with_previous_action(
        make_context({"case_id": "dwell-two", "mastery": 0.4, "assisted_success": True}),
        held.next_state.previous_action,
    )
    switched = policy.decide(
        context=context_two,
        bundle=make_bundle(profile),
        profile=profile,
        state=held.next_state,
        signals=(signal(EvidenceSignalKind.LEARNER_STATE_UPDATE, "learner-update"),),
    )
    assert switched.decision.action.strategy_family is StrategyFamily.GUIDED_PRACTICE
    assert switched.transition_reason_code == "TRANSITION_LEARNER_STATE_UPDATE"
    assert switched.next_state.evidence_opportunities_since_transition == 0


def test_duplicate_evidence_does_not_create_a_second_dwell_opportunity() -> None:
    profile = load_profile()
    state = initial_state({"case_id": "duplicate-start", "mastery": 0.2}, profile)
    policy = SequentialTeachingPolicy(FixedTimeSource(NOW))
    evidence = signal(EvidenceSignalKind.ASSESSMENT_RESULT, "same-assessment")
    context_one = with_previous_action(
        make_context({"case_id": "duplicate-one", "mastery": 0.4, "assisted_success": True}),
        state.previous_action,
    )
    first = policy.decide(
        context=context_one,
        bundle=make_bundle(profile),
        profile=profile,
        state=state,
        signals=(evidence,),
    )
    context_two = with_previous_action(
        make_context({"case_id": "duplicate-two", "mastery": 0.4, "assisted_success": True}),
        first.next_state.previous_action,
    )
    second = policy.decide(
        context=context_two,
        bundle=make_bundle(profile),
        profile=profile,
        state=first.next_state,
        signals=(evidence,),
    )
    assert second.transition_reason_code == "HOLD_MINIMUM_DWELL_EVIDENCE_OPPORTUNITY"
    assert second.next_state.evidence_opportunities_since_transition == 1


def test_explicit_user_request_has_stable_priority_independent_of_signal_order() -> None:
    profile_payload = load_profile().model_dump()
    profile_payload["minimum_dwell_opportunities"] = 0
    profile = PolicyRuntimeProfile.model_validate(profile_payload)
    state = initial_state({"case_id": "priority-start", "mastery": 0.2}, profile)
    context = with_previous_action(
        make_context({"case_id": "priority-next", "mastery": 0.2, "direct_answer_request": True}),
        state.previous_action,
    )
    signals = (
        signal(EvidenceSignalKind.ASSESSMENT_RESULT, "priority-assessment"),
        signal(EvidenceSignalKind.EXPLICIT_USER_REQUEST, "priority-user"),
    )
    policy = SequentialTeachingPolicy(FixedTimeSource(NOW))
    first = policy.decide(
        context=context,
        bundle=make_bundle(profile),
        profile=profile,
        state=state,
        signals=signals,
    )
    second = policy.decide(
        context=context,
        bundle=make_bundle(profile),
        profile=profile,
        state=state,
        signals=tuple(reversed(signals)),
    )
    assert first.decision.action.interaction_moves == (InteractionMove.DIRECT_ANSWER_OVERRIDE,)
    assert first.transition_reason_code == second.transition_reason_code
    assert first.transition_reason_code == "TRANSITION_EXPLICIT_USER_REQUEST"


def test_fixed_time_controls_meaningful_delay_and_few_seconds_are_non_material() -> None:
    profile_payload = load_profile().model_dump()
    profile_payload.update({"minimum_dwell_opportunities": 0, "switch_margin": 0.0})
    profile = PolicyRuntimeProfile.model_validate(profile_payload)
    state = initial_state({"case_id": "delay-start", "mastery": 0.2}, profile)
    context = with_previous_action(
        make_context(
            {
                "case_id": "delay-next",
                "mastery": 0.4,
                "review_context": True,
                "delayed_independent": True,
            }
        ),
        state.previous_action,
    )
    policy = SequentialTeachingPolicy(FixedTimeSource(NOW))
    short = policy.decide(
        context=context,
        bundle=make_bundle(profile),
        profile=profile,
        state=state,
        signals=(
            signal(EvidenceSignalKind.REVIEW_DELAY_TRANSITION, "short-delay", delay_seconds=5),
        ),
    )
    assert short.transition_reason_code == "HOLD_NO_MATERIAL_EVIDENCE"

    meaningful_signal = signal(
        EvidenceSignalKind.REVIEW_DELAY_TRANSITION,
        "meaningful-delay",
        delay_seconds=profile.meaningful_delay_seconds,
    )
    first = policy.decide(
        context=context,
        bundle=make_bundle(profile),
        profile=profile,
        state=state,
        signals=(meaningful_signal,),
    )
    second = policy.decide(
        context=context,
        bundle=make_bundle(profile),
        profile=profile,
        state=state,
        signals=(meaningful_signal,),
    )
    assert first == second
    assert first.decision.action.strategy_family is StrategyFamily.RETRIEVAL_PRACTICE
    assert first.transition_reason_code == "TRANSITION_MEANINGFUL_REVIEW_DELAY"


def test_unknown_low_confidence_uses_conservative_probe_without_guessing() -> None:
    profile_payload = load_profile().model_dump()
    profile_payload.update({"minimum_dwell_opportunities": 0, "switch_margin": 0.0})
    profile = PolicyRuntimeProfile.model_validate(profile_payload)
    state = initial_state({"case_id": "unknown-start", "mastery": 0.2}, profile)
    context = with_previous_action(
        make_context(
            {
                "case_id": "unknown-next",
                "mastery": 0.2,
                "error_type": "UNKNOWN",
                "diagnostic_confidence": 0.2,
                "needs_probe": True,
            }
        ),
        state.previous_action,
    )
    result = SequentialTeachingPolicy(FixedTimeSource(NOW)).decide(
        context=context,
        bundle=make_bundle(profile),
        profile=profile,
        state=state,
        signals=(signal(EvidenceSignalKind.DIAGNOSTIC_PROBE, "unknown-probe"),),
    )
    assert context.error_type.value == "UNKNOWN"
    assert result.decision.action.strategy_family is StrategyFamily.GUIDED_PRACTICE
    assert InteractionMove.SOCRATIC_PROBE in result.decision.action.interaction_moves


def test_open_validation_obligation_is_carried_by_sequential_action() -> None:
    profile = load_profile()
    state = initial_state({"case_id": "obligation-start", "mastery": 0.9}, profile)
    attempt, result = make_assessment_pair(
        name="obligation-assisted", assistance_state=AssistanceState.ASSISTED
    )
    obligation = advance_validation_obligation(None, attempt=attempt, result=result)
    assert obligation is not None
    state_payload = state.model_dump()
    state_payload["validation_obligation"] = obligation
    state = SequentialPolicyState.model_validate(state_payload)
    context = with_previous_action(
        make_context({"case_id": "obligation-next", "mastery": 0.9}),
        state.previous_action,
    )
    outcome = SequentialTeachingPolicy(FixedTimeSource(NOW)).decide(
        context=context,
        bundle=make_bundle(profile),
        profile=profile,
        state=state,
        signals=(),
    )
    assert (
        outcome.decision.action.validation_obligation
        is ValidationObligation.INDEPENDENT_VALIDATION_REQUIRED
    )

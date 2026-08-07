from __future__ import annotations

from app.contracts.adaptive import StrategyFamily
from app.domains.teaching_policy.evidence import EvidenceSignalKind
from app.domains.teaching_policy.models import PolicyRuntimeProfile
from app.domains.teaching_policy.sequential import SequentialTeachingPolicy
from app.domains.teaching_policy.time_source import FixedTimeSource
from tests.fixtures.v03_policy_factory import (
    NOW,
    load_profile,
    make_bundle,
    make_context,
    with_previous_action,
)
from tests.integration.test_v03_policy_sequential import initial_state, signal


def test_threshold_near_changes_do_not_oscillate_under_versioned_hysteresis() -> None:
    profile_payload = load_profile().model_dump()
    profile_payload.update({"minimum_dwell_opportunities": 0, "switch_margin": 100.0})
    profile = PolicyRuntimeProfile.model_validate(profile_payload)
    state = initial_state({"case_id": "hysteresis-start", "mastery": 0.2}, profile)
    context = with_previous_action(
        make_context({"case_id": "hysteresis-next", "mastery": 0.4, "assisted_success": True}),
        state.previous_action,
    )
    outcome = SequentialTeachingPolicy(FixedTimeSource(NOW)).decide(
        context=context,
        bundle=make_bundle(profile),
        profile=profile,
        state=state,
        signals=(signal(EvidenceSignalKind.ASSESSMENT_RESULT, "near-threshold"),),
    )
    assert outcome.decision.action.strategy_family is StrategyFamily.EXPLICIT_INSTRUCTION
    assert outcome.transition_reason_code == "HOLD_HYSTERESIS_SWITCH_MARGIN"


def test_repeated_near_threshold_replay_has_no_family_oscillation() -> None:
    profile_payload = load_profile().model_dump()
    profile_payload.update({"minimum_dwell_opportunities": 0, "switch_margin": 100.0})
    profile = PolicyRuntimeProfile.model_validate(profile_payload)
    state = initial_state({"case_id": "loop-start", "mastery": 0.2}, profile)
    policy = SequentialTeachingPolicy(FixedTimeSource(NOW))
    observed = []
    for index in range(20):
        context = with_previous_action(
            make_context(
                {
                    "case_id": f"loop-{index}",
                    "mastery": 0.4 if index % 2 == 0 else 0.2,
                    "assisted_success": index % 2 == 0,
                }
            ),
            state.previous_action,
        )
        outcome = policy.decide(
            context=context,
            bundle=make_bundle(profile),
            profile=profile,
            state=state,
            signals=(signal(EvidenceSignalKind.ASSESSMENT_RESULT, f"loop-evidence-{index}"),),
        )
        observed.append(outcome.decision.action.strategy_family)
        state = outcome.next_state
    assert set(observed) == {StrategyFamily.EXPLICIT_INSTRUCTION}


def test_hard_constraint_precedes_even_extreme_hysteresis() -> None:
    profile_payload = load_profile().model_dump()
    profile_payload.update({"minimum_dwell_opportunities": 999, "switch_margin": 100.0})
    profile = PolicyRuntimeProfile.model_validate(profile_payload)
    state = initial_state({"case_id": "hard-hysteresis-start", "mastery": 0.2}, profile)
    context = with_previous_action(
        make_context({"case_id": "hard-hysteresis-next", "mastery": 0.9, "activity_type": "exam"}),
        state.previous_action,
    )
    outcome = SequentialTeachingPolicy(FixedTimeSource(NOW)).decide(
        context=context,
        bundle=make_bundle(profile),
        profile=profile,
        state=state,
        signals=(),
    )
    assert outcome.decision.action.strategy_family is StrategyFamily.RETRIEVAL_PRACTICE
    assert outcome.transition_reason_code == "TRANSITION_HARD_CONSTRAINT_PRECEDENCE"

"""EXEC-042 production composition regression tests (section 九).

These tests drive the minimum-dwell / hysteresis / repeated-failure / hard-
constraint / UNKNOWN behavior through the REAL production decision composition
(LearningOrchestrationFacade._execute_adaptive_turn -> SequentialTeachingPolicy),
not through direct unit API calls. They reuse the deterministic policy fixtures.
"""

from __future__ import annotations

from app.domains.teaching_policy import TeachingPolicyKernel
from app.domains.teaching_policy.models import PolicyRuntimeProfile
from app.orchestration.learning_facade import CanonicalTurnRequest, LearningOrchestrationFacade
from tests.fixtures.v03_policy_factory import (
    load_profile,
    make_bundle,
    make_context,
    with_previous_action,
)


def _profile(**overrides) -> PolicyRuntimeProfile:
    payload = load_profile().model_dump()
    payload.update(overrides)
    return PolicyRuntimeProfile.model_validate(payload)


def _bundle(profile: PolicyRuntimeProfile):
    return make_bundle(profile)


def _bootstrap(case: dict, profile: PolicyRuntimeProfile):
    kernel = TeachingPolicyKernel()
    return kernel.decide(
        context=make_context(case), bundle=_bundle(profile), profile=profile
    )


def _facade_request(*, context, profile, previous_action, previous_trace):
    return CanonicalTurnRequest(
        session_id="comp-session",
        user_id="comp-user",
        text="continue",
        turn_id="comp-turn",
        subject="lesson",
        teaching_context_v03=context,
        policy_bundle_v03=_bundle(profile),
        policy_profile_v03=profile,
        adaptive_retrieval_candidates=(),
        previous_teaching_action_v03=previous_action,
        previous_decision_trace_v03=previous_trace,
    )


async def _run_second(context, profile, first):
    facade = LearningOrchestrationFacade()
    return await facade.run_turn(
        _facade_request(
            context=context,
            profile=profile,
            previous_action=first.action,
            previous_trace=first.trace,
        )
    )


async def test_exec042_production_minimum_dwell_holds_until_distinct_opportunity() -> None:
    """minimum dwell based on evidence opportunity, not chat turn, via production path."""
    profile = _profile(minimum_dwell_opportunities=2, switch_margin=0.0)
    first = _bootstrap({"case_id": "comp-dwell-boot", "mastery": 0.2}, profile)
    # Use a concrete (non-UNKNOWN) error_type so that exactly ONE material
    # opportunity (the assisted-success ASSISTANCE_EVENT) is projected; an
    # UNKNOWN error_type would also emit a DIAGNOSTIC_PROBE material signal and
    # artificially reach the dwell ceiling in a single turn.
    context = with_previous_action(
        make_context(
            {
                "case_id": "comp-dwell-next",
                "mastery": 0.4,
                "assisted_success": True,
                "error_type": "KNOWLEDGE_GAP",
            }
        ),
        first.action,
    )
    result = await _run_second(context, profile, first)
    trace = result.decision_trace_v03
    assert trace is not None
    anti = trace.anti_oscillation_decision
    assert anti is not None
    assert anti["decision"] == "HOLD"
    assert str(anti["reason_code"]).startswith("HOLD_")
    assert anti["evidence_opportunities_since_transition"] < 2


async def test_exec042_production_hysteresis_holds_below_switch_margin() -> None:
    """score delta below switch margin -> HOLD via production composition."""
    profile = _profile(minimum_dwell_opportunities=0, switch_margin=100.0)
    first = _bootstrap({"case_id": "comp-hys-boot", "mastery": 0.2}, profile)
    context = with_previous_action(
        make_context(
            {
                "case_id": "comp-dwell-next",
                "mastery": 0.4,
                "assisted_success": True,
                "error_type": "KNOWLEDGE_GAP",
            }
        ),
        first.action,
    )
    result = await _run_second(context, profile, first)
    trace = result.decision_trace_v03
    assert trace is not None
    anti = trace.anti_oscillation_decision
    assert anti is not None
    assert anti["decision"] == "HOLD"
    assert str(anti["reason_code"]).startswith("HOLD_")


async def test_exec042_production_repeated_failure_override() -> None:
    """repeated failure ceiling overrides sticky/dwell/hysteresis -> SWITCH."""
    profile = _profile(minimum_dwell_opportunities=999, switch_margin=100.0, failure_ceiling=3)
    first = _bootstrap(
        {"case_id": "comp-fail-boot", "mastery": 0.2, "consecutive_failures": 0}, profile
    )
    context = with_previous_action(
        make_context(
            {
                "case_id": "comp-fail-next",
                "mastery": 0.2,
                "assisted_success": True,
                "consecutive_failures": 5,
            }
        ),
        first.action,
    )
    result = await _run_second(context, profile, first)
    trace = result.decision_trace_v03
    assert trace is not None
    anti = trace.anti_oscillation_decision
    assert anti is not None
    assert anti["decision"] == "SWITCH"
    assert "OVERRIDE" in str(anti["reason_code"])


async def test_exec042_production_unknown_conservative_probe() -> None:
    """UNKNOWN diagnosis keeps a conservative probe path via production composition."""
    profile = _profile(minimum_dwell_opportunities=0, switch_margin=0.0)
    first = _bootstrap({"case_id": "comp-unk-boot", "mastery": 0.2}, profile)
    context = with_previous_action(
        make_context(
            {
                "case_id": "comp-unk-next",
                "mastery": 0.2,
                "error_type": "UNKNOWN",
                "needs_probe": True,
            }
        ),
        first.action,
    )
    result = await _run_second(context, profile, first)
    action = result.teaching_action_v03
    assert action is not None
    trace = result.decision_trace_v03
    assert trace is not None
    assert trace.anti_oscillation_decision is not None

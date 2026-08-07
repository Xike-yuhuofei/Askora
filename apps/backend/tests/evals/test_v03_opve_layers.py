from __future__ import annotations

from app.contracts.adaptive import StrategyFamily
from app.domains.teaching_policy.candidates import candidate_key_for_action, candidate_table
from app.domains.teaching_policy.constraints import evaluate_hard_constraints
from app.domains.teaching_policy.evidence import EvidenceSignal, EvidenceSignalKind
from app.domains.teaching_policy.kernel import TeachingPolicyKernel
from app.domains.teaching_policy.models import SequentialPolicyState
from app.domains.teaching_policy.opve import (
    OPVEEvidenceLabel,
    OPVELayer,
    OPVELayerResult,
    acceptable_action_gate,
    baseline_behavior_difference,
    verify_decision_contract,
)
from app.domains.teaching_policy.sequential import SequentialTeachingPolicy
from app.domains.teaching_policy.time_source import FixedTimeSource
from tests.fixtures.v03_policy_factory import (
    NOW,
    fixed_uuid,
    load_cases,
    load_profile,
    make_bundle,
    make_context,
    with_previous_action,
)


def test_opve_l1_contract_verification() -> None:
    profile = load_profile()
    decision = TeachingPolicyKernel().decide(
        context=make_context(), bundle=make_bundle(profile), profile=profile
    )
    result = verify_decision_contract(decision.action, decision.trace)
    assert result.layer is OPVELayer.CONTRACT
    assert result.passed


def test_opve_l2_six_family_scenario_replay() -> None:
    profile = load_profile()
    observed = {
        TeachingPolicyKernel()
        .decide(context=make_context(case), bundle=make_bundle(profile), profile=profile)
        .action.strategy_family
        for case in load_cases("six_family_contexts.json")
    }
    result = OPVELayerResult(
        layer=OPVELayer.SCENARIO,
        passed=observed == set(StrategyFamily),
        cases=6,
        reason_codes=("OPVE_L2_SIX_FAMILY_REPLAY",),
    )
    assert result.passed


def test_opve_l3_sequential_replay_entry() -> None:
    profile = load_profile()
    bundle = make_bundle(profile)
    initial = TeachingPolicyKernel().decide(
        context=make_context({"case_id": "opve-seq-initial", "mastery": 0.2}),
        bundle=bundle,
        profile=profile,
    )
    state = SequentialPolicyState(
        previous_action=initial.action,
        previous_trace=initial.trace,
        evidence_opportunities_since_transition=0,
    )
    context = with_previous_action(
        make_context({"case_id": "opve-seq-next", "mastery": 0.4, "assisted_success": True}),
        initial.action,
    )
    signal = EvidenceSignal(
        signal_id="wording-only",
        kind=EvidenceSignalKind.WORDING_VARIATION,
        occurred_at=NOW,
    )
    outcome = SequentialTeachingPolicy(FixedTimeSource(NOW)).decide(
        context=context,
        bundle=bundle,
        profile=profile,
        state=state,
        signals=(signal,),
    )
    result = OPVELayerResult(
        layer=OPVELayer.SEQUENTIAL,
        passed=(
            outcome.decision.action.strategy_family is StrategyFamily.EXPLICIT_INSTRUCTION
            and outcome.transition_reason_code == "HOLD_NO_MATERIAL_EVIDENCE"
        ),
        cases=1,
        reason_codes=("OPVE_L3_SEQUENTIAL_REPLAY",),
    )
    assert result.passed


def test_opve_l4_property_and_metamorphic_entry() -> None:
    profile = load_profile()
    context = make_context({"case_id": "opve-property", "prerequisite_confidence": 0.1})
    hard = evaluate_hard_constraints(context, profile, candidate_table())
    no_resurrection = "transfer_challenge.core" in hard.forbidden_action_keys

    left_payload = make_context({"case_id": "wording-left", "mastery": 0.2}).model_dump()
    left_payload["alternative_diagnostic_hypotheses"] = ({"label": "a"}, {"label": "b"})
    right_payload = dict(left_payload)
    right_payload["context_id"] = fixed_uuid("wording-right")
    right_payload["context_fingerprint"] = "sha256:wording-right"
    right_payload["alternative_diagnostic_hypotheses"] = ({"label": "b"}, {"label": "a"})
    context_type = type(context)
    left = TeachingPolicyKernel().decide(
        context=context_type.model_validate(left_payload),
        bundle=make_bundle(profile),
        profile=profile,
    )
    right = TeachingPolicyKernel().decide(
        context=context_type.model_validate(right_payload),
        bundle=make_bundle(profile),
        profile=profile,
    )
    same_semantics = (
        left.action.strategy_family,
        left.action.interaction_moves,
        left.action.scaffold_control,
        left.action.hint_specificity,
        left.action.answer_exposure,
    ) == (
        right.action.strategy_family,
        right.action.interaction_moves,
        right.action.scaffold_control,
        right.action.hint_specificity,
        right.action.answer_exposure,
    )
    result = OPVELayerResult(
        layer=OPVELayer.PROPERTY,
        passed=no_resurrection and same_semantics,
        cases=2,
        reason_codes=("OPVE_L4_NO_RESURRECTION_AND_ORDER_METAMORPHIC",),
    )
    assert result.passed


def test_opve_l5_baseline_differential_is_behavior_only() -> None:
    difference = baseline_behavior_difference(
        selected=StrategyFamily.GUIDED_PRACTICE,
        baseline=StrategyFamily.EXPLICIT_INSTRUCTION,
    )
    result = OPVELayerResult(
        layer=OPVELayer.BASELINE,
        passed=difference["interpretation"] == "POLICY_BEHAVIOR_DIFFERENCE_NOT_LEARNING_EFFECT",
        cases=1,
        reason_codes=("OPVE_L5_BASELINE_BEHAVIOR_ONLY",),
        details=difference,
    )
    assert result.passed
    assert result.evidence_label is OPVEEvidenceLabel.ENGINEERING_POLICY_ONLY


def test_opve_l6_synthetic_stress_is_engineering_evidence_only() -> None:
    profile = load_profile()
    bundle = make_bundle(profile)
    families = []
    for index in range(200):
        mastery = (index % 100) / 100
        case = {"case_id": f"synthetic-{index}", "mastery": mastery}
        if index % 11 == 0:
            case["diagnostic_confidence"] = 0.2
            case["needs_probe"] = True
        decision = TeachingPolicyKernel().decide(
            context=make_context(case), bundle=bundle, profile=profile
        )
        families.append(decision.action.strategy_family)
    result = OPVELayerResult(
        layer=OPVELayer.SYNTHETIC,
        passed=len(families) == 200,
        cases=200,
        reason_codes=("OPVE_L6_SYNTHETIC_STRESS_COMPLETE",),
        details={"human_efficacy_evidence": False},
    )
    assert result.passed
    assert result.evidence_label.value == "ENGINEERING/POLICY EVIDENCE ONLY"
    assert result.details["human_efficacy_evidence"] is False


def test_g0_g1_g2_gold_set_semantics() -> None:
    profile = load_profile()
    bundle = make_bundle(profile)
    g0 = load_cases("g0_cases.json")
    forbidden_selected = 0
    for case in g0:
        context = make_context(case)
        hard = evaluate_hard_constraints(context, profile, candidate_table())
        decision = TeachingPolicyKernel().decide(context=context, bundle=bundle, profile=profile)
        selected_key = candidate_key_for_action(decision.action)
        if selected_key in hard.forbidden_action_keys:
            forbidden_selected += 1
    assert len(g0) == 4
    assert forbidden_selected == 0

    g1 = load_cases("g1_acceptable_actions.json")
    for case in g1:
        selected = (
            TeachingPolicyKernel()
            .decide(context=make_context(case), bundle=bundle, profile=profile)
            .action.strategy_family
        )
        acceptable = {StrategyFamily(value) for value in case["acceptable"]}
        assert acceptable_action_gate(selected, acceptable)

    g2 = load_cases("g2_research_calibration.json")
    assert g2
    assert all(case["hard_gate"] is False for case in g2)
    assert all(case["scope"] == "RESEARCH_CALIBRATION_ONLY" for case in g2)

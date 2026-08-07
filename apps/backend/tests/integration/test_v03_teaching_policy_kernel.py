from __future__ import annotations

import pytest

from app.contracts.adaptive import (
    AnswerExposure,
    InteractionMove,
    StrategyFamily,
    ValidationObligation,
    VersionedRef,
)
from app.contracts.decisions import BehaviorPolicyType, ReplayabilityStatus
from app.domains.teaching_policy import TeachingPolicyKernel
from app.domains.teaching_policy.models import PolicyDecisionError, PolicyFailureCode
from tests.fixtures.v03_policy_factory import (
    load_cases,
    load_profile,
    make_assignment,
    make_bundle,
    make_context,
)


@pytest.mark.parametrize("case", load_cases("six_family_contexts.json"), ids=lambda c: c["case_id"])
def test_all_six_strategy_families_are_selected_by_fixed_contexts(case: dict[str, object]) -> None:
    profile = load_profile()
    decision = TeachingPolicyKernel().decide(
        context=make_context(case), bundle=make_bundle(profile), profile=profile
    )
    assert decision.action.strategy_family is StrategyFamily(str(case["expected_family"]))


def test_same_exact_inputs_replay_to_same_action_and_trace() -> None:
    profile = load_profile()
    bundle = make_bundle(profile)
    context, assignment = make_assignment(make_context({"case_id": "replay"}))
    kernel = TeachingPolicyKernel()
    first = kernel.decide(context=context, bundle=bundle, profile=profile, assignment=assignment)
    second = kernel.decide(context=context, bundle=bundle, profile=profile, assignment=assignment)
    assert first == second
    assert first.trace.replayability_status is ReplayabilityStatus.FULL
    assert first.trace.behavior_policy_type is BehaviorPolicyType.DETERMINISTIC
    assert first.trace.action_propensity is None
    assert first.trace.experiment_assignment_probability == 0.5
    assert first.trace.experiment_assignment_ref == context.experiment_assignment_ref


def test_trace_retains_losers_hard_filters_features_versions_and_tie_break() -> None:
    profile = load_profile()
    decision = TeachingPolicyKernel().decide(
        context=make_context(), bundle=make_bundle(profile), profile=profile
    )
    trace = decision.trace
    assert trace.context_fingerprint
    assert trace.context_source_refs
    assert trace.policy_bundle_hash == profile.content_digest
    assert len(trace.hard_constraint_results) == 11
    assert trace.hard_filtered_actions
    assert trace.available_actions
    assert trace.features
    assert trace.candidate_scores
    assert trace.tie_break_reason
    assert trace.selected_teaching_action_ref is not None
    assert trace.anti_oscillation_decision is None


def test_direct_answer_is_bounded_and_requires_independent_validation() -> None:
    profile = load_profile()
    context = make_context({"case_id": "answer", "direct_answer_request": True})
    decision = TeachingPolicyKernel().decide(
        context=context, bundle=make_bundle(profile), profile=profile
    )
    assert decision.action.interaction_moves == (InteractionMove.DIRECT_ANSWER_OVERRIDE,)
    assert decision.action.answer_exposure is AnswerExposure.COMPLETE
    assert (
        decision.action.validation_obligation
        is ValidationObligation.INDEPENDENT_VALIDATION_REQUIRED
    )


def test_no_legal_candidate_fails_closed_with_typed_reason() -> None:
    profile = load_profile()
    context = make_context(
        {"case_id": "blocked-assessment", "activity_type": "summative_exam", "mastery": 0.2}
    )
    with pytest.raises(PolicyDecisionError) as exc_info:
        TeachingPolicyKernel().decide(context=context, bundle=make_bundle(profile), profile=profile)
    assert exc_info.value.code is PolicyFailureCode.NO_LEGAL_CANDIDATE


def test_bundle_profile_mismatch_fails_closed() -> None:
    profile = load_profile()
    bundle_payload = make_bundle(profile).model_dump()
    bundle_payload["normalization_version"] = "different"
    with pytest.raises(PolicyDecisionError) as exc_info:
        TeachingPolicyKernel().decide(
            context=make_context(),
            bundle=type(make_bundle(profile)).model_validate(bundle_payload),
            profile=profile,
        )
    assert exc_info.value.code is PolicyFailureCode.UNSUPPORTED_CONFIGURATION


def test_context_cannot_hide_an_unpinned_owner_ref() -> None:
    profile = load_profile()
    context = make_context()
    payload = context.model_dump()
    payload["source_refs"] = (context.learning_objective_ref, context.learning_activity_ref)
    unpinned = type(context).model_validate(payload)
    with pytest.raises(PolicyDecisionError) as exc_info:
        TeachingPolicyKernel().decide(
            context=unpinned, bundle=make_bundle(profile), profile=profile
        )
    assert exc_info.value.code is PolicyFailureCode.INVALID_CONTEXT


def test_experiment_assignment_requires_exact_identity_and_version() -> None:
    profile = load_profile()
    context, assignment = make_assignment(make_context({"case_id": "assignment-version"}))
    payload = context.model_dump()
    wrong_ref = VersionedRef(
        entity_type="experiment_assignment",
        entity_id=str(assignment.assignment_id),
        version="different",
    )
    payload["experiment_assignment_ref"] = wrong_ref
    payload["source_refs"] = tuple(
        wrong_ref if ref.entity_type == "experiment_assignment" else ref
        for ref in context.source_refs
    )
    wrong_context = type(context).model_validate(payload)
    with pytest.raises(PolicyDecisionError) as exc_info:
        TeachingPolicyKernel().decide(
            context=wrong_context,
            bundle=make_bundle(profile),
            profile=profile,
            assignment=assignment,
        )
    assert exc_info.value.code is PolicyFailureCode.EXPERIMENT_ASSIGNMENT_MISMATCH

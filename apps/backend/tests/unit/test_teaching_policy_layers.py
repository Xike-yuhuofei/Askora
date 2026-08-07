from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.contracts.adaptive import AvailabilityStatus, StrategyFamily, TeachingStage
from app.domains.teaching_policy.candidates import candidate_table, generate_candidates
from app.domains.teaching_policy.constraints import evaluate_hard_constraints
from app.domains.teaching_policy.features import build_candidate_features, normalize_feature
from app.domains.teaching_policy.models import CandidateScore, PolicyRuntimeProfile
from app.domains.teaching_policy.scoring import select_stably
from app.domains.teaching_policy.stages import derive_teaching_stage
from tests.fixtures.v03_policy_factory import load_cases, load_profile, make_context


def test_candidate_table_is_closed_six_family_vocabulary() -> None:
    table = candidate_table()
    assert {candidate.strategy_family for candidate in table} == set(StrategyFamily)
    assert all("PRODUCTIVE_FAILURE" not in candidate.action_key for candidate in table)
    assert len({candidate.action_key for candidate in table}) == len(table)


def test_all_required_hard_rule_families_are_typed_and_versioned() -> None:
    profile = load_profile()
    evaluation = evaluate_hard_constraints(make_context(), profile, candidate_table())
    assert [result.rule_id for result in evaluation.results] == [
        "SYS05-HC-ASSESSMENT-INTEGRITY",
        "SYS05-HC-ANSWER-EXPOSURE-INTEGRITY",
        "SYS05-HC-PREREQUISITE-SAFETY",
        "SYS05-HC-REPEATED-FAILURE-CEILING",
        "SYS05-HC-INDEPENDENT-SUCCESS",
        "SYS05-HC-LOW-CONFIDENCE-CONSERVATISM",
        "SYS05-HC-OBJECTIVE-OWNERSHIP",
        "SYS05-HC-MODEL-LLM-OVERRIDE",
        "SYS05-HC-UNSUPPORTED-CONFIGURATION",
        "SYS05-HC-HARD-RULE-CONFLICT",
        "SYS05-HC-USER-DIRECT-ANSWER",
    ]
    assert all(
        result.rule_version == profile.hard_rule_set_version for result in evaluation.results
    )
    assert all(result.reason_codes for result in evaluation.results)
    assert all(result.input_refs for result in evaluation.results)


@pytest.mark.parametrize("case", load_cases("six_family_contexts.json"), ids=lambda c: c["case_id"])
def test_stage_mapper_is_deterministic_for_six_family_fixtures(case: dict[str, object]) -> None:
    profile = load_profile()
    context = make_context(case)
    first = derive_teaching_stage(context, profile)
    second = derive_teaching_stage(context, profile)
    expected = {
        "EXPLICIT_INSTRUCTION": TeachingStage.EXPLICIT_INSTRUCTION,
        "GUIDED_PRACTICE": TeachingStage.GUIDED_PRACTICE,
        "FADING_PRACTICE": TeachingStage.FADING_PRACTICE,
        "RETRIEVAL_PRACTICE": TeachingStage.RETRIEVAL_PRACTICE,
        "ERROR_REMEDIATION": TeachingStage.ERROR_REMEDIATION,
        "TRANSFER_CHALLENGE": TeachingStage.TRANSFER_CHALLENGE,
    }[str(case["expected_family"])]
    assert first is second is expected


def test_missing_critical_evidence_uses_explicit_conservative_stage() -> None:
    context = make_context()
    payload = context.model_dump()
    payload["assessment_confidence"] = {
        "value": None,
        "availability": AvailabilityStatus.MISSING,
        "confidence": None,
        "source_refs": (),
    }
    conservative = type(context).model_validate(payload)
    assert derive_teaching_stage(conservative, load_profile()) is TeachingStage.DIAGNOSE


def test_hard_filtered_candidate_cannot_be_regenerated() -> None:
    context = make_context({"case_id": "unsafe", "prerequisite_confidence": 0.1})
    hard = evaluate_hard_constraints(context, load_profile(), candidate_table())
    assert "transfer_challenge.core" in hard.forbidden_action_keys
    generated = generate_candidates(
        TeachingStage.TRANSFER_CHALLENGE,
        hard.forbidden_action_keys,
        direct_answer_request=False,
    )
    assert generated == ()


def test_feature_missing_semantics_and_fixed_normalization_are_auditable() -> None:
    profile = load_profile()
    context = make_context()
    candidate = candidate_table()[0]
    feature_set = build_candidate_features(
        context, TeachingStage.EXPLICIT_INSTRUCTION, candidate, profile
    )
    dependency = next(
        feature
        for feature in feature_set.features
        if feature.feature_name == "hint_dependency_risk"
    )
    assert dependency.availability is AvailabilityStatus.AVAILABLE
    assert dependency.source_refs == context.source_refs
    assert normalize_feature(dependency, profile) == pytest.approx(0.2)

    missing_context_payload = context.model_dump()
    missing_context_payload["assistance_history_summary"] = {}
    missing_context = type(context).model_validate(missing_context_payload)
    missing_feature = next(
        feature
        for feature in build_candidate_features(
            missing_context, TeachingStage.EXPLICIT_INSTRUCTION, candidate, profile
        ).features
        if feature.feature_name == "hint_dependency_risk"
    )
    assert missing_feature.value is None
    assert missing_feature.availability is AvailabilityStatus.MISSING
    assert normalize_feature(missing_feature, profile) is None


def test_stable_tie_break_ignores_input_iteration_order() -> None:
    profile = load_profile()
    scores = (
        CandidateScore(
            action_key="guided_practice.core",
            normalized_features={},
            weighted_components={},
            total_score=1.0,
        ),
        CandidateScore(
            action_key="error_remediation.core",
            normalized_features={},
            weighted_components={},
            total_score=1.0,
        ),
    )
    selected_a, reason_a = select_stably(scores, profile)
    selected_b, reason_b = select_stably(tuple(reversed(scores)), profile)
    assert selected_a.action_key == selected_b.action_key == "error_remediation.core"
    assert reason_a == reason_b == "tie-1:score_then_candidate_priority_then_action_key"


def test_profile_is_immutable_and_parameters_are_not_module_constants() -> None:
    profile = load_profile()
    with pytest.raises(ValidationError):
        profile.failure_ceiling = 99  # type: ignore[misc]
    assert isinstance(profile, PolicyRuntimeProfile)

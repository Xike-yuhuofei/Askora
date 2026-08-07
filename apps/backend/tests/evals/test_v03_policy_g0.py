from __future__ import annotations

import pytest

from app.domains.teaching_policy import TeachingPolicyKernel
from app.domains.teaching_policy.candidates import candidate_table
from app.domains.teaching_policy.constraints import evaluate_hard_constraints
from tests.fixtures.v03_policy_factory import load_cases, load_profile, make_bundle, make_context


@pytest.mark.parametrize("case", load_cases("g0_cases.json"), ids=lambda c: c["case_id"])
def test_g0_forbidden_action_count_is_zero(case: dict[str, object]) -> None:
    profile = load_profile()
    context = make_context(case)
    hard = evaluate_hard_constraints(context, profile, candidate_table())
    expected_forbidden = set(case["forbidden"])  # type: ignore[arg-type]
    assert expected_forbidden <= hard.forbidden_action_keys

    decision = TeachingPolicyKernel().decide(
        context=context, bundle=make_bundle(profile), profile=profile
    )
    selected_key = next(
        item["action_key"]
        for item in decision.trace.available_actions
        if item["strategy_family"] == decision.action.strategy_family.value
    )
    assert selected_key not in hard.forbidden_action_keys
    assert all(
        filtered.action_ref != selected_key for filtered in decision.trace.hard_filtered_actions
    )

"""Offline Policy Verification & Evaluation helpers (not causal RL/OPE)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import Field

from app.contracts.adaptive import StrategyFamily, TeachingActionV03
from app.contracts.base import ContractModel
from app.contracts.decisions import BehaviorPolicyType, DecisionTraceV03


class OPVELayer(StrEnum):
    CONTRACT = "L1_CONTRACT_VERIFICATION"
    SCENARIO = "L2_SCENARIO_REPLAY"
    SEQUENTIAL = "L3_SEQUENTIAL_REPLAY"
    PROPERTY = "L4_PROPERTY_METAMORPHIC"
    BASELINE = "L5_BASELINE_DIFFERENTIAL"
    SYNTHETIC = "L6_SYNTHETIC_STRESS"


class OPVEEvidenceLabel(StrEnum):
    ENGINEERING_POLICY_ONLY = "ENGINEERING/POLICY EVIDENCE ONLY"


class OPVELayerResult(ContractModel):
    layer: OPVELayer
    passed: bool
    cases: int = Field(ge=0)
    reason_codes: tuple[str, ...] = Field(min_length=1)
    evidence_label: OPVEEvidenceLabel = OPVEEvidenceLabel.ENGINEERING_POLICY_ONLY
    details: dict[str, Any] = Field(default_factory=dict)


def verify_decision_contract(action: TeachingActionV03, trace: DecisionTraceV03) -> OPVELayerResult:
    passed = (
        trace.behavior_policy_type is BehaviorPolicyType.DETERMINISTIC
        and trace.action_propensity is None
        and trace.selected_teaching_action_ref is not None
        and trace.selected_teaching_action_ref.entity_id == str(action.action_id)
    )
    return OPVELayerResult(
        layer=OPVELayer.CONTRACT,
        passed=passed,
        cases=1,
        reason_codes=("OPVE_L1_CONTRACT_VALID" if passed else "OPVE_L1_CONTRACT_INVALID",),
    )


def acceptable_action_gate(selected: StrategyFamily, acceptable: set[StrategyFamily]) -> bool:
    return selected in acceptable


def baseline_behavior_difference(
    *, selected: StrategyFamily, baseline: StrategyFamily
) -> dict[str, Any]:
    return {
        "same_behavior": selected is baseline,
        "selected": selected.value,
        "baseline": baseline.value,
        "interpretation": "POLICY_BEHAVIOR_DIFFERENCE_NOT_LEARNING_EFFECT",
        "evidence_label": OPVEEvidenceLabel.ENGINEERING_POLICY_ONLY.value,
    }

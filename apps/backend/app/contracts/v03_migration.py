"""Pure deterministic v0.2 -> v0.3 compatibility projections.

These functions are read/upcast adapters, not canonical writers.  They preserve
raw legacy values and explicitly degrade replayability whenever the frozen specs
do not define a lossless mapping.  No online model, current mutable state, or
current PolicyBundle is consulted.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Callable

from pydantic import Field

from app.contracts.adaptive import InteractionMove, StrategyFamily
from app.contracts.base import ContractModel
from app.contracts.decisions import BehaviorPolicyType, ReplayabilityStatus


class MigrationCandidate(StrEnum):
    HISTORICAL_STRATEGY = "historical_strategy"
    HISTORICAL_TEACHING_ACTION = "historical_teaching_action"
    OLD_SCAFFOLD_LEVEL = "old_scaffold_level"
    OLD_HINT_LEVEL = "old_hint_level"
    OLD_ANSWER_EXPOSURE = "old_answer_exposure"
    LEGACY_SOCRATIC_SELECTOR = "legacy_socratic_selector"
    OLD_POLICY_CONFIG = "old_policy_config"
    OLD_DECISION_PROPENSITY = "old_decision_propensity"
    HISTORICAL_REPLAY = "historical_replay"


class MigrationProjection(ContractModel):
    candidate: MigrationCandidate
    canonical_target: str = Field(min_length=1)
    compatibility_behavior: str = Field(min_length=1)
    canonical_payload: dict[str, Any] | None = None
    raw_legacy_payload: dict[str, Any]
    ambiguous: bool
    lossy: bool
    replayability_status: ReplayabilityStatus
    reason_codes: tuple[str, ...] = Field(min_length=1)
    retirement_condition: str = Field(min_length=1)


_STRATEGY_MAPPING: dict[str, dict[str, Any]] = {
    "DIRECT_INSTRUCTION": {
        "strategy_family": StrategyFamily.EXPLICIT_INSTRUCTION.value,
        "interaction_moves": [InteractionMove.DIRECT_INSTRUCTION.value],
        "classification": "INTERACTION_MOVE",
    },
    "WORKED_EXAMPLE": {
        "strategy_family": StrategyFamily.EXPLICIT_INSTRUCTION.value,
        "interaction_moves": [InteractionMove.WORKED_EXAMPLE.value],
        "classification": "INTERACTION_MOVE",
    },
    "WORKED_EXAMPLE_FADING": {
        "strategy_family": StrategyFamily.FADING_PRACTICE.value,
        "interaction_moves": [
            InteractionMove.WORKED_EXAMPLE.value,
            InteractionMove.FADING_STEP.value,
        ],
        "classification": "ACTION_PATTERN",
    },
    "SOCRATIC_PROBING": {
        "strategy_family": StrategyFamily.GUIDED_PRACTICE.value,
        "interaction_moves": [InteractionMove.SOCRATIC_PROBE.value],
        "classification": "BOUNDED_INTERACTION_MOVE",
    },
    "GUIDED_PRACTICE": {
        "strategy_family": StrategyFamily.GUIDED_PRACTICE.value,
        "interaction_moves": [],
        "classification": "STRATEGY_FAMILY",
    },
    "ERROR_REMEDIATION": {
        "strategy_family": StrategyFamily.ERROR_REMEDIATION.value,
        "interaction_moves": [],
        "classification": "STRATEGY_FAMILY",
    },
    "RETRIEVAL_PRACTICE": {
        "strategy_family": StrategyFamily.RETRIEVAL_PRACTICE.value,
        "interaction_moves": [],
        "classification": "STRATEGY_FAMILY",
    },
    "TRANSFER_CHALLENGE": {
        "strategy_family": StrategyFamily.TRANSFER_CHALLENGE.value,
        "interaction_moves": [InteractionMove.TRANSFER_TASK.value],
        "classification": "STRATEGY_FAMILY",
    },
}


def _historical_strategy(payload: dict[str, Any]) -> MigrationProjection:
    raw_value = str(payload.get("strategy", payload.get("strategy_id", ""))).upper()
    if raw_value == "METACOGNITIVE_REFLECTION":
        projected: dict[str, Any] = {
            "strategy_mapping_version": "ADR-0001-v1",
            "strategy_family": None,
            "interaction_moves": [],
            "action_modifiers": {"metacognitive_reflection": True},
            "classification": "ACTION_MODIFIER_OR_SYS06_ACTIVITY",
        }
        return MigrationProjection(
            candidate=MigrationCandidate.HISTORICAL_STRATEGY,
            canonical_target="ActionModifier or SYS06 metacognitive activity",
            compatibility_behavior="read-only versioned projection; never selectable family",
            canonical_payload=projected,
            raw_legacy_payload=payload,
            ambiguous=True,
            lossy=True,
            replayability_status=ReplayabilityStatus.PARTIAL,
            reason_codes=("LEGACY_STRATEGY_LAYER_CHANGED",),
            retirement_condition="all historical records projected or archived read-only",
        )
    if raw_value == "PRODUCTIVE_FAILURE":
        return MigrationProjection(
            candidate=MigrationCandidate.HISTORICAL_STRATEGY,
            canonical_target="deferred legacy audit value; no v0.3 StrategyFamily",
            compatibility_behavior="preserve original value; canonical selector rejects it",
            canonical_payload={
                "strategy_mapping_version": "ADR-0001-v1",
                "strategy_family": None,
                "classification": "DEFERRED",
            },
            raw_legacy_payload=payload,
            ambiguous=True,
            lossy=True,
            replayability_status=ReplayabilityStatus.PARTIAL,
            reason_codes=("PRODUCTIVE_FAILURE_DEFERRED",),
            retirement_condition="historical record archived; no active writer/selector remains",
        )
    mapped = _STRATEGY_MAPPING.get(raw_value)
    if mapped is None:
        return MigrationProjection(
            candidate=MigrationCandidate.HISTORICAL_STRATEGY,
            canonical_target="StrategyFamily/InteractionMove compatibility projection",
            compatibility_behavior="preserve unknown raw value without guessing",
            canonical_payload=None,
            raw_legacy_payload=payload,
            ambiguous=True,
            lossy=True,
            replayability_status=ReplayabilityStatus.PARTIAL,
            reason_codes=("UNKNOWN_LEGACY_STRATEGY",),
            retirement_condition="record explicitly classified or archived read-only",
        )
    return MigrationProjection(
        candidate=MigrationCandidate.HISTORICAL_STRATEGY,
        canonical_target="StrategyFamily + InteractionMove",
        compatibility_behavior="ADR-0001 versioned read projection",
        canonical_payload={"strategy_mapping_version": "ADR-0001-v1", **mapped},
        raw_legacy_payload=payload,
        ambiguous=False,
        lossy=raw_value in {"WORKED_EXAMPLE_FADING", "SOCRATIC_PROBING"},
        replayability_status=(
            ReplayabilityStatus.PARTIAL
            if raw_value in {"WORKED_EXAMPLE_FADING", "SOCRATIC_PROBING"}
            else ReplayabilityStatus.FULL
        ),
        reason_codes=("LEGACY_STRATEGY_PROJECTED_ADR0001",),
        retirement_condition="all historical strategy records projected or archived read-only",
    )


def _historical_teaching_action(payload: dict[str, Any]) -> MigrationProjection:
    strategy_projection = _historical_strategy(payload)
    projected = dict(strategy_projection.canonical_payload or {})
    projected.update(
        {
            "action_schema_version": "3.0-compatibility-projection",
            "original_action_id": payload.get("action_id"),
            "scaffold_control": None,
            "hint_specificity": None,
            "answer_exposure": None,
            "teaching_context_ref": None,
            "policy_bundle_ref": None,
        }
    )
    return MigrationProjection(
        candidate=MigrationCandidate.HISTORICAL_TEACHING_ACTION,
        canonical_target="TeachingAction v0.3 read projection",
        compatibility_behavior="preserve v1 payload; expose only reconstructable ontology fields",
        canonical_payload=projected,
        raw_legacy_payload=payload,
        ambiguous=True,
        lossy=True,
        replayability_status=ReplayabilityStatus.PARTIAL,
        reason_codes=("LEGACY_ACTION_MISSING_V03_EXACT_REFS",),
        retirement_condition="no active v0.2 workflow and supported history migrated/audited",
    )


def _ambiguous_integer_axis(
    candidate: MigrationCandidate,
    payload: dict[str, Any],
    *,
    canonical_target: str,
    reason_code: str,
) -> MigrationProjection:
    return MigrationProjection(
        candidate=candidate,
        canonical_target=canonical_target,
        compatibility_behavior="raw integer retained for audit; canonical value unavailable",
        canonical_payload={
            "value": None,
            "availability": "MISSING",
            "migration_reason": reason_code,
        },
        raw_legacy_payload=payload,
        ambiguous=True,
        lossy=True,
        replayability_status=ReplayabilityStatus.PARTIAL,
        reason_codes=(reason_code,),
        retirement_condition="all active writers/readers use orthogonal v0.3 assistance fields",
    )


def _old_scaffold(payload: dict[str, Any]) -> MigrationProjection:
    return _ambiguous_integer_axis(
        MigrationCandidate.OLD_SCAFFOLD_LEVEL,
        payload,
        canonical_target="scaffold_control",
        reason_code="AMBIGUOUS_LEGACY_SCAFFOLD_LEVEL",
    )


def _old_hint(payload: dict[str, Any]) -> MigrationProjection:
    return _ambiguous_integer_axis(
        MigrationCandidate.OLD_HINT_LEVEL,
        payload,
        canonical_target="hint_specificity",
        reason_code="AMBIGUOUS_LEGACY_HINT_LEVEL",
    )


def _old_exposure(payload: dict[str, Any]) -> MigrationProjection:
    return _ambiguous_integer_axis(
        MigrationCandidate.OLD_ANSWER_EXPOSURE,
        payload,
        canonical_target="answer_exposure",
        reason_code="AMBIGUOUS_LEGACY_ANSWER_EXPOSURE",
    )


def _legacy_socratic(payload: dict[str, Any]) -> MigrationProjection:
    return MigrationProjection(
        candidate=MigrationCandidate.LEGACY_SOCRATIC_SELECTOR,
        canonical_target="bounded SOCRATIC_PROBE provider/execution adapter",
        compatibility_behavior="read/execute only behind SYS05; never final action owner",
        canonical_payload={
            "interaction_move": InteractionMove.SOCRATIC_PROBE.value,
            "allowed_roles": ["MOVE_PROVIDER", "EXECUTION_ADAPTER", "TEST_FIXTURE"],
            "final_teaching_action_owner": False,
        },
        raw_legacy_payload=payload,
        ambiguous=False,
        lossy=True,
        replayability_status=ReplayabilityStatus.PARTIAL,
        reason_codes=("LEGACY_SOCRATIC_OWNERSHIP_REMOVED",),
        retirement_condition="canonical SYS05 path covers every supported legacy flow",
    )


_POLICY_COMPONENTS = {
    "schema_version",
    "policy_version",
    "hard_rule_set_version",
    "stage_mapper_version",
    "candidate_table_version",
    "feature_schema_version",
    "normalization_version",
    "weight_profile_version",
    "anti_oscillation_profile_version",
    "tie_break_version",
    "fallback_profile_version",
    "content_digest",
}


def _old_policy(payload: dict[str, Any]) -> MigrationProjection:
    missing = sorted(_POLICY_COMPONENTS.difference(payload))
    full = not missing and not payload.get("executable_rules")
    canonical_payload = dict(payload) if full else {"missing_components": missing}
    return MigrationProjection(
        candidate=MigrationCandidate.OLD_POLICY_CONFIG,
        canonical_target="immutable PolicyBundle manifest",
        compatibility_behavior=(
            "reconstruct exact immutable bundle" if full else "audit/import only; never execute"
        ),
        canonical_payload=canonical_payload,
        raw_legacy_payload=payload,
        ambiguous=not full,
        lossy=not full,
        replayability_status=(ReplayabilityStatus.FULL if full else ReplayabilityStatus.PARTIAL),
        reason_codes=(
            "LEGACY_POLICY_RECONSTRUCTED" if full else "LEGACY_POLICY_COMPONENT_VERSIONS_MISSING",
        ),
        retirement_condition="configs migrated to immutable bundles or retired from execution",
    )


def _old_propensity(payload: dict[str, Any]) -> MigrationProjection:
    raw = payload.get("propensity")
    provenance = payload.get("propensity_semantics")
    canonical: dict[str, Any] = {
        "raw_legacy_propensity": raw,
        "assignment_probability": None,
        "action_propensity": None,
        "behavior_policy_type": BehaviorPolicyType.UNKNOWN.value,
    }
    if provenance == "experiment_assignment_probability":
        canonical["assignment_probability"] = raw
        status = ReplayabilityStatus.PARTIAL
        ambiguous = False
        reason = "LEGACY_PROPENSITY_PROVEN_ASSIGNMENT_PROBABILITY"
    elif provenance == "action_selection_propensity":
        canonical["action_propensity"] = raw
        canonical["behavior_policy_type"] = BehaviorPolicyType.STOCHASTIC_EXPERIMENTAL.value
        status = ReplayabilityStatus.PARTIAL
        ambiguous = False
        reason = "LEGACY_PROPENSITY_PROVEN_ACTION_PROPENSITY"
    else:
        status = ReplayabilityStatus.PARTIAL
        ambiguous = True
        reason = "AMBIGUOUS_LEGACY_PROPENSITY"
    return MigrationProjection(
        candidate=MigrationCandidate.OLD_DECISION_PROPENSITY,
        canonical_target="separate assignment_probability and action_propensity",
        compatibility_behavior="preserve raw value; project only with explicit provenance",
        canonical_payload=canonical,
        raw_legacy_payload=payload,
        ambiguous=ambiguous,
        lossy=True,
        replayability_status=status,
        reason_codes=(reason,),
        retirement_condition="historical trace migrator completed with explicit probability semantics",
    )


def _historical_replay(payload: dict[str, Any]) -> MigrationProjection:
    required = {
        "teaching_context_ref",
        "policy_bundle_ref",
        "context_source_refs",
        "tie_break_version",
    }
    missing = sorted(key for key in required if not payload.get(key))
    if not missing:
        status = ReplayabilityStatus.FULL
        reasons = ("EXACT_HISTORICAL_REFS_AVAILABLE",)
    elif payload.get("teaching_context_ref") or payload.get("policy_bundle_ref"):
        status = ReplayabilityStatus.PARTIAL
        reasons = ("HISTORICAL_REPLAY_EXACT_REFS_PARTIAL",)
    else:
        status = ReplayabilityStatus.NON_REPLAYABLE
        reasons = ("HISTORICAL_REPLAY_EXACT_REFS_MISSING",)
    return MigrationProjection(
        candidate=MigrationCandidate.HISTORICAL_REPLAY,
        canonical_target="exact-version policy replay",
        compatibility_behavior="never fill missing refs from current mutable state/config",
        canonical_payload={"missing_exact_refs": missing, "online_llm_allowed": False},
        raw_legacy_payload=payload,
        ambiguous=bool(missing),
        lossy=bool(missing),
        replayability_status=status,
        reason_codes=reasons,
        retirement_condition="explicit replayability status retained for all supported history",
    )


_UPCASTERS: dict[MigrationCandidate, Callable[[dict[str, Any]], MigrationProjection]] = {
    MigrationCandidate.HISTORICAL_STRATEGY: _historical_strategy,
    MigrationCandidate.HISTORICAL_TEACHING_ACTION: _historical_teaching_action,
    MigrationCandidate.OLD_SCAFFOLD_LEVEL: _old_scaffold,
    MigrationCandidate.OLD_HINT_LEVEL: _old_hint,
    MigrationCandidate.OLD_ANSWER_EXPOSURE: _old_exposure,
    MigrationCandidate.LEGACY_SOCRATIC_SELECTOR: _legacy_socratic,
    MigrationCandidate.OLD_POLICY_CONFIG: _old_policy,
    MigrationCandidate.OLD_DECISION_PROPENSITY: _old_propensity,
    MigrationCandidate.HISTORICAL_REPLAY: _historical_replay,
}


def upcast_v03_compatibility(
    candidate: MigrationCandidate | str, payload: dict[str, Any]
) -> MigrationProjection:
    """Project one legacy candidate without mutable-state or model dependencies."""

    normalized = MigrationCandidate(candidate)
    return _UPCASTERS[normalized](dict(payload))

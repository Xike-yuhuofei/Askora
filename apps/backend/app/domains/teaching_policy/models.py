"""Private, typed policy models bound to an immutable PolicyBundle manifest."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from app.contracts.adaptive import (
    ActionModifier,
    AnswerExposure,
    AssistanceState,
    HintSpecificity,
    InteractionMove,
    PolicyBundleV03,
    ScaffoldControl,
    StrategyFamily,
    TeachingActionV03,
    TeachingStage,
    VersionedRef,
)
from app.contracts.base import ContractModel
from app.contracts.decisions import DecisionFeatureV03, DecisionTraceV03


class PolicyFailureCode(StrEnum):
    INVALID_CONTEXT = "POLICY_INVALID_CONTEXT"
    EXPERIMENT_ASSIGNMENT_MISMATCH = "POLICY_EXPERIMENT_ASSIGNMENT_MISMATCH"
    UNSUPPORTED_CONFIGURATION = "POLICY_UNSUPPORTED_CONFIGURATION"
    HARD_RULE_CONFLICT = "POLICY_HARD_RULE_CONFLICT"
    NO_LEGAL_CANDIDATE = "POLICY_NO_LEGAL_CANDIDATE"
    NORMALIZATION_FAILURE = "POLICY_NORMALIZATION_FAILURE"
    TIE_BREAK_CONFIGURATION_FAILURE = "POLICY_TIE_BREAK_CONFIGURATION_FAILURE"


class PolicyDecisionError(ValueError):
    """Typed fail-closed policy error; callers must not ask an LLM to recover."""

    def __init__(self, code: PolicyFailureCode, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code.value}: {detail}")


class NormalizationRange(ContractModel):
    minimum: float
    maximum: float

    @model_validator(mode="after")
    def require_nonzero_range(self) -> NormalizationRange:
        if self.maximum <= self.minimum:
            raise ValueError("normalization maximum must be greater than minimum")
        return self


class PolicyRuntimeProfile(ContractModel):
    """Static typed values whose exact versions/digest are pinned by PolicyBundle."""

    profile_id: str = Field(min_length=1)
    policy_version: str = Field(min_length=1)
    hard_rule_set_version: str = Field(min_length=1)
    stage_mapper_version: str = Field(min_length=1)
    candidate_table_version: str = Field(min_length=1)
    feature_schema_version: str = Field(min_length=1)
    normalization_version: str = Field(min_length=1)
    weight_profile_version: str = Field(min_length=1)
    tie_break_version: str = Field(min_length=1)
    fallback_profile_version: str = Field(min_length=1)
    content_digest: str = Field(min_length=1)

    failure_ceiling: int = Field(ge=1)
    diagnostic_confidence_cutoff: float = Field(ge=0.0, le=1.0)
    mastery_threshold: float = Field(ge=0.0, le=1.0)
    prerequisite_confidence_cutoff: float = Field(ge=0.0, le=1.0)
    transfer_novelty_cutoff: float = Field(ge=0.0, le=1.0)
    practical_harm_margin: float = Field(ge=0.0)
    minimum_dwell_opportunities: int = Field(ge=0)
    switch_margin: float = Field(ge=0.0)
    meaningful_delay_seconds: int = Field(ge=0)
    transition_priority: tuple[str, ...] = Field(min_length=1)

    normalization_ranges: dict[str, NormalizationRange]
    feature_weights: dict[str, float]
    candidate_priority: tuple[str, ...] = Field(min_length=1)

    def assert_matches(self, bundle: PolicyBundleV03) -> None:
        fields = (
            "policy_version",
            "hard_rule_set_version",
            "stage_mapper_version",
            "candidate_table_version",
            "feature_schema_version",
            "normalization_version",
            "weight_profile_version",
            "tie_break_version",
            "fallback_profile_version",
            "content_digest",
        )
        mismatches = [name for name in fields if getattr(self, name) != getattr(bundle, name)]
        if mismatches:
            raise PolicyDecisionError(
                PolicyFailureCode.UNSUPPORTED_CONFIGURATION,
                f"runtime profile does not match exact bundle fields: {','.join(mismatches)}",
            )


class TeachingCandidate(ContractModel):
    action_key: str = Field(min_length=1)
    strategy_family: StrategyFamily
    allowed_stages: tuple[TeachingStage, ...] = Field(min_length=1)
    interaction_moves: tuple[InteractionMove, ...] = Field(min_length=1)
    action_modifiers: ActionModifier
    scaffold_control: ScaffoldControl
    hint_specificity: HintSpecificity
    answer_exposure: AnswerExposure
    evidence_requirements: tuple[str, ...]
    expected_evidence_type: str | None
    success_condition: dict[str, Any]
    failure_condition: dict[str, Any]
    max_attempts: int | None = Field(default=None, ge=1)


class CandidateFeatureSet(ContractModel):
    action_key: str
    features: tuple[DecisionFeatureV03, ...]


class CandidateScore(ContractModel):
    action_key: str
    normalized_features: dict[str, float | None]
    weighted_components: dict[str, float]
    total_score: float


class PolicyDecision(ContractModel):
    action: TeachingActionV03
    trace: DecisionTraceV03


class ValidationObligationStatus(StrEnum):
    REQUIRED = "REQUIRED"
    SATISFIED = "SATISFIED"


class IndependentValidationRecord(ContractModel):
    obligation_id: UUID
    status: ValidationObligationStatus
    created_at: datetime
    source_attempt_ref: VersionedRef
    source_result_ref: VersionedRef
    assistance_state: AssistanceState
    satisfied_at: datetime | None = None
    satisfying_attempt_ref: VersionedRef | None = None
    satisfying_result_ref: VersionedRef | None = None
    reason_codes: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def require_satisfaction_evidence(self) -> IndependentValidationRecord:
        refs = (self.satisfying_attempt_ref, self.satisfying_result_ref, self.satisfied_at)
        if self.status is ValidationObligationStatus.SATISFIED and any(ref is None for ref in refs):
            raise ValueError(
                "satisfied validation obligation requires fresh evidence refs and time"
            )
        if self.status is ValidationObligationStatus.REQUIRED and any(
            ref is not None for ref in refs
        ):
            raise ValueError("required validation obligation cannot contain satisfaction evidence")
        return self


class SequentialPolicyState(ContractModel):
    previous_action: TeachingActionV03
    previous_trace: DecisionTraceV03
    evidence_opportunities_since_transition: int = Field(ge=0)
    observed_material_evidence_keys: tuple[str, ...] = ()
    validation_obligation: IndependentValidationRecord | None = None

    @model_validator(mode="after")
    def require_exact_previous_trace(self) -> SequentialPolicyState:
        selected = self.previous_trace.selected_teaching_action_ref
        if (
            selected is None
            or selected.entity_id != str(self.previous_action.action_id)
            or str(selected.version) != self.previous_action.action_schema_version
            or self.previous_trace.decision_id != self.previous_action.decision_id
        ):
            raise ValueError("previous DecisionTrace must exactly select previous TeachingAction")
        return self


class SequentialPolicyDecision(ContractModel):
    decision: PolicyDecision
    next_state: SequentialPolicyState
    transition_reason_code: str


class ValidatedPolicyInput(ContractModel):
    context_ref: VersionedRef
    bundle_ref: VersionedRef

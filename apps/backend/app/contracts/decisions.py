"""DecisionTrace contracts.

``DecisionTrace`` is the frozen v1 compatibility/audit reader.  New adaptive
teaching decisions use ``DecisionTraceV03`` so a v1 payload can never be
silently reinterpreted as v0.3 probability or replay semantics.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.contracts.adaptive import (
    AvailabilityStatus,
    StrategyFamily,
    TeachingStage,
    VersionedRef,
)
from app.contracts.base import ContractModel


class DecisionInput(ContractModel):
    entity_type: str
    entity_id: UUID | str
    version: str | int | None = None

    @field_validator("entity_id", mode="before")
    @classmethod
    def normalize_entity_id(cls, value: UUID | str) -> str:
        return str(value)


class DecisionAlgorithm(ContractModel):
    algorithm_id: str
    algorithm_version: str
    model_inference_ids: list[UUID]
    prompt_versions: list[str]


class DecisionExperiment(ContractModel):
    experiment_id: str | None = None
    variant_id: str | None = None
    propensity: float | None = Field(default=None, ge=0.0, le=1.0)


class DecisionTrace(ContractModel):
    """DECISION-001..091：领域系统提交、4.8 原样持久化的审计记录。"""

    decision_id: UUID
    decision_type: str = Field(min_length=1)
    schema_version: Literal["1.0"] = "1.0"
    owner_system: Literal[
        "content_knowledge",
        "retrieval",
        "learner_model",
        "assessment",
        "teaching_policy",
        "learning_planner",
        "review_scheduler",
        "ai_orchestration",
    ]
    inputs: list[DecisionInput]
    candidates: list[dict[str, Any]]
    selected: dict[str, Any]
    constraints: list[dict[str, Any]]
    reason_codes: list[str] = Field(min_length=1)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    algorithm: DecisionAlgorithm
    experiment: DecisionExperiment
    created_at: datetime
    correlation_id: UUID
    trace_id: str


class BehaviorPolicyType(StrEnum):
    DETERMINISTIC = "DETERMINISTIC"
    STOCHASTIC_EXPERIMENTAL = "STOCHASTIC_EXPERIMENTAL"
    UNKNOWN = "UNKNOWN"


class ReplayabilityStatus(StrEnum):
    FULL = "FULL"
    PARTIAL = "PARTIAL"
    NON_REPLAYABLE = "NON_REPLAYABLE"


class HardConstraintResultV03(ContractModel):
    rule_id: str = Field(min_length=1)
    rule_version: str = Field(min_length=1)
    passed: bool
    reason_codes: tuple[str, ...]
    forbidden_action_refs: tuple[str, ...] = ()
    input_refs: tuple[VersionedRef, ...] = ()


class HardFilteredActionV03(ContractModel):
    action_ref: str = Field(min_length=1)
    filter_reason_codes: tuple[str, ...] = Field(min_length=1)


class DecisionFeatureV03(ContractModel):
    feature_name: str = Field(min_length=1)
    value: float | None = None
    availability: AvailabilityStatus
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    feature_version: str = Field(min_length=1)
    source_refs: tuple[VersionedRef, ...] = ()

    @model_validator(mode="after")
    def validate_missing_value(self) -> DecisionFeatureV03:
        if self.availability is AvailabilityStatus.AVAILABLE and self.value is None:
            raise ValueError("AVAILABLE feature must carry a value")
        if (
            self.availability
            in {
                AvailabilityStatus.MISSING,
                AvailabilityStatus.NOT_APPLICABLE,
            }
            and self.value is not None
        ):
            raise ValueError("missing/not-applicable feature cannot carry a value")
        return self


class DecisionTraceV03(ContractModel):
    """DECISION-200..260 canonical v0.3 decision-time audit record."""

    decision_id: UUID
    decision_schema_version: str = Field(default="3.0", pattern=r"^3\.")
    decision_type: str = Field(min_length=1)
    owner_system: str = Field(min_length=1)
    decision_time: datetime

    teaching_context_ref: VersionedRef | None = None
    teaching_context_schema_version: str | None = None
    context_fingerprint: str | None = None
    context_source_refs: tuple[VersionedRef, ...] = ()

    policy_bundle_ref: VersionedRef | None = None
    policy_bundle_hash: str | None = None
    policy_version: str | None = None

    strategy_family: StrategyFamily | None = None
    strategy_version: str | None = None
    derived_teaching_stage: TeachingStage | None = None
    stage_mapper_version: str | None = None

    available_actions: tuple[dict[str, Any], ...] = ()
    hard_constraint_results: tuple[HardConstraintResultV03, ...] = ()
    hard_filtered_actions: tuple[HardFilteredActionV03, ...] = ()
    features: tuple[DecisionFeatureV03, ...] = ()
    candidate_scores: tuple[dict[str, Any], ...] = ()
    selected_teaching_action_ref: VersionedRef | None = None
    previous_teaching_action_ref: VersionedRef | None = None

    transition_reason_codes: tuple[str, ...] = ()
    material_evidence_refs: tuple[VersionedRef, ...] = ()
    anti_oscillation_decision: dict[str, Any] | None = None
    tie_break_reason: str | None = None

    experiment_assignment_ref: VersionedRef | None = None
    experiment_assignment_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    behavior_policy_type: BehaviorPolicyType
    action_propensity: float | None = Field(default=None, ge=0.0, le=1.0)

    algorithm: DecisionAlgorithm
    reason_codes: tuple[str, ...] = Field(min_length=1)
    replayability_status: ReplayabilityStatus
    replayability_reason_codes: tuple[str, ...] = ()
    migration_metadata: dict[str, Any] | None = None
    correlation_id: UUID | str
    trace_id: str = Field(min_length=1)
    created_at: datetime

    @field_validator("correlation_id", mode="before")
    @classmethod
    def normalize_correlation_id(cls, value: UUID | str) -> str:
        return str(value)

    @model_validator(mode="after")
    def enforce_probability_semantics(self) -> DecisionTraceV03:
        if (
            self.behavior_policy_type is BehaviorPolicyType.DETERMINISTIC
            and self.action_propensity is not None
        ):
            raise ValueError("deterministic B3 action_propensity must be null")
        return self

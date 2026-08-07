"""Askora v0.3 Adaptive Teaching Loop canonical public contracts.

The v0.2 contracts remain available from their historical modules for read/audit
compatibility.  New v0.3 writers must use the explicitly versioned contracts in
this module; their serialized payloads never contain the legacy integer support
fields or the nine-family strategy vocabulary.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.contracts.base import ContractModel


class AvailabilityStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    MISSING = "MISSING"
    STALE = "STALE"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class StrategyFamily(StrEnum):
    """DOMAIN-083/SYS05-201: the only v0.3 top-level strategy families."""

    EXPLICIT_INSTRUCTION = "EXPLICIT_INSTRUCTION"
    GUIDED_PRACTICE = "GUIDED_PRACTICE"
    FADING_PRACTICE = "FADING_PRACTICE"
    RETRIEVAL_PRACTICE = "RETRIEVAL_PRACTICE"
    ERROR_REMEDIATION = "ERROR_REMEDIATION"
    TRANSFER_CHALLENGE = "TRANSFER_CHALLENGE"


class InteractionMove(StrEnum):
    DIRECT_INSTRUCTION = "DIRECT_INSTRUCTION"
    WORKED_EXAMPLE = "WORKED_EXAMPLE"
    SOCRATIC_PROBE = "SOCRATIC_PROBE"
    SELF_EXPLANATION_PROMPT = "SELF_EXPLANATION_PROMPT"
    ORIENTATION_HINT = "ORIENTATION_HINT"
    CONCEPTUAL_HINT = "CONCEPTUAL_HINT"
    SUBGOAL_HINT = "SUBGOAL_HINT"
    PARTIAL_STEP = "PARTIAL_STEP"
    COMPLETION_PROBLEM = "COMPLETION_PROBLEM"
    FADING_STEP = "FADING_STEP"
    CORRECTNESS_FEEDBACK = "CORRECTNESS_FEEDBACK"
    PROCESS_FEEDBACK = "PROCESS_FEEDBACK"
    RETRIEVAL_REQUEST = "RETRIEVAL_REQUEST"
    DELAYED_RETRIEVAL_REQUEST = "DELAYED_RETRIEVAL_REQUEST"
    TRANSFER_TASK = "TRANSFER_TASK"
    DIRECT_ANSWER_OVERRIDE = "DIRECT_ANSWER_OVERRIDE"
    METACOGNITIVE_CHECK = "METACOGNITIVE_CHECK"


class ScaffoldControl(StrEnum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class HintSpecificity(StrEnum):
    NONE = "NONE"
    ORIENTATION = "ORIENTATION"
    CONCEPTUAL_STRATEGIC = "CONCEPTUAL_STRATEGIC"
    SUBGOAL = "SUBGOAL"
    PARTIAL_STEP = "PARTIAL_STEP"
    BOTTOM_OUT = "BOTTOM_OUT"


class AnswerExposure(StrEnum):
    NONE = "NONE"
    PARTIAL = "PARTIAL"
    COMPLETE = "COMPLETE"


class AssistanceState(StrEnum):
    INDEPENDENT = "INDEPENDENT"
    ASSISTED = "ASSISTED"
    ANSWER_EXPOSED = "ANSWER_EXPOSED"


class ErrorType(StrEnum):
    KNOWLEDGE_GAP = "KNOWLEDGE_GAP"
    CONCEPTUAL_MISCONCEPTION = "CONCEPTUAL_MISCONCEPTION"
    METHOD_SELECTION = "METHOD_SELECTION"
    EXECUTION = "EXECUTION"
    RETRIEVAL_FAILURE = "RETRIEVAL_FAILURE"
    TRANSFER_FAILURE = "TRANSFER_FAILURE"
    EXPRESSION_FORMAT = "EXPRESSION_FORMAT"
    UNKNOWN = "UNKNOWN"


class TeachingStage(StrEnum):
    DIAGNOSE = "DIAGNOSE"
    EXPLICIT_INSTRUCTION = "EXPLICIT_INSTRUCTION"
    GUIDED_PRACTICE = "GUIDED_PRACTICE"
    FADING_PRACTICE = "FADING_PRACTICE"
    RETRIEVAL_PRACTICE = "RETRIEVAL_PRACTICE"
    DELAYED_RETRIEVAL = "DELAYED_RETRIEVAL"
    ERROR_REMEDIATION = "ERROR_REMEDIATION"
    TRANSFER_CHALLENGE = "TRANSFER_CHALLENGE"


class ValidationObligation(StrEnum):
    NONE = "NONE"
    INDEPENDENT_VALIDATION_REQUIRED = "INDEPENDENT_VALIDATION_REQUIRED"


class ContaminationStatus(StrEnum):
    CLEAN = "CLEAN"
    POSSIBLE = "POSSIBLE"
    CONTAMINATED = "CONTAMINATED"
    UNKNOWN = "UNKNOWN"


class AttributionScope(StrEnum):
    ACTION_DIRECT = "ACTION_DIRECT"
    EPISODE_ASSOCIATED = "EPISODE_ASSOCIATED"
    TRAJECTORY_ASSOCIATED = "TRAJECTORY_ASSOCIATED"
    EXPERIMENTALLY_CAUSAL = "EXPERIMENTALLY_CAUSAL"
    UNATTRIBUTABLE = "UNATTRIBUTABLE"


class VersionedRef(ContractModel):
    """An exact immutable owner reference used by decision-time snapshots."""

    entity_type: str = Field(min_length=1)
    entity_id: str
    version: str | int

    @field_validator("entity_id", mode="before")
    @classmethod
    def normalize_entity_id(cls, value: UUID | str) -> str:
        return str(value)

    @field_validator("version")
    @classmethod
    def require_exact_version(cls, value: str | int) -> str | int:
        if isinstance(value, str) and not value.strip():
            raise ValueError("version must be an exact non-empty value")
        if isinstance(value, int) and value < 0:
            raise ValueError("integer version must be non-negative")
        return value


class ValueWithAvailability(ContractModel):
    """DOMAIN-005: missing is explicit and is never encoded as a numeric zero."""

    value: Any | None = None
    availability: AvailabilityStatus
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    source_refs: tuple[VersionedRef, ...] = ()

    @model_validator(mode="after")
    def validate_missing_semantics(self) -> ValueWithAvailability:
        if self.availability is AvailabilityStatus.AVAILABLE and self.value is None:
            raise ValueError("AVAILABLE values must carry a value")
        if (
            self.availability
            in {
                AvailabilityStatus.MISSING,
                AvailabilityStatus.NOT_APPLICABLE,
            }
            and self.value is not None
        ):
            raise ValueError(f"{self.availability.value} must not carry a value")
        return self


class ActionModifier(ContractModel):
    """DOMAIN-085: typed cross-cutting modifiers, never a StrategyFamily."""

    self_explanation: bool = False
    metacognitive_reflection: bool = False
    feedback_type: str | None = None
    representation_style: str | None = None
    transition_intent: str | None = None
    support_reason: tuple[str, ...] = ()
    target_scope: str | None = None
    delivery_mode: str | None = None


class AssistanceSnapshotV03(ContractModel):
    """DOMAIN-061..063/SYS04-210: actual orthogonal assistance facts."""

    assistance_schema_version: str = Field(default="3.0", pattern=r"^3\.")
    scaffold_control: ScaffoldControl
    hint_specificity: HintSpecificity
    answer_exposure: AnswerExposure
    assistance_state: AssistanceState
    hint_event_ids: tuple[UUID, ...] = ()
    support_reason: tuple[str, ...] = ()
    delivery_mode: str | None = None


class AssessmentDiagnosisV03(ContractModel):
    error_type: ErrorType
    diagnostic_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    diagnostic_evidence_refs: tuple[VersionedRef, ...] = ()
    misconception_evidence_refs: tuple[VersionedRef, ...] = ()
    alternative_hypotheses: tuple[dict[str, Any], ...] = ()
    needs_probe: bool = False
    reason_codes: tuple[str, ...] = ()


class AssessmentAttemptV03(ContractModel):
    """DOMAIN-061/SYS04-210: an Attempt with actual assistance frozen at submit time."""

    attempt_id: UUID
    attempt_schema_version: str = Field(default="3.0", pattern=r"^3\.")
    user_id: UUID
    session_id: UUID
    item_id: UUID
    item_version: str = Field(min_length=1)
    assessment_type: Literal["diagnostic", "formative", "summative", "review", "transfer"]
    started_at: datetime
    first_response_at: datetime | None = None
    submitted_at: datetime
    response_time_ms: int = Field(ge=0)
    raw_response: Any
    normalized_response: Any
    revision_count: int = Field(ge=0)
    assistance: AssistanceSnapshotV03
    idempotency_key: str = Field(min_length=1)


class AssessmentResultV03(ContractModel):
    """DOMAIN-070..074: a SYS04 measurement, never a mastery decision."""

    result_id: UUID
    result_schema_version: str = Field(default="3.0", pattern=r"^3\.")
    result_version: int = Field(ge=1)
    attempt_id: UUID
    item_id: UUID
    item_version: str = Field(min_length=1)
    score: float
    passed: bool | None
    correctness: Literal["correct", "partial", "incorrect", "unscorable"]
    rubric_scores: dict[str, Any]
    assessment_confidence: float = Field(ge=0.0, le=1.0)
    diagnosis: AssessmentDiagnosisV03
    assistance: AssistanceSnapshotV03
    evaluator_versions: tuple[str, ...]
    reviewer_result: Literal["accepted", "rejected", "needs_review"]
    created_at: datetime
    supersedes_result_id: UUID | None = None


class TeachingContextV03(ContractModel):
    """DOMAIN-088/SYS05-210..212: immutable exact-version policy input."""

    context_id: UUID
    context_schema_version: str = Field(default="3.0", pattern=r"^3\.")
    decision_time: datetime
    context_fingerprint: str = Field(min_length=1)
    learning_objective_ref: VersionedRef
    learning_activity_ref: VersionedRef
    activity_type: ValueWithAvailability
    target_capability: ValueWithAvailability
    current_task_ref: VersionedRef | None = None
    task_structure_refs: tuple[VersionedRef, ...] = ()
    mastery_estimate_ref: VersionedRef | None = None
    mastery_confidence: ValueWithAvailability
    prerequisite_state_refs: tuple[VersionedRef, ...] = ()
    prerequisite_confidence: ValueWithAvailability
    evidence_sufficiency: ValueWithAvailability
    recent_assessment_result_ref: VersionedRef | None = None
    correctness_score: ValueWithAvailability
    assessment_confidence: ValueWithAvailability
    error_type: ValueWithAvailability
    diagnostic_confidence: ValueWithAvailability
    misconception_evidence_refs: tuple[VersionedRef, ...] = ()
    alternative_diagnostic_hypotheses: tuple[dict[str, Any], ...] = ()
    needs_probe: ValueWithAvailability
    assistance_history_summary: dict[str, Any] = Field(default_factory=dict)
    scaffold_history: tuple[dict[str, Any], ...] = ()
    hint_history: tuple[dict[str, Any], ...] = ()
    answer_exposure_history: tuple[dict[str, Any], ...] = ()
    worked_example_exposure: ValueWithAvailability
    independent_success_history: tuple[VersionedRef, ...] = ()
    assisted_success_history: tuple[VersionedRef, ...] = ()
    previous_teaching_action_ref: VersionedRef | None = None
    previous_action_outcome_refs: tuple[VersionedRef, ...] = ()
    delayed_independent_evidence: ValueWithAvailability
    review_context: ValueWithAvailability
    transfer_evidence: ValueWithAvailability
    transfer_distance_novelty: ValueWithAvailability
    direct_answer_request: bool = False
    explanation_request: bool = False
    time_budget: ValueWithAvailability
    accessibility_constraints: tuple[dict[str, Any], ...] = ()
    experiment_assignment_ref: VersionedRef | None = None
    experiment_opt_out: bool = False
    source_refs: tuple[VersionedRef, ...]

    @model_validator(mode="after")
    def require_owner_sources(self) -> TeachingContextV03:
        if not self.source_refs:
            raise ValueError("TeachingContext must pin at least one exact owner source ref")
        return self


class PolicyBundleV03(ContractModel):
    """DOMAIN-089/SYS05-300..303 immutable policy manifest."""

    bundle_id: str = Field(min_length=1)
    schema_version: str = Field(default="3.0", pattern=r"^3\.")
    policy_version: str = Field(min_length=1)
    hard_rule_set_version: str = Field(min_length=1)
    stage_mapper_version: str = Field(min_length=1)
    candidate_table_version: str = Field(min_length=1)
    feature_schema_version: str = Field(min_length=1)
    normalization_version: str = Field(min_length=1)
    weight_profile_version: str = Field(min_length=1)
    anti_oscillation_profile_version: str = Field(min_length=1)
    tie_break_version: str = Field(min_length=1)
    fallback_profile_version: str = Field(min_length=1)
    subject_profile_version: str | None = None
    content_digest: str = Field(min_length=1)
    published_at: datetime


class PolicyBundleActivationV03(ContractModel):
    """Append-only atomic activation metadata; activation affects new actions only."""

    activation_id: UUID
    bundle_ref: VersionedRef
    activated_at: datetime
    supersedes_activation_id: UUID | None = None
    reason_codes: tuple[str, ...] = ()


class TeachingActionV03(ContractModel):
    """DOMAIN-090/SYS05: immutable canonical v0.3 executable decision."""

    action_id: UUID
    action_schema_version: str = Field(default="3.0", pattern=r"^3\.")
    learning_objective_ref: VersionedRef
    learning_activity_ref: VersionedRef
    strategy_family: StrategyFamily
    strategy_version: str = Field(min_length=1)
    teaching_stage: TeachingStage
    interaction_moves: tuple[InteractionMove, ...]
    action_modifiers: ActionModifier
    scaffold_control: ScaffoldControl
    hint_specificity: HintSpecificity
    answer_exposure: AnswerExposure
    evidence_requirements: tuple[str, ...] = ()
    expected_evidence_type: str | None = None
    success_condition: dict[str, Any]
    failure_condition: dict[str, Any]
    max_attempts: int | None = Field(default=None, ge=1)
    time_budget_seconds: int | None = Field(default=None, ge=1)
    validation_obligation: ValidationObligation = ValidationObligation.NONE
    reason_codes: tuple[str, ...] = Field(min_length=1)
    policy_bundle_ref: VersionedRef
    teaching_context_ref: VersionedRef
    decision_id: UUID
    created_at: datetime


class ExperimentAssignmentV03(ContractModel):
    assignment_id: UUID
    assignment_schema_version: str = Field(default="3.0", pattern=r"^3\.")
    experiment_id: str = Field(min_length=1)
    experiment_version: str = Field(min_length=1)
    unit_ref: str = Field(min_length=1)
    variant_id: str = Field(min_length=1)
    assignment_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    assigned_at: datetime
    opt_out: bool = False


class TeachingEpisodeV03(ContractModel):
    episode_id: UUID
    episode_schema_version: str = Field(default="3.0", pattern=r"^3\.")
    user_id: UUID
    learning_objective_ref: VersionedRef
    teaching_action_refs: tuple[VersionedRef, ...]
    started_at: datetime
    ended_at: datetime | None = None
    policy_bundle_refs: tuple[VersionedRef, ...]


class LearningTrajectoryV03(ContractModel):
    trajectory_id: UUID
    trajectory_schema_version: str = Field(default="3.0", pattern=r"^3\.")
    user_id: UUID
    learning_goal_ref: VersionedRef
    episode_refs: tuple[VersionedRef, ...]
    started_at: datetime
    ended_at: datetime | None = None


class OutcomeObservationV03(ContractModel):
    outcome_id: UUID
    outcome_schema_version: str = Field(default="3.0", pattern=r"^3\.")
    outcome_type: str = Field(min_length=1)
    measurement_reference: VersionedRef
    independence: bool | None = None
    assistance_state: AssistanceState | None = None
    scaffold_control: ScaffoldControl | None = None
    hint_specificity: HintSpecificity | None = None
    answer_exposure: AnswerExposure | None = None
    actual_delay_seconds: int | None = Field(default=None, ge=0)
    transfer_distance: str | None = None
    novelty: str | None = None
    score: float | None = None
    success: bool | None = None
    measurement_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    active_learning_time_seconds: int | None = Field(default=None, ge=0)
    time_cost_seconds: int | None = Field(default=None, ge=0)
    hint_cost: float | None = Field(default=None, ge=0.0)
    contamination_status: ContaminationStatus
    attribution_scope: AttributionScope
    teaching_episode_ref: VersionedRef | None = None
    learning_trajectory_ref: VersionedRef | None = None
    experiment_association: VersionedRef | None = None
    observed_at: datetime

    @model_validator(mode="after")
    def require_experiment_for_causal_attribution(self) -> OutcomeObservationV03:
        if (
            self.attribution_scope is AttributionScope.EXPERIMENTALLY_CAUSAL
            and self.experiment_association is None
        ):
            raise ValueError("EXPERIMENTALLY_CAUSAL requires an experiment association")
        return self

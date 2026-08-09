"""P1-01 SYS06 goal definition, draft, preview and state contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.contracts.adaptive import VersionedRef
from app.contracts.base import ContractModel

CognitiveProcess = Literal["recall", "understand", "explain", "apply", "transfer"]


class SuccessCriterionInputV1(ContractModel):
    criterion_id: UUID
    cognitive_process: CognitiveProcess
    statement: str = Field(min_length=1, max_length=500)
    evidence_requirements: tuple[str, ...] = Field(min_length=1, max_length=8)


class SuccessCriterionV1(SuccessCriterionInputV1):
    target_refs: tuple[VersionedRef, ...]


class LearningGoalDefinitionV2(ContractModel):
    goal_id: UUID
    definition_schema_version: Literal["2.0"] = "2.0"
    definition_version: int = Field(ge=1)
    user_id: UUID
    title: str = Field(min_length=1, max_length=200)
    topic: str = Field(min_length=1, max_length=200)
    target_capabilities: tuple[str, ...] = Field(min_length=1, max_length=12)
    application_context: str | None = Field(default=None, max_length=500)
    success_criteria: tuple[SuccessCriterionV1, ...] = Field(min_length=1, max_length=12)
    source_document_ids: tuple[UUID, ...] = Field(min_length=1, max_length=100)
    deadline_at: datetime | None = None
    weekly_time_budget_minutes: int | None = Field(default=None, ge=1, le=10_080)
    semantic_fingerprint: str = Field(min_length=64, max_length=64)
    created_at: datetime
    supersedes_definition_version: int | None = Field(default=None, ge=1)
    reason_codes: tuple[str, ...] = Field(min_length=1)


GoalStatus = Literal["confirmed", "active", "paused", "achieved", "archived"]


class LearningGoalStateV1(ContractModel):
    goal_id: UUID
    state_schema_version: Literal["1.0"] = "1.0"
    state_version: int = Field(ge=1)
    status: GoalStatus
    definition_version: int = Field(ge=1)
    mapping_ref: VersionedRef | None
    plan_ref: VersionedRef | None
    previous_status: GoalStatus | None
    reason_codes: tuple[str, ...] = Field(min_length=1)
    correlation_id: UUID
    created_at: datetime


class LearningPlanStateV1(ContractModel):
    plan_id: UUID
    plan_version: int = Field(ge=1)
    state_version: int = Field(ge=1)
    status: Literal["active", "paused", "completed", "superseded"]
    previous_status: Literal["active", "paused", "completed", "superseded"] | None
    reason_codes: tuple[str, ...] = Field(min_length=1)
    correlation_id: UUID
    created_at: datetime


class GoalSourceViewV1(ContractModel):
    document_id: UUID
    display_name: str
    status: Literal["executable", "waiting", "blocked"]
    reason_codes: tuple[str, ...]
    revision_ref: VersionedRef | None = None


class GoalTargetCardV1(ContractModel):
    target_id: UUID
    target_ref: VersionedRef
    name: str
    source_name: str
    evidence_excerpt: str
    recommended_reason: str


class LearningGoalDraftV1(ContractModel):
    draft_id: UUID
    draft_schema_version: Literal["1.0"] = "1.0"
    draft_version: int = Field(ge=1)
    user_id: UUID
    goal_id: UUID
    base_definition_version: int | None = Field(default=None, ge=1)
    status: Literal[
        "draft",
        "preview_ready",
        "approved_pending_boundary",
        "applying",
        "applied",
        "blocked",
        "cancelled",
    ]
    title: str = Field(min_length=1, max_length=200)
    topic: str = Field(min_length=1, max_length=200)
    target_capabilities: tuple[str, ...] = Field(min_length=1, max_length=12)
    application_context: str | None = Field(default=None, max_length=500)
    deadline_at: datetime | None = None
    weekly_time_budget_minutes: int | None = Field(default=None, ge=1, le=10_080)
    success_criteria: tuple[SuccessCriterionInputV1, ...] = Field(min_length=1, max_length=12)
    source_document_ids: tuple[UUID, ...] = Field(min_length=1, max_length=100)
    selected_target_ids: tuple[UUID, ...] = ()
    targets_confirmed: bool = False
    pending_preview_id: UUID | None = None
    block_reason_codes: tuple[str, ...] = ()
    created_at: datetime

    @model_validator(mode="after")
    def target_confirmation_is_explicit(self) -> LearningGoalDraftV1:
        if self.targets_confirmed and not self.selected_target_ids:
            raise ValueError("confirmed targets require a non-empty selection")
        return self


class GoalFieldDiffV1(ContractModel):
    field: str
    before: object | None
    after: object | None


class GoalChangePreviewV1(ContractModel):
    preview_id: UUID
    preview_schema_version: Literal["1.0"] = "1.0"
    preview_version: int = Field(ge=1)
    draft_id: UUID
    draft_version: int = Field(ge=1)
    goal_id: UUID
    input_refs: tuple[VersionedRef, ...] = Field(min_length=1)
    field_diffs: tuple[GoalFieldDiffV1, ...]
    sources: tuple[GoalSourceViewV1, ...] = ()
    target_cards: tuple[GoalTargetCardV1, ...]
    selected_target_ids: tuple[UUID, ...] = Field(min_length=1)
    plan_impact: dict[str, object]
    effective_timing: Literal["immediate", "activity_boundary"]
    active_activity_ref: VersionedRef | None = None
    expires_at: datetime
    created_at: datetime


class FocusedLearningGoalStateV1(ContractModel):
    user_id: UUID
    focus_version: int = Field(ge=1)
    goal_id: UUID | None
    reason_codes: tuple[str, ...] = Field(min_length=1)
    correlation_id: UUID
    created_at: datetime


class CreateGoalDraftCommandV1(ContractModel):
    source_document_ids: tuple[UUID, ...] = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    topic: str = Field(min_length=1, max_length=200)
    target_capabilities: tuple[str, ...] = Field(min_length=1, max_length=12)
    application_context: str | None = Field(default=None, max_length=500)
    deadline_at: datetime | None = None
    weekly_time_budget_minutes: int | None = Field(default=None, ge=1, le=10_080)
    success_criteria: tuple[SuccessCriterionInputV1, ...] = Field(min_length=1, max_length=12)
    idempotency_key: str = Field(min_length=8, max_length=200)


class UpdateGoalDraftCommandV1(ContractModel):
    expected_draft_version: int = Field(ge=1)
    source_document_ids: tuple[UUID, ...] | None = Field(default=None, min_length=1, max_length=100)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    topic: str | None = Field(default=None, min_length=1, max_length=200)
    target_capabilities: tuple[str, ...] | None = Field(default=None, min_length=1, max_length=12)
    application_context: str | None = Field(default=None, max_length=500)
    deadline_at: datetime | None = None
    weekly_time_budget_minutes: int | None = Field(default=None, ge=1, le=10_080)
    success_criteria: tuple[SuccessCriterionInputV1, ...] | None = Field(
        default=None, min_length=1, max_length=12
    )
    selected_target_ids: tuple[UUID, ...] | None = None
    targets_confirmed: bool | None = None
    idempotency_key: str = Field(min_length=8, max_length=200)


class PreviewGoalDraftCommandV1(ContractModel):
    expected_draft_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=200)


class ApplyGoalDraftCommandV1(ContractModel):
    expected_draft_version: int = Field(ge=1)
    expected_preview_version: int = Field(ge=1)
    preview_id: UUID
    boundary_mode: Literal["normal_boundary", "supersede_active"]
    set_focused: bool = False
    idempotency_key: str = Field(min_length=8, max_length=200)


class GoalApplyResultV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    draft_id: UUID
    draft_version: int
    goal_id: UUID
    status: Literal["approved_pending_boundary", "applied"]
    definition_ref: VersionedRef | None
    mapping_ref: VersionedRef | None
    plan_ref: VersionedRef | None
    activity_ref: VersionedRef | None
    reason_codes: tuple[str, ...]


class GoalTargetCardsResponseV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    draft_id: UUID
    draft_version: int
    targets: tuple[GoalTargetCardV1, ...]


class GoalDetailV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    definition: LearningGoalDefinitionV2
    state: LearningGoalStateV1
    plan_state: LearningPlanStateV1 | None = None
    focused: bool


class CreateEditGoalDraftCommandV1(ContractModel):
    expected_state_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=200)


class SuggestSuccessCriteriaRequestV1(ContractModel):
    topic: str = Field(min_length=1, max_length=200)
    cognitive_processes: tuple[CognitiveProcess, ...] = Field(min_length=1, max_length=5)


class SuggestSuccessCriteriaResponseV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    criteria: tuple[SuccessCriterionInputV1, ...]


class LearningObjectiveV1(ContractModel):
    objective_id: UUID
    objective_schema_version: Literal["1.0"] = "1.0"
    objective_version: int = Field(ge=1)
    goal_id: UUID
    definition_version: int = Field(ge=1)
    criterion_id: UUID
    cognitive_process: CognitiveProcess
    target_refs: tuple[VersionedRef, ...] = Field(min_length=1)
    evidence_requirements: tuple[str, ...] = Field(min_length=1)
    policy_ref: VersionedRef
    created_at: datetime


class GoalAchievementPolicyV1(ContractModel):
    policy_id: UUID
    policy_schema_version: Literal["1.0"] = "1.0"
    policy_version: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=120)
    delay_seconds: dict[CognitiveProcess, int]
    minimum_score: float = Field(ge=0.0, le=1.0)
    minimum_assessment_confidence: float = Field(ge=0.0, le=1.0)
    maximum_grader_disagreement: float = Field(ge=0.0, le=1.0)
    novelty_policy: dict[str, object]
    rubric_version: str = Field(min_length=1)
    grader_schema_version: str = Field(min_length=1)
    reviewer_required: bool = True
    created_at: datetime


GoalAssessmentStatus = Literal[
    "scheduled",
    "available",
    "submitted",
    "accepted",
    "needs_review",
    "scoring_failed",
    "cancelled",
]


class GoalAssessmentActivityV1(ContractModel):
    assessment_activity_id: UUID
    assessment_schema_version: Literal["1.0"] = "1.0"
    activity_version: int = Field(ge=1)
    user_id: UUID
    goal_id: UUID
    definition_version: int = Field(ge=1)
    objective_ref: VersionedRef
    criterion_id: UUID
    cognitive_process: CognitiveProcess
    scoring_method: Literal["structured", "open_response"]
    prompt: str = Field(min_length=1, max_length=2_000)
    status: GoalAssessmentStatus
    policy_ref: VersionedRef
    not_before: datetime
    result_ref: VersionedRef | None = None
    evidence_ref: VersionedRef | None = None
    reason_codes: tuple[str, ...] = Field(min_length=1)
    created_at: datetime


class ScheduleGoalAssessmentsCommandV1(ContractModel):
    expected_state_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=200)


class SubmitGoalAssessmentCommandV1(ContractModel):
    expected_state_version: int = Field(ge=1)
    expected_activity_version: int = Field(ge=1)
    response: str = Field(min_length=1, max_length=12_000)
    idempotency_key: str = Field(min_length=8, max_length=200)


class GoalCriterionEvaluationV1(ContractModel):
    criterion_id: UUID
    satisfied: bool
    assessment_result_refs: tuple[VersionedRef, ...] = ()
    learner_evidence_refs: tuple[VersionedRef, ...] = ()
    reason_codes: tuple[str, ...] = Field(min_length=1)


class GoalAchievementEvaluationV1(ContractModel):
    evaluation_id: UUID
    evaluation_schema_version: Literal["1.0"] = "1.0"
    evaluation_version: int = Field(ge=1)
    user_id: UUID
    goal_id: UUID
    definition_version: int = Field(ge=1)
    policy_ref: VersionedRef
    criterion_evaluations: tuple[GoalCriterionEvaluationV1, ...] = Field(min_length=1)
    open_validation_obligation_refs: tuple[VersionedRef, ...] = ()
    active_misconception_refs: tuple[VersionedRef, ...] = ()
    eligible_for_achievement: bool
    reason_codes: tuple[str, ...] = Field(min_length=1)
    created_at: datetime


class EvaluateGoalAchievementCommandV1(ContractModel):
    expected_state_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=200)


class GoalLifecycleCommandV1(ContractModel):
    expected_state_version: int = Field(ge=1)
    expected_plan_state_version: int | None = Field(default=None, ge=1)
    idempotency_key: str = Field(min_length=8, max_length=200)


class ConfirmGoalAchievementCommandV1(GoalLifecycleCommandV1):
    evaluation_id: UUID
    expected_evaluation_version: int = Field(ge=1)


class GoalLifecycleResultV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    state: LearningGoalStateV1
    plan_state: LearningPlanStateV1 | None = None
    copied_draft: LearningGoalDraftV1 | None = None
    reason_codes: tuple[str, ...] = Field(min_length=1)


class GoalAchievementWorkspaceV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    policy: GoalAchievementPolicyV1
    objectives: tuple[LearningObjectiveV1, ...]
    assessments: tuple[GoalAssessmentActivityV1, ...]
    latest_evaluation: GoalAchievementEvaluationV1 | None = None

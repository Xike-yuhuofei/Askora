"""跨系统共享的 v1 学习领域合同。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field

from app.contracts.base import ContractModel


class AssessmentResult(ContractModel):
    """DOMAIN-070：一次 Attempt 的评估测量，不包含 mastery 裁决。"""

    result_id: UUID
    result_version: int = Field(ge=1)
    attempt_id: UUID
    item_id: UUID
    item_version: str
    score: float
    passed: bool | None
    correctness: Literal["correct", "partial", "incorrect", "unscorable"]
    rubric_scores: dict[str, Any]
    error_type: (
        Literal[
            "knowledge_gap",
            "misconception",
            "condition_omission",
            "method_selection",
            "execution",
            "retrieval_failure",
            "transfer_failure",
            "expression_incomplete",
            "metacognitive",
            "unknown",
        ]
        | None
    )
    misconception_evidence: list[dict[str, Any]]
    independence: Literal["independent", "assisted", "answer_exposed"]
    assessment_confidence: float = Field(ge=0.0, le=1.0)
    evaluator_versions: list[str]
    reason_codes: list[str]
    reviewer_result: Literal["accepted", "rejected", "needs_review"]
    created_at: datetime
    supersedes_result_id: UUID | None = None


class LearnerEvidence(ContractModel):
    """DOMAIN-071：由 learner-model 接纳的版本化学习证据。"""

    evidence_id: UUID
    user_id: UUID
    knowledge_unit_id: UUID
    attempt_id: UUID | None = None
    result_id: UUID | None = None
    accepted_at: datetime
    dimension: Literal["recall", "routine_application", "transfer", "explanation"]
    outcome: Literal["success", "partial", "failure"]
    score: float
    confidence: float = Field(ge=0.0, le=1.0)
    independence: Literal["independent", "assisted", "answer_exposed"]
    delay_seconds: int = Field(ge=0)
    novelty: Literal["repeated", "near_variant", "far_variant"]
    evidence_weight: float = Field(ge=0.0)
    item_difficulty: float | None = None
    source_event_ids: list[UUID]
    eligibility_reason_codes: list[str]


class MasteryEstimate(ContractModel):
    """DOMAIN-080：4.3 拥有的 mastery 估计快照。"""

    estimate_id: UUID
    version: int = Field(ge=1)
    user_id: UUID
    knowledge_unit_id: UUID
    competence_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    independent_success_count: int = Field(ge=0)
    hint_dependency_score: float = Field(ge=0.0)
    last_independent_success_at: datetime | None = None
    delayed_recall_evidence_count: int = Field(ge=0)
    transfer_evidence_count: int = Field(ge=0)
    active_misconception_ids: list[UUID]
    evidence_count: int = Field(ge=0)
    effective_evidence_weight: float = Field(ge=0.0)
    algorithm_id: str
    algorithm_version: str
    source_evidence_ids: list[UUID]
    created_at: datetime


class TeachingAction(ContractModel):
    """DOMAIN-090：4.5 已决定且只能由 4.8 忠实执行的动作。"""

    action_id: UUID
    learning_objective_id: UUID
    learning_activity_id: UUID
    strategy_id: str
    strategy_version: str
    action_type: Literal[
        "explain",
        "worked_example",
        "socratic_question",
        "hint",
        "practice",
        "assessment",
        "feedback",
        "transfer_task",
        "reflection",
    ]
    scaffold_level: int = Field(ge=0)
    hint_level: int = Field(ge=0)
    answer_exposure_max: Literal[0, 1, 2, 3, 4]
    evidence_requirements: list[str]
    expected_evidence_type: str | None = None
    success_condition: dict[str, Any]
    failure_condition: dict[str, Any]
    max_attempts: int | None = Field(default=None, ge=1)
    time_budget_seconds: int | None = Field(default=None, ge=1)
    reason_codes: list[str]
    policy_version: str
    decision_id: UUID


class EvidenceItem(ContractModel):
    evidence_id: UUID
    source_span_ids: list[UUID]
    knowledge_unit_ids: list[UUID]
    pedagogical_role: Literal[
        "definition",
        "example",
        "counterexample",
        "prerequisite",
        "hint",
        "rubric",
        "solution",
        "context",
    ]
    content: str
    relevance: float | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    exposure_level: Literal[0, 1, 2, 3, 4]
    allowed_use: Literal["learner_visible", "grader_only", "internal_only"]


class EvidenceBundle(ContractModel):
    """DOMAIN-050：4.2 选择并约束的本轮证据集合。"""

    bundle_id: UUID
    request_id: UUID
    teaching_action_id: UUID | None = None
    assessment_context_id: UUID | None = None
    source_scope: dict[str, Any]
    index_versions: dict[str, Any]
    items: list[EvidenceItem]
    conflicts: list[dict[str, Any]]
    missing_roles: list[str]
    bundle_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    retrieval_trace_id: UUID


class LearningActivity(ContractModel):
    activity_id: UUID
    plan_id: UUID
    plan_version: int = Field(ge=1)
    objective_id: UUID
    type: Literal[
        "learn_new",
        "prerequisite_remediation",
        "diagnostic",
        "practice",
        "delayed_review",
        "transfer_check",
        "metacognitive_review",
    ]
    knowledge_unit_ids: list[UUID]
    estimated_duration_minutes: int = Field(ge=0)
    priority: float
    reason_codes: list[str]
    status: Literal["planned", "available", "active", "completed", "skipped", "superseded"]


class LearningPlan(ContractModel):
    plan_id: UUID
    version: int = Field(ge=1)
    learning_goal_id: UUID
    planning_horizon: dict[str, Any]
    objective_ids: list[UUID]
    activity_ids: list[UUID]
    constraints: dict[str, Any]
    assumptions: dict[str, Any]
    created_from_learner_state_version: int = Field(ge=0)
    knowledge_graph_version: str
    review_schedule_version: str | None = None
    reason_codes: list[str]
    status: Literal["active", "superseded", "completed", "paused"]


class ReviewSchedule(ContractModel):
    """DOMAIN-100：4.7 拥有的复习推荐状态。"""

    schedule_id: UUID
    version: int = Field(ge=1)
    user_id: UUID
    knowledge_unit_id: UUID
    memory_model: str
    model_version: str
    difficulty: float | None = None
    stability: float | None = None
    retrievability: float | None = Field(default=None, ge=0.0, le=1.0)
    desired_retention: float = Field(ge=0.0, le=1.0)
    last_valid_retrieval_at: datetime | None = None
    next_due_at: datetime | None = None
    review_priority: float
    evidence_quality: float = Field(ge=0.0, le=1.0)
    source_event_ids: list[UUID]
    created_at: datetime

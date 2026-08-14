"""SYS06/SYS07 的公共输入与派生投影合同。"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.contracts.adaptive import VersionedRef
from app.contracts.base import ContractModel


class ReviewObservation(ContractModel):
    observation_id: UUID
    user_id: UUID
    knowledge_unit_id: UUID
    observed_at: datetime
    actual_reviewed_at: datetime
    retrieval_required: bool
    independence: Literal["independent", "assisted", "answer_exposed"]
    hint_level: int = Field(ge=0)
    answer_seen_before_attempt: bool
    assessment_confidence: float = Field(ge=0.0, le=1.0)
    outcome: Literal["success", "partial", "failure"]
    delay_seconds: int = Field(ge=0)
    source_evidence_id: UUID
    source_event_ids: list[UUID]


class ReviewDueCandidate(ContractModel):
    schedule_id: UUID
    schedule_version: int = Field(ge=1)
    user_id: UUID
    knowledge_unit_id: UUID
    status: Literal["not_due", "due", "overdue"]
    recommended_due_at: datetime | None
    projected_at: datetime
    urgency: float = Field(ge=0.0)


class ConfirmedLearningGoal(ContractModel):
    goal_id: UUID
    objective_id: UUID
    target_knowledge_unit_ids: list[UUID]
    confirmed_at: datetime


class LearningGoalV1(ContractModel):
    """DOMAIN-010/011 SYS06-owned immutable goal version."""

    goal_id: UUID
    goal_schema_version: str = Field(default="1.0", pattern=r"^1\.")
    version: int = Field(ge=1)
    user_id: UUID
    title: str = Field(min_length=1, max_length=200)
    topic: str = Field(min_length=1, max_length=200)
    target_capabilities: tuple[str, ...] = Field(min_length=1)
    application_context: str | None = Field(default=None, max_length=500)
    success_criteria: tuple[str, ...] = Field(min_length=1)
    source_document_ids: tuple[UUID, ...]
    deadline_at: datetime | None = None
    weekly_time_budget_minutes: int | None = Field(default=None, ge=1)
    status: Literal["candidate", "confirmed", "active", "achieved", "paused", "archived"]
    confirmed_by_user: bool
    created_at: datetime
    confirmed_at: datetime | None = None
    supersedes_version: int | None = Field(default=None, ge=1)
    model_inference_refs: tuple[UUID, ...] = ()
    reason_codes: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def enforce_confirmation_owner(self) -> LearningGoalV1:
        if self.status in {"confirmed", "active"}:
            if self.confirmed_at is None:
                raise ValueError("confirmed/active goal requires confirmed_at")
            system_adopted = "GOAL_SYSTEM_ADOPTED_FROM_MATERIAL" in self.reason_codes
            if not self.confirmed_by_user and not system_adopted:
                raise ValueError(
                    "confirmed/active goal requires explicit user confirmation or system adoption"
                )
        if self.status == "candidate" and self.confirmed_by_user:
            raise ValueError("candidate goal cannot be user-confirmed")
        return self


class GoalFormationInferenceV1(ContractModel):
    """Persisted bounded model candidate; never a goal or mapping decision."""

    inference_id: UUID
    inference_schema_version: str = Field(default="1.0", pattern=r"^1\.")
    goal_id: UUID
    input_digest: str = Field(min_length=64, max_length=64)
    provider: str | None = None
    model_name: str | None = None
    model_snapshot: str | None = None
    prompt_version: str
    output_schema_version: str
    structured_result: dict[str, object] | None = None
    status: Literal["succeeded", "unavailable", "invalid"]
    reason_codes: tuple[str, ...] = Field(min_length=1)
    created_at: datetime


class GoalTargetEvidenceV1(ContractModel):
    """Exact selected/excluded KU evidence used by a mapping decision."""

    knowledge_unit_id: UUID
    knowledge_unit_ref: str = Field(min_length=1)
    source_document_id: UUID
    material_revision_id: UUID
    source_span_ids: tuple[UUID, ...] = Field(min_length=1)
    rank_positions: dict[str, int]
    fusion_score: float = Field(ge=0.0)
    reason_codes: tuple[str, ...] = Field(min_length=1)


class GoalKnowledgeMappingV1(ContractModel):
    """SPEC-D04 SYS06 decision record; not a SYS01 knowledge fact."""

    mapping_id: UUID
    mapping_schema_version: str = Field(default="1.0", pattern=r"^1\.")
    mapping_version: int = Field(ge=1)
    goal_id: UUID
    goal_version: int = Field(ge=1)
    source_document_ids: tuple[UUID, ...]
    knowledge_graph_versions: tuple[str, ...]
    candidate_target_ids: tuple[UUID, ...]
    selected_target_ids: tuple[UUID, ...]
    excluded_target_ids: tuple[UUID, ...]
    target_evidence: tuple[GoalTargetEvidenceV1, ...]
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    reason_codes: tuple[str, ...] = Field(min_length=1)
    mapper_version: str
    model_inference_refs: tuple[UUID, ...] = ()
    status: Literal["candidate", "confirmed", "blocked", "superseded"]
    clarification_question: str | None = None
    created_at: datetime

    @model_validator(mode="after")
    def enforce_executable_mapping(self) -> GoalKnowledgeMappingV1:
        evidence_ids = {item.knowledge_unit_id for item in self.target_evidence}
        if not set(self.selected_target_ids).issubset(evidence_ids):
            raise ValueError("selected targets require exact target evidence")
        if self.status == "confirmed" and not self.selected_target_ids:
            raise ValueError("confirmed mapping requires selected targets")
        if self.status == "blocked" and not self.clarification_question:
            raise ValueError("blocked mapping requires bounded clarification")
        return self


class GoalSpecificKnowledgeSubgraphV1(ContractModel):
    """SYS06 read-only planning projection over exact SYS01 relation refs."""

    subgraph_id: UUID
    subgraph_schema_version: str = Field(default="1.0", pattern=r"^1\.")
    version: int = Field(ge=1)
    goal_mapping_ref: VersionedRef
    target_knowledge_unit_ids: tuple[UUID, ...]
    included_prerequisite_ids: tuple[UUID, ...]
    relation_refs: tuple[VersionedRef, ...]
    knowledge_graph_versions: tuple[str, ...]
    closure_policy_version: str
    reason_codes: tuple[str, ...] = Field(min_length=1)
    created_at: datetime


class DiagnosticPrerequisiteEdgeV1(ContractModel):
    """Exact published SYS01 edge used as a SYS06 decision input reference."""

    prerequisite_id: UUID
    target_knowledge_unit_id: UUID
    relation_ref: VersionedRef


class DiagnosticNeedV1(ContractModel):
    """SPEC-D05 SYS06-owned immutable prerequisite diagnostic decision."""

    need_id: UUID
    diagnostic_need_schema_version: str = Field(default="1.0", pattern=r"^1\.")
    version: int = Field(ge=1)
    user_id: UUID
    goal_mapping_ref: VersionedRef
    goal_subgraph_ref: VersionedRef
    target_knowledge_unit_id: UUID
    prerequisite_knowledge_unit_ids: tuple[UUID, ...]
    prerequisite_edges: tuple[DiagnosticPrerequisiteEdgeV1, ...]
    unknown_ids: tuple[UUID, ...]
    unmet_ids: tuple[UUID, ...]
    sufficient_current_evidence_ids: tuple[UUID, ...]
    reason_codes: tuple[str, ...] = Field(min_length=1)
    planner_version: str = Field(min_length=1)
    diagnostic_planner_version: str = Field(min_length=1)
    budget_policy_version: str = Field(min_length=1)
    max_attempts: int = Field(ge=1)
    attempts_used: int = Field(ge=0)
    created_from_learner_state_version: int = Field(ge=1)
    knowledge_graph_versions: tuple[str, ...]
    current_knowledge_unit_id: UUID | None = None
    assessment_item_ref: VersionedRef | None = None
    assessment_result_refs: tuple[VersionedRef, ...] = ()
    status: Literal["active", "resolved", "blocked", "stopped"]
    stop_reason: (
        Literal[
            "ALL_DECISION_RELEVANT_PREREQUISITES_RESOLVED",
            "TARGET_READY",
            "REMEDIATION_REQUIRED",
            "DIAGNOSTIC_BUDGET_EXHAUSTED",
            "NO_VALID_ASSESSMENT_ITEM",
            "LOW_CONFIDENCE_REQUIRES_REVIEW",
            "USER_STOPPED",
            "SYSTEM_BLOCKED",
        ]
        | None
    ) = None
    created_at: datetime
    supersedes_version: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def enforce_diagnostic_partition_and_stop(self) -> DiagnosticNeedV1:
        prerequisites = set(self.prerequisite_knowledge_unit_ids)
        partitions = (
            set(self.unknown_ids),
            set(self.unmet_ids),
            set(self.sufficient_current_evidence_ids),
        )
        if any(not part.issubset(prerequisites) for part in partitions):
            raise ValueError("diagnostic classifications must stay inside prerequisite scope")
        if any(
            partitions[index] & partitions[other] for index in range(3) for other in range(index)
        ):
            raise ValueError("diagnostic prerequisite classifications must be disjoint")
        if self.attempts_used > self.max_attempts:
            raise ValueError("diagnostic attempts cannot exceed the versioned budget")
        if self.status == "active":
            if self.stop_reason is not None or self.current_knowledge_unit_id is None:
                raise ValueError("active diagnostic requires a selected knowledge unit and no stop")
        elif self.stop_reason is None:
            raise ValueError("terminal diagnostic requires an explicit stop reason")
        if self.assessment_item_ref is not None and self.current_knowledge_unit_id is None:
            raise ValueError("assessment item requires a selected diagnostic knowledge unit")
        return self

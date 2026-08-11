"""UI-01 read-only workspace response contracts.

These contracts compose owner-published state for presentation only. They do
not create a new domain owner or authorize any write command.

Spec coverage: UI-DATA-001..004, UI-DATA-020..032, UI01-VSLICE-AC-003/004.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.contracts.adaptive import AvailabilityStatus
from app.contracts.base import ContractModel
from app.contracts.library_management import LibraryCollectionViewV1, LibraryTagViewV1


class WorkspaceSourceSystem(StrEnum):
    PLATFORM_WORKSPACE = "PLATFORM_WORKSPACE"
    SYS01 = "SYS01"
    SYS03 = "SYS03"
    SYS06 = "SYS06"
    SYS07 = "SYS07"
    LEGACY_COMPATIBILITY = "LEGACY_COMPATIBILITY"


class WorkspaceSourceStatusV1(ContractModel):
    source_system: WorkspaceSourceSystem
    availability: AvailabilityStatus
    source_ref: str | None = None
    reason_codes: tuple[str, ...] = ()


class WorkspaceContextItemV1(ContractModel):
    workspace_id: UUID
    workspace_ref: str
    display_name: str
    version: int = Field(ge=1)
    lifecycle: Literal["active", "trash"]
    is_default: bool


class WorkspaceContextDataV1(ContractModel):
    view_state: Literal["READY", "MISSING", "PARTIAL", "STALE"]
    current_workspace: WorkspaceContextItemV1 | None = None
    switch_capability: Literal["SINGLE_WORKSPACE", "UNAVAILABLE"]


class WorkspaceContextResponseV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    generated_at: datetime
    data: WorkspaceContextDataV1
    source_status: tuple[WorkspaceSourceStatusV1, ...]
    correlation_id: str


class ActiveGoalSummaryV1(ContractModel):
    goal_ref: str
    title: str
    status: str
    target_capabilities: tuple[str, ...]


class ActivitySummaryV1(ContractModel):
    activity_ref: str
    objective_ref: str
    type: str
    title: str
    estimated_duration_minutes: int | None
    reason_codes: tuple[str, ...]
    status: str
    launch_state: Literal["ACTIVE", "RESUMABLE", "REQUIRES_START_COMMAND", "UNAVAILABLE"]


class ReviewDueCandidateViewV1(ContractModel):
    knowledge_unit_ref: str
    schedule_ref: str
    next_due_at: datetime
    review_priority: float
    evidence_quality: float
    included_activity_ref: str | None = None


class CurrentEvidenceSummaryV1(ContractModel):
    knowledge_unit_ref: str | None
    confidence: float | None
    independent_success_count: int | None
    delayed_recall_evidence_count: int | None
    transfer_evidence_count: int | None
    validation_obligation: Literal["NONE", "INDEPENDENT_VALIDATION_REQUIRED", "UNKNOWN"]


class CompatibilitySessionSummaryV1(ContractModel):
    session_id: UUID
    title: str | None
    subject: str
    knowledge_point_id: str | None
    status: Literal["active", "ended", "archived"]
    updated_at: datetime


class CompatibilityQuickStartV1(ContractModel):
    source_label: Literal["LEGACY_COMPATIBILITY"] = "LEGACY_COMPATIBILITY"
    recent_sessions: tuple[CompatibilitySessionSummaryV1, ...] = ()


class TodayWorkspaceDataV1(ContractModel):
    local_date: date
    timezone: str
    view_state: Literal["READY", "PARTIAL", "EMPTY"]
    active_goal: ActiveGoalSummaryV1 | None = None
    current_activity: ActivitySummaryV1 | None = None
    planned_activities: tuple[ActivitySummaryV1, ...] = ()
    review_due_candidates: tuple[ReviewDueCandidateViewV1, ...] = ()
    current_evidence_summary: CurrentEvidenceSummaryV1 | None = None
    compatibility_quick_start: CompatibilityQuickStartV1


class TodayWorkspaceResponseV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    generated_at: datetime
    data: TodayWorkspaceDataV1
    source_status: tuple[WorkspaceSourceStatusV1, ...]
    correlation_id: str


class GoalListItemV1(ContractModel):
    goal_ref: str
    title: str
    topic: str
    target_capabilities: tuple[str, ...]
    success_criteria: tuple[str, ...]
    deadline_at: datetime | None = None
    weekly_time_budget_minutes: int | None = None
    status: str
    confirmed_by_user: bool


class GoalListDataV1(ContractModel):
    view_state: Literal["READY", "EMPTY"]
    goals: tuple[GoalListItemV1, ...] = ()


class GoalListResponseV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    generated_at: datetime
    data: GoalListDataV1
    source_status: tuple[WorkspaceSourceStatusV1, ...]
    correlation_id: str


class LearningPathObjectiveV1(ContractModel):
    objective_ref: str
    capability: str | None = None
    cognitive_process: str | None = None
    status: str | None = None
    activity_refs: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = ()


class LearningPathActivityV1(ContractModel):
    activity_ref: str
    objective_ref: str
    type: str
    title: str
    estimated_duration_minutes: int
    priority: float
    reason_codes: tuple[str, ...]
    status: str
    launch_state: Literal["ACTIVE", "RESUMABLE", "REQUIRES_START_COMMAND", "UNAVAILABLE"]


class LearningPathViewV1(ContractModel):
    plan_ref: str
    goal_ref: str
    status: Literal["active", "superseded", "completed", "paused"]
    created_from_learner_state_version: int
    knowledge_graph_version: str
    review_schedule_version: str | None = None
    assumptions: dict
    reason_codes: tuple[str, ...]
    objectives: tuple[LearningPathObjectiveV1, ...]
    activities: tuple[LearningPathActivityV1, ...]


class LearningPathDataV1(ContractModel):
    view_state: Literal["READY", "PARTIAL", "EMPTY"]
    selected_goal_ref: str | None = None
    available_goal_refs: tuple[str, ...] = ()
    learning_path: LearningPathViewV1 | None = None
    reason_codes: tuple[str, ...] = ()


class LearningPathResponseV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    generated_at: datetime
    data: LearningPathDataV1
    source_status: tuple[WorkspaceSourceStatusV1, ...]
    correlation_id: str


class EvidenceEntryV1(ContractModel):
    knowledge_unit_ref: str
    label: str | None = None
    competence_probability: float | None = None
    confidence: float | None = None
    independent_success_count: int | None = None
    delayed_recall_evidence_count: int | None = None
    transfer_evidence_count: int | None = None
    evidence_count: int | None = None
    effective_evidence_weight: float | None = None
    active_misconception_ids: tuple[UUID, ...] | None = None
    algorithm_id: str | None = None
    algorithm_version: str | None = None
    product_label: str | None = None
    product_label_rule_version: str | None = None


class LegacyEvidenceCompatibilityV1(ContractModel):
    visible_by_default: Literal[False] = False
    fields: dict = Field(default_factory=dict)
    source_label: Literal["LEGACY_COMPATIBILITY"] = "LEGACY_COMPATIBILITY"


class EvidenceProfileDataV1(ContractModel):
    view_state: Literal["READY", "PARTIAL", "EMPTY"]
    knowledge_units_assessed: int
    entries: tuple[EvidenceEntryV1, ...] = ()
    legacy_compatibility: LegacyEvidenceCompatibilityV1


class EvidenceProfileResponseV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    generated_at: datetime
    data: EvidenceProfileDataV1
    source_status: tuple[WorkspaceSourceStatusV1, ...]
    correlation_id: str


class LibraryDocumentViewV1(ContractModel):
    document_ref: str
    document_id: UUID
    title: str
    metadata_version: int = 1
    media_type: str
    file_size_bytes: int
    subject: str | None = None
    author: str | None = None
    language: str | None = None
    tags: tuple[LibraryTagViewV1, ...] = ()
    collections: tuple[LibraryCollectionViewV1, ...] = ()
    match_field: Literal["title", "body"] | None = None
    match_excerpt: str | None = None
    match_source_span_ref: str | None = None
    processing_status: Literal[
        "pending", "processing", "completed", "failed", "rejected", "quarantined"
    ]
    moderation_status: Literal["pending", "approved", "requires_review", "rejected"]
    current_revision_ref: str | None = None
    knowledge_status: Literal["NOT_MODELED", "CANDIDATES", "PUBLISHED", "LEGACY_COMPATIBILITY"]
    knowledge_unit_count: int
    relation_count: int
    reason_codes: tuple[str, ...] = ()
    created_at: datetime
    updated_at: datetime


class LibraryWorkspaceDataV1(ContractModel):
    view_state: Literal["READY", "PARTIAL", "STALE", "EMPTY"]
    total: int
    page: int
    page_size: int
    documents: tuple[LibraryDocumentViewV1, ...]
    available_tags: tuple[LibraryTagViewV1, ...] = ()
    available_collections: tuple[LibraryCollectionViewV1, ...] = ()


class LibraryWorkspaceResponseV1(ContractModel):
    schema_version: Literal["1.0", "1.1"] = "1.0"
    generated_at: datetime
    data: LibraryWorkspaceDataV1
    source_status: tuple[WorkspaceSourceStatusV1, ...]
    correlation_id: str


class KnowledgeMapScopeV1(ContractModel):
    document_refs: tuple[str, ...]
    subject: str | None = None
    graph_version: str


class KnowledgeMapNodeV1(ContractModel):
    knowledge_unit_ref: str
    kind: str
    canonical_name: str
    description: str
    provenance_type: str
    confidence: float | None = None
    status: Literal["candidate", "verified", "published", "rejected", "superseded"]
    evidence_span_refs: tuple[str, ...]
    learner_evidence_summary: dict | None = None


class KnowledgeMapEdgeV1(ContractModel):
    relation_ref: str
    prerequisite_ref: str
    target_ref: str
    strength: Literal["hard", "soft", "contextual"]
    confidence: float | None = None
    status: Literal["candidate", "published", "rejected", "superseded"]
    evidence_span_refs: tuple[str, ...]


class SourceSpanViewV1(ContractModel):
    source_span_ref: str
    source_span_id: UUID
    document_id: UUID
    page: int | None = None
    chapter: str | None = None
    start_offset: int | None = None
    end_offset: int | None = None
    excerpt: str


class KnowledgeMapDataV1(ContractModel):
    scope: KnowledgeMapScopeV1
    nodes: tuple[KnowledgeMapNodeV1, ...]
    edges: tuple[KnowledgeMapEdgeV1, ...]
    source_spans: tuple[SourceSpanViewV1, ...]


class KnowledgeMapResponseV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    generated_at: datetime
    data: KnowledgeMapDataV1
    source_status: tuple[WorkspaceSourceStatusV1, ...]
    correlation_id: str

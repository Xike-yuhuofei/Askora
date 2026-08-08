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

from app.contracts.adaptive import AvailabilityStatus
from app.contracts.base import ContractModel


class WorkspaceSourceSystem(StrEnum):
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


class LibraryDocumentViewV1(ContractModel):
    document_ref: str
    document_id: UUID
    title: str
    media_type: str
    file_size_bytes: int
    subject: str | None = None
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


class LibraryWorkspaceResponseV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
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

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

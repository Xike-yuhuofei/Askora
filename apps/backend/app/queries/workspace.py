"""Read-only workspace query composition for UI-01.

The query deliberately avoids SYS06 plan/activity persistence: the current
schema has no safe public current-user ownership query or canonical
activity/session link. SYS06 is therefore reported as unavailable instead of
being inferred from legacy sessions.

Spec coverage: UI-DATA-001..004, UI01-VSLICE-AC-003/004, DEP-004.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Literal, cast
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts import AvailabilityStatus, ReviewSchedule
from app.contracts.workspace import (
    CompatibilityQuickStartV1,
    CompatibilitySessionSummaryV1,
    ReviewDueCandidateViewV1,
    TodayWorkspaceDataV1,
    TodayWorkspaceResponseV1,
    WorkspaceSourceStatusV1,
    WorkspaceSourceSystem,
)
from app.models.dialog import DialogSession, SessionStatus
from app.models.planning import ReviewScheduleRecord
from app.models.user import User


class WorkspaceTodayQueryService:
    """Compose an honest UI read model without acquiring domain ownership."""

    def __init__(
        self,
        db: AsyncSession,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._db = db
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    async def get_today(
        self,
        current_user: User,
        *,
        timezone_name: str,
        correlation_id: str,
    ) -> TodayWorkspaceResponseV1:
        generated_at = self._clock()
        local_timezone = ZoneInfo(timezone_name)
        review_due = await self._load_review_due(current_user, generated_at)
        recent_sessions = await self._load_recent_sessions(current_user)

        return TodayWorkspaceResponseV1(
            generated_at=generated_at,
            correlation_id=correlation_id,
            data=TodayWorkspaceDataV1(
                local_date=generated_at.astimezone(local_timezone).date(),
                timezone=timezone_name,
                view_state="PARTIAL",
                active_goal=None,
                current_activity=None,
                planned_activities=(),
                review_due_candidates=tuple(review_due),
                current_evidence_summary=None,
                compatibility_quick_start=CompatibilityQuickStartV1(
                    recent_sessions=tuple(recent_sessions)
                ),
            ),
            source_status=(
                WorkspaceSourceStatusV1(
                    source_system=WorkspaceSourceSystem.SYS06,
                    availability=AvailabilityStatus.MISSING,
                    reason_codes=("OWNER_QUERY_UNAVAILABLE",),
                ),
                WorkspaceSourceStatusV1(
                    source_system=WorkspaceSourceSystem.SYS07,
                    availability=AvailabilityStatus.AVAILABLE,
                    reason_codes=("LATEST_USER_SCHEDULES",),
                ),
                WorkspaceSourceStatusV1(
                    source_system=WorkspaceSourceSystem.SYS03,
                    availability=AvailabilityStatus.NOT_APPLICABLE,
                    reason_codes=("NO_CURRENT_ACTIVITY",),
                ),
                WorkspaceSourceStatusV1(
                    source_system=WorkspaceSourceSystem.LEGACY_COMPATIBILITY,
                    availability=AvailabilityStatus.AVAILABLE,
                    reason_codes=("DIALOG_SESSION_COMPATIBILITY",),
                ),
            ),
        )

    async def _load_review_due(
        self, current_user: User, generated_at: datetime
    ) -> list[ReviewDueCandidateViewV1]:
        records = (
            await self._db.scalars(
                select(ReviewScheduleRecord)
                .where(ReviewScheduleRecord.user_id == str(current_user.id))
                .order_by(
                    ReviewScheduleRecord.knowledge_unit_id,
                    ReviewScheduleRecord.version.desc(),
                )
            )
        ).all()
        latest_by_unit: dict[str, ReviewScheduleRecord] = {}
        for record in records:
            latest_by_unit.setdefault(record.knowledge_unit_id, record)

        candidates: list[ReviewDueCandidateViewV1] = []
        for record in latest_by_unit.values():
            schedule = ReviewSchedule.model_validate(record.payload)
            if str(schedule.user_id) != str(current_user.id):
                raise ValueError("review schedule payload owner mismatch")
            if schedule.next_due_at is None or schedule.next_due_at > generated_at:
                continue
            candidates.append(
                ReviewDueCandidateViewV1(
                    knowledge_unit_ref=f"knowledge_unit:{schedule.knowledge_unit_id}",
                    schedule_ref=(f"review_schedule:{schedule.schedule_id}:v{schedule.version}"),
                    next_due_at=schedule.next_due_at,
                    review_priority=schedule.review_priority,
                    evidence_quality=schedule.evidence_quality,
                )
            )
        return sorted(
            candidates,
            key=lambda item: (
                item.next_due_at,
                -item.review_priority,
                item.knowledge_unit_ref,
            ),
        )

    async def _load_recent_sessions(
        self, current_user: User
    ) -> list[CompatibilitySessionSummaryV1]:
        sessions = (
            await self._db.scalars(
                select(DialogSession)
                .where(
                    DialogSession.user_id == str(current_user.id),
                    DialogSession.status != SessionStatus.DELETED,
                )
                .order_by(DialogSession.updated_at.desc(), DialogSession.id)
                .limit(5)
            )
        ).all()
        return [
            CompatibilitySessionSummaryV1(
                session_id=UUID(session.id),
                title=session.title,
                subject=session.subject,
                knowledge_point_id=session.knowledge_point_id,
                status=cast(
                    Literal["active", "ended", "archived"],
                    session.status.value,
                ),
                updated_at=self._as_utc(session.updated_at),
            )
            for session in sessions
        ]

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        """Restore SQLite's timezone-stripped UTC timestamp for public output."""
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

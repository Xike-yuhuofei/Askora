"""Current-user read-only workspace query composition.

The assembler reads exact owner-published records and never writes domain
state. Missing objective metadata and ambiguous current-plan scope stay
explicit instead of being inferred from legacy sessions or presentation data.

Spec coverage: UI-DATA-001..004/020..042/070..083,
UI02B-VSLICE-AC-001..007, ADR-0006.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal, cast
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts import AvailabilityStatus, ReviewSchedule
from app.contracts.learning import LearningActivity, LearningPlan
from app.contracts.planning import LearningGoalV1
from app.contracts.workspace import (
    ActiveGoalSummaryV1,
    ActivitySummaryV1,
    CompatibilityQuickStartV1,
    CompatibilitySessionSummaryV1,
    CurrentEvidenceSummaryV1,
    EvidenceEntryV1,
    EvidenceProfileDataV1,
    EvidenceProfileResponseV1,
    GoalListDataV1,
    GoalListItemV1,
    GoalListResponseV1,
    LearningPathActivityV1,
    LearningPathDataV1,
    LearningPathObjectiveV1,
    LearningPathResponseV1,
    LearningPathViewV1,
    LegacyEvidenceCompatibilityV1,
    ReviewDueCandidateViewV1,
    TodayWorkspaceDataV1,
    TodayWorkspaceResponseV1,
    WorkspaceSourceStatusV1,
    WorkspaceSourceSystem,
)
from app.core.exceptions import BusinessError, ResourceNotFoundError
from app.domains.content_knowledge import CONTENT_RECORD_KEY
from app.infrastructure.activity_lifecycle import ActivityLifecycleRepository
from app.models.assessment import MasteryEstimateRecord
from app.models.dialog import DialogSession, SessionStatus
from app.models.document import ModerationStatus, ProcessingStatus, UserDocument
from app.models.planning import (
    LearningActivityRecord,
    LearningGoalRecord,
    LearningPlanRecord,
    ReviewScheduleRecord,
)
from app.models.user import User
from app.services.owner.canonical_identity import canonical_user_id

_ACTIVITY_TITLES = {
    "learn_new": "学习新内容",
    "prerequisite_remediation": "补齐前置知识",
    "diagnostic": "检查当前基础",
    "practice": "练习与巩固",
    "delayed_review": "延迟复习",
    "transfer_check": "迁移应用",
    "metacognitive_review": "复盘学习方法",
}


@dataclass(frozen=True)
class _PathSelection:
    goal: LearningGoalV1 | None
    plan: LearningPlan | None
    activities: tuple[LearningActivity, ...]
    available_goal_refs: tuple[str, ...]
    reason_codes: tuple[str, ...]


class WorkspaceTodayQueryService:
    """Compose UI read models without acquiring any domain ownership."""

    def __init__(
        self,
        db: AsyncSession,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._db = db
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    async def list_goals(
        self,
        current_user: User,
        *,
        correlation_id: str,
    ) -> GoalListResponseV1:
        goals = await self._latest_goals(current_user)
        items = tuple(
            GoalListItemV1(
                goal_ref=self._goal_ref(goal),
                title=goal.title,
                topic=goal.topic,
                target_capabilities=goal.target_capabilities,
                success_criteria=goal.success_criteria,
                deadline_at=goal.deadline_at,
                weekly_time_budget_minutes=goal.weekly_time_budget_minutes,
                status=goal.status,
                confirmed_by_user=goal.confirmed_by_user,
            )
            for goal in goals
        )
        return GoalListResponseV1(
            generated_at=self._clock(),
            correlation_id=correlation_id,
            data=GoalListDataV1(
                view_state="READY" if items else "EMPTY",
                goals=items,
            ),
            source_status=(
                WorkspaceSourceStatusV1(
                    source_system=WorkspaceSourceSystem.SYS06,
                    availability=AvailabilityStatus.AVAILABLE,
                    reason_codes=("LATEST_CURRENT_USER_GOAL_VERSIONS",),
                ),
            ),
        )

    async def get_path(
        self,
        current_user: User,
        *,
        goal_id: UUID | None,
        correlation_id: str,
    ) -> LearningPathResponseV1:
        selection = await self._select_path(current_user, goal_id=goal_id)
        path = self._path_view(selection)
        if path is None and "MULTIPLE_CURRENT_PLANS_REQUIRE_GOAL_SCOPE" in selection.reason_codes:
            view_state: Literal["READY", "PARTIAL", "EMPTY"] = "PARTIAL"
        elif path is None:
            view_state = "EMPTY"
        elif any(reason == "OBJECTIVE_METADATA_UNAVAILABLE" for reason in selection.reason_codes):
            view_state = "PARTIAL"
        else:
            view_state = "READY"
        source_ref = self._plan_ref(selection.plan) if selection.plan is not None else None
        availability = (
            AvailabilityStatus.AVAILABLE
            if selection.plan is not None or selection.available_goal_refs
            else AvailabilityStatus.MISSING
        )
        return LearningPathResponseV1(
            generated_at=self._clock(),
            correlation_id=correlation_id,
            data=LearningPathDataV1(
                view_state=view_state,
                selected_goal_ref=(
                    self._goal_ref(selection.goal) if selection.goal is not None else None
                ),
                available_goal_refs=selection.available_goal_refs,
                learning_path=path,
                reason_codes=selection.reason_codes,
            ),
            source_status=(
                WorkspaceSourceStatusV1(
                    source_system=WorkspaceSourceSystem.SYS06,
                    availability=availability,
                    source_ref=source_ref,
                    reason_codes=selection.reason_codes,
                ),
            ),
        )

    async def get_evidence(
        self,
        current_user: User,
        *,
        correlation_id: str,
    ) -> EvidenceProfileResponseV1:
        records = await self._latest_mastery_records(current_user)
        labels = await self._knowledge_labels(current_user)
        entries: list[EvidenceEntryV1] = []
        missing_labels = False
        for record in records:
            payload = record.payload
            label_record = labels.get(record.knowledge_unit_id)
            if label_record is None:
                missing_labels = True
                knowledge_ref = f"knowledge_unit:{record.knowledge_unit_id}:version-unavailable"
                label = None
            else:
                label, revision = label_record
                knowledge_ref = f"knowledge_unit:{record.knowledge_unit_id}:v{revision}"
            entries.append(
                EvidenceEntryV1(
                    knowledge_unit_ref=knowledge_ref,
                    label=label,
                    competence_probability=self._optional_float(
                        payload.get("competence_probability")
                    ),
                    confidence=self._optional_float(payload.get("confidence")),
                    independent_success_count=self._optional_int(
                        payload.get("independent_success_count")
                    ),
                    delayed_recall_evidence_count=self._optional_int(
                        payload.get("delayed_recall_evidence_count")
                    ),
                    transfer_evidence_count=self._optional_int(
                        payload.get("transfer_evidence_count")
                    ),
                    evidence_count=self._optional_int(payload.get("evidence_count")),
                    effective_evidence_weight=self._optional_float(
                        payload.get("effective_evidence_weight")
                    ),
                    active_misconception_ids=(
                        tuple(UUID(str(item)) for item in payload["active_misconception_ids"])
                        if payload.get("active_misconception_ids") is not None
                        else None
                    ),
                    algorithm_id=self._optional_str(payload.get("algorithm_id")),
                    algorithm_version=self._optional_str(payload.get("algorithm_version")),
                    product_label=None,
                    product_label_rule_version=None,
                )
            )
        view_state: Literal["READY", "PARTIAL", "EMPTY"]
        if not entries:
            view_state = "EMPTY"
        elif missing_labels:
            view_state = "PARTIAL"
        else:
            view_state = "READY"
        if not entries:
            sys01_availability = AvailabilityStatus.NOT_APPLICABLE
            sys01_reasons = ("NO_MASTERY_ENTRIES_TO_LABEL",)
        elif missing_labels:
            sys01_availability = AvailabilityStatus.MISSING
            sys01_reasons = ("KNOWLEDGE_UNIT_LABEL_UNAVAILABLE",)
        else:
            sys01_availability = AvailabilityStatus.AVAILABLE
            sys01_reasons = ("CURRENT_USER_KNOWLEDGE_LABELS",)
        return EvidenceProfileResponseV1(
            generated_at=self._clock(),
            correlation_id=correlation_id,
            data=EvidenceProfileDataV1(
                view_state=view_state,
                knowledge_units_assessed=len(entries),
                entries=tuple(entries),
                legacy_compatibility=LegacyEvidenceCompatibilityV1(),
            ),
            source_status=(
                WorkspaceSourceStatusV1(
                    source_system=WorkspaceSourceSystem.SYS03,
                    availability=AvailabilityStatus.AVAILABLE,
                    reason_codes=("LATEST_CURRENT_USER_MASTERY_VERSIONS",),
                ),
                WorkspaceSourceStatusV1(
                    source_system=WorkspaceSourceSystem.SYS01,
                    availability=sys01_availability,
                    reason_codes=sys01_reasons,
                ),
                WorkspaceSourceStatusV1(
                    source_system=WorkspaceSourceSystem.LEGACY_COMPATIBILITY,
                    availability=AvailabilityStatus.NOT_APPLICABLE,
                    reason_codes=("LEGACY_PROFILE_EXCLUDED_FROM_PRIMARY_EVIDENCE",),
                ),
            ),
        )

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
        selection = await self._select_path(current_user, goal_id=None)
        current_activity = self._current_activity(selection.activities)
        planned = tuple(
            self._activity_summary(item)
            for item in selection.activities
            if current_activity is None or item.activity_id != current_activity.activity_id
        )
        current_summary = (
            self._activity_summary(current_activity) if current_activity is not None else None
        )
        current_evidence = await self._current_evidence_summary(current_user, current_activity)
        has_plan = selection.plan is not None
        if has_plan:
            sys06_availability = AvailabilityStatus.AVAILABLE
        elif selection.available_goal_refs:
            sys06_availability = AvailabilityStatus.AVAILABLE
        else:
            sys06_availability = AvailabilityStatus.MISSING
        evidence_availability = (
            AvailabilityStatus.AVAILABLE
            if current_evidence is not None
            else AvailabilityStatus.NOT_APPLICABLE
        )
        evidence_reasons = (
            ("CURRENT_ACTIVITY_MASTERY_AVAILABLE",)
            if current_evidence is not None
            else (
                ("CURRENT_ACTIVITY_EVIDENCE_MISSING",)
                if current_activity
                else ("NO_CURRENT_ACTIVITY",)
            )
        )

        return TodayWorkspaceResponseV1(
            generated_at=generated_at,
            correlation_id=correlation_id,
            data=TodayWorkspaceDataV1(
                local_date=generated_at.astimezone(local_timezone).date(),
                timezone=timezone_name,
                view_state="READY" if has_plan else "PARTIAL",
                active_goal=(
                    ActiveGoalSummaryV1(
                        goal_ref=self._goal_ref(selection.goal),
                        title=selection.goal.title,
                        status=selection.goal.status,
                        target_capabilities=selection.goal.target_capabilities,
                    )
                    if selection.goal is not None
                    else None
                ),
                current_activity=current_summary,
                planned_activities=planned,
                review_due_candidates=tuple(review_due),
                current_evidence_summary=current_evidence,
                compatibility_quick_start=CompatibilityQuickStartV1(
                    recent_sessions=tuple(recent_sessions)
                ),
            ),
            source_status=(
                WorkspaceSourceStatusV1(
                    source_system=WorkspaceSourceSystem.SYS06,
                    availability=sys06_availability,
                    source_ref=(
                        self._plan_ref(selection.plan) if selection.plan is not None else None
                    ),
                    reason_codes=(
                        selection.reason_codes
                        if selection.reason_codes
                        else (
                            ("CURRENT_PLAN_AVAILABLE",)
                            if has_plan
                            else ("CURRENT_PLAN_NOT_AVAILABLE",)
                        )
                    ),
                ),
                WorkspaceSourceStatusV1(
                    source_system=WorkspaceSourceSystem.SYS07,
                    availability=AvailabilityStatus.AVAILABLE,
                    reason_codes=("LATEST_USER_SCHEDULES",),
                ),
                WorkspaceSourceStatusV1(
                    source_system=WorkspaceSourceSystem.SYS03,
                    availability=evidence_availability,
                    reason_codes=evidence_reasons,
                ),
                WorkspaceSourceStatusV1(
                    source_system=WorkspaceSourceSystem.LEGACY_COMPATIBILITY,
                    availability=AvailabilityStatus.AVAILABLE,
                    reason_codes=("DIALOG_SESSION_COMPATIBILITY",),
                ),
            ),
        )

    async def _latest_goals(self, current_user: User) -> list[LearningGoalV1]:
        owner_id = str(canonical_user_id(current_user.id))
        records = (
            await self._db.scalars(
                select(LearningGoalRecord)
                .where(LearningGoalRecord.user_id == owner_id)
                .order_by(LearningGoalRecord.goal_id, LearningGoalRecord.version.desc())
            )
        ).all()
        latest: dict[str, LearningGoalV1] = {}
        for record in records:
            if record.goal_id in latest:
                continue
            goal = LearningGoalV1.model_validate(record.payload)
            if str(goal.user_id) != owner_id or str(goal.goal_id) != record.goal_id:
                raise ValueError("learning goal owner or identity mismatch")
            latest[record.goal_id] = goal
        return sorted(
            latest.values(), key=lambda item: (-item.created_at.timestamp(), str(item.goal_id))
        )

    async def _select_path(
        self,
        current_user: User,
        *,
        goal_id: UUID | None,
    ) -> _PathSelection:
        goals = await self._latest_goals(current_user)
        goals_by_id = {goal.goal_id: goal for goal in goals}
        if goal_id is not None and goal_id not in goals_by_id:
            raise ResourceNotFoundError("学习目标")

        eligible = [
            goal for goal in goals if goal.status in {"confirmed", "active", "paused", "achieved"}
        ]
        plans = await self._latest_plans(eligible)
        current_goal_refs = tuple(
            self._goal_ref(goal)
            for goal in eligible
            if (plan := plans.get(goal.goal_id)) is not None and plan.status in {"active", "paused"}
        )

        selected_goal: LearningGoalV1 | None
        selected_plan: LearningPlan | None
        if goal_id is not None:
            selected_goal = goals_by_id[goal_id]
            selected_plan = plans.get(goal_id)
            reasons = (
                ("CURRENT_PLAN_AVAILABLE", "OBJECTIVE_METADATA_UNAVAILABLE")
                if selected_plan is not None
                else ("CURRENT_PLAN_NOT_AVAILABLE",)
            )
        else:
            candidates = [
                goal
                for goal in eligible
                if (plan := plans.get(goal.goal_id)) is not None
                and plan.status in {"active", "paused"}
            ]
            if len(candidates) > 1:
                return _PathSelection(
                    goal=None,
                    plan=None,
                    activities=(),
                    available_goal_refs=current_goal_refs,
                    reason_codes=("MULTIPLE_CURRENT_PLANS_REQUIRE_GOAL_SCOPE",),
                )
            selected_goal = candidates[0] if candidates else None
            selected_plan = plans.get(selected_goal.goal_id) if selected_goal is not None else None
            reasons = (
                ("CURRENT_PLAN_AVAILABLE", "OBJECTIVE_METADATA_UNAVAILABLE")
                if selected_plan is not None
                else ("CURRENT_PLAN_NOT_AVAILABLE",)
            )

        activities = (
            await self._ordered_activities(selected_plan) if selected_plan is not None else ()
        )
        return _PathSelection(
            goal=selected_goal,
            plan=selected_plan,
            activities=activities,
            available_goal_refs=current_goal_refs,
            reason_codes=reasons,
        )

    async def _latest_plans(self, goals: list[LearningGoalV1]) -> dict[UUID, LearningPlan]:
        goal_ids = [str(goal.goal_id) for goal in goals]
        if not goal_ids:
            return {}
        records = (
            await self._db.scalars(
                select(LearningPlanRecord)
                .where(LearningPlanRecord.learning_goal_id.in_(goal_ids))
                .order_by(
                    LearningPlanRecord.learning_goal_id,
                    LearningPlanRecord.version.desc(),
                )
            )
        ).all()
        latest: dict[UUID, LearningPlan] = {}
        seen_goal_ids: set[UUID] = set()
        for record in records:
            goal_key = UUID(record.learning_goal_id)
            if goal_key in seen_goal_ids:
                continue
            seen_goal_ids.add(goal_key)
            plan = LearningPlan.model_validate(record.payload).model_copy(
                update={"status": record.status}
            )
            if plan.learning_goal_id != goal_key or str(plan.plan_id) != record.plan_id:
                raise ValueError("learning plan identity mismatch")
            if plan.status == "superseded":
                continue
            latest[goal_key] = plan
        return latest

    async def _ordered_activities(self, plan: LearningPlan) -> tuple[LearningActivity, ...]:
        records = (
            await self._db.scalars(
                select(LearningActivityRecord).where(
                    LearningActivityRecord.plan_id == str(plan.plan_id),
                    LearningActivityRecord.plan_version == plan.version,
                )
            )
        ).all()
        by_id: dict[UUID, LearningActivity] = {}
        states = await ActivityLifecycleRepository(self._db).latest_for_plan(
            plan_id=plan.plan_id,
            plan_version=plan.version,
        )
        for record in records:
            activity = LearningActivity.model_validate(record.payload)
            if activity.plan_id != plan.plan_id or activity.plan_version != plan.version:
                raise ValueError("learning activity plan mismatch")
            state = states.get(activity.activity_id)
            if state is None:
                raise BusinessError(
                    message="学习活动尚未完成生命周期迁移",
                    error_code="LEGACY_ACTIVITY_STATE_UNMIGRATED",
                    status_code=409,
                )
            by_id[activity.activity_id] = activity.model_copy(update={"status": state.status})
        return tuple(by_id[item] for item in plan.activity_ids if item in by_id)

    def _path_view(self, selection: _PathSelection) -> LearningPathViewV1 | None:
        if selection.goal is None or selection.plan is None:
            return None
        plan = selection.plan
        activities = tuple(self._path_activity(item) for item in selection.activities)
        objective_refs = tuple(
            self._objective_ref(objective_id, plan.version) for objective_id in plan.objective_ids
        )
        return LearningPathViewV1(
            plan_ref=self._plan_ref(plan),
            goal_ref=self._goal_ref(selection.goal),
            status=plan.status,
            created_from_learner_state_version=plan.created_from_learner_state_version,
            knowledge_graph_version=plan.knowledge_graph_version,
            review_schedule_version=plan.review_schedule_version,
            assumptions=plan.assumptions,
            reason_codes=tuple(plan.reason_codes),
            objectives=tuple(
                LearningPathObjectiveV1(
                    objective_ref=objective_ref,
                    activity_refs=tuple(
                        item.activity_ref
                        for item in activities
                        if item.objective_ref == objective_ref
                    ),
                    reason_codes=("OBJECTIVE_METADATA_UNAVAILABLE",),
                )
                for objective_ref in objective_refs
            ),
            activities=activities,
        )

    def _path_activity(self, activity: LearningActivity) -> LearningPathActivityV1:
        return LearningPathActivityV1(
            activity_ref=self._activity_ref(activity),
            objective_ref=self._objective_ref(activity.objective_id, activity.plan_version),
            type=activity.type,
            title=_ACTIVITY_TITLES.get(activity.type, "学习活动"),
            estimated_duration_minutes=activity.estimated_duration_minutes,
            priority=activity.priority,
            reason_codes=tuple(activity.reason_codes),
            status=activity.status,
            launch_state=self._launch_state(activity.status),
        )

    def _activity_summary(self, activity: LearningActivity) -> ActivitySummaryV1:
        launch_state: Literal["ACTIVE", "RESUMABLE", "REQUIRES_START_COMMAND", "UNAVAILABLE"] = (
            self._launch_state(activity.status)
        )
        return ActivitySummaryV1(
            activity_ref=self._activity_ref(activity),
            objective_ref=self._objective_ref(activity.objective_id, activity.plan_version),
            type=activity.type,
            title=_ACTIVITY_TITLES.get(activity.type, "学习活动"),
            estimated_duration_minutes=activity.estimated_duration_minutes,
            reason_codes=tuple(activity.reason_codes),
            status=activity.status,
            launch_state=launch_state,
        )

    @staticmethod
    def _launch_state(
        status: str,
    ) -> Literal["ACTIVE", "RESUMABLE", "REQUIRES_START_COMMAND", "UNAVAILABLE"]:
        if status == "active":
            return "RESUMABLE"
        if status == "available":
            return "REQUIRES_START_COMMAND"
        return "UNAVAILABLE"

    @staticmethod
    def _current_activity(activities: tuple[LearningActivity, ...]) -> LearningActivity | None:
        for status in ("active", "available", "planned"):
            match = next((item for item in activities if item.status == status), None)
            if match is not None:
                return match
        return None

    async def _latest_mastery_records(self, current_user: User) -> list[MasteryEstimateRecord]:
        owner_id = str(canonical_user_id(current_user.id))
        records = (
            await self._db.scalars(
                select(MasteryEstimateRecord)
                .where(MasteryEstimateRecord.user_id == owner_id)
                .order_by(
                    MasteryEstimateRecord.knowledge_unit_id,
                    MasteryEstimateRecord.version.desc(),
                )
            )
        ).all()
        latest: dict[str, MasteryEstimateRecord] = {}
        for record in records:
            latest.setdefault(record.knowledge_unit_id, record)
        return list(latest.values())

    async def _current_evidence_summary(
        self,
        current_user: User,
        activity: LearningActivity | None,
    ) -> CurrentEvidenceSummaryV1 | None:
        if activity is None or not activity.knowledge_unit_ids:
            return None
        wanted = str(activity.knowledge_unit_ids[0])
        record = next(
            (
                item
                for item in await self._latest_mastery_records(current_user)
                if item.knowledge_unit_id == wanted
            ),
            None,
        )
        if record is None:
            return None
        payload = record.payload
        return CurrentEvidenceSummaryV1(
            knowledge_unit_ref=f"knowledge_unit:{wanted}:version-unavailable",
            confidence=self._optional_float(payload.get("confidence")),
            independent_success_count=self._optional_int(payload.get("independent_success_count")),
            delayed_recall_evidence_count=self._optional_int(
                payload.get("delayed_recall_evidence_count")
            ),
            transfer_evidence_count=self._optional_int(payload.get("transfer_evidence_count")),
            validation_obligation="UNKNOWN",
        )

    async def _knowledge_labels(self, current_user: User) -> dict[str, tuple[str, int]]:
        documents = (
            await self._db.scalars(
                select(UserDocument).where(
                    UserDocument.pseudonym_id == current_user.pseudonym_id,
                    UserDocument.is_deleted.is_(False),
                    UserDocument.processing_status == ProcessingStatus.COMPLETED,
                    UserDocument.moderation_status != ModerationStatus.REJECTED,
                )
            )
        ).all()
        found: dict[str, tuple[str, int]] = {}
        conflicts: set[str] = set()
        for document in documents:
            revision = self._current_revision(document)
            if revision is None:
                continue
            for raw in revision.get("knowledge_units", []):
                unit_id = str(raw.get("knowledge_unit_id", ""))
                label = str(raw.get("canonical_name", "")).strip()
                revision_number = int(raw.get("revision", 1))
                if not unit_id or not label:
                    continue
                candidate = (label, revision_number)
                if unit_id in found and found[unit_id] != candidate:
                    conflicts.add(unit_id)
                else:
                    found[unit_id] = candidate
        for unit_id in conflicts:
            found.pop(unit_id, None)
        return found

    async def _load_review_due(
        self, current_user: User, generated_at: datetime
    ) -> list[ReviewDueCandidateViewV1]:
        owner_id = str(canonical_user_id(current_user.id))
        records = (
            await self._db.scalars(
                select(ReviewScheduleRecord)
                .where(ReviewScheduleRecord.user_id == owner_id)
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
            if str(schedule.user_id) != owner_id:
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
    def _current_revision(document: UserDocument) -> dict[str, Any] | None:
        record = (document.moderation_details or {}).get(CONTENT_RECORD_KEY, {})
        current_id = record.get("current_revision_id")
        return next(
            (item for item in record.get("revisions", []) if item.get("revision_id") == current_id),
            None,
        )

    @staticmethod
    def _goal_ref(goal: LearningGoalV1) -> str:
        return f"learning_goal:{goal.goal_id}:v{goal.version}"

    @staticmethod
    def _plan_ref(plan: LearningPlan) -> str:
        return f"learning_plan:{plan.plan_id}:v{plan.version}"

    @staticmethod
    def _objective_ref(objective_id: UUID, plan_version: int) -> str:
        return f"learning_objective:{objective_id}:v{plan_version}"

    @staticmethod
    def _activity_ref(activity: LearningActivity) -> str:
        return f"learning_activity:{activity.activity_id}:v{activity.plan_version}"

    @staticmethod
    def _optional_int(value: Any) -> int | None:
        return int(value) if value is not None else None

    @staticmethod
    def _optional_float(value: Any) -> float | None:
        return float(value) if value is not None else None

    @staticmethod
    def _optional_str(value: Any) -> str | None:
        return str(value) if value is not None else None

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        """Restore SQLite's timezone-stripped UTC timestamp for public output."""
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

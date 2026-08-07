"""SYS06/SYS07 durable version repositories。"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.learning import LearningActivity, LearningPlan, ReviewSchedule
from app.contracts.planning import ReviewObservation
from app.domains.learning_planner import PlannerDecision
from app.models.planning import (
    LearningActivityRecord,
    LearningPlanRecord,
    ReviewObservationRecord,
    ReviewScheduleRecord,
)


class ReviewScheduleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def has_observation(self, observation_id: UUID) -> bool:
        return await self._session.get(ReviewObservationRecord, str(observation_id)) is not None

    async def save_observation(self, observation: ReviewObservation) -> None:
        if await self.has_observation(observation.observation_id):
            return
        self._session.add(
            ReviewObservationRecord(
                id=str(observation.observation_id),
                user_id=str(observation.user_id),
                knowledge_unit_id=str(observation.knowledge_unit_id),
                actual_reviewed_at=observation.actual_reviewed_at,
                payload=observation.model_dump(mode="json"),
            )
        )
        await self._session.flush()

    async def invalidate_observation(self, observation_id: UUID) -> None:
        record = await self._session.get(ReviewObservationRecord, str(observation_id))
        if record is None:
            raise KeyError(f"review observation not found: {observation_id}")
        record.invalidated_at = datetime.now(timezone.utc)
        await self._session.flush()

    async def list_valid_observations(
        self, *, user_id: UUID, knowledge_unit_id: UUID
    ) -> list[ReviewObservation]:
        records = (
            await self._session.scalars(
                select(ReviewObservationRecord)
                .where(
                    ReviewObservationRecord.user_id == str(user_id),
                    ReviewObservationRecord.knowledge_unit_id == str(knowledge_unit_id),
                    ReviewObservationRecord.invalidated_at.is_(None),
                )
                .order_by(
                    ReviewObservationRecord.actual_reviewed_at, ReviewObservationRecord.id
                )
            )
        ).all()
        return [ReviewObservation.model_validate(record.payload) for record in records]

    async def latest(
        self, *, user_id: UUID, knowledge_unit_id: UUID
    ) -> ReviewSchedule | None:
        record = await self._session.scalar(
            select(ReviewScheduleRecord)
            .where(
                ReviewScheduleRecord.user_id == str(user_id),
                ReviewScheduleRecord.knowledge_unit_id == str(knowledge_unit_id),
            )
            .order_by(ReviewScheduleRecord.version.desc())
            .limit(1)
        )
        return ReviewSchedule.model_validate(record.payload) if record else None

    async def save(self, schedule: ReviewSchedule) -> ReviewSchedule:
        record_id = f"{schedule.schedule_id}:{schedule.version}"
        existing = await self._session.get(ReviewScheduleRecord, record_id)
        if existing is not None:
            return ReviewSchedule.model_validate(existing.payload)
        self._session.add(
            ReviewScheduleRecord(
                id=record_id,
                schedule_id=str(schedule.schedule_id),
                user_id=str(schedule.user_id),
                knowledge_unit_id=str(schedule.knowledge_unit_id),
                version=schedule.version,
                next_due_at=schedule.next_due_at,
                payload=schedule.model_dump(mode="json"),
            )
        )
        await self._session.flush()
        return schedule

    async def list_latest_for_user(self, user_id: UUID) -> list[ReviewSchedule]:
        records = (
            await self._session.scalars(
                select(ReviewScheduleRecord)
                .where(ReviewScheduleRecord.user_id == str(user_id))
                .order_by(ReviewScheduleRecord.knowledge_unit_id, ReviewScheduleRecord.version.desc())
            )
        ).all()
        latest: dict[str, ReviewScheduleRecord] = {}
        for record in records:
            latest.setdefault(record.knowledge_unit_id, record)
        return [ReviewSchedule.model_validate(record.payload) for record in latest.values()]


class LearningPlanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_idempotency(self, idempotency_key: str) -> LearningPlan | None:
        record = await self._session.scalar(
            select(LearningPlanRecord).where(
                LearningPlanRecord.idempotency_key == idempotency_key
            )
        )
        return self._to_plan(record) if record else None

    async def next_version(self, learning_goal_id: UUID) -> int:
        latest = await self._session.scalar(
            select(func.max(LearningPlanRecord.version)).where(
                LearningPlanRecord.learning_goal_id == str(learning_goal_id)
            )
        )
        return int(latest or 0) + 1

    async def save(self, decision: PlannerDecision, *, idempotency_key: str) -> LearningPlan:
        plan = decision.plan
        prior = await self._session.scalar(
            select(LearningPlanRecord)
            .where(
                LearningPlanRecord.learning_goal_id == str(plan.learning_goal_id),
                LearningPlanRecord.status.in_(["active", "paused"]),
            )
            .order_by(LearningPlanRecord.version.desc())
            .limit(1)
        )
        if prior is not None and prior.version < plan.version:
            prior.status = "superseded"
            prior.superseded_by_version = plan.version
        record_id = f"{plan.plan_id}:{plan.version}"
        existing = await self._session.get(LearningPlanRecord, record_id)
        if existing is not None:
            return self._to_plan(existing)
        self._session.add(
            LearningPlanRecord(
                id=record_id,
                plan_id=str(plan.plan_id),
                learning_goal_id=str(plan.learning_goal_id),
                idempotency_key=idempotency_key,
                version=plan.version,
                status=plan.status,
                payload=plan.model_dump(mode="json"),
            )
        )
        for activity in decision.activities:
            self._session.add(
                LearningActivityRecord(
                    id=str(activity.activity_id),
                    plan_id=str(activity.plan_id),
                    plan_version=activity.plan_version,
                    priority=activity.priority,
                    payload=activity.model_dump(mode="json"),
                )
            )
        await self._session.flush()
        return plan

    async def list_versions(self, learning_goal_id: UUID) -> list[LearningPlan]:
        records = (
            await self._session.scalars(
                select(LearningPlanRecord)
                .where(LearningPlanRecord.learning_goal_id == str(learning_goal_id))
                .order_by(LearningPlanRecord.version)
            )
        ).all()
        return [self._to_plan(record) for record in records]

    async def activities(self, *, plan_id: UUID, plan_version: int) -> list[LearningActivity]:
        records = (
            await self._session.scalars(
                select(LearningActivityRecord)
                .where(
                    LearningActivityRecord.plan_id == str(plan_id),
                    LearningActivityRecord.plan_version == plan_version,
                )
                .order_by(LearningActivityRecord.priority.desc(), LearningActivityRecord.id)
            )
        ).all()
        return [LearningActivity.model_validate(record.payload) for record in records]

    @staticmethod
    def _to_plan(record: LearningPlanRecord) -> LearningPlan:
        plan = LearningPlan.model_validate(record.payload)
        return plan.model_copy(update={"status": record.status})

"""SYS06/SYS07 durable version repositories。"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.learning import LearningActivity, LearningPlan, ReviewSchedule
from app.contracts.planning import (
    GoalFormationInferenceV1,
    GoalKnowledgeMappingV1,
    GoalSpecificKnowledgeSubgraphV1,
    LearningGoalV1,
    ReviewObservation,
)
from app.domains.learning_planner import PlannerDecision
from app.models.planning import (
    GoalFormationInferenceRecord,
    GoalKnowledgeMappingRecord,
    GoalKnowledgeSubgraphRecord,
    LearningActivityRecord,
    LearningGoalRecord,
    LearningPlanRecord,
    ReviewObservationRecord,
    ReviewScheduleRecord,
)


class GoalPlanningRepository:
    """SYS06 immutable Goal/Mapping/Subgraph/Inference repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_goal_by_idempotency(self, key: str) -> LearningGoalV1 | None:
        record = await self._session.scalar(
            select(LearningGoalRecord).where(LearningGoalRecord.idempotency_key == key)
        )
        return LearningGoalV1.model_validate(record.payload) if record else None

    async def save_goal(self, goal: LearningGoalV1, *, idempotency_key: str) -> LearningGoalV1:
        existing = await self.find_goal_by_idempotency(idempotency_key)
        if existing is not None:
            return existing
        record_id = f"{goal.goal_id}:{goal.version}"
        version_record = await self._session.get(LearningGoalRecord, record_id)
        if version_record is not None:
            return LearningGoalV1.model_validate(version_record.payload)
        self._session.add(
            LearningGoalRecord(
                id=record_id,
                goal_id=str(goal.goal_id),
                user_id=str(goal.user_id),
                version=goal.version,
                status=goal.status,
                idempotency_key=idempotency_key,
                payload=goal.model_dump(mode="json"),
            )
        )
        await self._session.flush()
        return goal

    async def latest_goal(self, *, goal_id: UUID, user_id: UUID) -> LearningGoalV1 | None:
        record = await self._session.scalar(
            select(LearningGoalRecord)
            .where(
                LearningGoalRecord.goal_id == str(goal_id),
                LearningGoalRecord.user_id == str(user_id),
            )
            .order_by(LearningGoalRecord.version.desc())
            .limit(1)
        )
        return LearningGoalV1.model_validate(record.payload) if record else None

    async def get_goal_version(
        self, *, goal_id: UUID, version: int, user_id: UUID
    ) -> LearningGoalV1 | None:
        record = await self._session.scalar(
            select(LearningGoalRecord).where(
                LearningGoalRecord.goal_id == str(goal_id),
                LearningGoalRecord.version == version,
                LearningGoalRecord.user_id == str(user_id),
            )
        )
        return LearningGoalV1.model_validate(record.payload) if record else None

    async def next_goal_version(self, goal_id: UUID) -> int:
        latest = await self._session.scalar(
            select(func.max(LearningGoalRecord.version)).where(
                LearningGoalRecord.goal_id == str(goal_id)
            )
        )
        return int(latest or 0) + 1

    async def find_mapping_by_idempotency(self, key: str) -> GoalKnowledgeMappingV1 | None:
        record = await self._session.scalar(
            select(GoalKnowledgeMappingRecord).where(
                GoalKnowledgeMappingRecord.idempotency_key == key
            )
        )
        return GoalKnowledgeMappingV1.model_validate(record.payload) if record else None

    async def next_mapping_version(self, goal_id: UUID) -> int:
        latest = await self._session.scalar(
            select(func.max(GoalKnowledgeMappingRecord.mapping_version)).where(
                GoalKnowledgeMappingRecord.goal_id == str(goal_id)
            )
        )
        return int(latest or 0) + 1

    async def save_mapping(
        self,
        mapping: GoalKnowledgeMappingV1,
        *,
        idempotency_key: str,
    ) -> GoalKnowledgeMappingV1:
        existing = await self.find_mapping_by_idempotency(idempotency_key)
        if existing is not None:
            return existing
        record_id = f"{mapping.mapping_id}:{mapping.mapping_version}"
        version_record = await self._session.get(GoalKnowledgeMappingRecord, record_id)
        if version_record is not None:
            return GoalKnowledgeMappingV1.model_validate(version_record.payload)
        self._session.add(
            GoalKnowledgeMappingRecord(
                id=record_id,
                mapping_id=str(mapping.mapping_id),
                goal_id=str(mapping.goal_id),
                goal_version=mapping.goal_version,
                mapping_version=mapping.mapping_version,
                mapper_version=mapping.mapper_version,
                status=mapping.status,
                idempotency_key=idempotency_key,
                payload=mapping.model_dump(mode="json"),
            )
        )
        await self._session.flush()
        return mapping

    async def latest_mapping(self, goal_id: UUID) -> GoalKnowledgeMappingV1 | None:
        record = await self._session.scalar(
            select(GoalKnowledgeMappingRecord)
            .where(GoalKnowledgeMappingRecord.goal_id == str(goal_id))
            .order_by(GoalKnowledgeMappingRecord.mapping_version.desc())
            .limit(1)
        )
        return GoalKnowledgeMappingV1.model_validate(record.payload) if record else None

    async def save_subgraph(
        self, subgraph: GoalSpecificKnowledgeSubgraphV1
    ) -> GoalSpecificKnowledgeSubgraphV1:
        record_id = f"{subgraph.subgraph_id}:{subgraph.version}"
        existing = await self._session.get(GoalKnowledgeSubgraphRecord, record_id)
        if existing is not None:
            return GoalSpecificKnowledgeSubgraphV1.model_validate(existing.payload)
        self._session.add(
            GoalKnowledgeSubgraphRecord(
                id=record_id,
                subgraph_id=str(subgraph.subgraph_id),
                mapping_id=subgraph.goal_mapping_ref.entity_id,
                version=subgraph.version,
                payload=subgraph.model_dump(mode="json"),
            )
        )
        await self._session.flush()
        return subgraph

    async def get_subgraph(
        self, *, subgraph_id: UUID, version: int
    ) -> GoalSpecificKnowledgeSubgraphV1 | None:
        record = await self._session.get(GoalKnowledgeSubgraphRecord, f"{subgraph_id}:{version}")
        return GoalSpecificKnowledgeSubgraphV1.model_validate(record.payload) if record else None

    async def save_inference(self, inference: GoalFormationInferenceV1) -> GoalFormationInferenceV1:
        existing = await self._session.get(
            GoalFormationInferenceRecord, str(inference.inference_id)
        )
        if existing is not None:
            return GoalFormationInferenceV1.model_validate(existing.payload)
        self._session.add(
            GoalFormationInferenceRecord(
                inference_id=str(inference.inference_id),
                goal_id=str(inference.goal_id),
                input_digest=inference.input_digest,
                provider=inference.provider,
                model_name=inference.model_name,
                status=inference.status,
                payload=inference.model_dump(mode="json"),
            )
        )
        await self._session.flush()
        return inference

    async def get_inference(self, inference_id: UUID) -> GoalFormationInferenceV1 | None:
        record = await self._session.get(GoalFormationInferenceRecord, str(inference_id))
        return GoalFormationInferenceV1.model_validate(record.payload) if record else None


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
                .order_by(ReviewObservationRecord.actual_reviewed_at, ReviewObservationRecord.id)
            )
        ).all()
        return [ReviewObservation.model_validate(record.payload) for record in records]

    async def latest(self, *, user_id: UUID, knowledge_unit_id: UUID) -> ReviewSchedule | None:
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
                .order_by(
                    ReviewScheduleRecord.knowledge_unit_id, ReviewScheduleRecord.version.desc()
                )
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
            select(LearningPlanRecord).where(LearningPlanRecord.idempotency_key == idempotency_key)
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

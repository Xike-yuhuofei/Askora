"""SYS07→SYS06 integration：各 owner 在同一事务写自己的 state 与 outbox。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from app.contracts.learning import LearningPlan, ReviewSchedule
from app.contracts.planning import ConfirmedLearningGoal, ReviewObservation
from app.domains.learning_planner import LearningPlanner, PlannerDecision
from app.domains.review_scheduler import ReviewScheduler, project_due


class ReviewRepositoryPort(Protocol):
    async def latest(self, *, user_id: UUID, knowledge_unit_id: UUID) -> ReviewSchedule | None: ...
    async def has_observation(self, observation_id: UUID) -> bool: ...
    async def save_observation(self, observation: ReviewObservation) -> None: ...
    async def save(self, schedule: ReviewSchedule) -> ReviewSchedule: ...
    async def list_latest_for_user(self, user_id: UUID) -> list[ReviewSchedule]: ...
    async def invalidate_observation(self, observation_id: UUID) -> None: ...
    async def list_valid_observations(
        self, *, user_id: UUID, knowledge_unit_id: UUID
    ) -> list[ReviewObservation]: ...


class PlanRepositoryPort(Protocol):
    async def find_by_idempotency(self, idempotency_key: str) -> LearningPlan | None: ...
    async def next_version(self, learning_goal_id: UUID) -> int: ...
    async def save(
        self, decision: PlannerDecision, *, idempotency_key: str
    ) -> LearningPlan: ...


class OutboxPort(Protocol):
    async def enqueue(
        self,
        *,
        task_type: str,
        schema_version: str,
        payload: dict[str, Any],
        idempotency_key: str,
        next_attempt_at: datetime | None = None,
    ) -> Any: ...


class ReviewPlanningApplication:
    def __init__(
        self,
        reviews: ReviewRepositoryPort,
        plans: PlanRepositoryPort,
        outbox: OutboxPort,
    ) -> None:
        self._reviews = reviews
        self._plans = plans
        self._outbox = outbox
        self._scheduler = ReviewScheduler()
        self._planner = LearningPlanner()

    async def apply_review_observation(
        self,
        observation: ReviewObservation,
        *,
        desired_retention: float = 0.90,
        parameters: dict[str, float] | None = None,
    ) -> ReviewSchedule:
        prior = await self._reviews.latest(
            user_id=observation.user_id,
            knowledge_unit_id=observation.knowledge_unit_id,
        )
        if await self._reviews.has_observation(observation.observation_id):
            if prior is None:
                raise RuntimeError("REVIEW_OBSERVATION_WITHOUT_SCHEDULE")
            return prior
        decision = self._scheduler.update(
            observation=observation,
            prior=prior,
            version=(prior.version + 1) if prior else 1,
            desired_retention=desired_retention,
            parameters=parameters,
        )
        await self._reviews.save_observation(observation)
        schedule = await self._reviews.save(decision.schedule)
        await self._outbox.enqueue(
            task_type="review.due.check",
            schema_version="1.0",
            payload={
                "schedule": schedule.model_dump(mode="json"),
                "reason_codes": list(decision.reason_codes),
                "actual_reviewed_at": observation.actual_reviewed_at.isoformat(),
            },
            idempotency_key=f"review-due:{schedule.schedule_id}:{schedule.version}",
            next_attempt_at=schedule.next_due_at,
        )
        return schedule

    async def generate_plan(
        self,
        *,
        goal: ConfirmedLearningGoal,
        user_id: UUID,
        prerequisites: dict[UUID, list[UUID]],
        mastery: dict[UUID, float | None],
        time_budget_minutes: int,
        learner_state_version: int,
        knowledge_graph_version: str,
        at: datetime,
        idempotency_key: str,
        reason_codes: list[str] | None = None,
    ) -> LearningPlan:
        existing = await self._plans.find_by_idempotency(idempotency_key)
        if existing is not None:
            return existing
        schedules = await self._reviews.list_latest_for_user(user_id)
        due_candidates = [project_due(schedule, at=at) for schedule in schedules]
        version = await self._plans.next_version(goal.goal_id)
        decision = self._planner.generate(
            goal=goal,
            prerequisites=prerequisites,
            mastery=mastery,
            due_candidates=due_candidates,
            time_budget_minutes=time_budget_minutes,
            learner_state_version=learner_state_version,
            knowledge_graph_version=knowledge_graph_version,
            version=version,
            created_at=at,
            reason_codes=reason_codes,
        )
        plan = await self._plans.save(decision, idempotency_key=idempotency_key)
        await self._outbox.enqueue(
            task_type="learning.plan.generated",
            schema_version="1.0",
            payload={
                "plan": plan.model_dump(mode="json"),
                "activities": [
                    activity.model_dump(mode="json") for activity in decision.activities
                ],
                "scoring_trace": list(decision.scoring_trace),
            },
            idempotency_key=f"learning-plan:{plan.plan_id}:{plan.version}",
        )
        return plan

    async def recompute_after_observation_invalidation(
        self,
        *,
        observation_id: UUID,
        user_id: UUID,
        knowledge_unit_id: UUID,
        desired_retention: float = 0.90,
    ) -> ReviewSchedule:
        prior_latest = await self._reviews.latest(
            user_id=user_id, knowledge_unit_id=knowledge_unit_id
        )
        if prior_latest is None:
            raise RuntimeError("REVIEW_SCHEDULE_NOT_FOUND")
        await self._reviews.invalidate_observation(observation_id)
        observations = await self._reviews.list_valid_observations(
            user_id=user_id, knowledge_unit_id=knowledge_unit_id
        )
        if not observations:
            raise RuntimeError("REVIEW_RECOMPUTE_REQUIRES_VALID_OBSERVATION")
        replayed: ReviewSchedule | None = None
        last_reasons: tuple[str, ...] = ()
        for replay_index, observation in enumerate(observations, start=1):
            decision = self._scheduler.update(
                observation=observation,
                prior=replayed,
                version=replay_index,
                desired_retention=desired_retention,
            )
            replayed = decision.schedule
            last_reasons = decision.reason_codes
        if replayed is None:  # guarded above; keeps type narrowing explicit
            raise RuntimeError("REVIEW_REPLAY_EMPTY")
        recomputed = replayed.model_copy(update={"version": prior_latest.version + 1})
        recomputed = await self._reviews.save(recomputed)
        await self._outbox.enqueue(
            task_type="review.due.check",
            schema_version="1.0",
            payload={
                "schedule": recomputed.model_dump(mode="json"),
                "reason_codes": ["REVIEW_OBSERVATION_INVALIDATED", *last_reasons],
            },
            idempotency_key=f"review-due:{recomputed.schedule_id}:{recomputed.version}",
            next_attempt_at=recomputed.next_due_at,
        )
        return recomputed

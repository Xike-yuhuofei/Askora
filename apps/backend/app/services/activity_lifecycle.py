"""SYS06 owner service for canonical LearningActivity lifecycle commands."""

from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from http import HTTPStatus
from typing import Literal
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.activity_lifecycle import (
    ActivityExecutionCapabilityV1,
    ActivityLifecycleDataV1,
    ActivityLifecycleResponseV1,
    ActivityStatus,
    CompleteLearningActivityV1,
    LearningActivityStateV1,
    StartLearningActivityV1,
)
from app.contracts.adaptive import VersionedRef
from app.contracts.events import (
    EventActor,
    EventContext,
    EventPrivacy,
    EventProvenance,
    EventTrace,
    LearningEventEnvelope,
)
from app.contracts.learning import LearningActivity, LearningPlan
from app.contracts.planning import LearningGoalV1
from app.core.exceptions import BusinessError, ResourceNotFoundError
from app.infrastructure.activity_lifecycle import ActivityLifecycleRepository
from app.infrastructure.goal_management import GoalManagementRepository
from app.infrastructure.ledger import LearningEventRepository
from app.infrastructure.outbox import OutboxProducer
from app.models.book_learning import BookLearningTranscriptTurnRecord
from app.models.planning import LearningActivityRecord, LearningGoalRecord, LearningPlanRecord
from app.models.user import User
from app.services.auth.canonical_identity import canonical_user_id

_ACTIVITY_TITLES = {
    "learn_new": "学习新内容",
    "prerequisite_remediation": "补齐前置知识",
    "diagnostic": "检查当前基础",
    "practice": "练习与巩固",
    "delayed_review": "延迟复习",
    "transfer_check": "迁移应用",
    "metacognitive_review": "复盘学习方法",
}
_TRANSCRIPT_COMPLETABLE = {
    "learn_new",
    "prerequisite_remediation",
    "practice",
    "metacognitive_review",
}


@dataclass(frozen=True)
class _ActivityContext:
    goal: LearningGoalV1
    plan: LearningPlan
    plan_record: LearningPlanRecord
    activity: LearningActivity


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _error(code: str, message: str, status_code: int = HTTPStatus.CONFLICT) -> BusinessError:
    return BusinessError(message=message, error_code=code, status_code=status_code)


class ActivityLifecycleService:
    """Only SYS06 writes lifecycle state; API and SYS08 submit bounded commands."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._states = ActivityLifecycleRepository(session)
        self._goals = GoalManagementRepository(session)

    async def get(
        self, *, user: User, activity_id: UUID, correlation_id: UUID
    ) -> ActivityLifecycleResponseV1:
        context = await self._context(user=user, activity_id=activity_id)
        state = await self._require_state(activity_id)
        next_activity_ref = await self._next_executable_activity_ref(context, state)
        return self._response(
            context,
            state,
            correlation_id=correlation_id,
            next_activity_ref=next_activity_ref,
        )

    async def select_next(
        self,
        *,
        user: User,
        goal_id: UUID,
        idempotency_key: str,
        correlation_id: UUID,
        now: datetime | None = None,
    ) -> ActivityLifecycleResponseV1:
        owner_id = canonical_user_id(user.id)
        digest = self._digest({"command": "SelectNextLearningActivity", "goal_id": str(goal_id)})
        replay = await self._replay(
            user_id=owner_id, idempotency_key=idempotency_key, digest=digest
        )
        if replay is not None:
            return replay

        goal = await self._latest_goal(user=user, goal_id=goal_id)
        await self._require_goal_active(user=user, goal_id=goal_id)
        plan_record = await self._session.scalar(
            select(LearningPlanRecord)
            .where(
                LearningPlanRecord.learning_goal_id == str(goal.goal_id),
                LearningPlanRecord.status == "active",
            )
            .order_by(LearningPlanRecord.version.desc())
            .limit(1)
            .with_for_update()
        )
        if plan_record is None:
            raise _error("ACTIVITY_STALE_OR_SUPERSEDED", "当前学习计划不可执行")
        plan = LearningPlan.model_validate(plan_record.payload).model_copy(
            update={"status": plan_record.status}
        )
        definitions = await self._ordered_definitions(plan)
        states = await self._states.latest_for_plan(plan_id=plan.plan_id, plan_version=plan.version)
        if len(states) != len(definitions):
            raise _error(
                "LEGACY_ACTIVITY_STATE_UNMIGRATED",
                "学习活动尚未完成生命周期迁移",
            )

        current = next(
            (
                item
                for item in definitions
                if states[item.activity_id].status in {"available", "active"}
            ),
            None,
        )
        selected_at = now or _now()
        if current is None:
            current = next(
                (item for item in definitions if states[item.activity_id].status == "planned"),
                None,
            )
            if current is None:
                raise _error("ACTIVITY_NOT_AVAILABLE", "当前没有可选择的学习活动")
            prior = states[current.activity_id]
            state = self._next_state(
                prior,
                status="available",
                reason="SELECT_NEXT_LEARNING_ACTIVITY",
                actor_type="system",
                correlation_id=correlation_id,
                created_at=selected_at,
            )
            replay = await self._append_state_or_replay(
                state=state,
                user_id=owner_id,
                idempotency_key=idempotency_key,
                digest=digest,
            )
            if replay is not None:
                return replay
            context = _ActivityContext(goal, plan, plan_record, current)
            await self._publish_transition(
                user=user, context=context, state=state, event_type="ActivityAvailable"
            )
        else:
            state = states[current.activity_id]
            context = _ActivityContext(goal, plan, plan_record, current)
        response = self._response(context, state, correlation_id=correlation_id)
        return await self._receipt(
            user_id=owner_id,
            activity_id=current.activity_id,
            command_type="SelectNextLearningActivity",
            idempotency_key=idempotency_key,
            digest=digest,
            response=response,
        )

    async def replay_select_next(
        self, *, user: User, goal_id: UUID, idempotency_key: str
    ) -> ActivityLifecycleResponseV1 | None:
        """Let an adapter check idempotency before an external flow precondition."""
        return await self._replay(
            user_id=canonical_user_id(user.id),
            idempotency_key=idempotency_key,
            digest=self._digest({"command": "SelectNextLearningActivity", "goal_id": str(goal_id)}),
        )

    async def _require_goal_active(self, *, user: User, goal_id: UUID) -> None:
        """Prevent SYS06 activity commands while a versioned goal is not active.

        Legacy goals without a V2 state remain executable through the compatibility
        path; once migrated, the append-only goal state is authoritative.
        """
        state = await self._goals.latest_state(
            goal_id=goal_id,
            user_id=canonical_user_id(user.id),
        )
        if state is None or state.status == "active":
            return
        if state.status == "paused":
            raise _error("ACTIVITY_NOT_AVAILABLE", "目标已暂停，请先恢复目标")
        raise _error("ACTIVITY_STALE_OR_SUPERSEDED", "目标已结束，当前活动不可执行")

    async def start(
        self,
        *,
        user: User,
        command: StartLearningActivityV1,
        correlation_id: UUID,
        now: datetime | None = None,
    ) -> ActivityLifecycleResponseV1:
        owner_id = canonical_user_id(user.id)
        digest = self._digest(command.model_dump(mode="json"))
        replay = await self._replay(
            user_id=owner_id, idempotency_key=command.idempotency_key, digest=digest
        )
        if replay is not None:
            return replay
        context = await self._context(user=user, activity_id=command.activity_id, lock=True)
        await self._require_goal_active(user=user, goal_id=context.goal.goal_id)
        state = await self._require_state(command.activity_id, lock=True)
        self._require_current_plan(context)
        if state.version != command.expected_state_version:
            # A concurrent duplicate may have advanced state while its receipt is
            # not yet visible in this transaction snapshot. Refresh and use the
            # same bounded replay window as the optimistic append path.
            await self._session.rollback()
            replay = await self._replay_after_concurrent_conflict(
                user_id=owner_id,
                idempotency_key=command.idempotency_key,
                digest=digest,
            )
            if replay is not None:
                return replay
            raise _error("ACTIVITY_STATE_VERSION_CONFLICT", "活动状态已更新，请刷新后重试")
        if state.status != "available":
            code = (
                "ACTIVITY_STALE_OR_SUPERSEDED"
                if state.status == "superseded"
                else "ACTIVITY_NOT_AVAILABLE"
            )
            raise _error(code, "当前活动不可开始")
        started_at = now or _now()
        next_state = self._next_state(
            state,
            status="active",
            reason="LEARNER_STARTED_ACTIVITY",
            actor_type="learner",
            correlation_id=correlation_id,
            created_at=started_at,
            started_at=started_at,
        )
        replay = await self._append_state_or_replay(
            state=next_state,
            user_id=owner_id,
            idempotency_key=command.idempotency_key,
            digest=digest,
        )
        if replay is not None:
            return replay
        await self._publish_transition(
            user=user, context=context, state=next_state, event_type="ActivityStarted"
        )
        response = self._response(context, next_state, correlation_id=correlation_id)
        return await self._receipt(
            user_id=owner_id,
            activity_id=command.activity_id,
            command_type="StartLearningActivityV1",
            idempotency_key=command.idempotency_key,
            digest=digest,
            response=response,
        )

    async def complete(
        self,
        *,
        user: User,
        command: CompleteLearningActivityV1,
        correlation_id: UUID,
        now: datetime | None = None,
    ) -> ActivityLifecycleResponseV1:
        owner_id = canonical_user_id(user.id)
        digest = self._digest(command.model_dump(mode="json"))
        replay = await self._replay(
            user_id=owner_id, idempotency_key=command.idempotency_key, digest=digest
        )
        if replay is not None:
            return replay
        context = await self._context(user=user, activity_id=command.activity_id, lock=True)
        await self._require_goal_active(user=user, goal_id=context.goal.goal_id)
        state = await self._require_state(command.activity_id, lock=True)
        self._require_current_plan(context)
        if state.version != command.expected_state_version:
            await self._session.rollback()
            replay = await self._replay_after_concurrent_conflict(
                user_id=owner_id,
                idempotency_key=command.idempotency_key,
                digest=digest,
            )
            if replay is not None:
                return replay
            raise _error("ACTIVITY_STATE_VERSION_CONFLICT", "活动状态已更新，请刷新后重试")
        if state.status != "active":
            code = (
                "ACTIVITY_STALE_OR_SUPERSEDED"
                if state.status == "superseded"
                else "ACTIVITY_NOT_ACTIVE"
            )
            raise _error(code, "当前活动不在进行中")
        if context.activity.type not in _TRANSCRIPT_COMPLETABLE:
            raise _error(
                "ACTIVITY_COMPLETION_EVIDENCE_REQUIRED",
                "该活动必须由对应评估或复习结果完成",
            )
        await self._validate_transcript_refs(
            user_id=owner_id,
            activity_id=command.activity_id,
            refs=command.transcript_turn_refs,
        )
        completed_at = now or _now()
        completed = self._next_state(
            state,
            status="completed",
            reason="LEARNER_FINISHED_TRANSCRIPT_BACKED_ACTIVITY",
            actor_type="learner",
            correlation_id=correlation_id,
            created_at=completed_at,
            started_at=state.started_at,
            completed_at=completed_at,
            source_refs=command.transcript_turn_refs,
        )
        replay = await self._append_state_or_replay(
            state=completed,
            user_id=owner_id,
            idempotency_key=command.idempotency_key,
            digest=digest,
        )
        if replay is not None:
            return replay
        await self._publish_transition(
            user=user, context=context, state=completed, event_type="ActivityCompleted"
        )

        # P1-01A: an approved replan is applied at the activity boundary before
        # any next activity from the superseded plan becomes available.
        from app.services.goal_management import GoalManagementService

        replanned_activity_ref = await GoalManagementService(
            self._session
        ).apply_pending_at_boundary(
            user=user,
            completed_activity_id=command.activity_id,
            correlation_id=correlation_id,
            now=completed_at,
        )
        if replanned_activity_ref is not None:
            response = self._response(
                context,
                completed,
                correlation_id=correlation_id,
                next_activity_ref=replanned_activity_ref,
            )
            return await self._receipt(
                user_id=owner_id,
                activity_id=command.activity_id,
                command_type="CompleteLearningActivityV1",
                idempotency_key=command.idempotency_key,
                digest=digest,
                response=response,
            )

        next_ref: VersionedRef | None = None
        definitions = await self._ordered_definitions(context.plan)
        states = await self._states.latest_for_plan(
            plan_id=context.plan.plan_id, plan_version=context.plan.version
        )
        current_index = next(
            index
            for index, item in enumerate(definitions)
            if item.activity_id == command.activity_id
        )
        next_activity = next(
            (
                item
                for item in definitions[current_index + 1 :]
                if states[item.activity_id].status == "planned"
            ),
            None,
        )
        if next_activity is not None:
            prior = states[next_activity.activity_id]
            available = self._next_state(
                prior,
                status="available",
                reason="PREVIOUS_ACTIVITY_COMPLETED",
                actor_type="system",
                correlation_id=correlation_id,
                created_at=completed_at,
                source_refs=(
                    VersionedRef(
                        entity_type="LearningActivityState",
                        entity_id=str(completed.activity_id),
                        version=completed.version,
                    ),
                ),
            )
            await self._states.append(available)
            next_context = _ActivityContext(
                context.goal, context.plan, context.plan_record, next_activity
            )
            await self._publish_transition(
                user=user,
                context=next_context,
                state=available,
                event_type="ActivityAvailable",
            )
            next_ref = VersionedRef(
                entity_type="LearningActivity",
                entity_id=str(next_activity.activity_id),
                version=next_activity.plan_version,
            )
        else:
            remaining = [
                item
                for item in definitions
                if states[item.activity_id].status not in {"completed", "skipped", "superseded"}
                and item.activity_id != command.activity_id
            ]
            if not remaining:
                context.plan_record.status = "completed"
                context = _ActivityContext(
                    context.goal,
                    context.plan.model_copy(update={"status": "completed"}),
                    context.plan_record,
                    context.activity,
                )
        response = self._response(
            context,
            completed,
            correlation_id=correlation_id,
            next_activity_ref=next_ref,
        )
        return await self._receipt(
            user_id=owner_id,
            activity_id=command.activity_id,
            command_type="CompleteLearningActivityV1",
            idempotency_key=command.idempotency_key,
            digest=digest,
            response=response,
        )

    async def _next_executable_activity_ref(
        self,
        context: _ActivityContext,
        state: LearningActivityStateV1,
    ) -> VersionedRef | None:
        """Restore progression from canonical state after refresh/restart."""
        if state.status != "completed":
            return None
        definitions = await self._ordered_definitions(context.plan)
        states = await self._states.latest_for_plan(
            plan_id=context.plan.plan_id,
            plan_version=context.plan.version,
        )
        current_index = next(
            (
                index
                for index, item in enumerate(definitions)
                if item.activity_id == state.activity_id
            ),
            None,
        )
        if current_index is None:
            return None
        next_activity = next(
            (
                item
                for item in definitions[current_index + 1 :]
                if states.get(item.activity_id) is not None
                and states[item.activity_id].status in {"available", "active"}
            ),
            None,
        )
        if next_activity is None:
            return None
        return VersionedRef(
            entity_type="LearningActivity",
            entity_id=str(next_activity.activity_id),
            version=next_activity.plan_version,
        )

    async def _context(
        self, *, user: User, activity_id: UUID, lock: bool = False
    ) -> _ActivityContext:
        statement = select(LearningActivityRecord).where(
            LearningActivityRecord.id == str(activity_id)
        )
        if lock:
            statement = statement.with_for_update()
        activity_record = await self._session.scalar(statement)
        if activity_record is None:
            raise ResourceNotFoundError("学习活动")
        activity = LearningActivity.model_validate(activity_record.payload)
        plan_record = await self._session.scalar(
            select(LearningPlanRecord).where(
                LearningPlanRecord.plan_id == activity_record.plan_id,
                LearningPlanRecord.version == activity_record.plan_version,
            )
        )
        if plan_record is None:
            raise ResourceNotFoundError("学习活动")
        goal = await self._latest_goal(user=user, goal_id=UUID(plan_record.learning_goal_id))
        plan = LearningPlan.model_validate(plan_record.payload).model_copy(
            update={"status": plan_record.status}
        )
        return _ActivityContext(goal, plan, plan_record, activity)

    async def _latest_goal(self, *, user: User, goal_id: UUID) -> LearningGoalV1:
        owner_id = str(canonical_user_id(user.id))
        record = await self._session.scalar(
            select(LearningGoalRecord)
            .where(
                LearningGoalRecord.goal_id == str(goal_id),
                LearningGoalRecord.user_id == owner_id,
            )
            .order_by(LearningGoalRecord.version.desc())
            .limit(1)
        )
        if record is None:
            raise ResourceNotFoundError("学习活动")
        return LearningGoalV1.model_validate(record.payload)

    async def _ordered_definitions(self, plan: LearningPlan) -> tuple[LearningActivity, ...]:
        records = (
            await self._session.scalars(
                select(LearningActivityRecord).where(
                    LearningActivityRecord.plan_id == str(plan.plan_id),
                    LearningActivityRecord.plan_version == plan.version,
                )
            )
        ).all()
        by_id = {
            UUID(record.id): LearningActivity.model_validate(record.payload) for record in records
        }
        return tuple(by_id[item] for item in plan.activity_ids if item in by_id)

    async def _require_state(
        self, activity_id: UUID, *, lock: bool = False
    ) -> LearningActivityStateV1:
        state = await self._states.latest(activity_id, for_update=lock)
        if state is None:
            raise _error(
                "LEGACY_ACTIVITY_STATE_UNMIGRATED",
                "学习活动尚未完成生命周期迁移",
            )
        return state

    @staticmethod
    def _require_current_plan(context: _ActivityContext) -> None:
        if context.plan_record.status != "active":
            raise _error("ACTIVITY_STALE_OR_SUPERSEDED", "活动所属计划已失效")

    async def _validate_transcript_refs(
        self,
        *,
        user_id: UUID,
        activity_id: UUID,
        refs: tuple[VersionedRef, ...],
    ) -> None:
        if not refs:
            raise _error("ACTIVITY_COMPLETION_EVIDENCE_REQUIRED", "至少需要一条已接纳学习记录")
        for ref in refs:
            if ref.entity_type != "BookLearningTranscriptTurn":
                raise _error("ACTIVITY_COMPLETION_EVIDENCE_REQUIRED", "学习记录引用类型无效")
            try:
                turn_number = int(ref.version)
            except (TypeError, ValueError):
                raise _error("ACTIVITY_COMPLETION_EVIDENCE_REQUIRED", "学习记录版本无效") from None
            record = await self._session.scalar(
                select(BookLearningTranscriptTurnRecord).where(
                    BookLearningTranscriptTurnRecord.user_id == str(user_id),
                    BookLearningTranscriptTurnRecord.activity_id == str(activity_id),
                    BookLearningTranscriptTurnRecord.turn_id == ref.entity_id,
                    BookLearningTranscriptTurnRecord.turn_number == turn_number,
                )
            )
            if record is None:
                raise _error(
                    "ACTIVITY_COMPLETION_EVIDENCE_REQUIRED",
                    "学习记录不属于当前用户或活动",
                )

    async def _publish_transition(
        self,
        *,
        user: User,
        context: _ActivityContext,
        state: LearningActivityStateV1,
        event_type: str,
    ) -> None:
        event_id = uuid5(
            NAMESPACE_URL,
            f"askora:sys06:{state.activity_id}:lifecycle:v{state.version}:{event_type}",
        )
        event = LearningEventEnvelope(
            event_id=event_id,
            event_type=event_type,
            aggregate_type="LearningActivityLifecycle",
            aggregate_id=state.activity_id,
            aggregate_version=state.version,
            sequence=state.version,
            occurred_at=state.created_at,
            recorded_at=state.created_at,
            idempotency_key=f"sys06-activity-lifecycle:{state.activity_id}:v{state.version}",
            correlation_id=state.correlation_id,
            actor=EventActor(actor_type=state.actor_type, actor_id=user.id),
            context=EventContext(
                user_id=canonical_user_id(user.id),
                goal_id=context.goal.goal_id,
                knowledge_unit_ids=context.activity.knowledge_unit_ids,
                content_revision_ids=[],
            ),
            payload={
                "activity_ref": f"learning_activity:{state.activity_id}:v{state.plan_version}",
                "plan_ref": f"learning_plan:{state.plan_id}:v{state.plan_version}",
                "goal_ref": f"learning_goal:{context.goal.goal_id}:v{context.goal.version}",
                "previous_status": state.previous_status,
                "new_status": state.status,
                "lifecycle_version": state.version,
                "reason": state.transition_reason,
                "source_refs": [item.model_dump(mode="json") for item in state.source_refs],
            },
            provenance=EventProvenance(source="domain", algorithm_version="sys06-activity-v1"),
            trace=EventTrace(trace_id=f"activity-lifecycle:{state.correlation_id}"),
            privacy=EventPrivacy(
                classification="personal",
                external_processing=False,
                retention_class="core_learning",
            ),
        )
        await LearningEventRepository(self._session).append(event)
        await OutboxProducer(self._session).enqueue(
            task_type="sys06.activity.lifecycle.event",
            schema_version="1.0",
            payload={"event_id": str(event_id), "event_type": event_type},
            idempotency_key=f"outbox:sys06-activity-lifecycle:{state.activity_id}:v{state.version}",
            next_attempt_at=state.created_at,
        )

    async def _replay(
        self, *, user_id: UUID, idempotency_key: str, digest: str
    ) -> ActivityLifecycleResponseV1 | None:
        receipt = await self._states.get_receipt(user_id=user_id, idempotency_key=idempotency_key)
        if receipt is None:
            return None
        if receipt.command_digest != digest:
            raise _error(
                "ACTIVITY_IDEMPOTENCY_CONFLICT",
                "该幂等键已用于不同的活动命令",
            )
        return ActivityLifecycleResponseV1.model_validate(receipt.response_payload)

    async def _append_state_or_replay(
        self,
        *,
        state: LearningActivityStateV1,
        user_id: UUID,
        idempotency_key: str,
        digest: str,
    ) -> ActivityLifecycleResponseV1 | None:
        try:
            async with self._session.begin_nested():
                await self._states.append(state)
        except IntegrityError:
            # The failed optimistic write leaves a read transaction whose snapshot may
            # predate the winning receipt (notably on SQLite). No domain writes from
            # this command survived the nested rollback, so start a fresh snapshot.
            await self._session.rollback()
            replay = await self._replay_after_concurrent_conflict(
                user_id=user_id,
                idempotency_key=idempotency_key,
                digest=digest,
            )
            if replay is not None:
                return replay
            raise _error(
                "ACTIVITY_STATE_VERSION_CONFLICT",
                "活动状态已更新，请刷新后重试",
            ) from None
        return None

    async def _replay_after_concurrent_conflict(
        self,
        *,
        user_id: UUID,
        idempotency_key: str,
        digest: str,
    ) -> ActivityLifecycleResponseV1 | None:
        """Allow the winning transaction to publish its receipt before failing closed."""
        for _attempt in range(20):
            replay = await self._replay(
                user_id=user_id,
                idempotency_key=idempotency_key,
                digest=digest,
            )
            if replay is not None:
                return replay
            await asyncio.sleep(0.01)
        return None

    async def _receipt(
        self,
        *,
        user_id: UUID,
        activity_id: UUID,
        command_type: str,
        idempotency_key: str,
        digest: str,
        response: ActivityLifecycleResponseV1,
    ) -> ActivityLifecycleResponseV1:
        try:
            async with self._session.begin_nested():
                await self._states.append_receipt(
                    receipt_id=uuid5(
                        NAMESPACE_URL,
                        f"askora:activity-receipt:{user_id}:{idempotency_key}",
                    ),
                    user_id=user_id,
                    activity_id=activity_id,
                    command_type=command_type,
                    idempotency_key=idempotency_key,
                    command_digest=digest,
                    response_payload=response.model_dump(mode="json"),
                )
        except IntegrityError:
            await self._session.rollback()
            replay = await self._replay(
                user_id=user_id,
                idempotency_key=idempotency_key,
                digest=digest,
            )
            if replay is None:
                raise _error(
                    "ACTIVITY_IDEMPOTENCY_CONFLICT",
                    "该幂等键已用于其他活动命令",
                ) from None
            return replay
        return response

    @staticmethod
    def _next_state(
        prior: LearningActivityStateV1,
        *,
        status: ActivityStatus,
        reason: str,
        actor_type: Literal["system", "learner"],
        correlation_id: UUID,
        created_at: datetime,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        source_refs: tuple[VersionedRef, ...] = (),
    ) -> LearningActivityStateV1:
        return LearningActivityStateV1(
            activity_id=prior.activity_id,
            version=prior.version + 1,
            plan_id=prior.plan_id,
            plan_version=prior.plan_version,
            status=status,
            previous_status=prior.status,
            transition_reason=reason,
            source_refs=source_refs,
            actor_type=actor_type,
            started_at=started_at,
            completed_at=completed_at,
            correlation_id=correlation_id,
            created_at=created_at,
        )

    def _response(
        self,
        context: _ActivityContext,
        state: LearningActivityStateV1,
        *,
        correlation_id: UUID,
        next_activity_ref: VersionedRef | None = None,
    ) -> ActivityLifecycleResponseV1:
        supported = context.activity.type in _TRANSCRIPT_COMPLETABLE
        reasons: tuple[str, ...] = ()
        if context.plan.status != "active" or state.status == "superseded":
            reasons = ("ACTIVITY_STALE_OR_SUPERSEDED",)
        elif state.status == "planned":
            reasons = ("ACTIVITY_NOT_AVAILABLE",)
        elif state.status == "active" and not supported:
            reasons = ("ACTIVITY_COMPLETION_EVIDENCE_REQUIRED",)
        return ActivityLifecycleResponseV1(
            data=ActivityLifecycleDataV1(
                state=state,
                goal_id=context.goal.goal_id,
                activity_type=context.activity.type,
                title=_ACTIVITY_TITLES.get(context.activity.type, "学习活动"),
                estimated_duration_minutes=context.activity.estimated_duration_minutes,
                knowledge_unit_ids=tuple(context.activity.knowledge_unit_ids),
                execution=ActivityExecutionCapabilityV1(
                    can_start=context.plan.status == "active" and state.status == "available",
                    can_resume=context.plan.status == "active" and state.status == "active",
                    can_complete=(
                        context.plan.status == "active" and state.status == "active" and supported
                    ),
                    product_route=f"/learn/{state.activity_id}",
                    reason_codes=reasons,
                ),
            ),
            next_activity_ref=next_activity_ref,
            plan_status=context.plan.status,
            correlation_id=str(correlation_id),
        )

    @staticmethod
    def _digest(payload: dict) -> str:
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

"""Persistence adapter for the SYS06 activity lifecycle stream."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.activity_lifecycle import ActivityStatus, LearningActivityStateV1
from app.models.planning import (
    ActivityLifecycleCommandReceiptRecord,
    LearningActivityStateRecord,
)


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class ActivityLifecycleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def latest(
        self, activity_id: UUID | str, *, for_update: bool = False
    ) -> LearningActivityStateV1 | None:
        statement = (
            select(LearningActivityStateRecord)
            .where(LearningActivityStateRecord.activity_id == str(activity_id))
            .order_by(LearningActivityStateRecord.version.desc())
            .limit(1)
        )
        if for_update:
            statement = statement.with_for_update()
        record = await self._session.scalar(statement)
        return self._to_state(record) if record is not None else None

    async def latest_for_plan(
        self, *, plan_id: UUID | str, plan_version: int
    ) -> dict[UUID, LearningActivityStateV1]:
        records = (
            await self._session.scalars(
                select(LearningActivityStateRecord)
                .where(
                    LearningActivityStateRecord.plan_id == str(plan_id),
                    LearningActivityStateRecord.plan_version == plan_version,
                )
                .order_by(
                    LearningActivityStateRecord.activity_id,
                    LearningActivityStateRecord.version.desc(),
                )
            )
        ).all()
        latest: dict[UUID, LearningActivityStateV1] = {}
        for record in records:
            latest.setdefault(UUID(record.activity_id), self._to_state(record))
        return latest

    async def append(self, state: LearningActivityStateV1) -> LearningActivityStateV1:
        data = state.model_dump(mode="json")
        self._session.add(
            LearningActivityStateRecord(
                id=f"{state.activity_id}:{state.version}",
                activity_id=str(state.activity_id),
                version=state.version,
                plan_id=str(state.plan_id),
                plan_version=state.plan_version,
                status=state.status,
                previous_status=state.previous_status,
                transition_reason=state.transition_reason,
                source_refs=data["source_refs"],
                actor_type=state.actor_type,
                started_at=state.started_at,
                completed_at=state.completed_at,
                correlation_id=str(state.correlation_id),
                created_at=state.created_at,
            )
        )
        await self._session.flush()
        return state

    async def initialize(
        self,
        *,
        activity_id: UUID,
        plan_id: UUID,
        plan_version: int,
        status: ActivityStatus,
        correlation_id: UUID,
        created_at: datetime,
    ) -> LearningActivityStateV1:
        existing = await self.latest(activity_id)
        if existing is not None:
            return existing
        return await self.append(
            LearningActivityStateV1(
                activity_id=activity_id,
                version=1,
                plan_id=plan_id,
                plan_version=plan_version,
                status=status,
                transition_reason="ACTIVITY_CREATED_FROM_PLAN",
                actor_type="system",
                correlation_id=correlation_id,
                created_at=created_at,
            )
        )

    async def get_receipt(
        self, *, user_id: UUID | str, idempotency_key: str
    ) -> ActivityLifecycleCommandReceiptRecord | None:
        return await self._session.scalar(
            select(ActivityLifecycleCommandReceiptRecord).where(
                ActivityLifecycleCommandReceiptRecord.user_id == str(user_id),
                ActivityLifecycleCommandReceiptRecord.idempotency_key == idempotency_key,
            )
        )

    async def append_receipt(
        self,
        *,
        receipt_id: UUID,
        user_id: UUID,
        activity_id: UUID,
        command_type: str,
        idempotency_key: str,
        command_digest: str,
        response_payload: dict,
    ) -> None:
        self._session.add(
            ActivityLifecycleCommandReceiptRecord(
                receipt_id=str(receipt_id),
                user_id=str(user_id),
                activity_id=str(activity_id),
                command_type=command_type,
                idempotency_key=idempotency_key,
                command_digest=command_digest,
                response_payload=response_payload,
            )
        )
        await self._session.flush()

    @staticmethod
    def _to_state(record: LearningActivityStateRecord) -> LearningActivityStateV1:
        return LearningActivityStateV1.model_validate(
            {
                "activity_id": record.activity_id,
                "version": record.version,
                "plan_id": record.plan_id,
                "plan_version": record.plan_version,
                "status": record.status,
                "previous_status": record.previous_status,
                "transition_reason": record.transition_reason,
                "source_refs": record.source_refs,
                "actor_type": record.actor_type,
                "started_at": _aware(record.started_at) if record.started_at else None,
                "completed_at": _aware(record.completed_at) if record.completed_at else None,
                "correlation_id": record.correlation_id,
                "created_at": _aware(record.created_at),
            }
        )

"""Transactional Outbox producer、repository 与可恢复 worker skeleton。"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, cast

from sqlalchemy import select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.ledger import OutboxTaskRecord


class OutboxStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    RETRY = "retry"
    COMPLETED = "completed"
    DEAD_LETTER = "dead_letter"


class PermanentTaskError(RuntimeError):
    """Schema/business validation 等禁止盲重试的任务错误。"""


@dataclass(frozen=True)
class OutboxTask:
    id: str
    type: str
    schema_version: str
    payload: dict[str, Any]
    status: OutboxStatus
    idempotency_key: str
    attempt_count: int
    next_attempt_at: datetime
    last_error: str | None
    created_at: datetime
    updated_at: datetime


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


class OutboxRepository:
    """PERSIST-020..032：由调用方 session/transaction 管理的 outbox port。"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def enqueue(
        self,
        *,
        task_type: str,
        schema_version: str,
        payload: dict[str, Any],
        idempotency_key: str,
        next_attempt_at: datetime | None = None,
    ) -> OutboxTask:
        existing = await self.get_by_idempotency_key(idempotency_key)
        if existing is not None:
            return existing

        due_at = next_attempt_at or utc_now()
        if due_at.utcoffset() is None:
            raise ValueError("next_attempt_at must include a timezone offset")
        record = OutboxTaskRecord(
            type=task_type,
            schema_version=schema_version,
            payload=payload,
            status=OutboxStatus.PENDING.value,
            idempotency_key=idempotency_key,
            attempt_count=0,
            next_attempt_at=due_at,
        )
        savepoint = await self._session.begin_nested()
        try:
            self._session.add(record)
            await self._session.flush()
        except IntegrityError:
            await savepoint.rollback()
            existing = await self.get_by_idempotency_key(idempotency_key)
            if existing is None:
                raise
            return existing
        else:
            await savepoint.commit()
        await self._session.refresh(record)
        return self._to_task(record)

    async def get(self, task_id: str) -> OutboxTask | None:
        record = await self._session.get(OutboxTaskRecord, task_id)
        return self._to_task(record) if record is not None else None

    async def get_by_idempotency_key(self, key: str) -> OutboxTask | None:
        record = await self._session.scalar(
            select(OutboxTaskRecord).where(OutboxTaskRecord.idempotency_key == key)
        )
        return self._to_task(record) if record is not None else None

    async def list_pending(self, *, now: datetime | None = None) -> list[OutboxTask]:
        current = now or utc_now()
        records = (
            await self._session.scalars(
                select(OutboxTaskRecord)
                .where(
                    OutboxTaskRecord.status.in_(
                        [OutboxStatus.PENDING.value, OutboxStatus.RETRY.value]
                    ),
                    OutboxTaskRecord.next_attempt_at <= current,
                )
                .order_by(OutboxTaskRecord.next_attempt_at, OutboxTaskRecord.created_at)
            )
        ).all()
        return [self._to_task(record) for record in records]

    async def claim_next(
        self,
        *,
        task_types: set[str] | None = None,
        now: datetime | None = None,
    ) -> OutboxTask | None:
        current = now or utc_now()
        statement = select(OutboxTaskRecord.id).where(
            OutboxTaskRecord.status.in_([OutboxStatus.PENDING.value, OutboxStatus.RETRY.value]),
            OutboxTaskRecord.next_attempt_at <= current,
        )
        if task_types:
            statement = statement.where(OutboxTaskRecord.type.in_(task_types))
        task_id = await self._session.scalar(
            statement.order_by(OutboxTaskRecord.next_attempt_at, OutboxTaskRecord.created_at).limit(
                1
            )
        )
        if task_id is None:
            return None
        claimed = cast(
            CursorResult[Any],
            await self._session.execute(
                update(OutboxTaskRecord)
                .where(
                    OutboxTaskRecord.id == task_id,
                    OutboxTaskRecord.status.in_(
                        [OutboxStatus.PENDING.value, OutboxStatus.RETRY.value]
                    ),
                    OutboxTaskRecord.next_attempt_at <= current,
                )
                .values(
                    status=OutboxStatus.PROCESSING.value,
                    attempt_count=OutboxTaskRecord.attempt_count + 1,
                    updated_at=current,
                )
            ),
        )
        if claimed.rowcount != 1:
            return None
        record = await self._session.get(OutboxTaskRecord, task_id)
        if record is None:  # defensive: conditional update proved it existed
            return None
        return self._to_task(record)

    async def mark_completed(self, task_id: str, *, now: datetime | None = None) -> None:
        record = await self._require(task_id)
        record.status = OutboxStatus.COMPLETED.value
        record.last_error = None
        record.updated_at = now or utc_now()
        await self._session.flush()

    async def mark_failed(
        self,
        task_id: str,
        *,
        error: str,
        dead_letter: bool,
        next_attempt_at: datetime | None = None,
        now: datetime | None = None,
    ) -> None:
        record = await self._require(task_id)
        record.status = OutboxStatus.DEAD_LETTER.value if dead_letter else OutboxStatus.RETRY.value
        record.last_error = error[:4000]
        record.next_attempt_at = next_attempt_at or record.next_attempt_at
        record.updated_at = now or utc_now()
        await self._session.flush()

    async def recover_stale(
        self,
        *,
        stale_before: datetime,
        now: datetime | None = None,
    ) -> int:
        current = now or utc_now()
        result = cast(
            CursorResult[Any],
            await self._session.execute(
                update(OutboxTaskRecord)
                .where(
                    OutboxTaskRecord.status == OutboxStatus.PROCESSING.value,
                    OutboxTaskRecord.updated_at <= stale_before,
                )
                .values(
                    status=OutboxStatus.RETRY.value,
                    next_attempt_at=current,
                    last_error="OUTBOX_STALE_CLAIM_RECOVERED",
                    updated_at=current,
                )
            ),
        )
        return int(result.rowcount or 0)

    async def _require(self, task_id: str) -> OutboxTaskRecord:
        record = await self._session.get(OutboxTaskRecord, task_id)
        if record is None:
            raise KeyError(f"outbox task not found: {task_id}")
        return record

    @staticmethod
    def _to_task(record: OutboxTaskRecord) -> OutboxTask:
        return OutboxTask(
            id=record.id,
            type=record.type,
            schema_version=record.schema_version,
            payload=record.payload,
            status=OutboxStatus(record.status),
            idempotency_key=record.idempotency_key,
            attempt_count=record.attempt_count,
            next_attempt_at=_aware(record.next_attempt_at),
            last_error=record.last_error,
            created_at=_aware(record.created_at),
            updated_at=_aware(record.updated_at),
        )


class OutboxProducer:
    """显式 producer；复用 owner transaction 的 AsyncSession。"""

    def __init__(self, session: AsyncSession) -> None:
        self._repository = OutboxRepository(session)

    async def enqueue(
        self,
        *,
        task_type: str,
        schema_version: str,
        payload: dict[str, Any],
        idempotency_key: str,
        next_attempt_at: datetime | None = None,
    ) -> OutboxTask:
        return await self._repository.enqueue(
            task_type=task_type,
            schema_version=schema_version,
            payload=payload,
            idempotency_key=idempotency_key,
            next_attempt_at=next_attempt_at,
        )


TaskHandler = Callable[[OutboxTask], Awaitable[None]]


class DurableOutboxWorker:
    """EVENT-041/042：至少一次、指数退避、可恢复的本地 worker。"""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        handlers: Mapping[str, TaskHandler],
        *,
        max_attempts: int = 5,
        base_retry_seconds: int = 5,
    ) -> None:
        self._session_factory = session_factory
        self._handlers = dict(handlers)
        self._max_attempts = max_attempts
        self._base_retry_seconds = base_retry_seconds

    async def run_once(self, *, now: datetime | None = None) -> bool:
        current = now or utc_now()
        async with self._session_factory() as session:
            async with session.begin():
                task = await OutboxRepository(session).claim_next(now=current)
        if task is None:
            return False

        failure: str | None = None
        permanent = False
        if task.type not in self._handlers:
            failure = f"OUTBOX_HANDLER_NOT_FOUND:{task.type}"
            permanent = True
        elif task.schema_version.split(".", maxsplit=1)[0] != "1":
            failure = f"OUTBOX_UNSUPPORTED_SCHEMA_VERSION:{task.schema_version}"
            permanent = True
        else:
            try:
                await self._handlers[task.type](task)
            except PermanentTaskError as exc:
                failure = f"OUTBOX_PERMANENT_ERROR:{exc}"
                permanent = True
            except Exception as exc:  # noqa: BLE001 - worker boundary classifies retry
                failure = f"OUTBOX_TRANSIENT_ERROR:{type(exc).__name__}:{exc}"

        async with self._session_factory() as session:
            async with session.begin():
                repository = OutboxRepository(session)
                if failure is None:
                    await repository.mark_completed(task.id, now=current)
                else:
                    exhausted = task.attempt_count >= self._max_attempts
                    delay = self._base_retry_seconds * (2 ** max(task.attempt_count - 1, 0))
                    await repository.mark_failed(
                        task.id,
                        error=failure,
                        dead_letter=permanent or exhausted,
                        next_attempt_at=current + timedelta(seconds=delay),
                        now=current,
                    )
        return True

    async def recover_stale_claims(
        self,
        *,
        lease_timeout: timedelta = timedelta(minutes=5),
        now: datetime | None = None,
    ) -> int:
        current = now or utc_now()
        async with self._session_factory() as session:
            async with session.begin():
                return await OutboxRepository(session).recover_stale(
                    stale_before=current - lease_timeout,
                    now=current,
                )

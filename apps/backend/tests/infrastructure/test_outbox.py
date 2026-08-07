from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import Column, MetaData, String, Table, insert, select

from app.infrastructure.outbox import (
    DurableOutboxWorker,
    OutboxProducer,
    OutboxRepository,
    OutboxStatus,
    PermanentTaskError,
)


async def test_duplicate_outbox_idempotency_key_returns_original_task(sqlite_factory) -> None:
    """PERSIST-030/EXEC001-AC-002."""
    async with sqlite_factory() as session:
        async with session.begin():
            producer = OutboxProducer(session)
            first = await producer.enqueue(
                task_type="projection.update",
                schema_version="1.0",
                payload={"version": 1},
                idempotency_key="projection:fixture:1",
            )
            duplicate = await producer.enqueue(
                task_type="projection.update",
                schema_version="1.0",
                payload={"version": 999},
                idempotency_key="projection:fixture:1",
            )
    assert duplicate.id == first.id
    assert duplicate.payload == {"version": 1}


async def test_worker_retries_transient_errors_and_completes_idempotently(sqlite_factory) -> None:
    """EVENT-041/042: at-least-once worker uses durable exponential retry."""
    now = datetime.now(timezone.utc)
    calls = 0

    async def flaky_handler(_task) -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise TimeoutError("synthetic timeout")

    async with sqlite_factory() as session:
        async with session.begin():
            task = await OutboxProducer(session).enqueue(
                task_type="projection.update",
                schema_version="1.0",
                payload={"synthetic": True},
                idempotency_key="worker:retry:1",
                next_attempt_at=now,
            )

    worker = DurableOutboxWorker(
        sqlite_factory,
        {"projection.update": flaky_handler},
        max_attempts=3,
        base_retry_seconds=1,
    )
    assert await worker.run_once(now=now) is True
    async with sqlite_factory() as session:
        retrying = await OutboxRepository(session).get(task.id)
        assert retrying is not None
        assert retrying.status is OutboxStatus.RETRY
        retry_at = retrying.next_attempt_at

    assert await worker.run_once(now=retry_at) is True
    async with sqlite_factory() as session:
        completed = await OutboxRepository(session).get(task.id)
        assert completed is not None
        assert completed.status is OutboxStatus.COMPLETED
        assert completed.attempt_count == 2


async def test_worker_dead_letters_permanent_and_unknown_schema_errors(sqlite_factory) -> None:
    """EVENT-042/EVENT-AC-007: invalid business/schema tasks are not blindly retried."""
    now = datetime.now(timezone.utc)

    async def invalid_handler(_task) -> None:
        raise PermanentTaskError("synthetic validation failure")

    async with sqlite_factory() as session:
        async with session.begin():
            permanent = await OutboxProducer(session).enqueue(
                task_type="projection.invalid",
                schema_version="1.0",
                payload={},
                idempotency_key="worker:permanent:1",
                next_attempt_at=now,
            )
            unknown = await OutboxProducer(session).enqueue(
                task_type="projection.invalid",
                schema_version="2.0",
                payload={},
                idempotency_key="worker:schema:2",
                next_attempt_at=now,
            )

    worker = DurableOutboxWorker(sqlite_factory, {"projection.invalid": invalid_handler})
    assert await worker.run_once(now=now) is True
    assert await worker.run_once(now=now) is True

    async with sqlite_factory() as session:
        first = await OutboxRepository(session).get(permanent.id)
        second = await OutboxRepository(session).get(unknown.id)
        assert first is not None and first.status is OutboxStatus.DEAD_LETTER
        assert second is not None and second.status is OutboxStatus.DEAD_LETTER
        assert second.last_error == "OUTBOX_UNSUPPORTED_SCHEMA_VERSION:2.0"


async def test_worker_dead_letters_task_without_registered_handler(sqlite_factory) -> None:
    """EVENT-042: poison/unsupported task types remain durable and reviewable."""
    now = datetime.now(timezone.utc)
    async with sqlite_factory() as session:
        async with session.begin():
            task = await OutboxProducer(session).enqueue(
                task_type="unknown.task",
                schema_version="1.0",
                payload={},
                idempotency_key="worker:unknown-handler:1",
                next_attempt_at=now,
            )

    worker = DurableOutboxWorker(sqlite_factory, {})
    assert await worker.run_once(now=now) is True

    async with sqlite_factory() as session:
        failed = await OutboxRepository(session).get(task.id)
        assert failed is not None
        assert failed.status is OutboxStatus.DEAD_LETTER
        assert failed.last_error == "OUTBOX_HANDLER_NOT_FOUND:unknown.task"


async def test_stale_processing_task_is_recovered_after_worker_restart(sqlite_factory) -> None:
    """EXEC001-AC-007/TEST-AC-006."""
    now = datetime.now(timezone.utc)
    old_claim_time = now - timedelta(minutes=10)
    async with sqlite_factory() as session:
        async with session.begin():
            task = await OutboxProducer(session).enqueue(
                task_type="projection.update",
                schema_version="1.0",
                payload={},
                idempotency_key="worker:stale:1",
                next_attempt_at=old_claim_time,
            )
            claimed = await OutboxRepository(session).claim_next(now=old_claim_time)
            assert claimed is not None
            assert claimed.id == task.id

    worker = DurableOutboxWorker(sqlite_factory, {"projection.update": _noop})
    assert await worker.recover_stale_claims(now=now) == 1
    async with sqlite_factory() as session:
        recovered = await OutboxRepository(session).get(task.id)
        assert recovered is not None
        assert recovered.status is OutboxStatus.RETRY
        assert recovered.last_error == "OUTBOX_STALE_CLAIM_RECOVERED"


async def _noop(_task) -> None:
    return None


async def test_owner_state_and_outbox_share_one_atomic_transaction(
    sqlite_factory, tmp_path
) -> None:
    """EVENT-AC-005/EXEC001-AC-003: rollback removes owner state and outbox together."""
    metadata = MetaData()
    owned_state = Table(
        "synthetic_owner_state",
        metadata,
        Column("id", String(36), primary_key=True),
        Column("value", String(100), nullable=False),
    )
    bind = sqlite_factory.kw["bind"]
    async with bind.begin() as connection:
        await connection.run_sync(metadata.create_all)

    with pytest.raises(RuntimeError, match="synthetic owner failure"):
        async with sqlite_factory() as session:
            async with session.begin():
                await session.execute(insert(owned_state).values(id="state-1", value="accepted"))
                await OutboxProducer(session).enqueue(
                    task_type="state.changed",
                    schema_version="1.0",
                    payload={"state_id": "state-1"},
                    idempotency_key="state-1:v1",
                )
                raise RuntimeError("synthetic owner failure")

    async with sqlite_factory() as session:
        assert (await session.execute(select(owned_state))).all() == []
        assert await OutboxRepository(session).get_by_idempotency_key("state-1:v1") is None

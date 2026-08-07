from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base
from app.infrastructure.outbox import OutboxProducer, OutboxRepository, OutboxStatus


@pytest.mark.asyncio
async def test_processing_task_returns_to_retry_after_process_restart(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'pending-recovery.db'}"
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    stale_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    async with factory() as session:
        task = await OutboxProducer(session).enqueue(
            task_type="review.due.check",
            schema_version="1.0",
            payload={"schedule_id": "schedule-recovery"},
            idempotency_key="recovery-gate-task",
            next_attempt_at=stale_time,
        )
        claimed = await OutboxRepository(session).claim_next(now=stale_time)
        assert claimed is not None
        await session.commit()
    await engine.dispose()

    restarted = create_async_engine(database_url)
    restarted_factory = async_sessionmaker(restarted, expire_on_commit=False)
    async with restarted_factory() as session:
        repository = OutboxRepository(session)
        recovered = await repository.recover_stale(
            stale_before=datetime.now(timezone.utc),
            now=datetime.now(timezone.utc),
        )
        await session.commit()
        restored = await repository.get(task.id)
        assert recovered == 1
        assert restored is not None
        assert restored.status == OutboxStatus.RETRY
    await restarted.dispose()

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.infrastructure.ledger import LearningEventRepository
from app.infrastructure.outbox import OutboxProducer, OutboxRepository, OutboxStatus
from tests.infrastructure.factories import make_event

BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _run_alembic(database_url: str, *arguments: str) -> None:
    env = os.environ.copy()
    env.update(
        {
            "APP_ENV": "test",
            "DATABASE_URL": database_url,
            "JWT_SECRET_KEY": "test-secret-key-at-least-32-chars!!",
            "KEK_MASTER_KEY": "test-kek-key-at-least-32-bytes-long!!",
        }
    )
    completed = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "alembic", *arguments],
        cwd=BACKEND_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


async def test_migration_upgrade_forward_fix_and_restart_recovery(tmp_path) -> None:
    """PERSIST-090/EXEC001-AC-007: migrated SQLite survives reopen with pending work."""
    database_path = tmp_path / "representative.db"
    database_url = f"sqlite+aiosqlite:///{database_path}"

    # Representative old schema -> new additive schema -> rollback -> forward-fix.
    _run_alembic(database_url, "upgrade", "b87ea36c12f4")
    _run_alembic(database_url, "upgrade", "head")
    _run_alembic(database_url, "downgrade", "b87ea36c12f4")
    _run_alembic(database_url, "upgrade", "head")

    engine = create_async_engine(database_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    event = make_event()
    async with factory() as session:
        async with session.begin():
            await LearningEventRepository(session).append(event)
            task = await OutboxProducer(session).enqueue(
                task_type="projection.update",
                schema_version="1.0",
                payload={"event_id": str(event.event_id)},
                idempotency_key=f"projection:{event.event_id}",
            )
    await engine.dispose()

    reopened_engine = create_async_engine(database_url)
    reopened_factory = async_sessionmaker(reopened_engine, expire_on_commit=False)
    async with reopened_factory() as session:
        stored_event = await LearningEventRepository(session).get(event.event_id)
        pending_task = await OutboxRepository(session).get(task.id)
        assert stored_event == event
        assert pending_task is not None
        assert pending_task.status is OutboxStatus.PENDING
        assert [item.id for item in await OutboxRepository(session).list_pending()] == [task.id]
    await reopened_engine.dispose()

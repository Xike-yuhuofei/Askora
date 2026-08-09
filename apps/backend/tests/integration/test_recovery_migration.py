"""P1-07 recovery ledger migration and forward-fix evidence."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from app import models  # noqa: F401 - register tables for create_all compatibility
from app.core.database import Base

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PREVIOUS_HEAD = "a80d4f9c2b61"


def _alembic(database_url: str, *arguments: str) -> None:
    environment = os.environ.copy()
    environment["DATABASE_URL"] = database_url
    subprocess.run(  # noqa: S603
        [sys.executable, "-m", "alembic", *arguments],
        cwd=BACKEND_ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )


async def _has_recovery_table(database_url: str) -> bool:
    engine = create_async_engine(database_url)
    async with engine.connect() as connection:
        names = await connection.run_sync(lambda sync: inspect(sync).get_table_names())
    await engine.dispose()
    return "recovery_events" in names


@pytest.mark.asyncio
async def test_recovery_ledger_upgrade_downgrade_forward_fix(tmp_path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'recovery-migration.db'}"
    _alembic(database_url, "upgrade", PREVIOUS_HEAD)
    assert not await _has_recovery_table(database_url)
    _alembic(database_url, "upgrade", "head")
    _alembic(database_url, "check")
    assert await _has_recovery_table(database_url)
    _alembic(database_url, "downgrade", PREVIOUS_HEAD)
    assert not await _has_recovery_table(database_url)
    _alembic(database_url, "upgrade", "head")
    assert await _has_recovery_table(database_url)


@pytest.mark.asyncio
async def test_recovery_upgrade_accepts_matching_table_precreated_by_app_startup(
    tmp_path,
) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'precreated-recovery.db'}"
    _alembic(database_url, "upgrade", PREVIOUS_HEAD)
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    await engine.dispose()

    assert await _has_recovery_table(database_url)
    _alembic(database_url, "upgrade", "head")
    _alembic(database_url, "check")

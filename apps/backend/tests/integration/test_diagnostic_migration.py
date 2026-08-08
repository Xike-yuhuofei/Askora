"""EXEC-022 migration upgrade/rollback/forward-fix evidence."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PREVIOUS_HEAD = "f21a8b07d04a"


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


@pytest.mark.asyncio
async def test_exec022_diagnostic_migration_upgrade_rollback_forward_fix(tmp_path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'diagnostic-migration.db'}"
    _alembic(database_url, "upgrade", PREVIOUS_HEAD)
    _alembic(database_url, "upgrade", "head")
    engine = create_async_engine(database_url)
    async with engine.connect() as connection:
        tables = await connection.run_sync(lambda sync: set(inspect(sync).get_table_names()))
        assert {"learner_state_versions", "diagnostic_need_versions"}.issubset(tables)
        assert "canonical_mastery_estimate_versions" in tables
        assert "learning_plan_versions" in tables
    await engine.dispose()

    _alembic(database_url, "downgrade", PREVIOUS_HEAD)
    rolled_back = create_async_engine(database_url)
    async with rolled_back.connect() as connection:
        tables = await connection.run_sync(lambda sync: set(inspect(sync).get_table_names()))
        assert "learner_state_versions" not in tables
        assert "diagnostic_need_versions" not in tables
        assert "canonical_mastery_estimate_versions" in tables
        assert "learning_plan_versions" in tables
    await rolled_back.dispose()

    _alembic(database_url, "upgrade", "head")
    _alembic(database_url, "check")

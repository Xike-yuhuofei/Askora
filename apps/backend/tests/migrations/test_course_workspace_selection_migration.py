"""CWSP-070 fresh/legacy/rerun migration evidence for XIK-189."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PREVIOUS_HEAD = "w171r0e0a002"
COURSE_WORKSPACE_HEAD = "c189s0e0a001"


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
async def test_cwsp_fresh_migration_keeps_zero_workspace_and_selection(tmp_path) -> None:
    """CWSP-AC-001/011: schema creation itself does not invent a Course."""
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'fresh-course.db'}"
    _alembic(database_url, "upgrade", COURSE_WORKSPACE_HEAD)
    engine = create_async_engine(database_url)
    async with engine.connect() as connection:
        tables = await connection.run_sync(lambda sync: set(inspect(sync).get_table_names()))
        assert {"workspace_selections", "workspace_command_receipts"} <= tables
        assert (await connection.execute(text("SELECT COUNT(*) FROM workspaces"))).scalar() == 0
        assert (
            await connection.execute(text("SELECT COUNT(*) FROM workspace_selections"))
        ).scalar() == 0
        columns = await connection.run_sync(
            lambda sync: {item["name"] for item in inspect(sync).get_columns("learning_sessions")}
        )
        assert "learning_activity_id" in columns
    await engine.dispose()


@pytest.mark.asyncio
async def test_cwsp_existing_default_gets_one_selection_and_rerun_is_idempotent(tmp_path) -> None:
    """CWSP-AC-002/011: upgraded owners select the exact active default once."""
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'legacy-course.db'}"
    _alembic(database_url, "upgrade", PREVIOUS_HEAD)
    engine = create_async_engine(database_url)
    owner_id = str(uuid4())
    workspace_id = str(uuid4())
    now = datetime.now(timezone.utc)
    async with engine.begin() as connection:
        owners = await connection.run_sync(
            lambda sync: sa.Table("local_owners", sa.MetaData(), autoload_with=sync)
        )
        workspaces = await connection.run_sync(
            lambda sync: sa.Table("workspaces", sa.MetaData(), autoload_with=sync)
        )
        await connection.execute(
            owners.insert().values(
                singleton_key=1,
                owner_id=owner_id,
                schema_version="1.0",
                provenance="fresh",
                created_at=now,
            )
        )
        await connection.execute(
            workspaces.insert().values(
                workspace_id=workspace_id,
                owner_id=owner_id,
                version=1,
                display_name="旧课程",
                is_default=True,
                lifecycle="active",
                created_at=now,
                updated_at=now,
            )
        )
    await engine.dispose()

    _alembic(database_url, "upgrade", COURSE_WORKSPACE_HEAD)
    _alembic(database_url, "upgrade", COURSE_WORKSPACE_HEAD)
    engine = create_async_engine(database_url)
    async with engine.connect() as connection:
        row = (
            await connection.execute(
                text(
                    "SELECT owner_id, version, current_workspace_id, reason "
                    "FROM workspace_selections"
                )
            )
        ).one()
        assert tuple(row) == (owner_id, 1, workspace_id, "LEGACY_MIGRATION")
        assert (
            await connection.execute(text("SELECT COUNT(*) FROM workspace_selections"))
        ).scalar() == 1
    await engine.dispose()

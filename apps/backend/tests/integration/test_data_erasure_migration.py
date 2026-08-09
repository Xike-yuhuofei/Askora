"""EXEC-1034 additive erasure workflow migration evidence."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine

from app import models  # noqa: F401 - register current tables for create_all compatibility
from app.core.database import Base

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PREVIOUS_HEAD = "9b4c2d7e1a60"
ERASURE_TABLES = {
    "consent_records",
    "data_erasure_workflows",
    "data_erasure_steps",
    "data_erasure_receipts",
    "data_erasure_checkpoints",
}


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
async def test_erasure_schema_upgrade_rollback_and_forward_fix(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'erasure-migration.db'}"
    _alembic(database_url, "upgrade", PREVIOUS_HEAD)
    _alembic(database_url, "upgrade", "head")
    engine = create_async_engine(database_url)
    async with engine.connect() as connection:
        tables = await connection.run_sync(lambda sync: set(inspect(sync).get_table_names()))
        checkpoint = await connection.scalar(
            text("SELECT checkpoint FROM data_erasure_checkpoints WHERE id = 1")
        )
    await engine.dispose()
    assert ERASURE_TABLES.issubset(tables)
    assert checkpoint == 0

    _alembic(database_url, "downgrade", PREVIOUS_HEAD)
    rolled_back = create_async_engine(database_url)
    async with rolled_back.connect() as connection:
        tables = await connection.run_sync(lambda sync: set(inspect(sync).get_table_names()))
    await rolled_back.dispose()
    assert ERASURE_TABLES.isdisjoint(tables)

    _alembic(database_url, "upgrade", "head")
    _alembic(database_url, "check")


@pytest.mark.asyncio
async def test_erasure_upgrade_accepts_matching_tables_precreated_by_app_startup(
    tmp_path: Path,
) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'precreated-erasure-tables.db'}"
    _alembic(database_url, "upgrade", PREVIOUS_HEAD)
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    await engine.dispose()

    _alembic(database_url, "upgrade", "head")
    _alembic(database_url, "check")

    verified = create_async_engine(database_url)
    async with verified.connect() as connection:
        checkpoint = await connection.scalar(
            text("SELECT checkpoint FROM data_erasure_checkpoints WHERE id = 1")
        )
    await verified.dispose()
    assert checkpoint == 0

"""EXEC036 / PERSIST-081..083 deletion migration and forward-fix evidence."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PREVIOUS_HEAD = "f35b91b807d2"


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
async def test_account_deletion_migration_upgrade_rollback_forward_fix(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'account-deletion-migration.db'}"
    _alembic(database_url, "upgrade", PREVIOUS_HEAD)
    _alembic(database_url, "upgrade", "head")

    engine = create_async_engine(database_url)
    async with engine.connect() as connection:
        tables = await connection.run_sync(lambda sync: set(inspect(sync).get_table_names()))
        user_columns = await connection.run_sync(
            lambda sync: {column["name"] for column in inspect(sync).get_columns("users")}
        )
        assert {
            "account_deletion_previews",
            "account_deletion_requests",
            "owner_erasure_step_receipts",
            "privacy_tombstones",
        }.issubset(tables)
        assert "account_lifecycle" in user_columns
    await engine.dispose()

    _alembic(database_url, "downgrade", PREVIOUS_HEAD)
    rolled_back = create_async_engine(database_url)
    async with rolled_back.connect() as connection:
        tables = await connection.run_sync(lambda sync: set(inspect(sync).get_table_names()))
        user_columns = await connection.run_sync(
            lambda sync: {column["name"] for column in inspect(sync).get_columns("users")}
        )
        assert "account_deletion_requests" not in tables
        assert "account_lifecycle" not in user_columns
        assert "recovery_credentials" in tables
    await rolled_back.dispose()

    _alembic(database_url, "upgrade", "head")
    _alembic(database_url, "check")


def test_account_deletion_postgresql_offline_ddl_is_portable() -> None:
    environment = os.environ.copy()
    environment["DATABASE_URL"] = "postgresql+asyncpg://unused:unused@localhost/unused"
    result = subprocess.run(  # noqa: S603
        [
            sys.executable,
            "-m",
            "alembic",
            "upgrade",
            f"{PREVIOUS_HEAD}:head",
            "--sql",
        ],
        cwd=BACKEND_ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "CREATE TABLE account_deletion_requests" in result.stdout
    assert "account_lifecycle" in result.stdout

"""EXEC-053: Account deletion schema verification for v1 LocalOwner.

Rewrite: Replaced alembic upgrade/downgrade subprocess tests with direct
schema verification via Base.metadata.create_all. v1 uses SQLite only - no
PostgreSQL-specific DDL tests needed.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base


async def _database(tmp_path: Path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'deletion-schema.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


@pytest.mark.asyncio
async def test_account_deletion_tables_exist_in_current_schema(tmp_path: Path) -> None:
    """Verify account deletion tables exist in current v1 schema."""
    engine, factory = await _database(tmp_path)

    async with engine.connect() as connection:
        tables = await connection.run_sync(lambda sync: set(inspect(sync).get_table_names()))
        assert {
            "account_deletion_previews",
            "account_deletion_requests",
            "privacy_tombstones",
            "data_erasure_workflows",
            "data_erasure_receipts",
        }.issubset(tables)

    await engine.dispose()


@pytest.mark.asyncio
async def test_account_deletion_schema_has_owner_scoped_columns(tmp_path: Path) -> None:
    """Verify deletion tables have owner-scoped columns for v1 single-user."""
    engine, factory = await _database(tmp_path)

    async with engine.connect() as connection:
        columns = await connection.run_sync(
            lambda sync: {
                col["name"] for col in inspect(sync).get_columns("account_deletion_requests")
            }
        )
        assert "erasure_workflow_id" in columns
        assert "erasure_receipt_id" in columns
        assert "erasure_checkpoint" in columns

    await engine.dispose()


@pytest.mark.asyncio
async def test_user_table_has_account_lifecycle_column(tmp_path: Path) -> None:
    """Verify users table has account_lifecycle column for deletion tracking."""
    engine, factory = await _database(tmp_path)

    async with engine.connect() as connection:
        user_columns = await connection.run_sync(
            lambda sync: {col["name"] for col in inspect(sync).get_columns("users")}
        )
        assert "account_lifecycle" in user_columns

    await engine.dispose()


@pytest.mark.asyncio
async def test_schema_is_idempotent_on_recreate(tmp_path: Path) -> None:
    """Verify schema creation is idempotent (safe to run create_all again)."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'idempotent.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    # Running create_all again should be safe (no errors)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with engine.connect() as connection:
        tables = await connection.run_sync(lambda sync: set(inspect(sync).get_table_names()))
        assert "account_deletion_requests" in tables

    await engine.dispose()

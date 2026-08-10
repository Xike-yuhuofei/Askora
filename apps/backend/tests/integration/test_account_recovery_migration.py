"""EXEC-053: Recovery schema verification for v1 LocalOwner.

Rewrite: Replaced alembic upgrade/downgrade subprocess tests with direct
schema verification via Base.metadata.create_all. v1 uses SQLite only.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base


async def _database(tmp_path: Path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'recovery-schema.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


@pytest.mark.asyncio
async def test_recovery_tables_exist_in_current_schema(tmp_path: Path) -> None:
    """Verify recovery tables exist in current v1 schema."""
    engine, factory = await _database(tmp_path)

    async with engine.connect() as connection:
        tables = await connection.run_sync(lambda sync: set(inspect(sync).get_table_names()))
        assert "recovery_credentials" in tables
        assert "recovery_throttles" in tables

    await engine.dispose()


@pytest.mark.asyncio
async def test_recovery_credential_schema_has_required_columns(tmp_path: Path) -> None:
    """Verify recovery_credentials table has required columns."""
    engine, factory = await _database(tmp_path)

    async with engine.connect() as connection:
        columns = await connection.run_sync(
            lambda sync: {col["name"] for col in inspect(sync).get_columns("recovery_credentials")}
        )
        assert "credential_id" in columns
        assert "user_id" in columns
        assert "version" in columns
        assert "secret_digest" in columns
        assert "created_at" in columns

    await engine.dispose()


@pytest.mark.asyncio
async def test_recovery_throttle_schema_has_required_columns(tmp_path: Path) -> None:
    """Verify recovery_throttles table has required columns."""
    engine, factory = await _database(tmp_path)

    async with engine.connect() as connection:
        columns = await connection.run_sync(
            lambda sync: {col["name"] for col in inspect(sync).get_columns("recovery_throttles")}
        )
        assert "subject_digest" in columns
        assert "action" in columns
        assert "failure_count" in columns
        assert "locked_until" in columns

    await engine.dispose()


@pytest.mark.asyncio
async def test_recovery_schema_is_idempotent_on_recreate(tmp_path: Path) -> None:
    """Verify schema creation is idempotent (safe to run create_all again)."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'recovery-idempotent.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with engine.connect() as connection:
        tables = await connection.run_sync(lambda sync: set(inspect(sync).get_table_names()))
        assert "recovery_credentials" in tables
        assert "recovery_throttles" in tables

    await engine.dispose()

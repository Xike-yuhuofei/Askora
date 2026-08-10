"""EXEC-055 CI v2 Quality Gate: SQLite migration gate tests."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PREVIOUS_HEAD = "p107d2f1a04"
CURRENT_HEAD = "b1c0d2f3a001"


def _alembic(database_url: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["DATABASE_URL"] = database_url
    return subprocess.run(  # noqa: S603
        [sys.executable, "-m", "alembic", *arguments],
        cwd=BACKEND_ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.mark.asyncio
async def test_fresh_sqlite_migrates_to_head(tmp_path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'fresh.db'}"
    _alembic(database_url, "upgrade", "head")
    engine = create_async_engine(database_url)
    async with engine.connect() as connection:
        tables = await connection.run_sync(lambda sync: inspect(sync).get_table_names())
        assert "users" in tables
        assert "user_documents" in tables
        assert "document_chunks" in tables
        assert "outbox_tasks" in tables
        assert "local_owners" in tables
        assert "recovery_events" in tables
        result = await connection.execute(text("SELECT 1 FROM users LIMIT 1"))
        assert result.fetchone() is None
        result = await connection.execute(text("SELECT 1 FROM local_owners LIMIT 1"))
        assert result.fetchone() is None
    await engine.dispose()


@pytest.mark.asyncio
async def test_legacy_sqlite_fixture_migrates_to_head(tmp_path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'legacy.db'}"
    _alembic(database_url, "upgrade", PREVIOUS_HEAD)
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        users = await connection.run_sync(
            lambda sync: sa.Table("users", sa.MetaData(), autoload_with=sync)
        )
        user_id = str(uuid4())
        pseudonym_id = "legacy-pseudo-001"
        await connection.execute(
            users.insert().values(
                id=user_id,
                role="USER",
                status="ACTIVE",
                is_verified=False,
                pseudonym_id=pseudonym_id,
            )
        )
        doc_table = await connection.run_sync(
            lambda sync: sa.Table("user_documents", sa.MetaData(), autoload_with=sync)
        )
        doc_id = str(uuid4())
        await connection.execute(
            doc_table.insert().values(
                id=doc_id,
                pseudonym_id=pseudonym_id,
                original_filename="legacy_doc.md",
                file_extension="md",
                file_size_bytes=1024,
                storage_path=f"{pseudonym_id}/{doc_id}_legacy.md",
                processing_status="completed",
                metadata_version=1,
                moderation_status="approved",
                moderation_categories=[],
                moderation_details={},
                chunk_count=0,
                total_tokens=0,
                access_count=0,
                is_deleted=False,
            )
        )
    await engine.dispose()

    _alembic(database_url, "upgrade", "head")
    engine = create_async_engine(database_url)
    async with engine.connect() as connection:
        user_count = (await connection.execute(text("SELECT COUNT(*) FROM users"))).scalar()
        assert user_count == 1
        doc_count = (await connection.execute(text("SELECT COUNT(*) FROM user_documents"))).scalar()
        assert doc_count == 1
        owner_count = (await connection.execute(text("SELECT COUNT(*) FROM local_owners"))).scalar()
        assert owner_count == 1
    await engine.dispose()


@pytest.mark.asyncio
async def test_migration_failure_preserves_durable_data(tmp_path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'failure.db'}"
    _alembic(database_url, "upgrade", PREVIOUS_HEAD)
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        users = await connection.run_sync(
            lambda sync: sa.Table("users", sa.MetaData(), autoload_with=sync)
        )
        user_id = str(uuid4())
        await connection.execute(
            users.insert().values(
                id=user_id,
                role="USER",
                status="ACTIVE",
                is_verified=False,
                pseudonym_id="failure-pseudo",
            )
        )
        doc_table = await connection.run_sync(
            lambda sync: sa.Table("user_documents", sa.MetaData(), autoload_with=sync)
        )
        doc_id = str(uuid4())
        await connection.execute(
            doc_table.insert().values(
                id=doc_id,
                pseudonym_id="failure-pseudo",
                original_filename="recovery_doc.md",
                file_extension="md",
                file_size_bytes=2048,
                storage_path=f"failure-pseudo/{doc_id}_recovery.md",
                processing_status="completed",
                metadata_version=1,
                moderation_status="approved",
                moderation_categories=[],
                moderation_details={},
                chunk_count=0,
                total_tokens=0,
                access_count=0,
                is_deleted=False,
            )
        )
    await engine.dispose()

    _alembic(database_url, "upgrade", "head")
    _alembic(database_url, "downgrade", PREVIOUS_HEAD)
    _alembic(database_url, "upgrade", "head")

    engine = create_async_engine(database_url)
    async with engine.connect() as connection:
        user_count = (await connection.execute(text("SELECT COUNT(*) FROM users"))).scalar()
        assert user_count == 1
        doc_count = (await connection.execute(text("SELECT COUNT(*) FROM user_documents"))).scalar()
        assert doc_count == 1
        doc = (
            await connection.execute(text("SELECT id, original_filename FROM user_documents"))
        ).fetchone()
        assert doc is not None
        assert doc[1] == "recovery_doc.md"
    await engine.dispose()


@pytest.mark.asyncio
async def test_data_dir_schema_version_check(tmp_path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'schemaver.db'}"
    _alembic(database_url, "upgrade", "head")
    engine = create_async_engine(database_url)
    async with engine.connect() as connection:
        columns = await connection.run_sync(lambda sync: inspect(sync).get_columns("local_owners"))
        col_names = {c["name"] for c in columns}
        assert "schema_version" in col_names

        result = await connection.execute(text("SELECT schema_version FROM local_owners LIMIT 1"))
        row = result.fetchone()
        if row is not None:
            assert row[0] is not None
    await engine.dispose()


def test_migration_heads_are_clean() -> None:
    result = _alembic("sqlite+aiosqlite:///:memory:", "heads")
    assert f"{CURRENT_HEAD} (head)" in result.stdout

"""EXEC-026 SYS08 transcript projection migration evidence."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from app import models  # noqa: F401 - register tables for create_all compatibility regression
from app.core.database import Base

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PREVIOUS_HEAD = "9b4c2d7e1a60"


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


async def _book_learning_tables(database_url: str) -> set[str]:
    engine = create_async_engine(database_url)
    async with engine.connect() as connection:
        names = await connection.run_sync(lambda sync: inspect(sync).get_table_names())
    await engine.dispose()
    return {
        name
        for name in names
        if name in {"book_learning_transcript_turns", "book_learning_advance_records"}
    }


@pytest.mark.asyncio
async def test_exec026_transcript_upgrade_rollback_forward_fix(tmp_path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'book-transcript-migration.db'}"
    _alembic(database_url, "upgrade", PREVIOUS_HEAD)
    assert not await _book_learning_tables(database_url)

    _alembic(database_url, "upgrade", "head")
    assert await _book_learning_tables(database_url) == {
        "book_learning_transcript_turns",
        "book_learning_advance_records",
    }


@pytest.mark.asyncio
async def test_exec026_upgrade_accepts_matching_tables_precreated_by_app_startup(tmp_path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'precreated-transcript-tables.db'}"
    _alembic(database_url, "upgrade", PREVIOUS_HEAD)
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    await engine.dispose()

    assert await _book_learning_tables(database_url) == {
        "book_learning_transcript_turns",
        "book_learning_advance_records",
    }
    _alembic(database_url, "upgrade", "head")
    _alembic(database_url, "check")
    _alembic(database_url, "upgrade", "head")
    _alembic(database_url, "check")

    _alembic(database_url, "downgrade", PREVIOUS_HEAD)
    assert not await _book_learning_tables(database_url)

    _alembic(database_url, "upgrade", "head")
    assert await _book_learning_tables(database_url) == {
        "book_learning_transcript_turns",
        "book_learning_advance_records",
    }

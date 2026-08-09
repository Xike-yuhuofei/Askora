"""P1-04 SQLite migration, backfill and rollback evidence."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PREVIOUS_HEAD = "e30c06a1b2c3"


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
async def test_library_migration_backfills_current_visible_search_and_is_recoverable(
    tmp_path: Path,
) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'library-migration.db'}"
    _alembic(database_url, "upgrade", PREVIOUS_HEAD)
    previous = create_async_engine(database_url)
    revision_id = "11111111-1111-4111-8111-111111111111"
    visible_span_id = "22222222-2222-4222-8222-222222222222"
    hidden_span_id = "33333333-3333-4333-8333-333333333333"
    details = {
        "raw_asset_checksum": "a" * 64,
        "content_knowledge_v1": {
            "current_revision_id": revision_id,
            "revisions": [
                {
                    "revision_id": revision_id,
                    "source_spans": [
                        {"span_id": visible_span_id, "text": "迁移后可搜索的热力学正文"},
                        {
                            "span_id": hidden_span_id,
                            "text": "[grader-only] reference answer: hidden",
                        },
                    ],
                }
            ],
        },
    }
    async with previous.begin() as connection:
        await connection.exec_driver_sql(
            "INSERT INTO users (id, role, status, is_verified, pseudonym_id) "
            "VALUES (?, ?, ?, ?, ?)",
            ("legacy-user", "USER", "ACTIVE", 0, "legacy-library-owner"),
        )
        await connection.exec_driver_sql(
            "INSERT INTO user_documents ("
            "id, pseudonym_id, original_filename, file_extension, file_size_bytes, "
            "storage_path, processing_status, moderation_status, moderation_categories, "
            "moderation_details, chunk_count, total_tokens, access_count, is_deleted"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "legacy-document",
                "legacy-library-owner",
                "Legacy Notes.md",
                "md",
                128,
                "legacy/file.md",
                "completed",
                "approved",
                "[]",
                json.dumps(details),
                1,
                20,
                0,
                0,
            ),
        )
    await previous.dispose()

    _alembic(database_url, "upgrade", "head")
    upgraded = create_async_engine(database_url)
    async with upgraded.connect() as connection:
        profile = (
            await connection.exec_driver_sql(
                "SELECT display_title, metadata_version, raw_asset_checksum, "
                "content_fingerprint, fingerprint_version FROM user_documents "
                "WHERE id = ?",
                ("legacy-document",),
            )
        ).one()
        projection = (
            await connection.exec_driver_sql(
                "SELECT revision_id, normalized_title, normalized_body, source_span_refs "
                "FROM library_search_projections WHERE document_id = ?",
                ("legacy-document",),
            )
        ).one()
        assert profile[0:3] == ("Legacy Notes.md", 1, "a" * 64)
        assert profile.content_fingerprint is not None
        assert profile.fingerprint_version == "normalized-content-v1"
        assert projection.revision_id == revision_id
        assert projection.normalized_title == "legacy notes.md"
        assert "热力学正文" in projection.normalized_body
        assert "reference answer" not in projection.normalized_body
        assert json.loads(projection.source_span_refs) == [visible_span_id]
    await upgraded.dispose()

    _alembic(database_url, "downgrade", PREVIOUS_HEAD)
    rolled_back = create_async_engine(database_url)
    async with rolled_back.connect() as connection:
        tables = await connection.run_sync(lambda sync: set(inspect(sync).get_table_names()))
        columns = await connection.run_sync(
            lambda sync: {item["name"] for item in inspect(sync).get_columns("user_documents")}
        )
        original_filename = (
            await connection.exec_driver_sql(
                "SELECT original_filename FROM user_documents WHERE id = ?",
                ("legacy-document",),
            )
        ).scalar_one()
        assert "library_search_projections" not in tables
        assert "display_title" not in columns
        assert original_filename == "Legacy Notes.md"
    await rolled_back.dispose()

    _alembic(database_url, "upgrade", "head")

"""User authentication removal migration evidence.

Askora is a local single-user learning app with no account/login/auth system.
This verifies that migrating to head removes the authentication-only tables and
columns, and that a downgrade to the pre-LocalOwner revision restores them.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PREVIOUS_HEAD = "f34a91b807d1"

_AUTH_TABLES = {
    "auth_sessions",
    "identity_command_receipts",
    "recovery_credentials",
    "recovery_throttles",
    "account_deletion_requests",
    "account_deletion_previews",
    "privacy_tombstones",
    "owner_erasure_step_receipts",
}
_AUTH_USER_COLUMNS = {
    "account_lifecycle",
    "phone_encrypted",
    "phone_hash",
    "email_encrypted",
    "password_hash",
    "credential_version",
    "password_changed_at",
    "wechat_openid_encrypted",
    "real_name_encrypted",
    "is_verified",
    "last_login_at",
    "deleted_at",
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
async def test_auth_removal_migration_upgrade_rollback(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'auth-removal-migration.db'}"
    _alembic(database_url, "upgrade", PREVIOUS_HEAD)
    _alembic(database_url, "upgrade", "head")

    engine = create_async_engine(database_url)
    async with engine.connect() as connection:
        tables = set(await connection.run_sync(lambda sync: inspect(sync).get_table_names()))
        user_columns = set(
            await connection.run_sync(
                lambda sync: {column["name"] for column in inspect(sync).get_columns("users")}
            )
        )
        # Authentication-only tables/columns are gone after upgrading to head.
        assert not _AUTH_TABLES.intersection(tables)
        assert not _AUTH_USER_COLUMNS.intersection(user_columns)
        # Learner-owned compatibility projection is intact.
        assert {"id", "role", "status", "pseudonym_id"}.issubset(user_columns)
    await engine.dispose()

    _alembic(database_url, "downgrade", PREVIOUS_HEAD)
    rolled_back = create_async_engine(database_url)
    async with rolled_back.connect() as connection:
        tables = set(await connection.run_sync(lambda sync: inspect(sync).get_table_names()))
        user_columns = set(
            await connection.run_sync(
                lambda sync: {column["name"] for column in inspect(sync).get_columns("users")}
            )
        )
        # Downgrade restores the identity-session schema.
        assert "auth_sessions" in tables
        assert "credential_version" in user_columns
    await rolled_back.dispose()

    _alembic(database_url, "upgrade", "head")
    _alembic(database_url, "check")
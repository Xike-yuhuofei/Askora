"""P1-03/P1-07 recovery migration and forward-fix evidence."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from app import models  # noqa: F401 - register tables for create_all compatibility
from app.contracts.data_control import BackupReason
from app.core.database import Base
from app.data_control.crypto import generate_recovery_key, parse_recovery_key
from app.data_control.migration import StagedSchemaMigrator
from app.data_control.recovery import RecoveryManager
from app.data_control.restore import RestoreCoordinator

BACKEND_ROOT = Path(__file__).resolve().parents[2]
RECOVERY_LEDGER_PREVIOUS_HEAD = "a80d4f9c2b61"
OLDER_SUPPORTED_REVISION = "e23a91b807d1"


def _run_alembic(database_url: str, *arguments: str) -> None:
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


async def _has_recovery_table(database_url: str) -> bool:
    engine = create_async_engine(database_url)
    async with engine.connect() as connection:
        names = await connection.run_sync(lambda sync: inspect(sync).get_table_names())
    await engine.dispose()
    return "recovery_events" in names


@pytest.mark.asyncio
async def test_recovery_ledger_upgrade_downgrade_forward_fix(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'recovery-migration.db'}"
    _run_alembic(database_url, "upgrade", RECOVERY_LEDGER_PREVIOUS_HEAD)
    assert not await _has_recovery_table(database_url)
    _run_alembic(database_url, "upgrade", "head")
    _run_alembic(database_url, "check")
    assert await _has_recovery_table(database_url)
    _run_alembic(database_url, "downgrade", RECOVERY_LEDGER_PREVIOUS_HEAD)
    assert not await _has_recovery_table(database_url)
    _run_alembic(database_url, "upgrade", "head")
    assert await _has_recovery_table(database_url)


@pytest.mark.asyncio
async def test_recovery_upgrade_accepts_matching_table_precreated_by_app_startup(
    tmp_path: Path,
) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'precreated-recovery.db'}"
    _run_alembic(database_url, "upgrade", RECOVERY_LEDGER_PREVIOUS_HEAD)
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    await engine.dispose()

    assert await _has_recovery_table(database_url)
    _run_alembic(database_url, "upgrade", "head")
    _run_alembic(database_url, "check")


def test_older_supported_revision_forward_migrates_only_in_staging(
    tmp_path: Path,
) -> None:
    database = tmp_path / "askora.db"
    migrator = StagedSchemaMigrator()
    migrator._run_alembic(database, "upgrade", OLDER_SUPPORTED_REVISION)
    (tmp_path / "documents").mkdir()
    (tmp_path / "local-secrets.json").write_text(
        json.dumps({"jwtSecret": "old-jwt", "kekSecret": "stable-kek"}),
        encoding="utf-8",
    )
    manager = RecoveryManager(
        tmp_path,
        parse_recovery_key(generate_recovery_key()),
        app_version="migration-test",
    )
    point = manager.create_backup(BackupReason.MANUAL)
    coordinator = RestoreCoordinator(manager, migrator=migrator)

    awaiting = coordinator.restore(manager.recovery_dir / point.relative_path)

    assert awaiting.schema_before == OLDER_SUPPORTED_REVISION
    assert awaiting.schema_after == migrator.current_head
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone() == (
            migrator.current_head,
        )
        columns = {
            row[1]: row[2]
            for row in connection.execute(
                "PRAGMA table_info(decision_trace_inputs)"
            ).fetchall()
        }
    assert columns["entity_version"] == "VARCHAR(255)"
    assert coordinator.finalize(awaiting.transaction_id).status == "COMPLETED"

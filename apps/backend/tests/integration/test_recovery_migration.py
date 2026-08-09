"""P1-03/P1-07 recovery migration and forward-fix evidence."""

from __future__ import annotations

import hashlib
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
from app.contracts.data_control import BackupReason, DataControlErrorCode
from app.core.database import Base
from app.data_control.cli import RECOVERY_KEY_ENV, run
from app.data_control.crypto import generate_recovery_key, parse_recovery_key
from app.data_control.migration import StagedSchemaMigrator
from app.data_control.recovery import RecoveryError, RecoveryManager
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


def test_active_upgrade_requires_verified_pre_migration_and_preserves_jwt(
    tmp_path: Path,
) -> None:
    database = tmp_path / "askora.db"
    migrator = StagedSchemaMigrator()
    migrator._run_alembic(database, "upgrade", OLDER_SUPPORTED_REVISION)
    (tmp_path / "documents").mkdir()
    (tmp_path / "local-secrets.json").write_text(
        json.dumps({"jwtSecret": "session-must-survive", "kekSecret": "stable-kek"}),
        encoding="utf-8",
    )
    manager = RecoveryManager(
        tmp_path,
        parse_recovery_key(generate_recovery_key()),
        app_version="active-migration-test",
    )
    coordinator = RestoreCoordinator(manager, migrator=migrator)

    result = coordinator.migrate_active()

    assert result.required is True
    assert result.pre_migration_point is not None
    assert result.pre_migration_point.reason == BackupReason.PRE_MIGRATION
    assert result.pre_migration_point.status.value == "VERIFIED"
    assert result.recovery_report is not None
    assert result.recovery_report.status == "AWAITING_READINESS"
    assert result.schema_before == OLDER_SUPPORTED_REVISION
    assert result.schema_after == migrator.current_head
    active_secrets = json.loads(manager.local_secrets_path.read_text(encoding="utf-8"))
    assert active_secrets == {
        "jwtSecret": "session-must-survive",
        "kekSecret": "stable-kek",
    }
    assert coordinator.finalize(result.recovery_report.transaction_id).status == "COMPLETED"

    no_op = coordinator.migrate_active()
    assert no_op.required is False
    assert no_op.schema_before == migrator.current_head
    assert no_op.schema_after == migrator.current_head
    assert no_op.pre_migration_point is None
    assert no_op.recovery_report is None


def test_active_upgrade_backup_failure_leaves_active_database_unchanged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
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
        app_version="failed-migration-test",
    )
    before = hashlib.sha256(database.read_bytes()).hexdigest()

    def fail_backup(_reason: BackupReason):
        raise RecoveryError(
            DataControlErrorCode.BACKUP_INTEGRITY_FAILED,
            "pre-migration backup failed",
        )

    monkeypatch.setattr(manager, "create_backup", fail_backup)
    with pytest.raises(RecoveryError) as raised:
        RestoreCoordinator(manager, migrator=migrator).migrate_active()

    assert raised.value.code == DataControlErrorCode.BACKUP_INTEGRITY_FAILED
    assert hashlib.sha256(database.read_bytes()).hexdigest() == before
    assert migrator.revision(database) == OLDER_SUPPORTED_REVISION


def test_cli_active_upgrade_returns_transaction_for_readiness_finalize(
    tmp_path: Path,
) -> None:
    database = tmp_path / "askora.db"
    migrator = StagedSchemaMigrator()
    migrator._run_alembic(database, "upgrade", OLDER_SUPPORTED_REVISION)
    (tmp_path / "documents").mkdir()
    (tmp_path / "local-secrets.json").write_text(
        json.dumps({"jwtSecret": "cli-session-secret", "kekSecret": "stable-kek"}),
        encoding="utf-8",
    )
    environment = {RECOVERY_KEY_ENV: generate_recovery_key()}

    migrate_code, migrated = run(
        ["--user-data-dir", str(tmp_path), "migrate-active"],
        environ=environment,
    )

    assert migrate_code == 0
    assert migrated["result"]["required"] is True
    transaction_id = migrated["result"]["recovery_report"]["transaction_id"]
    finalize_code, finalized = run(
        [
            "--user-data-dir",
            str(tmp_path),
            "finalize-restore",
            "--transaction-id",
            transaction_id,
        ],
        environ=environment,
    )
    assert finalize_code == 0
    assert finalized["result"]["status"] == "COMPLETED"
    assert migrator.revision(database) == migrator.current_head


def test_active_upgrade_rejects_corrupt_database_before_creating_recovery_point(
    tmp_path: Path,
) -> None:
    database = tmp_path / "askora.db"
    database.write_bytes(b"not-a-sqlite-database")
    (tmp_path / "documents").mkdir()
    (tmp_path / "local-secrets.json").write_text(
        json.dumps({"jwtSecret": "corrupt-db-session", "kekSecret": "stable-kek"}),
        encoding="utf-8",
    )
    before = hashlib.sha256(database.read_bytes()).hexdigest()
    environment = {RECOVERY_KEY_ENV: generate_recovery_key()}

    code, payload = run(
        ["--user-data-dir", str(tmp_path), "migrate-active"],
        environ=environment,
    )

    assert code == 2
    assert payload["error"]["code"] == DataControlErrorCode.BACKUP_INTEGRITY_FAILED
    assert hashlib.sha256(database.read_bytes()).hexdigest() == before
    assert not (tmp_path / "recovery" / "catalog.json").exists()
    assert not (tmp_path / "recovery" / "backups").exists()

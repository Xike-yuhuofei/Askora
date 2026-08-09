from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from app.contracts.data_control import (
    BackupReason,
    DataControlErrorCode,
    ProtectionState,
    RecoveryPointStatus,
)
from app.data_control.cli import RECOVERY_KEY_ENV, run
from app.data_control.crypto import generate_recovery_key, parse_recovery_key
from app.data_control.recovery import RecoveryError, RecoveryManager


@pytest.fixture
def desktop_data(tmp_path: Path) -> Path:
    database = tmp_path / "askora.db"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE alembic_version (version_num TEXT PRIMARY KEY)")
        connection.execute("INSERT INTO alembic_version VALUES ('revision-1')")
        connection.execute("CREATE TABLE notes (id INTEGER PRIMARY KEY, body TEXT NOT NULL)")
        connection.execute("INSERT INTO notes (body) VALUES ('canonical fact')")
    documents = tmp_path / "documents"
    documents.mkdir()
    (documents / "source.epub").write_bytes(b"PK\x03\x04 source document")
    (tmp_path / "local-secrets.json").write_text(
        json.dumps({"jwtSecret": "must-not-be-backed-up", "kekSecret": "keep-kek"}),
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture
def manager(desktop_data: Path) -> RecoveryManager:
    return RecoveryManager(
        desktop_data,
        parse_recovery_key(generate_recovery_key()),
        app_version="test",
    )


def test_backup_is_published_only_after_full_verification(
    manager: RecoveryManager,
) -> None:
    before = manager.status()

    point = manager.create_backup(BackupReason.MANUAL)
    verification = manager.verify_backup(manager.recovery_dir / point.relative_path)
    after = manager.status()

    assert before.protection_state == ProtectionState.NOT_PROTECTED
    assert point.status == RecoveryPointStatus.VERIFIED
    assert point.verified_at is not None
    assert verification.backup_id == point.backup_id
    assert verification.sqlite_quick_check == "ok"
    assert verification.foreign_key_violations == 0
    assert verification.schema_revision == "revision-1"
    assert after.protection_state == ProtectionState.READY
    assert after.last_verified == point
    catalog = json.loads(manager.catalog_path.read_text(encoding="utf-8"))
    assert catalog["points"][0]["status"] == "VERIFIED"
    assert "jwtSecret" not in manager.catalog_path.read_text(encoding="utf-8")
    assert manager.catalog_path.stat().st_mode & 0o777 == 0o600


def test_tampered_backup_fails_verification(
    manager: RecoveryManager,
) -> None:
    point = manager.create_backup(BackupReason.MANUAL)
    backup_path = manager.recovery_dir / point.relative_path
    content = bytearray(backup_path.read_bytes())
    content[len(content) // 2] ^= 0x01
    backup_path.write_bytes(content)

    with pytest.raises(RecoveryError) as raised:
        manager.verify_backup(backup_path)

    assert raised.value.code == DataControlErrorCode.BACKUP_INTEGRITY_FAILED


def test_wrong_key_fails_verification(
    manager: RecoveryManager,
    desktop_data: Path,
) -> None:
    point = manager.create_backup(BackupReason.MANUAL)
    other_manager = RecoveryManager(
        desktop_data,
        parse_recovery_key(generate_recovery_key()),
        app_version="test",
    )

    with pytest.raises(RecoveryError) as raised:
        other_manager.verify_backup(manager.recovery_dir / point.relative_path)

    assert raised.value.code == DataControlErrorCode.BACKUP_INTEGRITY_FAILED


def test_document_symlink_is_rejected_without_partial_catalog(
    manager: RecoveryManager,
    desktop_data: Path,
) -> None:
    outside = desktop_data / "outside.txt"
    outside.write_text("not managed", encoding="utf-8")
    (desktop_data / "documents" / "escape").symlink_to(outside)

    with pytest.raises(RecoveryError) as raised:
        manager.create_backup(BackupReason.MANUAL)

    assert raised.value.code == DataControlErrorCode.BACKUP_INTEGRITY_FAILED
    assert not manager.catalog_path.exists()
    assert list(manager.backups_dir.glob("*")) == []


def test_source_size_limit_fails_closed(desktop_data: Path) -> None:
    manager = RecoveryManager(
        desktop_data,
        parse_recovery_key(generate_recovery_key()),
        app_version="test",
        max_single_file_bytes=8,
    )

    with pytest.raises(RecoveryError) as raised:
        manager.create_backup(BackupReason.MANUAL)

    assert raised.value.code == DataControlErrorCode.BACKUP_LIMIT_EXCEEDED
    assert not manager.catalog_path.exists()


def test_exclusive_maintenance_lock_rejects_concurrency(manager: RecoveryManager) -> None:
    with manager.exclusive_lock():
        with pytest.raises(RecoveryError) as raised:
            with manager.exclusive_lock():
                pass

    assert raised.value.code == DataControlErrorCode.MAINTENANCE_BUSY


def test_cli_does_not_accept_missing_key(tmp_path: Path) -> None:
    code, payload = run(
        ["--user-data-dir", str(tmp_path), "status"],
        environ={},
    )

    assert code == 2
    assert payload["error"]["code"] == DataControlErrorCode.RECOVERY_KEY_REQUIRED


def test_cli_backup_then_status_returns_json_safe_contract(desktop_data: Path) -> None:
    environment = {RECOVERY_KEY_ENV: generate_recovery_key()}

    backup_code, backup = run(
        [
            "--user-data-dir",
            str(desktop_data),
            "backup",
            "--reason",
            "PRE_MIGRATION",
        ],
        environ=environment,
    )
    status_code, status = run(
        ["--user-data-dir", str(desktop_data), "status"],
        environ=environment,
    )

    assert backup_code == 0
    assert backup["result"]["status"] == "VERIFIED"
    assert backup["result"]["reason"] == "PRE_MIGRATION"
    assert status_code == 0
    assert status["result"]["protection_state"] == "READY"
    json.dumps(backup)
    json.dumps(status)

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest
from sqlalchemy import create_engine

from app import models  # noqa: F401
from app.contracts.data_control import BackupReason, DataControlErrorCode
from app.core.database import Base
from app.data_control.crypto import generate_recovery_key, parse_recovery_key
from app.data_control.recovery import RecoveryError, RecoveryManager
from app.data_control.restore import RestoreCoordinator


def _write_desktop_secrets(root: Path) -> None:
    (root / "local-secrets.json").write_text(
        json.dumps({"jwtSecret": "original-jwt", "kekSecret": "stable-kek"}),
        encoding="utf-8",
    )
    (root / "documents").mkdir(exist_ok=True)


def _current_desktop(root: Path) -> None:
    engine = create_engine(f"sqlite:///{root / 'askora.db'}")
    Base.metadata.create_all(engine)
    engine.dispose()
    _write_desktop_secrets(root)


def _manager(root: Path) -> RecoveryManager:
    return RecoveryManager(
        root,
        parse_recovery_key(generate_recovery_key()),
        app_version="restore-test",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_current_unversioned_create_all_database_restores_and_is_stamped(
    tmp_path: Path,
) -> None:
    _current_desktop(tmp_path)
    manager = _manager(tmp_path)
    point = manager.create_backup(BackupReason.MANUAL)
    backup_path = manager.recovery_dir / point.relative_path
    original_kek = json.loads(manager.local_secrets_path.read_text(encoding="utf-8"))["kekSecret"]
    with sqlite3.connect(manager.database_path) as connection:
        connection.execute("DROP TABLE assessment_items")

    coordinator = RestoreCoordinator(manager)
    awaiting = coordinator.restore(backup_path)

    assert awaiting.status == "AWAITING_READINESS"
    assert awaiting.schema_before is None
    assert awaiting.schema_after == coordinator.migrator.current_head
    assert coordinator.journal_path.is_file()
    restored_secrets = json.loads(manager.local_secrets_path.read_text(encoding="utf-8"))
    assert restored_secrets["kekSecret"] == original_kek
    assert restored_secrets["jwtSecret"] != "original-jwt"
    with sqlite3.connect(manager.database_path) as connection:
        assert connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='assessment_items'"
        ).fetchone()

    completed = coordinator.finalize(awaiting.transaction_id)

    assert completed.status == "COMPLETED"
    assert completed.completed_at is not None
    assert not coordinator.journal_path.exists()


def test_future_revision_is_rejected_without_changing_active_bytes(tmp_path: Path) -> None:
    database = tmp_path / "askora.db"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE alembic_version (version_num TEXT PRIMARY KEY)")
        connection.execute("INSERT INTO alembic_version VALUES ('future-revision')")
        connection.execute("CREATE TABLE owner_fact (value TEXT NOT NULL)")
        connection.execute("INSERT INTO owner_fact VALUES ('must-survive')")
    _write_desktop_secrets(tmp_path)
    manager = _manager(tmp_path)
    point = manager.create_backup(BackupReason.MANUAL)
    backup_path = manager.recovery_dir / point.relative_path
    before_hash = _sha256(database)

    with pytest.raises(RecoveryError) as raised:
        RestoreCoordinator(manager).restore(backup_path)

    assert raised.value.code == DataControlErrorCode.RESTORE_SCHEMA_UNSUPPORTED
    assert _sha256(database) == before_hash
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT value FROM owner_fact").fetchone() == ("must-survive",)

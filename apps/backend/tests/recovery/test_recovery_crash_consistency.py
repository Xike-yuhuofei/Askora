from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

import pytest

from app.contracts.data_control import BackupReason, DataControlErrorCode
from app.data_control.crypto import generate_recovery_key, parse_recovery_key
from app.data_control.recovery import RecoveryError, RecoveryManager
from app.data_control.restore import RestoreCoordinator


class PassThroughMigrator:
    current_head = "test-revision"

    def prepare(self, _database_path: Path) -> tuple[str, str]:
        return self.current_head, self.current_head


def test_activation_failure_restores_exact_pre_restore_dataset(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = tmp_path / "askora.db"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE alembic_version (version_num TEXT PRIMARY KEY)")
        connection.execute("INSERT INTO alembic_version VALUES ('test-revision')")
        connection.execute("CREATE TABLE owner_fact (value TEXT NOT NULL)")
        connection.execute("INSERT INTO owner_fact VALUES ('package-version')")
    documents = tmp_path / "documents"
    documents.mkdir()
    document = documents / "state.txt"
    document.write_text("package-version", encoding="utf-8")
    secrets_path = tmp_path / "local-secrets.json"
    secrets_path.write_text(
        json.dumps({"jwtSecret": "package-jwt", "kekSecret": "package-kek"}),
        encoding="utf-8",
    )
    manager = RecoveryManager(
        tmp_path,
        parse_recovery_key(generate_recovery_key()),
        app_version="crash-test",
    )
    point = manager.create_backup(BackupReason.MANUAL)

    with sqlite3.connect(database) as connection:
        connection.execute("UPDATE owner_fact SET value = 'current-before-restore'")
    document.write_text("current-before-restore", encoding="utf-8")
    secrets_path.write_text(
        json.dumps({"jwtSecret": "current-jwt", "kekSecret": "current-kek"}),
        encoding="utf-8",
    )
    coordinator = RestoreCoordinator(manager, migrator=PassThroughMigrator())  # type: ignore[arg-type]
    real_replace = os.replace
    failure_injected = False

    def fail_first_new_database_activation(source: str | Path, target: str | Path) -> None:
        nonlocal failure_injected
        source_path = Path(source)
        if (
            not failure_injected
            and "restore-staging" in source_path.parts
            and source_path.name == "askora.db"
            and Path(target) == database
        ):
            failure_injected = True
            raise OSError("injected activation failure")
        real_replace(source, target)

    monkeypatch.setattr("app.data_control.restore.os.replace", fail_first_new_database_activation)

    with pytest.raises(RecoveryError) as raised:
        coordinator.restore(manager.recovery_dir / point.relative_path)

    assert raised.value.code == DataControlErrorCode.RESTORE_FAILED_ROLLED_BACK
    assert failure_injected
    assert not coordinator.journal_path.exists()
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT value FROM owner_fact").fetchone() == (
            "current-before-restore",
        )
    assert document.read_text(encoding="utf-8") == "current-before-restore"
    assert json.loads(secrets_path.read_text(encoding="utf-8")) == {
        "jwtSecret": "current-jwt",
        "kekSecret": "current-kek",
    }

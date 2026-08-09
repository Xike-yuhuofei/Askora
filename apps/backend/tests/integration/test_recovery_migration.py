from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.contracts.data_control import BackupReason
from app.data_control.crypto import generate_recovery_key, parse_recovery_key
from app.data_control.migration import StagedSchemaMigrator
from app.data_control.recovery import RecoveryManager
from app.data_control.restore import RestoreCoordinator

OLDER_SUPPORTED_REVISION = "e23a91b807d1"


def test_older_supported_revision_forward_migrates_only_in_staging(tmp_path: Path) -> None:
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
            for row in connection.execute("PRAGMA table_info(decision_trace_inputs)").fetchall()
        }
    assert columns["entity_version"] == "VARCHAR(255)"
    assert coordinator.finalize(awaiting.transaction_id).status == "COMPLETED"

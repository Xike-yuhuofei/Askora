from __future__ import annotations

import json
import shutil
import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest

from app.contracts.data_control import (
    BackupReason,
    DataControlErrorCode,
    ErasureScope,
    ErasureWorkflowStatus,
    ProtectionState,
    RecoveryPointStatus,
)
from app.data_control.crypto import generate_recovery_key, parse_recovery_key
from app.data_control.recovery import RecoveryError, RecoveryManager
from app.data_control.restore import RestoreCoordinator


def _prepare_user_data(root: Path) -> None:
    root.mkdir()
    (root / "documents").mkdir()
    (root / "local-secrets.json").write_text(
        json.dumps({"jwtSecret": "j" * 48, "kekSecret": "k" * 48}),
        encoding="utf-8",
    )
    with sqlite3.connect(root / "askora.db") as connection:
        connection.executescript("""
            CREATE TABLE users (id TEXT PRIMARY KEY, private_value TEXT);
            INSERT INTO users VALUES ('user-current', 'MUST-NOT-RESURRECT');
            CREATE TABLE data_erasure_checkpoints (
                id INTEGER PRIMARY KEY, checkpoint INTEGER NOT NULL,
                receipt_id TEXT, updated_at TEXT
            );
            INSERT INTO data_erasure_checkpoints VALUES (1, 0, NULL, CURRENT_TIMESTAMP);
            CREATE TABLE data_erasure_workflows (
                workflow_id TEXT PRIMARY KEY, status TEXT NOT NULL,
                checkpoint INTEGER, report JSON NOT NULL, updated_at TEXT
            );
            """)


def test_erasure_checkpoint_rejects_old_copy_and_finalizes_post_erasure_baseline(
    tmp_path: Path,
) -> None:
    user_data = tmp_path / "user-data"
    _prepare_user_data(user_data)
    manager = RecoveryManager(
        user_data,
        parse_recovery_key(generate_recovery_key()),
        app_version="erasure-recovery-test",
    )
    old_point = manager.create_backup(BackupReason.MANUAL)
    old_managed_path = manager.recovery_dir / old_point.relative_path
    old_external_copy = tmp_path / "old-external.askora-recovery"
    shutil.copyfile(old_managed_path, old_external_copy)
    workflow_id = uuid4()
    marker = manager.recovery_dir / "erasure-pending.json"
    marker.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "workflow_id": str(workflow_id),
                "checkpoint": 1,
                "status": ErasureWorkflowStatus.AWAITING_RECOVERY_BASELINE.value,
            }
        ),
        encoding="utf-8",
    )
    with sqlite3.connect(manager.database_path) as connection:
        connection.execute("DELETE FROM users WHERE id = 'user-current'")
        connection.execute("UPDATE data_erasure_checkpoints SET checkpoint = 1 WHERE id = 1")
        connection.execute(
            "INSERT INTO data_erasure_workflows "
            "(workflow_id, status, checkpoint, report, updated_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
            (
                str(workflow_id),
                ErasureWorkflowStatus.AWAITING_RECOVERY_BASELINE.value,
                1,
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "workflow_id": str(workflow_id),
                        "scope": ErasureScope.LEARNING_RECORDS.value,
                        "target_ref_hash": "a" * 64,
                        "status": ErasureWorkflowStatus.AWAITING_RECOVERY_BASELINE.value,
                        "checkpoint": 1,
                        "owner_results": [],
                        "started_at": "2026-08-09T00:00:00Z",
                        "reason_codes": ["DATA_POST_ERASURE_BASELINE_REQUIRED"],
                    }
                ),
            ),
        )

    pending_status = manager.status()
    assert pending_status.protection_state == ProtectionState.PARTIAL
    assert pending_status.last_verified is None

    with pytest.raises(RecoveryError) as stale_restore:
        RestoreCoordinator(manager).restore(old_external_copy)
    assert stale_restore.value.code == DataControlErrorCode.RESTORE_RECONCILIATION_FAILED
    with sqlite3.connect(manager.database_path) as connection:
        assert connection.execute("SELECT count(*) FROM users").fetchone() == (0,)

    result = manager.finalize_erasure(workflow_id=workflow_id, checkpoint=1)

    assert result.post_erasure_point.reason == BackupReason.POST_ERASURE
    assert result.post_erasure_point.status == RecoveryPointStatus.VERIFIED
    assert result.checkpoint == 1
    assert result.purged_points >= 1
    assert not old_managed_path.exists()
    assert not marker.exists()
    catalog = manager._load_catalog()
    assert catalog.erasure_checkpoint == 1
    assert all(
        point.status != RecoveryPointStatus.VERIFIED or point.erasure_checkpoint >= 1
        for point in catalog.points
    )
    with sqlite3.connect(manager.database_path) as connection:
        status, raw_report = connection.execute(
            "SELECT status, report FROM data_erasure_workflows WHERE workflow_id = ?",
            (str(workflow_id),),
        ).fetchone()
    assert status == ErasureWorkflowStatus.COMPLETED.value
    assert json.loads(raw_report)["post_erasure_backup_id"] == str(
        result.post_erasure_point.backup_id
    )


def test_interrupted_pre_checkpoint_erasure_rolls_back_marker_and_keeps_data(
    tmp_path: Path,
) -> None:
    user_data = tmp_path / "interrupted-user-data"
    _prepare_user_data(user_data)
    manager = RecoveryManager(
        user_data,
        parse_recovery_key(generate_recovery_key()),
        app_version="erasure-interruption-test",
    )
    workflow_id = uuid4()
    marker = manager.recovery_dir / "erasure-pending.json"
    marker.parent.mkdir(parents=True)
    marker.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "workflow_id": str(workflow_id),
                "checkpoint": None,
                "status": ErasureWorkflowStatus.RUNNING.value,
            }
        ),
        encoding="utf-8",
    )
    journal_dir = manager.recovery_dir / "erasure-files" / str(workflow_id)
    journal_dir.mkdir(parents=True)
    (journal_dir / "journal.json").write_text(
        json.dumps({"schema_version": "1.0", "relative_paths": []}),
        encoding="utf-8",
    )
    with sqlite3.connect(manager.database_path) as connection:
        connection.execute(
            "INSERT INTO data_erasure_workflows "
            "(workflow_id, status, checkpoint, report, updated_at) "
            "VALUES (?, ?, NULL, '{}', CURRENT_TIMESTAMP)",
            (str(workflow_id), ErasureWorkflowStatus.RUNNING.value),
        )

    result = manager.recover_interrupted_erasure()

    assert result == {"action": "ROLLED_BACK_PRE_CHECKPOINT_ERASURE"}
    assert not marker.exists()
    assert not journal_dir.exists()
    with sqlite3.connect(manager.database_path) as connection:
        assert connection.execute("SELECT count(*) FROM users").fetchone() == (1,)
        assert connection.execute(
            "SELECT status FROM data_erasure_workflows WHERE workflow_id = ?",
            (str(workflow_id),),
        ).fetchone() == (ErasureWorkflowStatus.FAILED_RETRYABLE.value,)

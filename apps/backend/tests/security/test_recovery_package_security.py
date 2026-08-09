from __future__ import annotations

import hashlib
import json
import sqlite3
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from app.contracts.data_control import (
    BackupReason,
    DataControlErrorCode,
    RecoveryManifestFileV1,
    RecoveryManifestTotalsV1,
    RecoveryManifestV1,
)
from app.data_control.crypto import (
    decrypt_file,
    encrypt_file,
    generate_recovery_key,
    parse_recovery_key,
)
from app.data_control.recovery import RecoveryError, RecoveryManager


@pytest.fixture
def secured_manager(tmp_path: Path) -> RecoveryManager:
    with sqlite3.connect(tmp_path / "askora.db") as connection:
        connection.execute("CREATE TABLE alembic_version (version_num TEXT PRIMARY KEY)")
        connection.execute("INSERT INTO alembic_version VALUES ('secure-revision')")
    (tmp_path / "documents").mkdir()
    (tmp_path / "documents" / "source.txt").write_text("owner content", encoding="utf-8")
    (tmp_path / "local-secrets.json").write_text(
        json.dumps(
            {
                "jwtSecret": "forbidden-jwt-material",
                "kekSecret": "required-kek-material",
                "providerKey": "forbidden-provider-key",
            }
        ),
        encoding="utf-8",
    )
    return RecoveryManager(
        tmp_path,
        parse_recovery_key(generate_recovery_key()),
        app_version="security-test",
    )


def test_recovery_payload_contains_kek_but_excludes_runtime_secrets(
    secured_manager: RecoveryManager,
    tmp_path: Path,
) -> None:
    point = secured_manager.create_backup(BackupReason.MANUAL)
    plaintext_archive = tmp_path / "inspected.zip"
    decrypt_file(
        secured_manager.recovery_dir / point.relative_path,
        plaintext_archive,
        secured_manager.recovery_key,
        max_plaintext_bytes=1024**2,
    )

    with zipfile.ZipFile(plaintext_archive) as package:
        recovery_secrets = json.loads(package.read("secrets/recovery-secrets.json"))
        combined_payload = b"".join(package.read(name) for name in package.namelist())

    assert recovery_secrets == {
        "schema_version": "1.0",
        "kekSecret": "required-kek-material",
    }
    assert b"forbidden-jwt-material" not in combined_payload
    assert b"forbidden-provider-key" not in combined_payload


def test_archive_traversal_is_rejected_before_extraction(
    secured_manager: RecoveryManager,
    tmp_path: Path,
) -> None:
    plaintext_archive = tmp_path / "malicious.zip"
    escape_content = b"escape"
    database_content = (secured_manager.user_data_dir / "askora.db").read_bytes()
    database_sha = hashlib.sha256(database_content).hexdigest()
    escape_sha = hashlib.sha256(escape_content).hexdigest()
    manifest = RecoveryManifestV1(
        backup_id=uuid4(),
        backup_set_id=uuid4(),
        reason=BackupReason.MANUAL,
        created_at=datetime.now(UTC),
        app_version="security-test",
        database_schema_revision="secure-revision",
        database_sha256=database_sha,
        erasure_checkpoint=0,
        files=(
            RecoveryManifestFileV1(
                relative_path="database/askora.db",
                size_bytes=len(database_content),
                sha256=database_sha,
            ),
            RecoveryManifestFileV1(
                relative_path="../escape.txt",
                size_bytes=len(escape_content),
                sha256=escape_sha,
            ),
        ),
        totals=RecoveryManifestTotalsV1(
            file_count=2,
            size_bytes=len(database_content) + len(escape_content),
        ),
    )
    with zipfile.ZipFile(plaintext_archive, "x") as package:
        package.writestr("database/askora.db", database_content)
        package.writestr("../escape.txt", escape_content)
        package.writestr("manifest.json", manifest.model_dump_json())
    encrypted = tmp_path / "malicious.askora-recovery"
    encrypt_file(plaintext_archive, encrypted, secured_manager.recovery_key)

    with pytest.raises(RecoveryError) as raised:
        secured_manager.verify_backup(encrypted)

    assert raised.value.code == DataControlErrorCode.BACKUP_INTEGRITY_FAILED
    assert not (tmp_path.parent / "escape.txt").exists()

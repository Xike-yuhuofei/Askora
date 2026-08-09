from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.contracts.data_control import (
    BackupReason,
    RecoveryManifestFileV1,
    RecoveryManifestTotalsV1,
    RecoveryManifestV1,
)


def test_recovery_manifest_is_strict_and_versioned() -> None:
    file = RecoveryManifestFileV1(
        relative_path="database/askora.db",
        size_bytes=10,
        sha256="a" * 64,
    )
    manifest = RecoveryManifestV1(
        backup_id=uuid4(),
        backup_set_id=uuid4(),
        reason=BackupReason.PRE_MIGRATION,
        created_at=datetime.now(UTC),
        app_version="0.1.0",
        database_schema_revision="revision-1",
        database_sha256=file.sha256,
        erasure_checkpoint=0,
        files=(file,),
        totals=RecoveryManifestTotalsV1(file_count=1, size_bytes=10),
    )

    assert manifest.format == "askora-recovery"
    assert manifest.schema_version == "1.0"
    assert manifest.reason == BackupReason.PRE_MIGRATION
    with pytest.raises(ValidationError):
        RecoveryManifestV1.model_validate({**manifest.model_dump(), "schema_version": "2.0"})


def test_recovery_contract_rejects_naive_datetime() -> None:
    with pytest.raises(ValidationError, match="timezone"):
        RecoveryManifestV1(
            backup_id=uuid4(),
            backup_set_id=uuid4(),
            reason=BackupReason.MANUAL,
            created_at=datetime.now(),
            app_version="0.1.0",
            database_sha256="a" * 64,
            erasure_checkpoint=0,
            files=(
                RecoveryManifestFileV1(
                    relative_path="database/askora.db",
                    size_bytes=1,
                    sha256="a" * 64,
                ),
            ),
            totals=RecoveryManifestTotalsV1(file_count=1, size_bytes=1),
        )

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.contracts.data_control import (
    ActiveMigrationResultV1,
    BackupReason,
    ErasureOwnerImpactV1,
    ErasurePreviewV1,
    ErasureReceiptV1,
    ErasureReportV1,
    ErasureScope,
    ErasureWorkflowStatus,
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


def test_active_migration_result_is_strict_and_versioned() -> None:
    result = ActiveMigrationResultV1(
        required=False,
        schema_before="current-head",
        schema_after="current-head",
    )

    assert result.schema_version == "1.0"
    assert result.pre_migration_point is None
    assert result.recovery_report is None
    with pytest.raises(ValidationError):
        ActiveMigrationResultV1.model_validate({**result.model_dump(), "secret": "forbidden"})


def test_erasure_preview_report_and_receipt_are_strict_and_content_free() -> None:
    now = datetime.now(UTC)
    preview = ErasurePreviewV1(
        preview_id=uuid4(),
        user_ref="u" * 24,
        scope=ErasureScope.DOCUMENT,
        target_ref="document-1",
        impacts=(
            ErasureOwnerImpactV1(
                owner_system="SYS01",
                estimated_records=3,
                actions=("DELETE_DOCUMENT_FACTS",),
            ),
        ),
        backup_impact="旧恢复点将失效并被清理；随后创建删除后基线。",
        irreversible=True,
        confirmation_phrase="永久删除 document-1",
        expires_at=now,
        confirmation_token="t" * 48,
    )
    report = ErasureReportV1(
        workflow_id=uuid4(),
        scope=preview.scope,
        target_ref_hash="a" * 64,
        status=ErasureWorkflowStatus.AWAITING_RECOVERY_BASELINE,
        checkpoint=1,
        owner_results=(),
        started_at=now,
        reason_codes=("DATA_ERASURE_DATABASE_COMMITTED",),
    )
    receipt = ErasureReceiptV1(
        receipt_id=uuid4(),
        workflow_id=report.workflow_id,
        user_ref=preview.user_ref,
        scope=preview.scope,
        target_ref_hash=report.target_ref_hash,
        checkpoint=1,
        result_digest="b" * 64,
        completed_at=now,
    )

    assert preview.schema_version == "1.0"
    assert report.status == ErasureWorkflowStatus.AWAITING_RECOVERY_BASELINE
    assert "content" not in receipt.model_dump()
    with pytest.raises(ValidationError):
        ErasureReceiptV1.model_validate({**receipt.model_dump(), "checkpoint": 0})

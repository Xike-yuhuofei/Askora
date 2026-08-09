"""P1-03 data-control public contracts (DATA-*)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal, Self
from uuid import UUID

from pydantic import Field, model_validator

from app.contracts.base import ContractModel


class BackupReason(str, Enum):
    MANUAL = "MANUAL"
    SCHEDULED = "SCHEDULED"
    PRE_MIGRATION = "PRE_MIGRATION"
    PRE_RESTORE = "PRE_RESTORE"
    POST_ERASURE = "POST_ERASURE"


class RecoveryPointStatus(str, Enum):
    CREATING = "CREATING"
    VERIFYING = "VERIFYING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    INVALIDATED = "INVALIDATED"
    PURGED = "PURGED"


class ProtectionState(str, Enum):
    NOT_PROTECTED = "NOT_PROTECTED"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"
    UNSUPPORTED = "UNSUPPORTED"


class ErasureScope(str, Enum):
    DOCUMENT = "DOCUMENT"
    LEARNING_RECORDS = "LEARNING_RECORDS"
    MODEL_EXECUTION = "MODEL_EXECUTION"
    ALL_PERSONAL_DATA = "ALL_PERSONAL_DATA"


class ErasureWorkflowStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    AWAITING_RECOVERY_BASELINE = "AWAITING_RECOVERY_BASELINE"
    COMPLETED = "COMPLETED"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"
    FAILED_TERMINAL = "FAILED_TERMINAL"
    PARTIAL = "PARTIAL"


class ExportScope(str, Enum):
    PROFILE = "PROFILE"
    DOCUMENTS = "DOCUMENTS"
    LEARNING_RECORDS = "LEARNING_RECORDS"
    MODEL_EXECUTION = "MODEL_EXECUTION"


class UserExportManifestFileV1(ContractModel):
    path: str = Field(min_length=1, max_length=1024)
    media_type: str = Field(min_length=1, max_length=200)
    size_bytes: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class UserExportManifestV1(ContractModel):
    format: Literal["askora-user-export"] = "askora-user-export"
    schema_version: Literal["1.0"] = "1.0"
    export_id: UUID
    created_at: datetime
    user_ref: str = Field(min_length=16, max_length=100)
    scopes: tuple[ExportScope, ...] = Field(min_length=1)
    includes_document_originals: bool = False
    files: tuple[UserExportManifestFileV1, ...] = Field(min_length=1)


class UserExportReadyV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    export_id: UUID
    created_at: datetime
    expires_at: datetime
    download_token: str = Field(min_length=32, max_length=200)
    file_count: int = Field(ge=1)
    size_bytes: int = Field(ge=0)


class ErasureOwnerImpactV1(ContractModel):
    owner_system: str = Field(min_length=1, max_length=50)
    estimated_records: int = Field(ge=0)
    actions: tuple[str, ...] = Field(min_length=1)


class ErasurePreviewV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    preview_id: UUID
    user_ref: str = Field(min_length=16, max_length=100)
    scope: ErasureScope
    target_ref: str | None = Field(default=None, min_length=1, max_length=255)
    impacts: tuple[ErasureOwnerImpactV1, ...] = Field(min_length=1)
    backup_impact: str = Field(min_length=1, max_length=500)
    irreversible: Literal[True] = True
    confirmation_phrase: str = Field(min_length=1, max_length=300)
    expires_at: datetime
    confirmation_token: str = Field(min_length=32, max_length=200)


class ErasureOwnerResultV1(ContractModel):
    owner_system: str = Field(min_length=1, max_length=50)
    status: Literal["COMPLETED", "FAILED_RETRYABLE", "FAILED_TERMINAL"]
    affected_records: int = Field(ge=0)
    reason_codes: tuple[str, ...] = ()


class ErasureReportV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    workflow_id: UUID
    scope: ErasureScope
    target_ref_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    status: ErasureWorkflowStatus
    checkpoint: int | None = Field(default=None, ge=1)
    owner_results: tuple[ErasureOwnerResultV1, ...]
    started_at: datetime
    completed_at: datetime | None = None
    receipt_id: UUID | None = None
    post_erasure_backup_id: UUID | None = None
    reason_codes: tuple[str, ...] = ()


class ErasureReceiptV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    receipt_id: UUID
    workflow_id: UUID
    user_ref: str = Field(min_length=16, max_length=100)
    scope: ErasureScope
    target_ref_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    checkpoint: int = Field(ge=1)
    result_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    completed_at: datetime


class PostErasureMaintenanceV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    workflow_id: UUID
    checkpoint: int = Field(ge=1)
    purged_points: int = Field(ge=0)
    post_erasure_point: RecoveryPointV1


class RecoveryManifestFileV1(ContractModel):
    relative_path: str = Field(min_length=1, max_length=1024)
    size_bytes: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class RecoveryManifestTotalsV1(ContractModel):
    file_count: int = Field(ge=1)
    size_bytes: int = Field(ge=0)


class RecoveryManifestV1(ContractModel):
    format: Literal["askora-recovery"] = "askora-recovery"
    schema_version: Literal["1.0"] = "1.0"
    backup_id: UUID
    backup_set_id: UUID
    reason: BackupReason
    created_at: datetime
    app_version: str = Field(min_length=1, max_length=100)
    database_kind: Literal["sqlite"] = "sqlite"
    database_schema_revision: str | None = Field(default=None, max_length=200)
    database_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    erasure_checkpoint: int = Field(ge=0)
    files: tuple[RecoveryManifestFileV1, ...] = Field(min_length=1)
    secrets_schema_version: Literal["1.0"] = "1.0"
    totals: RecoveryManifestTotalsV1


class RecoveryPointV1(ContractModel):
    backup_id: UUID
    backup_set_id: UUID
    reason: BackupReason
    status: RecoveryPointStatus
    created_at: datetime
    verified_at: datetime | None = None
    relative_path: str = Field(min_length=1, max_length=1024)
    size_bytes: int = Field(ge=0)
    schema_revision: str | None = None
    erasure_checkpoint: int = Field(ge=0)
    protected: bool = False
    reason_codes: tuple[str, ...] = ()


class RecoveryCatalogV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    backup_set_id: UUID
    erasure_checkpoint: int = Field(default=0, ge=0)
    points: tuple[RecoveryPointV1, ...] = ()
    updated_at: datetime


class RecoveryVerificationV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    backup_id: UUID
    status: Literal["VERIFIED"] = "VERIFIED"
    checked_at: datetime
    file_count: int = Field(ge=1)
    size_bytes: int = Field(ge=0)
    sqlite_quick_check: Literal["ok"] = "ok"
    foreign_key_violations: int = Field(ge=0)
    schema_revision: str | None = None
    reason_codes: tuple[str, ...] = ()


class RecoveryReportV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    report_id: UUID
    transaction_id: UUID
    backup_id: UUID
    rescue_backup_id: UUID
    status: Literal[
        "AWAITING_READINESS",
        "COMPLETED",
        "FAILED_ROLLED_BACK",
    ]
    schema_before: str | None = None
    schema_after: str | None = None
    file_count: int = Field(ge=1)
    size_bytes: int = Field(ge=0)
    document_refs_checked: int = Field(ge=0)
    projection_actions: tuple[str, ...] = ()
    erasure_checkpoint: int = Field(ge=0)
    started_at: datetime
    completed_at: datetime | None = None
    reason_codes: tuple[str, ...] = ()


class ActiveMigrationResultV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    required: bool
    schema_before: str | None = None
    schema_after: str
    pre_migration_point: RecoveryPointV1 | None = None
    recovery_report: RecoveryReportV1 | None = None

    @model_validator(mode="after")
    def validate_consistency(self) -> Self:
        has_evidence = self.pre_migration_point is not None and self.recovery_report is not None
        if self.required != has_evidence:
            raise ValueError("migration evidence must match required state")
        if not self.required and self.schema_before != self.schema_after:
            raise ValueError("no-op migration revisions must match")
        return self


class AutomaticBackupStatusV1(ContractModel):
    enabled: bool
    next_due_at: datetime | None = None
    last_error_code: str | None = None


class DataControlStatusV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    protection_state: ProtectionState
    supported_mode: Literal["PRIVATE_DESKTOP_SQLITE", "UNSUPPORTED"]
    last_verified: RecoveryPointV1 | None = None
    automatic_backup: AutomaticBackupStatusV1
    erasure_checkpoint: int = Field(ge=0)
    reason_codes: tuple[str, ...] = ()


class DataControlErrorCode(str, Enum):
    MODE_UNSUPPORTED = "DATA_MODE_UNSUPPORTED"
    MAINTENANCE_BUSY = "DATA_MAINTENANCE_BUSY"
    RECOVERY_KEY_REQUIRED = "DATA_RECOVERY_KEY_REQUIRED"
    RECOVERY_KEY_INVALID = "DATA_RECOVERY_KEY_INVALID"
    BACKUP_NOT_VERIFIED = "DATA_BACKUP_NOT_VERIFIED"
    BACKUP_INTEGRITY_FAILED = "DATA_BACKUP_INTEGRITY_FAILED"
    BACKUP_LIMIT_EXCEEDED = "DATA_BACKUP_LIMIT_EXCEEDED"
    RESTORE_SCHEMA_UNSUPPORTED = "DATA_RESTORE_SCHEMA_UNSUPPORTED"
    RESTORE_RECONCILIATION_FAILED = "DATA_RESTORE_RECONCILIATION_FAILED"
    RESTORE_FAILED_ROLLED_BACK = "DATA_RESTORE_FAILED_ROLLED_BACK"
    EXPORT_SCOPE_INVALID = "DATA_EXPORT_SCOPE_INVALID"
    EXPORT_EXPIRED = "DATA_EXPORT_EXPIRED"
    ERASURE_PREVIEW_EXPIRED = "DATA_ERASURE_PREVIEW_EXPIRED"
    ERASURE_CONFIRMATION_INVALID = "DATA_ERASURE_CONFIRMATION_INVALID"
    ERASURE_PARTIAL = "DATA_ERASURE_PARTIAL"

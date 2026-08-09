"""P1-03 data-control public contracts (DATA-*)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import Field

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


class ExportScope(str, Enum):
    PROFILE = "PROFILE"
    DOCUMENTS = "DOCUMENTS"
    LEARNING_RECORDS = "LEARNING_RECORDS"
    MODEL_EXECUTION = "MODEL_EXECUTION"


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

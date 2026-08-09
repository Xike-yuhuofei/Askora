"""P1-03 data-control public contracts (DATA-*)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.contracts.base import ContractModel


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


class DataControlErrorCode(str, Enum):
    MODE_UNSUPPORTED = "DATA_MODE_UNSUPPORTED"
    BACKUP_INTEGRITY_FAILED = "DATA_BACKUP_INTEGRITY_FAILED"
    EXPORT_SCOPE_INVALID = "DATA_EXPORT_SCOPE_INVALID"
    EXPORT_EXPIRED = "DATA_EXPORT_EXPIRED"
    ERASURE_PREVIEW_EXPIRED = "DATA_ERASURE_PREVIEW_EXPIRED"
    ERASURE_CONFIRMATION_INVALID = "DATA_ERASURE_CONFIRMATION_INVALID"
    ERASURE_PARTIAL = "DATA_ERASURE_PARTIAL"

"""Strict public v1 contracts for account deletion and privacy erasure."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ACCOUNT_DELETION_POLICY_VERSION: Literal["account-deletion-v1"] = "account-deletion-v1"
ACCOUNT_DELETION_CONFIRMATION_PHRASE: Literal["永久删除我的 Askora 账号"] = (
    "永久删除我的 Askora 账号"
)


class PrivacyContract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class DeletionLifecycle(str, Enum):
    ACTIVE = "active"
    DELETION_PENDING = "deletion_pending"
    PURGING = "purging"
    DELETION_BLOCKED = "deletion_blocked"
    DELETED = "deleted"


class PrivacyBlockingIssueV1(PrivacyContract):
    code: str = Field(min_length=1, max_length=100)
    owner: str | None = Field(default=None, max_length=20)
    record_type: str | None = Field(default=None, max_length=100)
    record_id: str | None = Field(default=None, max_length=255)


class AccountDeletionPreviewV1(PrivacyContract):
    preview_id: UUID = Field(strict=False)
    schema_version: Literal["1.0"] = "1.0"
    policy_version: Literal["account-deletion-v1"] = ACCOUNT_DELETION_POLICY_VERSION
    generated_at: datetime
    expires_at: datetime
    counts_by_owner: dict[str, int]
    file_count: int = Field(ge=0)
    pending_task_count: int = Field(ge=0)
    projection_count: int = Field(ge=0)
    blocking_issues: tuple[PrivacyBlockingIssueV1, ...] = ()
    explicit_exclusions: tuple[str, ...] = ()
    recovery_boundary: str = Field(min_length=1, max_length=500)
    preview_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")


class AccountDeletionRequestV1(PrivacyContract):
    schema_version: Literal["1.0"] = "1.0"
    current_password: str = Field(min_length=1, max_length=128)
    confirmation_phrase: Literal["永久删除我的 Askora 账号"]
    preview_id: UUID = Field(strict=False)
    preview_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    policy_version: Literal["account-deletion-v1"] = ACCOUNT_DELETION_POLICY_VERSION
    idempotency_key: str = Field(min_length=16, max_length=128)


class AccountDeletionCancelV1(PrivacyContract):
    schema_version: Literal["1.0"] = "1.0"
    request_id: UUID = Field(strict=False)
    idempotency_key: str = Field(min_length=16, max_length=128)


class AccountDeletionRetryV1(PrivacyContract):
    schema_version: Literal["1.0"] = "1.0"
    request_id: UUID = Field(strict=False)
    idempotency_key: str = Field(min_length=16, max_length=128)


class AccountDeletionStatusV1(PrivacyContract):
    schema_version: Literal["1.0"] = "1.0"
    request_id: UUID = Field(strict=False)
    lifecycle: DeletionLifecycle
    requested_at: datetime
    purge_due_at: datetime
    cancellable: bool
    current_step: str | None = Field(default=None, max_length=50)
    retry_count: int = Field(ge=0)
    blocking_issues: tuple[PrivacyBlockingIssueV1, ...] = ()
    completed_at: datetime | None = None


class AccountDeletionAcceptedV1(PrivacyContract):
    schema_version: Literal["1.0"] = "1.0"
    status: AccountDeletionStatusV1
    deletion_control_token: str = Field(min_length=32)


class AccountDeletionCancelResultV1(PrivacyContract):
    schema_version: Literal["1.0"] = "1.0"
    cancelled: bool
    replayed: bool
    status: AccountDeletionStatusV1


class OwnerErasureReceiptV1(PrivacyContract):
    schema_version: Literal["1.0"] = "1.0"
    owner: str
    requested_count: int = Field(ge=0)
    deleted_count: int = Field(ge=0)
    missing_count: int = Field(ge=0)
    error_count: int = Field(ge=0)
    manifest_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    receipt_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

"""EXEC036 / IDP-041..044 strict account-deletion contract tests."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.contracts.privacy import (
    ACCOUNT_DELETION_CONFIRMATION_PHRASE,
    ACCOUNT_DELETION_POLICY_VERSION,
    AccountDeletionCancelV1,
    AccountDeletionPreviewV1,
    AccountDeletionRequestV1,
    AccountDeletionStatusV1,
    DeletionLifecycle,
)


def _preview_payload() -> dict:
    generated_at = datetime(2026, 8, 9, 9, 0, tzinfo=timezone.utc)
    return {
        "preview_id": uuid4(),
        "schema_version": "1.0",
        "policy_version": ACCOUNT_DELETION_POLICY_VERSION,
        "generated_at": generated_at,
        "expires_at": generated_at.replace(hour=10),
        "counts_by_owner": {"SYS01": 2, "SYS08": 3},
        "file_count": 1,
        "pending_task_count": 1,
        "projection_count": 0,
        "blocking_issues": (),
        "explicit_exclusions": ("global_policy_bundle",),
        "recovery_boundary": "普通数据库快照之外的 restore barrier 仍会阻止旧账号恢复",
        "preview_digest": "sha256:" + "a" * 64,
    }


def test_deletion_preview_is_strict_versioned_and_frozen() -> None:
    preview = AccountDeletionPreviewV1.model_validate(_preview_payload())
    assert preview.schema_version == "1.0"
    assert preview.policy_version == "account-deletion-v1"
    assert preview.counts_by_owner == {"SYS01": 2, "SYS08": 3}

    with pytest.raises(ValidationError):
        AccountDeletionPreviewV1.model_validate({**_preview_payload(), "unexpected": True})
    with pytest.raises(ValidationError):
        AccountDeletionPreviewV1.model_validate({**_preview_payload(), "schema_version": "2.0"})
    with pytest.raises(ValidationError):
        preview.counts_by_owner = {"SYS01": 9}


def test_delete_account_requires_exact_confirmation_and_pinned_preview() -> None:
    preview = AccountDeletionPreviewV1.model_validate(_preview_payload())
    command = AccountDeletionRequestV1(
        current_password="current-password",
        confirmation_phrase=ACCOUNT_DELETION_CONFIRMATION_PHRASE,
        preview_id=preview.preview_id,
        preview_digest=preview.preview_digest,
        policy_version=preview.policy_version,
        idempotency_key="delete-account-command-0001",
    )
    assert command.confirmation_phrase == "永久删除我的 Askora 账号"

    with pytest.raises(ValidationError):
        AccountDeletionRequestV1.model_validate(
            {**command.model_dump(), "confirmation_phrase": "永久删除我的账号"}
        )
    with pytest.raises(ValidationError):
        AccountDeletionRequestV1.model_validate(
            {**command.model_dump(), "policy_version": "account-deletion-v2"}
        )


def test_status_and_cancel_contract_preserve_deletion_control_boundary() -> None:
    now = datetime(2026, 8, 9, 9, 0, tzinfo=timezone.utc)
    request_id = uuid4()
    status = AccountDeletionStatusV1(
        request_id=request_id,
        lifecycle=DeletionLifecycle.DELETION_PENDING,
        requested_at=now,
        purge_due_at=now.replace(day=10),
        cancellable=True,
        current_step=None,
        retry_count=0,
        blocking_issues=(),
        completed_at=None,
    )
    assert status.cancellable is True
    assert status.lifecycle is DeletionLifecycle.DELETION_PENDING

    cancel = AccountDeletionCancelV1(
        request_id=request_id,
        idempotency_key="cancel-deletion-command-0001",
    )
    assert cancel.schema_version == "1.0"
    with pytest.raises(ValidationError):
        AccountDeletionCancelV1.model_validate({**cancel.model_dump(), "schema_version": "2.0"})

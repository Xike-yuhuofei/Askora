"""EXEC036 / IDP-041..044 account deletion lifecycle integration tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.contracts.privacy import (
    ACCOUNT_DELETION_CONFIRMATION_PHRASE,
    AccountDeletionCancelV1,
    AccountDeletionRequestV1,
    DeletionLifecycle,
)
from app.core.database import Base
from app.core.exceptions import AuthSessionRevokedError, CurrentPasswordInvalidError
from app.models.data_control import DataErasureWorkflowRecord
from app.models.privacy import AccountDeletionRequestRecord
from app.services.auth.auth_service import AuthService
from app.services.privacy.account_deletion import AccountDeletionService


@pytest.mark.asyncio
async def test_preview_request_pending_idempotency_and_cancel_require_fresh_login(
    tmp_path: Path,
) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'deletion.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    fixed_now = datetime(2026, 8, 9, 9, 0, tzinfo=timezone.utc)

    async with factory() as session:
        auth = AuthService(session)
        user, _, _ = await auth.register_user(
            "13800138000", "Askora account password 2026", "待删除用户"
        )
        access_token, _, _, user = await auth.login_with_phone(
            "13800138000", "Askora account password 2026", "deletion-client"
        )
        deletion = AccountDeletionService(
            session,
            now=lambda: fixed_now,
            grace=timedelta(hours=24),
            storage_base_path=tmp_path / "documents",
            restore_barrier_path=tmp_path / "restore-barriers.json",
        )
        preview = await deletion.create_preview(user=user)
        assert preview.policy_version == "account-deletion-v1"
        assert preview.expires_at > preview.generated_at
        assert not preview.blocking_issues

        with pytest.raises(CurrentPasswordInvalidError):
            await deletion.request_deletion(
                user=user,
                command=AccountDeletionRequestV1(
                    current_password="wrong-password",
                    confirmation_phrase=ACCOUNT_DELETION_CONFIRMATION_PHRASE,
                    preview_id=preview.preview_id,
                    preview_digest=preview.preview_digest,
                    idempotency_key="delete-account-command-wrong",
                ),
            )
        assert user.account_lifecycle == "active"

        # The durable failed-attempt row changed the frozen deletion scope.
        preview = await deletion.create_preview(user=user)

        command = AccountDeletionRequestV1(
            current_password="Askora account password 2026",
            confirmation_phrase=ACCOUNT_DELETION_CONFIRMATION_PHRASE,
            preview_id=preview.preview_id,
            preview_digest=preview.preview_digest,
            idempotency_key="delete-account-command-0001",
        )
        accepted = await deletion.request_deletion(user=user, command=command)
        replayed = await deletion.request_deletion(user=user, command=command)
        assert accepted.status.lifecycle is DeletionLifecycle.DELETION_PENDING
        assert accepted.status.purge_due_at == fixed_now + timedelta(hours=24)
        assert replayed.status.request_id == accepted.status.request_id
        assert replayed.deletion_control_token == accepted.deletion_control_token
        assert user.account_lifecycle == "deletion_pending"

        with pytest.raises(AuthSessionRevokedError):
            await auth.validate_token_and_get_user(access_token, "deletion-client")

        cancelled = await deletion.cancel_deletion(
            deletion_control_token=accepted.deletion_control_token,
            command=AccountDeletionCancelV1(
                request_id=accepted.status.request_id,
                idempotency_key="cancel-deletion-command-0001",
            ),
        )
        replayed_cancel = await deletion.cancel_deletion(
            deletion_control_token=accepted.deletion_control_token,
            command=AccountDeletionCancelV1(
                request_id=accepted.status.request_id,
                idempotency_key="cancel-deletion-command-0001",
            ),
        )
        assert cancelled.cancelled is True
        assert cancelled.status.lifecycle is DeletionLifecycle.ACTIVE
        assert replayed_cancel.replayed is True
        assert user.account_lifecycle == "active"
        with pytest.raises(AuthSessionRevokedError):
            await auth.validate_token_and_get_user(access_token, "deletion-client")

        _, _, _, relogged = await auth.login_with_phone(
            "13800138000", "Askora account password 2026", "new-client"
        )
        assert relogged.id == user.id

        final_deletion = AccountDeletionService(
            session,
            now=lambda: fixed_now,
            grace=timedelta(0),
            storage_base_path=tmp_path / "documents",
            restore_barrier_path=tmp_path / "restore-barriers.json",
        )
        final_preview = await final_deletion.create_preview(user=relogged)
        final_accepted = await final_deletion.request_deletion(
            user=relogged,
            command=AccountDeletionRequestV1(
                current_password="Askora account password 2026",
                confirmation_phrase=ACCOUNT_DELETION_CONFIRMATION_PHRASE,
                preview_id=final_preview.preview_id,
                preview_digest=final_preview.preview_digest,
                idempotency_key="delete-account-command-0002",
            ),
        )
        assert await final_deletion.purge_due_requests() == 0
        pending_request = await session.get(
            AccountDeletionRequestRecord, str(final_accepted.status.request_id)
        )
        assert pending_request is not None
        assert pending_request.current_step == "POST_ERASURE_BASELINE"
        assert pending_request.erasure_workflow_id is not None
        workflow = await session.get(DataErasureWorkflowRecord, pending_request.erasure_workflow_id)
        assert workflow is not None
        workflow.status = "COMPLETED"
        workflow.report = {
            **workflow.report,
            "status": "COMPLETED",
            "completed_at": "2026-08-09T10:00:00Z",
        }
        await session.commit()
        assert await final_deletion.purge_due_requests() == 1
        requests = list((await session.execute(select(AccountDeletionRequestRecord))).scalars())
        assert len(requests) == 2
        assert all(item.user_id is None and item.manifest_payload is None for item in requests)
        old_request = next(
            item for item in requests if item.request_id == str(accepted.status.request_id)
        )
        assert old_request.control_token_digest is None
        final_request = next(
            item for item in requests if item.request_id == str(final_accepted.status.request_id)
        )
        assert final_request.lifecycle == "deleted"
        assert final_request.control_token_digest is not None
    await engine.dispose()

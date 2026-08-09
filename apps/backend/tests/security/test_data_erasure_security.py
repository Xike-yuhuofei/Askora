from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models  # noqa: F401
from app.contracts.data_control import DataControlErrorCode, ErasureScope
from app.core.database import Base
from app.data_control.erasure import ErasureCoordinator, ErasurePreviewRegistry
from app.data_control.recovery import RecoveryError
from app.models.dialog import DialogSession
from app.models.user import User, UserRole, UserStatus


@pytest.mark.asyncio
async def test_erasure_preview_is_user_bound_phrase_bound_and_stale_safe(tmp_path: Path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'security.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    current = User(
        id="user-current",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        pseudonym_id="pseudonym-current",
    )
    other = User(
        id="user-other",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        pseudonym_id="pseudonym-other",
    )
    async with factory() as session:
        session.add_all([current, other])
        await session.commit()
        coordinator = ErasureCoordinator(
            session,
            registry=ErasurePreviewRegistry(),
            documents_dir=tmp_path / "documents",
            fail_closed_marker=tmp_path / "recovery" / "erasure-pending.json",
        )
        preview = await coordinator.preview(
            user=current,
            scope=ErasureScope.LEARNING_RECORDS,
        )
        with pytest.raises(RecoveryError) as cross_user:
            await coordinator.confirm(
                user=other,
                preview_id=preview.preview_id,
                token=preview.confirmation_token,
                confirmation_phrase=preview.confirmation_phrase,
                idempotency_key="cross-user",
            )
        assert cross_user.value.code == DataControlErrorCode.ERASURE_PREVIEW_EXPIRED

        with pytest.raises(RecoveryError) as wrong_phrase:
            await coordinator.confirm(
                user=current,
                preview_id=preview.preview_id,
                token=preview.confirmation_token,
                confirmation_phrase="删除",
                idempotency_key="wrong-phrase",
            )
        assert wrong_phrase.value.code == DataControlErrorCode.ERASURE_CONFIRMATION_INVALID

        session.add(
            DialogSession(
                id="late-session",
                user_id=current.id,
                pseudonym_id=current.pseudonym_id,
                title="created-after-preview",
            )
        )
        await session.commit()
        with pytest.raises(RecoveryError) as stale:
            await coordinator.confirm(
                user=current,
                preview_id=preview.preview_id,
                token=preview.confirmation_token,
                confirmation_phrase=preview.confirmation_phrase,
                idempotency_key="stale-preview",
            )
        assert stale.value.code == DataControlErrorCode.ERASURE_CONFIRMATION_INVALID
    await engine.dispose()


@pytest.mark.asyncio
async def test_retryable_owner_failure_converges_with_same_idempotency_key(
    tmp_path: Path,
) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'retry.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    user = User(
        id="user-current",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        pseudonym_id="pseudonym-current",
    )
    failed = False

    def fail_once(owner_system: str) -> None:
        nonlocal failed
        if not failed and owner_system == "LEGACY_DIALOG":
            failed = True
            raise RuntimeError("injected owner failure")

    async with factory() as session:
        session.add_all(
            [
                user,
                DialogSession(
                    id="session-current",
                    user_id=user.id,
                    pseudonym_id=user.pseudonym_id,
                ),
            ]
        )
        await session.commit()
        coordinator = ErasureCoordinator(
            session,
            registry=ErasurePreviewRegistry(),
            documents_dir=tmp_path / "documents",
            fail_closed_marker=tmp_path / "recovery" / "erasure-pending.json",
            owner_failure_injector=fail_once,
        )
        preview = await coordinator.preview(
            user=user,
            scope=ErasureScope.LEARNING_RECORDS,
        )
        first = await coordinator.confirm(
            user=user,
            preview_id=preview.preview_id,
            token=preview.confirmation_token,
            confirmation_phrase=preview.confirmation_phrase,
            idempotency_key="retry-same-command",
        )
        second = await coordinator.confirm(
            user=user,
            preview_id=preview.preview_id,
            token=preview.confirmation_token,
            confirmation_phrase=preview.confirmation_phrase,
            idempotency_key="retry-same-command",
        )

        assert first.status.value == "FAILED_RETRYABLE"
        assert second.status.value == "AWAITING_RECOVERY_BASELINE"
        assert first.workflow_id == second.workflow_id
        assert await session.get(DialogSession, "session-current") is None
    await engine.dispose()

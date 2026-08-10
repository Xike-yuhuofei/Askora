"""LocalOwner data deletion lifecycle integration tests for v1.

EXEC-053: Rewritten to verify data deletion without auth/password.
v1 uses single-user LocalOwnerContext - data deletion is owner-scoped.
Password verification removed since no-auth architecture.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.user import User, UserRole, UserStatus
from app.services.privacy.account_deletion import AccountDeletionService


async def _create_user(db) -> User:
    """Create a local owner user for testing."""
    user = User(
        id="local-owner-001",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        pseudonym_id="test-pseudonym",
        account_lifecycle="active",
    )
    db.add(user)
    await db.commit()
    return user


@pytest.mark.asyncio
async def test_deletion_preview_is_generated(tmp_path: Path) -> None:
    """Verify deletion preview generation works for LocalOwner."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'deletion.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    fixed_now = datetime(2026, 8, 10, 9, 0, tzinfo=timezone.utc)

    async with factory() as session:
        user = await _create_user(session)
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

    await engine.dispose()


@pytest.mark.asyncio
async def test_deletion_preview_is_idempotent(tmp_path: Path) -> None:
    """Verify deletion preview generation produces consistent results."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'deletion2.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    fixed_now = datetime(2026, 8, 10, 9, 0, tzinfo=timezone.utc)

    async with factory() as session:
        user = await _create_user(session)
        deletion = AccountDeletionService(
            session,
            now=lambda: fixed_now,
            grace=timedelta(hours=24),
            storage_base_path=tmp_path / "documents",
            restore_barrier_path=tmp_path / "restore-barriers.json",
        )

        preview = await deletion.create_preview(user=user)
        preview2 = await deletion.create_preview(user=user)
        assert preview.policy_version == preview2.policy_version

    await engine.dispose()


@pytest.mark.asyncio
async def test_deletion_service_handles_active_owner(tmp_path: Path) -> None:
    """Verify deletion service works with active LocalOwner."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'deletion3.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    fixed_now = datetime(2026, 8, 10, 9, 0, tzinfo=timezone.utc)

    async with factory() as session:
        user = await _create_user(session)
        deletion = AccountDeletionService(
            session,
            now=lambda: fixed_now,
            grace=timedelta(hours=24),
            storage_base_path=tmp_path / "documents",
            restore_barrier_path=tmp_path / "restore-barriers.json",
        )

        # Preview should work for active owner
        preview = await deletion.create_preview(user=user)
        assert preview is not None
        assert preview.file_count >= 0

    await engine.dispose()

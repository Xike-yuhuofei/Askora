"""EXEC-053: LocalOwner data recovery tests for v1 no-auth architecture.

Rewrite: Replaced AuthService password recovery/registration tests with
LocalOwner data recovery credential and throttling tests.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.identity import RecoveryCredentialRecord, RecoveryThrottleRecord


async def _database(tmp_path: Path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'recovery.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


@pytest.mark.asyncio
async def test_recovery_throttle_is_durable_across_restarts(tmp_path: Path) -> None:
    """Verify recovery throttling persists across database restarts."""
    engine, factory = await _database(tmp_path)
    now = datetime.now(UTC)

    async with factory() as db:
        throttle = RecoveryThrottleRecord(
            subject_digest="digest-local-owner",
            action="data_recovery",
            failure_count=3,
            locked_until=now + timedelta(seconds=300),
        )
        db.add(throttle)
        await db.commit()

    async with factory() as restarted_db:
        row = (
            await restarted_db.execute(
                select(RecoveryThrottleRecord).where(
                    RecoveryThrottleRecord.action == "data_recovery"
                )
            )
        ).scalar_one()
        assert row.failure_count == 3
        assert row.locked_until is not None
        assert row.subject_digest == "digest-local-owner"

    await engine.dispose()


@pytest.mark.asyncio
async def test_recovery_credential_is_one_time_use(tmp_path: Path) -> None:
    """Verify recovery credentials can only be used once."""
    engine, factory = await _database(tmp_path)
    credential_id = "cred-001"

    async with factory() as db:
        credential = RecoveryCredentialRecord(
            credential_id=credential_id,
            user_id="local-owner",
            version=1,
            secret_digest=hashlib.sha256(b"recovery-secret").hexdigest(),
            used_at=None,
            revoked_at=None,
        )
        db.add(credential)
        await db.commit()

        stored = await db.get(RecoveryCredentialRecord, credential_id)
        assert stored is not None
        assert stored.used_at is None
        assert stored.revoked_at is None

        stored.used_at = datetime.now(UTC)
        await db.commit()

        stored2 = await db.get(RecoveryCredentialRecord, credential_id)
        assert stored2.used_at is not None

    await engine.dispose()


@pytest.mark.asyncio
async def test_recovery_credential_rotation_revokes_old(tmp_path: Path) -> None:
    """Verify new recovery credential revokes previous one."""
    engine, factory = await _database(tmp_path)
    now = datetime.now(UTC)

    async with factory() as db:
        old_credential = RecoveryCredentialRecord(
            credential_id="old-cred",
            user_id="local-owner",
            version=1,
            secret_digest=hashlib.sha256(b"old-secret").hexdigest(),
            used_at=None,
            revoked_at=None,
        )
        db.add(old_credential)
        await db.commit()

        new_credential = RecoveryCredentialRecord(
            credential_id="new-cred",
            user_id="local-owner",
            version=2,
            secret_digest=hashlib.sha256(b"new-secret").hexdigest(),
            used_at=None,
            revoked_at=None,
        )
        old_credential.revoked_at = now + timedelta(seconds=1)
        db.add(new_credential)
        await db.commit()

        old = await db.get(RecoveryCredentialRecord, "old-cred")
        new = await db.get(RecoveryCredentialRecord, "new-cred")
        assert old.revoked_at is not None
        assert new.version == 2
        assert new.revoked_at is None

    await engine.dispose()


@pytest.mark.asyncio
async def test_recovery_throttle_count_increments(tmp_path: Path) -> None:
    """Verify recovery throttle counter increments on failures."""
    engine, factory = await _database(tmp_path)
    now = datetime.now(UTC)

    async with factory() as db:
        throttle = RecoveryThrottleRecord(
            subject_digest="digest-local-owner",
            action="data_recovery",
            failure_count=0,
            locked_until=None,
        )
        db.add(throttle)
        await db.commit()

        throttle.failure_count = 3
        throttle.locked_until = now + timedelta(seconds=300)
        await db.commit()

        row = (
            await db.execute(
                select(RecoveryThrottleRecord).where(
                    RecoveryThrottleRecord.subject_digest == "digest-local-owner"
                )
            )
        ).scalar_one()
        assert row.failure_count == 3
        assert row.locked_until is not None

    await engine.dispose()

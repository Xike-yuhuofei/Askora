"""Deletion worker and pre-business restore-barrier enforcement."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.contracts.privacy import ACCOUNT_DELETION_POLICY_VERSION
from app.core.config import settings
from app.core.exceptions import PrivacyRestoreBlockedError
from app.infrastructure.privacy import PrivacyInventoryRepository, manifest_to_payload
from app.models.privacy import AccountDeletionRequestRecord
from app.models.user import User
from app.services.privacy.account_deletion import AccountDeletionService
from app.services.privacy.restore_barrier import RestoreBarrierStore


async def enforce_restore_barriers(
    factory: async_sessionmaker[AsyncSession],
    *,
    barrier_path: Path,
    storage_base_path: Path,
    max_attempts: int,
) -> int:
    """Re-purge users resurrected by an ordinary DB snapshot before business startup."""
    barriers = RestoreBarrierStore(barrier_path).load()
    if not barriers:
        return 0
    recovered = 0
    async with factory() as session:
        users = list((await session.execute(select(User))).scalars())
        for user in users:
            subject_digest = AccountDeletionService._subject_digest(user.id)
            if subject_digest not in barriers or user.account_lifecycle == "deleted":
                continue
            now = datetime.now(timezone.utc)
            manifest = await PrivacyInventoryRepository(session).build_manifest(
                user_id=user.id,
                pseudonym_id=user.pseudonym_id,
                subject_digest=subject_digest,
                subject_digests=AccountDeletionService._identity_subject_digests(user),
                storage_base_path=storage_base_path,
            )
            if manifest.blocking_issues:
                raise PrivacyRestoreBlockedError()
            # Never trust receipts restored with an older snapshot. A fresh request
            # binds a fresh manifest and forces every owner step to run again.
            record = AccountDeletionRequestRecord(
                request_id=str(uuid.uuid4()),
                user_id=user.id,
                preview_id=None,
                schema_version="1.0",
                policy_version=ACCOUNT_DELETION_POLICY_VERSION,
                subject_digest=subject_digest,
                lifecycle="purging",
                manifest_digest=manifest.manifest_digest,
                manifest_payload=manifest_to_payload(manifest),
                idempotency_key_digest=None,
                request_digest=None,
                control_token_digest=None,
                requested_at=now,
                purge_due_at=now,
                retry_count=0,
                blocking_issues=[],
            )
            session.add(record)
            user.account_lifecycle = "purging"
            await session.commit()
            service = AccountDeletionService(
                session,
                storage_base_path=storage_base_path,
                restore_barrier_path=barrier_path,
            )
            completed = await service._purge_record(record, max_attempts=max_attempts)
            if not completed:
                refreshed = await session.get(AccountDeletionRequestRecord, record.request_id)
                if not (
                    refreshed is not None
                    and refreshed.lifecycle == "purging"
                    and refreshed.current_step == "POST_ERASURE_BASELINE"
                    and refreshed.erasure_receipt_id is not None
                    and refreshed.erasure_checkpoint is not None
                ):
                    raise PrivacyRestoreBlockedError()
            recovered += 1
    return recovered


class AccountDeletionRuntime:
    def __init__(
        self,
        factory: async_sessionmaker[AsyncSession],
        *,
        barrier_path: Path,
        storage_base_path: Path,
        poll_interval: float,
        max_attempts: int,
    ) -> None:
        self._factory = factory
        self._barrier_path = barrier_path
        self._storage_base_path = storage_base_path
        self._poll_interval = poll_interval
        self._max_attempts = max_attempts
        self._task: asyncio.Task[None] | None = None
        self._stopping = asyncio.Event()

    async def start(self) -> None:
        await self.run_once()
        self._task = asyncio.create_task(self._run(), name="account-deletion-worker")

    async def stop(self) -> None:
        self._stopping.set()
        if self._task is not None:
            await self._task
            self._task = None

    async def run_once(self) -> int:
        async with self._factory() as session:
            return await AccountDeletionService(
                session,
                storage_base_path=self._storage_base_path,
                restore_barrier_path=self._barrier_path,
            ).purge_due_requests(max_attempts=self._max_attempts)

    async def _run(self) -> None:
        while not self._stopping.is_set():
            try:
                await asyncio.wait_for(self._stopping.wait(), timeout=self._poll_interval)
            except TimeoutError:
                await self.run_once()


_runtime: AccountDeletionRuntime | None = None


async def start_account_deletion_runtime(factory: async_sessionmaker[AsyncSession]) -> int:
    global _runtime
    barrier_path = Path(settings.privacy_restore_barrier_path)
    storage_base_path = Path(settings.local_storage_base_path)
    recovered = await enforce_restore_barriers(
        factory,
        barrier_path=barrier_path,
        storage_base_path=storage_base_path,
        max_attempts=settings.account_deletion_max_attempts,
    )
    _runtime = AccountDeletionRuntime(
        factory,
        barrier_path=barrier_path,
        storage_base_path=storage_base_path,
        poll_interval=settings.account_deletion_poll_interval,
        max_attempts=settings.account_deletion_max_attempts,
    )
    await _runtime.start()
    return recovered


async def stop_account_deletion_runtime() -> None:
    global _runtime
    if _runtime is not None:
        await _runtime.stop()
        _runtime = None

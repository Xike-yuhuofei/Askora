"""EXEC036 / IDP-052..056 owner purge, reconciliation and barrier recovery tests."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.contracts.privacy import (
    ACCOUNT_DELETION_CONFIRMATION_PHRASE,
    AccountDeletionRequestV1,
    AccountDeletionRetryV1,
    DeletionLifecycle,
)
from app.core.database import Base
from app.core.exceptions import InvalidTokenError
from app.infrastructure.privacy import FrozenSubjectManifest, PrivacyInventoryRepository
from app.models.document import DocumentChunk, ModerationStatus, ProcessingStatus, UserDocument
from app.models.knowledge import KnowledgePoint
from app.models.privacy import OwnerErasureStepReceiptRecord, PrivacyTombstoneRecord
from app.models.user import User, UserRole, UserStatus
from app.services.auth.auth_service import AuthService
from app.services.privacy.account_deletion import AccountDeletionService
from app.services.privacy.cache import cache_scope_digests, purge_matching_cache
from app.services.privacy.restore_barrier import RestoreBarrierStore
from app.services.privacy.runtime import enforce_restore_barriers


@pytest.mark.asyncio
async def test_due_purge_deletes_rows_files_and_identity_but_preserves_other_user_and_global(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "purge.db"
    documents = tmp_path / "documents"
    barrier_path = tmp_path / "restore-barriers.json"
    engine = create_async_engine(f"sqlite+aiosqlite:///{database_path}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    fixed_now = datetime(2026, 8, 9, 9, 0, tzinfo=timezone.utc)

    async with factory() as session:
        auth = AuthService(session)
        target, _, _ = await auth.register_user(
            "13800138000", "Askora target password 2026", "目标用户"
        )
        other, _, _ = await auth.register_user(
            "13900139000", "Askora other password 2026", "其他用户"
        )
        target_file = documents / target.pseudonym_id / "doc-target.txt"
        other_file = documents / other.pseudonym_id / "doc-other.txt"
        target_file.parent.mkdir(parents=True)
        other_file.parent.mkdir(parents=True)
        target_file.write_text("target private content", encoding="utf-8")
        other_file.write_text("other private content", encoding="utf-8")
        session.add_all(
            [
                UserDocument(
                    id="doc-target",
                    pseudonym_id=target.pseudonym_id,
                    original_filename="target.txt",
                    file_extension="txt",
                    file_size_bytes=target_file.stat().st_size,
                    storage_path=f"{target.pseudonym_id}/doc-target.txt",
                    processing_status=ProcessingStatus.COMPLETED,
                    moderation_status=ModerationStatus.APPROVED,
                    moderation_categories=[],
                    moderation_details={},
                    chunk_count=1,
                    total_tokens=3,
                    access_count=0,
                    is_deleted=False,
                ),
                UserDocument(
                    id="doc-other",
                    pseudonym_id=other.pseudonym_id,
                    original_filename="other.txt",
                    file_extension="txt",
                    file_size_bytes=other_file.stat().st_size,
                    storage_path=f"{other.pseudonym_id}/doc-other.txt",
                    processing_status=ProcessingStatus.COMPLETED,
                    moderation_status=ModerationStatus.APPROVED,
                    moderation_categories=[],
                    moderation_details={},
                    chunk_count=0,
                    total_tokens=3,
                    access_count=0,
                    is_deleted=False,
                ),
                DocumentChunk(
                    id="chunk-target",
                    document_id="doc-target",
                    chunk_index=0,
                    content="private content",
                    token_count=3,
                    chunk_metadata={},
                    embedding_model="fixture",
                    embedding_dimension=3,
                ),
                KnowledgePoint(
                    id="global-kp",
                    subject="math",
                    name="全局知识",
                    code="GLOBAL_KP",
                    level=1,
                    difficulty=1,
                    grade_range=[],
                    prerequisites=[],
                    successors=[],
                    misconceptions=[],
                    is_active=True,
                    version="1.0",
                ),
            ]
        )
        await session.commit()
        deletion = AccountDeletionService(
            session,
            now=lambda: fixed_now,
            grace=timedelta(0),
            storage_base_path=documents,
            restore_barrier_path=barrier_path,
        )
        preview = await deletion.create_preview(user=target)
        accepted = await deletion.request_deletion(
            user=target,
            command=AccountDeletionRequestV1(
                current_password="Askora target password 2026",
                confirmation_phrase=ACCOUNT_DELETION_CONFIRMATION_PHRASE,
                preview_id=preview.preview_id,
                preview_digest=preview.preview_digest,
                idempotency_key="purge-target-command-0001",
            ),
        )

        assert await deletion.purge_due_requests() == 1
        status = await deletion.get_status(deletion_control_token=accepted.deletion_control_token)
        assert status.lifecycle is DeletionLifecycle.DELETED
        assert target.account_lifecycle == "deleted"
        assert target.status is UserStatus.DELETED
        assert target.phone_encrypted is None
        assert target.phone_hash is None
        assert target.password_hash is None
        assert target.nickname is None
        assert not target_file.exists()
        assert other_file.exists()
        assert await session.get(UserDocument, "doc-target") is None
        assert await session.get(DocumentChunk, "chunk-target") is None
        assert await session.get(UserDocument, "doc-other") is not None
        assert await session.get(KnowledgePoint, "global-kp") is not None
        assert await session.get(PrivacyTombstoneRecord, str(status.request_id)) is not None
        receipt_count = await session.scalar(
            select(func.count(OwnerErasureStepReceiptRecord.receipt_id))
        )
        assert receipt_count == 12

    barrier_payload = json.loads(barrier_path.read_text(encoding="utf-8"))
    assert len(barrier_payload["barriers"]) == 1
    serialized = json.dumps(barrier_payload, ensure_ascii=False)
    assert "13800138000" not in serialized
    assert "目标用户" not in serialized
    await engine.dispose()


@pytest.mark.asyncio
async def test_old_database_snapshot_is_repurged_before_business_startup(
    tmp_path: Path,
) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'restored.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    barrier_path = tmp_path / "outside-db" / "restore-barriers.json"
    storage_path = tmp_path / "documents"
    now = datetime(2026, 8, 9, 11, 0, tzinfo=timezone.utc)

    async with factory() as session:
        target, _, _ = await AuthService(session).register_user(
            "13600136000", "Askora restored password 2026", "旧快照用户"
        )
        target_id = target.id
        subject_digest = AccountDeletionService._subject_digest(target.id)
        RestoreBarrierStore(barrier_path).append(
            subject_digest=subject_digest,
            request_id=str(uuid.uuid4()),
            policy_version="account-deletion-v1",
            manifest_digest="sha256:" + "0" * 64,
            completed_at=now,
        )

    assert (
        await enforce_restore_barriers(
            factory,
            barrier_path=barrier_path,
            storage_base_path=storage_path,
            max_attempts=3,
        )
        == 1
    )
    async with factory() as session:
        restored = await session.get(User, target_id)
        assert restored is not None
        assert restored.status is UserStatus.DELETED
        assert restored.account_lifecycle == "deleted"
        with pytest.raises(InvalidTokenError):
            await AuthService(session).login_with_phone(
                phone="13600136000",
                password="Askora restored password 2026",
            )
    await engine.dispose()


def test_deleted_user_shape_retains_no_reversible_identity() -> None:
    user = User(
        id="deleted-user",
        role=UserRole.USER,
        status=UserStatus.DELETED,
        account_lifecycle="deleted",
        credential_version=2,
        pseudonym_id="deleted_012345678901234567890123",
        is_verified=False,
    )
    assert user.phone_encrypted is None
    assert user.email_encrypted is None
    assert user.password_hash is None


class _FakeRedis:
    def __init__(self, values: dict[str, str]) -> None:
        self.values = values

    async def scan_iter(self, *, match: str):
        assert match == "*"
        for key in list(self.values):
            yield key

    async def type(self, key: str) -> str:
        return "string"

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def delete(self, key: str) -> int:
        return int(self.values.pop(key, None) is not None)


@pytest.mark.asyncio
async def test_cache_erasure_uses_plain_manifest_then_irreversible_barrier_scope() -> None:
    manifest = FrozenSubjectManifest(
        schema_version="1.0",
        policy_version="account-deletion-v1",
        user_id="user-cache-a",
        pseudonym_id="pseudo-cache-a",
        subject_digest="subject-cache-a",
        entries=(),
        blocking_issues=(),
        manifest_digest="sha256:" + "a" * 64,
        data_fingerprint="sha256:" + "b" * 64,
    )
    cache = _FakeRedis(
        {
            "session:session-a": json.dumps(
                {"user_id": "user-cache-a", "pseudonym_id": "pseudo-cache-a"}
            ),
            "profile:user-cache-a": "cached-profile",
            "profile:user-cache-b": json.dumps({"user_id": "user-cache-b"}),
        }
    )
    assert await purge_matching_cache(cache, aliases={manifest.user_id, manifest.pseudonym_id}) == 2
    assert set(cache.values) == {"profile:user-cache-b"}

    cache.values["askora:kt:user-cache-a:kp-1"] = "cached-mastery"
    assert await purge_matching_cache(cache, alias_digests=set(cache_scope_digests(manifest))) == 1
    assert set(cache.values) == {"profile:user-cache-b"}


@pytest.mark.asyncio
async def test_owner_failure_blocks_and_explicit_retry_resumes_from_receipts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'retry.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    fixed_now = datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc)
    original = PrivacyInventoryRepository.erase_owner
    failed = False

    async def fail_sys03_once(self, *, owner, manifest):
        nonlocal failed
        if owner == "SYS03" and not failed:
            failed = True
            raise OSError("simulated owner failure")
        return await original(self, owner=owner, manifest=manifest)

    monkeypatch.setattr(PrivacyInventoryRepository, "erase_owner", fail_sys03_once)
    async with factory() as session:
        user, _, _ = await AuthService(session).register_user(
            "13700137000", "Askora retry password 2026", "重试用户"
        )
        deletion = AccountDeletionService(
            session,
            now=lambda: fixed_now,
            grace=timedelta(0),
            storage_base_path=tmp_path / "documents",
            restore_barrier_path=tmp_path / "barriers.json",
        )
        preview = await deletion.create_preview(user=user)
        accepted = await deletion.request_deletion(
            user=user,
            command=AccountDeletionRequestV1(
                current_password="Askora retry password 2026",
                confirmation_phrase=ACCOUNT_DELETION_CONFIRMATION_PHRASE,
                preview_id=preview.preview_id,
                preview_digest=preview.preview_digest,
                idempotency_key="retry-request-command-0001",
            ),
        )
        assert await deletion.purge_due_requests() == 0
        blocked = await deletion.get_status(deletion_control_token=accepted.deletion_control_token)
        assert blocked.lifecycle is DeletionLifecycle.DELETION_BLOCKED
        receipts_before = await session.scalar(
            select(func.count(OwnerErasureStepReceiptRecord.receipt_id))
        )
        assert receipts_before == 4

        completed = await deletion.retry_deletion(
            deletion_control_token=accepted.deletion_control_token,
            command=AccountDeletionRetryV1(
                request_id=blocked.request_id,
                idempotency_key="retry-explicit-command-0001",
            ),
        )
        assert completed.lifecycle is DeletionLifecycle.DELETED
        receipts_after = await session.scalar(
            select(func.count(OwnerErasureStepReceiptRecord.receipt_id))
        )
        assert receipts_after == 12
        replay = await deletion.retry_deletion(
            deletion_control_token=accepted.deletion_control_token,
            command=AccountDeletionRetryV1(
                request_id=blocked.request_id,
                idempotency_key="retry-explicit-command-0001",
            ),
        )
        assert replay.lifecycle is DeletionLifecycle.DELETED

    await engine.dispose()


@pytest.mark.asyncio
async def test_postgresql_representative_deletion_fixture(tmp_path: Path) -> None:
    database_url = os.getenv("ASKORA_TEST_POSTGRES_URL")
    if not database_url:
        pytest.skip("ASKORA_TEST_POSTGRES_URL is required for the PostgreSQL release gate")
    assert "askora_p1_05_test_" in database_url
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    fixed_now = datetime(2026, 8, 9, 12, 0, tzinfo=timezone.utc)
    async with factory() as session:
        user, _, _ = await AuthService(session).register_user(
            "13400134000", "Askora postgres password 2026", "PostgreSQL 用户"
        )
        deletion = AccountDeletionService(
            session,
            now=lambda: fixed_now,
            grace=timedelta(0),
            storage_base_path=tmp_path / "documents",
            restore_barrier_path=tmp_path / "postgres-barriers.json",
        )
        preview = await deletion.create_preview(user=user)
        accepted = await deletion.request_deletion(
            user=user,
            command=AccountDeletionRequestV1(
                current_password="Askora postgres password 2026",
                confirmation_phrase=ACCOUNT_DELETION_CONFIRMATION_PHRASE,
                preview_id=preview.preview_id,
                preview_digest=preview.preview_digest,
                idempotency_key="postgres-delete-command-0001",
            ),
        )
        assert await deletion.purge_due_requests() == 1
        status = await deletion.get_status(deletion_control_token=accepted.deletion_control_token)
        assert status.lifecycle is DeletionLifecycle.DELETED
        assert await session.get(PrivacyTombstoneRecord, str(status.request_id)) is not None
    await engine.dispose()

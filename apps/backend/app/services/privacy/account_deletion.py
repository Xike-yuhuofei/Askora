"""IDP-041..044 preview, request, deletion-control and cancel lifecycle."""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.privacy import (
    ACCOUNT_DELETION_POLICY_VERSION,
    AccountDeletionAcceptedV1,
    AccountDeletionCancelResultV1,
    AccountDeletionCancelV1,
    AccountDeletionPreviewV1,
    AccountDeletionRequestV1,
    AccountDeletionRetryV1,
    AccountDeletionStatusV1,
    DeletionLifecycle,
    PrivacyBlockingIssueV1,
)
from app.core.config import settings
from app.core.exceptions import (
    AccountDeletionBlockedError,
    AccountDeletionInProgressError,
    AccountDeletionNotCancellableError,
    AccountDeletionPreviewStaleError,
    InvalidTokenError,
    PrivacySubjectAmbiguousError,
)
from app.infrastructure.identity import IdentityRepository
from app.infrastructure.privacy import (
    OWNER_ERASURE_ORDER,
    SUBJECT_REGISTRY,
    PrivacyInventoryRepository,
    manifest_from_payload,
    manifest_to_payload,
)
from app.models.privacy import (
    AccountDeletionPreviewRecord,
    AccountDeletionRequestRecord,
    OwnerErasureStepReceiptRecord,
    PrivacyTombstoneRecord,
)
from app.models.user import User, UserStatus
from app.services.auth.auth_service import AuthService
from app.services.privacy.cache import cache_scope_digests, purge_manifest_cache_if_available
from app.services.privacy.restore_barrier import RestoreBarrierStore

DELETION_CONTROL_TOKEN_TYPE = "deletion_control"


class AccountDeletionService:
    def __init__(
        self,
        db: AsyncSession,
        *,
        now: Callable[[], datetime] | None = None,
        grace: timedelta = timedelta(hours=24),
        preview_ttl: timedelta = timedelta(hours=1),
        storage_base_path: Path | None = None,
        restore_barrier_path: Path | None = None,
    ) -> None:
        self.db = db
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._grace = grace
        self._preview_ttl = preview_ttl
        self._storage_base_path = storage_base_path or Path(settings.local_storage_base_path)
        self._restore_barrier_path = restore_barrier_path

    async def create_preview(self, *, user: User) -> AccountDeletionPreviewV1:
        if user.account_lifecycle != "active":
            raise AccountDeletionInProgressError()
        generated_at = self._utc(self._now())
        subject_digest = self._subject_digest(user.id)
        manifest = await PrivacyInventoryRepository(self.db).build_manifest(
            user_id=user.id,
            pseudonym_id=user.pseudonym_id,
            subject_digest=subject_digest,
            subject_digests=self._identity_subject_digests(user),
            storage_base_path=self._storage_base_path,
        )
        counts: dict[str, int] = {}
        for entry in manifest.entries:
            counts[entry.owner] = counts.get(entry.owner, 0) + 1
        expires_at = generated_at + self._preview_ttl
        digest = self._sha256(
            {
                "manifest_digest": manifest.manifest_digest,
                "data_fingerprint": manifest.data_fingerprint,
                "generated_at": generated_at,
                "expires_at": expires_at,
                "policy_version": ACCOUNT_DELETION_POLICY_VERSION,
            }
        )
        preview = AccountDeletionPreviewV1(
            preview_id=uuid.uuid4(),
            generated_at=generated_at,
            expires_at=expires_at,
            counts_by_owner=counts,
            file_count=sum(entry.file_path is not None for entry in manifest.entries),
            pending_task_count=sum(
                entry.table_name == "outbox_tasks" for entry in manifest.entries
            ),
            projection_count=sum(entry.projection for entry in manifest.entries),
            blocking_issues=tuple(
                PrivacyBlockingIssueV1(
                    code=issue.code,
                    record_type=issue.table_name,
                    record_id=issue.record_id,
                )
                for issue in manifest.blocking_issues
            ),
            explicit_exclusions=tuple(
                sorted(
                    name
                    for name, registry in SUBJECT_REGISTRY.items()
                    if registry.disposition.value == "global"
                )
            ),
            recovery_boundary="普通数据库快照之外的 restore barrier 仍会阻止旧账号恢复",
            preview_digest=digest,
        )
        self.db.add(
            AccountDeletionPreviewRecord(
                preview_id=str(preview.preview_id),
                user_id=user.id,
                schema_version=preview.schema_version,
                policy_version=preview.policy_version,
                subject_digest=subject_digest,
                manifest_digest=manifest.manifest_digest,
                data_fingerprint=manifest.data_fingerprint,
                manifest_payload=manifest_to_payload(manifest),
                preview_payload=preview.model_dump(mode="json"),
                generated_at=generated_at,
                expires_at=expires_at,
            )
        )
        await self.db.commit()
        return preview

    async def request_deletion(
        self, *, user: User, command: AccountDeletionRequestV1
    ) -> AccountDeletionAcceptedV1:
        subject_digest = self._subject_digest(user.id)
        key_digest = self._digest(command.idempotency_key)
        request_digest = self._request_digest(command)
        existing = (
            await self.db.execute(
                select(AccountDeletionRequestRecord).where(
                    AccountDeletionRequestRecord.subject_digest == subject_digest,
                    AccountDeletionRequestRecord.idempotency_key_digest == key_digest,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            if existing.request_digest is None or not hmac.compare_digest(
                existing.request_digest, request_digest
            ):
                raise AccountDeletionPreviewStaleError()
            return AccountDeletionAcceptedV1(
                status=self._status(existing),
                deletion_control_token=self._issue_control_token(existing),
            )
        if user.account_lifecycle != "active":
            raise AccountDeletionInProgressError()

        preview = await self.db.get(AccountDeletionPreviewRecord, str(command.preview_id))
        now = self._utc(self._now())
        if (
            preview is None
            or preview.user_id != user.id
            or preview.consumed_at is not None
            or self._utc(preview.expires_at) <= now
            or preview.policy_version != command.policy_version
            or not hmac.compare_digest(
                preview.preview_payload["preview_digest"], command.preview_digest
            )
        ):
            raise AccountDeletionPreviewStaleError()
        if preview.manifest_payload.get("blocking_issues"):
            raise PrivacySubjectAmbiguousError()

        current_manifest = await PrivacyInventoryRepository(self.db).build_manifest(
            user_id=user.id,
            pseudonym_id=user.pseudonym_id,
            subject_digest=subject_digest,
            subject_digests=self._identity_subject_digests(user),
            storage_base_path=self._storage_base_path,
        )
        if (
            current_manifest.blocking_issues
            or current_manifest.manifest_digest != preview.manifest_digest
            or current_manifest.data_fingerprint != preview.data_fingerprint
        ):
            raise AccountDeletionPreviewStaleError()

        await AuthService(self.db).verify_current_password_for_action(
            user=user,
            password=command.current_password,
            action="deletion_confirmation",
        )
        request_id = str(uuid.uuid4())
        due_at = now + self._grace
        record = AccountDeletionRequestRecord(
            request_id=request_id,
            user_id=user.id,
            preview_id=preview.preview_id,
            schema_version="1.0",
            policy_version=ACCOUNT_DELETION_POLICY_VERSION,
            subject_digest=subject_digest,
            lifecycle="deletion_pending",
            manifest_digest=current_manifest.manifest_digest,
            manifest_payload=manifest_to_payload(current_manifest),
            idempotency_key_digest=key_digest,
            request_digest=request_digest,
            control_token_digest="pending",
            requested_at=now,
            purge_due_at=due_at,
            retry_count=0,
            blocking_issues=[],
        )
        token = self._issue_control_token(record)
        record.control_token_digest = self._digest(token)
        preview.consumed_by_request_id = request_id
        preview.consumed_at = now
        user.account_lifecycle = "deletion_pending"
        await IdentityRepository(self.db).revoke_all_sessions(
            user_id=user.id,
            now=now,
            reason="account_deletion_pending",
        )
        self.db.add(record)
        await self.db.commit()
        return AccountDeletionAcceptedV1(status=self._status(record), deletion_control_token=token)

    async def cancel_deletion(
        self,
        *,
        deletion_control_token: str,
        command: AccountDeletionCancelV1,
    ) -> AccountDeletionCancelResultV1:
        record = await self._request_from_control_token(deletion_control_token)
        if record.request_id != str(command.request_id):
            raise InvalidTokenError("删除控制令牌与请求不匹配")
        key_digest = self._digest(command.idempotency_key)
        if record.lifecycle == "cancelled":
            if record.cancel_idempotency_key_digest != key_digest:
                raise AccountDeletionNotCancellableError()
            return AccountDeletionCancelResultV1(
                cancelled=True, replayed=True, status=self._status(record)
            )
        now = self._utc(self._now())
        if record.lifecycle != "deletion_pending" or now >= self._utc(record.purge_due_at):
            raise AccountDeletionNotCancellableError()
        user = await self.db.get(User, record.user_id)
        if user is None:
            raise AccountDeletionNotCancellableError()
        record.lifecycle = "cancelled"
        record.cancelled_at = now
        record.cancel_idempotency_key_digest = key_digest
        user.account_lifecycle = "active"
        await self.db.commit()
        return AccountDeletionCancelResultV1(
            cancelled=True, replayed=False, status=self._status(record)
        )

    async def get_status(self, *, deletion_control_token: str) -> AccountDeletionStatusV1:
        return self._status(await self._request_from_control_token(deletion_control_token))

    async def retry_deletion(
        self,
        *,
        deletion_control_token: str,
        command: AccountDeletionRetryV1,
        max_attempts: int = 3,
    ) -> AccountDeletionStatusV1:
        record = await self._request_from_control_token(deletion_control_token)
        if record.request_id != str(command.request_id):
            raise InvalidTokenError("删除控制令牌与请求不匹配")
        key_digest = self._digest(command.idempotency_key)
        if record.retry_idempotency_key_digest == key_digest:
            return self._status(record)
        if record.lifecycle != "deletion_blocked" or record.retry_count >= max_attempts:
            raise AccountDeletionBlockedError()
        record.retry_idempotency_key_digest = key_digest
        record.lifecycle = "purging"
        record.last_error_code = None
        record.blocking_issues = []
        if record.user_id:
            user = await self.db.get(User, record.user_id)
            if user is not None:
                user.account_lifecycle = "purging"
        await self.db.commit()
        await self._purge_record(record, max_attempts=max_attempts)
        return self._status(record)

    async def purge_due_requests(self, *, max_attempts: int = 3) -> int:
        now = self._utc(self._now())
        records = list(
            (
                await self.db.execute(
                    select(AccountDeletionRequestRecord)
                    .where(
                        (
                            (AccountDeletionRequestRecord.lifecycle == "deletion_pending")
                            & (AccountDeletionRequestRecord.purge_due_at <= now)
                        )
                        | (AccountDeletionRequestRecord.lifecycle == "purging")
                    )
                    .order_by(
                        AccountDeletionRequestRecord.purge_due_at,
                        AccountDeletionRequestRecord.request_id,
                    )
                )
            ).scalars()
        )
        completed = 0
        for record in records:
            if await self._purge_record(record, max_attempts=max_attempts):
                completed += 1
        return completed

    async def _purge_record(
        self, record: AccountDeletionRequestRecord, *, max_attempts: int
    ) -> bool:
        if record.lifecycle not in {"deletion_pending", "purging"}:
            return record.lifecycle == "deleted"
        if record.manifest_payload is None or record.user_id is None:
            await self._block(record, "PRIVACY_MANIFEST_UNAVAILABLE")
            return False
        if record.retry_count >= max_attempts:
            await self._block(record, "PRIVACY_RETRY_EXHAUSTED")
            return False
        record.lifecycle = "purging"
        record.retry_count += 1
        record.purge_started_at = record.purge_started_at or self._utc(self._now())
        user = await self.db.get(User, record.user_id)
        if user is None:
            await self._block(record, "PRIVACY_SUBJECT_MISSING")
            return False
        user.account_lifecycle = "purging"
        await self.db.commit()

        manifest = manifest_from_payload(record.manifest_payload)
        repository = PrivacyInventoryRepository(self.db, storage_base_path=self._storage_base_path)
        attempt = record.retry_count
        request_id = record.request_id
        for owner in OWNER_ERASURE_ORDER:
            record.current_step = owner
            await self.db.commit()
            existing = (
                (
                    await self.db.execute(
                        select(OwnerErasureStepReceiptRecord).where(
                            OwnerErasureStepReceiptRecord.request_id == record.request_id,
                            OwnerErasureStepReceiptRecord.owner == owner,
                            OwnerErasureStepReceiptRecord.error_count == 0,
                            OwnerErasureStepReceiptRecord.manifest_digest
                            == manifest.manifest_digest,
                        )
                    )
                )
                .scalars()
                .first()
            )
            if existing is not None:
                continue
            try:
                counts = await repository.erase_owner(owner=owner, manifest=manifest)
                receipt_payload = {
                    "request_id": record.request_id,
                    "owner": owner,
                    "attempt": attempt,
                    "requested_count": counts.requested_count,
                    "deleted_count": counts.deleted_count,
                    "missing_count": counts.missing_count,
                    "error_count": counts.error_count,
                    "manifest_digest": manifest.manifest_digest,
                }
                self.db.add(
                    OwnerErasureStepReceiptRecord(
                        receipt_id=str(uuid.uuid4()),
                        request_id=record.request_id,
                        owner=owner,
                        attempt=attempt,
                        requested_count=counts.requested_count,
                        deleted_count=counts.deleted_count,
                        missing_count=counts.missing_count,
                        error_count=counts.error_count,
                        manifest_digest=manifest.manifest_digest,
                        receipt_digest=self._sha256(receipt_payload),
                    )
                )
                await self.db.commit()
            except Exception as exc:  # noqa: BLE001 - owner failure becomes durable blocked state
                await self.db.rollback()
                reloaded = await self.db.get(AccountDeletionRequestRecord, request_id)
                assert reloaded is not None
                record = reloaded
                await self._block(
                    record, f"PRIVACY_OWNER_ERASURE_FAILED:{owner}:{type(exc).__name__}"
                )
                return False

        record.current_step = "PROJECTIONS"
        await self.db.commit()
        residual = await PrivacyInventoryRepository(self.db).build_manifest(
            user_id=user.id,
            pseudonym_id=user.pseudonym_id,
            subject_digest=record.subject_digest,
            subject_digests=self._identity_subject_digests(user),
            storage_base_path=self._storage_base_path,
        )
        if residual.entries or residual.blocking_issues:
            await self._block(record, "PRIVACY_RECONCILIATION_FAILED")
            return False

        try:
            await self._finalize_identity(record=record, user=user, manifest=manifest)
        except Exception as exc:  # noqa: BLE001 - barrier/finalization failure must fail closed
            await self.db.rollback()
            reloaded = await self.db.get(AccountDeletionRequestRecord, request_id)
            assert reloaded is not None
            record = reloaded
            await self._block(record, f"PRIVACY_FINALIZE_FAILED:{type(exc).__name__}")
            return False
        return True

    async def _finalize_identity(
        self,
        *,
        record: AccountDeletionRequestRecord,
        user: User,
        manifest,
    ) -> None:
        now = self._utc(self._now())
        receipts = list(
            (
                await self.db.execute(
                    select(OwnerErasureStepReceiptRecord)
                    .where(OwnerErasureStepReceiptRecord.request_id == record.request_id)
                    .order_by(
                        OwnerErasureStepReceiptRecord.owner,
                        OwnerErasureStepReceiptRecord.attempt,
                    )
                )
            ).scalars()
        )
        receipts_digest = self._sha256(
            [
                {
                    "owner": receipt.owner,
                    "attempt": receipt.attempt,
                    "receipt_digest": receipt.receipt_digest,
                }
                for receipt in receipts
            ]
        )
        if self._restore_barrier_path is None:
            raise ValueError("PRIVACY_RESTORE_BARRIER_UNAVAILABLE")
        await purge_manifest_cache_if_available(manifest)
        barrier_digest = RestoreBarrierStore(self._restore_barrier_path).append(
            subject_digest=record.subject_digest,
            request_id=record.request_id,
            policy_version=record.policy_version,
            manifest_digest=record.manifest_digest,
            completed_at=now,
            cache_scope_digests=cache_scope_digests(manifest),
        )
        self.db.add(
            PrivacyTombstoneRecord(
                request_id=record.request_id,
                schema_version="1.0",
                policy_version=record.policy_version,
                subject_digest=record.subject_digest,
                manifest_digest=record.manifest_digest,
                receipts_digest=receipts_digest,
                restore_barrier_digest=barrier_digest,
                final_status="deleted",
                completed_at=now,
            )
        )
        user.status = UserStatus.DELETED
        user.account_lifecycle = "deleted"
        user.phone_encrypted = None
        user.phone_hash = None
        user.email_encrypted = None
        user.nickname = None
        user.password_hash = None
        user.password_changed_at = None
        user.wechat_openid_encrypted = None
        user.real_name_encrypted = None
        user.is_verified = False
        user.last_login_at = None
        user.deleted_at = now
        user.credential_version += 1
        user.pseudonym_id = f"deleted_{record.subject_digest[:24]}"

        original_user_id = record.user_id
        await self.db.execute(
            delete(AccountDeletionPreviewRecord).where(
                AccountDeletionPreviewRecord.user_id == original_user_id
            )
        )
        related_requests = list(
            (
                await self.db.execute(
                    select(AccountDeletionRequestRecord).where(
                        AccountDeletionRequestRecord.subject_digest == record.subject_digest
                    )
                )
            ).scalars()
        )
        for related in related_requests:
            related.user_id = None
            related.preview_id = None
            related.manifest_payload = None
            related.idempotency_key_digest = None
            related.request_digest = None
            related.cancel_idempotency_key_digest = None
            if related.request_id != record.request_id:
                related.retry_idempotency_key_digest = None
                related.control_token_digest = None
        record.lifecycle = "deleted"
        record.current_step = "IDENTITY_FINALIZE"
        record.completed_at = now
        record.last_error_code = None
        record.blocking_issues = []
        await self.db.commit()

    async def _block(self, record: AccountDeletionRequestRecord, code: str) -> None:
        record.lifecycle = "deletion_blocked"
        record.last_error_code = code
        record.blocking_issues = [{"code": code}]
        if record.user_id:
            user = await self.db.get(User, record.user_id)
            if user is not None:
                user.account_lifecycle = "deletion_blocked"
        await self.db.commit()

    async def _request_from_control_token(self, token: str) -> AccountDeletionRequestRecord:
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
                issuer=settings.app_name,
                options={"verify_iat": False, "verify_exp": False},
            )
        except jwt.PyJWTError as exc:
            raise InvalidTokenError("删除控制令牌无效或已过期") from exc
        if payload.get("type") != DELETION_CONTROL_TOKEN_TYPE or payload.get("scope") != [
            "status",
            "cancel",
            "retry",
        ]:
            raise InvalidTokenError("删除控制令牌权限无效")
        expires_at = payload.get("exp")
        if not isinstance(expires_at, int) or expires_at <= int(self._utc(self._now()).timestamp()):
            raise InvalidTokenError("删除控制令牌无效或已过期")
        request_id = payload.get("rid")
        if not isinstance(request_id, str):
            raise InvalidTokenError("删除控制令牌缺少请求标识")
        record = await self.db.get(AccountDeletionRequestRecord, request_id)
        if (
            record is None
            or record.control_token_digest is None
            or not hmac.compare_digest(record.control_token_digest, self._digest(token))
        ):
            raise InvalidTokenError("删除控制令牌已失效")
        return record

    def _issue_control_token(self, record: AccountDeletionRequestRecord) -> str:
        requested_at = self._utc(record.requested_at)
        payload = {
            "iss": settings.app_name,
            "type": DELETION_CONTROL_TOKEN_TYPE,
            "rid": record.request_id,
            "sub_digest": record.subject_digest,
            "scope": ["status", "cancel", "retry"],
            "iat": int(requested_at.timestamp()),
            "exp": int((requested_at + timedelta(days=30)).timestamp()),
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    def _status(self, record: AccountDeletionRequestRecord) -> AccountDeletionStatusV1:
        lifecycle = (
            DeletionLifecycle.ACTIVE
            if record.lifecycle == "cancelled"
            else DeletionLifecycle(record.lifecycle)
        )
        return AccountDeletionStatusV1(
            request_id=uuid.UUID(record.request_id),
            lifecycle=lifecycle,
            requested_at=self._utc(record.requested_at),
            purge_due_at=self._utc(record.purge_due_at),
            cancellable=record.lifecycle == "deletion_pending"
            and self._utc(self._now()) < self._utc(record.purge_due_at),
            current_step=record.current_step,
            retry_count=record.retry_count,
            blocking_issues=tuple(
                PrivacyBlockingIssueV1.model_validate(issue)
                for issue in (record.blocking_issues or [])
            ),
            completed_at=self._utc(record.completed_at) if record.completed_at else None,
        )

    @staticmethod
    def _utc(value: datetime) -> datetime:
        return (
            value.replace(tzinfo=timezone.utc)
            if value.tzinfo is None
            else value.astimezone(timezone.utc)
        )

    @staticmethod
    def _digest(value: str) -> str:
        return hmac.new(
            settings.kek_master_key.encode("utf-8"), value.encode("utf-8"), hashlib.sha256
        ).hexdigest()

    @classmethod
    def _subject_digest(cls, user_id: str) -> str:
        return cls._digest(f"account:{user_id}")

    @classmethod
    def _identity_subject_digests(cls, user: User) -> tuple[str, ...]:
        values = {cls._digest(f"user:{user.id}")}
        if user.phone_hash:
            values.add(user.phone_hash)
        return tuple(sorted(values))

    @classmethod
    def _request_digest(cls, command: AccountDeletionRequestV1) -> str:
        payload = command.model_dump(mode="json", exclude={"current_password"})
        payload["current_password_digest"] = cls._digest(command.current_password)
        return cls._digest(json.dumps(payload, sort_keys=True, separators=(",", ":")))

    @staticmethod
    def _sha256(value: object) -> str:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode(
            "utf-8"
        )
        return "sha256:" + hashlib.sha256(encoded).hexdigest()

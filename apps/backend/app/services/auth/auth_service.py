"""Identity application service backed by durable database sessions."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.identity import (
    AuthSessionV1,
    ChangePasswordResultV1,
    ChangePasswordV1,
    IssueRecoveryKitV1,
    RecoverPasswordResultV1,
    RecoverPasswordV1,
    RecoveryKitResultV1,
    RecoveryStatusV1,
    SessionCommandResultV1,
    SessionListV1,
    TokenPairV1,
)
from app.core.config import settings
from app.core.encryption import decrypt_pii, encrypt_pii
from app.core.exceptions import (
    AuthRecoveryInvalidError,
    AuthRecoveryRateLimitedError,
    AuthSessionNotFoundError,
    AuthSessionRequiredError,
    AuthSessionRevokedError,
    CurrentPasswordInvalidError,
    DeviceMismatchError,
    IdentityCommandConflictError,
    InvalidTokenError,
    PasswordPolicyRejectedError,
    RefreshReplayDetectedError,
    TooManySessionsError,
)
from app.core.logging import get_logger
from app.infrastructure.identity import IdentityRepository
from app.models.identity import (
    AuthSessionRecord,
    IdentityCommandReceiptRecord,
    RecoveryCredentialRecord,
)
from app.models.user import User, UserRole, UserStatus
from app.services.auth.token_service import (
    TokenService,
    hash_password,
    validate_new_password,
    verify_and_update_password,
    verify_password,
)

logger = get_logger(__name__)
MAX_SESSIONS = 5
MAX_AUTH_FAILURES = 5
AUTH_COOLDOWN = timedelta(minutes=15)
_DUMMY_PASSWORD_HASH = hash_password("askora-dummy-password-never-valid-v1")


class AuthService:
    """Only application writer for credentials and durable AuthSession state."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = IdentityRepository(db)

    async def login_with_phone(
        self,
        phone: str,
        password: str,
        device_fingerprint: str | None = None,
    ) -> tuple[str, str, datetime, User]:
        phone = phone.strip()
        phone_hash = self._phone_lookup_hash(phone)
        await self._assert_not_throttled(subject_digest=phone_hash, action="login")
        result = await self.db.execute(select(User).where(User.phone_hash == phone_hash))
        user = result.scalar_one_or_none()

        if user is None:
            user = await self._find_legacy_user(phone, phone_hash)
        password_hash = user.password_hash if user and user.password_hash else _DUMMY_PASSWORD_HASH
        verified, replacement_hash = verify_and_update_password(password, password_hash)
        if not user or not user.password_hash or not verified:
            await self._record_auth_failure(subject_digest=phone_hash, action="login")
            raise InvalidTokenError("手机号或密码错误")
        if user.status != UserStatus.ACTIVE or user.account_lifecycle != "active":
            raise InvalidTokenError("账号不可登录")

        now = datetime.now(timezone.utc)
        if await self.repo.active_session_count(user.id, now) >= MAX_SESSIONS:
            raise TooManySessionsError(MAX_SESSIONS)

        session_id = str(uuid.uuid4())
        family_id = str(uuid.uuid4())
        credential_version = user.credential_version
        client_digest = (
            self._hash_device_fingerprint(device_fingerprint) if device_fingerprint else None
        )
        access_token, _, access_expires_at = TokenService.create_access_token(
            user_id=user.id,
            role=user.role.value,
            pseudonym_id=user.pseudonym_id,
            device_fingerprint=client_digest,
            session_id=session_id,
            token_family_id=family_id,
            credential_version=credential_version,
            session_version=1,
        )
        refresh_token, refresh_jti, refresh_expires_at = TokenService.create_refresh_token(
            user_id=user.id,
            role=user.role.value,
            pseudonym_id=user.pseudonym_id,
            device_fingerprint=client_digest,
            session_id=session_id,
            token_family_id=family_id,
            credential_version=credential_version,
            session_version=1,
        )
        await self.repo.add_session(
            AuthSessionRecord(
                session_id=session_id,
                user_id=user.id,
                version=1,
                token_family_id=family_id,
                current_refresh_jti_digest=self._digest_secret(refresh_jti),
                client_instance_digest=client_digest,
                client_label=self._client_label(client_digest),
                credential_version=credential_version,
                created_at=now,
                last_seen_at=now,
                refresh_expires_at=refresh_expires_at,
            )
        )
        if replacement_hash:
            user.password_hash = replacement_hash
            user.password_changed_at = now
        user.last_login_at = now
        await self.repo.reset_throttle(subject_digest=phone_hash, action="login")
        await self.db.commit()

        logger.info("user_login_success", user_id=user.id, session_id=session_id[:8])
        return access_token, refresh_token, access_expires_at, user

    async def logout(self, user_id: str, session_id: str) -> None:
        await self.repo.revoke_session(
            session_id=session_id,
            user_id=user_id,
            now=datetime.now(timezone.utc),
            reason="logout",
        )
        await self.db.commit()
        logger.info("user_logout", user_id=user_id, session_id=session_id[:8])

    async def heartbeat(self, user_id: str, session_id: str) -> None:
        """Update last_seen_at to keep session alive. Called periodically by frontend."""
        now = datetime.now(timezone.utc)
        updated = await self.repo.touch_session(
            session_id=session_id,
            user_id=user_id,
            now=now,
        )
        if updated == 0:
            raise AuthSessionRevokedError("会话已失效")
        await self.db.commit()

    async def validate_token_and_get_user(
        self,
        token: str,
        device_fingerprint: str | None = None,
    ) -> tuple[User, dict[str, Any]]:
        payload = TokenService.decode_token(token, token_type="access")
        user_id, session_id, family_id, credential_version, session_version = (
            self._required_session_claims(payload)
        )
        self._verify_device_binding(payload, device_fingerprint)

        now = datetime.now(timezone.utc)
        session = await self.repo.get_exact_active_session(
            session_id=session_id,
            user_id=user_id,
            family_id=family_id,
            credential_version=credential_version,
            session_version=session_version,
            now=now,
        )
        if session is None:
            raise AuthSessionRevokedError()

        user = await self.db.get(User, user_id)
        if (
            not user
            or user.status != UserStatus.ACTIVE
            or user.account_lifecycle != "active"
            or user.credential_version != credential_version
        ):
            raise AuthSessionRevokedError()
        return user, payload

    async def refresh_tokens(
        self,
        refresh_token: str,
        device_fingerprint: str | None = None,
    ) -> tuple[str, str, datetime]:
        payload = TokenService.decode_token(refresh_token, token_type="refresh")
        user_id, session_id, family_id, credential_version, session_version = (
            self._required_session_claims(payload)
        )
        self._verify_device_binding(payload, device_fingerprint)
        jti = payload.get("jti")
        if not isinstance(jti, str) or not jti:
            raise AuthSessionRequiredError()

        user = await self.db.get(User, user_id)
        if (
            not user
            or user.status != UserStatus.ACTIVE
            or user.account_lifecycle != "active"
            or user.credential_version != credential_version
        ):
            raise AuthSessionRevokedError()

        session = await self.repo.get_session(session_id)
        now = datetime.now(timezone.utc)
        if (
            session is None
            or session.user_id != user_id
            or session.token_family_id != family_id
            or session.credential_version != credential_version
        ):
            raise AuthSessionRevokedError()
        if session.revoked_at is not None or self._as_utc(session.refresh_expires_at) <= now:
            raise AuthSessionRevokedError()

        expected_digest = self._digest_secret(jti)
        if not hmac.compare_digest(session.current_refresh_jti_digest, expected_digest):
            await self.repo.revoke_session(
                session_id=session_id,
                user_id=user_id,
                now=now,
                reason="refresh_replay",
            )
            await self.db.commit()
            raise RefreshReplayDetectedError()

        next_version = session_version + 1
        access_token, _, access_expires_at = TokenService.create_access_token(
            user_id=user.id,
            role=user.role.value,
            pseudonym_id=user.pseudonym_id,
            device_fingerprint=session.client_instance_digest,
            session_id=session_id,
            token_family_id=family_id,
            credential_version=credential_version,
            session_version=next_version,
        )
        next_refresh, next_jti, next_refresh_expires_at = TokenService.create_refresh_token(
            user_id=user.id,
            role=user.role.value,
            pseudonym_id=user.pseudonym_id,
            device_fingerprint=session.client_instance_digest,
            session_id=session_id,
            token_family_id=family_id,
            credential_version=credential_version,
            session_version=next_version,
        )
        rotated = await self.repo.rotate_refresh_compare_and_swap(
            session_id=session_id,
            user_id=user_id,
            family_id=family_id,
            credential_version=credential_version,
            expected_version=session_version,
            expected_jti_digest=expected_digest,
            next_jti_digest=self._digest_secret(next_jti),
            next_refresh_expires_at=next_refresh_expires_at,
            now=now,
        )
        if not rotated:
            await self.db.rollback()
            await self.repo.revoke_session(
                session_id=session_id,
                user_id=user_id,
                now=now,
                reason="refresh_replay",
            )
            await self.db.commit()
            raise RefreshReplayDetectedError()
        await self.db.commit()
        return access_token, next_refresh, access_expires_at

    async def list_sessions(self, *, user_id: str, current_session_id: str) -> SessionListV1:
        rows = await self.repo.list_sessions(user_id)
        return SessionListV1(
            sessions=tuple(
                AuthSessionV1(
                    session_id=row.session_id,
                    version=row.version,
                    client_label=row.client_label,
                    current=row.session_id == current_session_id,
                    created_at=self._as_utc(row.created_at),
                    last_seen_at=self._as_utc(row.last_seen_at),
                    refresh_expires_at=self._as_utc(row.refresh_expires_at),
                    revoked=row.revoked_at is not None,
                )
                for row in rows
            )
        )

    async def revoke_session(
        self,
        *,
        user_id: str,
        target_session_id: str,
        idempotency_key: str,
    ) -> SessionCommandResultV1:
        request = {"target_session_id": target_session_id}
        receipt = await self._matching_receipt(
            user_id=user_id,
            command_type="revoke_session_v1",
            idempotency_key=idempotency_key,
            request=request,
        )
        if receipt:
            return SessionCommandResultV1.model_validate(
                {**receipt.result_payload, "replayed": True}
            )

        session = await self.repo.get_session(target_session_id)
        if session is None or session.user_id != user_id:
            raise AuthSessionNotFoundError()
        count = await self.repo.revoke_session(
            session_id=target_session_id,
            user_id=user_id,
            now=datetime.now(timezone.utc),
            reason="user_revoked",
        )
        payload = {"success": True, "replayed": False, "revoked_sessions": count}
        await self._store_receipt(
            user_id=user_id,
            command_type="revoke_session_v1",
            idempotency_key=idempotency_key,
            request=request,
            result_payload=payload,
        )
        await self.db.commit()
        return SessionCommandResultV1.model_validate(payload)

    async def revoke_other_sessions(
        self,
        *,
        user_id: str,
        current_session_id: str,
        idempotency_key: str,
    ) -> SessionCommandResultV1:
        request = {"current_session_id": current_session_id}
        receipt = await self._matching_receipt(
            user_id=user_id,
            command_type="revoke_other_sessions_v1",
            idempotency_key=idempotency_key,
            request=request,
        )
        if receipt:
            return SessionCommandResultV1.model_validate(
                {**receipt.result_payload, "replayed": True}
            )
        count = await self.repo.revoke_other_sessions(
            user_id=user_id,
            current_session_id=current_session_id,
            now=datetime.now(timezone.utc),
            reason="user_revoked_others",
        )
        payload = {"success": True, "replayed": False, "revoked_sessions": count}
        await self._store_receipt(
            user_id=user_id,
            command_type="revoke_other_sessions_v1",
            idempotency_key=idempotency_key,
            request=request,
            result_payload=payload,
        )
        await self.db.commit()
        return SessionCommandResultV1.model_validate(payload)

    async def change_password(
        self,
        *,
        user: User,
        payload: dict[str, Any],
        command: ChangePasswordV1,
    ) -> ChangePasswordResultV1:
        _, session_id, family_id, credential_version, session_version = (
            self._required_session_claims(payload)
        )
        if command.current_session_version != session_version:
            raise IdentityCommandConflictError()

        request = {
            "session_id": session_id,
            "session_version": session_version,
            "current_password_digest": self._digest_secret(command.current_password),
            "new_password_digest": self._digest_secret(command.new_password),
        }
        receipt = await self._matching_receipt(
            user_id=user.id,
            command_type="change_password_v1",
            idempotency_key=command.idempotency_key,
            request=request,
        )
        if receipt:
            return ChangePasswordResultV1.model_validate(
                {
                    **receipt.result_payload,
                    "replayed": True,
                    "tokens": None,
                    "recovery_action": "密码已修改；若令牌响应丢失，请使用新密码重新登录",
                }
            )

        throttle_subject = self._user_throttle_subject(user)
        await self._assert_not_throttled(subject_digest=throttle_subject, action="current_password")
        if not user.password_hash or not verify_password(
            command.current_password, user.password_hash
        ):
            await self._record_auth_failure(
                subject_digest=throttle_subject, action="current_password"
            )
            raise CurrentPasswordInvalidError()
        try:
            validate_new_password(command.new_password, current_password=command.current_password)
        except ValueError as exc:
            raise PasswordPolicyRejectedError(str(exc))

        session = await self.repo.get_session(session_id)
        if (
            session is None
            or session.user_id != user.id
            or session.token_family_id != family_id
            or session.version != session_version
            or session.credential_version != credential_version
            or session.revoked_at is not None
        ):
            raise AuthSessionRevokedError()

        now = datetime.now(timezone.utc)
        next_credential_version = user.credential_version + 1
        next_session_version = session.version + 1
        next_family_id = str(uuid.uuid4())
        access_token, _, access_expires_at = TokenService.create_access_token(
            user_id=user.id,
            role=user.role.value,
            pseudonym_id=user.pseudonym_id,
            device_fingerprint=session.client_instance_digest,
            session_id=session.session_id,
            token_family_id=next_family_id,
            credential_version=next_credential_version,
            session_version=next_session_version,
        )
        refresh_token, refresh_jti, refresh_expires_at = TokenService.create_refresh_token(
            user_id=user.id,
            role=user.role.value,
            pseudonym_id=user.pseudonym_id,
            device_fingerprint=session.client_instance_digest,
            session_id=session.session_id,
            token_family_id=next_family_id,
            credential_version=next_credential_version,
            session_version=next_session_version,
        )

        revoked_others = await self.repo.revoke_other_sessions(
            user_id=user.id,
            current_session_id=session.session_id,
            now=now,
            reason="credential_changed",
        )
        user.password_hash = hash_password(command.new_password)
        user.credential_version = next_credential_version
        user.password_changed_at = now
        session.version = next_session_version
        session.token_family_id = next_family_id
        session.current_refresh_jti_digest = self._digest_secret(refresh_jti)
        session.credential_version = next_credential_version
        session.last_seen_at = now
        session.refresh_expires_at = refresh_expires_at
        await self.repo.reset_throttle(subject_digest=throttle_subject, action="current_password")

        stored_payload = {
            "schema_version": "1.0",
            "changed": True,
            "replayed": False,
            "session_id": session.session_id,
            "session_version": next_session_version,
            "revoked_other_sessions": revoked_others,
            "tokens": None,
            "recovery_action": None,
        }
        await self._store_receipt(
            user_id=user.id,
            command_type="change_password_v1",
            idempotency_key=command.idempotency_key,
            request=request,
            result_payload=stored_payload,
        )
        await self.db.commit()

        expires_in = int(access_expires_at.timestamp() - now.timestamp())
        return ChangePasswordResultV1.model_validate(
            {
                **stored_payload,
                "tokens": TokenPairV1(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    expires_in=max(0, expires_in),
                ),
            }
        )

    async def register_user(
        self,
        phone: str,
        password: str,
        nickname: str | None = None,
    ) -> tuple[User, str, RecoveryCredentialRecord]:
        try:
            validate_new_password(password)
        except ValueError as exc:
            raise PasswordPolicyRejectedError(str(exc))
        phone = phone.strip()
        phone_hash = self._phone_lookup_hash(phone)
        result = await self.db.execute(select(User).where(User.phone_hash == phone_hash))
        if result.scalar_one_or_none() is not None:
            raise ValueError("该手机号已注册")
        if await self._find_legacy_user(phone, phone_hash) is not None:
            raise ValueError("该手机号已注册")

        user = User(
            id=str(uuid.uuid4()),
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            phone_encrypted=encrypt_pii(phone),
            phone_hash=phone_hash,
            password_hash=hash_password(password),
            credential_version=1,
            password_changed_at=datetime.now(timezone.utc),
            nickname=nickname.strip() if nickname and nickname.strip() else None,
            pseudonym_id=uuid.uuid4().hex,
        )
        self.db.add(user)
        try:
            await self.db.flush()
            recovery_secret, recovery = await self._issue_recovery_credential(
                user_id=user.id,
                now=datetime.now(timezone.utc),
            )
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise ValueError("该手机号已注册") from exc
        await self.db.refresh(user)
        logger.info("user_registered", user_id=user.id)
        return user, recovery_secret, recovery

    async def recovery_status(self, *, user_id: str) -> RecoveryStatusV1:
        credential = await self.repo.get_active_recovery_credential(user_id)
        return RecoveryStatusV1(
            configured=credential is not None,
            credential_version=credential.version if credential else None,
            created_at=self._as_utc(credential.created_at) if credential else None,
        )

    async def issue_recovery_kit(
        self,
        *,
        user: User,
        command: IssueRecoveryKitV1,
    ) -> RecoveryKitResultV1:
        request = {"current_password_digest": self._digest_secret(command.current_password)}
        receipt = await self._matching_receipt(
            user_id=user.id,
            command_type="issue_recovery_kit_v1",
            idempotency_key=command.idempotency_key,
            request=request,
        )
        if receipt:
            created_at = datetime.fromisoformat(str(receipt.result_payload["created_at"]))
            return RecoveryKitResultV1(
                issued=True,
                replayed=True,
                recovery_secret=None,
                credential_version=int(receipt.result_payload["credential_version"]),
                created_at=created_at,
                storage_warning="恢复套件已生成且不会再次显示；如未保存，请重新轮换",
            )

        subject = self._user_throttle_subject(user)
        await self._assert_not_throttled(subject_digest=subject, action="current_password")
        if not user.password_hash or not verify_password(
            command.current_password, user.password_hash
        ):
            await self._record_auth_failure(subject_digest=subject, action="current_password")
            raise CurrentPasswordInvalidError()

        now = datetime.now(timezone.utc)
        secret, credential = await self._issue_recovery_credential(user_id=user.id, now=now)
        await self.repo.reset_throttle(subject_digest=subject, action="current_password")
        stored = {
            "credential_version": credential.version,
            "created_at": now.isoformat(),
        }
        await self._store_receipt(
            user_id=user.id,
            command_type="issue_recovery_kit_v1",
            idempotency_key=command.idempotency_key,
            request=request,
            result_payload=stored,
        )
        await self.db.commit()
        return RecoveryKitResultV1(
            issued=True,
            replayed=False,
            recovery_secret=secret,
            credential_version=credential.version,
            created_at=now,
        )

    async def recover_password(self, command: RecoverPasswordV1) -> RecoverPasswordResultV1:
        try:
            validate_new_password(command.new_password)
        except ValueError as exc:
            raise PasswordPolicyRejectedError(str(exc))

        phone = command.phone.strip()
        subject = self._phone_lookup_hash(phone)
        await self._assert_not_throttled(subject_digest=subject, action="recovery")
        result = await self.db.execute(select(User).where(User.phone_hash == subject))
        user = result.scalar_one_or_none()
        if user is None:
            user = await self._find_legacy_user(phone, subject)

        request = {
            "recovery_secret_digest": self._digest_secret(command.recovery_secret),
            "new_password_digest": self._digest_secret(command.new_password),
            "client_instance_digest": self._hash_device_fingerprint(command.client_instance),
        }
        if user is not None:
            receipt = await self._matching_receipt(
                user_id=user.id,
                command_type="recover_password_v1",
                idempotency_key=command.idempotency_key,
                request=request,
            )
            if receipt:
                return RecoverPasswordResultV1(
                    accepted=True,
                    replayed=True,
                    recovery_secret=None,
                    recovery_credential_version=int(
                        receipt.result_payload["recovery_credential_version"]
                    ),
                )

        credential = await self.repo.get_active_recovery_credential(
            user.id if user is not None else "__unknown_recovery_subject__"
        )
        provided_digest = self._digest_secret(command.recovery_secret)
        expected_digest = (
            credential.secret_digest if credential is not None else self._dummy_recovery_digest()
        )
        valid = hmac.compare_digest(provided_digest, expected_digest)
        if (
            not valid
            or user is None
            or credential is None
            or user.status != UserStatus.ACTIVE
            or user.account_lifecycle != "active"
        ):
            await self._record_auth_failure(subject_digest=subject, action="recovery")
            raise AuthRecoveryInvalidError()
        if user.password_hash and verify_password(command.new_password, user.password_hash):
            raise PasswordPolicyRejectedError("新密码不能与当前密码相同")

        now = datetime.now(timezone.utc)
        credential.used_at = now
        user.password_hash = hash_password(command.new_password)
        user.credential_version += 1
        user.password_changed_at = now
        await self.repo.revoke_all_sessions(
            user_id=user.id,
            now=now,
            reason="account_recovered",
        )
        new_secret, new_credential = await self._issue_recovery_credential(
            user_id=user.id,
            now=now,
            revoke_existing=False,
        )
        await self.repo.reset_throttle(subject_digest=subject, action="recovery")
        stored = {"recovery_credential_version": new_credential.version}
        await self._store_receipt(
            user_id=user.id,
            command_type="recover_password_v1",
            idempotency_key=command.idempotency_key,
            request=request,
            result_payload=stored,
        )
        await self.db.commit()
        logger.info("account_recovery_success", user_id=user.id)
        return RecoverPasswordResultV1(
            accepted=True,
            replayed=False,
            recovery_secret=new_secret,
            recovery_credential_version=new_credential.version,
        )

    async def _issue_recovery_credential(
        self,
        *,
        user_id: str,
        now: datetime,
        revoke_existing: bool = True,
    ) -> tuple[str, RecoveryCredentialRecord]:
        if revoke_existing:
            await self.repo.revoke_active_recovery_credentials(user_id=user_id, now=now)
        version = await self.repo.latest_recovery_version(user_id) + 1
        secret = secrets.token_urlsafe(24)
        credential = RecoveryCredentialRecord(
            credential_id=str(uuid.uuid4()),
            user_id=user_id,
            version=version,
            secret_digest=self._digest_secret(secret),
            created_at=now,
        )
        await self.repo.add_recovery_credential(credential)
        return secret, credential

    async def verify_current_password_for_action(
        self,
        *,
        user: User,
        password: str,
        action: str,
    ) -> None:
        """IDP-031: server-side throttled re-authentication for sensitive commands."""
        subject = self._user_throttle_subject(user)
        await self._assert_not_throttled(subject_digest=subject, action=action)
        if not user.password_hash or not verify_password(password, user.password_hash):
            await self._record_auth_failure(subject_digest=subject, action=action)
            raise CurrentPasswordInvalidError()
        await self.repo.reset_throttle(subject_digest=subject, action=action)

    async def _assert_not_throttled(self, *, subject_digest: str, action: str) -> None:
        row = await self.repo.get_throttle(subject_digest=subject_digest, action=action)
        if row is None or row.locked_until is None:
            return
        now = datetime.now(timezone.utc)
        locked_until = self._as_utc(row.locked_until)
        if locked_until <= now:
            await self.repo.reset_throttle(subject_digest=subject_digest, action=action)
            return
        raise AuthRecoveryRateLimitedError(int((locked_until - now).total_seconds()))

    async def _record_auth_failure(self, *, subject_digest: str, action: str) -> None:
        now = datetime.now(timezone.utc)
        row = await self.repo.record_throttle_failure(
            subject_digest=subject_digest,
            action=action,
            now=now,
            max_failures=MAX_AUTH_FAILURES,
            locked_until=now + AUTH_COOLDOWN,
        )
        await self.db.commit()
        if row.failure_count >= MAX_AUTH_FAILURES and row.locked_until is not None:
            raise AuthRecoveryRateLimitedError(int(AUTH_COOLDOWN.total_seconds()))

    def _user_throttle_subject(self, user: User) -> str:
        return user.phone_hash or self._digest_secret(f"user:{user.id}")

    @staticmethod
    def _dummy_recovery_digest() -> str:
        return AuthService._digest_secret("askora-recovery-dummy-v1")

    async def _find_legacy_user(self, phone: str, phone_hash: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.phone_hash.is_(None), User.phone_encrypted.isnot(None))
        )
        for candidate in result.scalars().all():
            try:
                if candidate.phone_encrypted and decrypt_pii(candidate.phone_encrypted) == phone:
                    candidate.phone_hash = phone_hash
                    return candidate
            except Exception:
                logger.warning("legacy_phone_decrypt_failed", user_id=candidate.id)
        return None

    def _required_session_claims(self, payload: dict[str, Any]) -> tuple[str, str, str, int, int]:
        user_id = payload.get("sub")
        session_id = payload.get("sid")
        family_id = payload.get("fam")
        credential_version = payload.get("cv")
        session_version = payload.get("sv")
        if (
            not isinstance(user_id, str)
            or not isinstance(session_id, str)
            or not isinstance(family_id, str)
            or not isinstance(credential_version, int)
            or not isinstance(session_version, int)
        ):
            raise AuthSessionRequiredError()
        return user_id, session_id, family_id, credential_version, session_version

    def _verify_device_binding(
        self, payload: dict[str, Any], device_fingerprint: str | None
    ) -> None:
        expected = payload.get("dfp")
        if not expected:
            return
        if not device_fingerprint:
            raise DeviceMismatchError()
        actual = self._hash_device_fingerprint(device_fingerprint)
        if not hmac.compare_digest(expected, actual):
            raise DeviceMismatchError()

    async def _matching_receipt(
        self,
        *,
        user_id: str,
        command_type: str,
        idempotency_key: str,
        request: dict[str, Any],
    ) -> IdentityCommandReceiptRecord | None:
        key_digest = self._digest_secret(idempotency_key)
        receipt = await self.repo.get_receipt(
            user_id=user_id, command_type=command_type, key_digest=key_digest
        )
        if receipt and not hmac.compare_digest(
            receipt.request_digest, self._request_digest(request)
        ):
            raise IdentityCommandConflictError()
        return receipt

    async def _store_receipt(
        self,
        *,
        user_id: str,
        command_type: str,
        idempotency_key: str,
        request: dict[str, Any],
        result_payload: dict[str, Any],
    ) -> None:
        await self.repo.add_receipt(
            IdentityCommandReceiptRecord(
                receipt_id=str(uuid.uuid4()),
                user_id=user_id,
                command_type=command_type,
                idempotency_key_digest=self._digest_secret(idempotency_key),
                request_digest=self._request_digest(request),
                result_payload=result_payload,
            )
        )

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        return (
            value.replace(tzinfo=timezone.utc)
            if value.tzinfo is None
            else value.astimezone(timezone.utc)
        )

    @staticmethod
    def _client_label(client_digest: str | None) -> str:
        return f"Askora App 实例 · {client_digest[-6:]}" if client_digest else "Askora App 实例"

    @staticmethod
    def _hash_device_fingerprint(device_fingerprint: str) -> str:
        return hmac.new(
            settings.kek_master_key.encode(), device_fingerprint.encode(), hashlib.sha256
        ).hexdigest()

    @staticmethod
    def _phone_lookup_hash(phone: str) -> str:
        return hmac.new(
            settings.kek_master_key.encode(), phone.encode(), hashlib.sha256
        ).hexdigest()

    @staticmethod
    def _digest_secret(value: str) -> str:
        return hmac.new(
            settings.kek_master_key.encode(), value.encode(), hashlib.sha256
        ).hexdigest()

    @classmethod
    def _request_digest(cls, value: dict[str, Any]) -> str:
        canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return cls._digest_secret(canonical)

"""EXEC035 local recovery issuance, rotation, consumption and throttling."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.contracts.identity import IssueRecoveryKitV1, RecoverPasswordV1
from app.core.exceptions import (
    AuthRecoveryInvalidError,
    AuthRecoveryRateLimitedError,
    CurrentPasswordInvalidError,
    InvalidTokenError,
)
from app.main import app_error_handler
from app.models.identity import (
    AuthSessionRecord,
    IdentityCommandReceiptRecord,
    RecoveryCredentialRecord,
    RecoveryThrottleRecord,
)
from app.models.user import User
from app.services.auth.auth_service import AuthService
from app.services.auth.token_service import verify_password

PASSWORD = "correct horse battery staple"
NEW_PASSWORD = "恢复后的 Askora 新密码 2026"


@pytest.mark.asyncio
async def test_rate_limit_error_preserves_retry_after_response_header() -> None:
    response = await app_error_handler(
        SimpleNamespace(state=SimpleNamespace(request_id="recovery-test")),
        AuthRecoveryRateLimitedError(900),
    )

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "900"


@pytest.mark.asyncio
async def test_unknown_login_runs_password_verification(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine, factory = await _database(tmp_path)
    verified_hashes: list[str] = []

    def fake_verify(_password: str, encoded: str) -> tuple[bool, None]:
        verified_hashes.append(encoded)
        return False, None

    monkeypatch.setattr("app.services.auth.auth_service.verify_and_update_password", fake_verify)
    async with factory() as db:
        with pytest.raises(InvalidTokenError):
            await AuthService(db).login_with_phone("13900139009", "unknown-password")

    assert len(verified_hashes) == 1
    assert verified_hashes[0].startswith("$argon2id$")
    await engine.dispose()


async def _database(tmp_path: Path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'recovery.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(User.__table__.create)
        await connection.run_sync(AuthSessionRecord.__table__.create)
        await connection.run_sync(IdentityCommandReceiptRecord.__table__.create)
        await connection.run_sync(RecoveryCredentialRecord.__table__.create)
        await connection.run_sync(RecoveryThrottleRecord.__table__.create)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


@pytest.mark.asyncio
async def test_registration_issues_once_and_settings_rotation_revokes_old_secret(
    tmp_path: Path,
) -> None:
    engine, factory = await _database(tmp_path)
    async with factory() as db:
        service = AuthService(db)
        user, registration_secret, credential = await service.register_user(
            "13800138001", PASSWORD, "恢复测试"
        )
        assert len(registration_secret) >= 32
        assert credential.secret_digest != registration_secret
        assert registration_secret not in str(credential.__dict__)

        rotated = await service.issue_recovery_kit(
            user=user,
            command=IssueRecoveryKitV1(
                current_password=PASSWORD,
                idempotency_key="issue-recovery-kit-0001",
            ),
        )
        assert rotated.recovery_secret and rotated.recovery_secret != registration_secret
        assert rotated.credential_version == 2
        first = await db.get(RecoveryCredentialRecord, credential.credential_id)
        await db.refresh(first)
        assert first is not None and first.revoked_at is not None

        replayed = await service.issue_recovery_kit(
            user=user,
            command=IssueRecoveryKitV1(
                current_password=PASSWORD,
                idempotency_key="issue-recovery-kit-0001",
            ),
        )
        assert replayed.replayed is True
        assert replayed.recovery_secret is None
        receipts = (await db.execute(select(IdentityCommandReceiptRecord))).scalars().all()
        persisted_receipts = json.dumps(
            [receipt.result_payload for receipt in receipts], ensure_ascii=False
        )
        assert registration_secret not in persisted_receipts
        assert rotated.recovery_secret not in persisted_receipts
    await engine.dispose()


@pytest.mark.asyncio
async def test_recovery_consumes_secret_revokes_sessions_and_rotates_credential(
    tmp_path: Path,
) -> None:
    engine, factory = await _database(tmp_path)
    async with factory() as db:
        service = AuthService(db)
        user, secret, first_credential = await service.register_user("13800138001", PASSWORD)
        await service.login_with_phone("13800138001", PASSWORD, "client-instance-0001")
        await service.login_with_phone("13800138001", PASSWORD, "client-instance-0002")

        recovered = await service.recover_password(
            RecoverPasswordV1(
                phone="13800138001",
                recovery_secret=secret,
                new_password=NEW_PASSWORD,
                client_instance="client-instance-recovery",
                idempotency_key="recover-password-0001",
            )
        )
        assert recovered.accepted and recovered.recovery_secret
        assert recovered.recovery_credential_version == 2
        assert user.credential_version == 2
        assert verify_password(NEW_PASSWORD, user.password_hash)
        sessions = await service.repo.list_sessions(user.id)
        assert len(sessions) == 2
        assert all(session.revoke_reason == "account_recovered" for session in sessions)
        assert (await db.get(RecoveryCredentialRecord, first_credential.credential_id)).used_at

        replayed = await service.recover_password(
            RecoverPasswordV1(
                phone="13800138001",
                recovery_secret=secret,
                new_password=NEW_PASSWORD,
                client_instance="client-instance-recovery",
                idempotency_key="recover-password-0001",
            )
        )
        assert replayed.replayed is True
        assert replayed.recovery_secret is None
        receipts = (await db.execute(select(IdentityCommandReceiptRecord))).scalars().all()
        persisted_receipts = json.dumps(
            [receipt.result_payload for receipt in receipts], ensure_ascii=False
        )
        assert secret not in persisted_receipts
        assert recovered.recovery_secret not in persisted_receipts

        with pytest.raises(AuthRecoveryInvalidError):
            await service.recover_password(
                RecoverPasswordV1(
                    phone="13800138001",
                    recovery_secret=secret,
                    new_password="另一个足够长的恢复密码 2026",
                    client_instance="client-instance-recovery",
                    idempotency_key="recover-password-0002",
                )
            )
    await engine.dispose()


@pytest.mark.asyncio
async def test_known_and_unknown_invalid_recovery_return_the_same_error(tmp_path: Path) -> None:
    engine, factory = await _database(tmp_path)
    async with factory() as db:
        service = AuthService(db)
        await service.register_user("13800138001", PASSWORD)
        failures = []
        for phone in ("13800138001", "13900139009"):
            with pytest.raises(AuthRecoveryInvalidError) as failure:
                await service.recover_password(
                    RecoverPasswordV1(
                        phone=phone,
                        recovery_secret="invalid-recovery-secret-same-path",
                        new_password=NEW_PASSWORD,
                        client_instance="client-instance-invalid",
                        idempotency_key=f"invalid-recovery-{phone}",
                    )
                )
            failures.append(failure.value)

        assert failures[0].error_code == failures[1].error_code
        assert failures[0].message == failures[1].message
    await engine.dispose()


@pytest.mark.asyncio
async def test_login_and_current_password_throttles_survive_restart(tmp_path: Path) -> None:
    engine, factory = await _database(tmp_path)
    async with factory() as db:
        service = AuthService(db)
        user, _, _ = await service.register_user("13800138001", PASSWORD)
        for attempt in range(4):
            with pytest.raises(InvalidTokenError):
                await service.login_with_phone("13800138001", f"wrong-login-password-{attempt}")
            with pytest.raises(CurrentPasswordInvalidError):
                await service.issue_recovery_kit(
                    user=user,
                    command=IssueRecoveryKitV1(
                        current_password=f"wrong-current-password-{attempt}",
                        idempotency_key=f"wrong-current-key-{attempt:04d}",
                    ),
                )

        with pytest.raises(AuthRecoveryRateLimitedError):
            await service.login_with_phone("13800138001", "wrong-login-password-final")
        with pytest.raises(AuthRecoveryRateLimitedError):
            await service.issue_recovery_kit(
                user=user,
                command=IssueRecoveryKitV1(
                    current_password="wrong-current-password-final",
                    idempotency_key="wrong-current-key-final",
                ),
            )

    async with factory() as restarted_db:
        restarted = AuthService(restarted_db)
        restarted_user = (
            await restarted_db.execute(select(User).where(User.phone_hash.is_not(None)))
        ).scalar_one()
        with pytest.raises(AuthRecoveryRateLimitedError):
            await restarted.login_with_phone("13800138001", PASSWORD)
        with pytest.raises(AuthRecoveryRateLimitedError):
            await restarted.issue_recovery_kit(
                user=restarted_user,
                command=IssueRecoveryKitV1(
                    current_password=PASSWORD,
                    idempotency_key="current-password-after-restart",
                ),
            )
    await engine.dispose()


@pytest.mark.asyncio
async def test_unknown_and_known_invalid_recovery_share_durable_throttle_path(
    tmp_path: Path,
) -> None:
    engine, factory = await _database(tmp_path)
    async with factory() as db:
        service = AuthService(db)
        await service.register_user("13800138001", PASSWORD)
        credential_lookup = AsyncMock(return_value=None)
        service.repo.get_active_recovery_credential = credential_lookup
        for attempt in range(4):
            with pytest.raises(AuthRecoveryInvalidError):
                await service.recover_password(
                    RecoverPasswordV1(
                        phone="13900139009",
                        recovery_secret=f"invalid-recovery-secret-{attempt:04d}",
                        new_password=NEW_PASSWORD,
                        client_instance="client-instance-unknown",
                        idempotency_key=f"unknown-recovery-{attempt:04d}",
                    )
                )
        with pytest.raises(AuthRecoveryRateLimitedError):
            await service.recover_password(
                RecoverPasswordV1(
                    phone="13900139009",
                    recovery_secret="invalid-recovery-secret-0004",
                    new_password=NEW_PASSWORD,
                    client_instance="client-instance-unknown",
                    idempotency_key="unknown-recovery-0004",
                )
            )
        assert credential_lookup.await_count == 5

    async with factory() as restarted_db:
        with pytest.raises(AuthRecoveryRateLimitedError):
            await AuthService(restarted_db).recover_password(
                RecoverPasswordV1(
                    phone="13900139009",
                    recovery_secret="invalid-recovery-secret-after-restart",
                    new_password=NEW_PASSWORD,
                    client_instance="client-instance-unknown",
                    idempotency_key="unknown-recovery-after-restart",
                )
            )
        rows = (await restarted_db.execute(select(RecoveryThrottleRecord))).scalars().all()
        assert len(rows) == 1 and rows[0].failure_count == 5
    await engine.dispose()


@pytest.mark.asyncio
async def test_concurrent_recovery_failures_are_counted_without_bypass(tmp_path: Path) -> None:
    engine, factory = await _database(tmp_path)

    async def fail_once(attempt: int) -> type[Exception]:
        async with factory() as db:
            try:
                await AuthService(db).recover_password(
                    RecoverPasswordV1(
                        phone="13900139008",
                        recovery_secret=f"parallel-invalid-secret-{attempt:04d}",
                        new_password=NEW_PASSWORD,
                        client_instance="parallel-client-instance",
                        idempotency_key=f"parallel-recovery-{attempt:04d}",
                    )
                )
            except (AuthRecoveryInvalidError, AuthRecoveryRateLimitedError) as exc:
                return type(exc)
        raise AssertionError("invalid recovery unexpectedly succeeded")

    failures = await asyncio.gather(*(fail_once(attempt) for attempt in range(5)))
    assert failures.count(AuthRecoveryInvalidError) == 4
    assert failures.count(AuthRecoveryRateLimitedError) == 1

    async with factory() as db:
        throttle = (
            await db.execute(
                select(RecoveryThrottleRecord).where(RecoveryThrottleRecord.action == "recovery")
            )
        ).scalar_one()
        assert throttle.failure_count == 5
        assert throttle.locked_until is not None
    await engine.dispose()

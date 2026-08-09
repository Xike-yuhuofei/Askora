"""EXEC034 durable Identity session integration tests with real SQLite."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.contracts.identity import ChangePasswordV1
from app.core.exceptions import (
    AuthSessionNotFoundError,
    AuthSessionRevokedError,
    RefreshReplayDetectedError,
    TooManySessionsError,
)
from app.models.identity import (
    AuthSessionRecord,
    IdentityCommandReceiptRecord,
    RecoveryCredentialRecord,
    RecoveryThrottleRecord,
)
from app.models.user import User, UserRole, UserStatus
from app.services.auth.auth_service import MAX_SESSIONS, AuthService
from app.services.auth.token_service import TokenService, hash_password, verify_password

PASSWORD = "correct horse battery staple"
NEW_PASSWORD = "新的 Askora 密码 足够长 2026"


async def _database(tmp_path: Path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'identity.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(User.__table__.create)
        await connection.run_sync(AuthSessionRecord.__table__.create)
        await connection.run_sync(IdentityCommandReceiptRecord.__table__.create)
        await connection.run_sync(RecoveryCredentialRecord.__table__.create)
        await connection.run_sync(RecoveryThrottleRecord.__table__.create)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    return engine, factory


async def _add_user(factory, *, suffix: str = "1") -> User:
    async with factory() as db:
        user = User(
            id=f"00000000-0000-0000-0000-00000000000{suffix}",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            phone_encrypted=f"encrypted-{suffix}",
            phone_hash=AuthService._phone_lookup_hash(f"1380013800{suffix}"),
            password_hash=hash_password(PASSWORD),
            credential_version=1,
            pseudonym_id=f"pseudonym-{suffix}",
        )
        db.add(user)
        await db.commit()
        return user


@pytest.mark.asyncio
async def test_login_refresh_replay_revokes_durable_family(tmp_path: Path) -> None:
    engine, factory = await _database(tmp_path)
    await _add_user(factory)
    async with factory() as db:
        service = AuthService(db)
        access, refresh, _, _ = await service.login_with_phone(
            "13800138001", PASSWORD, "client-instance-0001"
        )
        access_payload = TokenService.decode_token(access, token_type="access")
        assert {"sid", "fam", "cv", "sv"}.issubset(access_payload)
        assert await service.validate_token_and_get_user(access, "client-instance-0001")

        next_access, next_refresh, _ = await service.refresh_tokens(refresh, "client-instance-0001")
        assert TokenService.decode_token(next_access, token_type="access")["sv"] == 2
        assert next_refresh != refresh

        with pytest.raises(RefreshReplayDetectedError):
            await service.refresh_tokens(refresh, "client-instance-0001")
        with pytest.raises(AuthSessionRevokedError):
            await service.validate_token_and_get_user(next_access, "client-instance-0001")

        session = await service.repo.get_session(access_payload["sid"])
        assert session is not None and session.revoke_reason == "refresh_replay"
        assert (
            session.current_refresh_jti_digest
            != TokenService.decode_token(next_refresh, token_type="refresh")["jti"]
        )
    await engine.dispose()


@pytest.mark.asyncio
async def test_change_password_rotates_current_and_revokes_other_sessions(tmp_path: Path) -> None:
    engine, factory = await _database(tmp_path)
    await _add_user(factory)
    async with factory() as db:
        service = AuthService(db)
        access_one, refresh_one, _, current_user = await service.login_with_phone(
            "13800138001", PASSWORD, "client-instance-0001"
        )
        access_two, _, _, _ = await service.login_with_phone(
            "13800138001", PASSWORD, "client-instance-0002"
        )
        payload_one = TokenService.decode_token(access_one, token_type="access")

        result = await service.change_password(
            user=current_user,
            payload=payload_one,
            command=ChangePasswordV1(
                current_password=PASSWORD,
                new_password=NEW_PASSWORD,
                idempotency_key="change-password-0001",
                current_session_version=1,
            ),
        )
        assert result.changed and result.tokens is not None
        assert result.revoked_other_sessions == 1
        assert result.session_version == 2
        assert verify_password(NEW_PASSWORD, current_user.password_hash)
        assert current_user.password_hash.startswith("$argon2id$")

        with pytest.raises(AuthSessionRevokedError):
            await service.validate_token_and_get_user(access_two, "client-instance-0002")
        with pytest.raises(AuthSessionRevokedError):
            await service.refresh_tokens(refresh_one, "client-instance-0001")
        assert await service.validate_token_and_get_user(
            result.tokens.access_token, "client-instance-0001"
        )
    await engine.dispose()


@pytest.mark.asyncio
async def test_session_limit_uses_database_and_cross_user_revoke_is_not_enumerable(
    tmp_path: Path,
) -> None:
    engine, factory = await _database(tmp_path)
    user_one = await _add_user(factory, suffix="1")
    user_two = await _add_user(factory, suffix="2")
    async with factory() as db:
        service = AuthService(db)
        for index in range(MAX_SESSIONS):
            await service.login_with_phone("13800138001", PASSWORD, f"client-instance-{index:04d}")
        with pytest.raises(TooManySessionsError):
            await service.login_with_phone("13800138001", PASSWORD, "client-instance-over-limit")

        access_two, _, _, _ = await service.login_with_phone(
            "13800138002", PASSWORD, "client-instance-user-two"
        )
        session_two = TokenService.decode_token(access_two, token_type="access")["sid"]
        with pytest.raises(AuthSessionNotFoundError):
            await service.revoke_session(
                user_id=user_one.id,
                target_session_id=session_two,
                idempotency_key="cross-user-revoke-0001",
            )
        assert (await service.repo.get_session(session_two)).user_id == user_two.id
    await engine.dispose()


@pytest.mark.asyncio
async def test_concurrent_refresh_allows_at_most_one_and_revokes_family(tmp_path: Path) -> None:
    engine, factory = await _database(tmp_path)
    await _add_user(factory)
    async with factory() as setup_db:
        _, refresh, _, _ = await AuthService(setup_db).login_with_phone(
            "13800138001", PASSWORD, "client-instance-0001"
        )

    async def rotate_once():
        async with factory() as db:
            return await AuthService(db).refresh_tokens(refresh, "client-instance-0001")

    results = await asyncio.gather(rotate_once(), rotate_once(), return_exceptions=True)
    successes = [result for result in results if not isinstance(result, Exception)]
    failures = [result for result in results if isinstance(result, Exception)]
    assert len(successes) <= 1
    assert failures
    assert any(isinstance(result, RefreshReplayDetectedError) for result in failures)
    await engine.dispose()

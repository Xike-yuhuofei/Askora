"""认证阻断项的回归测试。"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app.api.v1.auth import PhoneLoginRequest, RegisterRequest, get_me
from app.core.exceptions import DeviceMismatchError, TooManySessionsError
from app.models.user import User, UserRole, UserStatus
from app.services.auth.auth_service import MAX_SESSIONS, AuthService
from app.services.auth.token_service import TokenService, hash_password, verify_password


class FakeDB:
    def __init__(self, user=None):
        self.user = user
        self.commit = AsyncMock()

    async def get(self, _model, _user_id):
        return self.user


def make_user(**overrides):
    values = {
        "id": "user-1",
        "role": UserRole.USER,
        "status": UserStatus.ACTIVE,
        "pseudonym_id": "pseudonym-1",
        "is_verified": False,
        "nickname": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_auth_requests_reject_invalid_phone_and_short_password():
    with pytest.raises(ValidationError):
        PhoneLoginRequest(phone="123", password="short")
    with pytest.raises(ValidationError):
        RegisterRequest(phone="13800138000", password="1234567")


@pytest.mark.asyncio
async def test_private_user_nickname_is_mapped_and_returned_by_me():
    assert User.__table__.c.nickname.type.length == 64
    payload = await get_me(make_user(nickname="私人昵称"))
    assert payload["nickname"] == "私人昵称"


def test_bcrypt_compatible_hash_round_trip_and_byte_limit():
    password = "test-password-123"
    hashed = hash_password(password)
    assert verify_password(password, hashed)
    assert not verify_password("wrong-password", hashed)

    with pytest.raises(ValidationError):
        RegisterRequest(phone="13800138000", password="密" * 25)
    with pytest.raises(ValueError, match="72 字节"):
        hash_password("密" * 25)


def test_refresh_token_contains_identity_claims():
    token, _, _ = TokenService.create_refresh_token(
        user_id="user-1",
        role="user",
        pseudonym_id="pseudonym-1",
    )
    payload = TokenService.decode_token(token, token_type="refresh")
    assert payload["role"] == "user"
    assert payload["pseudonym_id"] == "pseudonym-1"


@pytest.mark.asyncio
async def test_device_bound_access_token_rejects_other_device(monkeypatch):
    user = make_user()
    service = AuthService(FakeDB(user))
    bound_hash = service._hash_device_fingerprint("trusted-device")
    token, _, _ = TokenService.create_access_token(
        user_id=user.id,
        role=user.role.value,
        pseudonym_id=user.pseudonym_id,
        device_fingerprint=bound_hash,
    )
    monkeypatch.setattr(TokenService, "is_token_revoked", AsyncMock(return_value=False))

    with pytest.raises(DeviceMismatchError):
        await service.validate_token_and_get_user(token, "other-device")


@pytest.mark.asyncio
async def test_refresh_reads_current_identity_from_database(monkeypatch):
    user = make_user(pseudonym_id="current-pseudonym")
    service = AuthService(FakeDB(user))
    refresh_token, _, _ = TokenService.create_refresh_token(
        user_id=user.id,
        role="stale-role",
        pseudonym_id="stale-pseudonym",
    )
    consume = AsyncMock()
    monkeypatch.setattr(TokenService, "consume_refresh_token", consume)

    access_token, _, _ = await service.refresh_tokens(refresh_token)
    payload = TokenService.decode_token(access_token, token_type="access")

    consume.assert_awaited_once()
    assert payload["role"] == UserRole.USER.value
    assert payload["pseudonym_id"] == "current-pseudonym"


@pytest.mark.asyncio
async def test_session_limit_is_not_swallowed(monkeypatch):
    redis = SimpleNamespace(
        zremrangebyscore=AsyncMock(),
        zcard=AsyncMock(return_value=MAX_SESSIONS),
    )
    monkeypatch.setattr(
        "app.services.auth.auth_service.get_redis_client",
        lambda: redis,
    )

    with pytest.raises(TooManySessionsError):
        await AuthService(FakeDB())._check_session_limit(make_user())


@pytest.mark.asyncio
async def test_optional_redis_outage_uses_fast_local_auth_fallback(monkeypatch):
    def unexpected_redis_call():
        raise AssertionError("已知不可用时不应再次连接 Redis")

    monkeypatch.setattr("app.services.auth.auth_service.is_redis_available", lambda: False)
    monkeypatch.setattr("app.services.auth.auth_service.get_redis_client", unexpected_redis_call)
    monkeypatch.setattr("app.services.auth.token_service.is_redis_available", lambda: False)
    monkeypatch.setattr("app.services.auth.token_service.get_redis_client", unexpected_redis_call)

    service = AuthService(FakeDB())
    await service._check_session_limit(make_user())
    await service._register_session("user-1", "session-1", None)

    assert await TokenService.is_token_revoked("local-only-jti") is False
    await TokenService.revoke_token("local-only-jti", 60)
    assert await TokenService.is_token_revoked("local-only-jti") is True

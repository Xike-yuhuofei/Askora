"""Authentication security regression tests after durable-session cutover."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.api.v1.auth import PhoneLoginRequest, RegisterRequest, get_me
from app.core.exceptions import AuthSessionRequiredError
from app.models.user import User, UserRole, UserStatus
from app.services.auth.auth_service import AuthService
from app.services.auth.token_service import TokenService, hash_password, verify_password


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


def test_auth_requests_keep_legacy_login_but_enforce_v2_on_new_registration() -> None:
    with pytest.raises(ValidationError):
        PhoneLoginRequest(phone="123", password="legacy-password")
    assert PhoneLoginRequest(phone="13800138000", password="old-pass").password == "old-pass"
    with pytest.raises(ValidationError):
        RegisterRequest(phone="13800138000", password="short-password")
    assert RegisterRequest(
        phone="13800138000", password="correct horse battery staple"
    ).password


@pytest.mark.asyncio
async def test_private_user_nickname_is_mapped_and_returned_by_me() -> None:
    assert User.__table__.c.nickname.type.length == 64
    payload = await get_me(make_user(nickname="私人昵称"))
    assert payload["nickname"] == "私人昵称"


def test_argon2id_hash_round_trip_has_no_bcrypt_72_byte_truncation() -> None:
    password = "密" * 40 + " Askora"
    hashed = hash_password(password)
    assert hashed.startswith("$argon2id$")
    assert verify_password(password, hashed)
    assert not verify_password("wrong-password", hashed)
    with pytest.raises(ValueError, match="128"):
        hash_password("密" * 129)


def test_bound_tokens_contain_durable_identity_claims() -> None:
    token, _, _ = TokenService.create_refresh_token(
        user_id="user-1",
        role="user",
        pseudonym_id="pseudonym-1",
        session_id="session-1",
        token_family_id="family-1",
        credential_version=3,
        session_version=7,
    )
    payload = TokenService.decode_token(token, token_type="refresh")
    assert payload["sid"] == "session-1"
    assert payload["fam"] == "family-1"
    assert payload["cv"] == 3
    assert payload["sv"] == 7


def test_legacy_refresh_cutover_requires_explicit_relogin() -> None:
    token, _, _ = TokenService.create_refresh_token(
        user_id="user-1",
        role="user",
        pseudonym_id="pseudonym-1",
    )
    payload = TokenService.decode_token(token, token_type="refresh")
    with pytest.raises(AuthSessionRequiredError) as error:
        AuthService._required_session_claims(AuthService.__new__(AuthService), payload)
    assert error.value.error_code == "AUTH_SESSION_REQUIRED"

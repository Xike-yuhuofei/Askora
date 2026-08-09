"""EXEC034 security boundaries for credentials and durable sessions."""

from __future__ import annotations

import pytest
from passlib.context import CryptContext

from app.core.exceptions import AuthSessionRequiredError
from app.services.auth.auth_service import AuthService
from app.services.auth.token_service import (
    TokenService,
    hash_password,
    validate_new_password,
    verify_and_update_password,
)


def test_argon2id_accepts_long_unicode_and_bcrypt_is_read_rehash_only() -> None:
    password = "密" * 40 + " Askora"
    validate_new_password(password)
    encoded = hash_password(password)
    assert encoded.startswith("$argon2id$")

    legacy = CryptContext(schemes=["bcrypt"]).hash("legacy-password-123")
    verified, replacement = verify_and_update_password("legacy-password-123", legacy)
    assert verified is True
    assert replacement is not None and replacement.startswith("$argon2id$")


def test_legacy_token_without_durable_session_claims_fails_closed() -> None:
    token, _, _ = TokenService.create_access_token(
        user_id="user-1",
        role="user",
        pseudonym_id="pseudonym-1",
    )
    payload = TokenService.decode_token(token, token_type="access")
    with pytest.raises(AuthSessionRequiredError):
        AuthService._required_session_claims(AuthService.__new__(AuthService), payload)


def test_session_secret_digest_is_keyed_and_not_plaintext() -> None:
    secret = "refresh-jti-visible-only-in-token"
    digest = AuthService._digest_secret(secret)
    assert digest != secret
    assert len(digest) == 64
    assert AuthService._digest_secret(secret) == digest

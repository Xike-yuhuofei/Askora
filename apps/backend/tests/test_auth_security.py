"""Security regression tests for password hashing utilities.

EXEC-053: Removed JWT/session tests (no-auth single-user architecture).
Retained: password hash verification tests (tool-level, not auth-level).
"""

from __future__ import annotations

import pytest

from app.services.auth.token_service import hash_password, verify_password


def test_argon2id_hash_round_trip_has_no_bcrypt_72_byte_truncation() -> None:
    """Verify argon2id hashing handles multi-byte characters correctly."""
    password = "密" * 40 + " Askora"
    hashed = hash_password(password)
    assert hashed.startswith("$argon2id$")
    assert verify_password(password, hashed)
    assert not verify_password("wrong-password", hashed)
    with pytest.raises(ValueError, match="128"):
        hash_password("密" * 129)


def test_hash_output_is_not_plaintext() -> None:
    """Verify hash output never equals plaintext (non-deterministic due to salt)."""
    password = "test-password-2026"
    hash1 = hash_password(password)
    # Hash should not equal password
    assert hash1 != password
    # Hash should start with argon2id prefix
    assert hash1.startswith("$argon2id$")


def test_hash_never_exposes_plaintext() -> None:
    """Verify hash output never contains the plaintext password."""
    password = "super-secret-password-2026"
    hashed = hash_password(password)
    assert password not in hashed


def test_verify_password_fails_on_empty_input() -> None:
    """Verify empty password verification fails safely."""
    hashed = hash_password("real-password")
    assert not verify_password("", hashed)

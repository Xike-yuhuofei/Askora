"""EXEC034 strict Identity v1 public contract tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.contracts.identity import ChangePasswordV1, RecoverPasswordV1, RevokeSessionV1


def test_change_password_contract_is_strict_versioned_and_forbids_extras() -> None:
    command = ChangePasswordV1(
        current_password="legacy-password",
        new_password="这是一个足够长的新密码 Askora 2026",
        idempotency_key="idempotency-key-0001",
        current_session_version=1,
    )
    assert command.schema_version == "1.0"

    with pytest.raises(ValidationError):
        ChangePasswordV1.model_validate(
            {
                **command.model_dump(),
                "schema_version": "2.0",
            }
        )
    with pytest.raises(ValidationError):
        ChangePasswordV1.model_validate({**command.model_dump(), "unexpected": True})
    with pytest.raises(ValidationError):
        ChangePasswordV1(
            current_password="legacy-password",
            new_password="too-short",
            idempotency_key="idempotency-key-0002",
            current_session_version=1,
        )


def test_session_command_requires_bounded_idempotency_key() -> None:
    with pytest.raises(ValidationError):
        RevokeSessionV1(idempotency_key="short")
    assert RevokeSessionV1(idempotency_key="session-command-001").schema_version == "1.0"


def test_recover_password_contract_requires_strict_v1_and_high_entropy_secret_shape() -> None:
    command = RecoverPasswordV1(
        phone="13800138000",
        recovery_secret="recovery-secret-at-least-128-bits",
        new_password="新的恢复密码必须足够长 2026",
        client_instance="askora-client-instance",
        idempotency_key="recover-password-0001",
    )
    assert command.schema_version == "1.0"
    with pytest.raises(ValidationError):
        RecoverPasswordV1.model_validate({**command.model_dump(), "recovery_secret": "short"})

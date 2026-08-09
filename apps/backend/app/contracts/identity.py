"""Strict public v1 contracts for the Identity platform boundary."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class IdentityContract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


def _validate_new_password(value: str) -> str:
    if not 15 <= len(value) <= 128:
        raise ValueError("新密码必须为 15～128 个 Unicode 字符")
    return value


class ChangePasswordV1(IdentityContract):
    schema_version: Literal["1.0"] = "1.0"
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=15, max_length=128)
    idempotency_key: str = Field(min_length=16, max_length=128)
    current_session_version: int = Field(gt=0)

    _new_password_policy = field_validator("new_password")(_validate_new_password)


class RevokeSessionV1(IdentityContract):
    schema_version: Literal["1.0"] = "1.0"
    idempotency_key: str = Field(min_length=16, max_length=128)


class RevokeOtherSessionsV1(IdentityContract):
    schema_version: Literal["1.0"] = "1.0"
    idempotency_key: str = Field(min_length=16, max_length=128)


class AuthSessionV1(IdentityContract):
    schema_version: Literal["1.0"] = "1.0"
    session_id: str
    version: int
    client_label: str
    current: bool
    created_at: datetime
    last_seen_at: datetime
    refresh_expires_at: datetime
    revoked: bool


class SessionListV1(IdentityContract):
    schema_version: Literal["1.0"] = "1.0"
    sessions: tuple[AuthSessionV1, ...]


class TokenPairV1(IdentityContract):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = Field(ge=0)


class ChangePasswordResultV1(IdentityContract):
    schema_version: Literal["1.0"] = "1.0"
    changed: bool
    replayed: bool
    session_id: str
    session_version: int
    revoked_other_sessions: int
    tokens: TokenPairV1 | None
    recovery_action: str | None = None


class SessionCommandResultV1(IdentityContract):
    schema_version: Literal["1.0"] = "1.0"
    success: bool
    replayed: bool
    revoked_sessions: int

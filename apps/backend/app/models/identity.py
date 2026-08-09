"""Identity-owned durable credential and session state."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuthSessionRecord(Base):
    """Durable truth for one Askora App-instance login session."""

    __tablename__ = "auth_sessions"

    session_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    token_family_id: Mapped[str] = mapped_column(String(36), nullable=False)
    current_refresh_jti_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    client_instance_digest: Mapped[str | None] = mapped_column(String(64), nullable=True)
    client_label: Mapped[str] = mapped_column(String(128), nullable=False)
    credential_version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    refresh_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoke_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)

    __table_args__ = (
        UniqueConstraint("token_family_id", name="uq_auth_sessions_token_family"),
        CheckConstraint("version > 0", name="ck_auth_sessions_version_positive"),
        CheckConstraint(
            "credential_version > 0", name="ck_auth_sessions_credential_version_positive"
        ),
        Index(
            "ix_auth_sessions_user_active",
            "user_id",
            "revoked_at",
            "refresh_expires_at",
        ),
    )


class IdentityCommandReceiptRecord(Base):
    """Durable idempotency receipt without passwords or token material."""

    __tablename__ = "identity_command_receipts"

    receipt_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    command_type: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    request_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    result_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "command_type",
            "idempotency_key_digest",
            name="uq_identity_command_receipt_key",
        ),
        Index("ix_identity_command_receipts_user_created", "user_id", "created_at"),
    )


class RecoveryCredentialRecord(Base):
    """One versioned recovery secret; only a keyed digest is persisted."""

    __tablename__ = "recovery_credentials"

    credential_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    secret_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "version", name="uq_recovery_credentials_user_version"),
        CheckConstraint("version > 0", name="ck_recovery_credentials_version_positive"),
        Index("ix_recovery_credentials_user_created", "user_id", "created_at"),
    )


class RecoveryThrottleRecord(Base):
    """Durable bounded throttling for both known and unknown identifiers."""

    __tablename__ = "recovery_throttles"

    subject_digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    action: Mapped[str] = mapped_column(String(32), primary_key=True)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("failure_count >= 0", name="ck_recovery_throttles_failure_nonnegative"),
    )

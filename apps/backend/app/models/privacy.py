"""Privacy-owned durable deletion governance records (PERSIST-081..083)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AccountDeletionPreviewRecord(Base):
    __tablename__ = "account_deletion_previews"

    preview_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(100), nullable=False)
    subject_digest: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    manifest_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    data_fingerprint: Mapped[str] = mapped_column(String(71), nullable=False)
    manifest_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    preview_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_by_request_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (Index("ix_account_deletion_previews_user_expiry", "user_id", "expires_at"),)


class AccountDeletionRequestRecord(Base):
    __tablename__ = "account_deletion_requests"

    request_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    preview_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(100), nullable=False)
    subject_digest: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    lifecycle: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    manifest_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    manifest_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    idempotency_key_digest: Mapped[str | None] = mapped_column(String(64), nullable=True)
    request_digest: Mapped[str | None] = mapped_column(String(64), nullable=True)
    control_token_digest: Mapped[str | None] = mapped_column(String(64), nullable=True)
    cancel_idempotency_key_digest: Mapped[str | None] = mapped_column(String(64), nullable=True)
    retry_idempotency_key_digest: Mapped[str | None] = mapped_column(String(64), nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    purge_due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    purge_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_step: Mapped[str | None] = mapped_column(String(50), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    blocking_issues: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "subject_digest", "idempotency_key_digest", name="uq_account_deletion_request_key"
        ),
        CheckConstraint("retry_count >= 0", name="ck_account_deletion_retry_nonnegative"),
        CheckConstraint(
            "lifecycle IN ('deletion_pending', 'purging', 'deletion_blocked', 'deleted', "
            "'cancelled')",
            name="ck_account_deletion_lifecycle",
        ),
        Index("ix_account_deletion_requests_due", "lifecycle", "purge_due_at"),
    )


class OwnerErasureStepReceiptRecord(Base):
    __tablename__ = "owner_erasure_step_receipts"

    receipt_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    owner: Mapped[str] = mapped_column(String(20), nullable=False)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False)
    requested_count: Mapped[int] = mapped_column(Integer, nullable=False)
    deleted_count: Mapped[int] = mapped_column(Integer, nullable=False)
    missing_count: Mapped[int] = mapped_column(Integer, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False)
    manifest_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    receipt_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("request_id", "owner", "attempt", name="uq_owner_erasure_attempt"),
        CheckConstraint("attempt > 0", name="ck_owner_erasure_attempt_positive"),
        CheckConstraint(
            "requested_count >= 0 AND deleted_count >= 0 AND missing_count >= 0 "
            "AND error_count >= 0",
            name="ck_owner_erasure_counts_nonnegative",
        ),
    )


class PrivacyTombstoneRecord(Base):
    __tablename__ = "privacy_tombstones"

    request_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(100), nullable=False)
    subject_digest: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    manifest_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    receipts_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    restore_barrier_digest: Mapped[str] = mapped_column(String(71), nullable=False)
    final_status: Mapped[str] = mapped_column(String(20), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (UniqueConstraint("subject_digest", name="uq_privacy_tombstone_subject"),)

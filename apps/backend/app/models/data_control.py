"""P1-03 durable erasure orchestration and content-free tombstones."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DataErasureWorkflowRecord(Base):
    __tablename__ = "data_erasure_workflows"

    workflow_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    user_ref: Mapped[str] = mapped_column(String(100), index=True)
    scope: Mapped[str] = mapped_column(String(40), index=True)
    target_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_ref_hash: Mapped[str] = mapped_column(String(64))
    idempotency_key: Mapped[str] = mapped_column(String(200))
    request_digest: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(40), index=True)
    checkpoint: Mapped[int | None] = mapped_column(Integer, nullable=True)
    report: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("user_ref", "idempotency_key", name="uq_erasure_user_idempotency"),
        Index("ix_erasure_workflow_status_updated", "status", "updated_at"),
    )


class DataErasureStepRecord(Base):
    __tablename__ = "data_erasure_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workflow_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("data_erasure_workflows.workflow_id", ondelete="CASCADE"),
        index=True,
    )
    owner_system: Mapped[str] = mapped_column(String(50))
    ordinal: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(40), index=True)
    affected_records: Mapped[int] = mapped_column(Integer, default=0)
    reason_codes: Mapped[list[str]] = mapped_column(JSON, default=list)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("workflow_id", "owner_system", name="uq_erasure_step_owner"),
    )


class DataErasureReceiptRecord(Base):
    __tablename__ = "data_erasure_receipts"

    receipt_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workflow_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("data_erasure_workflows.workflow_id", ondelete="RESTRICT"),
        unique=True,
    )
    user_ref: Mapped[str] = mapped_column(String(100), index=True)
    scope: Mapped[str] = mapped_column(String(40), index=True)
    target_ref_hash: Mapped[str] = mapped_column(String(64))
    checkpoint: Mapped[int] = mapped_column(Integer, unique=True)
    result_digest: Mapped[str] = mapped_column(String(64))
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DataErasureCheckpointRecord(Base):
    __tablename__ = "data_erasure_checkpoints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    checkpoint: Mapped[int] = mapped_column(Integer)
    receipt_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

"""SYS06 P1-01 append-only goal management persistence."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class GoalDefinitionRecord(Base):
    __tablename__ = "learning_goal_definition_versions"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    goal_id: Mapped[str] = mapped_column(String(36), index=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    definition_version: Mapped[int] = mapped_column(Integer)
    semantic_fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint("goal_id", "definition_version", name="uq_goal_definition_version"),
    )


class GoalStateRecord(Base):
    __tablename__ = "learning_goal_state_versions"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    goal_id: Mapped[str] = mapped_column(String(36), index=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    state_version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(24), index=True)
    definition_version: Mapped[int] = mapped_column(Integer)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint("goal_id", "state_version", name="uq_goal_state_version"),)


class GoalPlanStateRecord(Base):
    __tablename__ = "learning_plan_state_versions"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    plan_id: Mapped[str] = mapped_column(String(36), index=True)
    plan_version: Mapped[int] = mapped_column(Integer)
    state_version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(24), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint(
            "plan_id", "plan_version", "state_version", name="uq_goal_plan_state_version"
        ),
    )


class GoalDraftRecord(Base):
    __tablename__ = "learning_goal_draft_versions"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    draft_id: Mapped[str] = mapped_column(String(36), index=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    goal_id: Mapped[str] = mapped_column(String(36), index=True)
    draft_version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(40), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint("draft_id", "draft_version", name="uq_goal_draft_version"),)


class GoalChangePreviewRecord(Base):
    __tablename__ = "goal_change_preview_versions"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    preview_id: Mapped[str] = mapped_column(String(36), index=True)
    preview_version: Mapped[int] = mapped_column(Integer)
    draft_id: Mapped[str] = mapped_column(String(36), index=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint("preview_id", "preview_version", name="uq_goal_preview_version"),
    )


class FocusedGoalStateRecord(Base):
    __tablename__ = "focused_learning_goal_state_versions"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    focus_version: Mapped[int] = mapped_column(Integer)
    goal_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint("user_id", "focus_version", name="uq_goal_focus_version"),)


class GoalManagementCommandReceiptRecord(Base):
    __tablename__ = "goal_management_command_receipts"
    receipt_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36))
    command_type: Mapped[str] = mapped_column(String(60))
    idempotency_key: Mapped[str] = mapped_column(String(200))
    payload_digest: Mapped[str] = mapped_column(String(64))
    response_type: Mapped[str] = mapped_column(String(80))
    response_payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uq_goal_management_user_key"),
        Index("ix_goal_management_receipt_command", "user_id", "command_type"),
    )

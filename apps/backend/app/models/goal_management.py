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


class GoalAchievementPolicyRecord(Base):
    __tablename__ = "goal_achievement_policy_versions"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    policy_id: Mapped[str] = mapped_column(String(36), index=True)
    policy_version: Mapped[int] = mapped_column(Integer)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint("policy_id", "policy_version", name="uq_goal_achievement_policy"),
    )


class GoalObjectiveRecord(Base):
    __tablename__ = "learning_objective_versions"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    objective_id: Mapped[str] = mapped_column(String(36), index=True)
    goal_id: Mapped[str] = mapped_column(String(36), index=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    objective_version: Mapped[int] = mapped_column(Integer)
    criterion_id: Mapped[str] = mapped_column(String(36), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint("objective_id", "objective_version", name="uq_learning_objective_version"),
    )


class GoalAssessmentActivityRecord(Base):
    __tablename__ = "goal_assessment_activity_versions"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    assessment_activity_id: Mapped[str] = mapped_column(String(36), index=True)
    goal_id: Mapped[str] = mapped_column(String(36), index=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    criterion_id: Mapped[str] = mapped_column(String(36), index=True)
    activity_version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(24), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    grader_payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint(
            "assessment_activity_id",
            "activity_version",
            name="uq_goal_assessment_activity_version",
        ),
    )


class GoalAchievementEvaluationRecord(Base):
    __tablename__ = "goal_achievement_evaluation_versions"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    evaluation_id: Mapped[str] = mapped_column(String(36), index=True)
    goal_id: Mapped[str] = mapped_column(String(36), index=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    evaluation_version: Mapped[int] = mapped_column(Integer)
    eligible: Mapped[bool] = mapped_column(index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint(
            "evaluation_id", "evaluation_version", name="uq_goal_achievement_evaluation"
        ),
    )

"""SYS06/SYS07 version stream persistence models。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ReviewObservationRecord(Base):
    __tablename__ = "review_observations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    knowledge_unit_id: Mapped[str] = mapped_column(String(36), index=True)
    actual_reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    payload: Mapped[dict] = mapped_column(JSON)
    invalidated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReviewScheduleRecord(Base):
    __tablename__ = "review_schedule_versions"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    schedule_id: Mapped[str] = mapped_column(String(36), index=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    knowledge_unit_id: Mapped[str] = mapped_column(String(36), index=True)
    version: Mapped[int] = mapped_column(Integer)
    next_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("schedule_id", "version", name="uq_review_schedule_version"),
        Index("idx_review_latest", "user_id", "knowledge_unit_id", "version"),
    )


class LearningPlanRecord(Base):
    __tablename__ = "learning_plan_versions"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    plan_id: Mapped[str] = mapped_column(String(36), index=True)
    learning_goal_id: Mapped[str] = mapped_column(String(36), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), index=True)
    superseded_by_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("plan_id", "version", name="uq_learning_plan_version"),)


class LearningActivityRecord(Base):
    __tablename__ = "learning_activities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    plan_id: Mapped[str] = mapped_column(String(36), index=True)
    plan_version: Mapped[int] = mapped_column(Integer)
    priority: Mapped[float] = mapped_column(Float)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LearningGoalRecord(Base):
    """SYS06 immutable LearningGoal version stream."""

    __tablename__ = "learning_goal_versions"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    goal_id: Mapped[str] = mapped_column(String(36), index=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("goal_id", "version", name="uq_learning_goal_version"),)


class GoalKnowledgeMappingRecord(Base):
    """SYS06 immutable GoalKnowledgeMapping decision version."""

    __tablename__ = "goal_knowledge_mapping_versions"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    mapping_id: Mapped[str] = mapped_column(String(36), index=True)
    goal_id: Mapped[str] = mapped_column(String(36), index=True)
    goal_version: Mapped[int] = mapped_column(Integer)
    mapping_version: Mapped[int] = mapped_column(Integer)
    mapper_version: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("mapping_id", "mapping_version", name="uq_goal_mapping_version"),
    )


class GoalKnowledgeSubgraphRecord(Base):
    """Rebuildable SYS06 projection over exact SYS01 relation refs."""

    __tablename__ = "goal_knowledge_subgraph_versions"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    subgraph_id: Mapped[str] = mapped_column(String(36), index=True)
    mapping_id: Mapped[str] = mapped_column(String(36), index=True)
    version: Mapped[int] = mapped_column(Integer)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("subgraph_id", "version", name="uq_goal_subgraph_version"),)


class GoalFormationInferenceRecord(Base):
    """Persisted bounded goal-formation model result or unavailable outcome."""

    __tablename__ = "goal_formation_inferences"

    inference_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    goal_id: Mapped[str] = mapped_column(String(36), index=True)
    input_digest: Mapped[str] = mapped_column(String(64), index=True)
    provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

"""4.8 所拥有的事件、决策与 durable outbox 持久化模型。"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    event,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ImmutableLedgerError(RuntimeError):
    """尝试修改或删除 append-only ledger row。"""


class LearningEventRecord(Base):
    """EVENT-002：不可变 LearningEvent ledger row。"""

    __tablename__ = "learning_events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(100), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(255), nullable=False)
    aggregate_version: Mapped[int] = mapped_column(Integer, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(36), nullable=False)
    causation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    actor: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    context: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    trace: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    privacy: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    producer_system: Mapped[str | None] = mapped_column(String(20), nullable=True)
    v03_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "aggregate_type",
            "aggregate_id",
            "aggregate_version",
            name="uq_learning_event_aggregate_version",
        ),
        UniqueConstraint("idempotency_key", name="uq_learning_event_idempotency_key"),
        Index(
            "ix_learning_event_aggregate_sequence",
            "aggregate_type",
            "aggregate_id",
            "sequence",
        ),
        Index("ix_learning_event_type_recorded", "event_type", "recorded_at"),
        Index("ix_learning_event_correlation", "correlation_id"),
        Index("ix_learning_event_producer", "producer_system"),
    )


class DecisionTraceRecord(Base):
    """DECISION-090：不可变 DecisionTrace ledger row。"""

    __tablename__ = "decision_traces"

    decision_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    decision_type: Mapped[str] = mapped_column(String(100), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    owner_system: Mapped[str] = mapped_column(String(50), nullable=False)
    inputs: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    candidates: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    selected: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    constraints: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    reason_codes: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    confidence: Mapped[float | None] = mapped_column(nullable=True)
    algorithm: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    algorithm_id: Mapped[str] = mapped_column(String(100), nullable=False)
    algorithm_version: Mapped[str] = mapped_column(String(100), nullable=False)
    experiment: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    experiment_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    decision_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    v03_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    teaching_context_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    policy_bundle_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    behavior_policy_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    action_propensity: Mapped[float | None] = mapped_column(nullable=True)
    experiment_assignment_probability: Mapped[float | None] = mapped_column(nullable=True)
    replayability_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(36), nullable=False)
    trace_id: Mapped[str] = mapped_column(String(255), nullable=False)

    indexed_inputs: Mapped[list["DecisionTraceInputRecord"]] = relationship(
        back_populates="decision",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("ix_decision_trace_type_created", "decision_type", "created_at"),
        Index("ix_decision_trace_owner", "owner_system"),
        Index("ix_decision_trace_correlation", "correlation_id"),
        Index("ix_decision_trace_trace_id", "trace_id"),
        Index("ix_decision_trace_algorithm", "algorithm_id", "algorithm_version"),
        Index("ix_decision_trace_experiment", "experiment_id"),
        Index("ix_decision_trace_context", "teaching_context_id"),
        Index("ix_decision_trace_policy_bundle", "policy_bundle_id"),
        Index("ix_decision_trace_behavior", "behavior_policy_type"),
        Index("ix_decision_trace_replayability", "replayability_status"),
    )


class DecisionTraceInputRecord(Base):
    """DECISION-091：跨 SQLite/PostgreSQL 可查询的 input entity 索引。"""

    __tablename__ = "decision_trace_inputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    decision_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("decision_traces.decision_id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_version: Mapped[str | None] = mapped_column(String(100), nullable=True)

    decision: Mapped[DecisionTraceRecord] = relationship(back_populates="indexed_inputs")

    __table_args__ = (
        Index(
            "ix_decision_input_entity",
            "entity_type",
            "entity_id",
            "entity_version",
        ),
        Index("ix_decision_input_decision", "decision_id"),
    )


class OutboxTaskRecord(Base):
    """PERSIST-022：可恢复、至少一次投递的 durable task。"""

    __tablename__ = "outbox_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_outbox_task_idempotency_key"),
        Index("ix_outbox_status_due", "status", "next_attempt_at", "created_at"),
        Index("ix_outbox_type_status", "type", "status"),
    )


def _reject_ledger_mutation(_mapper: Any, _connection: Any, target: Any) -> None:
    raise ImmutableLedgerError(
        f"{type(target).__name__} is append-only; append a correction record instead"
    )


for _immutable_model in (LearningEventRecord, DecisionTraceRecord, DecisionTraceInputRecord):
    event.listen(_immutable_model, "before_update", _reject_ledger_mutation)
    event.listen(_immutable_model, "before_delete", _reject_ledger_mutation)

"""SYS08 append-only Book Learning transcript projection records."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Index, Integer, String, Text, UniqueConstraint, event, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.ledger import ImmutableLedgerError


class BookLearningTranscriptTurnRecord(Base):
    """Accepted presentation turn; never a learner/plan/assessment truth source."""

    __tablename__ = "book_learning_transcript_turns"

    turn_record_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    goal_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    plan_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    plan_version: Mapped[int] = mapped_column(Integer, nullable=False)
    activity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    turn_id: Mapped[str] = mapped_column(String(200), nullable=False)
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False)
    turn_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(200), nullable=False)
    learner_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "idempotency_key",
            name="uq_book_transcript_user_idempotency",
        ),
        UniqueConstraint(
            "session_id",
            "turn_number",
            name="uq_book_transcript_session_turn_number",
        ),
        UniqueConstraint(
            "session_id",
            "turn_id",
            name="uq_book_transcript_session_turn_id",
        ),
        Index(
            "ix_book_transcript_user_activity_turn",
            "user_id",
            "activity_id",
            "turn_number",
        ),
    )


class BookLearningAdvanceRecord(Base):
    """Idempotent SYS08 workflow receipt for one accepted owner-command advance."""

    __tablename__ = "book_learning_advance_records"

    advance_record_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    document_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(200), nullable=False)
    applied_command: Mapped[str] = mapped_column(String(80), nullable=False)
    response_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "idempotency_key",
            name="uq_book_advance_user_idempotency",
        ),
        Index("ix_book_advance_user_document", "user_id", "document_id"),
    )


def _reject_transcript_mutation(_mapper: Any, _connection: Any, target: Any) -> None:
    raise ImmutableLedgerError(
        f"{type(target).__name__} is immutable; append a new transcript turn"
    )


event.listen(BookLearningTranscriptTurnRecord, "before_update", _reject_transcript_mutation)
event.listen(BookLearningTranscriptTurnRecord, "before_delete", _reject_transcript_mutation)
event.listen(BookLearningAdvanceRecord, "before_update", _reject_transcript_mutation)
event.listen(BookLearningAdvanceRecord, "before_delete", _reject_transcript_mutation)

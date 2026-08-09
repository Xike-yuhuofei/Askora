"""Platform Experience presentation-only onboarding persistence."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class OnboardingPreferenceRecord(Base):
    __tablename__ = "onboarding_preferences"

    preference_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    journey_id: Mapped[str] = mapped_column(String(80))
    preference_version: Mapped[int] = mapped_column(Integer)
    visibility: Mapped[str] = mapped_column(String(20))
    boundary_notice_version_acknowledged: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    dismissed_reason: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("user_id", "journey_id", name="uq_onboarding_preference_user_journey"),
        Index("ix_onboarding_preference_visibility", "user_id", "visibility"),
    )


class OnboardingPreferenceCommandReceiptRecord(Base):
    __tablename__ = "onboarding_preference_command_receipts"

    receipt_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    journey_id: Mapped[str] = mapped_column(String(80))
    idempotency_key: Mapped[str] = mapped_column(String(200))
    command_digest: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(40))
    resulting_preference_version: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "journey_id",
            "idempotency_key",
            name="uq_onboarding_preference_user_idempotency",
        ),
    )

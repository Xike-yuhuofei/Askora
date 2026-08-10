"""Canonical local data ownership truth for a single-user Askora instance.

``LocalOwnerRecord`` is the unique durable owner of local learning data. It is
*not* a credential principal: it carries no password, token, recovery secret or
device fingerprint, and it never authenticates a client. Its ``owner_id`` is the
stable subject by which learner-owned services resolve ownership.

Cardinality is enforced to exactly one row via a ``singleton_key`` primary key
guarded by ``CHECK (singleton_key = 1)``.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

#: Only this many rows may ever exist; the PK + CHECK guard make the table a singleton.
SINGLETON_KEY = 1
LOCAL_OWNER_SCHEMA_VERSION = "1.0"


class LocalOwnerRecord(Base):
    """Durable truth for the single canonical local owner of this data store."""

    __tablename__ = "local_owners"

    singleton_key: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    schema_version: Mapped[str] = mapped_column(
        String(20), nullable=False, default=LOCAL_OWNER_SCHEMA_VERSION
    )
    #: Provenance of how the owner was established (fresh / legacy_single_learner).
    provenance: Mapped[str] = mapped_column(String(40), nullable=False, default="fresh")
    #: Optional trace link to the legacy user that was mapped to this owner.
    legacy_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    legacy_pseudonym_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (CheckConstraint("singleton_key = 1", name="ck_local_owners_single_row"),)

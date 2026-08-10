"""SQLAlchemy adapter for the canonical LocalOwner singleton."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.local_owner import (
    LOCAL_OWNER_SCHEMA_VERSION,
    SINGLETON_KEY,
    LocalOwnerRecord,
)
from app.models.user import User, UserStatus


class LocalOwnerRepository:
    """Owns the single-row ``local_owners`` table and the legacy subject scan.

    The write path uses ``INSERT ... ON CONFLICT DO NOTHING`` on the singleton
    primary key so that concurrent ``ensure_local_owner`` calls can never yield
    more than one owner row.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self) -> LocalOwnerRecord | None:
        result = await self.db.execute(select(LocalOwnerRecord))
        return result.scalars().first()

    async def count(self) -> int:
        result = await self.db.execute(select(func.count(LocalOwnerRecord.singleton_key)))
        return int(result.scalar_one())

    async def count_eligible_legacy_subjects(self) -> int:
        """Count non-deleted legacy users that would be real learner subjects."""
        result = await self.db.execute(
            select(func.count(User.id)).where(User.status != UserStatus.DELETED)
        )
        return int(result.scalar_one())

    async def get_single_eligible_legacy_subject(self) -> User | None:
        result = await self.db.execute(
            select(User).where(User.status != UserStatus.DELETED).limit(2)
        )
        rows = list(result.scalars().all())
        if len(rows) != 1:
            return None
        return rows[0]

    async def create_if_absent(
        self,
        *,
        owner_id: str,
        provenance: str,
        legacy_user_id: str | None = None,
        legacy_pseudonym_id: str | None = None,
    ) -> LocalOwnerRecord:
        """Insert the singleton owner row, or return the existing row on conflict."""
        now = datetime.now(timezone.utc)
        values = {
            "singleton_key": SINGLETON_KEY,
            "owner_id": owner_id,
            "schema_version": LOCAL_OWNER_SCHEMA_VERSION,
            "provenance": provenance,
            "legacy_user_id": legacy_user_id,
            "legacy_pseudonym_id": legacy_pseudonym_id,
            "created_at": now,
        }
        dialect = self.db.get_bind().dialect.name
        statement: Any
        if dialect == "postgresql":
            statement = postgresql_insert(LocalOwnerRecord).values(**values)
        elif dialect == "sqlite":
            statement = sqlite_insert(LocalOwnerRecord).values(**values)
        else:
            raise RuntimeError(f"Unsupported local owner dialect: {dialect}")

        statement = statement.on_conflict_do_nothing(index_elements=["singleton_key"])
        await self.db.execute(statement)
        await self.db.flush()
        existing = await self.get()
        if existing is None:
            raise RuntimeError("failed to resolve a LocalOwner after bootstrapping")
        return existing


def format_owner_id(owner_id: UUID) -> str:
    """Render a canonical owner UUID the way learner-owned columns store it."""
    return str(owner_id)

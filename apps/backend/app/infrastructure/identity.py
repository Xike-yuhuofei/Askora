"""SQLAlchemy adapter for Identity-owned durable state."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import AuthSessionRecord, IdentityCommandReceiptRecord


class IdentityRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def active_session_count(self, user_id: str, now: datetime) -> int:
        result = await self.db.execute(
            select(func.count(AuthSessionRecord.session_id)).where(
                AuthSessionRecord.user_id == user_id,
                AuthSessionRecord.revoked_at.is_(None),
                AuthSessionRecord.refresh_expires_at > now,
            )
        )
        return int(result.scalar_one())

    async def add_session(self, session: AuthSessionRecord) -> None:
        self.db.add(session)
        await self.db.flush()

    async def get_session(self, session_id: str) -> AuthSessionRecord | None:
        return await self.db.get(AuthSessionRecord, session_id)

    async def list_sessions(self, user_id: str) -> list[AuthSessionRecord]:
        result = await self.db.execute(
            select(AuthSessionRecord)
            .where(AuthSessionRecord.user_id == user_id)
            .order_by(AuthSessionRecord.created_at.desc(), AuthSessionRecord.session_id.asc())
        )
        return list(result.scalars().all())

    async def rotate_refresh_compare_and_swap(
        self,
        *,
        session_id: str,
        user_id: str,
        family_id: str,
        credential_version: int,
        expected_version: int,
        expected_jti_digest: str,
        next_jti_digest: str,
        next_refresh_expires_at: datetime,
        now: datetime,
    ) -> bool:
        result = await self.db.execute(
            update(AuthSessionRecord)
            .where(
                AuthSessionRecord.session_id == session_id,
                AuthSessionRecord.user_id == user_id,
                AuthSessionRecord.token_family_id == family_id,
                AuthSessionRecord.credential_version == credential_version,
                AuthSessionRecord.version == expected_version,
                AuthSessionRecord.current_refresh_jti_digest == expected_jti_digest,
                AuthSessionRecord.revoked_at.is_(None),
                AuthSessionRecord.refresh_expires_at > now,
            )
            .values(
                version=AuthSessionRecord.version + 1,
                current_refresh_jti_digest=next_jti_digest,
                refresh_expires_at=next_refresh_expires_at,
                last_seen_at=now,
            )
            .execution_options(synchronize_session=False)
        )
        return int(getattr(result, "rowcount", 0) or 0) == 1

    async def revoke_session(
        self,
        *,
        session_id: str,
        user_id: str,
        now: datetime,
        reason: str,
    ) -> int:
        result = await self.db.execute(
            update(AuthSessionRecord)
            .where(
                AuthSessionRecord.session_id == session_id,
                AuthSessionRecord.user_id == user_id,
                AuthSessionRecord.revoked_at.is_(None),
            )
            .values(revoked_at=now, revoke_reason=reason, last_seen_at=now)
            .execution_options(synchronize_session=False)
        )
        return int(getattr(result, "rowcount", 0) or 0)

    async def revoke_other_sessions(
        self,
        *,
        user_id: str,
        current_session_id: str,
        now: datetime,
        reason: str,
    ) -> int:
        result = await self.db.execute(
            update(AuthSessionRecord)
            .where(
                AuthSessionRecord.user_id == user_id,
                AuthSessionRecord.session_id != current_session_id,
                AuthSessionRecord.revoked_at.is_(None),
            )
            .values(revoked_at=now, revoke_reason=reason, last_seen_at=now)
            .execution_options(synchronize_session=False)
        )
        return int(getattr(result, "rowcount", 0) or 0)

    async def revoke_all_sessions(self, *, user_id: str, now: datetime, reason: str) -> int:
        result = await self.db.execute(
            update(AuthSessionRecord)
            .where(
                AuthSessionRecord.user_id == user_id,
                AuthSessionRecord.revoked_at.is_(None),
            )
            .values(revoked_at=now, revoke_reason=reason, last_seen_at=now)
            .execution_options(synchronize_session=False)
        )
        return int(getattr(result, "rowcount", 0) or 0)

    async def get_receipt(
        self, *, user_id: str, command_type: str, key_digest: str
    ) -> IdentityCommandReceiptRecord | None:
        result = await self.db.execute(
            select(IdentityCommandReceiptRecord).where(
                IdentityCommandReceiptRecord.user_id == user_id,
                IdentityCommandReceiptRecord.command_type == command_type,
                IdentityCommandReceiptRecord.idempotency_key_digest == key_digest,
            )
        )
        return result.scalar_one_or_none()

    async def add_receipt(self, receipt: IdentityCommandReceiptRecord) -> None:
        self.db.add(receipt)
        await self.db.flush()

    async def get_exact_active_session(
        self,
        *,
        session_id: str,
        user_id: str,
        family_id: str,
        credential_version: int,
        session_version: int,
        now: datetime,
    ) -> AuthSessionRecord | None:
        result = await self.db.execute(
            select(AuthSessionRecord).where(
                and_(
                    AuthSessionRecord.session_id == session_id,
                    AuthSessionRecord.user_id == user_id,
                    AuthSessionRecord.token_family_id == family_id,
                    AuthSessionRecord.credential_version == credential_version,
                    AuthSessionRecord.version == session_version,
                    AuthSessionRecord.revoked_at.is_(None),
                    AuthSessionRecord.refresh_expires_at > now,
                )
            )
        )
        return result.scalar_one_or_none()

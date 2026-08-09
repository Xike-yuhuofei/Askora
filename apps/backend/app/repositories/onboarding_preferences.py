"""Single writer adapter for presentation-only onboarding preferences."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import cast
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.onboarding import (
    DismissedReason,
    JourneyId,
    OnboardingPreferenceV1,
    PreferenceVisibility,
)
from app.models.onboarding import (
    OnboardingPreferenceCommandReceiptRecord,
    OnboardingPreferenceRecord,
)


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class OnboardingPreferenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(
        self, *, user_id: str, journey_id: str, for_update: bool = False
    ) -> OnboardingPreferenceRecord | None:
        statement = select(OnboardingPreferenceRecord).where(
            OnboardingPreferenceRecord.user_id == user_id,
            OnboardingPreferenceRecord.journey_id == journey_id,
        )
        if for_update:
            statement = statement.with_for_update()
        return await self._session.scalar(statement)

    async def get_or_create_active(
        self, *, user_id: str, journey_id: str, now: datetime
    ) -> OnboardingPreferenceRecord:
        existing = await self.get(user_id=user_id, journey_id=journey_id)
        if existing is not None:
            return existing
        try:
            async with self._session.begin_nested():
                record = OnboardingPreferenceRecord(
                    preference_id=str(uuid4()),
                    user_id=user_id,
                    journey_id=journey_id,
                    preference_version=1,
                    visibility="ACTIVE",
                    created_at=now,
                    updated_at=now,
                )
                self._session.add(record)
                await self._session.flush()
            return record
        except IntegrityError:
            existing = await self.get(user_id=user_id, journey_id=journey_id)
            if existing is None:
                raise
            return existing

    async def get_receipt(
        self, *, user_id: str, journey_id: str, idempotency_key: str
    ) -> OnboardingPreferenceCommandReceiptRecord | None:
        return await self._session.scalar(
            select(OnboardingPreferenceCommandReceiptRecord).where(
                OnboardingPreferenceCommandReceiptRecord.user_id == user_id,
                OnboardingPreferenceCommandReceiptRecord.journey_id == journey_id,
                OnboardingPreferenceCommandReceiptRecord.idempotency_key == idempotency_key,
            )
        )

    async def update_if_version(
        self,
        *,
        user_id: str,
        journey_id: str,
        expected_version: int,
        now: datetime,
        values: dict[str, str | None],
    ) -> OnboardingPreferenceRecord | None:
        updated_id = await self._session.scalar(
            update(OnboardingPreferenceRecord)
            .where(
                OnboardingPreferenceRecord.user_id == user_id,
                OnboardingPreferenceRecord.journey_id == journey_id,
                OnboardingPreferenceRecord.preference_version == expected_version,
            )
            .values(
                **values,
                preference_version=expected_version + 1,
                updated_at=now,
            )
            .returning(OnboardingPreferenceRecord.preference_id)
        )
        if updated_id is None:
            return None
        return await self.get(user_id=user_id, journey_id=journey_id)

    async def append_receipt(
        self,
        *,
        user_id: str,
        journey_id: str,
        idempotency_key: str,
        command_digest: str,
        action: str,
        resulting_preference_version: int,
        now: datetime,
    ) -> None:
        self._session.add(
            OnboardingPreferenceCommandReceiptRecord(
                receipt_id=str(uuid4()),
                user_id=user_id,
                journey_id=journey_id,
                idempotency_key=idempotency_key,
                command_digest=command_digest,
                action=action,
                resulting_preference_version=resulting_preference_version,
                created_at=now,
            )
        )
        await self._session.flush()

    @staticmethod
    def to_contract(record: OnboardingPreferenceRecord) -> OnboardingPreferenceV1:
        return OnboardingPreferenceV1(
            journey_id=cast(JourneyId, record.journey_id),
            preference_version=record.preference_version,
            visibility=cast(PreferenceVisibility, record.visibility),
            boundary_notice_version_acknowledged=(record.boundary_notice_version_acknowledged),
            dismissed_reason=cast(DismissedReason | None, record.dismissed_reason),
            created_at=_aware(record.created_at),
            updated_at=_aware(record.updated_at),
        )

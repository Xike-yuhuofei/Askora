"""Persistence adapter for the SYS08 Book Learning transcript projection."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book_learning import BookLearningAdvanceRecord, BookLearningTranscriptTurnRecord


class BookLearningTranscriptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_idempotency(
        self, *, user_id: str, idempotency_key: str
    ) -> BookLearningTranscriptTurnRecord | None:
        return await self._session.scalar(
            select(BookLearningTranscriptTurnRecord).where(
                BookLearningTranscriptTurnRecord.user_id == user_id,
                BookLearningTranscriptTurnRecord.idempotency_key == idempotency_key,
            )
        )

    async def get_advance_by_idempotency(
        self, *, user_id: str, idempotency_key: str
    ) -> BookLearningAdvanceRecord | None:
        return await self._session.scalar(
            select(BookLearningAdvanceRecord).where(
                BookLearningAdvanceRecord.user_id == user_id,
                BookLearningAdvanceRecord.idempotency_key == idempotency_key,
            )
        )

    async def list_for_activity(
        self, *, user_id: str, activity_id: str
    ) -> tuple[BookLearningTranscriptTurnRecord, ...]:
        values = (
            await self._session.scalars(
                select(BookLearningTranscriptTurnRecord)
                .where(
                    BookLearningTranscriptTurnRecord.user_id == user_id,
                    BookLearningTranscriptTurnRecord.activity_id == activity_id,
                )
                .order_by(BookLearningTranscriptTurnRecord.turn_number)
            )
        ).all()
        return tuple(values)

    async def next_turn_number(self, *, session_id: str) -> int:
        latest = await self._session.scalar(
            select(func.max(BookLearningTranscriptTurnRecord.turn_number)).where(
                BookLearningTranscriptTurnRecord.session_id == session_id
            )
        )
        return int(latest or 0) + 1

    async def append(
        self, record: BookLearningTranscriptTurnRecord
    ) -> BookLearningTranscriptTurnRecord:
        self._session.add(record)
        await self._session.flush()
        return record

    async def append_advance(self, record: BookLearningAdvanceRecord) -> BookLearningAdvanceRecord:
        self._session.add(record)
        await self._session.flush()
        return record

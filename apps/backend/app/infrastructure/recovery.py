"""Append-only SYS08 operational recovery ledger."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ledger import RecoveryEventRecord


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RecoveryLedgerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_action_result(
        self, *, pseudonym_id: str, idempotency_key: str
    ) -> RecoveryEventRecord | None:
        return await self._session.scalar(
            select(RecoveryEventRecord).where(
                RecoveryEventRecord.pseudonym_id == pseudonym_id,
                RecoveryEventRecord.idempotency_key == idempotency_key,
                RecoveryEventRecord.event_type.in_(("action_succeeded", "action_failed")),
            )
        )

    async def list_events(self, *, pseudonym_id: str) -> list[RecoveryEventRecord]:
        return list(
            (
                await self._session.scalars(
                    select(RecoveryEventRecord)
                    .where(RecoveryEventRecord.pseudonym_id == pseudonym_id)
                    .order_by(
                        RecoveryEventRecord.issue_key,
                        RecoveryEventRecord.issue_version,
                        RecoveryEventRecord.created_at,
                    )
                )
            ).all()
        )

    async def append(
        self,
        *,
        pseudonym_id: str,
        issue_key: str,
        event_type: str,
        code: str,
        category: str,
        severity: str,
        status: str,
        source_system: str,
        data_safety: str,
        duplicate_risk: str,
        title: str,
        summary: str,
        resource_ref: str | None = None,
        correlation_id: str | None = None,
        attempt_count: int = 0,
        retry_budget: int | None = None,
        next_eligible_at: datetime | None = None,
        action_code: str | None = None,
        idempotency_key: str | None = None,
        result_ref: str | None = None,
        safe_details: dict | None = None,
        created_at: datetime | None = None,
    ) -> RecoveryEventRecord:
        latest_version = await self._session.scalar(
            select(RecoveryEventRecord.issue_version)
            .where(
                RecoveryEventRecord.pseudonym_id == pseudonym_id,
                RecoveryEventRecord.issue_key == issue_key,
            )
            .order_by(RecoveryEventRecord.issue_version.desc())
            .limit(1)
        )
        record = RecoveryEventRecord(
            id=str(uuid4()),
            pseudonym_id=pseudonym_id,
            issue_key=issue_key,
            issue_version=int(latest_version or 0) + 1,
            event_type=event_type,
            code=code,
            category=category,
            severity=severity,
            status=status,
            source_system=source_system,
            data_safety=data_safety,
            duplicate_risk=duplicate_risk,
            title=title,
            summary=summary,
            resource_ref=resource_ref,
            correlation_id=correlation_id,
            attempt_count=attempt_count,
            retry_budget=retry_budget,
            next_eligible_at=next_eligible_at,
            action_code=action_code,
            idempotency_key=idempotency_key,
            result_ref=result_ref,
            safe_details=safe_details or {},
            created_at=created_at or utc_now(),
        )
        self._session.add(record)
        await self._session.flush()
        return record

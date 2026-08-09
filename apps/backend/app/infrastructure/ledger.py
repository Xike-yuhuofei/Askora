"""SQLite/PostgreSQL-compatible append-only event and decision ledgers."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.decisions import DecisionTrace
from app.contracts.events import LearningEventEnvelope
from app.models.ledger import (
    DECISION_TRACE_INPUT_ENTITY_ID_MAX_LENGTH,
    DECISION_TRACE_INPUT_ENTITY_TYPE_MAX_LENGTH,
    DECISION_TRACE_INPUT_ENTITY_VERSION_MAX_LENGTH,
    DecisionTraceInputRecord,
    DecisionTraceRecord,
    LearningEventRecord,
)


class LedgerConflictError(RuntimeError):
    """Ledger 唯一性或版本冲突。"""


class AggregateVersionConflict(LedgerConflictError):
    """同一 aggregate version 已被另一事件占用。"""


class LedgerPersistenceError(RuntimeError):
    """Ledger payload cannot be represented by the durable schema."""


class DecisionTraceInputLengthError(LedgerPersistenceError):
    """A DecisionTrace query-index value exceeds its storage budget."""

    def __init__(self, *, field: str, actual_length: int, max_length: int) -> None:
        self.field = field
        self.actual_length = actual_length
        self.max_length = max_length
        super().__init__(
            f"DECISION_TRACE_INPUT_LENGTH_INVALID:{field}:"
            f"actual={actual_length}:max={max_length}"
        )


def _aware(value: datetime) -> datetime:
    """SQLite 丢弃 timezone 标志时按 UTC 恢复已约定的持久化语义。"""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


class LearningEventRepository:
    """EVENT-002/010/011/014/060 的 append/query/replay port 实现。"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(self, event: LearningEventEnvelope) -> LearningEventEnvelope:
        existing = await self.get_by_idempotency_key(event.idempotency_key)
        if existing is not None:
            return existing

        data = event.model_dump(mode="json")
        record = LearningEventRecord(
            event_id=data["event_id"],
            event_type=data["event_type"],
            schema_version=data["schema_version"],
            aggregate_type=data["aggregate_type"],
            aggregate_id=str(data["aggregate_id"]),
            aggregate_version=data["aggregate_version"],
            sequence=data["sequence"],
            occurred_at=event.occurred_at,
            recorded_at=event.recorded_at,
            idempotency_key=data["idempotency_key"],
            correlation_id=data["correlation_id"],
            causation_id=data["causation_id"],
            actor=data["actor"],
            context=data["context"],
            payload=data["payload"],
            provenance=data["provenance"],
            trace=data["trace"],
            privacy=data["privacy"],
        )

        savepoint = await self._session.begin_nested()
        try:
            self._session.add(record)
            await self._session.flush()
        except IntegrityError as exc:
            await savepoint.rollback()
            existing = await self.get_by_idempotency_key(event.idempotency_key)
            if existing is not None:
                return existing
            raise AggregateVersionConflict(
                f"aggregate version already exists: {event.aggregate_type}/"
                f"{event.aggregate_id}/v{event.aggregate_version}"
            ) from exc
        else:
            await savepoint.commit()
        return event

    async def get(self, event_id: UUID | str) -> LearningEventEnvelope | None:
        record = await self._session.get(LearningEventRecord, str(event_id))
        if record is None or record.schema_version != "1.0":
            return None
        return self._to_contract(record)

    async def get_by_idempotency_key(self, key: str) -> LearningEventEnvelope | None:
        record = await self._session.scalar(
            select(LearningEventRecord).where(
                LearningEventRecord.idempotency_key == key,
                LearningEventRecord.schema_version == "1.0",
            )
        )
        return self._to_contract(record) if record is not None else None

    async def query(
        self,
        *,
        event_type: str | None = None,
        correlation_id: UUID | str | None = None,
        limit: int = 100,
    ) -> list[LearningEventEnvelope]:
        statement = select(LearningEventRecord).where(LearningEventRecord.schema_version == "1.0")
        if event_type is not None:
            statement = statement.where(LearningEventRecord.event_type == event_type)
        if correlation_id is not None:
            statement = statement.where(LearningEventRecord.correlation_id == str(correlation_id))
        statement = statement.order_by(
            LearningEventRecord.recorded_at, LearningEventRecord.event_id
        ).limit(limit)
        records = (await self._session.scalars(statement)).all()
        return [self._to_contract(record) for record in records]

    async def replay(
        self,
        aggregate_type: str,
        aggregate_id: UUID | str,
        *,
        after_sequence: int = 0,
    ) -> list[LearningEventEnvelope]:
        """按 aggregate logical sequence 返回确定性的历史事件集合。"""
        records = (
            await self._session.scalars(
                select(LearningEventRecord)
                .where(
                    LearningEventRecord.schema_version == "1.0",
                    LearningEventRecord.aggregate_type == aggregate_type,
                    LearningEventRecord.aggregate_id == str(aggregate_id),
                    LearningEventRecord.sequence > after_sequence,
                )
                .order_by(
                    LearningEventRecord.sequence,
                    LearningEventRecord.aggregate_version,
                    LearningEventRecord.event_id,
                )
            )
        ).all()
        return [self._to_contract(record) for record in records]

    @staticmethod
    def _to_contract(record: LearningEventRecord) -> LearningEventEnvelope:
        if record.schema_version != "1.0":
            raise ValueError("v0.3 events require LearningEventV03Repository")
        return LearningEventEnvelope.model_validate(
            {
                "event_id": record.event_id,
                "event_type": record.event_type,
                "schema_version": record.schema_version,
                "aggregate_type": record.aggregate_type,
                "aggregate_id": record.aggregate_id,
                "aggregate_version": record.aggregate_version,
                "sequence": record.sequence,
                "occurred_at": _aware(record.occurred_at),
                "recorded_at": _aware(record.recorded_at),
                "idempotency_key": record.idempotency_key,
                "correlation_id": record.correlation_id,
                "causation_id": record.causation_id,
                "actor": record.actor,
                "context": record.context,
                "payload": record.payload,
                "provenance": record.provenance,
                "trace": record.trace,
                "privacy": record.privacy,
            }
        )


class DecisionTraceRepository:
    """DECISION-001/002/090/091 的 append-only ledger 实现。"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(self, trace: DecisionTrace) -> DecisionTrace:
        existing = await self.get(trace.decision_id)
        if existing is not None:
            return existing

        data = trace.model_dump(mode="json")
        indexed_inputs = [self._indexed_input(item) for item in data["inputs"]]
        record = DecisionTraceRecord(
            decision_id=data["decision_id"],
            decision_type=data["decision_type"],
            schema_version=data["schema_version"],
            owner_system=data["owner_system"],
            inputs=data["inputs"],
            candidates=data["candidates"],
            selected=data["selected"],
            constraints=data["constraints"],
            reason_codes=data["reason_codes"],
            confidence=data["confidence"],
            algorithm=data["algorithm"],
            algorithm_id=data["algorithm"]["algorithm_id"],
            algorithm_version=data["algorithm"]["algorithm_version"],
            experiment=data["experiment"],
            experiment_id=data["experiment"]["experiment_id"],
            created_at=trace.created_at,
            correlation_id=data["correlation_id"],
            trace_id=data["trace_id"],
            indexed_inputs=indexed_inputs,
        )

        savepoint = await self._session.begin_nested()
        try:
            self._session.add(record)
            await self._session.flush()
        except DataError as exc:
            await savepoint.rollback()
            raise LedgerPersistenceError("DECISION_TRACE_PERSISTENCE_REJECTED") from exc
        except IntegrityError as exc:
            await savepoint.rollback()
            existing = await self.get(trace.decision_id)
            if existing is not None:
                return existing
            raise LedgerConflictError(f"decision_id conflict: {trace.decision_id}") from exc
        else:
            await savepoint.commit()
        return trace

    @staticmethod
    def _indexed_input(item: dict) -> DecisionTraceInputRecord:
        entity_type = str(item["entity_type"])
        entity_id = str(item["entity_id"])
        entity_version = str(item["version"]) if item["version"] is not None else None
        DecisionTraceRepository._validate_length(
            field="entity_type",
            value=entity_type,
            max_length=DECISION_TRACE_INPUT_ENTITY_TYPE_MAX_LENGTH,
        )
        DecisionTraceRepository._validate_length(
            field="entity_id",
            value=entity_id,
            max_length=DECISION_TRACE_INPUT_ENTITY_ID_MAX_LENGTH,
        )
        if entity_version is not None:
            DecisionTraceRepository._validate_length(
                field="entity_version",
                value=entity_version,
                max_length=DECISION_TRACE_INPUT_ENTITY_VERSION_MAX_LENGTH,
            )
        return DecisionTraceInputRecord(
            entity_type=entity_type,
            entity_id=entity_id,
            entity_version=entity_version,
        )

    @staticmethod
    def _validate_length(*, field: str, value: str, max_length: int) -> None:
        actual_length = len(value)
        if actual_length > max_length:
            raise DecisionTraceInputLengthError(
                field=field,
                actual_length=actual_length,
                max_length=max_length,
            )

    async def get(self, decision_id: UUID | str) -> DecisionTrace | None:
        record = await self._session.get(DecisionTraceRecord, str(decision_id))
        if record is None or record.schema_version != "1.0":
            return None
        return self._to_contract(record)

    async def query(
        self,
        *,
        trace_id: str | None = None,
        correlation_id: UUID | str | None = None,
        entity_type: str | None = None,
        entity_id: UUID | str | None = None,
        entity_version: str | int | None = None,
        decision_type: str | None = None,
        algorithm_version: str | None = None,
        limit: int = 100,
    ) -> list[DecisionTrace]:
        statement = select(DecisionTraceRecord).where(DecisionTraceRecord.schema_version == "1.0")
        if entity_id is not None:
            statement = statement.join(DecisionTraceInputRecord)
            statement = statement.where(DecisionTraceInputRecord.entity_id == str(entity_id))
            if entity_type is not None:
                statement = statement.where(DecisionTraceInputRecord.entity_type == entity_type)
            if entity_version is not None:
                statement = statement.where(
                    DecisionTraceInputRecord.entity_version == str(entity_version)
                )
        if trace_id is not None:
            statement = statement.where(DecisionTraceRecord.trace_id == trace_id)
        if correlation_id is not None:
            statement = statement.where(DecisionTraceRecord.correlation_id == str(correlation_id))
        if decision_type is not None:
            statement = statement.where(DecisionTraceRecord.decision_type == decision_type)
        if algorithm_version is not None:
            statement = statement.where(DecisionTraceRecord.algorithm_version == algorithm_version)
        statement = statement.order_by(
            DecisionTraceRecord.created_at, DecisionTraceRecord.decision_id
        ).limit(limit)
        records = (await self._session.scalars(statement)).unique().all()
        return [self._to_contract(record) for record in records]

    @staticmethod
    def _to_contract(record: DecisionTraceRecord) -> DecisionTrace:
        if record.schema_version != "1.0":
            raise ValueError("v0.3 traces require DecisionTraceV03Repository")
        return DecisionTrace.model_validate(
            {
                "decision_id": record.decision_id,
                "decision_type": record.decision_type,
                "schema_version": record.schema_version,
                "owner_system": record.owner_system,
                "inputs": record.inputs,
                "candidates": record.candidates,
                "selected": record.selected,
                "constraints": record.constraints,
                "reason_codes": record.reason_codes,
                "confidence": record.confidence,
                "algorithm": record.algorithm,
                "experiment": record.experiment,
                "created_at": _aware(record.created_at),
                "correlation_id": record.correlation_id,
                "trace_id": record.trace_id,
            }
        )

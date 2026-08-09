from __future__ import annotations

from uuid import uuid4

import pytest

from app.contracts import DecisionInput
from app.infrastructure.ledger import (
    AggregateVersionConflict,
    DecisionTraceInputLengthError,
    DecisionTraceRepository,
    LearningEventRepository,
)
from app.models.ledger import (
    DecisionTraceRecord,
    ImmutableLedgerError,
    LearningEventRecord,
)
from tests.infrastructure.factories import make_decision, make_event


async def test_event_idempotency_version_conflict_and_replay(sqlite_factory) -> None:
    """EVENT-AC-001/002 and EXEC001-AC-001/002."""
    aggregate_id = uuid4()
    idempotency_key = f"submit:{uuid4()}"
    first = make_event(
        aggregate_id=aggregate_id,
        aggregate_version=1,
        sequence=1,
        idempotency_key=idempotency_key,
    )
    second = make_event(aggregate_id=aggregate_id, aggregate_version=2, sequence=2)

    async with sqlite_factory() as session:
        async with session.begin():
            repository = LearningEventRepository(session)
            appended = await repository.append(first)
            retried = await repository.append(make_event(idempotency_key=idempotency_key))
            await repository.append(second)
        assert retried.event_id == appended.event_id

    async with sqlite_factory() as session:
        repository = LearningEventRepository(session)
        replay = await repository.replay("Attempt", aggregate_id)
        assert [item.aggregate_version for item in replay] == [1, 2]
        assert len(await repository.query(event_type="ResponseSubmitted")) == 2

        conflicting = make_event(
            aggregate_id=aggregate_id,
            aggregate_version=2,
            sequence=3,
        )
        with pytest.raises(AggregateVersionConflict):
            await repository.append(conflicting)


async def test_event_rows_cannot_be_updated_or_deleted(sqlite_factory) -> None:
    """EVENT-002/EVENT-070: corrections are new events, never row mutation."""
    event = make_event()
    async with sqlite_factory() as session:
        async with session.begin():
            await LearningEventRepository(session).append(event)

    async with sqlite_factory() as session:
        record = await session.get(LearningEventRecord, str(event.event_id))
        assert record is not None
        record.payload = {"tampered": True}
        with pytest.raises(ImmutableLedgerError):
            await session.flush()
        await session.rollback()

    async with sqlite_factory() as session:
        record = await session.get(LearningEventRecord, str(event.event_id))
        assert record is not None
        await session.delete(record)
        with pytest.raises(ImmutableLedgerError):
            await session.flush()
        await session.rollback()


async def test_decision_ledger_is_append_only_and_queryable_by_trace_entity_version(
    sqlite_factory,
) -> None:
    """EXEC001-AC-005/DECISION-090/091."""
    entity_id = uuid4()
    decision = make_decision(entity_id=entity_id, version=7)
    original_selected = dict(decision.selected)

    async with sqlite_factory() as session:
        async with session.begin():
            repository = DecisionTraceRepository(session)
            appended = await repository.append(decision)
            duplicate = await repository.append(decision)
        assert duplicate.decision_id == appended.decision_id

    async with sqlite_factory() as session:
        repository = DecisionTraceRepository(session)
        by_trace = await repository.query(trace_id=decision.trace_id)
        by_entity = await repository.query(
            entity_type="LearnerState", entity_id=entity_id, entity_version=7
        )
        assert [item.decision_id for item in by_trace] == [decision.decision_id]
        assert [item.decision_id for item in by_entity] == [decision.decision_id]
        assert by_entity[0].selected == original_selected

        record = await session.get(DecisionTraceRecord, str(decision.decision_id))
        assert record is not None
        record.selected = {"action": "tampered"}
        with pytest.raises(ImmutableLedgerError):
            await session.flush()
        await session.rollback()


async def test_decision_input_index_accepts_full_snapshot_and_rejects_oversized_value(
    sqlite_factory,
) -> None:
    """PERSIST-032: storage budgets fail before the database and never truncate audit refs."""
    snapshot = (
        "document:17a0f10d-6a0d-475f-978d-1231b3e36231:"
        "revision:5d32553e-892e-5b79-95f6-b8355bb0a420:"
        "publication:b413e394-58d4-5d5b-8d86-c3d5b79a95ea"
    )
    assert len(snapshot) == 140
    accepted = make_decision().model_copy(
        update={
            "inputs": [
                DecisionInput(
                    entity_type="KnowledgeGraphSnapshot",
                    entity_id=snapshot,
                    version=snapshot,
                )
            ]
        }
    )
    rejected = make_decision().model_copy(
        update={
            "inputs": [
                DecisionInput(
                    entity_type="KnowledgeGraphSnapshot",
                    entity_id="snapshot",
                    version="v" * 256,
                )
            ]
        }
    )

    async with sqlite_factory() as session:
        async with session.begin():
            repository = DecisionTraceRepository(session)
            await repository.append(accepted)
            with pytest.raises(
                DecisionTraceInputLengthError,
                match="DECISION_TRACE_INPUT_LENGTH_INVALID:entity_version:actual=256:max=255",
            ):
                await repository.append(rejected)
        found = await repository.query(
            entity_type="KnowledgeGraphSnapshot",
            entity_id=snapshot,
            entity_version=snapshot,
        )
        assert [item.decision_id for item in found] == [accepted.decision_id]
        assert await repository.get(rejected.decision_id) is None

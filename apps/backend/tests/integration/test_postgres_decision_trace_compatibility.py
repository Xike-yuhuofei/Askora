"""PostgreSQL-only regression for DecisionTrace indexed input constraints."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.contracts import DecisionInput
from app.infrastructure.ledger import DecisionTraceRepository
from tests.infrastructure.factories import make_decision

POSTGRES_TEST_URL = os.environ.get("ASKORA_POSTGRES_TEST_URL")

pytestmark = pytest.mark.skipif(
    not POSTGRES_TEST_URL,
    reason="ASKORA_POSTGRES_TEST_URL is required for PostgreSQL compatibility tests",
)


def _async_url(value: str) -> str:
    if value.startswith("postgresql+asyncpg://"):
        return value
    if value.startswith("postgresql://"):
        return value.replace("postgresql://", "postgresql+asyncpg://", 1)
    raise ValueError("ASKORA_POSTGRES_TEST_URL must use PostgreSQL")


@pytest.mark.asyncio
async def test_postgres_persists_and_queries_full_snapshot_version() -> None:
    assert POSTGRES_TEST_URL is not None
    engine = create_async_engine(_async_url(POSTGRES_TEST_URL))
    factory = async_sessionmaker(engine, expire_on_commit=False)
    snapshot = (
        "document:17a0f10d-6a0d-475f-978d-1231b3e36231:"
        "revision:5d32553e-892e-5b79-95f6-b8355bb0a420:"
        "publication:b413e394-58d4-5d5b-8d86-c3d5b79a95ea"
    )
    decision = make_decision().model_copy(
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

    async with factory() as session:
        transaction = await session.begin()
        try:
            column_length = await session.scalar(
                text(
                    "SELECT character_maximum_length "
                    "FROM information_schema.columns "
                    "WHERE table_schema = current_schema() "
                    "AND table_name = 'decision_trace_inputs' "
                    "AND column_name = 'entity_version'"
                )
            )
            assert column_length == 255
            repository = DecisionTraceRepository(session)
            await repository.append(decision)
            found = await repository.query(
                entity_type="KnowledgeGraphSnapshot",
                entity_id=snapshot,
                entity_version=snapshot,
            )
            assert [item.decision_id for item in found] == [decision.decision_id]
        finally:
            await transaction.rollback()
    await engine.dispose()

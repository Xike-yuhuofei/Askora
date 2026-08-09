"""DecisionTrace input index width migration and forward-fix evidence."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.contracts import DecisionInput
from app.infrastructure.ledger import DecisionTraceRepository
from tests.infrastructure.factories import make_decision

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PREVIOUS_HEAD = "e23a91b807d1"


def _alembic(database_url: str, *arguments: str) -> None:
    environment = os.environ.copy()
    environment["DATABASE_URL"] = database_url
    subprocess.run(  # noqa: S603
        [sys.executable, "-m", "alembic", *arguments],
        cwd=BACKEND_ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )


async def _entity_version_length(database_url: str) -> int | None:
    engine = create_async_engine(database_url)
    async with engine.connect() as connection:
        columns = await connection.run_sync(
            lambda sync: inspect(sync).get_columns("decision_trace_inputs")
        )
    await engine.dispose()
    column = next(item for item in columns if item["name"] == "entity_version")
    return column["type"].length


@pytest.mark.asyncio
async def test_decision_trace_input_width_upgrade_rollback_forward_fix(tmp_path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'decision-input-migration.db'}"
    _alembic(database_url, "upgrade", PREVIOUS_HEAD)
    assert await _entity_version_length(database_url) == 100

    _alembic(database_url, "upgrade", "head")
    assert await _entity_version_length(database_url) == 255

    _alembic(database_url, "downgrade", PREVIOUS_HEAD)
    assert await _entity_version_length(database_url) == 100

    _alembic(database_url, "upgrade", "head")
    assert await _entity_version_length(database_url) == 255
    _alembic(database_url, "check")


@pytest.mark.asyncio
async def test_decision_trace_input_width_downgrade_never_truncates_audit_refs(
    tmp_path,
) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'blocked-downgrade.db'}"
    _alembic(database_url, "upgrade", "head")
    engine = create_async_engine(database_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    decision = make_decision().model_copy(
        update={
            "inputs": [
                DecisionInput(
                    entity_type="KnowledgeGraphSnapshot",
                    entity_id="snapshot",
                    version="v" * 140,
                )
            ]
        }
    )
    async with factory() as session:
        async with session.begin():
            await DecisionTraceRepository(session).append(decision)
    await engine.dispose()

    with pytest.raises(subprocess.CalledProcessError) as exc_info:
        _alembic(database_url, "downgrade", PREVIOUS_HEAD)
    assert "DECISION_TRACE_INPUT_VERSION_DOWNGRADE_BLOCKED" in exc_info.value.stderr
    assert await _entity_version_length(database_url) == 255

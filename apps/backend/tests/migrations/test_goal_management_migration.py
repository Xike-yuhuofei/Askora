"""P1-01A representative legacy backfill and rollback/forward-fix."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PREVIOUS_HEAD = "f1061a0b9c01"
GOAL_HEAD = "d2f1010a37a1"


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


def _goal_payload(goal_id: str, user_id: str, status: str, created_at: str) -> dict:
    return {
        "goal_id": goal_id,
        "goal_schema_version": "1.0",
        "version": 1,
        "user_id": user_id,
        "title": "Legacy Goal",
        "topic": "Thermodynamics",
        "target_capabilities": ["explain"],
        "application_context": None,
        "success_criteria": ["independently explain the second law"],
        "source_document_ids": [],
        "deadline_at": None,
        "weekly_time_budget_minutes": 60,
        "status": status,
        "confirmed_by_user": status != "candidate",
        "created_at": created_at,
        "confirmed_at": created_at if status != "candidate" else None,
        "supersedes_version": None,
        "model_inference_refs": [],
        "reason_codes": ["LEGACY_FIXTURE"],
    }


@pytest.mark.asyncio
async def test_goal_migration_backfills_definition_state_and_candidate_draft(tmp_path) -> None:
    url = f"sqlite+aiosqlite:///{tmp_path / 'goal-migration.db'}"
    _alembic(url, "upgrade", PREVIOUS_HEAD)
    engine = create_async_engine(url)
    now = datetime.now(timezone.utc).isoformat()
    async with engine.begin() as connection:
        for goal_id, status in (
            ("11111111-1111-4111-8111-111111111111", "candidate"),
            ("22222222-2222-4222-8222-222222222222", "active"),
        ):
            await connection.exec_driver_sql(
                "INSERT INTO learning_goal_versions "
                "(id, goal_id, user_id, version, status, idempotency_key, payload) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    f"{goal_id}:1",
                    goal_id,
                    "33333333-3333-4333-8333-333333333333",
                    1,
                    status,
                    f"legacy-{status}",
                    json.dumps(
                        _goal_payload(
                            goal_id,
                            "33333333-3333-4333-8333-333333333333",
                            status,
                            now,
                        )
                    ),
                ),
            )
    await engine.dispose()

    _alembic(url, "upgrade", GOAL_HEAD)
    upgraded = create_async_engine(url)
    async with upgraded.connect() as connection:
        definition_count = (
            await connection.exec_driver_sql(
                "SELECT COUNT(*) FROM learning_goal_definition_versions"
            )
        ).scalar_one()
        draft_status = (
            await connection.exec_driver_sql(
                "SELECT status FROM learning_goal_draft_versions"
            )
        ).scalar_one()
        state_status = (
            await connection.exec_driver_sql(
                "SELECT status FROM learning_goal_state_versions"
            )
        ).scalar_one()
        assert definition_count == 2
        assert draft_status == "draft"
        assert state_status == "active"
    await upgraded.dispose()

    _alembic(url, "downgrade", PREVIOUS_HEAD)
    rolled_back = create_async_engine(url)
    async with rolled_back.connect() as connection:
        tables = await connection.run_sync(lambda sync: set(inspect(sync).get_table_names()))
        legacy_count = (
            await connection.exec_driver_sql("SELECT COUNT(*) FROM learning_goal_versions")
        ).scalar_one()
        assert "learning_goal_definition_versions" not in tables
        assert legacy_count == 2
    await rolled_back.dispose()
    _alembic(url, "upgrade", GOAL_HEAD)

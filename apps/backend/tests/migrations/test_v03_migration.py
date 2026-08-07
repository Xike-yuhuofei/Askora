"""EXEC-008 additive schema migration and rollback/forward-fix evidence."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PREVIOUS_HEAD = "a42d9c0170e2"


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


@pytest.mark.asyncio
async def test_v02_database_upgrades_idempotently_without_reinterpreting_v1_trace(
    tmp_path: Path,
) -> None:
    """EXEC008-AC-007/010/011, PERSIST-090, DECISION-212."""
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'v02-to-v03.db'}"
    _alembic(database_url, "upgrade", PREVIOUS_HEAD)

    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.exec_driver_sql(
            """
            INSERT INTO decision_traces (
                decision_id, decision_type, schema_version, owner_system,
                inputs, candidates, selected, constraints, reason_codes, confidence,
                algorithm, algorithm_id, algorithm_version, experiment, experiment_id,
                created_at, correlation_id, trace_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "00000000-0000-0000-0000-000000000001",
                "TeachingActionSelected",
                "1.0",
                "teaching_policy",
                "[]",
                "[]",
                "{}",
                "[]",
                json.dumps(["LEGACY_TRACE"]),
                None,
                json.dumps(
                    {
                        "algorithm_id": "legacy",
                        "algorithm_version": "1",
                        "model_inference_ids": [],
                        "prompt_versions": [],
                    }
                ),
                "legacy",
                "1",
                json.dumps({"experiment_id": "legacy-exp", "variant_id": "a", "propensity": 0.5}),
                "legacy-exp",
                "2026-08-07 14:00:00",
                "00000000-0000-0000-0000-000000000002",
                "legacy-trace",
            ),
        )
    await engine.dispose()

    _alembic(database_url, "upgrade", "head")
    _alembic(database_url, "upgrade", "head")
    _alembic(database_url, "check")

    upgraded = create_async_engine(database_url)
    async with upgraded.connect() as connection:
        tables = await connection.run_sync(lambda sync: set(inspect(sync).get_table_names()))
        columns = await connection.run_sync(
            lambda sync: {column["name"] for column in inspect(sync).get_columns("decision_traces")}
        )
        event_columns = await connection.run_sync(
            lambda sync: {column["name"] for column in inspect(sync).get_columns("learning_events")}
        )
        row = (
            await connection.exec_driver_sql(
                """
                SELECT schema_version, experiment, action_propensity,
                       experiment_assignment_probability, replayability_status
                FROM decision_traces WHERE decision_id = ?
                """,
                ("00000000-0000-0000-0000-000000000001",),
            )
        ).one()
        assert {
            "teaching_contexts",
            "policy_bundles",
            "policy_bundle_activations",
            "teaching_action_versions",
            "experiment_assignments",
            "teaching_episodes",
            "learning_trajectories",
            "outcome_observations",
        }.issubset(tables)
        assert {
            "v03_payload",
            "teaching_context_id",
            "policy_bundle_id",
            "behavior_policy_type",
            "action_propensity",
            "experiment_assignment_probability",
            "replayability_status",
        }.issubset(columns)
        assert {"producer_system", "v03_payload"}.issubset(event_columns)
        assert row[0] == "1.0"
        assert json.loads(row[1])["propensity"] == 0.5
        assert row[2:] == (None, None, None)
    await upgraded.dispose()

    _alembic(database_url, "downgrade", PREVIOUS_HEAD)
    rolled_back = create_async_engine(database_url)
    async with rolled_back.connect() as connection:
        tables = await connection.run_sync(lambda sync: set(inspect(sync).get_table_names()))
        columns = await connection.run_sync(
            lambda sync: {column["name"] for column in inspect(sync).get_columns("decision_traces")}
        )
        event_columns = await connection.run_sync(
            lambda sync: {column["name"] for column in inspect(sync).get_columns("learning_events")}
        )
        count = (
            await connection.exec_driver_sql(
                "SELECT COUNT(*) FROM decision_traces WHERE decision_id = ?",
                ("00000000-0000-0000-0000-000000000001",),
            )
        ).scalar_one()
        assert "teaching_contexts" not in tables
        assert "v03_payload" not in columns
        assert "producer_system" not in event_columns
        assert "v03_payload" not in event_columns
        assert count == 1
    await rolled_back.dispose()

    _alembic(database_url, "upgrade", "head")

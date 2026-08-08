"""ADR-0003 deterministic bootstrap migration and rollback evidence."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from app.services.policy_runtime import (
    DEFAULT_POLICY_ACTIVATION_ID,
    DEFAULT_POLICY_BUNDLE_ID,
    default_policy_bundle,
)

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PREVIOUS_HEAD = "c22d05a8e101"


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
async def test_default_policy_bootstrap_upgrade_rollback_forward_fix(tmp_path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'policy-migration.db'}"
    _alembic(database_url, "upgrade", PREVIOUS_HEAD)
    _alembic(database_url, "upgrade", "head")
    _alembic(database_url, "upgrade", "head")

    engine = create_async_engine(database_url)
    async with engine.connect() as connection:
        bundle_row = (
            await connection.exec_driver_sql(
                "SELECT payload FROM policy_bundles WHERE bundle_id = ?",
                (DEFAULT_POLICY_BUNDLE_ID,),
            )
        ).one()
        activation_row = (
            await connection.exec_driver_sql(
                "SELECT bundle_id, reason_codes FROM policy_bundle_activations "
                "WHERE activation_id = ?",
                (DEFAULT_POLICY_ACTIVATION_ID,),
            )
        ).one()
        assert json.loads(bundle_row[0]) == default_policy_bundle().model_dump(mode="json")
        assert activation_row[0] == DEFAULT_POLICY_BUNDLE_ID
        assert json.loads(activation_row[1]) == ["ADR_0003_DEFAULT_BOOTSTRAP"]
    await engine.dispose()

    _alembic(database_url, "downgrade", PREVIOUS_HEAD)
    rolled_back = create_async_engine(database_url)
    async with rolled_back.connect() as connection:
        bundle_count = (
            await connection.exec_driver_sql(
                "SELECT COUNT(*) FROM policy_bundles WHERE bundle_id = ?",
                (DEFAULT_POLICY_BUNDLE_ID,),
            )
        ).scalar_one()
        assert bundle_count == 0
    await rolled_back.dispose()

    _alembic(database_url, "upgrade", "head")
    _alembic(database_url, "check")


@pytest.mark.asyncio
async def test_default_policy_downgrade_preserves_referenced_history(tmp_path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'policy-in-use.db'}"
    _alembic(database_url, "upgrade", "head")
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.exec_driver_sql(
            "INSERT INTO teaching_contexts "
            "(context_id, schema_version, context_fingerprint, decision_time, payload) "
            "VALUES (?, ?, ?, ?, ?)",
            ("context-adr0003", "3.0", "sha256:adr0003-context", "2026-08-08", "{}"),
        )
        await connection.exec_driver_sql(
            "INSERT INTO teaching_action_versions "
            "(action_id, schema_version, decision_id, context_id, policy_bundle_id, "
            "strategy_family, payload, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "action-adr0003",
                "3.0",
                "decision-adr0003",
                "context-adr0003",
                DEFAULT_POLICY_BUNDLE_ID,
                "GUIDED_PRACTICE",
                "{}",
                "2026-08-08",
            ),
        )
    await engine.dispose()

    environment = os.environ.copy()
    environment["DATABASE_URL"] = database_url
    result = subprocess.run(  # noqa: ASYNC221,S603
        [sys.executable, "-m", "alembic", "downgrade", PREVIOUS_HEAD],
        cwd=BACKEND_ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "DEFAULT_POLICY_RUNTIME_IN_USE_FORWARD_FIX_REQUIRED" in result.stderr

    preserved = create_async_engine(database_url)
    async with preserved.connect() as connection:
        assert (
            await connection.exec_driver_sql(
                "SELECT COUNT(*) FROM policy_bundles WHERE bundle_id = ?",
                (DEFAULT_POLICY_BUNDLE_ID,),
            )
        ).scalar_one() == 1
    await preserved.dispose()

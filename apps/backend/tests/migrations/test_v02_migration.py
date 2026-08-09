from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import MetaData, Table, inspect, select
from sqlalchemy.ext.asyncio import create_async_engine

from app.models.assessment import AssessmentResult
from app.models.dialog import DialogSession

BACKEND_ROOT = Path(__file__).resolve().parents[2]


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
async def test_representative_legacy_database_forward_rollback_and_reconcile(
    tmp_path: Path,
) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'legacy-v02.db'}"
    _alembic(database_url, "upgrade", "c81f6ec4a2d1")
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:

        def insert_historical_fixture(sync_connection) -> None:
            metadata = MetaData()
            users = Table("users", metadata, autoload_with=sync_connection)
            dialogs = Table("dialog_sessions", metadata, autoload_with=sync_connection)
            results = Table("assessment_results", metadata, autoload_with=sync_connection)
            sync_connection.execute(
                users.insert().values(
                    id="legacy-user",
                    role="USER",
                    status="ACTIVE",
                    is_verified=False,
                    pseudonym_id="legacy-pseudonym",
                )
            )
            sync_connection.execute(
                dialogs.insert().values(
                    id="legacy-session",
                    user_id="legacy-user",
                    pseudonym_id="legacy-pseudonym",
                    subject="science",
                    status="ACTIVE",
                    current_hint_level=0,
                    hint_escalation_count=0,
                    wrong_streak=0,
                    mastery_estimate=0.88,
                    turn_count=0,
                    total_tokens=0,
                    duration_seconds=0,
                    moderation_status="approved",
                    model_provider="fixture",
                    model_name="fixture",
                )
            )
            sync_connection.execute(
                results.insert().values(
                    id="legacy-result",
                    user_id="legacy-user",
                    pseudonym_id="legacy-pseudonym",
                    assessment_type="formative",
                    subject="science",
                    knowledge_point_ids=["legacy-kp"],
                    grade_level=0,
                    total_items=1,
                    correct_count=1,
                    score=1.0,
                    time_spent_seconds=5,
                    mastery_estimates={"legacy-kp": {"p": 0.99}},
                    detected_misconceptions=[],
                    item_results=[],
                    started_at=datetime.now(timezone.utc),
                )
            )

        await connection.run_sync(insert_historical_fixture)
    await engine.dispose()

    _alembic(database_url, "upgrade", "head")
    _alembic(database_url, "upgrade", "head")
    _alembic(database_url, "check")
    upgraded = create_async_engine(database_url)
    async with upgraded.connect() as connection:
        tables = await connection.run_sync(lambda sync: set(inspect(sync).get_table_names()))
        legacy_mastery = await connection.scalar(
            select(DialogSession.mastery_estimate).where(DialogSession.id == "legacy-session")
        )
        legacy_assessment = await connection.scalar(
            select(AssessmentResult.mastery_estimates).where(AssessmentResult.id == "legacy-result")
        )
        canonical_evidence_count = await connection.exec_driver_sql(
            "SELECT COUNT(*) FROM learner_evidence"
        )
        assert "review_schedule_versions" in tables
        assert "learning_plan_versions" in tables
        assert legacy_mastery == pytest.approx(0.88)
        assert legacy_assessment == {"legacy-kp": {"p": 0.99}}
        assert canonical_evidence_count.scalar_one() == 0
    await upgraded.dispose()

    _alembic(database_url, "downgrade", "c81f6ec4a2d1")
    rolled_back = create_async_engine(database_url)
    async with rolled_back.connect() as connection:
        tables = await connection.run_sync(lambda sync: set(inspect(sync).get_table_names()))
        assert "dialog_sessions" in tables
        assert "learner_evidence" not in tables
    await rolled_back.dispose()
    _alembic(database_url, "upgrade", "head")

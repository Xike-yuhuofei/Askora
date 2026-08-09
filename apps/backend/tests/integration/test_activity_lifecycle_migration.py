"""SQLite migration/backfill/forward-fix evidence for SYS06-ACT-AC-006."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.contracts.learning import LearningActivity, LearningPlan
from app.contracts.planning import LearningGoalV1
from app.models.book_learning import BookLearningTranscriptTurnRecord
from app.models.planning import (
    LearningActivityRecord,
    LearningActivityStateRecord,
    LearningGoalRecord,
    LearningPlanRecord,
)

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PREVIOUS_HEAD = "a80d4f9c2b61"
LIFECYCLE_REVISION = "e30c06a1b2c3"
NOW = datetime(2026, 8, 9, 7, 0, tzinfo=timezone.utc)


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
async def test_exec030_backfill_uses_accepted_owner_transcript_without_completion(tmp_path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'activity-migration.db'}"
    _alembic(database_url, "upgrade", PREVIOUS_HEAD)
    engine = create_async_engine(database_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    goal_id, plan_id, objective_id, activity_id = uuid4(), uuid4(), uuid4(), uuid4()
    user_id = uuid4()
    goal = LearningGoalV1(
        goal_id=goal_id,
        version=1,
        user_id=user_id,
        title="迁移测试",
        topic="test",
        target_capabilities=("test",),
        success_criteria=("test",),
        source_document_ids=(),
        status="active",
        confirmed_by_user=True,
        created_at=NOW,
        confirmed_at=NOW,
        reason_codes=("TEST",),
    )
    plan = LearningPlan(
        plan_id=plan_id,
        version=1,
        learning_goal_id=goal_id,
        planning_horizon={},
        objective_ids=[objective_id],
        activity_ids=[activity_id],
        constraints={},
        assumptions={},
        created_from_learner_state_version=0,
        knowledge_graph_version="test",
        reason_codes=[],
        status="active",
    )
    activity = LearningActivity(
        activity_id=activity_id,
        plan_id=plan_id,
        plan_version=1,
        objective_id=objective_id,
        type="learn_new",
        knowledge_unit_ids=[uuid4()],
        estimated_duration_minutes=5,
        priority=1,
        reason_codes=[],
        status="planned",
    )
    async with factory() as session:
        session.add_all(
            [
                LearningGoalRecord(
                    id=f"{goal_id}:1",
                    goal_id=str(goal_id),
                    user_id=str(user_id),
                    version=1,
                    status="active",
                    idempotency_key="migration-goal",
                    payload=goal.model_dump(mode="json"),
                ),
                LearningPlanRecord(
                    id=f"{plan_id}:1",
                    plan_id=str(plan_id),
                    learning_goal_id=str(goal_id),
                    idempotency_key="migration-plan",
                    version=1,
                    status="active",
                    payload=plan.model_dump(mode="json"),
                ),
                LearningActivityRecord(
                    id=str(activity_id),
                    plan_id=str(plan_id),
                    plan_version=1,
                    priority=1,
                    payload=activity.model_dump(mode="json"),
                ),
                BookLearningTranscriptTurnRecord(
                    turn_record_id=str(uuid4()),
                    user_id=str(user_id),
                    goal_id=str(goal_id),
                    plan_id=str(plan_id),
                    plan_version=1,
                    activity_id=str(activity_id),
                    session_id=str(uuid4()),
                    turn_id="accepted-turn",
                    turn_number=1,
                    turn_kind="learner",
                    idempotency_key="migration-turn",
                    learner_text="accepted",
                    response_payload={},
                    created_at=NOW,
                ),
            ]
        )
        await session.commit()
    await engine.dispose()

    _alembic(database_url, "upgrade", LIFECYCLE_REVISION)
    engine = create_async_engine(database_url)
    async with engine.connect() as connection:
        row = (
            await connection.execute(
                select(
                    LearningActivityStateRecord.status,
                    LearningActivityStateRecord.transition_reason,
                    LearningActivityStateRecord.completed_at,
                ).where(
                    LearningActivityStateRecord.activity_id == str(activity_id)
                )
            )
        ).one()
        assert row.status == "active"
        assert row.transition_reason == "BACKFILL_ACCEPTED_CURRENT_USER_TRANSCRIPT"
        assert row.completed_at is None
        counts = (
            await connection.execute(
                select(
                    LearningActivityStateRecord.activity_id,
                    LearningActivityStateRecord.plan_id,
                    LearningActivityStateRecord.plan_version,
                )
            )
        ).all()
        assert counts == [(str(activity_id), str(plan_id), 1)]
    await engine.dispose()

    _alembic(database_url, "downgrade", PREVIOUS_HEAD)
    _alembic(database_url, "upgrade", LIFECYCLE_REVISION)
    engine = create_async_engine(database_url)
    async with engine.connect() as connection:
        restored = await connection.scalar(
            select(LearningActivityStateRecord.status).where(
                LearningActivityStateRecord.activity_id == str(activity_id)
            )
        )
        assert restored == "active"
    await engine.dispose()


@pytest.mark.asyncio
async def test_exec030_migration_creates_both_lifecycle_tables(tmp_path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'activity-empty.db'}"
    _alembic(database_url, "upgrade", LIFECYCLE_REVISION)
    engine = create_async_engine(database_url)
    async with engine.connect() as connection:
        tables = await connection.run_sync(lambda sync: set(inspect(sync).get_table_names()))
    await engine.dispose()
    assert {
        "learning_activity_state_versions",
        "activity_lifecycle_command_receipts",
    } <= tables

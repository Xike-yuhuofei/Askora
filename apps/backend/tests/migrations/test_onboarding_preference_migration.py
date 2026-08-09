"""PERSIST-301 existing-user backfill and new-user migration evidence."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import func, inspect, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.schema import CreateTable

from app.models.onboarding import (
    OnboardingPreferenceCommandReceiptRecord,
    OnboardingPreferenceRecord,
)
from app.models.user import User
from app.repositories.onboarding_preferences import OnboardingPreferenceRepository

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PREVIOUS_HEAD = "d2f0410a33c3"
ONBOARDING_REVISION = "f1061a0b9c01"
POSTGRES_TEST_URL = os.environ.get("ASKORA_POSTGRES_TEST_URL")


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
async def test_existing_user_is_backfilled_dismissed_without_completion_guess(tmp_path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'onboarding.db'}"
    _alembic(database_url, "upgrade", PREVIOUS_HEAD)
    engine = create_async_engine(database_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    user = User(
        id=str(uuid4()),
        pseudonym_id=uuid4().hex,
        phone_hash=uuid4().hex,
        password_hash="hash",
    )
    async with factory() as session:
        session.add(user)
        await session.commit()
    await engine.dispose()

    _alembic(database_url, "upgrade", ONBOARDING_REVISION)
    engine = create_async_engine(database_url)
    async with engine.connect() as connection:
        row = (
            await connection.execute(
                select(
                    OnboardingPreferenceRecord.visibility,
                    OnboardingPreferenceRecord.dismissed_reason,
                ).where(OnboardingPreferenceRecord.user_id == user.id)
            )
        ).one()
        assert row.visibility == "DISMISSED"
        assert row.dismissed_reason == "LEGACY_EXISTING_USER_BACKFILL"
        tables = await connection.run_sync(lambda sync: set(inspect(sync).get_table_names()))
        assert {
            "onboarding_preferences",
            "onboarding_preference_command_receipts",
        } <= tables
    await engine.dispose()


@pytest.mark.asyncio
async def test_user_created_after_migration_starts_active_and_survives_restart(
    tmp_path,
) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'new-user.db'}"
    _alembic(database_url, "upgrade", ONBOARDING_REVISION)
    engine = create_async_engine(database_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    user = User(
        id=str(uuid4()),
        pseudonym_id=uuid4().hex,
        phone_hash=uuid4().hex,
        password_hash="hash",
    )
    async with factory() as session:
        session.add(user)
        await session.commit()
    async with factory() as session:
        record = await OnboardingPreferenceRepository(session).get_or_create_active(
            user_id=user.id,
            journey_id="first-learning-v1",
            now=datetime(2026, 8, 9, 13, 0, tzinfo=timezone.utc),
        )
        assert record.visibility == "ACTIVE"
        assert record.preference_version == 1
        await session.commit()
    async with factory() as restarted:
        count = await restarted.scalar(
            select(func.count(OnboardingPreferenceRecord.preference_id)).where(
                OnboardingPreferenceRecord.user_id == user.id
            )
        )
        assert count == 1
    await engine.dispose()


def test_onboarding_schema_compiles_to_postgresql_without_dialect_fallback() -> None:
    preference_sql = str(
        CreateTable(OnboardingPreferenceRecord.__table__).compile(dialect=postgresql.dialect())
    )
    receipt_sql = str(
        CreateTable(OnboardingPreferenceCommandReceiptRecord.__table__).compile(
            dialect=postgresql.dialect()
        )
    )
    assert "TIMESTAMP WITH TIME ZONE" in preference_sql
    assert "ON DELETE CASCADE" in preference_sql
    assert "UNIQUE (user_id, journey_id)" in preference_sql
    assert "UNIQUE (user_id, journey_id, idempotency_key)" in receipt_sql
    assert not {
        "document_ref",
        "goal_ref",
        "plan_ref",
        "activity_ref",
        "transcript_ref",
        "step_completion",
    } & set(OnboardingPreferenceRecord.__table__.columns.keys())


def _postgres_async_url(value: str) -> str:
    if value.startswith("postgresql+asyncpg://"):
        return value
    if value.startswith("postgresql://"):
        return value.replace("postgresql://", "postgresql+asyncpg://", 1)
    raise ValueError("ASKORA_POSTGRES_TEST_URL must use PostgreSQL")


@pytest.mark.skipif(
    not POSTGRES_TEST_URL,
    reason="ASKORA_POSTGRES_TEST_URL is required for live onboarding migration evidence",
)
@pytest.mark.asyncio
async def test_postgres_head_contains_onboarding_constraints() -> None:
    assert POSTGRES_TEST_URL is not None
    engine = create_async_engine(_postgres_async_url(POSTGRES_TEST_URL))
    async with engine.connect() as connection:
        tables = await connection.run_sync(lambda sync: set(inspect(sync).get_table_names()))
        assert {
            "onboarding_preferences",
            "onboarding_preference_command_receipts",
        } <= tables
        unique_constraints = await connection.run_sync(
            lambda sync: {
                item["name"]
                for item in inspect(sync).get_unique_constraints("onboarding_preferences")
            }
        )
        assert "uq_onboarding_preference_user_journey" in unique_constraints
    await engine.dispose()

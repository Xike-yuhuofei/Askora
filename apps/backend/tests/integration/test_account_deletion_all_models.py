"""EXEC-053: All-surface data erasure manifest tests for v1 LocalOwner architecture.

Rewrite: Replaced multi-user cross-reference tests with single LocalOwner
data erasure verification. v1 is single-user LocalOwnerContext - no cross-user
relations or isolation needed.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, LargeBinary, Numeric, insert, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base
from app.infrastructure.privacy import (
    OWNER_ERASURE_ORDER,
    SUBJECT_REGISTRY,
    PrivacyInventoryRepository,
    RegistryDisposition,
)
from app.models.ledger import OutboxTaskRecord
from app.models.planning import LearningActivityRecord, LearningGoalRecord, LearningPlanRecord
from app.models.user import User, UserRole, UserStatus


async def _database(tmp_path: Path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'privacy.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


def _user(user_id: str, pseudonym_id: str) -> User:
    return User(
        id=user_id,
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        account_lifecycle="active",
        password_hash="hash",
        credential_version=1,
        pseudonym_id=pseudonym_id,
        is_verified=False,
    )


@pytest.mark.asyncio
async def test_iterative_manifest_reaches_goal_plan_activity_and_task(tmp_path: Path) -> None:
    """Verify manifest building traverses all planning layers for LocalOwner."""
    engine, factory = await _database(tmp_path)
    now = datetime.now(timezone.utc)
    async with factory() as session:
        session.add(_user("local-owner", "local-pseudo"))
        session.add_all(
            [
                LearningGoalRecord(
                    id="goal:1",
                    goal_id="goal-1",
                    user_id="local-owner",
                    version=1,
                    status="active",
                    idempotency_key="goal-key",
                    payload={"user_id": "local-owner"},
                ),
                LearningPlanRecord(
                    id="plan:1",
                    plan_id="plan-1",
                    learning_goal_id="goal-1",
                    idempotency_key="plan-key",
                    version=1,
                    status="active",
                    payload={"goal_id": "goal-1"},
                ),
                LearningActivityRecord(
                    id="activity-1",
                    plan_id="plan-1",
                    plan_version=1,
                    priority=1.0,
                    payload={"plan_id": "plan-1"},
                ),
                OutboxTaskRecord(
                    id="task-1",
                    type="activity.project",
                    schema_version="1.0",
                    payload={"activity_id": "activity-1"},
                    status="pending",
                    idempotency_key="task-key",
                    attempt_count=0,
                    next_attempt_at=now,
                    created_at=now,
                    updated_at=now,
                ),
            ]
        )
        await session.commit()

        manifest = await PrivacyInventoryRepository(session).build_manifest(
            user_id="local-owner",
            pseudonym_id="local-pseudo",
            subject_digest="a" * 64,
        )
        selected = {(entry.table_name, entry.record_id) for entry in manifest.entries}
        assert not manifest.blocking_issues
        assert ("learning_goal_versions", "id=goal:1") in selected
        assert ("learning_plan_versions", "id=plan:1") in selected
        assert ("learning_activities", "id=activity-1") in selected
        assert ("outbox_tasks", "id=task-1") in selected
    await engine.dispose()


@pytest.mark.asyncio
async def test_unknown_table_blocks_manifest_for_local_owner(tmp_path: Path) -> None:
    """Verify unregistered tables produce blocking issues in manifest."""
    engine, factory = await _database(tmp_path)
    async with engine.begin() as connection:
        await connection.execute(
            text("CREATE TABLE future_user_notes (id TEXT PRIMARY KEY, user_id TEXT)")
        )
    async with factory() as session:
        session.add(_user("local-owner", "local-pseudo"))
        await session.commit()
        manifest = await PrivacyInventoryRepository(session).build_manifest(
            user_id="local-owner",
            pseudonym_id="local-pseudo",
            subject_digest="a" * 64,
        )
        codes = {issue.code for issue in manifest.blocking_issues}
        assert "PRIVACY_REGISTRY_TABLE_UNCLASSIFIED" in codes
    await engine.dispose()


def _fixture_value(column, table_index: int):
    if isinstance(column.type, Boolean):
        return False
    if isinstance(column.type, Integer):
        return table_index + 1
    if isinstance(column.type, (Float, Numeric)):
        return 1.0
    if isinstance(column.type, DateTime):
        return datetime.now(timezone.utc)
    if isinstance(column.type, JSON):
        return {}
    if isinstance(column.type, LargeBinary):
        return b"fixture"
    if getattr(column.type, "enums", None):
        return column.type.enums[0]
    return f"fixture-{table_index}-{column.name}"


@pytest.mark.asyncio
async def test_representative_fixture_selects_every_erasable_registered_table(
    tmp_path: Path,
) -> None:
    """One representative row per ERASE registry entry guards all-table drift."""
    engine, factory = await _database(tmp_path)
    storage_base = tmp_path / "documents"
    representative_file = storage_base / "local-pseudo" / "representative.bin"
    representative_file.parent.mkdir(parents=True)
    representative_file.write_bytes(b"private representative content")
    async with factory() as session:
        session.add(_user("local-owner", "local-pseudo"))
        await session.commit()

    async with engine.connect() as connection:
        await connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        await connection.exec_driver_sql("PRAGMA ignore_check_constraints=ON")
        await connection.commit()
        for table_index, (table_name, registry) in enumerate(SUBJECT_REGISTRY.items()):
            if registry.disposition is not RegistryDisposition.ERASE:
                continue
            table = Base.metadata.tables.get(table_name)
            if table is None:
                continue
            values = {}
            for column in table.columns:
                if column.server_default is not None or column.autoincrement is True:
                    continue
                if column.nullable and not column.primary_key:
                    continue
                values[column.name] = _fixture_value(column, table_index)
            for column_name in registry.subject_columns:
                values[column_name] = (
                    "local-pseudo" if "pseudonym" in column_name else "local-owner"
                )
            if registry.subject_digest_column:
                values[registry.subject_digest_column] = "digest-a"
            if registry.reference_columns:
                values[registry.reference_columns[0]] = "local-owner"
            if registry.json_columns:
                values[registry.json_columns[0]] = {"subject": "local-owner"}
            if table_name == "user_documents":
                values["storage_path"] = "local-pseudo/representative.bin"
            try:
                await connection.execute(insert(table).values(**values))
            except Exception:
                pass
        await connection.commit()

    async with factory() as session:
        manifest = await PrivacyInventoryRepository(session).build_manifest(
            user_id="local-owner",
            pseudonym_id="local-pseudo",
            subject_digest="account-digest",
            subject_digests=("digest-a",),
            storage_base_path=storage_base,
        )
        selected_tables = {entry.table_name for entry in manifest.entries}
        expected_tables = {
            name
            for name, entry in SUBJECT_REGISTRY.items()
            if entry.disposition is RegistryDisposition.ERASE and name in Base.metadata.tables
        }
        assert not manifest.blocking_issues
        assert selected_tables == expected_tables
        repository = PrivacyInventoryRepository(session, storage_base_path=storage_base)
        for owner in OWNER_ERASURE_ORDER:
            await repository.erase_owner(owner=owner, manifest=manifest)
            await session.commit()
        residual = await repository.build_manifest(
            user_id="local-owner",
            pseudonym_id="local-pseudo",
            subject_digest="account-digest",
            subject_digests=("digest-a",),
            storage_base_path=storage_base,
        )
        assert not residual.entries
        assert not residual.blocking_issues
        assert not representative_file.exists()
    await engine.dispose()

"""EXEC-047 LocalOwner migration evidence: fresh, legacy single, ambiguous, replay."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PREVIOUS_HEAD = "p107d2f1a04"
LOCAL_OWNER_REVISION = "b1c0d2f3a001"


def _alembic(database_url: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["DATABASE_URL"] = database_url
    return subprocess.run(  # noqa: S603
        [sys.executable, "-m", "alembic", *arguments],
        cwd=BACKEND_ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )


async def _insert_user(engine, *, user_id: str, pseudonym_id: str, status: str = "ACTIVE") -> None:
    async with engine.begin() as connection:
        users = await connection.run_sync(
            lambda sync: sa.Table("users", sa.MetaData(), autoload_with=sync)
        )
        await connection.execute(
            users.insert().values(
                id=user_id,
                role="USER",
                status=status,
                is_verified=False,
                pseudonym_id=pseudonym_id,
            )
        )


async def _owner_columns(engine) -> tuple[list[str], int, str]:
    async with engine.connect() as connection:

        def _load(sync) -> tuple[list[str], int, str]:
            owners = sa.Table("local_owners", sa.MetaData(), autoload_with=sync)
            rows = sync.execute(sa.select(owners.c.owner_id, owners.c.provenance)).all()
            return (
                [c["name"] for c in inspect(sync).get_columns("local_owners")],
                len(rows),
                (rows[0][0] if rows else ""),
            )

        return await connection.run_sync(_load)


@pytest.mark.asyncio
async def test_model_matches_migration_via_alembic_check_fresh(tmp_path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'check.db'}"
    _alembic(database_url, "upgrade", "head")
    _alembic(database_url, "check")  # proves ORM model matches migration schema


@pytest.mark.asyncio
async def test_fresh_db_migration_creates_empty_table(tmp_path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'fresh.db'}"
    _alembic(database_url, "upgrade", "head")
    engine = create_async_engine(database_url)
    columns, count, owner_id = await _owner_columns(engine)
    assert count == 0  # fresh store bootstraps at runtime, not in migration
    assert {
        "singleton_key",
        "owner_id",
        "schema_version",
        "provenance",
        "legacy_user_id",
        "legacy_pseudonym_id",
        "created_at",
    } == set(columns)
    await engine.dispose()


@pytest.mark.asyncio
async def test_legacy_single_learner_migrates_to_stable_owner(tmp_path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'legacy-single.db'}"
    _alembic(database_url, "upgrade", PREVIOUS_HEAD)
    engine = create_async_engine(database_url)
    legacy_id, pseudo = str(uuid4()), "pseudo_legacy"
    await _insert_user(engine, user_id=legacy_id, pseudonym_id=pseudo)
    await engine.dispose()

    _alembic(database_url, "upgrade", "head")
    engine = create_async_engine(database_url)
    columns, count, owner_id = await _owner_columns(engine)
    assert count == 1
    # legacy uuid primary key is reused as-is (stable canonical owner)
    assert owner_id == legacy_id
    await engine.dispose()


@pytest.mark.asyncio
async def test_ambiguous_multi_subject_migration_fails_closed(tmp_path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'ambiguous.db'}"
    _alembic(database_url, "upgrade", PREVIOUS_HEAD)
    engine = create_async_engine(database_url)
    await _insert_user(engine, user_id=str(uuid4()), pseudonym_id="pseudo_a")
    await _insert_user(engine, user_id=str(uuid4()), pseudonym_id="pseudo_b")
    await engine.dispose()

    with pytest.raises(subprocess.CalledProcessError) as excinfo:
        _alembic(database_url, "upgrade", "head")
    stdout = (excinfo.value.stdout or "") + (excinfo.value.stderr or "")
    assert "LOCAL_OWNER_AMBIGUOUS" in stdout

    # fail closed: upgrade left no owner row and deleted no legacy data.
    engine = create_async_engine(database_url)
    async with engine.connect() as connection:
        owner_count, remaining = await connection.run_sync(
            lambda sync: (
                sync.execute(
                    sa.select(
                        sa.func.count(
                            sa.Table(
                                "local_owners", sa.MetaData(), autoload_with=sync
                            ).c.singleton_key
                        )
                    )
                ).scalar(),
                sync.execute(
                    sa.select(
                        sa.func.count(sa.Table("users", sa.MetaData(), autoload_with=sync).c.id)
                    )
                ).scalar(),
            )
        )
        assert owner_count == 0
        assert remaining == 2
    await engine.dispose()


@pytest.mark.asyncio
async def test_owner_mapping_is_replayable_and_deterministic(tmp_path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'replay.db'}"
    _alembic(database_url, "upgrade", PREVIOUS_HEAD)
    engine = create_async_engine(database_url)
    legacy_id = str(uuid4())
    await _insert_user(engine, user_id=legacy_id, pseudonym_id="pseudo_replay")
    await engine.dispose()

    _alembic(database_url, "upgrade", "head")
    engine = create_async_engine(database_url)
    _, _, first_owner = await _owner_columns(engine)
    await engine.dispose()

    _alembic(database_url, "downgrade", PREVIOUS_HEAD)
    _alembic(database_url, "upgrade", "head")
    engine = create_async_engine(database_url)
    _, count, second_owner = await _owner_columns(engine)
    assert count == 1
    assert second_owner == first_owner
    await engine.dispose()


def test_migration_heads_are_clean() -> None:
    result = _alembic("sqlite+aiosqlite:///:memory:", "heads")
    assert "c189s0e0a001 (head)" in result.stdout

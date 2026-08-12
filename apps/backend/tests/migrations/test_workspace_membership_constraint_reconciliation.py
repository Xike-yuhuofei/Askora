"""EXEC-074 regression tests for Workspace membership constraint reconciliation."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import MetaData, Table, func, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PREVIOUS_HEAD = "x174e0e0a002"
CURRENT_HEAD = "c189s0e0a001"

MEMBERSHIPS = (
    (
        "project_materials",
        "uq_project_material",
        ("project_id", "material_id"),
        {"project_id": "project-1", "material_id": "material-1"},
    ),
    (
        "learning_session_materials",
        "uq_learning_session_material",
        ("session_id", "material_id"),
        {"session_id": "session-1", "material_id": "material-1"},
    ),
)


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


async def _schema_snapshot(database_url: str) -> dict[str, dict[str, object]]:
    engine = create_async_engine(database_url)
    try:
        async with engine.connect() as connection:
            return await connection.run_sync(
                lambda sync: {
                    table_name: {
                        "primary_key": tuple(
                            inspect(sync).get_pk_constraint(table_name)["constrained_columns"]
                        ),
                        "unique_names": {
                            constraint["name"]
                            for constraint in inspect(sync).get_unique_constraints(table_name)
                        },
                    }
                    for table_name, _constraint_name, _columns, _values in MEMBERSHIPS
                }
            )
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_upgrade_preserves_rows_and_composite_primary_keys(tmp_path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'membership.db'}"
    _alembic(database_url, "upgrade", PREVIOUS_HEAD)

    before = await _schema_snapshot(database_url)
    for table_name, constraint_name, columns, _values in MEMBERSHIPS:
        assert before[table_name]["primary_key"] == columns
        assert constraint_name in before[table_name]["unique_names"]

    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.execute(text("PRAGMA foreign_keys=OFF"))
        for table_name, _constraint_name, _columns, values in MEMBERSHIPS:
            table = await connection.run_sync(
                lambda sync, name=table_name: Table(name, MetaData(), autoload_with=sync)
            )
            await connection.execute(table.insert().values(**values))
    await engine.dispose()

    _alembic(database_url, "upgrade", "head")
    after = await _schema_snapshot(database_url)
    for table_name, constraint_name, columns, _values in MEMBERSHIPS:
        assert after[table_name]["primary_key"] == columns
        assert constraint_name not in after[table_name]["unique_names"]

    engine = create_async_engine(database_url)
    async with engine.connect() as connection:
        for table_name, _constraint_name, _columns, values in MEMBERSHIPS:
            table = await connection.run_sync(
                lambda sync, name=table_name: Table(name, MetaData(), autoload_with=sync)
            )
            count = (await connection.execute(select(func.count()).select_from(table))).scalar_one()
            assert count == 1
            with pytest.raises(IntegrityError):
                async with connection.begin_nested():
                    await connection.execute(table.insert().values(**values))
    await engine.dispose()


@pytest.mark.asyncio
async def test_downgrade_restores_named_constraints_and_reupgrade_is_clean(tmp_path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'roundtrip.db'}"
    _alembic(database_url, "upgrade", "head")
    _alembic(database_url, "downgrade", PREVIOUS_HEAD)

    downgraded = await _schema_snapshot(database_url)
    for table_name, constraint_name, columns, _values in MEMBERSHIPS:
        assert downgraded[table_name]["primary_key"] == columns
        assert constraint_name in downgraded[table_name]["unique_names"]

    _alembic(database_url, "upgrade", "head")
    checked = _alembic(database_url, "check")
    assert "No new upgrade operations detected" in checked.stdout

    result = _alembic(database_url, "current")
    assert CURRENT_HEAD in result.stdout

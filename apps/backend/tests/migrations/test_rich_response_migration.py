"""EXEC-014 additive dialog render-payload migration evidence."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.contracts.rendering import markdown_render_payload
from app.models.dialog import DialogMessage, DialogSession, MessageRole, SessionStatus
from app.models.user import User, UserRole, UserStatus

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PREVIOUS_HEAD = "d6a1c3f90308"


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
async def test_render_ac_001_002_migration_forward_rollback_and_legacy_fallback(
    tmp_path: Path,
) -> None:
    """RENDER-020/021 and EXEC014-AC-007: additive nullable JSON is recoverable."""
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'rich-response.db'}"
    _alembic(database_url, "upgrade", PREVIOUS_HEAD)

    previous = create_async_engine(database_url)
    async with previous.connect() as connection:
        columns = await connection.run_sync(
            lambda sync: {column["name"] for column in inspect(sync).get_columns("dialog_messages")}
        )
        assert "render_payload" not in columns
    await previous.dispose()

    _alembic(database_url, "upgrade", "head")
    upgraded = create_async_engine(database_url)
    factory = async_sessionmaker(upgraded, expire_on_commit=False)
    async with factory() as session:
        user = User(
            id="render-user",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            pseudonym_id="render-pseudonym",
        )
        dialog = DialogSession(
            id="render-session",
            user_id=user.id,
            pseudonym_id=user.pseudonym_id,
            status=SessionStatus.ACTIVE,
        )
        rich = markdown_render_payload("# 可读内容")
        assert rich is not None
        message = DialogMessage(
            id="render-message",
            session_id=dialog.id,
            user_id=user.id,
            role=MessageRole.ASSISTANT,
            content="可读内容",
            render_payload=rich.model_dump(mode="json"),
            turn_number=1,
            moderation_result={},
            watermark_info={},
        )
        session.add_all([user, dialog, message])
        await session.commit()
    await upgraded.dispose()

    _alembic(database_url, "downgrade", PREVIOUS_HEAD)
    rolled_back = create_async_engine(database_url)
    async with rolled_back.connect() as connection:
        columns = await connection.run_sync(
            lambda sync: {column["name"] for column in inspect(sync).get_columns("dialog_messages")}
        )
        content = (
            await connection.exec_driver_sql(
                "SELECT content FROM dialog_messages WHERE id = ?",
                ("render-message",),
            )
        ).scalar_one()
        assert "render_payload" not in columns
        assert content == "可读内容"
    await rolled_back.dispose()

    _alembic(database_url, "upgrade", "head")
    forward_fixed = create_async_engine(database_url)
    async with forward_fixed.connect() as connection:
        row = (
            await connection.exec_driver_sql(
                "SELECT content, render_payload FROM dialog_messages WHERE id = ?",
                ("render-message",),
            )
        ).one()
        assert row == ("可读内容", None)
    await forward_fixed.dispose()

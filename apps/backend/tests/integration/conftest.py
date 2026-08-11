"""Shared real-SQLite fixtures for backend integration contracts."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base


@pytest.fixture
async def sqlite_factory(tmp_path) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """Create a disposable SQLite store with production FK enforcement."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'integration.db'}")

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()

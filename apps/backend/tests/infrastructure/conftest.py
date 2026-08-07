from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models import ledger as ledger_models  # noqa: F401


@pytest.fixture
async def sqlite_factory(tmp_path) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """Synthetic SQLite fixture with FK discipline enabled (PERSIST-050)."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'ledger.db'}")

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()

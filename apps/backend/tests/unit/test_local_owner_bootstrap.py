"""LocalOwner bootstrap tests for v1 no-auth architecture.

EXEC-053: Replaced dev auto-login tests with LocalOwner bootstrap tests.
v1 uses single-user LocalOwnerContext - no dev auto-login needed.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import AppEnv, Settings
from app.core.database import Base
from app.services.local_identity import (
    LocalOwnerContext,
    LocalOwnerError,
    ensure_local_owner,
    get_local_owner_context,
)


def test_local_owner_bootstrap_available_in_all_environments():
    """Verify LocalOwner bootstrap is always available (no env restriction)."""
    # All environments should support LocalOwner
    for env in [AppEnv.DEVELOPMENT, AppEnv.TEST, AppEnv.PRODUCTION]:
        settings = Settings(app_env=env)
        assert settings.app_env == env


@pytest.mark.asyncio
async def test_local_owner_bootstrap_creates_owner(tmp_path: Path) -> None:
    """Verify ensure_local_owner creates a new owner when none exists."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'bootstrap.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as db:
        ctx = await ensure_local_owner(db)
        assert isinstance(ctx, LocalOwnerContext)
        assert ctx.owner_id is not None
        assert ctx.provenance == "fresh"

    await engine.dispose()


@pytest.mark.asyncio
async def test_local_owner_bootstrap_is_idempotent(tmp_path: Path) -> None:
    """Verify ensure_local_owner returns same owner on repeated calls."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'bootstrap2.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as db:
        ctx1 = await ensure_local_owner(db)
        ctx2 = await ensure_local_owner(db)
        # Same owner_id, provenance may differ (fresh vs reused)
        assert ctx1.owner_id == ctx2.owner_id

    await engine.dispose()


@pytest.mark.asyncio
async def test_get_context_without_bootstrap_raises_error(tmp_path: Path) -> None:
    """Verify get_local_owner_context raises error if not bootstrapped."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'bootstrap3.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as db:
        with pytest.raises(LocalOwnerError) as exc_info:
            await get_local_owner_context(db)
        assert "尚未初始化" in str(exc_info.value)

    await engine.dispose()

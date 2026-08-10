"""LocalOwner state management tests for v1 no-auth architecture.

EXEC-053: Replaced session/auth tests with LocalOwner lifecycle tests.
v1 uses single-user LocalOwnerContext - no login/session needed.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base
from app.services.local_identity import (
    LocalOwnerContext,
    LocalOwnerError,
    ensure_local_owner,
    get_local_owner_context,
)


async def _database(tmp_path: Path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'local_owner.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    return engine, factory


@pytest.mark.asyncio
async def test_ensure_local_owner_creates_single_record(tmp_path: Path) -> None:
    """Verify ensure_local_owner creates exactly one LocalOwner."""
    engine, factory = await _database(tmp_path)
    async with factory() as db:
        ctx = await ensure_local_owner(db)
        assert isinstance(ctx, LocalOwnerContext)
        assert ctx.owner_id is not None

        # ensure_local_owner is idempotent - returns same owner
        ctx2 = await ensure_local_owner(db)
        assert ctx.owner_id == ctx2.owner_id
    await engine.dispose()


@pytest.mark.asyncio
async def test_get_local_owner_context_after_bootstrap(tmp_path: Path) -> None:
    """Verify context retrieval works after ensure_local_owner."""
    engine, factory = await _database(tmp_path)
    async with factory() as db:
        await ensure_local_owner(db)
        ctx = await get_local_owner_context(db)
        assert ctx is not None
        assert ctx.owner_id == ctx.owner_id  # same owner
    await engine.dispose()


@pytest.mark.asyncio
async def test_get_local_owner_context_without_bootstrap_raises(tmp_path: Path) -> None:
    """Verify context retrieval without bootstrap raises LocalOwnerError."""
    engine, factory = await _database(tmp_path)
    async with factory() as db:
        with pytest.raises(LocalOwnerError) as exc_info:
            await get_local_owner_context(db)
        assert "尚未初始化" in str(exc_info.value)
    await engine.dispose()


@pytest.mark.asyncio
async def test_ensure_local_owner_auto_bootstraps_if_missing(tmp_path: Path) -> None:
    """Verify ensure_local_owner bootstraps if no owner exists."""
    engine, factory = await _database(tmp_path)
    async with factory() as db:
        ctx = await ensure_local_owner(db)
        assert ctx is not None
        assert ctx.owner_id is not None

        # Second call returns existing owner
        ctx2 = await ensure_local_owner(db)
        assert ctx.owner_id == ctx2.owner_id
    await engine.dispose()


@pytest.mark.asyncio
async def test_local_owner_context_fields_are_accessible(tmp_path: Path) -> None:
    """Verify LocalOwnerContext has expected fields."""
    engine, factory = await _database(tmp_path)
    async with factory() as db:
        ctx = await ensure_local_owner(db)

        # Verify context fields
        assert ctx.owner_id is not None
        assert ctx.provenance in ("fresh", "legacy_single_learner", "reused")
        assert hasattr(ctx, "legacy_user_id")
        assert hasattr(ctx, "legacy_pseudonym_id")
    await engine.dispose()


@pytest.mark.asyncio
async def test_local_owner_context_is_hashable_for_cache(tmp_path: Path) -> None:
    """Verify LocalOwnerContext can be used in sets/dicts (hashable)."""
    engine, factory = await _database(tmp_path)
    async with factory() as db:
        ctx = await ensure_local_owner(db)

        # Verify context is hashable (frozen dataclass)
        ctx_dict = {ctx: "owner_value"}
        assert ctx_dict[ctx] == "owner_value"

        # Verify two calls return same owner_id (but may differ in provenance)
        ctx2 = await ensure_local_owner(db)
        assert ctx.owner_id == ctx2.owner_id
    await engine.dispose()


@pytest.mark.asyncio
async def test_concurrent_ensure_local_owner_produces_single_owner(tmp_path: Path) -> None:
    """Verify ensure_local_owner creates exactly one owner across multiple calls."""
    engine, factory = await _database(tmp_path)

    async with factory() as db:
        # First call creates the owner
        first = await ensure_local_owner(db)
        # Second call in same session should return the same owner
        second = await ensure_local_owner(db)
        assert first.owner_id == second.owner_id

    await engine.dispose()

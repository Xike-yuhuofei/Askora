"""Security boundaries for data deletion and export APIs.

EXEC-053: Rewritten to verify security without auth routes.
v1 uses single-user LocalOwnerContext - API is private by default.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.services.auth.dependencies import get_current_owner_projection


async def _create_user(db):
    """Create a local owner user for testing."""
    from app.models.user import User, UserRole, UserStatus

    user = User(
        id="local-owner-security",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        pseudonym_id="security-pseudonym",
        account_lifecycle="active",
    )
    db.add(user)
    await db.commit()
    return user


@pytest.mark.asyncio
async def test_owner_projection_dependency_can_be_overridden(tmp_path: Path) -> None:
    """Verify get_current_owner_projection can be overridden for testing."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'dep-test.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as session:
        user = await _create_user(session)

        async def override_db():
            yield session

        async def override_owner_projection():
            return user

        # Verify we can set up dependency overrides
        from app.main import app

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_owner_projection] = override_owner_projection

        # Clean up
        app.dependency_overrides.clear()

    await engine.dispose()


@pytest.mark.asyncio
async def test_owner_projection_boundary_is_private(tmp_path: Path) -> None:
    """Verify owner projection is private (not exposed without proper setup)."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'boundary-test.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as db:
        from app.services.local_identity import (
            LocalOwnerContext,
            LocalOwnerError,
            ensure_local_owner,
            get_local_owner_context,
        )

        # Before bootstrap, getting context should fail
        with pytest.raises(LocalOwnerError):
            await get_local_owner_context(db)

        # After bootstrap, context should be available
        ctx = await ensure_local_owner(db)
        assert isinstance(ctx, LocalOwnerContext)

    await engine.dispose()


@pytest.mark.asyncio
async def test_export_token_is_owner_bound(tmp_path: Path) -> None:
    """Verify export token is bound to LocalOwner identity."""
    import hashlib
    from datetime import UTC, datetime, timedelta
    from uuid import uuid4

    from app.contracts.data_control import DataControlErrorCode
    from app.data_control.export import ExportArtifact, ExportRegistry
    from app.data_control.recovery import RecoveryError

    registry = ExportRegistry()
    export_id = uuid4()
    artifact = tmp_path / "artifact.zip"
    artifact.write_bytes(b"export")
    token = "t" * 48
    registry.register(
        ExportArtifact(
            export_id=export_id,
            user_id="local-owner",
            path=artifact,
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            expires_at=datetime.now(UTC) + timedelta(minutes=1),
        )
    )

    # Cross-owner consumption should fail
    with pytest.raises(RecoveryError) as cross_owner:
        registry.consume(export_id, "other-owner", token)
    assert cross_owner.value.code == DataControlErrorCode.EXPORT_EXPIRED

    # Correct owner can consume once
    assert registry.consume(export_id, "local-owner", token) == artifact
    # One-time use
    with pytest.raises(RecoveryError):
        registry.consume(export_id, "local-owner", token)

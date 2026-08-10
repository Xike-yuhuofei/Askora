"""Required evidence for the temporary LID-013 User ORM compatibility boundary."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base
from app.data_control.export import UserDataExporter
from app.models.user import User, UserRole, UserStatus
from app.services.local_identity import ensure_local_owner
from app.services.owner.dependencies import get_current_owner_projection


@pytest.mark.required
@pytest.mark.sqlite_integration
@pytest.mark.asyncio
async def test_fresh_local_owner_projection_is_complete_transient_user(tmp_path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'owner-projection.db'}")
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            owner = await ensure_local_owner(session)
            projection = await get_current_owner_projection(session)

            assert isinstance(projection, User)
            assert projection.id == owner.canonical_owner_id
            assert projection.pseudonym_id == owner.owner_id.hex
            assert projection.role == UserRole.USER
            assert projection.status == UserStatus.ACTIVE

            exported_profile = await UserDataExporter(session)._profile(projection)
            account = exported_profile["account"]
            assert account["nickname"] is None
            # Authentication-only fields (phone / email / real_name) are removed.
            assert "phone" not in account
            assert "email" not in account
            assert "real_name" not in account
    finally:
        await engine.dispose()

"""Required evidence for the temporary LID-013 User ORM compatibility boundary."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.user import User, UserRole, UserStatus
from app.services.auth.dependencies import get_current_owner_projection
from app.services.local_identity import ensure_local_owner


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
            assert projection.account_lifecycle == "active"

            # LID-003/LID-054: the fresh compatibility projection is not an
            # Account identity and never fabricates credential/PII material.
            assert projection.phone_encrypted is None
            assert projection.phone_hash is None
            assert projection.email_encrypted is None
            assert projection.password_hash is None
            assert projection.wechat_openid_encrypted is None
            assert projection.real_name_encrypted is None

            # The projection is deliberately transient: LocalOwner remains the
            # only durable identity truth and no compatibility User row is added.
            assert await session.get(User, owner.canonical_owner_id) is None
    finally:
        await engine.dispose()

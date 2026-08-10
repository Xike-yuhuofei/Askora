"""Required evidence for the temporary LID-013 User ORM compatibility boundary."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base
from app.data_control.export import UserDataExporter
from app.models.user import User, UserRole, UserStatus
from app.services.auth.dependencies import get_current_owner_projection
from app.services.local_identity import ensure_local_owner


@pytest.mark.required
@pytest.mark.sqlite_integration
@pytest.mark.asyncio
async def test_fresh_local_owner_projection_is_complete_compatibility_user(
    tmp_path,
) -> None:
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

            # Concrete legacy-consumer regression from the PR review: PROFILE
            # export must be able to read the complete compatibility projection
            # without AttributeError or fabricated personal data.
            exported_profile = await UserDataExporter(session)._profile(projection)
            assert exported_profile["account"]["nickname"] is None
            assert exported_profile["account"]["phone"] is None
            assert exported_profile["account"]["email"] is None
            assert exported_profile["account"]["real_name"] is None

            # LID-053: the compatibility User row is durable so that historical
            # user_id / pseudonym_id FK columns keep referential integrity
            # during migration. LocalOwner remains the only identity truth;
            # this row carries no login credential or PII.
            durable_row = await session.get(User, owner.canonical_owner_id)
            assert durable_row is not None
            assert durable_row.id == owner.canonical_owner_id
            assert durable_row.pseudonym_id == owner.owner_id.hex
            assert durable_row.role == UserRole.USER
            assert durable_row.status == UserStatus.ACTIVE
            assert durable_row.password_hash is None
            assert durable_row.phone_encrypted is None
            assert durable_row.email_encrypted is None
            assert durable_row.real_name_encrypted is None
    finally:
        await engine.dispose()

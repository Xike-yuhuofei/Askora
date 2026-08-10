"""EXEC-047 E047-AC-003 referential integrity: legacy owner refs resolve to LocalOwner."""

from __future__ import annotations

from uuid import uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.document import UserDocument
from app.models.planning import LearningGoalRecord
from app.models.user import User, UserRole, UserStatus
from app.services.auth.canonical_identity import canonical_user_id
from app.services.local_identity import ensure_local_owner


async def _factory(database_url: str):
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


@pytest.mark.asyncio
async def test_legacy_owner_refs_map_with_counts_unchanged(tmp_path) -> None:
    engine, factory = await _factory(f"sqlite+aiosqlite:///{tmp_path / 'integrity.db'}")
    legacy_id = str(uuid4())
    pseudonym_id = "pseudo_integrity"
    owner_id = str(canonical_user_id(legacy_id))

    async with factory() as session:
        session.add(
            User(
                id=legacy_id,
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                pseudonym_id=pseudonym_id,
            )
        )
        session.add(
            LearningGoalRecord(
                id=f"learning-goal:{legacy_id}:1",
                goal_id=str(uuid4()),
                user_id=owner_id,
                version=1,
                status="ACTIVE",
                idempotency_key=str(uuid4()),
                payload={"title": "legacy goal"},
            )
        )
        session.add(
            UserDocument(
                id=str(uuid4()),
                pseudonym_id=pseudonym_id,
                original_filename="legacy.pdf",
                file_extension="pdf",
                file_size_bytes=100,
                storage_path="/tmp/legacy.pdf",
            )
        )
        await session.commit()

    async with factory() as session:
        ctx = await ensure_local_owner(session)
        await session.commit()

        assert str(ctx.owner_id) == owner_id
        assert ctx.legacy_user_id == legacy_id
        assert ctx.legacy_pseudonym_id == pseudonym_id

        # counts unchanged after owner resolution
        goal_count = await session.scalar(sa.select(sa.func.count(LearningGoalRecord.id)))
        doc_count = await session.scalar(sa.select(sa.func.count(UserDocument.id)))
        assert goal_count == 1
        assert doc_count == 1

        # canonical owner resolves the legacy goal's stored user_id
        goal_user_ids = set(
            (await session.execute(sa.select(LearningGoalRecord.user_id))).scalars()
        )
        assert goal_user_ids == {owner_id}
    await engine.dispose()

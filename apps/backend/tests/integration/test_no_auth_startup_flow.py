"""No-auth startup and core learning flow regression tests.

EXEC: user authentication removal.
Askora is a local single-user learning app: the app must start directly into the
product UI without login/register/session/token, and core learning data must
persist across restarts keyed to the LocalOwner singleton (no account identity).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.dialog import DialogMessage, DialogSession, MessageRole
from app.models.document import ModerationStatus, ProcessingStatus, UserDocument
from app.models.local_owner import LocalOwnerRecord
from app.services.local_identity import ensure_local_owner, get_local_owner_context
from app.services.owner.dependencies import get_current_owner


@pytest.fixture
async def sqlite_factory(tmp_path) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'noauth.db'}")

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


@pytest.mark.asyncio
async def test_app_start_resolves_local_owner_without_any_credential(
    sqlite_factory,
) -> None:
    """Startup needs no login/session/token: the LocalOwner is resolved directly."""
    async with sqlite_factory() as session:
        # Simulates the lifespan bootstrap path: ensure_local_owner only.
        owner = await ensure_local_owner(session)
        await session.commit()

        # The no-auth dependency resolves the same owner without credentials.
        ctx = await get_local_owner_context(session)
        assert ctx.canonical_owner_id == owner.canonical_owner_id

        # Exactly one owner row exists; no users/accounts/sessions tables used.
        count = await session.scalar(select(func.count(LocalOwnerRecord.singleton_key)))
        assert count == 1


@pytest.mark.asyncio
async def test_core_learning_data_persists_across_restarts(sqlite_factory) -> None:
    """Learning records survive restart, keyed to LocalOwner, not an account."""
    async with sqlite_factory() as session:
        owner = await ensure_local_owner(session)
        await session.commit()

        # Create a dialog session + message and a document (core learning flow).
        session_id = str(uuid4())
        doc_id = str(uuid4())
        session.add(
            DialogSession(
                id=session_id,
                user_id=owner.canonical_owner_id,
                pseudonym_id=owner.legacy_pseudonym_id or owner.owner_id.hex,
                subject="数学",
                status="ACTIVE",
            )
        )
        session.add(
            DialogMessage(
                id=str(uuid4()),
                session_id=session_id,
                user_id=owner.canonical_owner_id,
                role=MessageRole.USER,
                content="什么是向量",
                turn_number=1,
            )
        )
        session.add(
            UserDocument(
                id=doc_id,
                pseudonym_id=owner.legacy_pseudonym_id or owner.owner_id.hex,
                original_filename="notes.pdf",
                file_extension="pdf",
                file_size_bytes=1024,
                storage_path=f"{owner.owner_id.hex}/{doc_id}.pdf",
                processing_status=ProcessingStatus.COMPLETED,
                metadata_version=1,
                moderation_status=ModerationStatus.APPROVED,
                moderation_categories=[],
                moderation_details={},
                chunk_count=0,
                total_tokens=0,
                access_count=0,
                is_deleted=False,
            )
        )
        await session.commit()

    # ---- restart (new session, same engine/db) ----
    async with sqlite_factory() as session:
        owner_after = await ensure_local_owner(session)
        assert owner_after.canonical_owner_id == owner.canonical_owner_id

        session_count = await session.scalar(
            select(func.count(DialogSession.id)).where(
                DialogSession.user_id == owner_after.canonical_owner_id
            )
        )
        message_count = await session.scalar(
            select(func.count(DialogMessage.id)).where(
                DialogMessage.user_id == owner_after.canonical_owner_id
            )
        )
        doc_count = await session.scalar(
            select(func.count(UserDocument.id)).where(
                UserDocument.pseudonym_id
                == (owner_after.legacy_pseudonym_id or owner_after.owner_id.hex)
            )
        )
        assert session_count == 1
        assert message_count == 1
        assert doc_count == 1


@pytest.mark.asyncio
async def test_current_owner_dependency_needs_no_credentials(sqlite_factory) -> None:
    """get_current_owner (the no-auth DI dependency) resolves without auth state."""
    async with sqlite_factory() as session:
        boot = await ensure_local_owner(session)
        await session.commit()
    async with sqlite_factory() as session:
        ctx = await get_current_owner(session)
        assert ctx.canonical_owner_id == boot.canonical_owner_id

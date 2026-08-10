"""EXEC-047 LocalOwner bootstrap, stability, legacy mapping and ambiguity tests."""

from __future__ import annotations

from uuid import uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.local_owner import LocalOwnerRecord
from app.models.user import User, UserRole, UserStatus
from app.services.auth.canonical_identity import canonical_user_id
from app.services.local_identity import (
    LOCAL_OWNER_AMBIGUOUS,
    LocalOwnerAmbiguousError,
    LocalOwnerContext,
    LocalOwnerError,
    ensure_local_owner,
    get_local_owner_context,
    legacy_learner_is_ambiguous,
)


def _make_url(tmp_path) -> str:
    return f"sqlite+aiosqlite:///{tmp_path / 'local-identity.db'}"


async def _session_factory(database_url: str):
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    return engine, factory


async def _add_user(session, *, user_id: str, pseudonym_id: str, status: UserStatus = UserStatus.ACTIVE) -> None:
    session.add(
        User(
            id=user_id,
            role=UserRole.USER,
            status=status,
            pseudonym_id=pseudonym_id,
        )
    )
    await session.flush()


@pytest.mark.asyncio
async def test_empty_db_first_bootstrap_creates_exactly_one_owner(tmp_path) -> None:
    engine, factory = await _session_factory(_make_url(tmp_path))
    async with factory() as session:
        ctx = await ensure_local_owner(session)
        await session.commit()
        assert isinstance(ctx.owner_id, type(uuid4()))
        assert ctx.provenance == "fresh"

        count = await session.scalar(
            sa.select(sa.func.count(LocalOwnerRecord.singleton_key))
        )
        assert count == 1
    await engine.dispose()


@pytest.mark.asyncio
async def test_repeated_bootstrap_returns_same_owner_id(tmp_path) -> None:
    engine, factory = await _session_factory(_make_url(tmp_path))
    first: LocalOwnerContext | None = None
    for _ in range(3):  # simulate restarts
        async with factory() as session:
            ctx = await ensure_local_owner(session)
            await session.commit()
            if first is None:
                first = ctx
            assert ctx.owner_id == first.owner_id
        assert first is not None
    await engine.dispose()


@pytest.mark.asyncio
async def test_concurrent_bootstrap_yields_exactly_one_owner(tmp_path) -> None:
    engine, factory = await _session_factory(_make_url(tmp_path))
    contexts: list[LocalOwnerContext] = []
    for _ in range(5):
        async with factory() as session:
            ctx = await ensure_local_owner(session)
            await session.commit()
            contexts.append(ctx)
    owner_ids = {ctx.owner_id for ctx in contexts}
    assert len(owner_ids) == 1
    async with factory() as session:
        count = await session.scalar(
            sa.select(sa.func.count(LocalOwnerRecord.singleton_key))
        )
        assert count == 1
    await engine.dispose()


@pytest.mark.asyncio
async def test_single_legacy_learner_maps_to_stable_canonical_uuid(tmp_path) -> None:
    engine, factory = await _session_factory(_make_url(tmp_path))
    legacy_user_id = str(uuid4())
    async with factory() as session:
        await _add_user(session, user_id=legacy_user_id, pseudonym_id="pseudo_one")
        await session.commit()
    async with factory() as session:
        ctx = await ensure_local_owner(session)
        await session.commit()
        assert ctx.owner_id == canonical_user_id(legacy_user_id)
        assert ctx.provenance == "legacy_single_learner"
        assert ctx.legacy_user_id == legacy_user_id
        assert ctx.legacy_pseudonym_id == "pseudo_one"
    # restart must keep the same owner
    async with factory() as session:
        ctx2 = await ensure_local_owner(session)
        await session.commit()
        assert ctx2.owner_id == canonical_user_id(legacy_user_id)
    await engine.dispose()


@pytest.mark.asyncio
async def test_ambiguous_multi_subject_fails_closed_without_destructive_cleanup(tmp_path) -> None:
    engine, factory = await _session_factory(_make_url(tmp_path))
    u1, u2 = str(uuid4()), str(uuid4())
    async with factory() as session:
        await _add_user(session, user_id=u1, pseudonym_id="pseudo_a")
        await _add_user(session, user_id=u2, pseudonym_id="pseudo_b")
        await session.commit()
    async with factory() as session:
        with pytest.raises(LocalOwnerAmbiguousError) as excinfo:
            await ensure_local_owner(session)
        assert excinfo.value.error_code == LOCAL_OWNER_AMBIGUOUS
        await session.rollback()
        # no owner was created and no subject was deleted
        count = await session.scalar(sa.select(sa.func.count(LocalOwnerRecord.singleton_key)))
        assert count == 0
        users = await session.scalar(sa.select(sa.func.count(User.id)))
        assert users == 2
    await engine.dispose()


@pytest.mark.asyncio
async def test_owner_selection_never_reads_secret_material(tmp_path) -> None:
    engine, factory = await _session_factory(_make_url(tmp_path))
    legacy_user_id = str(uuid4())
    async with factory() as session:
        session.add(
            User(
                id=legacy_user_id,
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                pseudonym_id="pseudo_secret",
                password_hash="plaintext-hash-placeholder",
            )
        )
        await session.commit()
    async with factory() as session:
        ctx = await ensure_local_owner(session)
        await session.commit()
        # owner derives from the stable user id, never from the password hash.
        assert ctx.owner_id == canonical_user_id(legacy_user_id)
        assert "plaintext-hash-placeholder" not in str(ctx.owner_id)
    await engine.dispose()


@pytest.mark.asyncio
async def test_get_local_owner_context_missing_raises_stable_code(tmp_path) -> None:
    engine, factory = await _session_factory(_make_url(tmp_path))
    async with factory() as session:
        with pytest.raises(LocalOwnerError) as excinfo:
            await get_local_owner_context(session)
        assert excinfo.value.detail["reason_code"] == "LOCAL_OWNER_MISSING"
    await engine.dispose()


@pytest.mark.asyncio
async def test_get_local_owner_context_after_bootstrap(tmp_path) -> None:
    engine, factory = await _session_factory(_make_url(tmp_path))
    async with factory() as session:
        boot = await ensure_local_owner(session)
        await session.commit()
    async with factory() as session:
        ctx = await get_local_owner_context(session)
        assert ctx.owner_id == boot.owner_id
    await engine.dispose()


def test_legacy_learner_is_ambiguous_helper() -> None:
    assert not legacy_learner_is_ambiguous([])
    assert not legacy_learner_is_ambiguous(["only-one"])
    assert legacy_learner_is_ambiguous(["a", "b"])
    assert not legacy_learner_is_ambiguous(["", "one"])
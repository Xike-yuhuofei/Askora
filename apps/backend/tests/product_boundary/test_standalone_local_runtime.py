"""XIK-167 — Standalone Local Runtime closure regression tests.

Verify Askora v1's default Local Web runtime:
- resolves to Askora-managed SQLite (`{data_dir}/askora.db`) with no DATABASE_URL;
- requires no Redis/PostgreSQL/Docker/JWT for startup, `/ready`, core learning
  loop or durable document jobs;
- `/ready` reflects true Required (SQLite) vs Optional (Redis) dependencies;
- local schema (re)init is non-destructive and preserves durable data.

These tests are part of the Required Product Boundary suite.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core import database as db_module
from app.core import redis_client as rc_module
from app.core.config import Settings
from app.observability import readiness_probe


def _clean_default_env(monkeypatch) -> None:
    """Remove env overrides so pure Settings defaults apply (bypasses .env)."""
    for key in ("DATABASE_URL", "REDIS_URL", "ASKORA_DATA_DIR", "APP_ENV", "HOST"):
        monkeypatch.delenv(key, raising=False)


def _reset_db_singletons() -> None:
    db_module._engine = None
    db_module._session_factory = None


def _reset_redis_singletons() -> None:
    rc_module._redis_client = None
    rc_module._redis_available = None


# ---------------------------------------------------------------------------
# Test 1 — Clean Local Startup
# ---------------------------------------------------------------------------


def test_default_config_resolves_to_managed_sqlite(monkeypatch) -> None:
    """EXEC060-AC-001: no DATABASE_URL → Askora-managed SQLite under data dir."""
    _clean_default_env(monkeypatch)
    s = Settings(_env_file=None)
    assert s.app_env.value == "local"
    assert s.database_url.startswith("sqlite+aiosqlite://")
    assert str(s.data_directory / "askora.db") in s.database_url
    assert s.redis_url == ""
    assert s.host == "127.0.0.1"


@pytest.mark.asyncio
async def test_clean_local_startup_and_readiness(tmp_path, monkeypatch) -> None:
    """Clean env (no PG/Redis/Docker/JWT) starts, creates managed SQLite, /ready PASS."""
    sqlite_url = f"sqlite+aiosqlite:///{tmp_path / 'askora.db'}"
    monkeypatch.setattr(db_module.settings, "database_url", sqlite_url)
    monkeypatch.setattr(db_module.settings, "askora_data_dir", str(tmp_path))
    monkeypatch.setattr(db_module.settings, "redis_url", "")
    _reset_db_singletons()
    _reset_redis_singletons()
    try:
        db_module.ensure_data_directory()
        await db_module.init_db()

        from app.services.local_identity import ensure_local_owner

        factory = db_module.get_session_factory()
        async with factory() as session:
            owner = await ensure_local_owner(session)
            await session.commit()
        assert owner is not None
        assert (tmp_path / "askora.db").exists()
        # No Redis configured → client is None, startup still succeeds.
        assert rc_module.get_redis_client() is None

        resp = await readiness_probe()
        assert resp.status_code == 200
        body = json.loads(resp.body)
        assert body["status"] == "ready"
        assert body["requirements"]["database"] is True
        assert body["requirements"]["redis"] is False
    finally:
        await db_module.close_db()
        _reset_db_singletons()
        _reset_redis_singletons()


# ---------------------------------------------------------------------------
# Test 2 — Redis Absence (core learning loop works with no Redis)
# ---------------------------------------------------------------------------


def test_core_learning_loop_works_without_redis(monkeypatch) -> None:
    """EXEC060-AC-002: no Redis → client None, KT degrades to memory, loop works."""
    monkeypatch.setattr(rc_module.settings, "redis_url", "")
    _reset_redis_singletons()
    assert rc_module.get_redis_client() is None

    from app.services.kt.knowledge_tracing_service import KnowledgeTracingService

    service = KnowledgeTracingService()
    assert service._redis is None
    before = service.get_mastery("u-xik167", "kp-algebra").p
    after = service.update_mastery("u-xik167", "kp-algebra", is_correct=True).p
    assert after > before


# ---------------------------------------------------------------------------
# Test 3 — SQLite Persistence across restart
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sqlite_persistence_survives_restart(tmp_path) -> None:
    """Test-3: durable data survives close/reopen of the same SQLite file."""
    import app.models  # noqa: F401  register all models on Base.metadata
    from app.models.local_owner import LocalOwnerRecord
    from app.services.local_identity import ensure_local_owner

    db_url = f"sqlite+aiosqlite:///{tmp_path / 'persist.db'}"

    def make_factory():
        engine = create_async_engine(db_url)

        @event.listens_for(engine.sync_engine, "connect")
        def _fk(dbapi_connection, _record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return engine, async_sessionmaker(engine, expire_on_commit=False)

    engine, factory = make_factory()
    async with engine.begin() as connection:
        await connection.run_sync(db_module.Base.metadata.create_all)
    async with factory() as session:
        owner = await ensure_local_owner(session)
        await session.commit()
        owner_id = owner.canonical_owner_id
    await engine.dispose()

    # ---- restart (new engine/session, same file) ----
    engine2, factory2 = make_factory()
    async with factory2() as session:
        owner2 = await ensure_local_owner(session)
        assert owner2.canonical_owner_id == owner_id
        count = await session.scalar(select(func.count(LocalOwnerRecord.singleton_key)))
        assert count == 1
    await engine2.dispose()


# ---------------------------------------------------------------------------
# Test 4 — Migration / schema safety (non-destructive local re-init)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_init_db_does_not_destructively_repair_existing_data(tmp_path, monkeypatch) -> None:
    """EXEC060-AC-006: local (re)init is non-destructive; durable rows survive."""
    import app.models  # noqa: F401
    from app.models.local_owner import LocalOwnerRecord
    from app.services.local_identity import ensure_local_owner

    sqlite_url = f"sqlite+aiosqlite:///{tmp_path / 'ndt.db'}"
    monkeypatch.setattr(db_module.settings, "database_url", sqlite_url)
    monkeypatch.setattr(db_module.settings, "askora_data_dir", str(tmp_path))
    _reset_db_singletons()
    try:
        await db_module.init_db()
        factory = db_module.get_session_factory()
        async with factory() as session:
            owner = await ensure_local_owner(session)
            await session.commit()
            owner_id = owner.canonical_owner_id

        # simulate a restart: re-init against the existing file
        await db_module.close_db()
        _reset_db_singletons()
        await db_module.init_db()

        factory = db_module.get_session_factory()
        async with factory() as session:
            owner2 = await ensure_local_owner(session)
            assert owner2.canonical_owner_id == owner_id
            count = await session.scalar(select(func.count(LocalOwnerRecord.singleton_key)))
            assert count == 1  # no data loss / no destructive repair
    finally:
        await db_module.close_db()
        _reset_db_singletons()


# ---------------------------------------------------------------------------
# Test 5 — Durable document job is SQLite/outbox-backed (no Redis)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_durable_document_job_is_sqlite_backed(tmp_path, monkeypatch) -> None:
    """EXEC060-AC-002: job truth is durable SQLite outbox, not Redis-only."""
    import app.models  # noqa: F401
    from app.infrastructure.outbox import OutboxProducer, OutboxStatus
    from app.models.ledger import OutboxTaskRecord
    from app.services.documents.document_service import (
        DOCUMENT_PROCESS_TASK_SCHEMA_VERSION,
        DOCUMENT_PROCESS_TASK_TYPE,
        document_processing_idempotency_key,
    )
    from app.services.documents.processing_worker import DocumentProcessingWorker

    monkeypatch.setattr(db_module.settings, "redis_url", "")
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'docjob.db'}")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(db_module.Base.metadata.create_all)

    doc_id = str(uuid4())
    async with factory() as session:
        await OutboxProducer(session).enqueue(
            task_type=DOCUMENT_PROCESS_TASK_TYPE,
            schema_version=DOCUMENT_PROCESS_TASK_SCHEMA_VERSION,
            payload={"document_id": doc_id},
            idempotency_key=document_processing_idempotency_key(doc_id),
        )
        await session.commit()

    # job truth lives in SQLite, not Redis
    async with factory() as session:
        task = (await session.scalars(select(OutboxTaskRecord))).first()
        assert task is not None
        assert task.status == OutboxStatus.PENDING.value

    # restart with a fresh worker: durable state reconciles idempotently (no Redis)
    worker = DocumentProcessingWorker(factory)
    await worker.reconcile()
    async with factory() as session:
        tasks = (await session.scalars(select(OutboxTaskRecord))).all()
        assert len(tasks) == 1  # idempotent: no duplicate enqueue across restart
    await engine.dispose()


# ---------------------------------------------------------------------------
# Test 6 — Readiness semantics
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_readiness_db_required_redis_optional(monkeypatch) -> None:
    """Redis unavailable must NOT fail readiness; SQLite healthy → 200."""
    monkeypatch.setattr("app.observability._check_db_ready", AsyncMock(return_value=True))
    monkeypatch.setattr("app.observability._check_redis_ready", AsyncMock(return_value=False))
    resp = await readiness_probe()
    assert resp.status_code == 200
    body = json.loads(resp.body)
    assert body["status"] == "ready"
    assert body["requirements"]["database"] is True
    assert body["requirements"]["redis"] is False


@pytest.mark.asyncio
async def test_readiness_fails_closed_on_db_failure(monkeypatch) -> None:
    """Critical SQLite/migration failure → readiness FAIL (503), not fake 200."""
    monkeypatch.setattr("app.observability._check_db_ready", AsyncMock(return_value=False))
    monkeypatch.setattr("app.observability._check_redis_ready", AsyncMock(return_value=True))
    resp = await readiness_probe()
    assert resp.status_code == 503
    body = json.loads(resp.body)
    assert body["status"] == "degraded"


# ---------------------------------------------------------------------------
# Test 7 — Product default configuration
# ---------------------------------------------------------------------------


def test_product_default_configuration(monkeypatch) -> None:
    """EXEC060-AC-001/AC-003/AC-005: loopback local runtime, SQLite, no external infra."""
    _clean_default_env(monkeypatch)
    s = Settings(_env_file=None)
    assert s.host == "127.0.0.1"  # loopback
    assert s.app_env.value == "local"  # local runtime
    assert s.database_url.startswith("sqlite")  # SQLite production-local
    assert s.redis_url == ""  # no Redis requirement
    assert s.private_app is True

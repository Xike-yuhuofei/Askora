"""EXEC-055 CI v2 Quality Gate: job interruption and idempotency tests."""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base
from app.infrastructure.outbox import (
    OutboxProducer,
    OutboxRepository,
    OutboxStatus,
    utc_now,
)
from app.models.document import ProcessingStatus, UserDocument
from app.models.user import User
from app.services.storage.local_storage import LocalFileStorage


@pytest.mark.asyncio
async def test_interrupted_job_can_resume(tmp_path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'resume.db'}"
    engine = create_async_engine(database_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    now = utc_now()
    async with factory() as session:
        producer = OutboxProducer(session)
        task = await producer.enqueue(
            task_type="test.rebuild",
            schema_version="1.0",
            payload={"material_id": "mat-001", "rebuild_type": "chunks"},
            idempotency_key="resume-test-001",
            next_attempt_at=now,
        )
        assert task.status == OutboxStatus.PENDING
        assert task.attempt_count == 0

        repo = OutboxRepository(session)
        claimed = await repo.claim_next(now=now)
        assert claimed is not None
        assert claimed.status == OutboxStatus.PROCESSING
        task_id = claimed.id
        await session.commit()

    interrupted_engine = create_async_engine(database_url)
    interrupted_factory = async_sessionmaker(interrupted_engine, expire_on_commit=False)
    stale_time = now - timedelta(minutes=10)
    async with interrupted_factory() as session:
        await session.execute(
            text("UPDATE outbox_tasks SET updated_at = :stale_time WHERE id = :task_id"),
            {"stale_time": stale_time, "task_id": task_id},
        )
        await session.commit()

        repo = OutboxRepository(session)
        recovered = await repo.recover_stale(
            stale_before=stale_time + timedelta(seconds=1),
            now=now,
        )
        await session.commit()
        assert recovered == 1

        restored = await repo.get(task_id)
        assert restored is not None
        assert restored.status == OutboxStatus.RETRY
        assert restored.last_error == "OUTBOX_STALE_CLAIM_RECOVERED"
    await interrupted_engine.dispose()

    resume_engine = create_async_engine(database_url)
    resume_factory = async_sessionmaker(resume_engine, expire_on_commit=False)
    async with resume_factory() as session:
        repo = OutboxRepository(session)
        claimed = await repo.claim_next(now=now + timedelta(seconds=1))
        assert claimed is not None
        assert claimed.id == task_id
        assert claimed.status == OutboxStatus.PROCESSING
        assert claimed.attempt_count == 2
    await resume_engine.dispose()


@pytest.mark.asyncio
async def test_duplicate_retry_does_not_duplicate_durable_state(tmp_path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'idempotent.db'}"
    engine = create_async_engine(database_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with factory() as session:
        producer = OutboxProducer(session)
        idem_key = "duplicate-retry-key-001"

        task1 = await producer.enqueue(
            task_type="test.process",
            schema_version="1.0",
            payload={"doc_id": "doc-001"},
            idempotency_key=idem_key,
            next_attempt_at=utc_now(),
        )
        assert task1 is not None
        task1_id = task1.id

        task_count_before = (
            await session.execute(text("SELECT COUNT(*) FROM outbox_tasks"))
        ).scalar()
        assert task_count_before == 1

        task2 = await producer.enqueue(
            task_type="test.process",
            schema_version="1.0",
            payload={"doc_id": "doc-001"},
            idempotency_key=idem_key,
            next_attempt_at=utc_now(),
        )
        assert task2.id == task1_id

        task_count_after = (
            await session.execute(text("SELECT COUNT(*) FROM outbox_tasks"))
        ).scalar()
        assert task_count_after == 1

        fetched = await OutboxRepository(session).get_by_idempotency_key(idem_key)
        assert fetched is not None
        assert fetched.id == task1_id
    await engine.dispose()


@pytest.mark.asyncio
async def test_concurrent_same_material_rebuild_is_deduplicated(tmp_path, monkeypatch) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'dedup.db'}"
    engine = create_async_engine(database_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    storage = LocalFileStorage(str(tmp_path / "dedup_storage"))
    monkeypatch.setattr(
        "app.services.documents.document_service.get_local_storage",
        lambda: storage,
    )

    async with factory() as session:
        user = User(id=str(uuid4()), pseudonym_id="dedup-owner")
        session.add(user)
        await session.commit()

        doc = UserDocument(
            id=str(uuid4()),
            pseudonym_id="dedup-owner",
            original_filename="dedup_source.md",
            file_extension="md",
            file_size_bytes=256,
            storage_path="dedup-owner/dedup_source.md",
            processing_status=ProcessingStatus.COMPLETED,
        )
        session.add(doc)
        await session.commit()

        material_id = doc.id
        idem_key = f"rebuild:{material_id}:chunks"

        producer = OutboxProducer(session)
        task_a = await producer.enqueue(
            task_type="sys01.rebuild_chunks",
            schema_version="1.0",
            payload={"material_id": material_id, "rebuild_type": "chunks"},
            idempotency_key=idem_key,
            next_attempt_at=utc_now(),
        )
        task_a_id = task_a.id

        task_b = await producer.enqueue(
            task_type="sys01.rebuild_chunks",
            schema_version="1.0",
            payload={"material_id": material_id, "rebuild_type": "chunks"},
            idempotency_key=idem_key,
            next_attempt_at=utc_now(),
        )
        task_b_id = task_b.id

        assert task_a_id == task_b_id

        task_count = (
            await session.execute(
                text("SELECT COUNT(*) FROM outbox_tasks WHERE idempotency_key = :key"),
                {"key": idem_key},
            )
        ).scalar()
        assert task_count == 1

        all_tasks_for_material = (
            await session.execute(text("SELECT id, idempotency_key, status FROM outbox_tasks"))
        ).fetchall()
        assert len(all_tasks_for_material) == 1
        assert all_tasks_for_material[0][2] == OutboxStatus.PENDING.value

    await engine.dispose()

    second_engine = create_async_engine(database_url)
    second_factory = async_sessionmaker(second_engine, expire_on_commit=False)
    async with second_factory() as session:
        repo = OutboxRepository(session)
        fetched = await repo.get_by_idempotency_key(idem_key)
        assert fetched is not None
        assert fetched.id == task_a_id

        claimed = await repo.claim_next(now=utc_now())
        assert claimed is not None
        assert claimed.id == task_a_id

        claimed_again = await repo.claim_next(now=utc_now())
        assert claimed_again is None
    await second_engine.dispose()

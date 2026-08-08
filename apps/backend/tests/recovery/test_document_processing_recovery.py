"""Durable document-processing restart and idempotency tests for UI-02A."""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base
from app.domains.content_knowledge import CONTENT_RECORD_KEY, EXTRACTION_VERSION
from app.infrastructure.outbox import OutboxStatus, utc_now
from app.models.document import ProcessingStatus, UserDocument
from app.models.ledger import OutboxTaskRecord
from app.models.user import User
from app.services.documents.document_service import DocumentService
from app.services.documents.processing_worker import DocumentProcessingWorker
from app.services.storage.local_storage import LocalFileStorage


@pytest.mark.asyncio
async def test_ui02a_processing_task_recovers_after_restart_and_is_idempotent(
    tmp_path, monkeypatch
) -> None:
    """UI02A-VSLICE-AC-002: stale durable work survives restart without duplicate revision."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'document-recovery.db'}")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    storage = LocalFileStorage(str(tmp_path / "documents"))
    monkeypatch.setattr(
        "app.services.documents.document_service.get_local_storage",
        lambda: storage,
    )
    async with factory() as session:
        user = User(id=str(uuid4()), pseudonym_id="document-recovery")
        session.add(user)
        await session.commit()
        service = DocumentService(session)
        document = await service.upload_document(
            user.pseudonym_id,
            "recovery.md",
            b"# Durable processing\n\nThe source remains available after restart.",
        )
        task = await session.scalar(select(OutboxTaskRecord))
        assert task is not None
        assert task.status == OutboxStatus.PENDING.value
        task.status = OutboxStatus.PROCESSING.value
        task.updated_at = utc_now() - timedelta(minutes=10)
        await session.commit()

    restarted = DocumentProcessingWorker(factory)
    assert await restarted.reconcile() >= 1
    assert await restarted.run_once() is True
    assert await restarted.run_once() is False

    async with factory() as session:
        stored = await session.get(UserDocument, document.id)
        assert stored is not None
        assert stored.processing_status == ProcessingStatus.COMPLETED
        record = stored.moderation_details[CONTENT_RECORD_KEY]
        assert len(record["revisions"]) == 1
        current = record["revisions"][0]
        assert current["extraction_version"] == EXTRACTION_VERSION
        assert current["knowledge_units"][0]["status"] == "published"
        assert current["knowledge_publication_result"]["published_knowledge_unit_refs"]
        task = await session.scalar(select(OutboxTaskRecord))
        assert task is not None
        assert task.status == OutboxStatus.COMPLETED.value
    await engine.dispose()


@pytest.mark.asyncio
async def test_ui02a_document_worker_bounds_transient_retries(tmp_path, monkeypatch) -> None:
    """UI02A-VSLICE-AC-002: document work dead-letters after its fixed retry budget."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'document-retry.db'}")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    storage = LocalFileStorage(str(tmp_path / "retry-documents"))
    monkeypatch.setattr(
        "app.services.documents.document_service.get_local_storage",
        lambda: storage,
    )
    async with factory() as session:
        user = User(id=str(uuid4()), pseudonym_id="document-retry")
        session.add(user)
        await session.commit()
        await DocumentService(session).upload_document(
            user.pseudonym_id,
            "retry.md",
            b"# Retry boundary\n\nThe outbox owns bounded retries.",
        )

    async def fail_transiently(_service, _document_id):
        raise OSError("temporary storage outage")

    monkeypatch.setattr(DocumentService, "process_document", fail_transiently)
    worker = DocumentProcessingWorker(factory, max_attempts=2, base_retry_seconds=0)
    current = utc_now()
    assert await worker.run_once(now=current) is True
    assert await worker.run_once(now=current) is True

    async with factory() as session:
        task = await session.scalar(select(OutboxTaskRecord))
        assert task is not None
        assert task.status == OutboxStatus.DEAD_LETTER.value
        assert task.attempt_count == 2
        assert task.last_error is not None
        assert "OUTBOX_TRANSIENT_ERROR:OSError" in task.last_error
    await engine.dispose()

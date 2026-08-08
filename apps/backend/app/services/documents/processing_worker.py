"""Durable SYS01 document processing runtime backed by the shared outbox ledger."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.logging import get_logger
from app.domains.content_knowledge import CONTENT_RECORD_KEY, EXTRACTION_VERSION
from app.infrastructure.outbox import (
    OutboxProducer,
    OutboxRepository,
    OutboxTask,
    PermanentTaskError,
    utc_now,
)
from app.models.document import ProcessingStatus, UserDocument
from app.services.documents.document_service import (
    DOCUMENT_PROCESS_TASK_SCHEMA_VERSION,
    DOCUMENT_PROCESS_TASK_TYPE,
    DocumentService,
    document_processing_idempotency_key,
)

logger = get_logger(__name__)


class DocumentProcessingWorker:
    """Claim only document tasks, preserving other outbox consumers' ownership."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        max_attempts: int = 5,
        base_retry_seconds: int = 5,
    ) -> None:
        self._session_factory = session_factory
        self._max_attempts = max_attempts
        self._base_retry_seconds = base_retry_seconds

    async def reconcile(self) -> int:
        """Recover stale claims and enqueue missing/current-extraction work idempotently."""
        current = utc_now()
        async with self._session_factory() as session:
            async with session.begin():
                repository = OutboxRepository(session)
                recovered = await repository.recover_stale(
                    stale_before=current - timedelta(minutes=5),
                    now=current,
                )
                documents = (
                    await session.scalars(
                        select(UserDocument).where(UserDocument.is_deleted.is_(False))
                    )
                ).all()
                enqueued = 0
                for document in documents:
                    if not self._needs_processing(document):
                        continue
                    task = await OutboxProducer(session).enqueue(
                        task_type=DOCUMENT_PROCESS_TASK_TYPE,
                        schema_version=DOCUMENT_PROCESS_TASK_SCHEMA_VERSION,
                        payload={"document_id": document.id},
                        idempotency_key=document_processing_idempotency_key(document.id),
                    )
                    if task.attempt_count == 0:
                        enqueued += 1
                return recovered + enqueued

    async def run_once(self, *, now=None) -> bool:
        current = now or utc_now()
        async with self._session_factory() as session:
            async with session.begin():
                task = await OutboxRepository(session).claim_next(
                    task_types={DOCUMENT_PROCESS_TASK_TYPE},
                    now=current,
                )
        if task is None:
            return False

        failure: str | None = None
        permanent = False
        try:
            await self._handle(task)
        except PermanentTaskError as exc:
            failure = f"OUTBOX_PERMANENT_ERROR:{exc}"
            permanent = True
        except Exception as exc:  # noqa: BLE001 - durable worker classifies retry boundary
            failure = f"OUTBOX_TRANSIENT_ERROR:{type(exc).__name__}:{exc}"

        async with self._session_factory() as session:
            async with session.begin():
                repository = OutboxRepository(session)
                if failure is None:
                    await repository.mark_completed(task.id, now=current)
                else:
                    exhausted = task.attempt_count >= self._max_attempts
                    delay = self._base_retry_seconds * (2 ** max(task.attempt_count - 1, 0))
                    await repository.mark_failed(
                        task.id,
                        error=failure,
                        dead_letter=permanent or exhausted,
                        next_attempt_at=current + timedelta(seconds=delay),
                        now=current,
                    )
        return True

    async def _handle(self, task: OutboxTask) -> None:
        if task.schema_version != DOCUMENT_PROCESS_TASK_SCHEMA_VERSION:
            raise PermanentTaskError("DOCUMENT_PROCESS_SCHEMA_UNSUPPORTED")
        document_id = task.payload.get("document_id")
        if not isinstance(document_id, str) or not document_id:
            raise PermanentTaskError("DOCUMENT_PROCESS_ID_INVALID")
        try:
            async with self._session_factory() as session:
                await DocumentService(session).process_document(document_id)
        except ValueError as exc:
            raise PermanentTaskError(str(exc)) from exc

    @staticmethod
    def _needs_processing(document: UserDocument) -> bool:
        if document.processing_status in {ProcessingStatus.PENDING, ProcessingStatus.PROCESSING}:
            return True
        if document.processing_status != ProcessingStatus.COMPLETED:
            return False
        record: dict[str, Any] = (document.moderation_details or {}).get(CONTENT_RECORD_KEY, {})
        current_id = record.get("current_revision_id")
        revision = next(
            (item for item in record.get("revisions", []) if item.get("revision_id") == current_id),
            None,
        )
        return revision is None or revision.get("extraction_version") != EXTRACTION_VERSION


class DocumentProcessingRuntime:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.worker = DocumentProcessingWorker(session_factory)
        self._stop = asyncio.Event()
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> int:
        reconciled = await self.worker.reconcile()
        self._task = asyncio.create_task(self._run(), name="document-processing-worker")
        return reconciled

    async def stop(self, *, timeout_seconds: float = 15.0) -> None:
        self._stop.set()
        if self._task is None:
            return
        try:
            await asyncio.wait_for(self._task, timeout=timeout_seconds)
        except TimeoutError:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)

    async def _run(self) -> None:
        while not self._stop.is_set():
            try:
                worked = await self.worker.run_once()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 - runtime must survive transient DB outages
                logger.error(
                    "document_processing_worker_iteration_failed",
                    error_type=type(exc).__name__,
                )
                worked = False
            if worked:
                continue
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=0.5)
            except TimeoutError:
                continue


_runtime: DocumentProcessingRuntime | None = None


async def start_document_processing_runtime(
    session_factory: async_sessionmaker[AsyncSession],
) -> int:
    global _runtime
    if _runtime is not None:
        return 0
    runtime = DocumentProcessingRuntime(session_factory)
    try:
        reconciled = await runtime.start()
    except Exception:
        await runtime.stop()
        raise
    _runtime = runtime
    return reconciled


async def stop_document_processing_runtime() -> None:
    global _runtime
    if _runtime is None:
        return
    runtime = _runtime
    _runtime = None
    await runtime.stop()

"""P1-04C OCR candidate/review/publication integration coverage."""

from __future__ import annotations

import io
from uuid import uuid4

import pytest
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base
from app.core.exceptions import ResourceNotFoundError
from app.infrastructure.outbox import OutboxStatus
from app.models.document import UserDocument
from app.models.ledger import OutboxTaskRecord
from app.models.user import User
from app.queries.library import WorkspaceLibraryQueryService
from app.services.documents.document_service import DocumentService
from app.services.documents.ocr import (
    OcrService,
    RecognitionResult,
    RecognizedBlock,
)
from app.services.documents.processing_worker import DocumentProcessingWorker
from app.services.storage.local_storage import LocalFileStorage


class FakeOcrAdapter:
    def version(self) -> str:
        return "tesseract 5.test"

    def languages(self) -> set[str]:
        return {"chi_sim", "eng"}

    def recognize(self, _raw: bytes, _languages: tuple[str, ...]) -> RecognitionResult:
        return RecognitionResult(
            page_count=1,
            blocks=(
                RecognizedBlock(
                    page_number=1,
                    block_index=0,
                    bbox=(12.0, 24.0, 620.0, 96.0),
                    text="扫描原文中的热传导定律",
                    confidence=87.5,
                    image_hash="a" * 64,
                ),
            ),
            reason_codes=(),
        )


def _scanned_pdf() -> bytes:
    stream = io.BytesIO()
    Image.new("RGB", (800, 300), "white").save(stream, format="PDF", resolution=150)
    return stream.getvalue()


@pytest.mark.asyncio
async def test_ocr_survives_worker_restart_requires_review_and_publishes_traceable_revision(
    tmp_path, monkeypatch
) -> None:
    """LIB-AC-006..008: durable candidate gate, provenance, owner isolation and search."""
    database_path = tmp_path / "ocr.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{database_path}")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    storage = LocalFileStorage(str(tmp_path / "documents"))
    owner_id = str(uuid4())
    other_id = str(uuid4())
    async with factory() as session:
        owner = User(id=owner_id, pseudonym_id="ocr-owner")
        other = User(id=other_id, pseudonym_id="ocr-other")
        session.add_all([owner, other])
        await session.commit()
        documents = DocumentService(session)
        documents.storage = storage
        document = await documents.upload_document(owner.pseudonym_id, "scan.pdf", _scanned_pdf())
        await documents.process_document(document.id)
        old_revision_id = document.moderation_details["content_knowledge_v1"]["current_revision_id"]
        process_task = await session.scalar(
            select(OutboxTaskRecord).where(OutboxTaskRecord.type == "sys01.process_document")
        )
        assert process_task is not None
        process_task.status = OutboxStatus.COMPLETED.value
        await session.commit()

        requested = await OcrService(
            session, adapter=FakeOcrAdapter(), storage=storage
        ).request_run(
            document_id=document.id,
            pseudonym_id=owner.pseudonym_id,
            idempotency_key="ocr-request-001",
            languages=("chi_sim", "eng"),
        )
        assert requested.status == "pending"
        assert requested.candidates == ()

    await engine.dispose()

    restarted = create_async_engine(f"sqlite+aiosqlite:///{database_path}")
    restarted_factory = async_sessionmaker(restarted, expire_on_commit=False)
    import app.services.documents.processing_worker as worker_module

    monkeypatch.setattr(
        worker_module,
        "OcrService",
        lambda session: OcrService(session, adapter=FakeOcrAdapter(), storage=storage),
    )
    worker = DocumentProcessingWorker(restarted_factory)
    assert await worker.run_once()

    async with restarted_factory() as session:
        owner = await session.get(User, owner_id)
        other = await session.get(User, other_id)
        document = await session.get(UserDocument, document.id)
        assert owner is not None and other is not None and document is not None
        ocr = OcrService(session, adapter=FakeOcrAdapter(), storage=storage)
        ready = await ocr.get_run(run_id=str(requested.run_id), pseudonym_id=owner.pseudonym_id)
        assert ready.status == "review_required"
        assert ready.candidate_count == 1
        candidate = ready.candidates[0]
        assert candidate.bbox == (12.0, 24.0, 620.0, 96.0)
        assert candidate.image_hash == "a" * 64
        with pytest.raises(ResourceNotFoundError):
            await ocr.get_run(run_id=str(requested.run_id), pseudonym_id=other.pseudonym_id)
        page_image = await ocr.render_page(
            run_id=str(requested.run_id),
            pseudonym_id=owner.pseudonym_id,
            page_number=1,
        )
        assert page_image.startswith(b"\x89PNG\r\n\x1a\n")

        before_review = await WorkspaceLibraryQueryService(session).list_library(
            owner,
            status=None,
            subject=None,
            query_text="热传导定律",
            page=1,
            page_size=20,
            correlation_id="before-review",
        )
        assert before_review.data.total == 0

        accepted = await ocr.review_run(
            run_id=str(requested.run_id),
            pseudonym_id=owner.pseudonym_id,
            idempotency_key="ocr-review-001",
            decisions=(
                {
                    "candidate_id": str(candidate.candidate_id),
                    "expected_version": candidate.version,
                    "action": "ACCEPT",
                    "corrected_text": "复核后的热传导定律",
                },
            ),
            publish=True,
        )
        replay = await ocr.review_run(
            run_id=str(requested.run_id),
            pseudonym_id=owner.pseudonym_id,
            idempotency_key="ocr-review-001",
            decisions=(
                {
                    "candidate_id": str(candidate.candidate_id),
                    "expected_version": candidate.version,
                    "action": "ACCEPT",
                    "corrected_text": "复核后的热传导定律",
                },
            ),
            publish=True,
        )
        assert replay == accepted
        assert accepted.status == "accepted"
        current = document.moderation_details["content_knowledge_v1"]
        assert current["current_revision_id"] != old_revision_id
        revision = next(
            item
            for item in current["revisions"]
            if item["revision_id"] == current["current_revision_id"]
        )
        provenance = revision["ocr_provenance"]
        assert provenance["run_id"] == str(requested.run_id)
        locator = next(iter(provenance["source_span_locators"].values()))
        assert locator["page"] == 1
        assert locator["bbox"] == [12.0, 24.0, 620.0, 96.0]

        after_review = await WorkspaceLibraryQueryService(session).list_library(
            owner,
            status=None,
            subject=None,
            query_text="复核后的热传导定律",
            page=1,
            page_size=20,
            correlation_id="after-review",
        )
        assert after_review.data.total == 1
        assert after_review.data.documents[0].match_source_span_ref is not None
        assert len(current["revisions"]) == 2
        assert storage.get_file_size(document.storage_path) == document.file_size_bytes
    await restarted.dispose()

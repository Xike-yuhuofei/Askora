"""Bounded local OCR candidate/review pipeline owned by SYS01."""

from __future__ import annotations

import asyncio
import csv
import hashlib
import io
import re
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal, cast
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.library_management import OcrCandidateViewV1, OcrRunViewV1
from app.core.exceptions import (
    LibraryIdempotencyConflictError,
    OcrEngineUnavailableError,
    OcrNotApplicableError,
    OcrOutputInvalidError,
    OcrReviewVersionConflictError,
    OcrRunNotReadyError,
    OcrTimeoutError,
    ResourceNotFoundError,
)
from app.domains.content_knowledge import (
    CONTENT_RECORD_KEY,
    RAW_ASSET_CHECKSUM_KEY,
    build_content_revision,
    build_multi_granularity_projections,
)
from app.infrastructure.outbox import OutboxProducer
from app.models.document import DocumentOcrCandidate, DocumentOcrRun, UserDocument
from app.services.documents.document_service import DocumentService
from app.services.documents.library_management import LibraryManagementService
from app.services.storage.local_storage import LocalFileStorage, get_local_storage

OCR_TASK_TYPE = "sys01.ocr_document"
OCR_TASK_SCHEMA_VERSION = "1.0"
OCR_POLICY_VERSION = "local-tesseract-review-v1"
OCR_MAX_PAGES = 100
OCR_RENDER_DPI = 200
OCR_PAGE_TIMEOUT_SECONDS = 30
OCR_MAX_OUTPUT_BYTES = 10 * 1024 * 1024
_LANGUAGE_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


@dataclass(frozen=True)
class RecognizedBlock:
    page_number: int
    block_index: int
    bbox: tuple[float, float, float, float]
    text: str
    confidence: float | None
    image_hash: str


@dataclass(frozen=True)
class RecognitionResult:
    page_count: int
    blocks: tuple[RecognizedBlock, ...]
    reason_codes: tuple[str, ...]


class TesseractLocalAdapter:
    """No-shell/no-network adapter with explicit page, time and output bounds."""

    def __init__(self, binary: str | None = None) -> None:
        self.binary = binary or shutil.which("tesseract")

    def version(self) -> str:
        if not self.binary:
            raise OcrEngineUnavailableError()
        try:
            result = subprocess.run(  # noqa: S603 - resolved local binary, fixed argv, no shell
                [self.binary, "--version"],
                capture_output=True,
                check=True,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise OcrEngineUnavailableError() from exc
        return result.stdout.decode("utf-8", errors="replace").splitlines()[0][:100]

    def languages(self) -> set[str]:
        if not self.binary:
            raise OcrEngineUnavailableError()
        try:
            result = subprocess.run(  # noqa: S603 - resolved local binary, fixed argv, no shell
                [self.binary, "--list-langs"],
                capture_output=True,
                check=True,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise OcrEngineUnavailableError() from exc
        return set(result.stdout.decode("utf-8", errors="replace").splitlines()[1:])

    def recognize(self, file_content: bytes, languages: tuple[str, ...]) -> RecognitionResult:
        try:
            import pdfplumber
        except ImportError as exc:  # pragma: no cover - pinned production dependency
            raise OcrEngineUnavailableError() from exc
        if not self.binary:
            raise OcrEngineUnavailableError()
        blocks: list[RecognizedBlock] = []
        reasons: list[str] = []
        page_count = 0
        try:
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                page_count = len(pdf.pages)
                if not 1 <= page_count <= OCR_MAX_PAGES:
                    raise OcrNotApplicableError()
                for page_number, page in enumerate(pdf.pages, start=1):
                    digital_text = " ".join((page.extract_text() or "").split())
                    if len(digital_text) >= 40:
                        reasons.append(f"OCR_PAGE_{page_number}_DIGITAL_TEXT_SKIPPED")
                        continue
                    image = page.to_image(resolution=OCR_RENDER_DPI).original
                    stream = io.BytesIO()
                    image.save(stream, format="PNG")
                    png = stream.getvalue()
                    image_hash = hashlib.sha256(png).hexdigest()
                    try:
                        result = subprocess.run(  # noqa: S603 - fixed argv, no shell/network
                            [
                                self.binary,
                                "stdin",
                                "stdout",
                                "-l",
                                "+".join(languages),
                                "tsv",
                            ],
                            input=png,
                            capture_output=True,
                            check=True,
                            timeout=OCR_PAGE_TIMEOUT_SECONDS,
                        )
                    except subprocess.TimeoutExpired as exc:
                        raise OcrTimeoutError() from exc
                    except (OSError, subprocess.CalledProcessError) as exc:
                        raise OcrOutputInvalidError() from exc
                    if len(result.stdout) > OCR_MAX_OUTPUT_BYTES:
                        raise OcrOutputInvalidError()
                    blocks.extend(
                        self._parse_tsv(
                            result.stdout.decode("utf-8", errors="replace"),
                            page_number=page_number,
                            image_hash=image_hash,
                        )
                    )
        except OcrNotApplicableError:
            raise
        except Exception as exc:
            if isinstance(exc, (OcrTimeoutError, OcrOutputInvalidError)):
                raise
            raise OcrOutputInvalidError() from exc
        return RecognitionResult(
            page_count=page_count,
            blocks=tuple(blocks),
            reason_codes=tuple(reasons),
        )

    @staticmethod
    def _parse_tsv(
        content: str, *, page_number: int, image_hash: str
    ) -> list[RecognizedBlock]:
        grouped: dict[tuple[str, str, str], list[dict[str, str]]] = {}
        for row in csv.DictReader(io.StringIO(content), delimiter="\t"):
            text = (row.get("text") or "").strip()
            if row.get("level") != "5" or not text:
                continue
            key = (row.get("block_num", "0"), row.get("par_num", "0"), row.get("line_num", "0"))
            grouped.setdefault(key, []).append(row)
        output: list[RecognizedBlock] = []
        for block_index, rows in enumerate(grouped.values()):
            text = " ".join((row.get("text") or "").strip() for row in rows).strip()
            if not text:
                continue
            left = min(int(row.get("left") or 0) for row in rows)
            top = min(int(row.get("top") or 0) for row in rows)
            right = max(int(row.get("left") or 0) + int(row.get("width") or 0) for row in rows)
            bottom = max(int(row.get("top") or 0) + int(row.get("height") or 0) for row in rows)
            confidences = [
                float(row["conf"])
                for row in rows
                if row.get("conf") not in {None, "", "-1"}
            ]
            output.append(
                RecognizedBlock(
                    page_number=page_number,
                    block_index=block_index,
                    bbox=(float(left), float(top), float(right), float(bottom)),
                    text=text[:20_000],
                    confidence=(round(sum(confidences) / len(confidences), 3) if confidences else None),
                    image_hash=image_hash,
                )
            )
        return output


class OcrService:
    def __init__(
        self,
        db: AsyncSession,
        *,
        adapter: TesseractLocalAdapter | None = None,
        storage: LocalFileStorage | None = None,
    ) -> None:
        self.db = db
        self.adapter = adapter or TesseractLocalAdapter()
        self.storage = storage or get_local_storage()

    async def request_run(
        self,
        *,
        document_id: str,
        pseudonym_id: str,
        idempotency_key: str,
        languages: tuple[str, ...],
    ) -> OcrRunViewV1:
        existing = await self.db.scalar(
            select(DocumentOcrRun).where(
                DocumentOcrRun.pseudonym_id == pseudonym_id,
                DocumentOcrRun.idempotency_key == idempotency_key,
            )
        )
        if existing is not None:
            if existing.document_id != document_id or tuple(existing.languages) != languages:
                raise LibraryIdempotencyConflictError()
            return await self._view(existing)
        document = await self._owned_pdf(document_id, pseudonym_id)
        if any(not _LANGUAGE_PATTERN.fullmatch(item) for item in languages):
            raise OcrNotApplicableError()
        engine_version = await asyncio.to_thread(self.adapter.version)
        available = await asyncio.to_thread(self.adapter.languages)
        if not set(languages).issubset(available):
            raise OcrEngineUnavailableError()
        details = document.moderation_details or {}
        checksum = document.raw_asset_checksum or details.get(RAW_ASSET_CHECKSUM_KEY)
        if not checksum:
            raise OcrNotApplicableError()
        current = self._current_revision(document)
        run = DocumentOcrRun(
            id=str(uuid.uuid4()),
            document_id=document.id,
            pseudonym_id=pseudonym_id,
            input_revision_id=current.get("revision_id") if current else None,
            raw_checksum=checksum,
            engine="tesseract-local",
            engine_version=engine_version,
            languages=list(languages),
            policy_version=OCR_POLICY_VERSION,
            status="pending",
            page_count=0,
            candidate_count=0,
            reason_codes=["OCR_REVIEW_REQUIRED"],
            idempotency_key=idempotency_key,
        )
        self.db.add(run)
        await self.db.flush()
        await OutboxProducer(self.db).enqueue(
            task_type=OCR_TASK_TYPE,
            schema_version=OCR_TASK_SCHEMA_VERSION,
            payload={"run_id": run.id, "pseudonym_id": pseudonym_id},
            idempotency_key=f"ocr-run:{run.id}:{OCR_POLICY_VERSION}",
        )
        await self.db.commit()
        return await self._view(run)

    async def process_run(self, run_id: str) -> OcrRunViewV1:
        run = await self.db.get(DocumentOcrRun, run_id)
        if run is None:
            raise ResourceNotFoundError("文字识别任务")
        if run.status in {"review_required", "accepted", "rejected"}:
            return await self._view(run)
        document = await self._owned_pdf(run.document_id, run.pseudonym_id)
        raw = await asyncio.to_thread(self.storage.read_file, document.storage_path)
        if hashlib.sha256(raw).hexdigest() != run.raw_checksum:
            raise OcrNotApplicableError()
        run.status = "processing"
        run.error_code = None
        await self.db.commit()
        result = await asyncio.to_thread(self.adapter.recognize, raw, tuple(run.languages))
        if not result.blocks:
            raise OcrOutputInvalidError()
        await self.db.execute(delete(DocumentOcrCandidate).where(DocumentOcrCandidate.run_id == run.id))
        for block in result.blocks:
            self.db.add(
                DocumentOcrCandidate(
                    id=str(uuid.uuid4()),
                    run_id=run.id,
                    page_number=block.page_number,
                    block_index=block.block_index,
                    bbox=list(block.bbox),
                    text=block.text,
                    confidence=block.confidence,
                    image_hash=block.image_hash,
                    status="candidate",
                    version=1,
                )
            )
        run.page_count = result.page_count
        run.candidate_count = len(result.blocks)
        run.reason_codes = ["OCR_REVIEW_REQUIRED", *result.reason_codes]
        run.status = "review_required"
        await self.db.commit()
        return await self._view(run)

    async def get_run(self, *, run_id: str, pseudonym_id: str) -> OcrRunViewV1:
        run = await self.db.scalar(
            select(DocumentOcrRun).where(
                DocumentOcrRun.id == run_id,
                DocumentOcrRun.pseudonym_id == pseudonym_id,
            )
        )
        if run is None:
            raise ResourceNotFoundError("文字识别任务")
        return await self._view(run)

    async def render_page(
        self, *, run_id: str, pseudonym_id: str, page_number: int
    ) -> bytes:
        run = await self.db.scalar(
            select(DocumentOcrRun).where(
                DocumentOcrRun.id == run_id,
                DocumentOcrRun.pseudonym_id == pseudonym_id,
            )
        )
        if run is None:
            raise ResourceNotFoundError("文字识别任务")
        document = await self._owned_pdf(run.document_id, pseudonym_id)
        raw = await asyncio.to_thread(self.storage.read_file, document.storage_path)
        if hashlib.sha256(raw).hexdigest() != run.raw_checksum:
            raise OcrNotApplicableError()

        def render() -> bytes:
            try:
                import pdfplumber

                with pdfplumber.open(io.BytesIO(raw)) as pdf:
                    if not 1 <= page_number <= min(len(pdf.pages), OCR_MAX_PAGES):
                        raise OcrNotApplicableError()
                    image = pdf.pages[page_number - 1].to_image(
                        resolution=OCR_RENDER_DPI
                    ).original
                    stream = io.BytesIO()
                    image.save(stream, format="PNG")
                    return stream.getvalue()
            except OcrNotApplicableError:
                raise
            except Exception as exc:
                raise OcrOutputInvalidError() from exc

        return await asyncio.to_thread(render)

    async def review_run(
        self,
        *,
        run_id: str,
        pseudonym_id: str,
        idempotency_key: str,
        decisions: tuple[dict[str, Any], ...],
        publish: bool,
    ) -> OcrRunViewV1:
        management = LibraryManagementService(self.db)
        payload = {
            "run_id": run_id,
            "decisions": decisions,
            "publish": publish,
        }
        replay = await management._receipt_result(
            pseudonym_id, "review_ocr_run", idempotency_key, payload
        )
        if replay is not None:
            return OcrRunViewV1.model_validate(replay)
        run = await self.db.scalar(
            select(DocumentOcrRun).where(
                DocumentOcrRun.id == run_id,
                DocumentOcrRun.pseudonym_id == pseudonym_id,
            )
        )
        if run is None:
            raise ResourceNotFoundError("文字识别任务")
        if run.status != "review_required":
            raise OcrRunNotReadyError()
        candidates = (
            await self.db.scalars(
                select(DocumentOcrCandidate)
                .where(DocumentOcrCandidate.run_id == run.id)
                .order_by(DocumentOcrCandidate.page_number, DocumentOcrCandidate.block_index)
            )
        ).all()
        by_id = {item.id: item for item in candidates}
        if publish and set(by_id) != {item["candidate_id"] for item in decisions}:
            raise OcrRunNotReadyError()
        for decision in decisions:
            candidate = by_id.get(decision["candidate_id"])
            if candidate is None or candidate.version != decision["expected_version"]:
                raise OcrReviewVersionConflictError()
            candidate.status = "accepted" if decision["action"] == "ACCEPT" else "rejected"
            candidate.corrected_text = (
                " ".join((decision.get("corrected_text") or "").split()).strip() or None
            )
            candidate.version += 1
        await self.db.flush()
        if publish:
            accepted = [item for item in candidates if item.status == "accepted"]
            if not accepted:
                raise OcrRunNotReadyError()
            await self._publish(run, accepted)
            run.status = "accepted"
            run.reason_codes = ["OCR_REVIEW_ACCEPTED", "OCR_REVISION_PUBLISHED"]
        elif all(item.status == "rejected" for item in candidates):
            run.status = "rejected"
            run.reason_codes = ["OCR_REVIEW_REJECTED"]
        result = await self._view(run)
        await management._store_receipt(
            pseudonym_id,
            "review_ocr_run",
            idempotency_key,
            payload,
            result.model_dump(mode="json"),
        )
        await self.db.commit()
        return result

    async def record_failure(self, run_id: str, error_code: str) -> None:
        run = await self.db.get(DocumentOcrRun, run_id)
        if run is None or run.status in {"accepted", "rejected"}:
            return
        run.status = "failed"
        run.error_code = error_code[:100]
        run.reason_codes = [error_code[:100], "OCR_OLD_REVISION_RETAINED"]
        await self.db.flush()

    async def _publish(
        self, run: DocumentOcrRun, accepted: list[DocumentOcrCandidate]
    ) -> None:
        document = await self._owned_pdf(run.document_id, run.pseudonym_id)
        raw = await asyncio.to_thread(self.storage.read_file, document.storage_path)
        if hashlib.sha256(raw).hexdigest() != run.raw_checksum:
            raise OcrNotApplicableError()
        chunks = [
            f"[Page {item.page_number}]\n{item.corrected_text or item.text}" for item in accepted
        ]
        full_text = "\n\n".join(chunks)
        text_hash = hashlib.sha256(full_text.encode("utf-8")).hexdigest()
        details = dict(document.moderation_details or {})
        previous = details.get(CONTENT_RECORD_KEY, {})
        content_record = await asyncio.to_thread(
            build_content_revision,
            document_id=UUID(document.id),
            original_filename=document.original_filename,
            file_content=raw,
            full_text=full_text,
            chunks=chunks,
            previous_record=previous,
            knowledge_point_id=document.knowledge_point_id,
            parser_version=f"pdf-ocr-tesseract-v1:{text_hash[:12]}",
            document_format="pdf",
        )
        revision = DocumentService._current_revision(content_record)
        if revision is None:
            raise OcrOutputInvalidError()
        statuses = {str(item["span_id"]): "RECOVERED" for item in revision["source_spans"]}
        published = await asyncio.to_thread(
            DocumentService._publish_revision_knowledge,
            revision,
            statuses,
        )
        publication_result = published["knowledge_publication_result"]
        published.update(
            await asyncio.to_thread(
                build_multi_granularity_projections,
                revision_id=UUID(published["revision_id"]),
                source_spans=published.get("source_spans", []),
                document_nodes=published.get("document_nodes", []),
                knowledge_units=published.get("knowledge_units", []),
                relations=published.get("relations", []),
                publication_bindings=published.get("knowledge_publication_bindings", {}),
                knowledge_extractor_version=published.get("knowledge_extractor_version"),
                publication_policy_version=published.get("knowledge_publication_policy_version"),
                publication_decision_id=publication_result.get("decision_id"),
            )
        )
        published["ocr_provenance"] = {
            "run_id": run.id,
            "engine": run.engine,
            "engine_version": run.engine_version,
            "policy_version": run.policy_version,
            "raw_checksum": run.raw_checksum,
            "source_span_locators": {
                span["span_id"]: {
                    "page": candidate.page_number,
                    "bbox": candidate.bbox,
                    "image_hash": candidate.image_hash,
                    "text_hash": hashlib.sha256(
                        (candidate.corrected_text or candidate.text).encode("utf-8")
                    ).hexdigest(),
                }
                for span, candidate in zip(published["source_spans"], accepted, strict=True)
            },
        }
        content_record["revisions"] = [
            published if item.get("revision_id") == published["revision_id"] else item
            for item in content_record.get("revisions", [])
        ]
        document.moderation_details = {**details, CONTENT_RECORD_KEY: content_record}
        document.processing_error = None
        document.processing_status = "completed"
        document.processing_completed_at = datetime.now(timezone.utc)
        document_service = DocumentService(self.db)
        document_service.storage = self.storage
        document.chunk_count = await document_service._create_chunks(
            document.id,
            chunks,
            {"format": "pdf", "ocr_run_id": run.id},
            content_record,
        )
        document.total_tokens = sum(DocumentService._estimate_tokens(item) for item in chunks)
        management = LibraryManagementService(self.db)
        projection = await management.rebuild_search_projection(document)
        await management.refresh_duplicate_suggestions(
            document, normalized_body=projection.normalized_body
        )
        await document_service._append_knowledge_publication_audit(document, published)

    async def _owned_pdf(self, document_id: str, pseudonym_id: str) -> UserDocument:
        document = await self.db.scalar(
            select(UserDocument).where(
                UserDocument.id == document_id,
                UserDocument.pseudonym_id == pseudonym_id,
                UserDocument.is_deleted.is_(False),
            )
        )
        if document is None:
            raise ResourceNotFoundError("资料")
        if document.file_extension != "pdf":
            raise OcrNotApplicableError()
        return document

    async def _view(self, run: DocumentOcrRun) -> OcrRunViewV1:
        candidates = (
            await self.db.scalars(
                select(DocumentOcrCandidate)
                .where(DocumentOcrCandidate.run_id == run.id)
                .order_by(DocumentOcrCandidate.page_number, DocumentOcrCandidate.block_index)
            )
        ).all()
        return OcrRunViewV1(
            run_id=UUID(run.id),
            document_id=UUID(run.document_id),
            input_revision_id=UUID(run.input_revision_id) if run.input_revision_id else None,
            engine=run.engine,
            engine_version=run.engine_version,
            languages=tuple(run.languages),
            policy_version=run.policy_version,
            status=cast(
                Literal[
                    "pending",
                    "processing",
                    "review_required",
                    "accepted",
                    "rejected",
                    "failed",
                ],
                run.status,
            ),
            page_count=run.page_count,
            candidate_count=run.candidate_count,
            reason_codes=tuple(run.reason_codes),
            error_code=run.error_code,
            candidates=tuple(
                OcrCandidateViewV1(
                    candidate_id=UUID(item.id),
                    page_number=item.page_number,
                    block_index=item.block_index,
                    bbox=tuple(item.bbox),
                    text=item.text,
                    confidence=item.confidence,
                    image_hash=item.image_hash,
                    status=cast(
                        Literal["candidate", "accepted", "rejected"], item.status
                    ),
                    corrected_text=item.corrected_text,
                    version=item.version,
                )
                for item in candidates
            ),
        )

    @staticmethod
    def _current_revision(document: UserDocument) -> dict[str, Any] | None:
        return DocumentService._current_revision(
            (document.moderation_details or {}).get(CONTENT_RECORD_KEY, {})
        )

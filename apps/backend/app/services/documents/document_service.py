"""
文档服务 - 核心业务逻辑
负责文档上传、处理、查询、删除等操作

核心流程：
1. 用户上传文件 → 保存到本地 → 创建文档记录
2. 异步处理：解析 → 安全扫描 → 分块 → 向量化
3. 对话时：RAG 检索 → 注入上下文
"""

from __future__ import annotations

import asyncio
import copy
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Literal, Optional
from uuid import UUID, uuid5

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.content import SourceReplayResult
from app.core.exceptions import (
    ContentChecksumMismatchError,
    ContentFileMissingError,
    ContentReinspectionChecksumMismatchError,
    ContentReinspectionNotAllowedError,
    ContentReinspectionPolicyUnchangedError,
    ContentReinspectionUnavailableError,
    ResourceNotFoundError,
)
from app.core.logging import get_logger
from app.domains.content_knowledge import (
    CONTENT_RECORD_KEY,
    EXTRACTION_VERSION,
    KNOWLEDGE_EXTRACTOR_VERSION,
    KNOWLEDGE_PUBLICATION_POLICY_VERSION,
    PARSER_VERSION,
    RAW_ASSET_CHECKSUM_KEY,
    SAFETY_REINSPECTION_KEY,
    SAFETY_SCAN_CURRENT_KEY,
    SAFETY_SCAN_RUNS_KEY,
    SAFETY_SCANNER_VERSION,
    SEGMENTATION_VERSION,
    build_content_revision,
    build_multi_granularity_projections,
    build_publication_decision_trace,
    build_publication_events,
    publish_revision_knowledge,
)
from app.domains.content_knowledge.epub_structure import replay_epub_locator
from app.infrastructure.ledger import DecisionTraceRepository, LearningEventRepository
from app.infrastructure.outbox import OutboxProducer, OutboxRepository, OutboxStatus, OutboxTask
from app.models.document import (
    DocumentChunk,
    ModerationStatus,
    ProcessingStatus,
    UserDocument,
)
from app.models.user import User
from app.services.auth.canonical_identity import canonical_user_id
from app.services.documents.parsers import (
    ParsedContent,
    get_parser,
)
from app.services.documents.security_scanner import ScanResult, get_security_scanner
from app.services.storage.local_storage import LocalFileStorage, get_local_storage

logger = get_logger(__name__)

DOCUMENT_PROCESS_TASK_TYPE = "sys01.process_document"
DOCUMENT_PROCESS_TASK_SCHEMA_VERSION = "1.0"
DOCUMENT_REINSPECTION_TASK_TYPE = "sys01.reinspect_document"
DOCUMENT_REINSPECTION_TASK_SCHEMA_VERSION = "1.0"


def document_processing_idempotency_key(document_id: str) -> str:
    return (
        f"document:{document_id}:process:{PARSER_VERSION}:"
        f"{EXTRACTION_VERSION}:{KNOWLEDGE_EXTRACTOR_VERSION}:"
        f"{KNOWLEDGE_PUBLICATION_POLICY_VERSION}:{SAFETY_SCANNER_VERSION}"
    )


def document_reinspection_idempotency_key(document_id: str) -> str:
    return f"document:{document_id}:reinspect:{SAFETY_SCANNER_VERSION}"


def document_post_reinspection_processing_idempotency_key(document_id: str) -> str:
    return f"document:{document_id}:process-after-reinspect:{SAFETY_SCANNER_VERSION}"


class DocumentService:
    """文档服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.storage: LocalFileStorage = get_local_storage()
        self.scanner = get_security_scanner()

    async def upload_document(
        self,
        pseudonym_id: str,
        original_filename: str,
        file_content: bytes,
        subject: Optional[str] = None,
        knowledge_point_id: Optional[str] = None,
    ) -> UserDocument:
        """
        上传文档
        """
        file_ext = self._get_extension(original_filename)

        if not self.storage.is_supported(file_ext):
            raise ValueError(f"不支持的文件格式: .{file_ext}")

        document_id = str(uuid.uuid4())

        storage_path, file_size = await self.storage.save_file(
            pseudonym_id=pseudonym_id,
            document_id=document_id,
            original_filename=original_filename,
            file_content=file_content,
            file_extension=file_ext,
        )

        document = UserDocument(
            id=document_id,
            pseudonym_id=pseudonym_id,
            original_filename=original_filename,
            file_extension=file_ext,
            file_size_bytes=file_size,
            storage_path=storage_path,
            processing_status=ProcessingStatus.PENDING,
            moderation_status=ModerationStatus.PENDING,
            subject=subject,
            knowledge_point_id=knowledge_point_id,
            moderation_details={
                RAW_ASSET_CHECKSUM_KEY: hashlib.sha256(file_content).hexdigest(),
            },
        )

        self.db.add(document)
        await self.db.flush()
        await OutboxProducer(self.db).enqueue(
            task_type=DOCUMENT_PROCESS_TASK_TYPE,
            schema_version=DOCUMENT_PROCESS_TASK_SCHEMA_VERSION,
            payload={"document_id": document_id},
            idempotency_key=document_processing_idempotency_key(document_id),
        )
        await self.db.commit()
        await self.db.refresh(document)

        logger.info(
            "document_uploaded",
            document_id=document_id,
            pseudonym_id=pseudonym_id,
            filename=original_filename,
            size=file_size,
        )

        return document

    async def request_reinspection(
        self,
        *,
        document_id: str,
        pseudonym_id: str,
    ) -> tuple[UserDocument, Literal["accepted", "already_pending"]]:
        """Durably enqueue the explicit owner command without lifting quarantine."""
        document = await self.db.scalar(
            select(UserDocument).where(
                UserDocument.id == document_id,
                UserDocument.pseudonym_id == pseudonym_id,
                UserDocument.is_deleted.is_(False),
            )
        )
        if document is None:
            raise ResourceNotFoundError("文档")
        if document.processing_status != ProcessingStatus.QUARANTINED:
            raise ContentReinspectionNotAllowedError()

        details = dict(document.moderation_details or {})
        control = details.get(SAFETY_REINSPECTION_KEY, {})
        if (
            isinstance(control, dict)
            and control.get("target_scanner_version") == SAFETY_SCANNER_VERSION
            and control.get("status") in {"pending", "processing"}
        ):
            await OutboxProducer(self.db).enqueue(
                task_type=DOCUMENT_REINSPECTION_TASK_TYPE,
                schema_version=DOCUMENT_REINSPECTION_TASK_SCHEMA_VERSION,
                payload={
                    "document_id": document.id,
                    "pseudonym_id": pseudonym_id,
                    "previous_scanner_version": control.get("previous_scanner_version"),
                    "target_scanner_version": SAFETY_SCANNER_VERSION,
                    "expected_checksum": details.get(RAW_ASSET_CHECKSUM_KEY),
                },
                idempotency_key=document_reinspection_idempotency_key(document.id),
            )
            await self.db.commit()
            return document, "already_pending"
        if (
            isinstance(control, dict)
            and control.get("target_scanner_version") == SAFETY_SCANNER_VERSION
            and control.get("status") == "failed"
        ):
            raise ContentReinspectionUnavailableError()

        previous_version = self._last_scanner_version(details) or "legacy-unversioned"
        if previous_version == SAFETY_SCANNER_VERSION:
            raise ContentReinspectionPolicyUnchangedError()

        task = await OutboxProducer(self.db).enqueue(
            task_type=DOCUMENT_REINSPECTION_TASK_TYPE,
            schema_version=DOCUMENT_REINSPECTION_TASK_SCHEMA_VERSION,
            payload={
                "document_id": document.id,
                "pseudonym_id": pseudonym_id,
                "previous_scanner_version": previous_version,
                "target_scanner_version": SAFETY_SCANNER_VERSION,
                "expected_checksum": details.get(RAW_ASSET_CHECKSUM_KEY),
            },
            idempotency_key=document_reinspection_idempotency_key(document.id),
        )
        if task.status in {OutboxStatus.COMPLETED, OutboxStatus.DEAD_LETTER}:
            raise ContentReinspectionUnavailableError()

        details[SAFETY_REINSPECTION_KEY] = {
            "request_id": task.id,
            "status": "pending",
            "previous_scanner_version": previous_version,
            "target_scanner_version": SAFETY_SCANNER_VERSION,
            "requested_at": datetime.now(timezone.utc).isoformat(),
        }
        document.moderation_details = details
        await self.db.commit()
        await self.db.refresh(document)
        return document, "accepted"

    async def retry_failed_document(
        self,
        *,
        document_id: str,
        pseudonym_id: str,
        recovery_idempotency_key: str,
        recovery_of: str | None = None,
    ) -> tuple[UserDocument, OutboxTask]:
        """SYS01 owner command: replace a failed processing task without erasing history."""
        document = await self.db.scalar(
            select(UserDocument).where(
                UserDocument.id == document_id,
                UserDocument.pseudonym_id == pseudonym_id,
                UserDocument.is_deleted.is_(False),
            )
        )
        if document is None:
            raise ResourceNotFoundError("文档")
        replacement_key = f"document:{document.id}:recovery:{recovery_idempotency_key}"
        existing = await OutboxRepository(self.db).get_by_idempotency_key(replacement_key)
        if existing is not None:
            return document, existing
        if document.processing_status != ProcessingStatus.FAILED:
            from app.core.exceptions import RecoveryActionNotAllowedError

            raise RecoveryActionNotAllowedError("DOCUMENT_NOT_FAILED")

        try:
            raw = await asyncio.to_thread(self.storage.read_file, document.storage_path)
        except FileNotFoundError as exc:
            raise ContentFileMissingError() from exc
        expected_checksum = (document.moderation_details or {}).get(RAW_ASSET_CHECKSUM_KEY)
        if expected_checksum and hashlib.sha256(raw).hexdigest() != expected_checksum:
            raise ContentChecksumMismatchError()

        document.processing_status = ProcessingStatus.PENDING
        document.processing_error = None
        document.processing_started_at = None
        document.processing_completed_at = None
        task = await OutboxProducer(self.db).enqueue(
            task_type=DOCUMENT_PROCESS_TASK_TYPE,
            schema_version=DOCUMENT_PROCESS_TASK_SCHEMA_VERSION,
            payload={
                "document_id": document.id,
                "pseudonym_id": pseudonym_id,
                "recovery_of": recovery_of or f"document:{document.id}:failed",
            },
            idempotency_key=replacement_key,
        )
        await self.db.flush()
        return document, task

    async def reinspect_document(
        self,
        *,
        document_id: str,
        pseudonym_id: str,
        previous_scanner_version: str,
        target_scanner_version: str,
        expected_checksum: str | None,
    ) -> UserDocument:
        """Execute an explicit reinspection while quarantine remains fail-closed."""
        document = await self.db.scalar(
            select(UserDocument).where(
                UserDocument.id == document_id,
                UserDocument.pseudonym_id == pseudonym_id,
                UserDocument.is_deleted.is_(False),
            )
        )
        if document is None:
            raise ResourceNotFoundError("文档")
        if target_scanner_version != SAFETY_SCANNER_VERSION:
            raise ContentReinspectionUnavailableError()

        details = dict(document.moderation_details or {})
        control = dict(details.get(SAFETY_REINSPECTION_KEY, {}))
        if (
            control.get("status") == "completed"
            and control.get("previous_scanner_version") == previous_scanner_version
            and control.get("target_scanner_version") == target_scanner_version
        ):
            return document
        if document.processing_status != ProcessingStatus.QUARANTINED:
            raise ContentReinspectionNotAllowedError()
        current_version = self._last_scanner_version(details) or "legacy-unversioned"
        if current_version != previous_scanner_version:
            raise ContentReinspectionPolicyUnchangedError()
        control.update(
            {
                "status": "processing",
                "started_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        details[SAFETY_REINSPECTION_KEY] = control
        document.moderation_details = details
        await self.db.commit()

        file_content = await asyncio.to_thread(self.storage.read_file, document.storage_path)
        checksum = hashlib.sha256(file_content).hexdigest()
        baseline_checksum = expected_checksum or details.get(RAW_ASSET_CHECKSUM_KEY)
        legacy_baseline = baseline_checksum is None
        if baseline_checksum is not None and checksum != baseline_checksum:
            raise ContentReinspectionChecksumMismatchError()
        if legacy_baseline and len(file_content) != document.file_size_bytes:
            raise ContentReinspectionChecksumMismatchError()

        scan_result = self.scanner.scan(
            file_content,
            document.file_extension,
            document.original_filename,
        )
        extra_reasons = (
            ("LEGACY_RAW_ASSET_CHECKSUM_BASELINE_ESTABLISHED",) if legacy_baseline else ()
        )
        updated_details = self._with_scan_record(
            document,
            scan_result,
            checksum,
            extra_reason_codes=extra_reasons,
        )
        control = dict(updated_details.get(SAFETY_REINSPECTION_KEY, {}))
        control.update(
            {
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "outcome": scan_result.verdict,
            }
        )
        updated_details[SAFETY_REINSPECTION_KEY] = control

        if scan_result.should_block:
            document.processing_status = (
                ProcessingStatus.QUARANTINED
                if scan_result.should_quarantine
                else ProcessingStatus.REJECTED
            )
            document.moderation_status = ModerationStatus.REJECTED
            updated_details["reason"] = (
                "security_scan_failed"
                if scan_result.should_quarantine
                else "content_validation_failed"
            )
            updated_details["threats"] = scan_result.threats
            document.moderation_details = updated_details
            document.processing_completed_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(document)
            return document

        document.processing_status = ProcessingStatus.PENDING
        document.processing_error = None
        document.moderation_status = (
            ModerationStatus.REQUIRES_REVIEW
            if scan_result.requires_review
            else ModerationStatus.APPROVED
        )
        document.moderation_details = updated_details
        await OutboxProducer(self.db).enqueue(
            task_type=DOCUMENT_PROCESS_TASK_TYPE,
            schema_version=DOCUMENT_PROCESS_TASK_SCHEMA_VERSION,
            payload={"document_id": document.id},
            idempotency_key=document_post_reinspection_processing_idempotency_key(document.id),
        )
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def record_reinspection_task_failure(
        self,
        *,
        document_id: str,
        target_scanner_version: str,
        failure_code: str,
    ) -> None:
        """Project a terminal task failure without lifting the security boundary."""
        document = await self.db.get(UserDocument, document_id)
        if document is None:
            return
        details = dict(document.moderation_details or {})
        control = dict(details.get(SAFETY_REINSPECTION_KEY, {}))
        if control.get("target_scanner_version") != target_scanner_version:
            return
        control.update(
            {
                "status": "failed",
                "failure_code": failure_code,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        details[SAFETY_REINSPECTION_KEY] = control
        document.moderation_details = details
        document.processing_status = ProcessingStatus.QUARANTINED
        document.moderation_status = ModerationStatus.REJECTED
        await self.db.flush()

    async def process_document(self, document_id: str) -> UserDocument:
        """
        处理文档（解析 + 安全扫描 + 分块）
        """
        result = await self.db.execute(select(UserDocument).where(UserDocument.id == document_id))
        document = result.scalar_one_or_none()

        if document is None:
            raise ValueError(f"文档不存在: {document_id}")
        if document.is_deleted:
            raise ValueError(f"文档已删除: {document_id}")

        try:
            file_content = await asyncio.to_thread(
                self.storage.read_file,
                document.storage_path,
            )
            checksum = hashlib.sha256(file_content).hexdigest()
            existing_details = dict(document.moderation_details or {})
            expected_checksum = existing_details.get(RAW_ASSET_CHECKSUM_KEY)
            if (
                expected_checksum is not None
                and checksum != expected_checksum
                and document.processing_status != ProcessingStatus.COMPLETED
            ):
                raise ValueError("raw asset checksum mismatch")
            canonical = existing_details.get(CONTENT_RECORD_KEY, {})
            current = self._current_revision(canonical)
            parser = get_parser(document.file_extension)
            if (
                document.processing_status == ProcessingStatus.COMPLETED
                and current
                and current.get("checksum") == checksum
                and current.get("parser_version") == parser.semantic_version
                and current.get("extraction_version") == EXTRACTION_VERSION
                and current.get("knowledge_extractor_version") == KNOWLEDGE_EXTRACTOR_VERSION
                and current.get("knowledge_publication_policy_version")
                == KNOWLEDGE_PUBLICATION_POLICY_VERSION
            ):
                chunk_count = await self.db.scalar(
                    select(func.count())
                    .select_from(DocumentChunk)
                    .where(DocumentChunk.document_id == document_id)
                )
                if chunk_count:
                    return document
                await self.rebuild_chunk_projection(document_id)
                await self.db.refresh(document)
                return document

            document.processing_status = ProcessingStatus.PROCESSING
            document.processing_started_at = datetime.now(timezone.utc)
            await self.db.commit()

            # 1. 安全扫描（本地轻量扫描）
            scan_result = self.scanner.scan(
                file_content, document.file_extension, document.original_filename
            )
            scan_details = self._with_scan_record(document, scan_result, checksum)

            if scan_result.should_block:
                document.processing_status = (
                    ProcessingStatus.QUARANTINED
                    if scan_result.should_quarantine
                    else ProcessingStatus.REJECTED
                )
                document.moderation_status = ModerationStatus.REJECTED
                document.moderation_details = {
                    **scan_details,
                    "reason": (
                        "security_scan_failed"
                        if scan_result.should_quarantine
                        else "content_validation_failed"
                    ),
                    "threats": scan_result.threats,
                }
                document.processing_completed_at = datetime.now(timezone.utc)
                await self.db.commit()

                logger.warning(
                    "document_blocked_by_safety_scan",
                    document_id=document_id,
                    verdict=scan_result.verdict,
                    threats=scan_result.threats,
                )
                return document

            # 2. 解析文档
            parsed: ParsedContent = parser.parse(file_content, document.file_extension)
            canonical_chunks = (
                parsed.chunks
                if parsed.document_nodes is not None
                else self._split_visibility_boundaries(parsed.chunks)
            )

            # 3. 建立不可变 revision/SourceSpan，并执行 SYS01 候选验证与发布。
            content_record = build_content_revision(
                document_id=UUID(document.id),
                original_filename=document.original_filename,
                file_content=file_content,
                full_text=parsed.full_text,
                chunks=canonical_chunks,
                previous_record=canonical,
                knowledge_point_id=document.knowledge_point_id,
                parser_version=parser.semantic_version,
                document_format=self._canonical_document_format(document.file_extension),
                document_nodes=parsed.document_nodes,
                root_node_local_id=parsed.root_node_local_id,
            )
            current_revision = self._current_revision(content_record)
            if current_revision is None:
                raise ValueError("canonical content revision missing")
            anchor_statuses = self._current_revision_anchor_statuses(
                current_revision,
                file_content=file_content,
                full_text=parsed.full_text,
                file_extension=document.file_extension,
            )
            published_revision = publish_revision_knowledge(
                current_revision,
                anchor_status_by_span=anchor_statuses,
            )
            publication_result = published_revision["knowledge_publication_result"]
            published_revision.update(
                build_multi_granularity_projections(
                    revision_id=UUID(published_revision["revision_id"]),
                    source_spans=published_revision.get("source_spans", []),
                    document_nodes=published_revision.get("document_nodes", []),
                    knowledge_units=published_revision.get("knowledge_units", []),
                    relations=published_revision.get("relations", []),
                    publication_bindings=published_revision.get(
                        "knowledge_publication_bindings", {}
                    ),
                    knowledge_extractor_version=published_revision.get(
                        "knowledge_extractor_version"
                    ),
                    publication_policy_version=published_revision.get(
                        "knowledge_publication_policy_version"
                    ),
                    publication_decision_id=publication_result.get("decision_id"),
                )
            )
            content_record["revisions"] = [
                (
                    published_revision
                    if item.get("revision_id") == published_revision["revision_id"]
                    else item
                )
                for item in content_record.get("revisions", [])
            ]
            document.moderation_details = {
                **scan_details,
                CONTENT_RECORD_KEY: content_record,
            }
            document.moderation_status = (
                ModerationStatus.REQUIRES_REVIEW
                if scan_result.requires_review
                else ModerationStatus.APPROVED
            )

            # 4. 从 canonical spans 创建可删除、可重建的 SourceChunk projection。
            chunks_created = await self._create_chunks(
                document_id=document_id,
                chunks=canonical_chunks,
                metadata=parsed.metadata,
                content_record=content_record,
            )

            # 5. 更新文档统计
            document.chunk_count = chunks_created
            document.total_tokens = parsed.metadata.get("estimated_tokens", 0)
            document.processing_status = ProcessingStatus.COMPLETED
            document.processing_completed_at = datetime.now(timezone.utc)

            await self._append_knowledge_publication_audit(document, published_revision)

            await self.db.commit()
            await self.db.refresh(document)

            logger.info(
                "document_processed",
                document_id=document_id,
                chunks=chunks_created,
                tokens=document.total_tokens,
            )

            return document

        except Exception as e:
            await self.db.rollback()
            document = await self.db.get(UserDocument, document_id)
            if document is None:
                raise
            document.processing_status = ProcessingStatus.FAILED
            document.processing_error = str(e)
            document.processing_completed_at = datetime.now(timezone.utc)
            await self.db.commit()

            logger.error(
                "document_processing_failed",
                document_id=document_id,
                error=str(e),
            )
            raise

    @staticmethod
    def _current_revision_anchor_statuses(
        revision: dict,
        *,
        file_content: bytes,
        full_text: str,
        file_extension: str,
    ) -> dict[str, str]:
        """Verify current-revision evidence without trusting candidate/model assertions."""
        nodes = {item["node_id"]: item for item in revision.get("document_nodes", [])}
        statuses: dict[str, str] = {}
        for span in revision.get("source_spans", []):
            span_id = span["span_id"]
            node = nodes.get(span.get("node_id"))
            if file_extension == "epub" and node is not None:
                status, _resolved = replay_epub_locator(
                    file_content,
                    locator=node["source_locator"],
                    expected_content_hash=node["content_hash"],
                )
                statuses[span_id] = status
                continue
            start = span.get("start_offset")
            end = span.get("end_offset")
            if (
                isinstance(start, int)
                and isinstance(end, int)
                and full_text[start:end] == span.get("text")
            ):
                statuses[span_id] = "EXACT"
            elif span.get("text") and span["text"] in full_text:
                statuses[span_id] = "RECOVERED"
            else:
                statuses[span_id] = "FAILED"
        return statuses

    async def _append_knowledge_publication_audit(
        self,
        document: UserDocument,
        revision: dict,
    ) -> None:
        """Persist owner decision/events in the same transaction as published truth."""
        user = await self.db.scalar(select(User).where(User.pseudonym_id == document.pseudonym_id))
        if user is None:
            raise ValueError("knowledge publication owner context missing")
        revision_id = UUID(revision["revision_id"])
        correlation_id = uuid5(revision_id, "knowledge-publication-correlation")
        trace = build_publication_decision_trace(
            revision,
            correlation_id=correlation_id,
        )
        await DecisionTraceRepository(self.db).append(trace)
        event_repository = LearningEventRepository(self.db)
        for event in build_publication_events(
            revision,
                user_id=canonical_user_id(user.id),
            correlation_id=correlation_id,
        ):
            await event_repository.append(event)

    async def _create_chunks(
        self,
        document_id: str,
        chunks: list[str],
        metadata: dict,
        content_record: dict,
    ) -> int:
        """Create a replaceable SourceChunk projection from canonical spans."""
        await self.db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
        chunk_objects = []
        revision = self._current_revision(content_record)
        if revision is None:
            raise ValueError("canonical content revision missing")
        revision_id = UUID(revision["revision_id"])
        spans = revision.get("source_spans", [])
        knowledge_unit_ids_by_span: dict[str, list[str]] = {}
        for item in revision.get("knowledge_units", []):
            for span_id in item.get("evidence_span_ids", []):
                knowledge_unit_ids_by_span.setdefault(span_id, []).append(item["knowledge_unit_id"])

        retrieval_chunks = revision.get("retrieval_chunks", [])
        projection_rows = (
            retrieval_chunks
            if retrieval_chunks
            else [
                {
                    "chunk_id": str(uuid5(revision_id, f"{SEGMENTATION_VERSION}:chunk:{idx}")),
                    "text": content,
                    "source_span_ids": [spans[idx]["span_id"]],
                    "knowledge_unit_ids": knowledge_unit_ids_by_span.get(spans[idx]["span_id"], []),
                    "pedagogical_role": self._classify_projection_visibility(content)[0],
                    "answer_exposure": (
                        "COMPLETE"
                        if self._classify_projection_visibility(content)[2] == "grader_only"
                        else "NONE"
                    ),
                    "allowed_use": self._classify_projection_visibility(content)[2],
                    "hierarchy_scope_refs": [],
                    "segmentation_version": SEGMENTATION_VERSION,
                }
                for idx, content in enumerate(chunks)
            ]
        )

        for idx, projection in enumerate(projection_rows):
            content = projection["text"]
            exposure_level = 4 if projection["answer_exposure"] == "COMPLETE" else 0
            chunk = DocumentChunk(
                id=projection["chunk_id"],
                document_id=document_id,
                chunk_index=idx,
                content=content,
                token_count=self._estimate_tokens(content),
                chunk_metadata={
                    **metadata,
                    "chunk_index": idx,
                    "total_chunks": len(projection_rows),
                    "position": round(idx / max(len(projection_rows) - 1, 1), 2),
                    "revision_id": str(revision_id),
                    "segmentation_version": projection["segmentation_version"],
                    "source_span_ids": projection["source_span_ids"],
                    "knowledge_unit_ids": projection["knowledge_unit_ids"],
                    "knowledge_unit_refs": projection.get("knowledge_unit_refs", []),
                    "relation_refs": projection.get("relation_refs", []),
                    "source_span_refs": projection.get("source_span_refs", []),
                    "semantic_unit_ids": projection.get("semantic_unit_ids", []),
                    "pedagogical_role": projection["pedagogical_role"],
                    "answer_exposure": projection["answer_exposure"],
                    "exposure_level": exposure_level,
                    "allowed_use": projection["allowed_use"],
                    "hierarchy_scope_refs": projection["hierarchy_scope_refs"],
                    "hierarchy_refs": projection.get("hierarchy_refs", []),
                    "projection_versions": projection.get("projection_versions", {}),
                    "projection_fingerprint": projection.get("projection_fingerprint"),
                    "canonical_retrieval_eligible": projection.get(
                        "canonical_retrieval_eligible", False
                    ),
                    "eligibility_reason_codes": projection.get("eligibility_reason_codes", []),
                    "compatibility_projection": "legacy-exposure-read-v1",
                },
            )
            chunk_objects.append(chunk)

        self.db.add_all(chunk_objects)
        await self.db.flush()

        return len(chunk_objects)

    async def rebuild_chunk_projection(self, document_id: str) -> int:
        """Rebuild indexes from canonical records without reparsing the source file."""
        document = await self.db.get(UserDocument, document_id)
        if document is None:
            raise ValueError(f"文档不存在: {document_id}")
        content_record = self._rebuild_current_revision_projections(document)
        revision = self._current_revision(content_record)
        if revision is None:
            raise ValueError("canonical content revision missing")
        chunks = [item["text"] for item in revision.get("source_spans", [])]
        count = await self._create_chunks(
            document_id=document_id,
            chunks=chunks,
            metadata={"format": document.file_extension, "rebuilt": True},
            content_record=content_record,
        )
        document.chunk_count = count
        await self.db.commit()
        return count

    async def rebuild_content_projections(self, document_id: str) -> dict:
        """Rebuild all D02 working sets/projections without changing content truth."""
        document = await self.db.get(UserDocument, document_id)
        if document is None:
            raise ValueError(f"文档不存在: {document_id}")
        content_record = self._rebuild_current_revision_projections(document)
        await self.db.commit()
        revision = self._current_revision(content_record)
        if revision is None:
            raise ValueError("canonical content revision missing")
        return revision

    @staticmethod
    def _rebuild_current_revision_projections(document: UserDocument) -> dict:
        """Replace only rebuildable D02 fields in the current immutable revision envelope."""
        details = copy.deepcopy(document.moderation_details or {})
        content_record = details.get(CONTENT_RECORD_KEY, {})
        revision = DocumentService._current_revision(content_record)
        if revision is None:
            raise ValueError("canonical content revision missing")
        rebuilt = build_multi_granularity_projections(
            revision_id=UUID(revision["revision_id"]),
            source_spans=revision.get("source_spans", []),
            document_nodes=revision.get("document_nodes", []),
            knowledge_units=revision.get("knowledge_units", []),
            relations=revision.get("relations", []),
            publication_bindings=revision.get("knowledge_publication_bindings", {}),
            knowledge_extractor_version=revision.get("knowledge_extractor_version"),
            publication_policy_version=revision.get("knowledge_publication_policy_version"),
            publication_decision_id=revision.get("knowledge_publication_result", {}).get(
                "decision_id"
            ),
        )
        revision.update(rebuilt)
        document.moderation_details = details
        return content_record

    async def get_source_span(self, document_id: str, span_id: str) -> dict | None:
        """Replay a citation anchor from canonical content truth (SYS01-AC-001)."""
        document = await self.db.get(UserDocument, document_id)
        if document is None:
            return None
        content_record = (document.moderation_details or {}).get(CONTENT_RECORD_KEY, {})
        for revision in content_record.get("revisions", []):
            for span in revision.get("source_spans", []):
                if span.get("span_id") == span_id:
                    return {
                        **span,
                        "document_id": document_id,
                        "original_filename": document.original_filename,
                    }
        return None

    async def replay_source_span(
        self,
        document_id: str,
        span_id: str,
    ) -> SourceReplayResult | None:
        """Replay SourceSpan -> DocumentNode -> original EPUB locator (D01-050/051)."""
        document = await self.db.get(UserDocument, document_id)
        if document is None:
            return None
        content_record = (document.moderation_details or {}).get(CONTENT_RECORD_KEY, {})
        for revision in content_record.get("revisions", []):
            span = next(
                (
                    item
                    for item in revision.get("source_spans", [])
                    if item.get("span_id") == span_id
                ),
                None,
            )
            if span is None:
                continue
            node_id = span.get("node_id")
            node = next(
                (
                    item
                    for item in revision.get("document_nodes", [])
                    if item.get("node_id") == node_id
                ),
                None,
            )
            if node is None or document.file_extension.casefold() != "epub":
                return SourceReplayResult(
                    status="FAILED",
                    document_id=UUID(document_id),
                    revision_id=UUID(revision["revision_id"]),
                    span_id=UUID(span_id),
                    node_id=UUID(node_id) if node_id else None,
                    reason_codes=["SOURCE_ANCHOR_FAILED"],
                )
            file_content = await asyncio.to_thread(self.storage.read_file, document.storage_path)
            if hashlib.sha256(file_content).hexdigest() != revision.get("checksum"):
                return SourceReplayResult(
                    status="FAILED",
                    document_id=UUID(document_id),
                    revision_id=UUID(revision["revision_id"]),
                    span_id=UUID(span_id),
                    node_id=UUID(node_id),
                    reason_codes=["SOURCE_ASSET_CHECKSUM_MISMATCH"],
                )
            status, resolved_path = replay_epub_locator(
                file_content,
                locator=node["source_locator"],
                expected_content_hash=node["content_hash"],
            )
            reason_codes = {
                "EXACT": [],
                "RECOVERED": ["SOURCE_LOCATOR_RECOVERED"],
                "FAILED": ["SOURCE_ANCHOR_FAILED"],
            }[status]
            return SourceReplayResult(
                status=status,
                document_id=UUID(document_id),
                revision_id=UUID(revision["revision_id"]),
                span_id=UUID(span_id),
                node_id=UUID(node_id),
                resolved_node_path=resolved_path,
                reason_codes=reason_codes,
            )
        return None

    @staticmethod
    def _current_revision(content_record: dict) -> dict | None:
        revision_id = content_record.get("current_revision_id")
        return next(
            (
                revision
                for revision in content_record.get("revisions", [])
                if revision.get("revision_id") == revision_id
            ),
            None,
        )

    def _with_scan_record(
        self,
        document: UserDocument,
        scan_result: ScanResult,
        checksum: str,
        *,
        extra_reason_codes: tuple[str, ...] = (),
    ) -> dict:
        """Append one immutable scan run and retain a current-record projection."""
        details = dict(document.moderation_details or {})
        runs = self._existing_scan_runs(document, details)
        run_id = str(
            uuid5(
                UUID(document.id),
                f"safety-scan:{checksum}:{SAFETY_SCANNER_VERSION}",
            )
        )
        existing = next((item for item in runs if item.get("run_id") == run_id), None)
        if existing is None:
            record = {
                **scan_result.to_record(),
                "run_id": run_id,
                "checksum": checksum,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
            record["reason_codes"] = list(
                dict.fromkeys([*record.get("reason_codes", []), *extra_reason_codes])
            )
            runs.append(record)
        else:
            record = existing
        details[RAW_ASSET_CHECKSUM_KEY] = checksum
        details[SAFETY_SCAN_CURRENT_KEY] = record
        details[SAFETY_SCAN_RUNS_KEY] = runs
        return details

    @staticmethod
    def _existing_scan_runs(document: UserDocument, details: dict) -> list[dict]:
        runs = [
            dict(item) for item in details.get(SAFETY_SCAN_RUNS_KEY, []) if isinstance(item, dict)
        ]
        if runs:
            return runs
        current = details.get(SAFETY_SCAN_CURRENT_KEY)
        completed_at = (
            document.processing_completed_at.isoformat()
            if document.processing_completed_at is not None
            else None
        )
        if isinstance(current, dict) and current:
            legacy = dict(current)
            legacy.setdefault(
                "run_id",
                str(uuid5(UUID(document.id), "legacy-current-safety-scan")),
            )
            legacy.setdefault("scanner_version", "legacy-unversioned")
            legacy.setdefault("completed_at", completed_at)
            runs.append(legacy)
        elif details.get("reason") == "security_scan_failed":
            runs.append(
                {
                    "run_id": str(uuid5(UUID(document.id), "legacy-quarantine-safety-scan")),
                    "scanner_version": "legacy-unversioned",
                    "verdict": "quarantine",
                    "severity": "high",
                    "reason_codes": ["CONTENT_QUARANTINED"],
                    "threats": list(details.get("threats", [])),
                    "checksum": None,
                    "completed_at": completed_at,
                }
            )
        return runs

    @staticmethod
    def _last_scanner_version(details: dict) -> str | None:
        current = details.get(SAFETY_SCAN_CURRENT_KEY)
        if isinstance(current, dict) and isinstance(current.get("scanner_version"), str):
            return current["scanner_version"]
        runs = details.get(SAFETY_SCAN_RUNS_KEY, [])
        if isinstance(runs, list):
            for item in reversed(runs):
                if isinstance(item, dict) and isinstance(item.get("scanner_version"), str):
                    return item["scanner_version"]
        if details.get("reason") == "security_scan_failed":
            return "legacy-unversioned"
        return None

    @staticmethod
    def last_scanner_version(details: dict) -> str | None:
        """Expose the SYS01 safety-policy version for read-only projections."""

        return DocumentService._last_scanner_version(details)

    @staticmethod
    def _classify_projection_visibility(content: str) -> tuple[str, int, str]:
        lowered = content.lower()
        if any(
            marker in lowered for marker in ("[grader-only]", "参考答案：", "reference answer:")
        ):
            return "solution", 4, "grader_only"
        if "例" in content or "example" in lowered:
            return "example", 1, "learner_visible"
        if "定义" in content or "definition" in lowered:
            return "definition", 1, "learner_visible"
        return "context", 0, "learner_visible"

    @staticmethod
    def _split_visibility_boundaries(chunks: list[str]) -> list[str]:
        """Prevent grader-only material from sharing a learner-visible projection chunk."""
        result: list[str] = []
        for chunk in chunks:
            lowered = chunk.lower()
            marker_positions = [
                position
                for marker in ("[grader-only]", "reference answer:", "参考答案：")
                if (position := lowered.find(marker)) >= 0
            ]
            if not marker_positions:
                result.append(chunk)
                continue
            split_at = min(marker_positions)
            before = chunk[:split_at].strip()
            protected = chunk[split_at:].strip()
            if before:
                result.append(before)
            if protected:
                result.append(protected)
        return result

    async def get_document(self, document_id: str) -> Optional[UserDocument]:
        """获取文档详情"""
        result = await self.db.execute(
            select(UserDocument).where(
                UserDocument.id == document_id,
                UserDocument.is_deleted.is_(False),
            )
        )
        document = result.scalar_one_or_none()

        if document:
            document.access_count += 1
            document.last_accessed_at = datetime.now(timezone.utc)
            await self.db.commit()

        return document

    async def list_user_documents(
        self,
        pseudonym_id: str,
        status: Optional[str] = None,
        subject: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[UserDocument], int]:
        """
        获取用户文档列表

        Returns:
            (文档列表, 总数)
        """
        query = select(UserDocument).where(
            UserDocument.pseudonym_id == pseudonym_id,
            UserDocument.is_deleted.is_(False),
        )

        if status:
            query = query.where(UserDocument.processing_status == status)
        if subject:
            query = query.where(UserDocument.subject == subject)

        count_result = await self.db.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar() or 0

        query = (
            query.order_by(UserDocument.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.db.execute(query)
        documents = list(result.scalars().all())

        return documents, total

    async def delete_document(self, document_id: str, pseudonym_id: str) -> bool:
        """
        删除文档（软删除）
        """
        result = await self.db.execute(
            select(UserDocument).where(
                UserDocument.id == document_id,
                UserDocument.pseudonym_id == pseudonym_id,
            )
        )
        document = result.scalar_one_or_none()

        if document is None:
            return False

        document.is_deleted = True
        document.deleted_at = datetime.now(timezone.utc)
        document.processing_status = ProcessingStatus.FAILED

        await self.db.commit()

        await asyncio.to_thread(self.storage.delete_file, document.storage_path)

        logger.info(
            "document_deleted",
            document_id=document_id,
            pseudonym_id=pseudonym_id,
        )

        return True

    async def get_user_storage_info(self, pseudonym_id: str) -> dict:
        """获取用户存储信息"""
        storage_info = self.storage.get_user_usage(pseudonym_id)

        result = await self.db.execute(
            select(
                func.count(UserDocument.id),
                func.sum(UserDocument.file_size_bytes),
            ).where(
                UserDocument.pseudonym_id == pseudonym_id,
                UserDocument.is_deleted.is_(False),
            )
        )
        doc_count, total_size = result.one()

        return {
            **storage_info,
            "document_count": doc_count or 0,
            "total_document_size": total_size or 0,
        }

    @staticmethod
    def _get_extension(filename: str) -> str:
        """从文件名提取扩展名"""
        if "." in filename:
            return filename.rsplit(".", 1)[-1].lower()
        return ""

    @staticmethod
    def _canonical_document_format(file_extension: str) -> str:
        return {
            "md": "markdown",
            "markdown": "markdown",
            "txt": "text",
        }.get(file_extension.casefold(), file_extension.casefold())

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """粗略估算 token 数"""
        import re

        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        other_chars = len(text) - chinese_chars
        return max(1, int(chinese_chars / 1.5 + other_chars / 4))


def get_document_service(db: AsyncSession) -> DocumentService:
    """获取文档服务实例"""
    return DocumentService(db)

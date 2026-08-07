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
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid5

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.domains.content_knowledge import (
    CONTENT_RECORD_KEY,
    SEGMENTATION_VERSION,
    build_content_revision,
)
from app.models.document import (
    DocumentChunk,
    ModerationStatus,
    ProcessingStatus,
    UserDocument,
)
from app.services.documents.parsers import (
    ParsedContent,
    get_parser,
)
from app.services.documents.security_scanner import get_security_scanner
from app.services.storage.local_storage import LocalFileStorage, get_local_storage

logger = get_logger(__name__)


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
        )

        self.db.add(document)
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

    async def process_document(self, document_id: str) -> UserDocument:
        """
        处理文档（解析 + 安全扫描 + 分块）
        """
        result = await self.db.execute(select(UserDocument).where(UserDocument.id == document_id))
        document = result.scalar_one_or_none()

        if document is None:
            raise ValueError(f"文档不存在: {document_id}")

        try:
            file_content = await asyncio.to_thread(
                self.storage.read_file,
                document.storage_path,
            )
            checksum = hashlib.sha256(file_content).hexdigest()
            canonical = (document.moderation_details or {}).get(CONTENT_RECORD_KEY, {})
            current = self._current_revision(canonical)
            if (
                document.processing_status == ProcessingStatus.COMPLETED
                and current
                and current.get("checksum") == checksum
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

            if scan_result.should_block:
                document.processing_status = ProcessingStatus.FAILED
                document.moderation_status = ModerationStatus.REJECTED
                document.moderation_details = {
                    **(document.moderation_details or {}),
                    "reason": "security_scan_failed",
                    "threats": scan_result.threats,
                }
                document.processing_completed_at = datetime.now(timezone.utc)
                await self.db.commit()

                logger.warning(
                    "document_rejected_by_security_scan",
                    document_id=document_id,
                    threats=scan_result.threats,
                )
                return document

            # 2. 解析文档
            parser = get_parser(document.file_extension)
            parsed: ParsedContent = parser.parse(file_content, document.file_extension)
            canonical_chunks = self._split_visibility_boundaries(parsed.chunks)

            # 3. 建立不可变 revision、SourceSpan 与最小 KnowledgeUnit truth。
            content_record = build_content_revision(
                document_id=UUID(document.id),
                original_filename=document.original_filename,
                file_content=file_content,
                full_text=parsed.full_text,
                chunks=canonical_chunks,
                previous_record=canonical,
                knowledge_point_id=document.knowledge_point_id,
            )
            document.moderation_details = {
                **(document.moderation_details or {}),
                CONTENT_RECORD_KEY: content_record,
                "security_scan": {
                    "severity": scan_result.severity,
                    "threats": scan_result.threats,
                },
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
        knowledge_unit_ids = [
            item["knowledge_unit_id"] for item in revision.get("knowledge_units", [])
        ]

        for idx, content in enumerate(chunks):
            span = spans[idx]
            role, exposure_level, allowed_use = self._classify_projection_visibility(content)
            chunk = DocumentChunk(
                id=str(uuid5(revision_id, f"{SEGMENTATION_VERSION}:chunk:{idx}")),
                document_id=document_id,
                chunk_index=idx,
                content=content,
                token_count=self._estimate_tokens(content),
                chunk_metadata={
                    **metadata,
                    "chunk_index": idx,
                    "total_chunks": len(chunks),
                    "position": round(idx / max(len(chunks) - 1, 1), 2),
                    "revision_id": str(revision_id),
                    "segmentation_version": SEGMENTATION_VERSION,
                    "source_span_ids": [span["span_id"]],
                    "knowledge_unit_ids": knowledge_unit_ids,
                    "pedagogical_role": role,
                    "exposure_level": exposure_level,
                    "allowed_use": allowed_use,
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
        content_record = (document.moderation_details or {}).get(CONTENT_RECORD_KEY, {})
        revision = self._current_revision(content_record)
        if revision is None:
            raise ValueError("canonical content revision missing")
        spans = revision.get("source_spans", [])
        chunks = [item["text"] for item in spans]
        count = await self._create_chunks(
            document_id=document_id,
            chunks=chunks,
            metadata={"format": document.file_extension, "rebuilt": True},
            content_record=content_record,
        )
        document.chunk_count = count
        await self.db.commit()
        return count

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

    @staticmethod
    def _classify_projection_visibility(content: str) -> tuple[str, int, str]:
        lowered = content.lower()
        if any(marker in lowered for marker in ("[grader-only]", "参考答案：", "reference answer:")):
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
    def _estimate_tokens(text: str) -> int:
        """粗略估算 token 数"""
        import re

        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        other_chars = len(text) - chinese_chars
        return max(1, int(chinese_chars / 1.5 + other_chars / 4))


def get_document_service(db: AsyncSession) -> DocumentService:
    """获取文档服务实例"""
    return DocumentService(db)

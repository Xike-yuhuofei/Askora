"""
用户文档模型
支持用户上传自定义文档作为学习内容
通过 pseudonym_id 与用户隐私隔离设计保持一致

表结构：
- user_documents: 文档元数据（关联用户、状态、存储路径）
- document_chunks: 文档分块内容（用于 RAG 检索）
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    null,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ProcessingStatus:
    """文档处理状态"""

    PENDING = "pending"  # 等待处理
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"  # 处理完成
    FAILED = "failed"  # 处理失败
    REJECTED = "rejected"  # 内容审核拒绝
    QUARANTINED = "quarantined"  # 安全隔离，禁止进入检索与 learner-visible map


class ModerationStatus:
    """内容审核状态"""

    PENDING = "pending"  # 待审核
    APPROVED = "approved"  # 审核通过
    REJECTED = "rejected"  # 审核拒绝
    REQUIRES_REVIEW = "requires_review"  # 需人工复核


class MaterialLifecycle:
    """Canonical Material lifecycle (MATLIFE-010/011/013).

    ``active`` MAY participate in ordinary search/retrieval/learning.
    ``trash`` is durable and recoverable; excluded from ordinary visibility.
    ``deleted`` is a terminal legacy tombstone only (MATLIFE-083): the managed
    SourceFile was already removed under the old contract, so the row is a
    historical-loss record and is never restorable. Normal Permanent Delete
    removes the Material row entirely through the canonical Data Control
    ``DOCUMENT`` erasure workflow and therefore does not persist ``deleted``.
    """

    ACTIVE = "active"
    TRASH = "trash"
    DELETED = "deleted"


class TrashReason:
    """Origin/cause of a Material entering Trash (MATLIFE-020)."""

    USER_DELETE = "USER_DELETE"
    BATCH_DELETE = "BATCH_DELETE"
    LEGACY_DELETE_SOURCE_PRESENT = "LEGACY_DELETE_SOURCE_PRESENT"
    LEGACY_SOURCE_ALREADY_REMOVED = "LEGACY_SOURCE_ALREADY_REMOVED"
    OTHER = "OTHER"


class UserDocument(Base):
    """
    用户文档表
    存储用户上传的学习文档元数据
    """

    __tablename__ = "user_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # 用户关联（使用 pseudonym_id 进行隐私隔离）
    pseudonym_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.pseudonym_id"), index=True
    )

    # WSP-021: Workspace attribution. Backfilled at bootstrap; canonical Material
    # writers MUST resolve exact Workspace before writing (nullable only during
    # the additive migration / legacy window).
    workspace_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True, server_default=null()
    )

    # 文件信息
    original_filename: Mapped[str] = mapped_column(String(255))
    # P1-04 canonical, user-editable profile.  The original filename remains
    # immutable source metadata and is only a compatibility fallback.
    display_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_version: Mapped[int] = mapped_column(Integer, default=1)
    file_extension: Mapped[str] = mapped_column(String(20), index=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer)
    storage_path: Mapped[str] = mapped_column(String(500))
    raw_asset_checksum: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    content_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    fingerprint_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # 处理状态
    processing_status: Mapped[str] = mapped_column(
        String(20), default=ProcessingStatus.PENDING, index=True
    )
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    processing_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # 内容审核
    moderation_status: Mapped[str] = mapped_column(
        String(20), default=ModerationStatus.PENDING, index=True
    )
    moderation_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    moderation_categories: Mapped[list] = mapped_column(JSON, default=list)
    moderation_details: Mapped[dict] = mapped_column(JSON, default=dict)

    # 知识关联（用户可选标注）
    subject: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    language: Mapped[str | None] = mapped_column(String(35), nullable=True)
    knowledge_point_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # 分块统计
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)

    # 使用统计
    last_accessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    access_count: Mapped[int] = mapped_column(Integer, default=0)

    # 软删除（生命周期兼容镜像，仅限有界窗口，非真相：MATLIFE-085）
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # 规范 Material lifecycle（MATLIFE-010/011/013/020）
    # lifecycle_version 单调递增，Trash/Restore 乐观并发（MATLIFE-021）
    lifecycle: Mapped[str] = mapped_column(
        String(20), default=MaterialLifecycle.ACTIVE, index=True, server_default="active"
    )
    lifecycle_version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    trashed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    trash_reason: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 关系
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_user_docs_pseudonym_status", "pseudonym_id", "processing_status"),
        Index("idx_user_docs_subject", "subject"),
    )

    @property
    def is_processed(self) -> bool:
        """文档是否已处理完成"""
        return self.processing_status == ProcessingStatus.COMPLETED

    @property
    def is_available(self) -> bool:
        """文档是否可用于检索（已处理 + 审核通过 + active）"""
        return (
            self.processing_status == ProcessingStatus.COMPLETED
            and self.moderation_status == ModerationStatus.APPROVED
            and self.lifecycle == MaterialLifecycle.ACTIVE
        )

    @property
    def is_active(self) -> bool:
        """Canonical active-lifecycle check (MATLIFE-010)."""
        return self.lifecycle == MaterialLifecycle.ACTIVE


class DocumentChunk(Base):
    """
    文档分块表
    存储文档被切分后的内容块，用于 RAG 向量检索
    """

    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # 关联文档
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_documents.id"), index=True
    )

    # 分块内容
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer, default=0)

    # 元数据（用于检索过滤）
    chunk_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    """
    example: {
        "page": 1,
        "heading_level": 2,
        "source_section": "Introduction",
        "is_heading": False,
        "position": 0.15  # 在文档中的位置（0-1）
    }
    """

    # 向量信息（PGVector）
    embedding_model: Mapped[str] = mapped_column(String(100), default="text-embedding-v2")
    embedding_dimension: Mapped[int] = mapped_column(Integer, default=1536)

    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # 关系
    document: Mapped["UserDocument"] = relationship("UserDocument", back_populates="chunks")

    __table_args__ = (Index("idx_chunks_doc_index", "document_id", "chunk_index"),)


class LibraryTag(Base):
    """SYS01-owned flat personal label."""

    __tablename__ = "library_tags"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    pseudonym_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.pseudonym_id"))
    workspace_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True, server_default=null()
    )
    name: Mapped[str] = mapped_column(String(80))
    normalized_name: Mapped[str] = mapped_column(String(80))
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("pseudonym_id", "normalized_name", name="uq_library_tag_owner_name"),
        Index("ix_library_tags_owner_archived", "pseudonym_id", "is_archived"),
    )


class LibraryCollection(Base):
    """SYS01-owned flat collection; nesting and smart rules are intentionally absent."""

    __tablename__ = "library_collections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    pseudonym_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.pseudonym_id"))
    workspace_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True, server_default=null()
    )
    name: Mapped[str] = mapped_column(String(120))
    normalized_name: Mapped[str] = mapped_column(String(120))
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "pseudonym_id", "normalized_name", name="uq_library_collection_owner_name"
        ),
        Index("ix_library_collections_owner_archived", "pseudonym_id", "is_archived"),
    )


class DocumentTagAssignment(Base):
    __tablename__ = "document_tag_assignments"

    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_documents.id"), primary_key=True
    )
    tag_id: Mapped[str] = mapped_column(String(36), ForeignKey("library_tags.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DocumentCollectionAssignment(Base):
    __tablename__ = "document_collection_assignments"

    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_documents.id"), primary_key=True
    )
    collection_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("library_collections.id"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LibrarySearchProjection(Base):
    """Rebuildable current-revision lexical projection, never content truth."""

    __tablename__ = "library_search_projections"

    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_documents.id"), primary_key=True
    )
    pseudonym_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.pseudonym_id"))
    workspace_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True, server_default=null()
    )
    revision_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    index_version: Mapped[str] = mapped_column(String(50))
    normalized_title: Mapped[str] = mapped_column(String(255))
    normalized_body: Mapped[str] = mapped_column(Text, default="")
    source_span_refs: Mapped[list] = mapped_column(JSON, default=list)
    freshness: Mapped[str] = mapped_column(String(20), default="AVAILABLE")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_library_search_owner_title", "pseudonym_id", "normalized_title"),
        Index("ix_library_search_owner_freshness", "pseudonym_id", "freshness"),
    )


class MaterialLifecycleReceipt(Base):
    """Durable idempotency receipt for Material Trash/Restore commands (MATLIFE-022/032).

    A repeat of the same command with the same idempotency key returns the stored
    original result; the same key with a different payload/target is a conflict.
    """

    __tablename__ = "material_lifecycle_receipts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    pseudonym_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.pseudonym_id"))
    workspace_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True, server_default=null()
    )
    material_id: Mapped[str] = mapped_column(String(36), index=True)
    command_type: Mapped[str] = mapped_column(String(30))
    idempotency_key: Mapped[str] = mapped_column(String(200))
    payload_digest: Mapped[str] = mapped_column(String(64))
    result_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "pseudonym_id",
            "command_type",
            "idempotency_key",
            name="uq_material_lifecycle_receipt_owner_command_key",
        ),
    )


class LibraryCommandReceipt(Base):
    """Durable idempotency receipt for SYS01 metadata/batch commands."""

    __tablename__ = "library_command_receipts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    pseudonym_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.pseudonym_id"))
    workspace_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True, server_default=null()
    )
    command_type: Mapped[str] = mapped_column(String(80))
    idempotency_key: Mapped[str] = mapped_column(String(200))
    payload_digest: Mapped[str] = mapped_column(String(64))
    result_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "pseudonym_id",
            "command_type",
            "idempotency_key",
            name="uq_library_receipt_owner_command_key",
        ),
    )


class DuplicateSuggestion(Base):
    """Evidence-bound suggestion; it never performs an automatic merge."""

    __tablename__ = "document_duplicate_suggestions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    pseudonym_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.pseudonym_id"))
    workspace_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True, server_default=null()
    )
    primary_document_id: Mapped[str] = mapped_column(String(36), ForeignKey("user_documents.id"))
    candidate_document_id: Mapped[str] = mapped_column(String(36), ForeignKey("user_documents.id"))
    kind: Mapped[str] = mapped_column(String(30))
    fingerprint_version: Mapped[str] = mapped_column(String(50))
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    resolution_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "primary_document_id",
            "candidate_document_id",
            "fingerprint_version",
            name="uq_document_duplicate_pair_policy",
        ),
        Index("ix_duplicate_suggestions_owner_status", "pseudonym_id", "status"),
    )


class DocumentOcrRun(Base):
    __tablename__ = "document_ocr_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("user_documents.id"))
    pseudonym_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.pseudonym_id"))
    workspace_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True, server_default=null()
    )
    input_revision_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    raw_checksum: Mapped[str] = mapped_column(String(64))
    engine: Mapped[str] = mapped_column(String(50))
    engine_version: Mapped[str] = mapped_column(String(100))
    languages: Mapped[list] = mapped_column(JSON, default=list)
    policy_version: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(30), default="pending")
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    candidate_count: Mapped[int] = mapped_column(Integer, default=0)
    reason_codes: Mapped[list] = mapped_column(JSON, default=list)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("pseudonym_id", "idempotency_key", name="uq_ocr_run_owner_key"),
        Index("ix_document_ocr_runs_document_status", "document_id", "status"),
    )


class DocumentOcrCandidate(Base):
    __tablename__ = "document_ocr_candidates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("document_ocr_runs.id"))
    page_number: Mapped[int] = mapped_column(Integer)
    block_index: Mapped[int] = mapped_column(Integer)
    bbox: Mapped[list] = mapped_column(JSON, default=list)
    text: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    image_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20), default="candidate")
    corrected_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("run_id", "page_number", "block_index", name="uq_ocr_run_page_block"),
        Index("ix_document_ocr_candidates_run_status", "run_id", "status"),
    )

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
    func,
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


class ModerationStatus:
    """内容审核状态"""

    PENDING = "pending"  # 待审核
    APPROVED = "approved"  # 审核通过
    REJECTED = "rejected"  # 审核拒绝
    REQUIRES_REVIEW = "requires_review"  # 需人工复核


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

    # 文件信息
    original_filename: Mapped[str] = mapped_column(String(255))
    file_extension: Mapped[str] = mapped_column(String(20), index=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer)
    storage_path: Mapped[str] = mapped_column(String(500))

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
    knowledge_point_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # 分块统计
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)

    # 使用统计
    last_accessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    access_count: Mapped[int] = mapped_column(Integer, default=0)

    # 软删除
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

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
        """文档是否可用于检索（已处理 + 审核通过 + 未删除）"""
        return (
            self.processing_status == ProcessingStatus.COMPLETED
            and self.moderation_status == ModerationStatus.APPROVED
            and not self.is_deleted
        )


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

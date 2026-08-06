"""
对话模型 - 核心业务数据
会话与消息存储，支持流式响应和苏格拉底式教学
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class MessageRole(str, enum.Enum):
    """消息角色"""

    USER = "user"  # 用户
    ASSISTANT = "assistant"  # AI 助手
    SYSTEM = "system"  # 系统消息


class SessionStatus(str, enum.Enum):
    """会话状态"""

    ACTIVE = "active"  # 进行中
    ENDED = "ended"  # 已结束
    ARCHIVED = "archived"  # 已归档
    DELETED = "deleted"  # 已删除（软删除）


class DialogSession(Base):
    """
    对话会话表
    存储会话元数据，通过 pseudonym_id 关联用户（不含直接 PII）
    """

    __tablename__ = "dialog_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # 用户关联（使用假名化 ID，学习数据域与 PII 物理隔离）
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    pseudonym_id: Mapped[str] = mapped_column(String(32), index=True)

    # 会话信息
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    subject: Mapped[str] = mapped_column(String(100), default="general")  # 学科
    topic: Mapped[str | None] = mapped_column(String(200), nullable=True)  # 当前主题
    knowledge_point_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # 状态
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus), default=SessionStatus.ACTIVE, index=True
    )

    # 苏格拉底教学状态
    current_hint_level: Mapped[int] = mapped_column(Integer, default=1)  # 1-5 级渐次提示
    current_strategy: Mapped[str | None] = mapped_column(String(100), nullable=True)
    hint_escalation_count: Mapped[int] = mapped_column(Integer, default=0)
    wrong_streak: Mapped[int] = mapped_column(Integer, default=0)

    # 掌握度估计（会话级）
    mastery_estimate: Mapped[float] = mapped_column(Float, default=0.0)

    # 元认知目标
    meta_cognitive_goal: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # 统计
    turn_count: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)

    # 内容审核状态
    moderation_status: Mapped[str] = mapped_column(String(50), default="passed")
    """
    passed: 通过
    flagged: 已标记
    rejected: 已拒绝
    degraded: 降级模式下生成
    """

    # 模型信息
    model_provider: Mapped[str] = mapped_column(String(50), default="qwen")
    model_name: Mapped[str] = mapped_column(String(100), default="qwen-turbo")

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # 软删除
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="dialog_sessions")
    messages: Mapped[list["DialogMessage"]] = relationship(
        "DialogMessage", back_populates="session", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_dialog_user_status", "user_id", "status"),
        Index("idx_dialog_pseudonym_created", "pseudonym_id", "created_at"),
    )


class DialogMessage(Base):
    """
    对话消息表
    存储每轮对话的详细内容
    """

    __tablename__ = "dialog_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("dialog_sessions.id"), index=True
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)

    # 消息基本信息
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole), index=True)
    content: Mapped[str] = mapped_column(Text)
    turn_number: Mapped[int] = mapped_column(Integer)  # 第几轮

    # 苏格拉底教学元数据（仅 assistant 消息有）
    strategy: Mapped[str | None] = mapped_column(String(100), nullable=True)
    hint_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    intent: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 用户意图识别

    # 内容审核结果
    moderation_result: Mapped[dict] = mapped_column(JSON, default=dict)
    """
    示例:
    {
        "passed": true,
        "level": "L0",
        "categories": [],
        "confidence": 0.98,
        "provider": "aliyun",
        "latency_ms": 45
    }
    """
    moderation_degrade_level: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # 生成内容标识
    is_ai_generated: Mapped[bool] = mapped_column(default=True)
    watermark_info: Mapped[dict] = mapped_column(JSON, default=dict)

    # Token 使用
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)

    # 性能指标
    ttft_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 首 Token 延迟
    generation_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 生成总耗时

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # 关系
    session: Mapped["DialogSession"] = relationship("DialogSession", back_populates="messages")

    __table_args__ = (
        Index("idx_message_session_turn", "session_id", "turn_number"),
        Index("idx_message_user_created", "user_id", "created_at"),
        UniqueConstraint(
            "session_id",
            "turn_number",
            "role",
            name="uq_dialog_message_turn_role",
        ),
    )

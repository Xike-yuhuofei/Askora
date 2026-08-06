"""
用户画像模型 - 学习数据与 PII 物理隔离
通过 pseudonym_id 关联，学习数据域不含直接 PII
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class UserProfile(Base):
    """
    用户学习画像表
    存储学习相关的聚合数据，L3 重要级别
    通过 pseudonym_id 与用户关联，不含直接 PII
    """

    __tablename__ = "user_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # 假名化 ID（与 users 表关联，但物理隔离）
    pseudonym_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)

    # 学科偏好
    favorite_subjects: Mapped[dict] = mapped_column(JSON, default=list)

    # 学习统计
    total_sessions: Mapped[int] = mapped_column(Integer, default=0)
    total_learning_minutes: Mapped[int] = mapped_column(Integer, default=0)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    skills_mastered: Mapped[int] = mapped_column(Integer, default=0)

    # 掌握度概览（按学科聚合）
    mastery_summary: Mapped[dict] = mapped_column(JSON, default=dict)
    """
    示例:
    {
        "math": {"mastery": 0.45, "kp_count": 120, "mastered_count": 54},
        "chinese": {"mastery": 0.62, "kp_count": 100, "mastered_count": 62}
    }
    """

    # 元认知能力评估
    metacognition: Mapped[dict] = mapped_column(JSON, default=dict)
    """
    示例:
    {
        "planning_ability": 0.5,
        "monitoring_ability": 0.4,
        "evaluation_ability": 0.35,
        "reflection_quality": 0.45
    }
    """

    # 情感状态
    affective: Mapped[dict] = mapped_column(JSON, default=dict)
    """
    示例:
    {
        "engagement_level": 0.7,
        "frustration_level": 0.3,
        "confidence_level": 0.5
    }
    """

    # 年级信息（L3 级别，不存具体学校班级）
    grade_level: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 关系 - 通过 pseudonym_id 关联（PII 与学习数据物理隔离）
    user: Mapped["User"] = relationship(
        "User",
        back_populates="profiles",
        primaryjoin="UserProfile.pseudonym_id == User.pseudonym_id",
        foreign_keys="UserProfile.pseudonym_id",
    )


class ChildProfile(Base):
    """
    儿童扩展信息
    家长可查看的儿童学习相关设置
    """

    __tablename__ = "child_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # 关联的儿童用户（假名化 ID）
    child_pseudonym_id: Mapped[str] = mapped_column(String(32), index=True)

    # 家长设置
    daily_time_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 分钟
    allowed_subjects: Mapped[list] = mapped_column(JSON, default=list)
    blocked_keywords: Mapped[list] = mapped_column(JSON, default=list)

    # 学习目标
    learning_goals: Mapped[dict] = mapped_column(JSON, default=dict)

    # 家长可见的学习摘要（脱敏后）
    learning_summary: Mapped[dict] = mapped_column(JSON, default=dict)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ParentChildRelation(Base):
    """
    家长-儿童绑定关系
    记录监护关系，用于数据访问授权
    """

    __tablename__ = "parent_child_relations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    parent_id: Mapped[str] = mapped_column(String(36), index=True)
    child_id: Mapped[str] = mapped_column(String(36), index=True)

    # 关系类型
    relation_type: Mapped[str] = mapped_column(String(50), default="parent")  # parent/guardian

    # 授权状态
    is_guardian_consent_given: Mapped[bool] = mapped_column(Boolean, default=False)
    guardian_consent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # 权限范围
    can_view_dialogs: Mapped[bool] = mapped_column(Boolean, default=True)
    can_view_assessments: Mapped[bool] = mapped_column(Boolean, default=True)
    can_manage_account: Mapped[bool] = mapped_column(Boolean, default=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (UniqueConstraint("parent_id", "child_id", name="uq_parent_child"),)

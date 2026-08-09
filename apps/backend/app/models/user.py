"""
用户模型 - 精简版
个人用户场景：支持基础用户账号
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.dialog import DialogSession
    from app.models.profile import UserProfile


class UserRole(str, enum.Enum):
    """用户角色（简化版）"""

    USER = "user"  # 个人用户


class UserStatus(str, enum.Enum):
    """用户状态"""

    ACTIVE = "active"  # 正常
    PENDING_VERIFICATION = "pending_verification"  # 待审核
    SUSPENDED = "suspended"  # 已停用
    DELETED = "deleted"  # 已删除（软删除）


class User(Base):
    """
    用户基础信息表
    精简版：移除了多角色/儿童账号/学校等平台功能
    """

    __tablename__ = "users"

    # 主键
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # 角色与状态
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER, index=True)
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus), default=UserStatus.ACTIVE, index=True
    )
    # IDP-043 account lifecycle is distinct from legacy availability/status.
    account_lifecycle: Mapped[str] = mapped_column(
        String(32), nullable=False, default="active", server_default="active", index=True
    )

    # 认证信息
    phone_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 仅用于等值查找；HMAC 不能还原手机号，并由数据库唯一约束防并发重复注册。
    phone_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )
    email_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    nickname: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # 密码哈希
    password_hash: Mapped[str | None] = mapped_column(String(256), nullable=True)
    credential_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    password_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # 微信 OpenID
    wechat_openid_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 实名信息（可选）
    real_name_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # 假名化 ID（用于学习数据关联，不暴露真实 user_id）
    pseudonym_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # 软删除
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # 关系
    profiles: Mapped[list["UserProfile"]] = relationship(
        "UserProfile",
        back_populates="user",
        primaryjoin="User.pseudonym_id == UserProfile.pseudonym_id",
        foreign_keys="UserProfile.pseudonym_id",
        cascade="all, delete-orphan",
    )
    dialog_sessions: Mapped[list["DialogSession"]] = relationship(
        "DialogSession", back_populates="user", cascade="all, delete-orphan"
    )
    __table_args__ = (
        CheckConstraint("credential_version > 0", name="ck_users_credential_version_positive"),
        CheckConstraint(
            "account_lifecycle IN ('active', 'deletion_pending', 'purging', "
            "'deletion_blocked', 'deleted')",
            name="ck_users_account_lifecycle",
        ),
        Index("idx_users_role_status", "role", "status"),
    )

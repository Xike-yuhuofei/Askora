"""
LocalOwner 兼容投影模型
Askora 为本地单机个人学习 App，无用户账号/登录/认证体系。
本表仅作为学习者数据归属的 transitional compatibility projection：
保留 id / pseudonym_id 等被历史表外键引用的字段，不含任何登录凭据。
LocalOwner 是唯一身份真源（见 app/infrastructure/local_owner.py）。
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum,
    Index,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.dialog import DialogSession
    from app.models.profile import UserProfile


class UserRole(str, enum.Enum):
    """单用户学习者角色"""

    USER = "user"


class UserStatus(str, enum.Enum):
    """本地学习者状态（单一本地实例恒为 ACTIVE）"""

    ACTIVE = "active"


class User(Base):
    """
    LocalOwner 兼容投影表（无认证语义）。

    仅保留被历史表外键引用的归属字段；登录账号、密码、会话、
    OAuth、验证等认证专用列已全部移除。
    """

    __tablename__ = "users"

    # 主键：等价于 LocalOwner owner_id
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # 学习者角色与状态（单用户恒为 USER / ACTIVE）
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER, index=True)
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus), default=UserStatus.ACTIVE, index=True
    )
    nickname: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # 假名化 ID（用于学习数据关联，不暴露 owner_id）
    pseudonym_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

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
    __table_args__ = (Index("idx_users_role_status", "role", "status"),)

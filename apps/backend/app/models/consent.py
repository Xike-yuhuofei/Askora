"""
同意管理模型 - PIPL 合规核心
记录用户的各项同意，支持撤回和审计
"""

from __future__ import annotations

import enum
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class ConsentType(str, enum.Enum):
    """同意类型"""

    # 必要同意（不可拒绝）
    TERMS_OF_SERVICE = "terms_of_service"  # 服务条款
    PRIVACY_POLICY = "privacy_policy"  # 隐私政策
    NECESSARY_DATA_COLLECTION = "necessary_data_collection"  # 必要数据收集

    # 可选同意
    PERSONALIZATION = "personalization"  # 个性化推荐
    DATA_ANALYTICS = "data_analytics"  # 数据分析
    MARKETING = "marketing"  # 营销推送

    # 未成年人特殊同意
    GUARDIAN_CONSENT = "guardian_consent"  # 监护人单独同意
    MINOR_DATA_PROCESSING = "minor_data_processing"  # 未成年人信息处理

    # 教育场景特殊同意
    EDUCATIONAL_DATA_USE = "educational_data_use"  # 教育数据使用
    VOICE_DATA_COLLECTION = "voice_data_collection"  # 语音数据收集


class ConsentStatus(str, enum.Enum):
    """同意状态"""

    GRANTED = "granted"  # 已同意
    WITHDRAWN = "withdrawn"  # 已撤回
    EXPIRED = "expired"  # 已过期


class ConsentRecord(Base):
    """
    同意记录表
    记录每次同意/撤回操作，支持完整审计追踪
    """

    __tablename__ = "consent_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)

    # 同意类型
    consent_type: Mapped[ConsentType] = mapped_column(Enum(ConsentType), index=True)

    # 状态
    status: Mapped[ConsentStatus] = mapped_column(
        Enum(ConsentStatus), default=ConsentStatus.GRANTED
    )

    # 同意版本（用于版本更新时重新获取同意）
    consent_version: Mapped[str] = mapped_column(String(50))

    # 同意时展示的完整文案（留痕，用于举证）
    consent_text: Mapped[str] = mapped_column(Text)

    # 操作方式
    action_method: Mapped[str] = mapped_column(String(50))
    """
    示例:
    - checkbox_checked: 勾选确认框
    - button_click: 点击同意按钮
    - guardian_verified: 监护人验证通过
    - sms_verified: 短信验证
    """

    # 操作时的上下文信息
    context: Mapped[dict] = mapped_column(JSON, default=dict)
    """
    示例:
    {
        "ip": "192.168.1.1",
        "user_agent": "...",
        "device_type": "ios",
        "screen": "settings/privacy"
    }
    """

    # 监护人信息（未成年人同意时）
    guardian_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    guardian_verification_method: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # sms / id_card / wechat

    # 时间戳
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # 关系
    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        Index("idx_consent_user_type", "user_id", "consent_type"),
        Index("idx_consent_status", "status"),
    )

    @property
    def is_active(self) -> bool:
        """同意是否有效"""
        if self.status != ConsentStatus.GRANTED:
            return False
        if self.expires_at and self.expires_at < datetime.now(UTC):
            return False
        return True

"""
固定演示用户保障

开发/本地调试用：保证固定演示账号存在，供开发自动登录（免登录直接进入系统）。
仅应在非生产环境、且显式开启 dev auto login 时使用，不承载任何生产语义。
"""

from __future__ import annotations

import hashlib
import hmac

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.encryption import encrypt_pii
from app.core.logging import get_logger
from app.models.user import User, UserRole, UserStatus
from app.services.auth.token_service import hash_password

logger = get_logger(__name__)

# 固定演示用户（与 scripts/init_test_data.py 保持一致）
DEV_DEMO_USER_ID = "test-user-001"
DEV_DEMO_PHONE = "15967954989"
DEV_DEMO_PASSWORD = "asdf1234."
DEV_DEMO_PSEUDONYM_ID = "user_pseudo_001"
DEV_DEMO_NICKNAME = "演示用户"


def _phone_lookup_hash(phone: str) -> str:
    """为手机号生成不可逆、可查询的 HMAC 盲索引。"""
    return hmac.new(
        settings.kek_master_key.encode(),
        phone.encode(),
        hashlib.sha256,
    ).hexdigest()


async def ensure_demo_user(db: AsyncSession) -> User:
    """
    确保固定演示用户存在并返回之。

    幂等：已存在（含旧账号已回填密码）则直接返回；缺失则创建。
    """
    result = await db.execute(select(User).where(User.id == DEV_DEMO_USER_ID))
    user = result.scalar_one_or_none()

    if user is not None and user.password_hash:
        return user

    if user is None:
        user = User(
            id=DEV_DEMO_USER_ID,
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            phone_encrypted=encrypt_pii(DEV_DEMO_PHONE),
            phone_hash=_phone_lookup_hash(DEV_DEMO_PHONE),
            password_hash=hash_password(DEV_DEMO_PASSWORD),
            nickname=DEV_DEMO_NICKNAME,
            pseudonym_id=DEV_DEMO_PSEUDONYM_ID,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info("dev_demo_user_created", user_id=user.id)

    return user

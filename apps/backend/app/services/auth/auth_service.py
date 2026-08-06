"""
认证服务 - 简化版
处理登录、登出、Token 刷新、并发会话限制
移除了审计日志依赖，适合个人用户场景
"""

from __future__ import annotations

import hashlib
import hmac
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.encryption import decrypt_pii, encrypt_pii
from app.core.exceptions import (
    DeviceMismatchError,
    InvalidTokenError,
    TooManySessionsError,
)
from app.core.logging import get_logger
from app.core.redis_client import get_redis_client, is_redis_available, mark_redis_unavailable
from app.models.user import User, UserRole, UserStatus
from app.services.auth.token_service import (
    TokenService,
    hash_password,
    verify_password,
)

logger = get_logger(__name__)

# 并发会话限制（简化版）
MAX_SESSIONS = 5


class AuthService:
    """认证服务（简化版）"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def login_with_phone(
        self,
        phone: str,
        password: str,
        device_fingerprint: Optional[str] = None,
    ) -> tuple[str, str, datetime, User]:
        """
        手机号密码登录

        Returns:
            (access_token, refresh_token, expires_at, user)
        """
        # 查找用户
        phone = phone.strip()
        phone_hash = self._phone_lookup_hash(phone)
        result = await self.db.execute(select(User).where(User.phone_hash == phone_hash))
        user: Optional[User] = result.scalar_one_or_none()

        # 兼容迁移前没有 phone_hash 的旧账号；成功登录后自动回填。
        if user is None:
            result = await self.db.execute(
                select(User).where(
                    User.phone_hash.is_(None),
                    User.phone_encrypted.isnot(None),
                )
            )
            for candidate in result.scalars().all():
                try:
                    if (
                        candidate.phone_encrypted
                        and decrypt_pii(candidate.phone_encrypted) == phone
                    ):
                        user = candidate
                        user.phone_hash = phone_hash
                        break
                except Exception:
                    logger.warning("legacy_phone_decrypt_failed", user_id=candidate.id)

        if not user or not user.password_hash:
            raise InvalidTokenError("手机号或密码错误")

        # 验证密码
        if not verify_password(password, user.password_hash):
            raise InvalidTokenError("手机号或密码错误")

        # 检查状态
        if user.status != UserStatus.ACTIVE:
            raise InvalidTokenError(f"账号状态异常：{user.status.value}")

        # 检查并发会话数
        await self._check_session_limit(user)

        # 生成 Token
        device_fp_hash = (
            self._hash_device_fingerprint(device_fingerprint) if device_fingerprint else None
        )
        access_token, access_jti, expires_at = TokenService.create_access_token(
            user_id=user.id,
            role=user.role.value,
            pseudonym_id=user.pseudonym_id,
            device_fingerprint=device_fp_hash,
        )
        refresh_token, _, _ = TokenService.create_refresh_token(
            user_id=user.id,
            role=user.role.value,
            pseudonym_id=user.pseudonym_id,
            device_fingerprint=device_fp_hash,
        )

        # 更新最后登录时间
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.commit()

        # 记录会话
        await self._register_session(user.id, access_jti, device_fp_hash)

        logger.info("user_login_success", user_id=user.id)
        return access_token, refresh_token, expires_at, user

    async def logout(self, user_id: str, token_jti: str) -> None:
        """用户登出"""
        expires_in = settings.access_token_expire_minutes * 60
        await TokenService.revoke_token(token_jti, expires_in)
        await self._unregister_session(user_id, token_jti)
        logger.info("user_logout", user_id=user_id)

    async def validate_token_and_get_user(
        self,
        token: str,
        device_fingerprint: Optional[str] = None,
    ) -> tuple[User, dict]:
        """验证 Token 并返回用户和 Token 载荷"""
        payload = TokenService.decode_token(token, token_type="access")

        user_id = payload.get("sub")
        jti = payload.get("jti")

        if not user_id or not jti:
            raise InvalidTokenError()

        if await TokenService.is_token_revoked(jti):
            raise InvalidTokenError("Token 已失效")

        expected_device_fp = payload.get("dfp")
        if expected_device_fp:
            if not device_fingerprint:
                raise DeviceMismatchError()
            actual_device_fp = self._hash_device_fingerprint(device_fingerprint)
            if not hmac.compare_digest(expected_device_fp, actual_device_fp):
                raise DeviceMismatchError()

        user = await self.db.get(User, user_id)
        if not user or user.status != UserStatus.ACTIVE:
            raise InvalidTokenError("用户不存在或已停用")

        return user, payload

    async def _check_session_limit(self, user: User) -> None:
        """检查并发会话数限制"""
        if is_redis_available() is False and settings.auto_create_tables:
            return
        try:
            redis = get_redis_client()
            key = f"session:active:{user.id}"
            now = int(datetime.now(timezone.utc).timestamp())
            await redis.zremrangebyscore(key, "-inf", now)
            current_count = await redis.zcard(key)

            if current_count >= MAX_SESSIONS:
                raise TooManySessionsError(MAX_SESSIONS)
        except TooManySessionsError:
            raise
        except Exception as e:
            mark_redis_unavailable()
            logger.warning(
                "redis_session_check_failed",
                user_id=user.id,
                error_type=type(e).__name__,
            )
            if not settings.auto_create_tables:
                from app.core.exceptions import AuthenticationStateUnavailableError

                raise AuthenticationStateUnavailableError() from e

    async def _register_session(
        self, user_id: str, session_jti: str, device_fp_hash: Optional[str]
    ) -> None:
        """注册活跃会话"""
        if is_redis_available() is False and settings.auto_create_tables:
            return
        try:
            redis = get_redis_client()
            key = f"session:active:{user_id}"
            ttl = settings.access_token_expire_minutes * 60
            expires_at = int(datetime.now(timezone.utc).timestamp()) + ttl

            await redis.zadd(key, {session_jti: expires_at})
            await redis.expire(key, ttl)

            if device_fp_hash:
                device_key = f"session:device:{user_id}:{session_jti}"
                await redis.setex(device_key, ttl, device_fp_hash)
        except Exception as e:
            mark_redis_unavailable()
            logger.warning(
                "redis_session_register_failed",
                user_id=user_id,
                error_type=type(e).__name__,
            )
            if not settings.auto_create_tables:
                from app.core.exceptions import AuthenticationStateUnavailableError

                raise AuthenticationStateUnavailableError() from e

    async def _unregister_session(self, user_id: str, session_jti: str) -> None:
        """注销会话"""
        if is_redis_available() is False and settings.auto_create_tables:
            return
        try:
            redis = get_redis_client()
            key = f"session:active:{user_id}"
            await redis.zrem(key, session_jti)

            device_key = f"session:device:{user_id}:{session_jti}"
            await redis.delete(device_key)
        except Exception as e:
            mark_redis_unavailable()
            logger.warning(
                "redis_session_unregister_failed",
                user_id=user_id,
                error_type=type(e).__name__,
            )
            if not settings.auto_create_tables:
                from app.core.exceptions import AuthenticationStateUnavailableError

                raise AuthenticationStateUnavailableError() from e

    @staticmethod
    def _hash_device_fingerprint(device_fingerprint: str) -> str:
        """生成设备指纹哈希"""
        return hmac.new(
            settings.kek_master_key.encode(),
            device_fingerprint.encode(),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def _phone_lookup_hash(phone: str) -> str:
        """为手机号生成不可逆、可查询的 HMAC 盲索引。"""
        return hmac.new(
            settings.kek_master_key.encode(),
            phone.encode(),
            hashlib.sha256,
        ).hexdigest()

    async def refresh_tokens(
        self,
        refresh_token: str,
        device_fingerprint: Optional[str] = None,
    ) -> tuple[str, str, datetime]:
        """轮换 Refresh Token，并从数据库重新读取当前用户身份。"""
        payload = TokenService.decode_token(refresh_token, token_type="refresh")
        user_id = payload.get("sub")
        if not user_id:
            raise InvalidTokenError("Refresh Token 格式无效")

        expected_device_fp = payload.get("dfp")
        if expected_device_fp:
            if not device_fingerprint:
                raise DeviceMismatchError()
            actual_device_fp = self._hash_device_fingerprint(device_fingerprint)
            if not hmac.compare_digest(expected_device_fp, actual_device_fp):
                raise DeviceMismatchError()

        user = await self.db.get(User, user_id)
        if not user or user.status != UserStatus.ACTIVE:
            raise InvalidTokenError("用户不存在或已停用")

        await TokenService.consume_refresh_token(payload)
        access_token, _, expires_at = TokenService.create_access_token(
            user_id=user.id,
            role=user.role.value,
            pseudonym_id=user.pseudonym_id,
            device_fingerprint=expected_device_fp,
        )
        new_refresh_token, _, _ = TokenService.create_refresh_token(
            user_id=user.id,
            role=user.role.value,
            pseudonym_id=user.pseudonym_id,
            device_fingerprint=expected_device_fp,
        )
        return access_token, new_refresh_token, expires_at

    async def register_user(
        self,
        phone: str,
        password: str,
        nickname: Optional[str] = None,
    ) -> User:
        """用户注册"""
        # 检查手机号是否已注册
        phone = phone.strip()
        phone_hash = self._phone_lookup_hash(phone)
        result = await self.db.execute(select(User).where(User.phone_hash == phone_hash))
        if result.scalar_one_or_none() is not None:
            raise ValueError("该手机号已注册")

        result = await self.db.execute(
            select(User).where(
                User.phone_hash.is_(None),
                User.phone_encrypted.isnot(None),
            )
        )
        existing_users = result.scalars().all()

        for u in existing_users:
            try:
                if u.phone_encrypted and decrypt_pii(u.phone_encrypted) == phone:
                    raise ValueError("该手机号已注册")
            except ValueError:
                raise
            except Exception:
                logger.warning("legacy_phone_decrypt_failed", user_id=u.id)
                continue

        # 创建新用户
        user_id = str(uuid.uuid4())
        pseudonym_id = uuid.uuid4().hex

        user = User(
            id=user_id,
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            phone_encrypted=encrypt_pii(phone),
            phone_hash=phone_hash,
            password_hash=hash_password(password),
            nickname=nickname.strip() if nickname and nickname.strip() else None,
            pseudonym_id=pseudonym_id,
        )

        self.db.add(user)
        try:
            await self.db.commit()
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError("该手机号已注册") from e
        await self.db.refresh(user)

        logger.info("user_registered", user_id=user.id)
        return user

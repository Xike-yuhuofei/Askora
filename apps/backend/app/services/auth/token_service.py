"""
JWT Token 服务
Access Token（15分钟）+ Refresh Token（7天，Rotation）
儿童账号额外绑定设备指纹
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt
from jwt import InvalidTokenError as PyJWTError
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import AuthenticationStateUnavailableError, InvalidTokenError
from app.core.logging import get_logger
from app.core.redis_client import (
    RedisKeys,
    get_redis_client,
    is_redis_available,
    mark_redis_unavailable,
)

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = get_logger(__name__)

# 私人本地/开发/测试模式在 Redis 暂不可用时使用进程内黑名单。生产环境不降级放行。
_local_revoked_tokens: dict[str, float] = {}
_local_revoke_lock = asyncio.Lock()


class TokenType:
    ACCESS = "access"
    REFRESH = "refresh"


class TokenService:
    """Token 管理服务"""

    @staticmethod
    def _create_token(
        subject: str,
        token_type: str,
        expires_delta: timedelta,
        extra_claims: Optional[dict[str, Any]] = None,
    ) -> tuple[str, str]:
        """
        创建 JWT Token

        Returns:
            (token, jti): Token 字符串和唯一标识
        """
        jti = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        expire = now + expires_delta

        claims: dict[str, Any] = {
            "sub": subject,  # user_id
            "type": token_type,
            "jti": jti,
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
            "iss": settings.app_name,
        }

        if extra_claims:
            claims.update(extra_claims)

        token = jwt.encode(
            claims,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        return token, jti

    @classmethod
    def create_access_token(
        cls,
        user_id: str,
        role: str,
        pseudonym_id: str,
        device_fingerprint: Optional[str] = None,
    ) -> tuple[str, str, datetime]:
        """
        创建 Access Token

        Returns:
            (token, jti, expires_at)
        """
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
        expires_at = datetime.now(timezone.utc) + expires_delta

        extra_claims = {
            "role": role,
            "pseudonym_id": pseudonym_id,
        }
        if device_fingerprint:
            extra_claims["dfp"] = device_fingerprint

        token, jti = cls._create_token(
            subject=user_id,
            token_type=TokenType.ACCESS,
            expires_delta=expires_delta,
            extra_claims=extra_claims,
        )
        return token, jti, expires_at

    @classmethod
    def create_refresh_token(
        cls,
        user_id: str,
        role: str,
        pseudonym_id: str,
        device_fingerprint: Optional[str] = None,
    ) -> tuple[str, str, datetime]:
        """
        创建 Refresh Token（带 Rotation）

        Returns:
            (token, jti, expires_at)
        """
        expires_delta = timedelta(days=settings.refresh_token_expire_days)
        expires_at = datetime.now(timezone.utc) + expires_delta

        extra_claims = {
            "role": role,
            "pseudonym_id": pseudonym_id,
        }
        if device_fingerprint:
            extra_claims["dfp"] = device_fingerprint

        token, jti = cls._create_token(
            subject=user_id,
            token_type=TokenType.REFRESH,
            expires_delta=expires_delta,
            extra_claims=extra_claims,
        )
        return token, jti, expires_at

    @staticmethod
    def decode_token(token: str, token_type: Optional[str] = None) -> dict[str, Any]:
        """
        解码并验证 Token

        Raises:
            InvalidTokenError: Token 无效或过期
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
                issuer=settings.app_name,
            )

            # 验证 token 类型
            if token_type and payload.get("type") != token_type:
                raise InvalidTokenError("Token 类型不匹配")

            return payload
        except PyJWTError as e:
            raise InvalidTokenError(f"Token 无效：{str(e)}")

    @staticmethod
    async def revoke_token(jti: str, expires_in_seconds: int) -> None:
        """
        吊销 Token（加入黑名单）
        用于登出和 Refresh Token Rotation
        Redis 故障时仅私人本地/开发/测试模式降级为进程内黑名单。
        """
        expires_at = datetime.now(timezone.utc).timestamp() + max(1, expires_in_seconds)
        async with _local_revoke_lock:
            _local_revoked_tokens[jti] = expires_at
        if is_redis_available() is False:
            if not settings.auto_create_tables:
                raise AuthenticationStateUnavailableError()
            return
        try:
            redis = get_redis_client()
            key = RedisKeys.format(RedisKeys.TOKEN_BLACKLIST, token_jti=jti)
            await redis.setex(key, max(1, expires_in_seconds), "1")
        except Exception as e:
            mark_redis_unavailable()
            logger.warning("redis_token_revoke_failed", jti=jti[:8], error_type=type(e).__name__)
            if not settings.auto_create_tables:
                raise AuthenticationStateUnavailableError() from e

    @staticmethod
    async def is_token_revoked(jti: str) -> bool:
        """检查 Token 是否已被吊销；生产环境 Redis 故障时拒绝放行。"""
        now = datetime.now(timezone.utc).timestamp()
        async with _local_revoke_lock:
            expired = [key for key, expiry in _local_revoked_tokens.items() if expiry <= now]
            for key in expired:
                _local_revoked_tokens.pop(key, None)
            if jti in _local_revoked_tokens:
                return True
        if is_redis_available() is False:
            if not settings.auto_create_tables:
                raise AuthenticationStateUnavailableError()
            return False
        try:
            redis = get_redis_client()
            key = RedisKeys.format(RedisKeys.TOKEN_BLACKLIST, token_jti=jti)
            result = await redis.exists(key)
            return result > 0
        except Exception as e:
            mark_redis_unavailable()
            logger.warning("redis_token_check_failed", jti=jti[:8], error_type=type(e).__name__)
            if not settings.auto_create_tables:
                raise AuthenticationStateUnavailableError() from e
            return False

    @classmethod
    async def consume_refresh_token(cls, payload: dict[str, Any]) -> None:
        """原子消费 Refresh Token，防止并发重放。"""
        jti = payload.get("jti")
        exp_timestamp = payload.get("exp", 0)
        if not jti:
            raise InvalidTokenError("Refresh Token 格式无效")
        remaining_seconds = max(
            1,
            int(exp_timestamp - datetime.now(timezone.utc).timestamp()),
        )

        if is_redis_available() is False:
            if not settings.auto_create_tables:
                raise AuthenticationStateUnavailableError()
            await cls._consume_refresh_token_locally(jti, remaining_seconds)
            return

        try:
            redis = get_redis_client()
            key = RedisKeys.format(RedisKeys.TOKEN_BLACKLIST, token_jti=jti)
            consumed = await redis.set(key, "1", ex=remaining_seconds, nx=True)
            if not consumed:
                raise InvalidTokenError("Refresh Token 已失效，请重新登录")
            async with _local_revoke_lock:
                _local_revoked_tokens[jti] = (
                    datetime.now(timezone.utc).timestamp() + remaining_seconds
                )
            return
        except InvalidTokenError:
            raise
        except Exception as e:
            mark_redis_unavailable()
            logger.warning("redis_refresh_consume_failed", jti=jti[:8], error_type=type(e).__name__)
            if not settings.auto_create_tables:
                raise AuthenticationStateUnavailableError() from e

        await cls._consume_refresh_token_locally(jti, remaining_seconds)

    @staticmethod
    async def _consume_refresh_token_locally(jti: str, remaining_seconds: int) -> None:
        """在私人本地模式原子消费刷新令牌。"""
        async with _local_revoke_lock:
            now = datetime.now(timezone.utc).timestamp()
            if _local_revoked_tokens.get(jti, 0) > now:
                raise InvalidTokenError("Refresh Token 已失效，请重新登录")
            _local_revoked_tokens[jti] = now + remaining_seconds


# 密码相关工具函数
def hash_password(password: str) -> str:
    """哈希密码"""
    if len(password.encode("utf-8")) > 72:
        raise ValueError("密码的 UTF-8 编码不能超过 72 字节")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

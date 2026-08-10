"""
Redis 连接管理
用于会话缓存、限流、Token 黑名单等
"""

from __future__ import annotations

from typing import Any, Optional

import redis.asyncio as redis

from app.core.config import settings

_redis_client: Optional[redis.Redis] = None
_redis_available: Optional[bool] = None


def get_redis_client(skip_check: bool = False) -> Optional[redis.Redis]:
    """获取 Redis 客户端（单例），Redis 不可用时返回 None"""
    global _redis_client
    if _redis_available is False and not skip_check:
        return None
    if _redis_client is None:
        connection_kwargs: dict[str, Any] = {
            "decode_responses": True,
            "max_connections": settings.redis_pool_size,
            "socket_timeout": 5,
            "socket_connect_timeout": 5,
            "retry_on_timeout": True,
        }
        if settings.redis_password:
            connection_kwargs["password"] = settings.redis_password

        _redis_client = redis.from_url(
            settings.redis_url,
            **connection_kwargs,
        )
    return _redis_client


async def init_redis() -> None:
    """初始化 Redis 连接（应用启动时调用）"""
    global _redis_available
    client = get_redis_client(skip_check=True)
    if client is None:
        _redis_available = False
        raise ConnectionError("无法初始化 Redis 客户端")
    try:
        await client.ping()
    except Exception:
        _redis_available = False
        raise
    _redis_available = True


def is_redis_available() -> Optional[bool]:
    """返回最近一次连接状态；None 表示尚未探测。"""
    return _redis_available


def mark_redis_unavailable() -> None:
    """连接失败后开启本地快速降级，避免每个请求重复等待超时。"""
    global _redis_available
    _redis_available = False


async def close_redis() -> None:
    """关闭 Redis 连接（应用关闭时调用）"""
    global _redis_available, _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
    _redis_available = None


# Redis Key 命名空间管理
class RedisKeys:
    """Redis Key 命名规范，避免 Key 冲突"""

    # 会话相关
    SESSION = "session:{session_id}"
    SESSION_TTL = 86400  # 24 小时

    # 用户画像缓存
    USER_PROFILE = "profile:{user_id}"
    USER_PROFILE_TTL = 3600  # 1 小时

    # 限流
    RATE_LIMIT_USER = "rate_limit:user:{user_id}:{window}"
    RATE_LIMIT_IP = "rate_limit:ip:{ip}:{window}"
    RATE_LIMIT_TTL = 60  # 1 分钟

    # Token 黑名单（登出/刷新时使用）
    TOKEN_BLACKLIST = "token:blacklist:{token_jti}"
    TOKEN_BLACKLIST_TTL = 86400 * 7  # 7 天

    # 模板级缓存
    TEMPLATE_CACHE = "template:{template_id}:{hint_level}:{kp_id}"
    TEMPLATE_CACHE_TTL = 86400  # 24 小时

    @classmethod
    def format(cls, key_template: str, **kwargs) -> str:
        return key_template.format(**kwargs)

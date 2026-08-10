"""
认证鉴权依赖 - FastAPI 依赖注入
精简版：移除了多角色权限体系，仅保留基础认证

EXEC-048: 迁移到 LocalOwnerContext，移除 JWT/AuthSession 依赖
"""

from __future__ import annotations

from typing import Optional, TypeAlias

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import InvalidTokenError
from app.models.user import User
from app.services.auth.auth_service import AuthService
from app.services.local_identity import (
    LocalOwnerContext,
    LocalOwnerError,
    LocalOwnerMigrationFailedError,
    ensure_local_owner,
    get_local_owner_context,
)

OwnerProjection: TypeAlias = User


async def get_current_owner(
    db: AsyncSession = Depends(get_db),
) -> LocalOwnerContext:
    """Get LocalOwnerContext for no-auth loopback production."""
    try:
        return await get_local_owner_context(db)
    except LocalOwnerError:
        if settings.is_development or settings.app_env.value == "test":
            return await ensure_local_owner(db)
        raise


async def get_current_owner_projection(
    db: AsyncSession = Depends(get_db),
) -> OwnerProjection:
    """Return the LID-013 ORM compatibility row for legacy service/FK boundaries."""
    ctx = await get_current_owner(db)
    projection_id = ctx.legacy_user_id or ctx.canonical_owner_id
    projection = await db.get(User, projection_id)
    if projection is None:
        raise LocalOwnerMigrationFailedError(
            "LocalOwner compatibility learner row is missing",
            detail={"projection_user_id": projection_id},
        )
    return projection


async def get_current_user_ws(
    token: str,
    device_fingerprint: Optional[str] = None,
    db: Optional[AsyncSession] = None,
) -> User:
    """WebSocket 连接认证"""
    if not token:
        raise InvalidTokenError("缺少认证 Token")

    if db is None:
        from app.core.database import get_session_factory

        factory = get_session_factory()
        async with factory() as session:
            auth_service = AuthService(session)
            user, _ = await auth_service.validate_token_and_get_user(
                token=token,
                device_fingerprint=device_fingerprint,
            )
            return user
    else:
        auth_service = AuthService(db)
        user, _ = await auth_service.validate_token_and_get_user(
            token=token,
            device_fingerprint=device_fingerprint,
        )
        return user


def _extract_token(authorization: Optional[str]) -> str:
    """从 Authorization 头中提取 Bearer Token"""
    if not authorization:
        raise InvalidTokenError("缺少 Authorization 头")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise InvalidTokenError("Authorization 格式错误，应为 Bearer <token>")

    return parts[1]


def _get_device_fingerprint(
    request: Request,
    x_device_fingerprint: Optional[str] = Header(None),
) -> Optional[str]:
    """获取设备指纹"""
    if x_device_fingerprint:
        return x_device_fingerprint

    user_agent = request.headers.get("user-agent", "")
    x_forwarded_for = request.headers.get("x-forwarded-for", "")
    if user_agent or x_forwarded_for:
        return f"{x_forwarded_for}:{user_agent[:50]}"

    return None


async def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_device_fingerprint: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """获取当前认证用户"""
    token = _extract_token(authorization)
    device_fp = x_device_fingerprint or _get_device_fingerprint(request, x_device_fingerprint)

    auth_service = AuthService(db)
    user, _ = await auth_service.validate_token_and_get_user(
        token=token,
        device_fingerprint=device_fp,
    )
    return user


async def get_current_user_with_payload(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_device_fingerprint: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> tuple[User, dict]:
    """获取当前用户及 Token 载荷"""
    token = _extract_token(authorization)
    device_fp = x_device_fingerprint or _get_device_fingerprint(request, x_device_fingerprint)

    auth_service = AuthService(db)
    user, payload = await auth_service.validate_token_and_get_user(
        token=token,
        device_fingerprint=device_fp,
    )
    return user, payload

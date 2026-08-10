"""
认证鉴权依赖 - FastAPI 依赖注入
精简版：移除了多角色权限体系，仅保留基础认证

EXEC-048: 迁移到 LocalOwnerContext，移除 JWT/AuthSession 依赖
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, TypeAlias, cast

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import InvalidTokenError
from app.models.user import User, UserRole, UserStatus
from app.services.auth.auth_service import AuthService
from app.services.local_identity import (
    LocalOwnerContext,
    LocalOwnerError,
    ensure_local_owner,
    get_local_owner_context,
)


@dataclass(frozen=True)
class _OwnerProjectionRuntime:
    """Runtime compatibility projection for legacy services still shaped around User."""

    id: str
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.ACTIVE
    pseudonym_id: str | None = None
    is_verified: bool = True
    account_lifecycle: str = "active"

    @classmethod
    def from_context(cls, ctx: LocalOwnerContext) -> "_OwnerProjectionRuntime":
        return cls(
            id=ctx.canonical_owner_id,
            pseudonym_id=ctx.legacy_pseudonym_id,
        )

    @property
    def canonical_id(self) -> str:
        return self.id


# Transitional LocalOwner cutover boundary:
# legacy application services are still nominally typed as ``User`` even though
# production APIs now resolve a LocalOwner projection. During static checking we
# deliberately expose this compatibility projection as the legacy ``User`` type,
# so the boundary is centralized here instead of scattering dozens of ignores or
# casts across endpoints. Runtime keeps the small immutable projection above.
# This alias should disappear when service signatures are migrated to a shared
# owner protocol / LocalOwnerContext in the dedicated cleanup work.
if TYPE_CHECKING:
    OwnerProjection: TypeAlias = User
else:
    OwnerProjection = _OwnerProjectionRuntime


async def get_current_owner(
    db: AsyncSession = Depends(get_db),
) -> LocalOwnerContext:
    """Get LocalOwnerContext for no-auth loopback production.

    EXEC-048: Replaces get_current_user for production API endpoints.
    No JWT/session validation needed - single-user local instance.

    In test/development environments, auto-bootstraps LocalOwner if missing.
    """
    try:
        return await get_local_owner_context(db)
    except LocalOwnerError:
        if settings.is_development or settings.app_env.value == "test":
            return await ensure_local_owner(db)
        raise


async def get_current_owner_projection(
    db: AsyncSession = Depends(get_db),
) -> OwnerProjection:
    """Get the LocalOwner compatibility projection for legacy service boundaries."""
    ctx = await get_current_owner(db)
    return cast(OwnerProjection, _OwnerProjectionRuntime.from_context(ctx))


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

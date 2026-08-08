"""
开发自动登录接口（仅开发/本地调试）

用于“免登录直接进入系统”，加快调试与迭代。仅在显式开启且非生产环境时可用：
- 由 app.main 按 settings.dev_auto_login_enabled 决定是否注册路由；
- 路由内部再次校验，防止误注册到生产环境。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import LoginResponse
from app.core.config import settings
from app.core.database import get_db
from app.services.auth.auth_service import AuthService
from app.services.auth.demo_user import (
    DEV_DEMO_PASSWORD,
    DEV_DEMO_PHONE,
    ensure_demo_user,
)

router = APIRouter(prefix="/auth/dev", tags=["认证(开发)"])


class DevAutoLoginRequest(BaseModel):
    device_fingerprint: Optional[str] = Field(None, min_length=8, max_length=512)


@router.post("/auto-login", response_model=LoginResponse, summary="开发自动登录")
async def dev_auto_login(
    req: DevAutoLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """使用固定演示用户签发真实 Token，免登录直接进入系统。"""
    if not settings.dev_auto_login_enabled:
        raise HTTPException(status_code=404, detail="开发自动登录未启用")

    await ensure_demo_user(db)

    auth_service = AuthService(db)
    access_token, refresh_token, expires_at, user = await auth_service.login_with_phone(
        phone=DEV_DEMO_PHONE,
        password=DEV_DEMO_PASSWORD,
        device_fingerprint=req.device_fingerprint,
    )

    expires_in = int((expires_at.timestamp() - datetime.now(timezone.utc).timestamp()))

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=max(0, expires_in),
        user={
            "id": user.id,
            "role": user.role.value,
            "status": user.status.value,
            "is_verified": user.is_verified,
            "nickname": user.nickname,
        },
    )

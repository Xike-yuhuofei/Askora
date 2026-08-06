"""私人用户认证 API：注册、登录、令牌刷新和登出。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.services.auth.auth_service import AuthService
from app.services.auth.dependencies import get_current_user, get_current_user_with_payload

router = APIRouter(prefix="/auth", tags=["认证"])


# ========== 请求/响应模型 ==========


class PhoneLoginRequest(BaseModel):
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="中国大陆手机号")
    password: str = Field(..., min_length=8, max_length=128, description="密码")
    device_fingerprint: Optional[str] = Field(None, min_length=8, max_length=512)

    @field_validator("password")
    @classmethod
    def validate_bcrypt_length(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("密码的 UTF-8 编码不能超过 72 字节")
        return value


class RegisterRequest(BaseModel):
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="中国大陆手机号")
    password: str = Field(..., min_length=8, max_length=128, description="密码")
    nickname: Optional[str] = Field(None, max_length=64, description="昵称（选填）")

    @field_validator("password")
    @classmethod
    def validate_bcrypt_length(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("密码的 UTF-8 编码不能超过 72 字节")
        return value


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=32, description="刷新令牌")
    device_fingerprint: Optional[str] = Field(None, min_length=8, max_length=512)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # 秒
    user: dict


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LogoutResponse(BaseModel):
    message: str
    success: bool


# ========== 路由 ==========


@router.post("/login/phone", response_model=LoginResponse, summary="手机号密码登录")
async def login_with_phone(
    req: PhoneLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    私人用户使用手机号密码登录

    - **phone**: 手机号
    - **password**: 密码
    - **device_fingerprint**: 设备指纹（可选；提供后令牌绑定该设备）
    """
    auth_service = AuthService(db)
    access_token, refresh_token, expires_at, user = await auth_service.login_with_phone(
        phone=req.phone,
        password=req.password,
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


@router.post("/register", summary="用户注册")
async def register(
    req: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    新用户注册

    - **phone**: 手机号
    - **password**: 密码（至少 8 位）
    - **nickname**: 昵称（选填）
    """
    auth_service = AuthService(db)
    try:
        user = await auth_service.register_user(
            phone=req.phone,
            password=req.password,
            nickname=req.nickname,
        )
        return {
            "message": "注册成功",
            "user": {
                "id": user.id,
                "role": user.role.value,
                "phone": req.phone,
                "nickname": user.nickname,
            },
        }
    except ValueError as e:
        from fastapi import HTTPException

        if "已注册" in str(e):
            raise HTTPException(status_code=409, detail={"message": str(e)})
        raise HTTPException(status_code=422, detail={"message": str(e)})


@router.post("/refresh", response_model=RefreshResponse, summary="刷新 Access Token")
async def refresh_token(
    req: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    使用 Refresh Token 刷新 Access Token
    实现 Refresh Token Rotation：每次刷新生成新的 Refresh Token，旧的立即失效
    """
    auth_service = AuthService(db)
    new_access_token, new_refresh_token, expires_at = await auth_service.refresh_tokens(
        req.refresh_token,
        device_fingerprint=req.device_fingerprint,
    )

    import datetime

    expires_in = int((expires_at.timestamp() - datetime.datetime.now(timezone.utc).timestamp()))

    return RefreshResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=max(0, expires_in),
    )


@router.post("/logout", response_model=LogoutResponse, summary="登出")
async def logout(
    current: tuple[User, dict] = Depends(get_current_user_with_payload),
    db: AsyncSession = Depends(get_db),
):
    """
    用户登出，吊销当前 Token
    """
    current_user, payload = current
    jti = payload.get("jti")
    if not jti:
        from app.core.exceptions import InvalidTokenError

        raise InvalidTokenError("Token 缺少 jti")
    auth_service = AuthService(db)
    await auth_service.logout(current_user.id, jti)

    return LogoutResponse(message="登出成功", success=True)


@router.get("/me", summary="获取当前用户信息")
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户的基本信息"""
    return {
        "id": current_user.id,
        "role": current_user.role.value,
        "status": current_user.status.value,
        "is_verified": current_user.is_verified,
        "nickname": current_user.nickname,
        "pseudonym_id": current_user.pseudonym_id,
    }

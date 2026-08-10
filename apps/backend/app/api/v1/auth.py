"""私人用户认证 API：注册、登录、令牌刷新和登出。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.identity import (
    ChangePasswordResultV1,
    ChangePasswordV1,
    IssueRecoveryKitV1,
    RecoverPasswordResultV1,
    RecoverPasswordV1,
    RecoveryKitResultV1,
    RecoveryStatusV1,
    RevokeOtherSessionsV1,
    RevokeSessionV1,
    SessionCommandResultV1,
    SessionListV1,
)
from app.core.database import get_db
from app.models.user import User
from app.services.auth.auth_service import AuthService
from app.services.auth.dependencies import get_current_user, get_current_user_with_payload
from app.services.auth.token_service import TokenService

router = APIRouter(prefix="/auth", tags=["认证"])


# ========== 请求/响应模型 ==========


class PhoneLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="中国大陆手机号")
    password: str = Field(..., min_length=1, max_length=128, description="密码")
    device_fingerprint: Optional[str] = Field(None, min_length=8, max_length=512)


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="中国大陆手机号")
    password: str = Field(..., min_length=15, max_length=128, description="密码")
    nickname: Optional[str] = Field(None, max_length=64, description="昵称（选填）")


class RefreshTokenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str = Field(..., min_length=32, description="刷新令牌")
    device_fingerprint: Optional[str] = Field(None, min_length=8, max_length=512)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # 秒
    session_version: int | None = None
    user: dict


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    session_version: int


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
    access_payload = TokenService.decode_token(access_token, token_type="access")

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=max(0, expires_in),
        session_version=access_payload["sv"],
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
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    新用户注册

    - **phone**: 手机号
    - **password**: 密码（15～128 个 Unicode 字符）
    - **nickname**: 昵称（选填）
    """
    auth_service = AuthService(db)
    try:
        user, recovery_secret, recovery = await auth_service.register_user(
            phone=req.phone,
            password=req.password,
            nickname=req.nickname,
        )
        response.headers["Cache-Control"] = "private, no-store"
        return {
            "message": "注册成功",
            "user": {
                "id": user.id,
                "role": user.role.value,
                "phone": req.phone,
                "nickname": user.nickname,
            },
            "recovery_kit": RecoveryKitResultV1(
                issued=True,
                replayed=False,
                recovery_secret=recovery_secret,
                credential_version=recovery.version,
                created_at=auth_service._as_utc(recovery.created_at),
            ).model_dump(mode="json"),
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
        session_version=TokenService.decode_token(new_access_token, token_type="access")["sv"],
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
    session_id = payload.get("sid")
    if not session_id:
        from app.core.exceptions import InvalidTokenError

        raise InvalidTokenError("Token 缺少 sid")
    auth_service = AuthService(db)
    await auth_service.logout(current_user.id, session_id)

    return LogoutResponse(message="登出成功", success=True)


@router.post("/heartbeat", summary="心跳 - 保持会话活跃")
async def heartbeat(
    current: tuple[User, dict] = Depends(get_current_user_with_payload),
    db: AsyncSession = Depends(get_db),
):
    """
    前端定期调用以更新会话 last_seen_at，防止会话因空闲而超时。
    浏览器关闭后心跳停止，超过空闲阈值后会话自动不计入并发上限。
    """
    current_user, payload = current
    session_id = payload.get("sid")
    if not session_id:
        from app.core.exceptions import InvalidTokenError

        raise InvalidTokenError("Token 缺少 sid")
    auth_service = AuthService(db)
    await auth_service.heartbeat(current_user.id, session_id)
    return {"ok": True}


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


@router.post(
    "/password/change",
    response_model=ChangePasswordResultV1,
    summary="修改密码并轮换当前会话",
)
async def change_password(
    req: ChangePasswordV1,
    response: Response,
    current: tuple[User, dict] = Depends(get_current_user_with_payload),
    db: AsyncSession = Depends(get_db),
):
    response.headers["Cache-Control"] = "private, no-store"
    user, payload = current
    return await AuthService(db).change_password(user=user, payload=payload, command=req)


@router.get("/sessions", response_model=SessionListV1, summary="列出当前账号会话")
async def list_sessions(
    response: Response,
    current: tuple[User, dict] = Depends(get_current_user_with_payload),
    db: AsyncSession = Depends(get_db),
):
    response.headers["Cache-Control"] = "private, no-store"
    user, payload = current
    return await AuthService(db).list_sessions(
        user_id=user.id,
        current_session_id=payload["sid"],
    )


@router.post(
    "/sessions/{session_id}/revoke",
    response_model=SessionCommandResultV1,
    summary="撤销一个账号会话",
)
async def revoke_session(
    session_id: str,
    req: RevokeSessionV1,
    response: Response,
    current: tuple[User, dict] = Depends(get_current_user_with_payload),
    db: AsyncSession = Depends(get_db),
):
    response.headers["Cache-Control"] = "private, no-store"
    user, _ = current
    return await AuthService(db).revoke_session(
        user_id=user.id,
        target_session_id=session_id,
        idempotency_key=req.idempotency_key,
    )


@router.post(
    "/sessions/revoke-others",
    response_model=SessionCommandResultV1,
    summary="撤销当前会话以外的所有会话",
)
async def revoke_other_sessions(
    req: RevokeOtherSessionsV1,
    response: Response,
    current: tuple[User, dict] = Depends(get_current_user_with_payload),
    db: AsyncSession = Depends(get_db),
):
    response.headers["Cache-Control"] = "private, no-store"
    user, payload = current
    return await AuthService(db).revoke_other_sessions(
        user_id=user.id,
        current_session_id=payload["sid"],
        idempotency_key=req.idempotency_key,
    )


@router.get(
    "/recovery/status",
    response_model=RecoveryStatusV1,
    summary="读取恢复套件状态",
)
async def recovery_status(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    response.headers["Cache-Control"] = "private, no-store"
    return await AuthService(db).recovery_status(user_id=current_user.id)


@router.post(
    "/recovery/issue",
    response_model=RecoveryKitResultV1,
    summary="创建或轮换离线恢复套件",
)
async def issue_recovery_kit(
    req: IssueRecoveryKitV1,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    response.headers["Cache-Control"] = "private, no-store"
    return await AuthService(db).issue_recovery_kit(user=current_user, command=req)


@router.post(
    "/recovery/password",
    response_model=RecoverPasswordResultV1,
    summary="使用离线恢复套件重设密码",
)
async def recover_password(
    req: RecoverPasswordV1,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    response.headers["Cache-Control"] = "private, no-store"
    return await AuthService(db).recover_password(req)

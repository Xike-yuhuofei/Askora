"""UI workspace read endpoints (transport adapter only)."""

from __future__ import annotations

from zoneinfo import ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.workspace import TodayWorkspaceResponseV1
from app.core.database import get_db
from app.core.exceptions import ValidationInputError
from app.models.user import User
from app.queries.workspace import WorkspaceTodayQueryService
from app.services.auth.dependencies import get_current_user

router = APIRouter(prefix="/workspace", tags=["学习工作区"])


@router.get("/today", response_model=TodayWorkspaceResponseV1, summary="获取今日学习工作区")
async def get_today_workspace(
    request: Request,
    response: Response,
    timezone_name: str = Query("Asia/Shanghai", alias="timezone", min_length=1, max_length=64),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TodayWorkspaceResponseV1:
    """Return a current-user-scoped, read-only UI aggregation."""
    try:
        result = await WorkspaceTodayQueryService(db).get_today(
            current_user,
            timezone_name=timezone_name,
            correlation_id=getattr(request.state, "request_id", "unknown"),
        )
    except ZoneInfoNotFoundError:
        raise ValidationInputError("timezone 必须是有效的 IANA 时区")
    response.headers["Cache-Control"] = "private, no-store"
    return result

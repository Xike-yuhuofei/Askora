"""UI workspace read endpoints (transport adapter only)."""

from __future__ import annotations

from uuid import UUID
from zoneinfo import ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.workspace import (
    KnowledgeMapResponseV1,
    LibraryWorkspaceResponseV1,
    TodayWorkspaceResponseV1,
)
from app.core.database import get_db
from app.core.exceptions import ValidationInputError
from app.models.user import User
from app.queries.library import WorkspaceLibraryQueryService
from app.queries.workspace import WorkspaceTodayQueryService
from app.services.auth.dependencies import get_current_user

router = APIRouter(prefix="/workspace", tags=["学习工作区"])


@router.get("/library", response_model=LibraryWorkspaceResponseV1, summary="获取资料库")
async def get_library_workspace(
    request: Request,
    response: Response,
    status: str | None = Query(None, max_length=20),
    subject: str | None = Query(None, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LibraryWorkspaceResponseV1:
    result = await WorkspaceLibraryQueryService(db).list_library(
        current_user,
        status=status,
        subject=subject,
        page=page,
        page_size=page_size,
        correlation_id=getattr(request.state, "request_id", "unknown"),
    )
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.get(
    "/knowledge-map",
    response_model=KnowledgeMapResponseV1,
    summary="获取范围化知识地图",
)
async def get_knowledge_map(
    request: Request,
    response: Response,
    document_id: UUID = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeMapResponseV1:
    result = await WorkspaceLibraryQueryService(db).get_knowledge_map(
        current_user,
        document_id=document_id,
        correlation_id=getattr(request.state, "request_id", "unknown"),
    )
    response.headers["Cache-Control"] = "private, no-store"
    return result


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

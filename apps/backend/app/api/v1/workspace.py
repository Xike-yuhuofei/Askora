"""UI workspace read endpoints (transport adapter only)."""

from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5
from zoneinfo import ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.activity_lifecycle import (
    ActivityLifecycleResponseV1,
    CompleteLearningActivityV1,
    StartLearningActivityV1,
)
from app.contracts.workspace import (
    EvidenceProfileResponseV1,
    GoalListResponseV1,
    KnowledgeMapResponseV1,
    LearningPathResponseV1,
    LibraryWorkspaceResponseV1,
    TodayWorkspaceResponseV1,
)
from app.core.database import get_db
from app.core.exceptions import BusinessError, ValidationInputError
from app.models.user import User
from app.models.workspace import Workspace
from app.queries.library import WorkspaceLibraryQueryService
from app.queries.workspace import WorkspaceTodayQueryService
from app.services.activity_lifecycle import ActivityLifecycleService
from app.services.owner.dependencies import get_current_owner_projection
from app.services.workspace.dependencies import get_default_workspace

router = APIRouter(prefix="/workspace", tags=["学习工作区"])


def _correlation_id(request: Request) -> UUID:
    raw = str(getattr(request.state, "request_id", "unknown"))
    try:
        return UUID(raw)
    except ValueError:
        return uuid5(NAMESPACE_URL, f"askora:request:{raw}")


def _require_activity_match(path_id: UUID, body_id: UUID) -> None:
    if path_id != body_id:
        raise BusinessError(
            message="活动路径与命令不一致",
            error_code="ACTIVITY_STALE_OR_SUPERSEDED",
            status_code=409,
        )


@router.get(
    "/activities/{activity_id}",
    response_model=ActivityLifecycleResponseV1,
    summary="获取 canonical 学习活动状态",
)
async def get_activity_lifecycle(
    activity_id: UUID,
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
) -> ActivityLifecycleResponseV1:
    result = await ActivityLifecycleService(db).get(
        user=current_user,
        activity_id=activity_id,
        correlation_id=_correlation_id(request),
    )
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.post(
    "/activities/{activity_id}/start",
    response_model=ActivityLifecycleResponseV1,
    summary="开始 canonical 学习活动",
)
async def start_activity_lifecycle(
    activity_id: UUID,
    body: StartLearningActivityV1,
    request: Request,
    current_user: User = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
) -> ActivityLifecycleResponseV1:
    _require_activity_match(activity_id, body.activity_id)
    return await ActivityLifecycleService(db).start(
        user=current_user,
        command=body,
        correlation_id=_correlation_id(request),
    )


@router.post(
    "/activities/{activity_id}/complete",
    response_model=ActivityLifecycleResponseV1,
    summary="完成 canonical 学习活动",
)
async def complete_activity_lifecycle(
    activity_id: UUID,
    body: CompleteLearningActivityV1,
    request: Request,
    current_user: User = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
) -> ActivityLifecycleResponseV1:
    _require_activity_match(activity_id, body.activity_id)
    return await ActivityLifecycleService(db).complete(
        user=current_user,
        command=body,
        correlation_id=_correlation_id(request),
    )


@router.get("/goals", response_model=GoalListResponseV1, summary="获取学习目标")
async def get_goals_workspace(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
) -> GoalListResponseV1:
    result = await WorkspaceTodayQueryService(db).list_goals(
        current_user,
        correlation_id=getattr(request.state, "request_id", "unknown"),
    )
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.get("/path", response_model=LearningPathResponseV1, summary="获取学习路径")
async def get_path_workspace(
    request: Request,
    response: Response,
    goal_id: UUID | None = Query(None),
    current_user: User = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
) -> LearningPathResponseV1:
    result = await WorkspaceTodayQueryService(db).get_path(
        current_user,
        goal_id=goal_id,
        correlation_id=getattr(request.state, "request_id", "unknown"),
    )
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.get("/evidence", response_model=EvidenceProfileResponseV1, summary="获取学习证据")
async def get_evidence_workspace(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
) -> EvidenceProfileResponseV1:
    result = await WorkspaceTodayQueryService(db).get_evidence(
        current_user,
        correlation_id=getattr(request.state, "request_id", "unknown"),
    )
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.get("/library", response_model=LibraryWorkspaceResponseV1, summary="获取资料库")
async def get_library_workspace(
    request: Request,
    response: Response,
    status: str | None = Query(None, max_length=20),
    subject: str | None = Query(None, max_length=100),
    q: str | None = Query(None, max_length=500),
    document_id: UUID | None = Query(None),
    tag_id: UUID | None = Query(None),
    collection_id: UUID | None = Query(None),
    archived: bool = Query(False),
    sort: str = Query("created_desc", max_length=30),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    default_workspace: Workspace = Depends(get_default_workspace),
    current_user: User = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
) -> LibraryWorkspaceResponseV1:
    # EXEC063-AC-001/AC-008: the legacy UI library route resolves the canonical
    # default Workspace only; it never aggregates across Workspaces.
    result = await WorkspaceLibraryQueryService(db).list_library(
        current_user,
        workspace_id=default_workspace.workspace_id,
        status=status,
        subject=subject,
        query_text=q,
        document_id=document_id,
        tag_id=tag_id,
        collection_id=collection_id,
        archived=archived,
        sort=sort,
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
    default_workspace: Workspace = Depends(get_default_workspace),
    current_user: User = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeMapResponseV1:
    result = await WorkspaceLibraryQueryService(db).get_knowledge_map(
        current_user,
        workspace_id=default_workspace.workspace_id,
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
    current_user: User = Depends(get_current_owner_projection),
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

"""P1-07 recovery query and command transport adapter."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.recovery import (
    RecoveryCommandV1,
    RecoveryIssueListResponseV1,
    RecoveryResultV1,
)
from app.core.database import get_db
from app.models.user import User
from app.queries.recovery import RecoveryQueryService
from app.services.auth.dependencies import get_current_user
from app.services.recovery import RecoveryActionService

router = APIRouter(prefix="/recovery", tags=["错误恢复"])


@router.get("/issues", response_model=RecoveryIssueListResponseV1)
async def list_recovery_issues(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RecoveryIssueListResponseV1:
    result = await RecoveryQueryService(db).list_issues(
        current_user,
        correlation_id=getattr(request.state, "request_id", "unknown"),
    )
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.post("/actions", response_model=RecoveryResultV1)
async def execute_recovery_action(
    command: RecoveryCommandV1,
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RecoveryResultV1:
    result = await RecoveryActionService(db).execute(
        current_user,
        command,
        correlation_id=getattr(request.state, "request_id", "unknown"),
    )
    response.headers["Cache-Control"] = "private, no-store"
    return result

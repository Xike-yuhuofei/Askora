"""Authenticated current-user data export endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.background import BackgroundTask

from app.contracts.data_control import ExportScope, UserExportReadyV1
from app.core.database import get_db
from app.core.exceptions import AppError
from app.data_control.export import UserDataExporter, export_registry
from app.data_control.recovery import RecoveryError
from app.models.user import User
from app.services.auth.dependencies import get_current_user

router = APIRouter(prefix="/data-control", tags=["数据控制"])


class CreateUserExportRequest(BaseModel):
    scopes: tuple[ExportScope, ...] = Field(min_length=1, max_length=4)
    include_document_originals: bool = False


@router.post("/exports", response_model=UserExportReadyV1)
async def create_user_export(
    request: CreateUserExportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserExportReadyV1:
    try:
        return await UserDataExporter(db).create(
            user=current_user,
            scopes=request.scopes,
            include_document_originals=request.include_document_originals,
        )
    except RecoveryError as exc:
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=exc.code.value,
            message=exc.message,
        )


@router.get("/exports/{export_id}")
async def download_user_export(
    export_id: UUID,
    token: str = Header(
        min_length=32,
        max_length=200,
        alias="X-Askora-Export-Token",
    ),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    try:
        artifact_path = export_registry.consume(export_id, current_user.id, token)
    except RecoveryError as exc:
        raise AppError(
            status_code=status.HTTP_410_GONE,
            error_code=exc.code.value,
            message=exc.message,
        )
    return FileResponse(
        artifact_path,
        media_type="application/zip",
        filename=f"Askora-user-data-{export_id}.zip",
        background=BackgroundTask(export_registry.delete, export_id, artifact_path),
    )

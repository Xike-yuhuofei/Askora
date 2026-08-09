"""Authenticated current-user data export endpoints."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, Header, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.background import BackgroundTask

from app.contracts.data_control import (
    ErasurePreviewV1,
    ErasureReportV1,
    ErasureScope,
    ExportScope,
    UserExportReadyV1,
)
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AppError
from app.data_control.erasure import ErasureCoordinator
from app.data_control.export import UserDataExporter, export_registry
from app.data_control.recovery import RecoveryError
from app.models.user import User
from app.services.auth.dependencies import get_current_user

router = APIRouter(prefix="/data-control", tags=["数据控制"])


class CreateUserExportRequest(BaseModel):
    scopes: tuple[ExportScope, ...] = Field(min_length=1, max_length=4)
    include_document_originals: bool = False


class CreateErasurePreviewRequest(BaseModel):
    scope: ErasureScope
    target_ref: str | None = Field(default=None, min_length=1, max_length=255)


class ConfirmErasureRequest(BaseModel):
    preview_id: UUID
    confirmation_token: str = Field(min_length=32, max_length=200)
    confirmation_phrase: str = Field(min_length=1, max_length=300)
    idempotency_key: str = Field(min_length=16, max_length=200)


def _erasure_coordinator(db: AsyncSession) -> ErasureCoordinator:
    documents_dir = Path(settings.local_storage_base_path).resolve()
    return ErasureCoordinator(
        db,
        documents_dir=documents_dir,
        fail_closed_marker=documents_dir.parent / "recovery" / "erasure-pending.json",
    )


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


@router.post("/erasures/preview", response_model=ErasurePreviewV1)
async def create_erasure_preview(
    request: CreateErasurePreviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ErasurePreviewV1:
    try:
        return await _erasure_coordinator(db).preview(
            user=current_user,
            scope=request.scope,
            target_ref=request.target_ref,
        )
    except RecoveryError as exc:
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=exc.code.value,
            message=exc.message,
        )


@router.post("/erasures/confirm", response_model=ErasureReportV1)
async def confirm_erasure(
    request: ConfirmErasureRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ErasureReportV1:
    try:
        return await _erasure_coordinator(db).confirm(
            user=current_user,
            preview_id=request.preview_id,
            token=request.confirmation_token,
            confirmation_phrase=request.confirmation_phrase,
            idempotency_key=request.idempotency_key,
        )
    except RecoveryError as exc:
        raise AppError(
            status_code=(
                status.HTTP_410_GONE
                if exc.code.value == "DATA_ERASURE_PREVIEW_EXPIRED"
                else status.HTTP_409_CONFLICT
            ),
            error_code=exc.code.value,
            message=exc.message,
        )

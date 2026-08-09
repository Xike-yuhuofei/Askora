"""Account deletion API with ordinary-session and deletion-control separation."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, Header, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.privacy import (
    AccountDeletionAcceptedV1,
    AccountDeletionCancelResultV1,
    AccountDeletionCancelV1,
    AccountDeletionPreviewV1,
    AccountDeletionRequestV1,
    AccountDeletionRetryV1,
    AccountDeletionStatusV1,
)
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import InvalidTokenError
from app.models.user import User
from app.services.auth.dependencies import get_current_user
from app.services.privacy.account_deletion import AccountDeletionService

router = APIRouter(prefix="/account/deletion", tags=["账号删除"])


def _service(db: AsyncSession) -> AccountDeletionService:
    return AccountDeletionService(
        db,
        grace=timedelta(hours=settings.account_deletion_grace_hours),
        storage_base_path=Path(settings.local_storage_base_path),
        restore_barrier_path=Path(settings.privacy_restore_barrier_path),
    )


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "private, no-store"


def _control_token(value: str | None) -> str:
    if not value:
        raise InvalidTokenError("缺少删除控制令牌")
    return value


@router.post("/preview", response_model=AccountDeletionPreviewV1)
async def preview_account_deletion(
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _no_store(response)
    return await _service(db).create_preview(user=user)


@router.post("/request", response_model=AccountDeletionAcceptedV1)
async def request_account_deletion(
    command: AccountDeletionRequestV1,
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _no_store(response)
    return await _service(db).request_deletion(user=user, command=command)


@router.get("/status", response_model=AccountDeletionStatusV1)
async def account_deletion_status(
    response: Response,
    x_deletion_control: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    _no_store(response)
    return await _service(db).get_status(deletion_control_token=_control_token(x_deletion_control))


@router.post("/cancel", response_model=AccountDeletionCancelResultV1)
async def cancel_account_deletion(
    command: AccountDeletionCancelV1,
    response: Response,
    x_deletion_control: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    _no_store(response)
    return await _service(db).cancel_deletion(
        deletion_control_token=_control_token(x_deletion_control), command=command
    )


@router.post("/retry", response_model=AccountDeletionStatusV1)
async def retry_account_deletion(
    command: AccountDeletionRetryV1,
    response: Response,
    x_deletion_control: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    _no_store(response)
    return await _service(db).retry_deletion(
        deletion_control_token=_control_token(x_deletion_control),
        command=command,
        max_attempts=settings.account_deletion_max_attempts,
    )

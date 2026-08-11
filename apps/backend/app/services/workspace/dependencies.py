"""FastAPI dependency resolution for the default Workspace.

Legacy owner-global endpoints that must be cut over resolve the canonical
default Workspace instead of creating owner-global records. Reading across
Workspaces is not allowed; only the single default Workspace is exposed.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import BusinessError
from app.models.workspace import Workspace
from app.services.local_identity import (
    LocalOwnerContext,
    LocalOwnerError,
    LocalOwnerMigrationFailedError,
    ensure_local_owner,
    get_local_owner_context,
)
from app.services.owner.dependencies import get_current_owner
from app.services.workspace.repository import WorkspaceRepository, WorkspaceSelectionRepository


async def get_default_workspace(
    db: AsyncSession = Depends(get_db),
) -> Workspace:
    """Resolve exactly one active default Workspace for the LocalOwner.

    In test/development environments a missing LocalOwner/Workspace is
    bootstrapped automatically.
    """
    try:
        ctx = await get_local_owner_context(db)
    except LocalOwnerError:
        if not (settings.is_development or settings.app_env.value == "test"):
            raise
        ctx = await ensure_local_owner(db)
    repo = WorkspaceRepository(db)
    ws = await repo.get_default(ctx.canonical_owner_id)
    if ws is None:
        if settings.is_development or settings.app_env.value == "test":
            ws = await repo.create_default_if_absent(ctx.canonical_owner_id)
        else:
            raise LocalOwnerMigrationFailedError(
                "default Workspace is missing for the LocalOwner",
                detail={"owner_id": ctx.canonical_owner_id},
            )
    return ws


async def get_current_workspace(
    db: AsyncSession = Depends(get_db),
    owner: LocalOwnerContext = Depends(get_current_owner),
) -> Workspace:
    """CWSP-041 side-effect-free current selection resolution."""
    selection = await WorkspaceSelectionRepository(db).get(owner.canonical_owner_id)
    if selection is None:
        raise BusinessError(
            message="当前课程尚未选择",
            error_code="WORKSPACE_SELECTION_MISSING",
            status_code=404,
            category="not_found",
        )
    workspace = await WorkspaceRepository(db).get_for_owner(
        owner.canonical_owner_id, selection.current_workspace_id
    )
    if workspace is None or workspace.lifecycle != "active":
        raise BusinessError(
            message="课程选择状态不可用",
            error_code="WORKSPACE_INTEGRITY_FAILED",
            status_code=500,
            category="internal",
        )
    return workspace

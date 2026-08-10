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
from app.models.workspace import Workspace
from app.services.local_identity import (
    LocalOwnerError,
    LocalOwnerMigrationFailedError,
    ensure_local_owner,
    get_local_owner_context,
)
from app.services.workspace.repository import WorkspaceRepository


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

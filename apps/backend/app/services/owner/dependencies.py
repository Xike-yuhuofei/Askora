"""LocalOwner resolution dependencies - FastAPI dependency injection.

EXEC-048: Migrated to LocalOwnerContext. No JWT / AuthSession runtime exists.
The single-user local Askora instance resolves ownership via LocalOwnerContext.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.services.local_identity import (
    LocalOwnerAmbiguousError,
    LocalOwnerContext,
    LocalOwnerError,
    LocalOwnerMigrationFailedError,
    _ensure_fresh_local_owner,
    ensure_local_owner,
    get_local_owner_context,
)


async def get_current_owner(
    db: AsyncSession = Depends(get_db),
) -> LocalOwnerContext:
    """Get LocalOwnerContext for no-auth loopback production.

    EXEC-048: Replaces get_current_user for production API endpoints.
    No JWT/session validation needed - single-user local instance.

    In test/development environments, auto-bootstraps LocalOwner if missing.
    When legacy subjects are ambiguous, falls back to a fresh owner.
    """
    try:
        return await get_local_owner_context(db)
    except LocalOwnerError:
        if not (settings.is_development or settings.app_env.value == "test"):
            raise
        try:
            return await ensure_local_owner(db)
        except LocalOwnerAmbiguousError:
            return await _ensure_fresh_local_owner(db)


async def get_current_owner_projection(
    db: AsyncSession = Depends(get_db),
) -> User:
    """Return the LID-013 ORM compatibility row for legacy service/FK boundaries.

    The projection is expunged from the session so that callers can safely
    read identity attributes after a rollback without triggering lazy-load
    greenlet errors. LocalOwner remains the only durable identity truth;
    this compatibility row has no login credential or PII.
    """
    ctx = await get_current_owner(db)
    projection_id = ctx.legacy_user_id or ctx.canonical_owner_id
    projection = await db.get(User, projection_id)
    if projection is None:
        raise LocalOwnerMigrationFailedError(
            "LocalOwner compatibility learner row is missing",
            detail={"projection_user_id": projection_id},
        )
    db.expunge(projection)
    return projection

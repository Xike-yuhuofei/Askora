"""Fail-closed Workspace resolution for learner/assessment writers (XIK-177).

Requirement EXEC-062 #10: when a Workspace cannot be resolved, the caller must
fail BEFORE creating evidence / TeachingAction. This helper centralises the
canonical default-Workspace resolution used by application-layer services that
write LearnerEvidence / MasteryEstimate / LearnerState / ReviewSchedule.

The owner is the canonical LocalOwner id produced by ``canonical_user_id`` in
the normal single-owner runtime; the default Workspace is the deterministic
migration target for legacy owner-global learner data. The helper never returns
``None``: it either returns an exact Workspace id or raises
:class:`WorkspaceResolutionError` (fail-closed).
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.workspace.repository import WorkspaceRepository


class WorkspaceResolutionError(RuntimeError):
    """Raised when no exact Workspace can be resolved (fail-closed)."""


async def resolve_workspace_id(db: AsyncSession, owner_id: UUID) -> UUID:
    """Resolve exactly one active default Workspace id for a canonical owner.

    Fails closed: if no Workspace can be resolved / created, raises
    :class:`WorkspaceResolutionError` so no owner-global learner record is ever
    written by an active writer for an unresolved scope.
    """
    repo = WorkspaceRepository(db)
    ws = await repo.get_default(str(owner_id))
    if ws is not None:
        return UUID(ws.workspace_id)
    created = await repo.create_default_if_absent(str(owner_id))
    return UUID(created.workspace_id)

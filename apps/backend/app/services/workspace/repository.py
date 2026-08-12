"""SQLAlchemy repositories for the Platform Workspace / Project / Session registry.

Ownership (ADR-0016 / WSP-001..003):
- :class:`WorkspaceRepository`  -> Platform Workspace Registry
- :class:`ProjectRepository`    -> Platform Workspace / Product Organization
- :class:`SessionRepository`    -> Platform Learning Session Registry

These repositories persist scope/lifecycle/identity metadata only. They never
write Material content, Goal semantics, LearnerState, TeachingAction,
AssessmentResult or ReviewSchedule truth.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import (
    LearningProject,
    LearningSession,
    LearningSessionMaterial,
    LearningSessionStatus,
    ProjectMaterial,
    ProjectStatus,
    SourceFile,
    Workspace,
    WorkspaceCommandReceipt,
    WorkspaceLifecycle,
    WorkspaceSelection,
)

DEFAULT_WORKSPACE_NAME = "默认工作区"


class WorkspaceError(RuntimeError):
    """Base error for Workspace / Project / Session domain operations."""


class WorkspaceNotFoundError(WorkspaceError):
    pass


class WorkspaceSelectionVersionConflictError(WorkspaceError):
    pass


class WorkspaceIdempotencyConflictError(WorkspaceError):
    pass


class CrossWorkspaceReferenceError(WorkspaceError):
    """A ref would cross a Workspace boundary (WSP-030/031/032)."""


class DistinctInsertUnsupportedError(WorkspaceError):
    pass


def _insert_on_conflict_nothing(table: Any, values: dict[str, Any], dialect: str):
    """``INSERT ... ON CONFLICT DO NOTHING`` (no conflict target).

    SQLite's partial unique index (``uq_workspaces_one_active_default``) cannot
    be used as an ``ON CONFLICT (owner_id)`` target because partial indexes
    require a matching WHERE clause in the conflict target. A target-less
    ``ON CONFLICT DO NOTHING`` intercepts any uniqueness conflict, including on
    partial indexes, which gives us concurrency-safe idempotent bootstrap.
    """
    dialect_stmt: Any
    if dialect == "postgresql":
        dialect_stmt = postgresql_insert(table).values(**values)
    elif dialect == "sqlite":
        dialect_stmt = sqlite_insert(table).values(**values)
    else:
        raise DistinctInsertUnsupportedError(f"Unsupported workspace dialect: {dialect}")
    return dialect_stmt.on_conflict_do_nothing()


class WorkspaceRepository:
    """Owns the ``workspaces`` table and default-Workspace resolution.

    The default-Workspace write path uses ``INSERT ... ON CONFLICT DO NOTHING``
    on the partial unique index ``uq_workspaces_one_active_default`` so that
    concurrent bootstrap can never yield two active default Workspaces.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, workspace_id: str) -> Workspace | None:
        return await self.db.get(Workspace, workspace_id)

    async def get_default(self, owner_id: str) -> Workspace | None:
        result = await self.db.execute(
            select(Workspace).where(
                Workspace.owner_id == owner_id,
                Workspace.is_default.is_(True),
                Workspace.lifecycle == WorkspaceLifecycle.ACTIVE,
            )
        )
        return result.scalars().first()

    async def list_for_owner(self, owner_id: str) -> list[Workspace]:
        result = await self.db.execute(
            select(Workspace).where(Workspace.owner_id == owner_id).order_by(Workspace.created_at)
        )
        return list(result.scalars().all())

    async def list_active_for_owner(self, owner_id: str) -> list[Workspace]:
        result = await self.db.execute(
            select(Workspace)
            .where(
                Workspace.owner_id == owner_id,
                Workspace.lifecycle == WorkspaceLifecycle.ACTIVE,
            )
            .order_by(Workspace.created_at, Workspace.workspace_id)
        )
        return list(result.scalars().all())

    async def get_for_owner(self, owner_id: str, workspace_id: str) -> Workspace | None:
        return await self.db.scalar(
            select(Workspace).where(
                Workspace.owner_id == owner_id,
                Workspace.workspace_id == workspace_id,
            )
        )

    async def create(self, *, owner_id: str, display_name: str, is_default: bool) -> Workspace:
        workspace = Workspace(
            workspace_id=str(uuid4()),
            owner_id=owner_id,
            version=1,
            display_name=display_name,
            is_default=is_default,
            lifecycle=WorkspaceLifecycle.ACTIVE,
        )
        self.db.add(workspace)
        await self.db.flush()
        return workspace

    async def count_for_owner(self, owner_id: str) -> int:
        result = await self.db.execute(
            select(func.count(Workspace.workspace_id)).where(Workspace.owner_id == owner_id)
        )
        return int(result.scalar_one())

    async def count_active_for_owner(self, owner_id: str) -> int:
        result = await self.db.execute(
            select(func.count(Workspace.workspace_id)).where(
                Workspace.owner_id == owner_id,
                Workspace.lifecycle == WorkspaceLifecycle.ACTIVE,
            )
        )
        return int(result.scalar_one())

    async def create_default_if_absent(self, owner_id: str) -> Workspace:
        """Create the deterministic active default Workspace, or return the existing one.

        Idempotent and concurrent-safe: conflicts on the partial unique index
        ``uq_workspaces_one_active_default`` are swallowed.
        """
        existing = await self.get_default(owner_id)
        if existing is not None:
            return existing

        now = datetime.now(timezone.utc)
        values = {
            "workspace_id": str(uuid4()),
            "owner_id": owner_id,
            "version": 1,
            "display_name": DEFAULT_WORKSPACE_NAME,
            "is_default": True,
            "lifecycle": WorkspaceLifecycle.ACTIVE,
            "created_at": now,
            "updated_at": now,
        }
        dialect = self.db.get_bind().dialect.name
        stmt = _insert_on_conflict_nothing(Workspace, values, dialect)
        await self.db.execute(stmt)
        await self.db.flush()

        resolved = await self.get_default(owner_id)
        if resolved is None:
            raise WorkspaceError("failed to resolve a default Workspace after bootstrap")
        return resolved


class WorkspaceSelectionRepository:
    """CWSP-010/012 persistence for current selection and command receipts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, owner_id: str, *, for_update: bool = False) -> WorkspaceSelection | None:
        statement = select(WorkspaceSelection).where(WorkspaceSelection.owner_id == owner_id)
        if for_update:
            statement = statement.with_for_update()
        return await self.db.scalar(statement)

    async def set(
        self,
        *,
        owner_id: str,
        current_workspace_id: str,
        reason: str,
        correlation_id: str,
        expected_version: int | None,
    ) -> WorkspaceSelection:
        values = {
            "owner_id": owner_id,
            "version": 1,
            "current_workspace_id": current_workspace_id,
            "previous_workspace_id": None,
            "reason": reason,
            "correlation_id": correlation_id,
        }
        if expected_version is None:
            dialect = self.db.get_bind().dialect.name
            statement = _insert_on_conflict_nothing(WorkspaceSelection, values, dialect)
            result = await self.db.execute(statement)
        else:
            result = await self.db.execute(
                update(WorkspaceSelection)
                .where(
                    WorkspaceSelection.owner_id == owner_id,
                    WorkspaceSelection.version == expected_version,
                )
                .values(
                    version=expected_version + 1,
                    previous_workspace_id=WorkspaceSelection.current_workspace_id,
                    current_workspace_id=current_workspace_id,
                    reason=reason,
                    correlation_id=correlation_id,
                    updated_at=datetime.now(timezone.utc),
                )
            )
        if not isinstance(result, CursorResult) or result.rowcount != 1:
            raise WorkspaceSelectionVersionConflictError("workspace selection version conflict")
        await self.db.flush()
        selection = await self.get(owner_id)
        if selection is None:
            raise WorkspaceError("workspace selection disappeared after successful CAS")
        return selection

    async def get_receipt(
        self, *, owner_id: str, command_type: str, idempotency_key: str
    ) -> WorkspaceCommandReceipt | None:
        return await self.db.scalar(
            select(WorkspaceCommandReceipt).where(
                WorkspaceCommandReceipt.owner_id == owner_id,
                WorkspaceCommandReceipt.command_type == command_type,
                WorkspaceCommandReceipt.idempotency_key == idempotency_key,
            )
        )

    async def append_receipt(
        self,
        *,
        owner_id: str,
        command_type: str,
        idempotency_key: str,
        command_digest: str,
        response_payload: dict,
    ) -> WorkspaceCommandReceipt:
        values = {
            "receipt_id": str(uuid4()),
            "owner_id": owner_id,
            "command_type": command_type,
            "idempotency_key": idempotency_key,
            "command_digest": command_digest,
            "response_payload": response_payload,
        }
        dialect = self.db.get_bind().dialect.name
        await self.db.execute(_insert_on_conflict_nothing(WorkspaceCommandReceipt, values, dialect))
        await self.db.flush()
        receipt = await self.get_receipt(
            owner_id=owner_id,
            command_type=command_type,
            idempotency_key=idempotency_key,
        )
        if receipt is None:
            raise WorkspaceError("workspace command receipt disappeared after append")
        if receipt.command_digest != command_digest:
            raise WorkspaceIdempotencyConflictError(
                "workspace idempotency key was reused with another command digest"
            )
        return receipt


class ProjectRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, project_id: str) -> LearningProject | None:
        return await self.db.get(LearningProject, project_id)

    async def create(
        self,
        *,
        workspace_id: str,
        title: str,
        status: str = ProjectStatus.ACTIVE,
    ) -> LearningProject:
        project = LearningProject(
            project_id=str(uuid4()),
            workspace_id=workspace_id,
            version=1,
            title=title,
            status=status,
        )
        self.db.add(project)
        await self.db.flush()
        return project

    async def list_for_workspace(self, workspace_id: str) -> list[LearningProject]:
        result = await self.db.execute(
            select(LearningProject)
            .where(LearningProject.workspace_id == workspace_id)
            .order_by(LearningProject.created_at)
        )
        return list(result.scalars().all())


class ProjectMaterialRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _material_workspace(self, material_id: str) -> str | None:
        """Resolve the Workspace a Material belongs to (best-effort, from attribution)."""
        from app.models.document import UserDocument

        row = await self.db.get(UserDocument, material_id)
        return row.workspace_id if row is not None else None

    async def add(
        self,
        *,
        project_id: str,
        material_id: str,
        project_workspace_id: str,
        material_workspace_id: str | None = None,
    ) -> ProjectMaterial:
        """Add a Material membership to a Project (idempotent).

        Validates same-Workspace before writing (WSP-012). When
        ``material_workspace_id`` is not supplied it is resolved from the
        Material attribution; if the Material is not yet attributed
        (legacy window) the explicit ``material_workspace_id`` must be given.
        """
        resolved = material_workspace_id or await self._material_workspace(material_id)
        if resolved is None:
            raise CrossWorkspaceReferenceError(
                "cannot attribute Material to a Project without a resolvable Workspace"
            )
        if resolved != project_workspace_id:
            raise CrossWorkspaceReferenceError("cross-workspace ProjectMaterial reference rejected")

        existing = await self.db.get(ProjectMaterial, (project_id, material_id))
        if existing is not None:
            return existing

        membership = ProjectMaterial(project_id=project_id, material_id=material_id)
        self.db.add(membership)
        await self.db.flush()
        return membership

    async def remove(self, *, project_id: str, material_id: str) -> bool:
        """Remove a ProjectMaterial membership only (never the Material).

        Idempotent: returns False when the membership did not exist.
        """
        existing = await self.db.get(ProjectMaterial, (project_id, material_id))
        if existing is None:
            return False
        await self.db.delete(existing)
        await self.db.flush()
        return True

    async def list_material_ids(self, project_id: str) -> list[str]:
        result = await self.db.execute(
            select(ProjectMaterial.material_id).where(ProjectMaterial.project_id == project_id)
        )
        return list(result.scalars().all())


class SessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, session_id: str) -> LearningSession | None:
        return await self.db.get(LearningSession, session_id)

    async def create(
        self,
        *,
        workspace_id: str,
        learning_activity_id: str | None = None,
        project_id: str | None = None,
        learning_goal_id: str | None = None,
        status: str = LearningSessionStatus.ACTIVE,
    ) -> LearningSession:
        session = LearningSession(
            session_id=str(uuid4()),
            workspace_id=workspace_id,
            learning_activity_id=learning_activity_id,
            project_id=project_id,
            learning_goal_id=learning_goal_id,
            status=status,
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def add_material(
        self,
        *,
        session_id: str,
        material_id: str,
        session_workspace_id: str,
        material_workspace_id: str | None = None,
    ) -> LearningSessionMaterial:
        resolved = material_workspace_id or await self._material_workspace(material_id)
        if resolved is None:
            raise CrossWorkspaceReferenceError(
                "cannot attribute Material to a Session without a resolvable Workspace"
            )
        if resolved != session_workspace_id:
            raise CrossWorkspaceReferenceError(
                "cross-workspace LearningSessionMaterial reference rejected"
            )
        existing = await self.db.get(LearningSessionMaterial, (session_id, material_id))
        if existing is not None:
            return existing
        row = LearningSessionMaterial(session_id=session_id, material_id=material_id)
        self.db.add(row)
        await self.db.flush()
        return row

    async def _material_workspace(self, material_id: str) -> str | None:
        from app.models.document import UserDocument

        row = await self.db.get(UserDocument, material_id)
        return row.workspace_id if row is not None else None

    async def end(self, session_id: str) -> LearningSession | None:
        session = await self.db.get(LearningSession, session_id)
        if session is None:
            return None
        session.status = LearningSessionStatus.ENDED
        session.ended_at = datetime.now(timezone.utc)
        await self.db.flush()
        return session


class SourceFileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_material(self, material_id: str) -> list[SourceFile]:
        result = await self.db.execute(
            select(SourceFile)
            .where(SourceFile.material_id == material_id)
            .order_by(SourceFile.created_at)
        )
        return list(result.scalars().all())

    async def count_by_material(self, material_id: str) -> int:
        result = await self.db.execute(
            select(func.count(SourceFile.source_file_id)).where(
                SourceFile.material_id == material_id
            )
        )
        return int(result.scalar_one())

    async def create_if_absent(self, values: dict[str, Any]) -> SourceFile:
        """Idempotently create a SourceFile keyed by ``source_file_id``."""
        existing = await self.db.get(SourceFile, values["source_file_id"])
        if existing is not None:
            return existing
        row = SourceFile(**values)
        self.db.add(row)
        await self.db.flush()
        return row

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

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
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
    WorkspaceLifecycle,
)

DEFAULT_WORKSPACE_NAME = "默认工作区"


class WorkspaceError(RuntimeError):
    """Base error for Workspace / Project / Session domain operations."""


class WorkspaceNotFoundError(WorkspaceError):
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

    async def count_for_owner(self, owner_id: str) -> int:
        result = await self.db.execute(
            select(func.count(Workspace.workspace_id)).where(Workspace.owner_id == owner_id)
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
        project_id: str | None = None,
        learning_goal_id: str | None = None,
        status: str = LearningSessionStatus.ACTIVE,
    ) -> LearningSession:
        session = LearningSession(
            session_id=str(uuid4()),
            workspace_id=workspace_id,
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

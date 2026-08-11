"""Domain operations for the Workspace / Project / Session foundation.

Enforces same-Workspace fail-closed (WSP-012/030/031/032):

- ProjectMaterial: ``project.workspace == material.workspace``
- LearningSession refs: workspace == project/goal/every material workspace
- removing a ProjectMaterial never deletes the Material or SourceFile
- add/remove are idempotent
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.goal_management import GoalDefinitionRecord
from app.models.planning import LearningActivityRecord, LearningGoalRecord, LearningPlanRecord
from app.models.workspace import LearningProject, LearningSession, ProjectMaterial
from app.services.workspace.repository import (
    CrossWorkspaceReferenceError,
    ProjectMaterialRepository,
    ProjectRepository,
    SessionRepository,
    WorkspaceNotFoundError,
)

#: canonical goal aggregate table (goal_id -> workspace_id attribution).
_GOAL_TABLES = (
    "learning_goal_versions",
    "learning_goal_definition_versions",
    "learning_goal_state_versions",
    "focused_learning_goal_state_versions",
)


class WorkspaceService:
    """Highest-level controller for Workspace/Project/Session domain operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.projects = ProjectRepository(db)
        self.project_materials = ProjectMaterialRepository(db)
        self.sessions = SessionRepository(db)

    # ---- Projects ---------------------------------------------------------

    async def create_project(
        self,
        *,
        workspace_id: str,
        title: str,
    ) -> LearningProject:
        return await self.projects.create(workspace_id=workspace_id, title=title)

    async def add_project_material(
        self,
        *,
        project_id: str,
        material_id: str,
        workspace_id: str,
        material_workspace_id: str | None = None,
    ) -> ProjectMaterial:
        """Add a Material to a Project iff both are in the same Workspace."""
        project = await self.projects.get(project_id)
        if project is None:
            raise WorkspaceNotFoundError(f"project {project_id} not found")
        if project.workspace_id != workspace_id:
            raise CrossWorkspaceReferenceError("project does not belong to the target Workspace")
        return await self.project_materials.add(
            project_id=project_id,
            material_id=material_id,
            project_workspace_id=project.workspace_id,
            material_workspace_id=material_workspace_id,
        )

    async def remove_project_material(
        self,
        *,
        project_id: str,
        material_id: str,
        workspace_id: str,
    ) -> bool:
        """Remove a membership only; never deletes the Material/SourceFile."""
        project = await self.projects.get(project_id)
        if project is None:
            raise WorkspaceNotFoundError(f"project {project_id} not found")
        if project.workspace_id != workspace_id:
            raise CrossWorkspaceReferenceError("project does not belong to the target Workspace")
        return await self.project_materials.remove(project_id=project_id, material_id=material_id)

    # ---- Sessions ---------------------------------------------------------

    async def create_session(
        self,
        *,
        workspace_id: str,
        learning_activity_id: str | None = None,
        project_id: str | None = None,
        learning_goal_id: str | None = None,
    ) -> LearningSession:
        """Create a LearningSession that may exist with no Project and no Goal."""
        if project_id is not None:
            project = await self.projects.get(project_id)
            if project is None:
                raise WorkspaceNotFoundError(f"project {project_id} not found")
            if project.workspace_id != workspace_id:
                raise CrossWorkspaceReferenceError(
                    "session project ref crosses a Workspace boundary"
                )
        if learning_goal_id is not None:
            goal_workspace = await self._resolve_goal_workspace(learning_goal_id)
            if goal_workspace is not None and goal_workspace != workspace_id:
                raise CrossWorkspaceReferenceError("session goal ref crosses a Workspace boundary")
        if learning_activity_id is not None:
            activity_goal_id = await self._validate_activity_scope(
                learning_activity_id=learning_activity_id,
                workspace_id=workspace_id,
            )
            if learning_goal_id is not None and learning_goal_id != activity_goal_id:
                raise CrossWorkspaceReferenceError(
                    "session Activity and Goal refs do not share the same SYS06 chain"
                )
        return await self.sessions.create(
            workspace_id=workspace_id,
            learning_activity_id=learning_activity_id,
            project_id=project_id,
            learning_goal_id=learning_goal_id,
        )

    async def add_session_material(
        self,
        *,
        session_id: str,
        material_id: str,
        workspace_id: str,
        material_workspace_id: str | None = None,
    ):
        session = await self.sessions.get(session_id)
        if session is None:
            raise WorkspaceNotFoundError(f"session {session_id} not found")
        if session.workspace_id != workspace_id:
            raise CrossWorkspaceReferenceError("session does not belong to the target Workspace")
        return await self.sessions.add_material(
            session_id=session_id,
            material_id=material_id,
            session_workspace_id=session.workspace_id,
            material_workspace_id=material_workspace_id,
        )

    async def _resolve_goal_workspace(self, learning_goal_id: str) -> str | None:
        """Resolve the canonical Goal's Workspace attribution (best-effort)."""
        for model in (LearningGoalRecord, GoalDefinitionRecord):
            rows = (
                (await self.db.execute(select(model).where(model.goal_id == learning_goal_id)))
                .scalars()
                .all()
            )
            if rows:
                ws = getattr(rows[0], "workspace_id", None)
                return ws if ws else None
        return None

    async def _validate_activity_scope(
        self,
        *,
        learning_activity_id: str,
        workspace_id: str,
    ) -> str:
        """CWSP-054: prove the immutable Activity→Plan→Goal→Workspace chain."""
        activity = await self.db.get(LearningActivityRecord, learning_activity_id)
        if activity is None:
            raise WorkspaceNotFoundError("learning Activity does not exist or is inaccessible")
        plan = await self.db.scalar(
            select(LearningPlanRecord).where(
                LearningPlanRecord.plan_id == activity.plan_id,
                LearningPlanRecord.version == activity.plan_version,
            )
        )
        if plan is None:
            raise CrossWorkspaceReferenceError(
                "session Activity ref has no exact immutable Plan version"
            )
        goal_workspace = await self._resolve_goal_workspace(plan.learning_goal_id)
        if goal_workspace is None:
            raise CrossWorkspaceReferenceError(
                "session Activity ref has no resolvable Goal Workspace"
            )
        if goal_workspace != workspace_id:
            raise CrossWorkspaceReferenceError("session Activity ref crosses a Workspace boundary")
        return plan.learning_goal_id

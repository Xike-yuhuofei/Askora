"""Platform Workspace / Project / Session application services.

Scope: durable Workspace/Project/Session foundation for XIK-171. No learner
state, teaching, assessment or review semantics are produced here.
"""

from __future__ import annotations

from app.services.workspace.bootstrap import (
    MigrationResult,
    WorkspaceBootstrapService,
    ensure_default_workspace,
    migrate_legacy_to_default,
)
from app.services.workspace.repository import (
    CrossWorkspaceReferenceError,
    ProjectMaterialRepository,
    ProjectRepository,
    SessionRepository,
    SourceFileRepository,
    WorkspaceError,
    WorkspaceNotFoundError,
    WorkspaceRepository,
)
from app.services.workspace.service import WorkspaceService

__all__ = [
    "CrossWorkspaceReferenceError",
    "MigrationResult",
    "ProjectMaterialRepository",
    "ProjectRepository",
    "SessionRepository",
    "SourceFileRepository",
    "WorkspaceBootstrapService",
    "WorkspaceError",
    "WorkspaceNotFoundError",
    "WorkspaceRepository",
    "WorkspaceService",
    "ensure_default_workspace",
    "migrate_legacy_to_default",
]

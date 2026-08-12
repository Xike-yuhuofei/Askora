"""Durable Platform Workspace / Project / Session / SourceFile persistence.

Governing contracts: ADR-0016, ``docs/specs/platform/workspace-project-session-scope.md``
(WSP-010..WSP-013, WSP-022), ``docs/specs/architecture/state-ownership.md`` (STATE-005).

Ownership:
- ``Workspace``                -> Platform Workspace Registry (WSP-001)
- ``LearningProject``/``ProjectMaterial`` -> Platform Workspace / Product Organization (WSP-002)
- ``LearningSession``/``LearningSessionMaterial`` -> Platform Learning Session Registry (WSP-003)
- ``SourceFile``               -> SYS01-managed raw asset, attributed to Material (WSP-022)

These aggregates own only scope/lifecycle/identity metadata. They MUST NOT write
Material content, Goal semantics, LearnerState, TeachingAction, AssessmentResult
or ReviewSchedule truth.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy import (
    text as sa_text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WorkspaceLifecycle:
    ACTIVE = "active"
    TRASH = "trash"


class Workspace(Base):
    """A single high-level data isolation boundary owned by one LocalOwner.

    WSP-010: stable ``workspace_id``; ``display_name`` is mutable presentation
    metadata and is not identity. Exactly one active default Workspace per owner
    is guaranteed by a partial unique index created in migration
    (``uq_workspaces_one_active_default``) plus application-level idempotent bootstrap.
    """

    __tablename__ = "workspaces"

    workspace_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("local_owners.owner_id"), index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    display_name: Mapped[str] = mapped_column(String(120))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    lifecycle: Mapped[str] = mapped_column(
        String(20), default=WorkspaceLifecycle.ACTIVE, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("lifecycle in ('active', 'trash')", name="ck_workspaces_lifecycle"),
        Index("ix_workspaces_owner_lifecycle", "owner_id", "lifecycle"),
        # WSP-010: exactly one active default Workspace per owner. Partial index
        # works on both SQLite and PostgreSQL.
        Index(
            "uq_workspaces_one_active_default",
            "owner_id",
            unique=True,
            sqlite_where=sa_text("is_default = 1 AND lifecycle = 'active'"),
            postgresql_where=sa_text("is_default = true AND lifecycle = 'active'"),
        ),
    )


class WorkspaceSelection(Base):
    """CWSP-010 durable current-Workspace preference owned by Platform Registry."""

    __tablename__ = "workspace_selections"

    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("local_owners.owner_id"), primary_key=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    current_workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.workspace_id"), nullable=False, index=True
    )
    previous_workspace_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    reason: Mapped[str] = mapped_column(String(40), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(36), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (CheckConstraint("version >= 1", name="ck_workspace_selections_version"),)


class WorkspaceCommandReceipt(Base):
    """CWSP-012 immutable create/switch idempotency receipt."""

    __tablename__ = "workspace_command_receipts"

    receipt_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("local_owners.owner_id"), nullable=False, index=True
    )
    command_type: Mapped[str] = mapped_column(String(40), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(200), nullable=False)
    command_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    response_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index(
            "uq_workspace_command_owner_type_key",
            "owner_id",
            "command_type",
            "idempotency_key",
            unique=True,
        ),
    )


class ProjectStatus:
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class LearningProject(Base):
    """Long-term organizational unit inside one Workspace (WSP-011).

    A Project references canonical refs only; it never copies Material/Goal truth.
    """

    __tablename__ = "learning_projects"

    project_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.workspace_id"), index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default=ProjectStatus.ACTIVE, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "status in ('active', 'paused', 'archived')", name="ck_learning_projects_status"
        ),
        Index("ix_learning_projects_workspace_status", "workspace_id", "status"),
    )


class ProjectMaterial(Base):
    """Current N:M membership between a Project and same-Workspace Materials.

    WSP-012: ``(project_id, material_id)`` unique; Material and Project MUST belong
    to the same Workspace; add/remove idempotent; removing a row never deletes the
    Material or SourceFile.
    """

    __tablename__ = "project_materials"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("learning_projects.project_id"), primary_key=True
    )
    material_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_documents.id"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("ix_project_materials_material", "material_id"),)


class LearningSessionStatus:
    ACTIVE = "active"
    ENDED = "ended"
    ARCHIVED = "archived"


class LearningSession(Base):
    """Narrow Platform Learning Session Registry envelope (WSP-013).

    Owns only the continuous-learning-interval scope/lifecycle:
    Workspace + optional Project/Goal/Material refs + start/end/status. It MUST
    NOT own transcript, TeachingAction, AssessmentResult, LearnerState or
    LearningPlan semantics. ``learning_goal_id`` is a stable canonical ref (the
    goal aggregate id from ``learning_goal_versions.goal_id``) and is not a FK so
    that a Session may exist before a Goal row does.
    """

    __tablename__ = "learning_sessions"

    session_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.workspace_id"), index=True
    )
    learning_activity_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    project_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("learning_projects.project_id"), nullable=True, index=True
    )
    learning_goal_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    status: Mapped[str] = mapped_column(
        String(20), default=LearningSessionStatus.ACTIVE, index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "status in ('active', 'ended', 'archived')", name="ck_learning_sessions_status"
        ),
        Index("ix_learning_sessions_workspace_status", "workspace_id", "status"),
    )


class LearningSessionMaterial(Base):
    """Normalized optional material context for a LearningSession (WSP-013)."""

    __tablename__ = "learning_session_materials"

    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("learning_sessions.session_id"), primary_key=True
    )
    material_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_documents.id"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("ix_learning_session_materials_material", "material_id"),)


class SourceFile(Base):
    """Normalized managed raw source asset attributed to a Material (WSP-022).

    Material ``1:N`` SourceFile. ``managed_storage_ref`` is internal and MUST NOT
    become a browser/public stable path API. Backfilled from embedded legacy
    metadata ``without`` re-copying bytes solely for migration.
    """

    __tablename__ = "source_files"

    source_file_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    material_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_documents.id"), index=True
    )
    checksum: Mapped[str] = mapped_column(String(64))
    original_filename: Mapped[str] = mapped_column(String(255))
    media_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer)
    managed_storage_ref: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("ix_source_files_material", "material_id"),)

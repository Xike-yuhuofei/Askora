"""Add durable Workspace / Project / Session / SourceFile foundation (XIK-171)

Additive, non-destructive migration implementing ADR-0016 + WSP-010..WSP-013,
WSP-021, WSP-022. It:

- creates Platform Workspace / Project / Session / SourceFile tables
  (all new, no existing rows touched);
- adds nullable ``workspace_id`` attribution columns to existing owner-global
  tables (Material, Library, Goal, Dialog, jobs) so legacy data can be
  backfilled deterministically into the default Workspace;
- adds nullable ``learning_session_id`` to ``dialog_sessions`` for canonical
  LearningSession compatibility refs (stays NULL when it cannot be
  reconstructed);
- installs a partial unique index guaranteeing at most one active default
  Workspace per owner.

The migration is additive-first and idempotent: every ``CREATE TABLE`` /
``ADD COLUMN`` / ``CREATE INDEX`` is guarded so it also succeeds when the schema
was already materialised by ``Base.metadata.create_all`` at application startup
(app-startup compatibility, see ``test_exec026_upgrade_accepts_matching_tables_precreated_by_app_startup``).
No NOT NULL is added to existing columns, no data is rewritten and no stable ID
is regenerated. Backfill of the default Workspace and SourceFile records happens
in the application bootstrap/service layer, not here.

Revision ID: w171d0e0a001
Revises: g001d0e0a001
Create Date: 2026-08-10 22:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "w171d0e0a001"
down_revision: str | None = "g001d0e0a001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: owner-global tables that gain a nullable workspace attribution column.
_WORKSPACE_ATTRIBUTION_TABLES = [
    "user_documents",
    "library_tags",
    "library_collections",
    "library_search_projections",
    "library_command_receipts",
    "document_duplicate_suggestions",
    "document_ocr_runs",
    "dialog_sessions",
    "dialog_messages",
    "outbox_tasks",
    "learning_goal_versions",
    "learning_goal_definition_versions",
    "learning_goal_state_versions",
    "focused_learning_goal_state_versions",
    "goal_management_command_receipts",
]


def _existing_tables(bind) -> set[str]:
    return {t for t in sa.inspect(bind).get_table_names()}


def _existing_columns(bind, table: str) -> set[str]:
    if table not in _existing_tables(bind):
        return set()
    return {c["name"] for c in sa.inspect(bind).get_columns(table)}


def _existing_indexes(bind, table: str) -> set[str]:
    if table not in _existing_tables(bind):
        return set()
    return {i["name"] for i in sa.inspect(bind).get_indexes(table)}


def _create_table_guarded(name: str, *columns, **kwargs) -> None:
    bind = op.get_bind()
    if name in _existing_tables(bind):
        return
    op.create_table(name, *columns, **kwargs)


def _add_index_guarded(index_name: str, table: str, *columns, **kwargs) -> None:
    bind = op.get_bind()
    if index_name in _existing_indexes(bind, table):
        return
    op.create_index(index_name, table, list(columns), **kwargs)


def _add_column_guarded(table: str, column: sa.Column) -> None:
    bind = op.get_bind()
    if column.name in _existing_columns(bind, table):
        return
    op.add_column(table, column)


def upgrade() -> None:
    bind = op.get_bind()

    _create_table_guarded(
        "workspaces",
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("lifecycle", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("lifecycle in ('active', 'trash')", name="ck_workspaces_lifecycle"),
        sa.ForeignKeyConstraint(["owner_id"], ["local_owners.owner_id"]),
        sa.PrimaryKeyConstraint("workspace_id"),
    )
    _add_index_guarded("ix_workspaces_owner_lifecycle", "workspaces", "owner_id", "lifecycle")
    _add_index_guarded("ix_workspaces_owner_id", "workspaces", "owner_id")
    _add_index_guarded("ix_workspaces_lifecycle", "workspaces", "lifecycle")
    _add_index_guarded(
        "uq_workspaces_one_active_default",
        "workspaces",
        "owner_id",
        unique=True,
        sqlite_where=sa.text("is_default = 1 AND lifecycle = 'active'"),
        postgresql_where=sa.text("is_default = true AND lifecycle = 'active'"),
    )

    _create_table_guarded(
        "learning_projects",
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "status in ('active', 'paused', 'archived')", name="ck_learning_projects_status"
        ),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.workspace_id"]),
        sa.PrimaryKeyConstraint("project_id"),
    )
    _add_index_guarded(
        "ix_learning_projects_workspace_status",
        "learning_projects",
        "workspace_id",
        "status",
    )
    _add_index_guarded("ix_learning_projects_workspace_id", "learning_projects", "workspace_id")
    _add_index_guarded("ix_learning_projects_status", "learning_projects", "status")

    _create_table_guarded(
        "project_materials",
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("material_id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["material_id"], ["user_documents.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["learning_projects.project_id"]),
        sa.PrimaryKeyConstraint("project_id", "material_id"),
        sa.UniqueConstraint("project_id", "material_id", name="uq_project_material"),
    )
    _add_index_guarded("ix_project_materials_material", "project_materials", "material_id")

    _create_table_guarded(
        "learning_sessions",
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=True),
        sa.Column("learning_goal_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "status in ('active', 'ended', 'archived')", name="ck_learning_sessions_status"
        ),
        sa.ForeignKeyConstraint(["project_id"], ["learning_projects.project_id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.workspace_id"]),
        sa.PrimaryKeyConstraint("session_id"),
    )
    _add_index_guarded(
        "ix_learning_sessions_workspace_status", "learning_sessions", "workspace_id", "status"
    )
    _add_index_guarded("ix_learning_sessions_project_id", "learning_sessions", "project_id")
    _add_index_guarded(
        "ix_learning_sessions_learning_goal_id", "learning_sessions", "learning_goal_id"
    )
    _add_index_guarded("ix_learning_sessions_status", "learning_sessions", "status")
    _add_index_guarded("ix_learning_sessions_workspace_id", "learning_sessions", "workspace_id")

    _create_table_guarded(
        "learning_session_materials",
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("material_id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["material_id"], ["user_documents.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["learning_sessions.session_id"]),
        sa.PrimaryKeyConstraint("session_id", "material_id"),
        sa.UniqueConstraint("session_id", "material_id", name="uq_learning_session_material"),
    )
    _add_index_guarded(
        "ix_learning_session_materials_material", "learning_session_materials", "material_id"
    )

    _create_table_guarded(
        "source_files",
        sa.Column("source_file_id", sa.String(length=36), nullable=False),
        sa.Column("material_id", sa.String(length=36), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("media_type", sa.String(length=100), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("managed_storage_ref", sa.String(length=500), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["material_id"], ["user_documents.id"]),
        sa.PrimaryKeyConstraint("source_file_id"),
    )
    _add_index_guarded("ix_source_files_material", "source_files", "material_id")
    _add_index_guarded("ix_source_files_material_id", "source_files", "material_id")

    # Nullable workspace attribution on existing owner-global tables.
    for table in _WORKSPACE_ATTRIBUTION_TABLES:
        _add_column_guarded(
            table,
            sa.Column(
                "workspace_id",
                sa.String(length=36),
                nullable=True,
                server_default=sa.null(),
            ),
        )
        _add_index_guarded(f"ix_{table}_workspace_id", table, "workspace_id")

    # Canonical LearningSession compatibility ref on legacy DialogSession.
    _add_column_guarded(
        "dialog_sessions",
        sa.Column(
            "learning_session_id",
            sa.String(length=36),
            nullable=True,
            server_default=sa.null(),
        ),
    )
    _add_index_guarded(
        "ix_dialog_sessions_learning_session_id", "dialog_sessions", "learning_session_id"
    )


def downgrade() -> None:
    # Non-destructive reverse for migration tooling / recovery verification.
    # Reversing does NOT push multiple Workspaces back into owner-global rows;
    # it only drops the additive columns and new tables.
    op.drop_index("ix_dialog_sessions_learning_session_id", table_name="dialog_sessions")
    op.drop_column("dialog_sessions", "learning_session_id")

    for table in reversed(_WORKSPACE_ATTRIBUTION_TABLES):
        op.drop_index(f"ix_{table}_workspace_id", table_name=table)
        op.drop_column(table, "workspace_id")

    op.drop_index("ix_source_files_material_id", table_name="source_files")
    op.drop_index("ix_source_files_material", table_name="source_files")
    op.drop_table("source_files")
    op.drop_index(
        "ix_learning_session_materials_material", table_name="learning_session_materials"
    )
    op.drop_table("learning_session_materials")
    op.drop_index(
        "ix_learning_sessions_learning_goal_id", table_name="learning_sessions"
    )
    op.drop_index("ix_learning_sessions_project_id", table_name="learning_sessions")
    op.drop_index("ix_learning_sessions_status", table_name="learning_sessions")
    op.drop_index("ix_learning_sessions_workspace_id", table_name="learning_sessions")
    op.drop_index("ix_learning_sessions_workspace_status", table_name="learning_sessions")
    op.drop_table("learning_sessions")
    op.drop_index("ix_project_materials_material", table_name="project_materials")
    op.drop_table("project_materials")
    op.drop_index("ix_learning_projects_status", table_name="learning_projects")
    op.drop_index("ix_learning_projects_workspace_id", table_name="learning_projects")
    op.drop_index("ix_learning_projects_workspace_status", table_name="learning_projects")
    op.drop_table("learning_projects")
    op.drop_index("uq_workspaces_one_active_default", table_name="workspaces")
    op.drop_index("ix_workspaces_owner_lifecycle", table_name="workspaces")
    op.drop_index("ix_workspaces_owner_id", table_name="workspaces")
    op.drop_index("ix_workspaces_lifecycle", table_name="workspaces")
    op.drop_table("workspaces")
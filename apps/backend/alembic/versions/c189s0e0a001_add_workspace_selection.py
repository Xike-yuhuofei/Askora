"""Add ADR-0023 WorkspaceSelection, receipts and Activity-scoped Session ref.

Revision ID: c189s0e0a001
Revises: w171r0e0a002
Create Date: 2026-08-11 22:35:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa

from alembic import op

revision: str = "c189s0e0a001"
down_revision: str | None = "w171r0e0a002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _tables(bind: sa.engine.Connection) -> set[str]:
    return set(sa.inspect(bind).get_table_names())


def _columns(bind: sa.engine.Connection, table: str) -> set[str]:
    if table not in _tables(bind):
        return set()
    return {str(column["name"]) for column in sa.inspect(bind).get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    tables = _tables(bind)
    if "workspace_selections" not in tables:
        op.create_table(
            "workspace_selections",
            sa.Column("owner_id", sa.String(length=36), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.Column("current_workspace_id", sa.String(length=36), nullable=False),
            sa.Column("previous_workspace_id", sa.String(length=36), nullable=True),
            sa.Column("reason", sa.String(length=40), nullable=False),
            sa.Column("correlation_id", sa.String(length=36), nullable=False),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["owner_id"], ["local_owners.owner_id"]),
            sa.ForeignKeyConstraint(["current_workspace_id"], ["workspaces.workspace_id"]),
            sa.CheckConstraint("version >= 1", name="ck_workspace_selections_version"),
            sa.PrimaryKeyConstraint("owner_id"),
        )
        op.create_index(
            "ix_workspace_selections_current_workspace_id",
            "workspace_selections",
            ["current_workspace_id"],
        )
    if "workspace_command_receipts" not in tables:
        op.create_table(
            "workspace_command_receipts",
            sa.Column("receipt_id", sa.String(length=36), nullable=False),
            sa.Column("owner_id", sa.String(length=36), nullable=False),
            sa.Column("command_type", sa.String(length=40), nullable=False),
            sa.Column("idempotency_key", sa.String(length=200), nullable=False),
            sa.Column("command_digest", sa.String(length=64), nullable=False),
            sa.Column("response_payload", sa.JSON(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["owner_id"], ["local_owners.owner_id"]),
            sa.PrimaryKeyConstraint("receipt_id"),
        )
        op.create_index(
            "ix_workspace_command_receipts_owner_id",
            "workspace_command_receipts",
            ["owner_id"],
        )
        op.create_index(
            "uq_workspace_command_owner_type_key",
            "workspace_command_receipts",
            ["owner_id", "command_type", "idempotency_key"],
            unique=True,
        )
    if "learning_activity_id" not in _columns(bind, "learning_sessions"):
        op.add_column(
            "learning_sessions",
            sa.Column("learning_activity_id", sa.String(length=36), nullable=True),
        )
        op.create_index(
            "ix_learning_sessions_learning_activity_id",
            "learning_sessions",
            ["learning_activity_id"],
        )

    # Existing migrated owners get a deterministic current selection to their
    # active default. A truly fresh database has no Workspace and remains empty.
    if "workspaces" in _tables(bind):
        rows = bind.execute(
            sa.text(
                "SELECT owner_id, workspace_id FROM workspaces "
                "WHERE is_default = :is_default AND lifecycle = 'active'"
            ),
            {"is_default": True},
        ).mappings()
        for row in rows:
            exists = bind.execute(
                sa.text("SELECT 1 FROM workspace_selections WHERE owner_id = :owner_id"),
                {"owner_id": row["owner_id"]},
            ).first()
            if exists is not None:
                continue
            correlation = str(uuid5(NAMESPACE_URL, f"askora:workspace-selection:{row['owner_id']}"))
            bind.execute(
                sa.text(
                    "INSERT INTO workspace_selections "
                    "(owner_id, version, current_workspace_id, previous_workspace_id, "
                    "reason, correlation_id) VALUES "
                    "(:owner_id, 1, :workspace_id, NULL, 'LEGACY_MIGRATION', :correlation_id)"
                ),
                {
                    "owner_id": row["owner_id"],
                    "workspace_id": row["workspace_id"],
                    "correlation_id": correlation,
                },
            )


def downgrade() -> None:
    bind = op.get_bind()
    if "workspace_command_receipts" in _tables(bind):
        if bind.execute(sa.text("SELECT 1 FROM workspace_command_receipts LIMIT 1")).first():
            raise RuntimeError("CWSP-071 forbids downgrade after Workspace command writes")
    if "workspace_selections" in _tables(bind):
        changed = bind.execute(
            sa.text("SELECT 1 FROM workspace_selections WHERE version > 1 LIMIT 1")
        ).first()
        multiple = bind.execute(
            sa.text(
                "SELECT owner_id FROM workspaces WHERE lifecycle = 'active' "
                "GROUP BY owner_id HAVING COUNT(*) > 1 LIMIT 1"
            )
        ).first()
        if changed or multiple:
            raise RuntimeError("CWSP-071 forbids destructive multi-Workspace downgrade")
    if "learning_activity_id" in _columns(bind, "learning_sessions"):
        if bind.execute(
            sa.text(
                "SELECT 1 FROM learning_sessions WHERE learning_activity_id IS NOT NULL LIMIT 1"
            )
        ).first():
            raise RuntimeError("CWSP-071 forbids dropping Activity-scoped Session refs")
        op.drop_index("ix_learning_sessions_learning_activity_id", table_name="learning_sessions")
        with op.batch_alter_table("learning_sessions") as batch_op:
            batch_op.drop_column("learning_activity_id")
    if "workspace_command_receipts" in _tables(bind):
        op.drop_index(
            "uq_workspace_command_owner_type_key", table_name="workspace_command_receipts"
        )
        op.drop_index(
            "ix_workspace_command_receipts_owner_id", table_name="workspace_command_receipts"
        )
        op.drop_table("workspace_command_receipts")
    if "workspace_selections" in _tables(bind):
        op.drop_index(
            "ix_workspace_selections_current_workspace_id", table_name="workspace_selections"
        )
        op.drop_table("workspace_selections")

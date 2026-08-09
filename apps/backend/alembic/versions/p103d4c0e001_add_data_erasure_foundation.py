"""add P1-03 durable data-erasure foundation

Revision ID: p103d4c0e001
Revises: 9b4c2d7e1a60
Create Date: 2026-08-09 13:35:00.000000

Forward strategy: add orchestration, owner-step, content-free receipt and
monotonic checkpoint tables. Existing domain data is not rewritten.

Rollback strategy: allowed only before any erasure checkpoint is issued. Once
an erasure receipt exists, keep the tombstones and use a forward-fix so an old
recovery point can never silently regain eligibility.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "p103d4c0e001"
down_revision = "9b4c2d7e1a60"
branch_labels = None
depends_on = None


def _assert_compatible_existing_table(
    table_name: str,
    *,
    required_columns: set[str],
    required_unique_constraints: set[str],
) -> None:
    """Fail closed instead of accepting a guessed pre-created schema."""
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns(table_name)}
    unique_constraints = {
        constraint["name"]
        for constraint in inspector.get_unique_constraints(table_name)
        if constraint.get("name")
    }
    missing_columns = required_columns - columns
    missing_constraints = required_unique_constraints - unique_constraints
    if missing_columns or missing_constraints:
        raise RuntimeError(
            f"existing {table_name} is incompatible with {revision}: "
            f"missing columns={sorted(missing_columns)}, "
            f"missing unique constraints={sorted(missing_constraints)}"
        )


def _ensure_index(table_name: str, index_name: str, columns: list[str]) -> None:
    inspector = sa.inspect(op.get_bind())
    existing = {index["name"] for index in inspector.get_indexes(table_name)}
    if index_name not in existing:
        op.create_index(index_name, table_name, columns, unique=False)


def upgrade() -> None:
    existing_tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "data_erasure_checkpoints" not in existing_tables:
        op.create_table(
            "data_erasure_checkpoints",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("checkpoint", sa.Integer(), nullable=False),
            sa.Column("receipt_id", sa.String(36), nullable=True),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )
    else:
        _assert_compatible_existing_table(
            "data_erasure_checkpoints",
            required_columns={"id", "checkpoint", "receipt_id", "updated_at"},
            required_unique_constraints=set(),
        )
    bind = op.get_bind()
    if not bind.scalar(sa.text("SELECT count(*) FROM data_erasure_checkpoints WHERE id = 1")):
        op.execute(sa.text("INSERT INTO data_erasure_checkpoints (id, checkpoint) VALUES (1, 0)"))

    if "data_erasure_workflows" not in existing_tables:
        op.create_table(
            "data_erasure_workflows",
            sa.Column("workflow_id", sa.String(36), primary_key=True),
            sa.Column("user_id", sa.String(36), nullable=False),
            sa.Column("user_ref", sa.String(100), nullable=False),
            sa.Column("scope", sa.String(40), nullable=False),
            sa.Column("target_ref", sa.String(255), nullable=True),
            sa.Column("target_ref_hash", sa.String(64), nullable=False),
            sa.Column("idempotency_key", sa.String(200), nullable=False),
            sa.Column("request_digest", sa.String(64), nullable=False),
            sa.Column("status", sa.String(40), nullable=False),
            sa.Column("checkpoint", sa.Integer(), nullable=True),
            sa.Column("report", sa.JSON(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.UniqueConstraint(
                "user_ref", "idempotency_key", name="uq_erasure_user_idempotency"
            ),
        )
    else:
        _assert_compatible_existing_table(
            "data_erasure_workflows",
            required_columns={
                "workflow_id", "user_id", "user_ref", "scope", "target_ref",
                "target_ref_hash", "idempotency_key", "request_digest", "status",
                "checkpoint", "report", "created_at", "updated_at",
            },
            required_unique_constraints={"uq_erasure_user_idempotency"},
        )
    for index_name, columns in {
        "ix_data_erasure_workflows_user_id": ["user_id"],
        "ix_data_erasure_workflows_user_ref": ["user_ref"],
        "ix_data_erasure_workflows_scope": ["scope"],
        "ix_data_erasure_workflows_status": ["status"],
        "ix_erasure_workflow_status_updated": ["status", "updated_at"],
    }.items():
        _ensure_index("data_erasure_workflows", index_name, columns)

    if "data_erasure_steps" not in existing_tables:
        op.create_table(
            "data_erasure_steps",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("workflow_id", sa.String(36), nullable=False),
            sa.Column("owner_system", sa.String(50), nullable=False),
            sa.Column("ordinal", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(40), nullable=False),
            sa.Column("affected_records", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("reason_codes", sa.JSON(), nullable=False),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["workflow_id"], ["data_erasure_workflows.workflow_id"], ondelete="CASCADE"
            ),
            sa.UniqueConstraint("workflow_id", "owner_system", name="uq_erasure_step_owner"),
        )
    else:
        _assert_compatible_existing_table(
            "data_erasure_steps",
            required_columns={
                "id", "workflow_id", "owner_system", "ordinal", "status",
                "affected_records", "reason_codes", "updated_at",
            },
            required_unique_constraints={"uq_erasure_step_owner"},
        )
    _ensure_index("data_erasure_steps", "ix_data_erasure_steps_workflow_id", ["workflow_id"])
    _ensure_index("data_erasure_steps", "ix_data_erasure_steps_status", ["status"])

    if "data_erasure_receipts" not in existing_tables:
        op.create_table(
            "data_erasure_receipts",
            sa.Column("receipt_id", sa.String(36), primary_key=True),
            sa.Column("workflow_id", sa.String(36), nullable=False, unique=True),
            sa.Column("user_ref", sa.String(100), nullable=False),
            sa.Column("scope", sa.String(40), nullable=False),
            sa.Column("target_ref_hash", sa.String(64), nullable=False),
            sa.Column("checkpoint", sa.Integer(), nullable=False, unique=True),
            sa.Column("result_digest", sa.String(64), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(
                ["workflow_id"], ["data_erasure_workflows.workflow_id"], ondelete="RESTRICT"
            ),
        )
    else:
        _assert_compatible_existing_table(
            "data_erasure_receipts",
            required_columns={
                "receipt_id", "workflow_id", "user_ref", "scope", "target_ref_hash",
                "checkpoint", "result_digest", "completed_at",
            },
            required_unique_constraints=set(),
        )
    _ensure_index("data_erasure_receipts", "ix_data_erasure_receipts_user_ref", ["user_ref"])
    _ensure_index("data_erasure_receipts", "ix_data_erasure_receipts_scope", ["scope"])


def downgrade() -> None:
    bind = op.get_bind()
    receipts = bind.scalar(sa.text("SELECT count(*) FROM data_erasure_receipts"))
    checkpoint = bind.scalar(
        sa.text("SELECT checkpoint FROM data_erasure_checkpoints WHERE id = 1")
    )
    if receipts or checkpoint:
        raise RuntimeError("DATA_ERASURE_DOWNGRADE_BLOCKED_BY_TOMBSTONE")
    op.drop_table("data_erasure_receipts")
    op.drop_table("data_erasure_steps")
    op.drop_table("data_erasure_workflows")
    op.drop_table("data_erasure_checkpoints")

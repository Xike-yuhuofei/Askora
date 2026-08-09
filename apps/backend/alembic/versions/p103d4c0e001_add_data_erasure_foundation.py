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


def upgrade() -> None:
    op.create_table(
        "data_erasure_checkpoints",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("checkpoint", sa.Integer(), nullable=False),
        sa.Column("receipt_id", sa.String(36), nullable=True),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.execute(sa.text("INSERT INTO data_erasure_checkpoints (id, checkpoint) VALUES (1, 0)"))
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
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("user_ref", "idempotency_key", name="uq_erasure_user_idempotency"),
    )
    op.create_index("ix_data_erasure_workflows_user_id", "data_erasure_workflows", ["user_id"])
    op.create_index("ix_data_erasure_workflows_user_ref", "data_erasure_workflows", ["user_ref"])
    op.create_index("ix_data_erasure_workflows_scope", "data_erasure_workflows", ["scope"])
    op.create_index("ix_data_erasure_workflows_status", "data_erasure_workflows", ["status"])
    op.create_index(
        "ix_erasure_workflow_status_updated",
        "data_erasure_workflows",
        ["status", "updated_at"],
    )
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
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["workflow_id"], ["data_erasure_workflows.workflow_id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("workflow_id", "owner_system", name="uq_erasure_step_owner"),
    )
    op.create_index("ix_data_erasure_steps_workflow_id", "data_erasure_steps", ["workflow_id"])
    op.create_index("ix_data_erasure_steps_status", "data_erasure_steps", ["status"])
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
    op.create_index("ix_data_erasure_receipts_user_ref", "data_erasure_receipts", ["user_ref"])
    op.create_index("ix_data_erasure_receipts_scope", "data_erasure_receipts", ["scope"])


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

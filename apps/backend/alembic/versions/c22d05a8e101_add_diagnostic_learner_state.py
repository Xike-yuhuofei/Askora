"""add prerequisite diagnostic and LearnerState projections

Revision ID: c22d05a8e101
Revises: f21a8b07d04a
Create Date: 2026-08-08 20:00:00.000000

Forward strategy: additive immutable SYS03 LearnerState and SYS06
DiagnosticNeed version streams. Existing mastery, assessment, and plan truth is
untouched.

Rollback strategy: export exact JSON payloads, downgrade to f21a8b07d04a, and
retain all existing assessment/mastery/plan tables. A forward-fix recreates the
two projections from their exact source versions without online model calls.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "c22d05a8e101"
down_revision = "f21a8b07d04a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "learner_state_versions",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("learner_state_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("learner_state_id", "version", name="uq_learner_state_version"),
    )
    op.create_index(
        "ix_learner_state_versions_learner_state_id",
        "learner_state_versions",
        ["learner_state_id"],
    )
    op.create_index("ix_learner_state_versions_user_id", "learner_state_versions", ["user_id"])

    op.create_table(
        "diagnostic_need_versions",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("need_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("goal_mapping_id", sa.String(36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("need_id", "version", name="uq_diagnostic_need_version"),
    )
    for name, columns in (
        ("ix_diagnostic_need_versions_need_id", ["need_id"]),
        ("ix_diagnostic_need_versions_user_id", ["user_id"]),
        ("ix_diagnostic_need_versions_goal_mapping_id", ["goal_mapping_id"]),
        ("ix_diagnostic_need_versions_status", ["status"]),
    ):
        op.create_index(name, "diagnostic_need_versions", columns)
    op.create_index(
        "ix_diagnostic_need_versions_idempotency_key",
        "diagnostic_need_versions",
        ["idempotency_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("diagnostic_need_versions")
    op.drop_table("learner_state_versions")

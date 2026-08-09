"""add P1-01B goal lifecycle, objectives and achievement evidence

Revision ID: d2f1010b38b2
Revises: d2f1010a37a1
Create Date: 2026-08-09 15:10:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "d2f1010b38b2"
down_revision = "d2f1010a37a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    existing = set(sa.inspect(op.get_bind()).get_table_names())
    if "goal_achievement_policy_versions" in existing:
        return
    op.create_table(
        "goal_achievement_policy_versions",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("policy_id", sa.String(36), nullable=False),
        sa.Column("policy_version", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("policy_id", "policy_version", name="uq_goal_achievement_policy"),
    )
    op.create_index(
        "ix_goal_achievement_policy_versions_policy_id",
        "goal_achievement_policy_versions",
        ["policy_id"],
    )
    op.create_table(
        "learning_objective_versions",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("objective_id", sa.String(36), nullable=False),
        sa.Column("goal_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("objective_version", sa.Integer(), nullable=False),
        sa.Column("criterion_id", sa.String(36), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("objective_id", "objective_version", name="uq_learning_objective_version"),
    )
    for column in ("objective_id", "goal_id", "user_id", "criterion_id"):
        op.create_index(
            f"ix_learning_objective_versions_{column}", "learning_objective_versions", [column]
        )
    op.create_table(
        "goal_assessment_activity_versions",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("assessment_activity_id", sa.String(36), nullable=False),
        sa.Column("goal_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("criterion_id", sa.String(36), nullable=False),
        sa.Column("activity_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("grader_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "assessment_activity_id",
            "activity_version",
            name="uq_goal_assessment_activity_version",
        ),
    )
    for column in ("assessment_activity_id", "goal_id", "user_id", "criterion_id", "status"):
        op.create_index(
            f"ix_goal_assessment_activity_versions_{column}",
            "goal_assessment_activity_versions",
            [column],
        )
    op.create_table(
        "goal_achievement_evaluation_versions",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("evaluation_id", sa.String(36), nullable=False),
        sa.Column("goal_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("evaluation_version", sa.Integer(), nullable=False),
        sa.Column("eligible", sa.Boolean(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "evaluation_id",
            "evaluation_version",
            name="uq_goal_achievement_evaluation",
        ),
    )
    for column in ("evaluation_id", "goal_id", "user_id", "eligible"):
        op.create_index(
            f"ix_goal_achievement_evaluation_versions_{column}",
            "goal_achievement_evaluation_versions",
            [column],
        )


def downgrade() -> None:
    op.drop_table("goal_achievement_evaluation_versions")
    op.drop_table("goal_assessment_activity_versions")
    op.drop_table("learning_objective_versions")
    op.drop_table("goal_achievement_policy_versions")

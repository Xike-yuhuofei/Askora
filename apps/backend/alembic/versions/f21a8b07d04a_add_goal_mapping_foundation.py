"""add SYS06 goal formation and knowledge mapping foundation

Revision ID: f21a8b07d04a
Revises: e14a1c0de014
Create Date: 2026-08-08 18:00:00.000000

Forward strategy: additive immutable/versioned SYS06 tables. Existing plans,
content truth, learner state and review schedules are untouched.

Rollback strategy: export goal/mapping/subgraph/inference payloads, downgrade to
e14a1c0de014, and retain existing planner/content tables. A forward-fix can
recreate these tables from the exported exact versioned payloads; replay never
calls an online model.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "f21a8b07d04a"
down_revision = "e14a1c0de014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "learning_goal_versions",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("goal_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("goal_id", "version", name="uq_learning_goal_version"),
    )
    op.create_index("ix_learning_goal_versions_goal_id", "learning_goal_versions", ["goal_id"])
    op.create_index("ix_learning_goal_versions_user_id", "learning_goal_versions", ["user_id"])
    op.create_index("ix_learning_goal_versions_status", "learning_goal_versions", ["status"])
    op.create_index(
        "ix_learning_goal_versions_idempotency_key",
        "learning_goal_versions",
        ["idempotency_key"],
        unique=True,
    )

    op.create_table(
        "goal_knowledge_mapping_versions",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("mapping_id", sa.String(36), nullable=False),
        sa.Column("goal_id", sa.String(36), nullable=False),
        sa.Column("goal_version", sa.Integer(), nullable=False),
        sa.Column("mapping_version", sa.Integer(), nullable=False),
        sa.Column("mapper_version", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("mapping_id", "mapping_version", name="uq_goal_mapping_version"),
    )
    for name, columns in (
        ("ix_goal_knowledge_mapping_versions_mapping_id", ["mapping_id"]),
        ("ix_goal_knowledge_mapping_versions_goal_id", ["goal_id"]),
        ("ix_goal_knowledge_mapping_versions_status", ["status"]),
    ):
        op.create_index(name, "goal_knowledge_mapping_versions", columns)
    op.create_index(
        "ix_goal_knowledge_mapping_versions_idempotency_key",
        "goal_knowledge_mapping_versions",
        ["idempotency_key"],
        unique=True,
    )

    op.create_table(
        "goal_knowledge_subgraph_versions",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("subgraph_id", sa.String(36), nullable=False),
        sa.Column("mapping_id", sa.String(36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("subgraph_id", "version", name="uq_goal_subgraph_version"),
    )
    op.create_index(
        "ix_goal_knowledge_subgraph_versions_subgraph_id",
        "goal_knowledge_subgraph_versions",
        ["subgraph_id"],
    )
    op.create_index(
        "ix_goal_knowledge_subgraph_versions_mapping_id",
        "goal_knowledge_subgraph_versions",
        ["mapping_id"],
    )

    op.create_table(
        "goal_formation_inferences",
        sa.Column("inference_id", sa.String(36), primary_key=True),
        sa.Column("goal_id", sa.String(36), nullable=False),
        sa.Column("input_digest", sa.String(64), nullable=False),
        sa.Column("provider", sa.String(100), nullable=True),
        sa.Column("model_name", sa.String(200), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_goal_formation_inferences_goal_id", "goal_formation_inferences", ["goal_id"]
    )
    op.create_index(
        "ix_goal_formation_inferences_input_digest",
        "goal_formation_inferences",
        ["input_digest"],
    )
    op.create_index("ix_goal_formation_inferences_status", "goal_formation_inferences", ["status"])


def downgrade() -> None:
    op.drop_table("goal_formation_inferences")
    op.drop_table("goal_knowledge_subgraph_versions")
    op.drop_table("goal_knowledge_mapping_versions")
    op.drop_table("learning_goal_versions")

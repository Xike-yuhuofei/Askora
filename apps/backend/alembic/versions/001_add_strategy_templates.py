"""001 - add strategy templates, knowledge points, learning materials

Revision ID: 001
Revises:
Create Date: 2026-08-05 00:00:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "strategy_templates",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("level_1_goal", sa.String(length=100), nullable=False),
        sa.Column("level_2_skill", sa.String(length=100), nullable=False),
        sa.Column("level_3_context", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("prompt_template", sa.Text(), nullable=False),
        sa.Column(
            "follow_up_strategies",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
        sa.Column(
            "escalation_threshold",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("3"),
        ),
        sa.Column(
            "de_escalation_threshold",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("2"),
        ),
        sa.Column(
            "version",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'1.0'"),
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_strategy_templates_level_1_goal",
        "strategy_templates",
        ["level_1_goal"],
    )
    op.create_index(
        "ix_strategy_templates_level_2_skill",
        "strategy_templates",
        ["level_2_skill"],
    )
    op.create_index(
        "ix_strategy_templates_level_3_context",
        "strategy_templates",
        ["level_3_context"],
    )
    op.create_index(
        "idx_strategy_l1_l2_l3",
        "strategy_templates",
        ["level_1_goal", "level_2_skill", "level_3_context"],
    )

    op.create_table(
        "knowledge_points",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("subject", sa.String(length=100), nullable=False),
        sa.Column("unit_id", sa.String(length=36), nullable=True),
        sa.Column("parent_id", sa.String(length=36), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("difficulty", sa.Integer(), nullable=False, server_default=sa.text("3")),
        sa.Column("grade_range", sa.JSON(), nullable=False),
        sa.Column("prerequisites", sa.JSON(), nullable=False),
        sa.Column("successors", sa.JSON(), nullable=False),
        sa.Column("misconceptions", sa.JSON(), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "version",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'1.0'"),
        ),
        sa.Column("vector_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("graph_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(
        "ix_knowledge_points_subject",
        "knowledge_points",
        ["subject"],
    )
    op.create_index(
        "ix_knowledge_points_parent_id",
        "knowledge_points",
        ["parent_id"],
    )
    op.create_index(
        "idx_kp_subject_level",
        "knowledge_points",
        ["subject", "level"],
    )
    op.create_index(
        "idx_kp_parent_id",
        "knowledge_points",
        ["parent_id"],
    )

    op.create_table(
        "learning_materials",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("knowledge_point_id", sa.String(length=36), nullable=False),
        sa.Column("material_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_json", sa.JSON(), nullable=False),
        sa.Column("difficulty", sa.Integer(), nullable=False, server_default=sa.text("3")),
        sa.Column("hint_levels", sa.JSON(), nullable=False),
        sa.Column("template_id", sa.String(length=100), nullable=True),
        sa.Column(
            "is_cacheable",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("source", sa.String(length=200), nullable=True),
        sa.Column("license", sa.String(length=100), nullable=True),
        sa.Column(
            "review_status",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'draft'"),
        ),
        sa.Column("reviewed_by", sa.String(length=36), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "version",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'1.0'"),
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["knowledge_point_id"],
            ["knowledge_points.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_learning_materials_knowledge_point_id",
        "learning_materials",
        ["knowledge_point_id"],
    )
    op.create_index(
        "ix_learning_materials_material_type",
        "learning_materials",
        ["material_type"],
    )
    op.create_index(
        "ix_learning_materials_template_id",
        "learning_materials",
        ["template_id"],
    )
    op.create_index(
        "idx_material_kp_type",
        "learning_materials",
        ["knowledge_point_id", "material_type"],
    )
    op.create_index(
        "idx_material_template_id",
        "learning_materials",
        ["template_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_material_template_id", table_name="learning_materials")
    op.drop_index("idx_material_kp_type", table_name="learning_materials")
    op.drop_index("ix_learning_materials_template_id", table_name="learning_materials")
    op.drop_index("ix_learning_materials_material_type", table_name="learning_materials")
    op.drop_index("ix_learning_materials_knowledge_point_id", table_name="learning_materials")
    op.drop_table("learning_materials")

    op.drop_index("idx_kp_parent_id", table_name="knowledge_points")
    op.drop_index("idx_kp_subject_level", table_name="knowledge_points")
    op.drop_index("ix_knowledge_points_parent_id", table_name="knowledge_points")
    op.drop_index("ix_knowledge_points_subject", table_name="knowledge_points")
    op.drop_table("knowledge_points")

    op.drop_index("idx_strategy_l1_l2_l3", table_name="strategy_templates")
    op.drop_index("ix_strategy_templates_level_3_context", table_name="strategy_templates")
    op.drop_index("ix_strategy_templates_level_2_skill", table_name="strategy_templates")
    op.drop_index("ix_strategy_templates_level_1_goal", table_name="strategy_templates")
    op.drop_table("strategy_templates")

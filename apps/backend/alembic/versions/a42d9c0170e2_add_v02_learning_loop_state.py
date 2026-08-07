"""add v0.2 assessment, learner, review, and planning state

Revision ID: a42d9c0170e2
Revises: c81f6ec4a2d1
Create Date: 2026-08-07 18:00:00.000000

Forward strategy: additive version-stream tables. Legacy assessment mastery JSON and
DialogSession.mastery_estimate are deliberately not backfilled into canonical evidence.
Rollback strategy: drain/export pending v0.2 outbox work, then downgrade to c81f6ec4a2d1;
legacy sessions/messages remain untouched. A forward-fix re-applies this revision and
replays only audited AssessmentResult/LearnerEvidence records.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "a42d9c0170e2"
down_revision = "c81f6ec4a2d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "canonical_assessment_attempts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("item_id", sa.String(36), nullable=False),
        sa.Column("item_version", sa.String(50), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_canonical_assessment_attempts_idempotency_key",
        "canonical_assessment_attempts",
        ["idempotency_key"],
        unique=True,
    )
    op.create_index(
        "ix_canonical_assessment_attempts_user_id", "canonical_assessment_attempts", ["user_id"]
    )
    op.create_index(
        "ix_canonical_assessment_attempts_item_id", "canonical_assessment_attempts", ["item_id"]
    )

    op.create_table(
        "canonical_assessment_result_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("attempt_id", sa.String(36), nullable=False),
        sa.Column("result_version", sa.Integer(), nullable=False),
        sa.Column("supersedes_result_id", sa.String(36), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("attempt_id", "result_version", name="uq_canonical_result_version"),
    )
    op.create_index(
        "ix_canonical_assessment_result_versions_attempt_id",
        "canonical_assessment_result_versions",
        ["attempt_id"],
    )

    op.create_table(
        "learner_evidence",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_result_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("knowledge_unit_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("reason_codes", sa.JSON(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_learner_evidence_source_result_id",
        "learner_evidence",
        ["source_result_id"],
        unique=True,
    )
    op.create_index("ix_learner_evidence_user_id", "learner_evidence", ["user_id"])
    op.create_index(
        "ix_learner_evidence_knowledge_unit_id", "learner_evidence", ["knowledge_unit_id"]
    )
    op.create_index("ix_learner_evidence_status", "learner_evidence", ["status"])

    op.create_table(
        "canonical_mastery_estimate_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("knowledge_unit_id", sa.String(36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint(
            "user_id", "knowledge_unit_id", "version", name="uq_canonical_mastery_version"
        ),
    )
    op.create_index(
        "ix_canonical_mastery_estimate_versions_user_id",
        "canonical_mastery_estimate_versions",
        ["user_id"],
    )
    op.create_index(
        "ix_canonical_mastery_estimate_versions_knowledge_unit_id",
        "canonical_mastery_estimate_versions",
        ["knowledge_unit_id"],
    )

    op.create_table(
        "review_observations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("knowledge_unit_id", sa.String(36), nullable=False),
        sa.Column("actual_reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_review_observations_user_id", "review_observations", ["user_id"])
    op.create_index(
        "ix_review_observations_knowledge_unit_id", "review_observations", ["knowledge_unit_id"]
    )

    op.create_table(
        "review_schedule_versions",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("schedule_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("knowledge_unit_id", sa.String(36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("next_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("schedule_id", "version", name="uq_review_schedule_version"),
    )
    op.create_index(
        "ix_review_schedule_versions_schedule_id", "review_schedule_versions", ["schedule_id"]
    )
    op.create_index("ix_review_schedule_versions_user_id", "review_schedule_versions", ["user_id"])
    op.create_index(
        "ix_review_schedule_versions_knowledge_unit_id",
        "review_schedule_versions",
        ["knowledge_unit_id"],
    )
    op.create_index(
        "idx_review_latest", "review_schedule_versions", ["user_id", "knowledge_unit_id", "version"]
    )

    op.create_table(
        "learning_plan_versions",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("plan_id", sa.String(36), nullable=False),
        sa.Column("learning_goal_id", sa.String(36), nullable=False),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("superseded_by_version", sa.Integer(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("plan_id", "version", name="uq_learning_plan_version"),
    )
    op.create_index("ix_learning_plan_versions_plan_id", "learning_plan_versions", ["plan_id"])
    op.create_index(
        "ix_learning_plan_versions_learning_goal_id", "learning_plan_versions", ["learning_goal_id"]
    )
    op.create_index(
        "ix_learning_plan_versions_idempotency_key",
        "learning_plan_versions",
        ["idempotency_key"],
        unique=True,
    )
    op.create_index("ix_learning_plan_versions_status", "learning_plan_versions", ["status"])

    op.create_table(
        "learning_activities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("plan_id", sa.String(36), nullable=False),
        sa.Column("plan_version", sa.Integer(), nullable=False),
        sa.Column("priority", sa.Float(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_learning_activities_plan_id", "learning_activities", ["plan_id"])


def downgrade() -> None:
    op.drop_table("learning_activities")
    op.drop_table("learning_plan_versions")
    op.drop_table("review_schedule_versions")
    op.drop_table("review_observations")
    op.drop_table("canonical_mastery_estimate_versions")
    op.drop_table("learner_evidence")
    op.drop_table("canonical_assessment_result_versions")
    op.drop_table("canonical_assessment_attempts")

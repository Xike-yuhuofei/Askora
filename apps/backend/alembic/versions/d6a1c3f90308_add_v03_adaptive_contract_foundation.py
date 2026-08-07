"""add v0.3 adaptive contract and migration foundation

Revision ID: d6a1c3f90308
Revises: a42d9c0170e2
Create Date: 2026-08-07 22:00:00.000000

Forward strategy: additive immutable/versioned tables plus nullable v0.3 index
columns on the existing append-only DecisionTrace ledger.  Historical v1 rows
are preserved byte-for-byte and are read only through the v1 compatibility path.

Rollback strategy: export/drain v0.3 rows, downgrade to a42d9c0170e2, and keep
all v0.2 ledgers/state untouched.  A forward-fix may recreate these tables and
replay only exact v0.3 payloads; lossy legacy values are never guessed.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "d6a1c3f90308"
down_revision = "a42d9c0170e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "teaching_contexts",
        sa.Column("context_id", sa.String(36), primary_key=True),
        sa.Column("schema_version", sa.String(20), nullable=False),
        sa.Column("context_fingerprint", sa.String(255), nullable=False),
        sa.Column("decision_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("context_fingerprint"),
    )
    op.create_index("ix_teaching_context_decision_time", "teaching_contexts", ["decision_time"])

    op.create_table(
        "policy_bundles",
        sa.Column("bundle_id", sa.String(255), primary_key=True),
        sa.Column("schema_version", sa.String(20), nullable=False),
        sa.Column("policy_version", sa.String(100), nullable=False),
        sa.Column("content_digest", sa.String(255), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("policy_version"),
        sa.UniqueConstraint("content_digest"),
    )

    op.create_table(
        "policy_bundle_activations",
        sa.Column("activation_id", sa.String(36), primary_key=True),
        sa.Column("bundle_id", sa.String(255), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("supersedes_activation_id", sa.String(36), nullable=True),
        sa.Column("reason_codes", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["bundle_id"], ["policy_bundles.bundle_id"]),
        sa.ForeignKeyConstraint(
            ["supersedes_activation_id"], ["policy_bundle_activations.activation_id"]
        ),
    )
    op.create_index(
        "ix_policy_bundle_activations_bundle_id",
        "policy_bundle_activations",
        ["bundle_id"],
    )
    op.create_index(
        "ix_policy_activation_time",
        "policy_bundle_activations",
        ["activated_at", "activation_id"],
    )

    op.create_table(
        "teaching_action_versions",
        sa.Column("action_id", sa.String(36), primary_key=True),
        sa.Column("schema_version", sa.String(20), nullable=False),
        sa.Column("decision_id", sa.String(36), nullable=False),
        sa.Column("context_id", sa.String(36), nullable=False),
        sa.Column("policy_bundle_id", sa.String(255), nullable=False),
        sa.Column("strategy_family", sa.String(50), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["context_id"], ["teaching_contexts.context_id"]),
        sa.ForeignKeyConstraint(["policy_bundle_id"], ["policy_bundles.bundle_id"]),
        sa.UniqueConstraint("decision_id"),
    )
    op.create_index(
        "ix_teaching_action_versions_context_id", "teaching_action_versions", ["context_id"]
    )
    op.create_index(
        "ix_teaching_action_versions_policy_bundle_id",
        "teaching_action_versions",
        ["policy_bundle_id"],
    )
    op.create_index(
        "ix_teaching_action_versions_strategy_family",
        "teaching_action_versions",
        ["strategy_family"],
    )

    op.create_table(
        "experiment_assignments",
        sa.Column("assignment_id", sa.String(36), primary_key=True),
        sa.Column("schema_version", sa.String(20), nullable=False),
        sa.Column("experiment_id", sa.String(100), nullable=False),
        sa.Column("experiment_version", sa.String(100), nullable=False),
        sa.Column("unit_ref", sa.String(255), nullable=False),
        sa.Column("variant_id", sa.String(100), nullable=False),
        sa.Column("assignment_probability", sa.Float(), nullable=True),
        sa.Column("opt_out", sa.Boolean(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_index(
        "ix_experiment_assignment_lookup",
        "experiment_assignments",
        ["experiment_id", "experiment_version", "unit_ref"],
    )

    op.create_table(
        "teaching_episodes",
        sa.Column("episode_id", sa.String(36), primary_key=True),
        sa.Column("schema_version", sa.String(20), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_index("ix_teaching_episodes_user_id", "teaching_episodes", ["user_id"])

    op.create_table(
        "learning_trajectories",
        sa.Column("trajectory_id", sa.String(36), primary_key=True),
        sa.Column("schema_version", sa.String(20), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_index("ix_learning_trajectories_user_id", "learning_trajectories", ["user_id"])

    op.create_table(
        "outcome_observations",
        sa.Column("outcome_id", sa.String(36), primary_key=True),
        sa.Column("schema_version", sa.String(20), nullable=False),
        sa.Column("outcome_type", sa.String(100), nullable=False),
        sa.Column("measurement_entity_type", sa.String(100), nullable=False),
        sa.Column("measurement_entity_id", sa.String(255), nullable=False),
        sa.Column("measurement_version", sa.String(100), nullable=False),
        sa.Column("attribution_scope", sa.String(50), nullable=False),
        sa.Column("teaching_episode_id", sa.String(36), nullable=True),
        sa.Column("learning_trajectory_id", sa.String(36), nullable=True),
        sa.Column("experiment_assignment_id", sa.String(36), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["teaching_episode_id"], ["teaching_episodes.episode_id"]),
        sa.ForeignKeyConstraint(
            ["learning_trajectory_id"], ["learning_trajectories.trajectory_id"]
        ),
        sa.ForeignKeyConstraint(
            ["experiment_assignment_id"], ["experiment_assignments.assignment_id"]
        ),
    )
    op.create_index(
        "ix_outcome_measurement",
        "outcome_observations",
        ["measurement_entity_type", "measurement_entity_id", "measurement_version"],
    )
    op.create_index("ix_outcome_observed_at", "outcome_observations", ["observed_at"])

    with op.batch_alter_table("learning_events") as batch:
        batch.add_column(sa.Column("producer_system", sa.String(20), nullable=True))
        batch.add_column(sa.Column("v03_payload", sa.JSON(), nullable=True))
    op.create_index("ix_learning_event_producer", "learning_events", ["producer_system"])

    with op.batch_alter_table("decision_traces") as batch:
        batch.add_column(sa.Column("decision_time", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("v03_payload", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("teaching_context_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("policy_bundle_id", sa.String(255), nullable=True))
        batch.add_column(sa.Column("behavior_policy_type", sa.String(40), nullable=True))
        batch.add_column(sa.Column("action_propensity", sa.Float(), nullable=True))
        batch.add_column(sa.Column("experiment_assignment_probability", sa.Float(), nullable=True))
        batch.add_column(sa.Column("replayability_status", sa.String(30), nullable=True))

    op.create_index("ix_decision_trace_context", "decision_traces", ["teaching_context_id"])
    op.create_index("ix_decision_trace_policy_bundle", "decision_traces", ["policy_bundle_id"])
    op.create_index("ix_decision_trace_behavior", "decision_traces", ["behavior_policy_type"])
    op.create_index("ix_decision_trace_replayability", "decision_traces", ["replayability_status"])


def downgrade() -> None:
    op.drop_index("ix_decision_trace_replayability", table_name="decision_traces")
    op.drop_index("ix_decision_trace_behavior", table_name="decision_traces")
    op.drop_index("ix_decision_trace_policy_bundle", table_name="decision_traces")
    op.drop_index("ix_decision_trace_context", table_name="decision_traces")
    with op.batch_alter_table("decision_traces") as batch:
        batch.drop_column("replayability_status")
        batch.drop_column("experiment_assignment_probability")
        batch.drop_column("action_propensity")
        batch.drop_column("behavior_policy_type")
        batch.drop_column("policy_bundle_id")
        batch.drop_column("teaching_context_id")
        batch.drop_column("v03_payload")
        batch.drop_column("decision_time")

    op.drop_index("ix_learning_event_producer", table_name="learning_events")
    with op.batch_alter_table("learning_events") as batch:
        batch.drop_column("v03_payload")
        batch.drop_column("producer_system")

    op.drop_table("outcome_observations")
    op.drop_table("learning_trajectories")
    op.drop_table("teaching_episodes")
    op.drop_table("experiment_assignments")
    op.drop_table("teaching_action_versions")
    op.drop_table("policy_bundle_activations")
    op.drop_table("policy_bundles")
    op.drop_table("teaching_contexts")

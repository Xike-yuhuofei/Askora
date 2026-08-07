"""add event, decision, and outbox foundation

Revision ID: c81f6ec4a2d1
Revises: b87ea36c12f4
Create Date: 2026-08-07 11:10:00.000000

Forward strategy: additive tables only; legacy readers/writers remain compatible.
Rollback strategy: downgrade removes only EXEC-001 tables. Before rollback, drain or
export their rows because append-only v0.2 ledger data has no legacy representation.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "c81f6ec4a2d1"
down_revision = "b87ea36c12f4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "learning_events",
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("schema_version", sa.String(length=20), nullable=False),
        sa.Column("aggregate_type", sa.String(length=100), nullable=False),
        sa.Column("aggregate_id", sa.String(length=255), nullable=False),
        sa.Column("aggregate_version", sa.Integer(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("correlation_id", sa.String(length=36), nullable=False),
        sa.Column("causation_id", sa.String(length=36), nullable=True),
        sa.Column("actor", sa.JSON(), nullable=False),
        sa.Column("context", sa.JSON(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("trace", sa.JSON(), nullable=False),
        sa.Column("privacy", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("event_id"),
        sa.UniqueConstraint(
            "aggregate_type",
            "aggregate_id",
            "aggregate_version",
            name="uq_learning_event_aggregate_version",
        ),
        sa.UniqueConstraint("idempotency_key", name="uq_learning_event_idempotency_key"),
    )
    op.create_index(
        "ix_learning_event_aggregate_sequence",
        "learning_events",
        ["aggregate_type", "aggregate_id", "sequence"],
    )
    op.create_index(
        "ix_learning_event_type_recorded", "learning_events", ["event_type", "recorded_at"]
    )
    op.create_index(
        "ix_learning_event_correlation", "learning_events", ["correlation_id"]
    )

    op.create_table(
        "decision_traces",
        sa.Column("decision_id", sa.String(length=36), nullable=False),
        sa.Column("decision_type", sa.String(length=100), nullable=False),
        sa.Column("schema_version", sa.String(length=20), nullable=False),
        sa.Column("owner_system", sa.String(length=50), nullable=False),
        sa.Column("inputs", sa.JSON(), nullable=False),
        sa.Column("candidates", sa.JSON(), nullable=False),
        sa.Column("selected", sa.JSON(), nullable=False),
        sa.Column("constraints", sa.JSON(), nullable=False),
        sa.Column("reason_codes", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("algorithm", sa.JSON(), nullable=False),
        sa.Column("algorithm_id", sa.String(length=100), nullable=False),
        sa.Column("algorithm_version", sa.String(length=100), nullable=False),
        sa.Column("experiment", sa.JSON(), nullable=False),
        sa.Column("experiment_id", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("correlation_id", sa.String(length=36), nullable=False),
        sa.Column("trace_id", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("decision_id"),
    )
    op.create_index(
        "ix_decision_trace_type_created", "decision_traces", ["decision_type", "created_at"]
    )
    op.create_index("ix_decision_trace_owner", "decision_traces", ["owner_system"])
    op.create_index(
        "ix_decision_trace_correlation", "decision_traces", ["correlation_id"]
    )
    op.create_index("ix_decision_trace_trace_id", "decision_traces", ["trace_id"])
    op.create_index(
        "ix_decision_trace_algorithm",
        "decision_traces",
        ["algorithm_id", "algorithm_version"],
    )
    op.create_index("ix_decision_trace_experiment", "decision_traces", ["experiment_id"])

    op.create_table(
        "decision_trace_inputs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("decision_id", sa.String(length=36), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=255), nullable=False),
        sa.Column("entity_version", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(
            ["decision_id"], ["decision_traces.decision_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_decision_input_entity",
        "decision_trace_inputs",
        ["entity_type", "entity_id", "entity_version"],
    )
    op.create_index(
        "ix_decision_input_decision", "decision_trace_inputs", ["decision_id"]
    )

    op.create_table(
        "outbox_tasks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("type", sa.String(length=100), nullable=False),
        sa.Column("schema_version", sa.String(length=20), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
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
        sa.UniqueConstraint("idempotency_key", name="uq_outbox_task_idempotency_key"),
    )
    op.create_index(
        "ix_outbox_status_due",
        "outbox_tasks",
        ["status", "next_attempt_at", "created_at"],
    )
    op.create_index("ix_outbox_type_status", "outbox_tasks", ["type", "status"])


def downgrade() -> None:
    op.drop_index("ix_outbox_type_status", table_name="outbox_tasks")
    op.drop_index("ix_outbox_status_due", table_name="outbox_tasks")
    op.drop_table("outbox_tasks")

    op.drop_index("ix_decision_input_decision", table_name="decision_trace_inputs")
    op.drop_index("ix_decision_input_entity", table_name="decision_trace_inputs")
    op.drop_table("decision_trace_inputs")

    op.drop_index("ix_decision_trace_experiment", table_name="decision_traces")
    op.drop_index("ix_decision_trace_algorithm", table_name="decision_traces")
    op.drop_index("ix_decision_trace_trace_id", table_name="decision_traces")
    op.drop_index("ix_decision_trace_correlation", table_name="decision_traces")
    op.drop_index("ix_decision_trace_owner", table_name="decision_traces")
    op.drop_index("ix_decision_trace_type_created", table_name="decision_traces")
    op.drop_table("decision_traces")

    op.drop_index("ix_learning_event_correlation", table_name="learning_events")
    op.drop_index("ix_learning_event_type_recorded", table_name="learning_events")
    op.drop_index("ix_learning_event_aggregate_sequence", table_name="learning_events")
    op.drop_table("learning_events")

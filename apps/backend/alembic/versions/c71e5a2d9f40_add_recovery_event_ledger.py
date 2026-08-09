"""add append-only recovery event ledger

Revision ID: c71e5a2d9f40
Revises: a80d4f9c2b61
Create Date: 2026-08-09 13:10:00.000000

The table is an operational audit/projection owned by SYS08. It does not
replace any domain owner state. Downgrade removes only this additive ledger;
owner documents, outbox tasks and learning state remain untouched.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c71e5a2d9f40"
down_revision: str | None = "a80d4f9c2b61"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _assert_compatible_existing_table() -> None:
    """Fail closed if app startup precreated an incompatible recovery ledger."""

    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("recovery_events")}
    unique_constraints = {
        constraint["name"]
        for constraint in inspector.get_unique_constraints("recovery_events")
        if constraint.get("name")
    }
    required_columns = {
        "id",
        "pseudonym_id",
        "issue_key",
        "issue_version",
        "event_type",
        "code",
        "category",
        "severity",
        "status",
        "source_system",
        "data_safety",
        "duplicate_risk",
        "title",
        "summary",
        "resource_ref",
        "correlation_id",
        "attempt_count",
        "retry_budget",
        "next_eligible_at",
        "action_code",
        "idempotency_key",
        "result_ref",
        "safe_details",
        "created_at",
    }
    required_unique_constraints = {
        "uq_recovery_issue_version",
        "uq_recovery_action_event",
    }
    missing_columns = required_columns - columns
    missing_constraints = required_unique_constraints - unique_constraints
    if missing_columns or missing_constraints:
        raise RuntimeError(
            f"existing recovery_events is incompatible with {revision}: "
            f"missing columns={sorted(missing_columns)}, "
            f"missing unique constraints={sorted(missing_constraints)}"
        )


def _ensure_index(index_name: str, columns: list[str]) -> None:
    inspector = sa.inspect(op.get_bind())
    existing = {index["name"] for index in inspector.get_indexes("recovery_events")}
    if index_name not in existing:
        op.create_index(index_name, "recovery_events", columns, unique=False)


def upgrade() -> None:
    existing_tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "recovery_events" not in existing_tables:
        op.create_table(
            "recovery_events",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("pseudonym_id", sa.String(length=32), nullable=False),
            sa.Column("issue_key", sa.String(length=255), nullable=False),
            sa.Column("issue_version", sa.Integer(), nullable=False),
            sa.Column("event_type", sa.String(length=40), nullable=False),
            sa.Column("code", sa.String(length=100), nullable=False),
            sa.Column("category", sa.String(length=40), nullable=False),
            sa.Column("severity", sa.String(length=20), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("source_system", sa.String(length=30), nullable=False),
            sa.Column("data_safety", sa.String(length=40), nullable=False),
            sa.Column("duplicate_risk", sa.String(length=40), nullable=False),
            sa.Column("title", sa.String(length=160), nullable=False),
            sa.Column("summary", sa.String(length=500), nullable=False),
            sa.Column("resource_ref", sa.String(length=255), nullable=True),
            sa.Column("correlation_id", sa.String(length=100), nullable=True),
            sa.Column("attempt_count", sa.Integer(), nullable=False),
            sa.Column("retry_budget", sa.Integer(), nullable=True),
            sa.Column("next_eligible_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("action_code", sa.String(length=80), nullable=True),
            sa.Column("idempotency_key", sa.String(length=255), nullable=True),
            sa.Column("result_ref", sa.String(length=100), nullable=True),
            sa.Column("safe_details", sa.JSON(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["pseudonym_id"], ["users.pseudonym_id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "pseudonym_id",
                "issue_key",
                "issue_version",
                name="uq_recovery_issue_version",
            ),
            sa.UniqueConstraint(
                "pseudonym_id",
                "idempotency_key",
                "event_type",
                name="uq_recovery_action_event",
            ),
        )
    else:
        _assert_compatible_existing_table()
    _ensure_index(
        "ix_recovery_owner_status",
        ["pseudonym_id", "status", "created_at"],
    )
    _ensure_index(
        "ix_recovery_issue_version",
        ["issue_key", "issue_version"],
    )


def downgrade() -> None:
    op.drop_index("ix_recovery_issue_version", table_name="recovery_events")
    op.drop_index("ix_recovery_owner_status", table_name="recovery_events")
    op.drop_table("recovery_events")

"""widen DecisionTrace input version storage

Revision ID: 9b4c2d7e1a60
Revises: e23a91b807d1
Create Date: 2026-08-08 20:30:00.000000

Forward strategy: widen the generic DecisionTrace query index without rewriting
the append-only trace payload or changing domain ownership. Existing code is
compatible with the wider column.

Rollback strategy: narrow only when every persisted value still fits the old
100-character budget. Never truncate immutable audit provenance; otherwise
retain the wider schema and use a forward-fix.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "9b4c2d7e1a60"
down_revision = "e23a91b807d1"
branch_labels = None
depends_on = None

OLD_MAX_LENGTH = 100
NEW_MAX_LENGTH = 255


def upgrade() -> None:
    with op.batch_alter_table("decision_trace_inputs") as batch_op:
        batch_op.alter_column(
            "entity_version",
            existing_type=sa.String(OLD_MAX_LENGTH),
            type_=sa.String(NEW_MAX_LENGTH),
            existing_nullable=True,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inputs = sa.table(
        "decision_trace_inputs",
        sa.column("entity_version", sa.String(NEW_MAX_LENGTH)),
    )
    oversized = bind.scalar(
        sa.select(sa.func.count())
        .select_from(inputs)
        .where(sa.func.length(inputs.c.entity_version) > OLD_MAX_LENGTH)
    )
    if oversized:
        raise RuntimeError(
            "DECISION_TRACE_INPUT_VERSION_DOWNGRADE_BLOCKED:"
            f"{oversized} immutable values exceed {OLD_MAX_LENGTH} characters"
        )
    with op.batch_alter_table("decision_trace_inputs") as batch_op:
        batch_op.alter_column(
            "entity_version",
            existing_type=sa.String(NEW_MAX_LENGTH),
            type_=sa.String(OLD_MAX_LENGTH),
            existing_nullable=True,
        )

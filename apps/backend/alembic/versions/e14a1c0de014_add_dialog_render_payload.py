"""add versioned rich-response payload to dialog messages

Revision ID: e14a1c0de014
Revises: d6a1c3f90308
Create Date: 2026-08-08 12:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "e14a1c0de014"
down_revision = "d6a1c3f90308"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("dialog_messages") as batch_op:
        batch_op.add_column(sa.Column("render_payload", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("dialog_messages") as batch_op:
        batch_op.drop_column("render_payload")

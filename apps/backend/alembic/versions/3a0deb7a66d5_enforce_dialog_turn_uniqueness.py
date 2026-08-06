"""enforce dialog turn uniqueness

Revision ID: 3a0deb7a66d5
Revises: 7a6ff3390755
Create Date: 2026-08-06 18:28:34.582344

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "3a0deb7a66d5"
down_revision = "7a6ff3390755"
branch_labels = None
depends_on = None


def upgrade() -> None:
    duplicate_groups = (
        op.get_bind()
        .execute(
            sa.text(
                "SELECT COUNT(*) FROM ("
                "SELECT 1 FROM dialog_messages "
                "GROUP BY session_id, turn_number, role HAVING COUNT(*) > 1"
                ") AS duplicate_groups"
            )
        )
        .scalar_one()
    )
    if duplicate_groups:
        raise RuntimeError(
            "dialog_messages contains duplicate turn/role rows; "
            "back up and reconcile those rows before retrying this migration"
        )

    with op.batch_alter_table("dialog_messages") as batch_op:
        batch_op.create_unique_constraint(
            "uq_dialog_message_turn_role",
            ["session_id", "turn_number", "role"],
        )


def downgrade() -> None:
    with op.batch_alter_table("dialog_messages") as batch_op:
        batch_op.drop_constraint("uq_dialog_message_turn_role", type_="unique")

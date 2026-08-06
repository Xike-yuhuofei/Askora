"""Add the optional private-user nickname.

Revision ID: b87ea36c12f4
Revises: 3a0deb7a66d5
"""

import sqlalchemy as sa

from alembic import op

revision = "b87ea36c12f4"
down_revision = "3a0deb7a66d5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("nickname", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "nickname")

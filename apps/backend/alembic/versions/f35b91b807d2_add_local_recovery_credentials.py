"""Add local recovery credentials and durable throttling.

Revision ID: f35b91b807d2
Revises: f34a91b807d1
"""

import sqlalchemy as sa

from alembic import op

revision = "f35b91b807d2"
down_revision = "f34a91b807d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recovery_credentials",
        sa.Column("credential_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("secret_digest", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("version > 0", name="ck_recovery_credentials_version_positive"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("credential_id"),
        sa.UniqueConstraint("user_id", "version", name="uq_recovery_credentials_user_version"),
    )
    op.create_index(
        "ix_recovery_credentials_user_created",
        "recovery_credentials",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_table(
        "recovery_throttles",
        sa.Column("subject_digest", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("failure_count", sa.Integer(), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "failure_count >= 0", name="ck_recovery_throttles_failure_nonnegative"
        ),
        sa.PrimaryKeyConstraint("subject_digest", "action"),
    )


def downgrade() -> None:
    op.drop_table("recovery_throttles")
    op.drop_index("ix_recovery_credentials_user_created", table_name="recovery_credentials")
    op.drop_table("recovery_credentials")

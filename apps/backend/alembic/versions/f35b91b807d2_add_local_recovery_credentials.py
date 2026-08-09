"""Add local recovery credentials and durable throttling.

Revision ID: f35b91b807d2
Revises: f34a91b807d1
"""

import sqlalchemy as sa

from alembic import context, op

revision = "f35b91b807d2"
down_revision = "f34a91b807d1"
branch_labels = None
depends_on = None


def _accept_compatible_precreated_schema() -> bool:
    if context.is_offline_mode():
        return False
    inspector = sa.inspect(op.get_bind())
    expected_tables = {"recovery_credentials", "recovery_throttles"}
    precreated = expected_tables & set(inspector.get_table_names())
    if not precreated:
        return False
    if precreated != expected_tables:
        raise RuntimeError(f"partial precreated recovery schema before {revision}: {sorted(precreated)}")
    required_columns = {
        "recovery_credentials": {
            "credential_id",
            "user_id",
            "version",
            "secret_digest",
            "created_at",
            "used_at",
            "revoked_at",
        },
        "recovery_throttles": {
            "subject_digest",
            "action",
            "failure_count",
            "locked_until",
            "updated_at",
        },
    }
    for table_name, required in required_columns.items():
        columns = {item["name"] for item in inspector.get_columns(table_name)}
        if not required.issubset(columns):
            raise RuntimeError(
                f"incompatible precreated {table_name} schema for {revision}: "
                f"missing={sorted(required - columns)}"
            )
    return True


def upgrade() -> None:
    if _accept_compatible_precreated_schema():
        return
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

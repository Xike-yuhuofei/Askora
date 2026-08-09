"""Add durable identity session foundation.

Revision ID: f34a91b807d1
Revises: e23a91b807d1
"""

import sqlalchemy as sa

from alembic import context, op

revision = "f34a91b807d1"
down_revision = "e23a91b807d1"
branch_labels = None
depends_on = None


def _precreated_schema_state() -> tuple[bool, bool]:
    if context.is_offline_mode():
        return False, False
    inspector = sa.inspect(op.get_bind())
    expected_tables = {"auth_sessions", "identity_command_receipts"}
    expected_user_columns = {"credential_version", "password_changed_at"}
    existing_tables = set(inspector.get_table_names())
    existing_user_columns = {item["name"] for item in inspector.get_columns("users")}
    precreated_tables = expected_tables & existing_tables
    precreated_user_columns = expected_user_columns & existing_user_columns
    if precreated_tables and precreated_tables != expected_tables:
        raise RuntimeError(
            f"partial precreated identity schema before {revision}: "
            f"tables={sorted(precreated_tables)}"
        )
    if precreated_user_columns and precreated_user_columns != expected_user_columns:
        raise RuntimeError(
            f"partial precreated identity user columns before {revision}: "
            f"user_columns={sorted(precreated_user_columns)}"
        )
    required_columns = {
        "auth_sessions": {
            "session_id",
            "user_id",
            "version",
            "token_family_id",
            "current_refresh_jti_digest",
            "credential_version",
            "refresh_expires_at",
            "revoked_at",
        },
        "identity_command_receipts": {
            "receipt_id",
            "user_id",
            "command_type",
            "idempotency_key_digest",
            "request_digest",
            "result_payload",
        },
    }
    if precreated_tables:
        for table_name, required in required_columns.items():
            columns = {item["name"] for item in inspector.get_columns(table_name)}
            if not required.issubset(columns):
                raise RuntimeError(
                    f"incompatible precreated {table_name} schema for {revision}: "
                    f"missing={sorted(required - columns)}"
                )
    return bool(precreated_user_columns), bool(precreated_tables)


def upgrade() -> None:
    user_columns_precreated, tables_precreated = _precreated_schema_state()
    if not user_columns_precreated:
        with op.batch_alter_table("users") as batch_op:
            batch_op.add_column(
                sa.Column("credential_version", sa.Integer(), server_default="1", nullable=False)
            )
            batch_op.add_column(
                sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True)
            )
            batch_op.create_check_constraint(
                "ck_users_credential_version_positive", "credential_version > 0"
            )

    if tables_precreated:
        return

    op.create_table(
        "auth_sessions",
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("token_family_id", sa.String(length=36), nullable=False),
        sa.Column("current_refresh_jti_digest", sa.String(length=64), nullable=False),
        sa.Column("client_instance_digest", sa.String(length=64), nullable=True),
        sa.Column("client_label", sa.String(length=128), nullable=False),
        sa.Column("credential_version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("refresh_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoke_reason", sa.String(length=64), nullable=True),
        sa.CheckConstraint("credential_version > 0", name="ck_auth_sessions_credential_version_positive"),
        sa.CheckConstraint("version > 0", name="ck_auth_sessions_version_positive"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("session_id"),
        sa.UniqueConstraint("token_family_id", name="uq_auth_sessions_token_family"),
    )
    op.create_index(
        "ix_auth_sessions_user_active",
        "auth_sessions",
        ["user_id", "revoked_at", "refresh_expires_at"],
        unique=False,
    )

    op.create_table(
        "identity_command_receipts",
        sa.Column("receipt_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("command_type", sa.String(length=64), nullable=False),
        sa.Column("idempotency_key_digest", sa.String(length=64), nullable=False),
        sa.Column("request_digest", sa.String(length=64), nullable=False),
        sa.Column("result_payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("receipt_id"),
        sa.UniqueConstraint(
            "user_id",
            "command_type",
            "idempotency_key_digest",
            name="uq_identity_command_receipt_key",
        ),
    )
    op.create_index(
        "ix_identity_command_receipts_user_created",
        "identity_command_receipts",
        ["user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_identity_command_receipts_user_created", table_name="identity_command_receipts"
    )
    op.drop_table("identity_command_receipts")
    op.drop_index("ix_auth_sessions_user_active", table_name="auth_sessions")
    op.drop_table("auth_sessions")
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("ck_users_credential_version_positive", type_="check")
        batch_op.drop_column("password_changed_at")
        batch_op.drop_column("credential_version")

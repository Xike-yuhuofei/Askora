"""Add account deletion lifecycle and privacy governance records.

Revision ID: f36c91b807d3
Revises: f35b91b807d2, f1061a0b9c01
"""

import sqlalchemy as sa

from alembic import context, op

revision = "f36c91b807d3"
down_revision = ("f35b91b807d2", "f1061a0b9c01")
branch_labels = None
depends_on = None


def _precreated_schema_state() -> tuple[bool, bool]:
    if context.is_offline_mode():
        return False, False
    inspector = sa.inspect(op.get_bind())
    expected_tables = {
        "account_deletion_previews",
        "account_deletion_requests",
        "owner_erasure_step_receipts",
        "privacy_tombstones",
    }
    existing_tables = set(inspector.get_table_names())
    user_columns = {item["name"] for item in inspector.get_columns("users")}
    precreated_tables = expected_tables & existing_tables
    lifecycle_precreated = "account_lifecycle" in user_columns
    if precreated_tables and precreated_tables != expected_tables:
        raise RuntimeError(
            f"partial precreated account deletion schema before {revision}: "
            f"tables={sorted(precreated_tables)}"
        )
    required_columns = {
        "account_deletion_previews": {
            "preview_id",
            "user_id",
            "subject_digest",
            "manifest_digest",
            "data_fingerprint",
            "preview_payload",
            "expires_at",
        },
        "account_deletion_requests": {
            "request_id",
            "user_id",
            "subject_digest",
            "lifecycle",
            "manifest_digest",
            "purge_due_at",
            "retry_count",
            "blocking_issues",
        },
        "owner_erasure_step_receipts": {
            "receipt_id",
            "request_id",
            "owner",
            "attempt",
            "manifest_digest",
            "receipt_digest",
        },
        "privacy_tombstones": {
            "request_id",
            "subject_digest",
            "manifest_digest",
            "receipts_digest",
            "restore_barrier_digest",
            "final_status",
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
    return lifecycle_precreated, bool(precreated_tables)


def upgrade() -> None:
    lifecycle_precreated, tables_precreated = _precreated_schema_state()
    if not lifecycle_precreated:
        with op.batch_alter_table("users") as batch_op:
            batch_op.add_column(
                sa.Column(
                    "account_lifecycle",
                    sa.String(length=32),
                    server_default="active",
                    nullable=False,
                )
            )
            batch_op.create_check_constraint(
                "ck_users_account_lifecycle",
                "account_lifecycle IN ('active', 'deletion_pending', 'purging', "
                "'deletion_blocked', 'deleted')",
            )
            batch_op.create_index(
                "ix_users_account_lifecycle", ["account_lifecycle"], unique=False
            )

    if tables_precreated:
        return

    op.create_table(
        "account_deletion_previews",
        sa.Column("preview_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("schema_version", sa.String(length=20), nullable=False),
        sa.Column("policy_version", sa.String(length=100), nullable=False),
        sa.Column("subject_digest", sa.String(length=64), nullable=False),
        sa.Column("manifest_digest", sa.String(length=71), nullable=False),
        sa.Column("data_fingerprint", sa.String(length=71), nullable=False),
        sa.Column("manifest_payload", sa.JSON(), nullable=False),
        sa.Column("preview_payload", sa.JSON(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_by_request_id", sa.String(length=36), nullable=True),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("preview_id"),
    )
    op.create_index(
        "ix_account_deletion_previews_user_id", "account_deletion_previews", ["user_id"]
    )
    op.create_index(
        "ix_account_deletion_previews_subject_digest",
        "account_deletion_previews",
        ["subject_digest"],
    )
    op.create_index(
        "ix_account_deletion_previews_user_expiry",
        "account_deletion_previews",
        ["user_id", "expires_at"],
    )

    op.create_table(
        "account_deletion_requests",
        sa.Column("request_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("preview_id", sa.String(length=36), nullable=True),
        sa.Column("schema_version", sa.String(length=20), nullable=False),
        sa.Column("policy_version", sa.String(length=100), nullable=False),
        sa.Column("subject_digest", sa.String(length=64), nullable=False),
        sa.Column("lifecycle", sa.String(length=32), nullable=False),
        sa.Column("manifest_digest", sa.String(length=71), nullable=False),
        sa.Column("manifest_payload", sa.JSON(), nullable=True),
        sa.Column("idempotency_key_digest", sa.String(length=64), nullable=True),
        sa.Column("request_digest", sa.String(length=64), nullable=True),
        sa.Column("control_token_digest", sa.String(length=64), nullable=True),
        sa.Column("cancel_idempotency_key_digest", sa.String(length=64), nullable=True),
        sa.Column("retry_idempotency_key_digest", sa.String(length=64), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("purge_due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("purge_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_step", sa.String(length=50), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("last_error_code", sa.String(length=100), nullable=True),
        sa.Column("blocking_issues", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("retry_count >= 0", name="ck_account_deletion_retry_nonnegative"),
        sa.CheckConstraint(
            "lifecycle IN ('deletion_pending', 'purging', 'deletion_blocked', "
            "'deleted', 'cancelled')",
            name="ck_account_deletion_lifecycle",
        ),
        sa.PrimaryKeyConstraint("request_id"),
        sa.UniqueConstraint(
            "subject_digest", "idempotency_key_digest", name="uq_account_deletion_request_key"
        ),
    )
    op.create_index(
        "ix_account_deletion_requests_user_id", "account_deletion_requests", ["user_id"]
    )
    op.create_index(
        "ix_account_deletion_requests_subject_digest",
        "account_deletion_requests",
        ["subject_digest"],
    )
    op.create_index(
        "ix_account_deletion_requests_lifecycle", "account_deletion_requests", ["lifecycle"]
    )
    op.create_index(
        "ix_account_deletion_requests_due",
        "account_deletion_requests",
        ["lifecycle", "purge_due_at"],
    )

    op.create_table(
        "owner_erasure_step_receipts",
        sa.Column("receipt_id", sa.String(length=36), nullable=False),
        sa.Column("request_id", sa.String(length=36), nullable=False),
        sa.Column("owner", sa.String(length=20), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("requested_count", sa.Integer(), nullable=False),
        sa.Column("deleted_count", sa.Integer(), nullable=False),
        sa.Column("missing_count", sa.Integer(), nullable=False),
        sa.Column("error_count", sa.Integer(), nullable=False),
        sa.Column("manifest_digest", sa.String(length=71), nullable=False),
        sa.Column("receipt_digest", sa.String(length=71), nullable=False),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("attempt > 0", name="ck_owner_erasure_attempt_positive"),
        sa.CheckConstraint(
            "requested_count >= 0 AND deleted_count >= 0 AND missing_count >= 0 AND error_count >= 0",
            name="ck_owner_erasure_counts_nonnegative",
        ),
        sa.PrimaryKeyConstraint("receipt_id"),
        sa.UniqueConstraint("request_id", "owner", "attempt", name="uq_owner_erasure_attempt"),
    )
    op.create_index(
        "ix_owner_erasure_step_receipts_request_id", "owner_erasure_step_receipts", ["request_id"]
    )

    op.create_table(
        "privacy_tombstones",
        sa.Column("request_id", sa.String(length=36), nullable=False),
        sa.Column("schema_version", sa.String(length=20), nullable=False),
        sa.Column("policy_version", sa.String(length=100), nullable=False),
        sa.Column("subject_digest", sa.String(length=64), nullable=False),
        sa.Column("manifest_digest", sa.String(length=71), nullable=False),
        sa.Column("receipts_digest", sa.String(length=71), nullable=False),
        sa.Column("restore_barrier_digest", sa.String(length=71), nullable=False),
        sa.Column("final_status", sa.String(length=20), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("request_id"),
        sa.UniqueConstraint("subject_digest", name="uq_privacy_tombstone_subject"),
    )
    op.create_index(
        "ix_privacy_tombstones_subject_digest",
        "privacy_tombstones",
        ["subject_digest"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_privacy_tombstones_subject_digest", table_name="privacy_tombstones")
    op.drop_table("privacy_tombstones")
    op.drop_index(
        "ix_owner_erasure_step_receipts_request_id", table_name="owner_erasure_step_receipts"
    )
    op.drop_table("owner_erasure_step_receipts")
    op.drop_index("ix_account_deletion_requests_due", table_name="account_deletion_requests")
    op.drop_index("ix_account_deletion_requests_lifecycle", table_name="account_deletion_requests")
    op.drop_index(
        "ix_account_deletion_requests_subject_digest", table_name="account_deletion_requests"
    )
    op.drop_index("ix_account_deletion_requests_user_id", table_name="account_deletion_requests")
    op.drop_table("account_deletion_requests")
    op.drop_index(
        "ix_account_deletion_previews_user_expiry", table_name="account_deletion_previews"
    )
    op.drop_index(
        "ix_account_deletion_previews_subject_digest", table_name="account_deletion_previews"
    )
    op.drop_index("ix_account_deletion_previews_user_id", table_name="account_deletion_previews")
    op.drop_table("account_deletion_previews")
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_index("ix_users_account_lifecycle")
        batch_op.drop_constraint("ck_users_account_lifecycle", type_="check")
        batch_op.drop_column("account_lifecycle")

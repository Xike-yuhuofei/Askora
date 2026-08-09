"""Add account deletion lifecycle and privacy governance records.

Revision ID: f36c91b807d3
Revises: f35b91b807d2, m103f1061a01
"""

import sqlalchemy as sa

from alembic import context, op

revision = "f36c91b807d3"
down_revision = ("f35b91b807d2", "m103f1061a01")
branch_labels = None
depends_on = None


def _precreated_schema_state() -> tuple[bool, bool, set[str]]:
    if context.is_offline_mode():
        return False, False, set()
    inspector = sa.inspect(op.get_bind())
    expected_tables = {
        "account_deletion_previews",
        "account_deletion_requests",
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
    return lifecycle_precreated, bool(precreated_tables), existing_tables


def upgrade() -> None:
    lifecycle_precreated, tables_precreated, existing_tables = _precreated_schema_state()
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
        request_columns = {
            item["name"]
            for item in sa.inspect(op.get_bind()).get_columns("account_deletion_requests")
        }
        additions = {
            "erasure_workflow_id": sa.Column(
                "erasure_workflow_id", sa.String(length=36), nullable=True
            ),
            "erasure_receipt_id": sa.Column(
                "erasure_receipt_id", sa.String(length=36), nullable=True
            ),
            "erasure_checkpoint": sa.Column("erasure_checkpoint", sa.Integer(), nullable=True),
            "restore_barrier_digest": sa.Column(
                "restore_barrier_digest", sa.String(length=71), nullable=True
            ),
        }
        missing = [name for name in additions if name not in request_columns]
        if missing:
            with op.batch_alter_table("account_deletion_requests") as batch_op:
                for name in missing:
                    batch_op.add_column(additions[name])
                if "erasure_workflow_id" in missing:
                    batch_op.create_unique_constraint(
                        "uq_account_deletion_erasure_workflow", ["erasure_workflow_id"]
                    )
        if "owner_erasure_step_receipts" in existing_tables:
            op.drop_table("owner_erasure_step_receipts")
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
        sa.Column("erasure_workflow_id", sa.String(length=36), nullable=True),
        sa.Column("erasure_receipt_id", sa.String(length=36), nullable=True),
        sa.Column("erasure_checkpoint", sa.Integer(), nullable=True),
        sa.Column("restore_barrier_digest", sa.String(length=71), nullable=True),
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
        sa.UniqueConstraint("erasure_workflow_id", name="uq_account_deletion_erasure_workflow"),
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

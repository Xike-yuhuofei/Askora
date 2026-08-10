"""Remove user account authentication system

Askora is a local single-user learning app with no account/login/auth system.
This migration drops the authentication-specific columns from ``users``
(keeping the LocalOwner compatibility projection) and removes the
authentication-only tables (sessions, identity commands, recovery credentials,
account deletion lifecycle).

Revision ID: g001d0e0a001
Revises: b1c0d2f3a001
Create Date: 2026-08-10 21:30:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "g001d0e0a001"
down_revision: str | None = "b1c0d2f3a001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Authentication-only tables that are no longer backed by any ORM model.
_AUTH_TABLES = [
    "auth_sessions",
    "identity_command_receipts",
    "recovery_credentials",
    "recovery_throttles",
    "account_deletion_requests",
    "account_deletion_previews",
    "privacy_tombstones",
    "owner_erasure_step_receipts",
]

# Authentication-only columns removed from the LocalOwner compatibility projection.
_AUTH_USER_COLUMNS = [
    "account_lifecycle",
    "phone_encrypted",
    "phone_hash",
    "email_encrypted",
    "password_hash",
    "credential_version",
    "password_changed_at",
    "wechat_openid_encrypted",
    "real_name_encrypted",
    "is_verified",
    "last_login_at",
    "deleted_at",
]


def _existing_table_names(bind) -> set[str]:
    return set(sa.inspect(bind).get_table_names())


def _existing_user_columns(bind, table: str) -> set[str]:
    return {item["name"] for item in sa.inspect(bind).get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()

    # Constraints / indexes that reference auth-only columns and must be dropped
    # before those columns (SQLite batch DROP re-creates the table including any
    # surviving CHECK constraints that reference the dropped columns).
    _REFERENCING_CONSTRAINTS = [
        "ck_users_account_lifecycle",
        "ck_users_credential_version_positive",
    ]
    _REFERENCING_INDEXES = ["ix_users_account_lifecycle", "ix_users_phone_hash"]

    # 1. Drop authentication-only columns from the users projection.
    existing = _existing_user_columns(bind, "users")
    to_drop = [c for c in _AUTH_USER_COLUMNS if c in existing]
    if to_drop:
        existing_constraints = {c["name"] for c in sa.inspect(bind).get_check_constraints("users")}
        existing_indexes = {i["name"] for i in sa.inspect(bind).get_indexes("users")}
        with op.batch_alter_table("users") as batch_op:
            for cname in _REFERENCING_CONSTRAINTS:
                if cname in existing_constraints:
                    batch_op.drop_constraint(cname, type_="check")
            for iname in _REFERENCING_INDEXES:
                if iname in existing_indexes:
                    batch_op.drop_index(iname)
            for c in to_drop:
                batch_op.drop_column(c)

    # 2. Recreate the status column as a single-value ACTIVE enum so the ORM
    #    model (UserStatus) matches the migration schema (alembic check).
    existing_status_type = None
    for c in sa.inspect(bind).get_columns("users"):
        if c["name"] == "status":
            existing_status_type = c["type"]
            break
    if existing_status_type is not None:
        with op.batch_alter_table("users") as batch_op:
            batch_op.alter_column(
                "status",
                type_=sa.Enum("ACTIVE", name="userstatus"),
                nullable=False,
                existing_server_default=False,
            )

    # 3. Drop authentication-only tables.
    existing_tables = _existing_table_names(bind)
    for table in _AUTH_TABLES:
        if table in existing_tables:
            op.drop_table(table)


def downgrade() -> None:
    """Restore the full pre-removal schema (prior head b1c0d2f3a001).

    Credential *data* is not recoverable; this restores the schema so the
    migration chain can be rolled back to before the auth system was added.
    """
    # 1. Restore auth-only users columns.
    for col in [
        {"name": "phone_encrypted", "type": sa.Text()},
        {"name": "phone_hash", "type": sa.String(length=64)},
        {"name": "email_encrypted", "type": sa.Text()},
        {"name": "password_hash", "type": sa.String(length=256)},
        {"name": "credential_version", "type": sa.Integer(), "server_default": "1"},
        {"name": "password_changed_at", "type": sa.DateTime(timezone=True)},
        {"name": "wechat_openid_encrypted", "type": sa.Text()},
        {"name": "real_name_encrypted", "type": sa.Text()},
        {"name": "is_verified", "type": sa.Boolean(), "server_default": "false"},
        {"name": "last_login_at", "type": sa.DateTime(timezone=True)},
        {"name": "deleted_at", "type": sa.DateTime(timezone=True)},
    ]:
        with op.batch_alter_table("users") as batch_op:
            batch_op.add_column(
                sa.Column(
                    col["name"],
                    col["type"],
                    nullable=True,
                    server_default=col.get("server_default"),
                )
            )

    # account_lifecycle carries an index + CHECK constraint that the rollback
    # chain (f36c91b807d3.downgrade) expects to drop.
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column("account_lifecycle", sa.String(length=32), server_default="active")
        )
        batch_op.create_check_constraint(
            "ck_users_account_lifecycle",
            "account_lifecycle IN ('active', 'deletion_pending', 'purging', "
            "'deletion_blocked', 'deleted')",
        )
        batch_op.create_index("ix_users_account_lifecycle", ["account_lifecycle"], unique=False)

    # phone_hash carries a unique index that the earlier chain
    # (7a6ff3390755.downgrade) drops. The upgrade() removed it, so restore it here.
    with op.batch_alter_table("users") as batch_op:
        batch_op.create_index("ix_users_phone_hash", ["phone_hash"], unique=True)

    # credential_version carries a CHECK constraint that f34a91b807d1.downgrade drops.
    with op.batch_alter_table("users") as batch_op:
        batch_op.create_check_constraint(
            "ck_users_credential_version_positive", "credential_version > 0"
        )

    # 2. Restore the multi-value status enum used by the pre-removal schema.
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "status",
            type_=sa.Enum(
                "ACTIVE", "PENDING_VERIFICATION", "SUSPENDED", "DELETED", name="userstatus"
            ),
            nullable=False,
            existing_server_default=False,
        )

    # 3. Restore identity-session tables (f34a91b807d1).
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

    # 4. Restore recovery tables (f35b91b807d2).
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

    # 5. Restore account-deletion / privacy tables (f36c91b807d3).
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
"""register the existing consent owner table in the migration history

Revision ID: p103c5a0d003
Revises: p103m4a8c002
Create Date: 2026-08-09 15:45:00.000000

Upgrade creates an empty owner table or accepts the exact table previously
created by app startup. It never synthesizes consent facts.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "p103c5a0d003"
down_revision = "p103m4a8c002"
branch_labels = None
depends_on = None

CONSENT_COLUMNS = {
    "id",
    "user_id",
    "consent_type",
    "status",
    "consent_version",
    "consent_text",
    "action_method",
    "context",
    "guardian_user_id",
    "guardian_verification_method",
    "granted_at",
    "withdrawn_at",
    "expires_at",
}
CONSENT_INDEXES = {
    "ix_consent_records_user_id": ["user_id"],
    "ix_consent_records_consent_type": ["consent_type"],
    "idx_consent_user_type": ["user_id", "consent_type"],
    "idx_consent_status": ["status"],
}

consent_type = sa.Enum(
    "TERMS_OF_SERVICE",
    "PRIVACY_POLICY",
    "NECESSARY_DATA_COLLECTION",
    "PERSONALIZATION",
    "DATA_ANALYTICS",
    "MARKETING",
    "GUARDIAN_CONSENT",
    "MINOR_DATA_PROCESSING",
    "EDUCATIONAL_DATA_USE",
    "VOICE_DATA_COLLECTION",
    name="consenttype",
)
consent_status = sa.Enum(
    "GRANTED",
    "WITHDRAWN",
    "EXPIRED",
    name="consentstatus",
)


def _accept_exact_precreated_table() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("consent_records")}
    if columns != CONSENT_COLUMNS:
        raise RuntimeError("existing consent_records does not match the canonical schema")
    primary_key = set(
        inspector.get_pk_constraint("consent_records").get("constrained_columns") or []
    )
    if primary_key != {"id"}:
        raise RuntimeError("existing consent_records has an incompatible primary key")
    foreign_keys = {
        (
            tuple(item.get("constrained_columns") or []),
            item.get("referred_table"),
            tuple(item.get("referred_columns") or []),
        )
        for item in inspector.get_foreign_keys("consent_records")
    }
    if (("user_id",), "users", ("id",)) not in foreign_keys:
        raise RuntimeError("existing consent_records has an incompatible user owner reference")


def _ensure_indexes() -> None:
    inspector = sa.inspect(op.get_bind())
    existing = {index["name"] for index in inspector.get_indexes("consent_records")}
    for name, columns in CONSENT_INDEXES.items():
        if name not in existing:
            op.create_index(name, "consent_records", columns, unique=False)


def upgrade() -> None:
    existing = set(sa.inspect(op.get_bind()).get_table_names())
    if "consent_records" in existing:
        _accept_exact_precreated_table()
    else:
        op.create_table(
            "consent_records",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("user_id", sa.String(36), nullable=False),
            sa.Column("consent_type", consent_type, nullable=False),
            sa.Column("status", consent_status, nullable=False),
            sa.Column("consent_version", sa.String(50), nullable=False),
            sa.Column("consent_text", sa.Text(), nullable=False),
            sa.Column("action_method", sa.String(50), nullable=False),
            sa.Column("context", sa.JSON(), nullable=False),
            sa.Column("guardian_user_id", sa.String(36), nullable=True),
            sa.Column("guardian_verification_method", sa.String(50), nullable=True),
            sa.Column(
                "granted_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        )
    _ensure_indexes()


def downgrade() -> None:
    op.drop_table("consent_records")
    bind = op.get_bind()
    consent_status.drop(bind, checkfirst=True)
    consent_type.drop(bind, checkfirst=True)

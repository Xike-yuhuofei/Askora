"""add P1-06 presentation-only onboarding preferences

Revision ID: f1061a0b9c01
Revises: d2f0410a33c3
Create Date: 2026-08-09 13:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa

from alembic import op

revision: str = "f1061a0b9c01"
down_revision: str | None = "d2f0410a33c3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_PREFERENCE_TABLE = "onboarding_preferences"
_RECEIPT_TABLE = "onboarding_preference_command_receipts"


def _backfill_existing_users() -> None:
    bind = op.get_bind()
    metadata = sa.MetaData()
    users = sa.Table("users", metadata, autoload_with=bind)
    preferences = sa.Table(_PREFERENCE_TABLE, metadata, autoload_with=bind)
    existing_user_ids = {
        row[0] for row in bind.execute(sa.select(preferences.c.user_id)).all()
    }
    now = datetime.now(timezone.utc)
    values = [
        {
            "preference_id": str(
                uuid5(NAMESPACE_URL, f"askora:onboarding-preference:{user_id}")
            ),
            "user_id": user_id,
            "journey_id": "first-learning-v1",
            "preference_version": 1,
            "visibility": "DISMISSED",
            "boundary_notice_version_acknowledged": None,
            "dismissed_reason": "LEGACY_EXISTING_USER_BACKFILL",
            "created_at": now,
            "updated_at": now,
        }
        for (user_id,) in bind.execute(sa.select(users.c.id)).all()
        if user_id not in existing_user_ids
    ]
    if values:
        bind.execute(preferences.insert(), values)


def _validate_precreated() -> None:
    inspector = sa.inspect(op.get_bind())
    preference_columns = {
        item["name"] for item in inspector.get_columns(_PREFERENCE_TABLE)
    }
    receipt_columns = {item["name"] for item in inspector.get_columns(_RECEIPT_TABLE)}
    if not {
        "preference_id",
        "user_id",
        "journey_id",
        "preference_version",
        "visibility",
        "boundary_notice_version_acknowledged",
        "dismissed_reason",
    }.issubset(preference_columns) or not {
        "receipt_id",
        "user_id",
        "journey_id",
        "idempotency_key",
        "command_digest",
        "resulting_preference_version",
    }.issubset(receipt_columns):
        raise RuntimeError(f"incompatible precreated onboarding schema for {revision}")


def upgrade() -> None:
    existing = set(sa.inspect(op.get_bind()).get_table_names())
    present = existing & {_PREFERENCE_TABLE, _RECEIPT_TABLE}
    if present:
        if present != {_PREFERENCE_TABLE, _RECEIPT_TABLE}:
            raise RuntimeError(f"partial precreated onboarding schema: {sorted(present)}")
        _validate_precreated()
        _backfill_existing_users()
        return

    op.create_table(
        _PREFERENCE_TABLE,
        sa.Column("preference_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("journey_id", sa.String(length=80), nullable=False),
        sa.Column("preference_version", sa.Integer(), nullable=False),
        sa.Column("visibility", sa.String(length=20), nullable=False),
        sa.Column(
            "boundary_notice_version_acknowledged", sa.String(length=100), nullable=True
        ),
        sa.Column("dismissed_reason", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("preference_id"),
        sa.UniqueConstraint(
            "user_id", "journey_id", name="uq_onboarding_preference_user_journey"
        ),
    )
    op.create_index(
        "ix_onboarding_preferences_user_id",
        _PREFERENCE_TABLE,
        ["user_id"],
    )
    op.create_index(
        "ix_onboarding_preference_visibility",
        _PREFERENCE_TABLE,
        ["user_id", "visibility"],
    )
    op.create_table(
        _RECEIPT_TABLE,
        sa.Column("receipt_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("journey_id", sa.String(length=80), nullable=False),
        sa.Column("idempotency_key", sa.String(length=200), nullable=False),
        sa.Column("command_digest", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=40), nullable=False),
        sa.Column("resulting_preference_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("receipt_id"),
        sa.UniqueConstraint(
            "user_id",
            "journey_id",
            "idempotency_key",
            name="uq_onboarding_preference_user_idempotency",
        ),
    )
    op.create_index(
        "ix_onboarding_preference_command_receipts_user_id",
        _RECEIPT_TABLE,
        ["user_id"],
    )
    _backfill_existing_users()


def downgrade() -> None:
    op.drop_index(
        "ix_onboarding_preference_command_receipts_user_id",
        table_name=_RECEIPT_TABLE,
    )
    op.drop_table(_RECEIPT_TABLE)
    op.drop_index("ix_onboarding_preference_visibility", table_name=_PREFERENCE_TABLE)
    op.drop_index("ix_onboarding_preferences_user_id", table_name=_PREFERENCE_TABLE)
    op.drop_table(_PREFERENCE_TABLE)

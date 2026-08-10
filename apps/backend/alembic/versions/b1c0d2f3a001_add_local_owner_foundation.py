"""add canonical LocalOwner singleton foundation

Revision ID: b1c0d2f3a001
Revises: p107d2f1a04
Create Date: 2026-08-10 12:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from uuid import NAMESPACE_URL, UUID, uuid5

import sqlalchemy as sa

from alembic import op

revision: str = "b1c0d2f3a001"
down_revision: str | None = "p107d2f1a04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_LOCAL_OWNER_TABLE = "local_owners"
_SINGLETON_KEY = 1
_SCHEMA_VERSION = "1.0"
_PROVENANCE_LEGACY = "legacy_single_learner"


def _canonical_user_id(user_id: str) -> str:
    """Deterministically project a legacy user primary key to a canonical UUID."""
    try:
        return str(UUID(user_id))
    except ValueError:
        return str(uuid5(NAMESPACE_URL, f"askora:legacy-user:{user_id}"))


def _seed_legacy_owner(connection: sa.engine.Connection) -> None:
    """Map a unique non-deleted legacy learner to the canonical owner, or fail closed."""
    inspector = sa.inspect(connection)
    if "users" not in set(inspector.get_table_names()):
        return
    users = sa.Table("users", sa.MetaData(), autoload_with=connection)
    existing = sa.Table(_LOCAL_OWNER_TABLE, sa.MetaData(), autoload_with=connection)
    already = connection.execute(sa.select(existing.c.singleton_key)).all()
    if already:
        return

    rows = connection.execute(
        sa.select(users.c.id, users.c.pseudonym_id).where(users.c.status != "DELETED")
    ).all()
    if not rows:
        # Fresh data store: bootstrap happens at runtime; nothing to seed here.
        return
    if len(rows) > 1:
        raise RuntimeError(
            "LOCAL_OWNER_AMBIGUOUS: "
            f"detected {len(rows)} real legacy learner subjects; cannot safely merge"
        )
    (legacy_user_id, legacy_pseudonym_id) = rows[0]
    connection.execute(
        existing.insert().values(
            singleton_key=_SINGLETON_KEY,
            owner_id=_canonical_user_id(legacy_user_id),
            schema_version=_SCHEMA_VERSION,
            provenance=_PROVENANCE_LEGACY,
            legacy_user_id=legacy_user_id,
            legacy_pseudonym_id=legacy_pseudonym_id,
            created_at=datetime.now(timezone.utc),
        )
    )


def _validate_and_seed_if_present() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {c["name"] for c in inspector.get_columns(_LOCAL_OWNER_TABLE)}
    expected = {
        "singleton_key",
        "owner_id",
        "schema_version",
        "provenance",
        "legacy_user_id",
        "legacy_pseudonym_id",
        "created_at",
    }
    if not expected.issubset(columns):
        raise RuntimeError(
            f"incompatible precreated local_owners schema for {revision}: {sorted(expected - columns)}"
        )
    _seed_legacy_owner(op.get_bind())


def upgrade() -> None:
    existing = set(sa.inspect(op.get_bind()).get_table_names())
    if _LOCAL_OWNER_TABLE in existing:
        _validate_and_seed_if_present()
        return

    op.create_table(
        _LOCAL_OWNER_TABLE,
        sa.Column("singleton_key", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("schema_version", sa.String(length=20), nullable=False),
        sa.Column("provenance", sa.String(length=40), nullable=False),
        sa.Column("legacy_user_id", sa.String(length=36), nullable=True),
        sa.Column("legacy_pseudonym_id", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("singleton_key = 1", name="ck_local_owners_single_row"),
        sa.PrimaryKeyConstraint("singleton_key"),
        sa.UniqueConstraint("owner_id", name="uq_local_owners_owner_id"),
    )
    _seed_legacy_owner(op.get_bind())


def downgrade() -> None:
    op.drop_table(_LOCAL_OWNER_TABLE)
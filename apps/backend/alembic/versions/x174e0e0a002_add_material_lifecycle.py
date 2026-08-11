"""Add canonical Material lifecycle fields and deterministic legacy migration (XIK-174 / EXEC-065)

Implements ``MATLIFE-020`` (canonical lifecycle record) and ``MATLIFE-080..085``
(legacy ``is_deleted/deleted_at`` migration) with a strict source-presence matrix:

```text
is_deleted=false                          -> lifecycle=active
is_deleted=true  + managed source present -> lifecycle=trash   (restorable)
is_deleted=true  + managed source missing -> lifecycle=deleted (terminal legacy tombstone)
```

The source-presence check reads the managed storage base path from the app
settings (the same root the storage adapter resolves against). A legacy deleted
row whose SourceFile was already physically removed is classified as a terminal
legacy tombstone (``MATLIFE-083``): it is NOT reconstructed from stale chunks/
index/backup and does NOT imply broader erasure consent.

The migration is deterministic and idempotent: it only advances rows whose
``lifecycle`` is still NULL (i.e. rows materialised before this migration), so a
re-run never overwrites canonical lifecycle written by the application writer.

Revision ID: x174e0e0a002
Revises: w171d0e0a001
Create Date: 2026-08-10 23:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy import text

from alembic import op

revision: str = "x174e0e0a002"
down_revision: str | None = "x062d0e0a001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _existing_columns(bind, table: str) -> set[str]:
    try:
        return {c["name"] for c in sa.inspect(bind).get_columns(table)}
    except sa.exc.NoSuchTableError:
        return set()


def upgrade() -> None:
    bind = op.get_bind()
    columns = _existing_columns(bind, "user_documents")

    if "lifecycle" not in columns:
        op.add_column(
            "user_documents",
            sa.Column(
                "lifecycle",
                sa.String(length=20),
                nullable=False,
                server_default="active",
            ),
        )
        op.create_index("ix_user_documents_lifecycle", "user_documents", ["lifecycle"])
    if "lifecycle_version" not in columns:
        op.add_column(
            "user_documents",
            sa.Column("lifecycle_version", sa.Integer(), nullable=False, server_default="1"),
        )
    if "trashed_at" not in columns:
        op.add_column(
            "user_documents",
            sa.Column("trashed_at", sa.DateTime(timezone=True), nullable=True),
        )
    if "trash_reason" not in columns:
        op.add_column(
            "user_documents",
            sa.Column("trash_reason", sa.String(length=50), nullable=True),
        )

    # Idempotency receipts table for Trash/Restore commands (MATLIFE-022/032).
    receipt_columns = _existing_columns(bind, "material_lifecycle_receipts")
    if "id" not in receipt_columns:
        op.create_table(
            "material_lifecycle_receipts",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("pseudonym_id", sa.String(length=32), nullable=False),
            sa.Column("workspace_id", sa.String(length=36), nullable=True),
            sa.Column("material_id", sa.String(length=36), nullable=False),
            sa.Column("command_type", sa.String(length=30), nullable=False),
            sa.Column("idempotency_key", sa.String(length=200), nullable=False),
            sa.Column("payload_digest", sa.String(length=64), nullable=False),
            sa.Column("result_payload", sa.JSON(), nullable=False, server_default=text("'{}'")),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["pseudonym_id"], ["users.pseudonym_id"]),
            sa.UniqueConstraint(
                "pseudonym_id",
                "command_type",
                "idempotency_key",
                name="uq_material_lifecycle_receipt_owner_command_key",
            ),
        )
        op.create_index(
            "ix_material_lifecycle_receipts_workspace_id",
            "material_lifecycle_receipts",
            ["workspace_id"],
        )
        op.create_index(
            "ix_material_lifecycle_receipts_material_id",
            "material_lifecycle_receipts",
            ["material_id"],
        )

    # Data migration: classify legacy rows deterministically by source presence.
    try:
        from app.core.config import settings
    except Exception:  # pragma: no cover - settings always importable in alembic env
        storage_root = Path("./data/documents")
    else:
        storage_root = Path(settings.local_storage_base_path)

    rows = bind.execute(
        text(
            "SELECT id, storage_path, is_deleted, deleted_at "
            "FROM user_documents WHERE is_deleted = TRUE"
        )
    ).all()

    for document_id, storage_path, is_deleted, deleted_at in rows:
        if is_deleted:
            source_present = False
            if isinstance(storage_path, str) and storage_path:
                try:
                    candidate = (storage_root / storage_path).resolve()
                    root = storage_root.resolve()
                    source_present = root in candidate.parents and candidate.is_file()
                except (OSError, ValueError):
                    source_present = False
            if source_present:
                lifecycle = "trash"
                reason = "LEGACY_DELETE_SOURCE_PRESENT"
            else:
                lifecycle = "deleted"
                reason = "LEGACY_SOURCE_ALREADY_REMOVED"
            bind.execute(
                text(
                    "UPDATE user_documents SET lifecycle=:l, lifecycle_version=1, "
                    "trashed_at=:t, trash_reason=:r WHERE id=:i"
                ),
                {
                    "l": lifecycle,
                    "t": deleted_at,
                    "r": reason,
                    "i": document_id,
                },
            )


def downgrade() -> None:
    op.drop_index(
        "ix_material_lifecycle_receipts_workspace_id",
        table_name="material_lifecycle_receipts",
    )
    op.drop_index(
        "ix_material_lifecycle_receipts_material_id",
        table_name="material_lifecycle_receipts",
    )
    op.drop_table("material_lifecycle_receipts")
    op.drop_index("ix_user_documents_lifecycle", table_name="user_documents")
    op.drop_column("user_documents", "lifecycle")
    op.drop_column("user_documents", "lifecycle_version")
    op.drop_column("user_documents", "trashed_at")
    op.drop_column("user_documents", "trash_reason")

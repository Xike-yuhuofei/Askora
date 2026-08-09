"""add P1-04B versioned duplicate suggestions

Revision ID: d2f0410a32b2
Revises: d2f0410a31a1
Create Date: 2026-08-09 12:46:00.000000
"""

from __future__ import annotations

import hashlib
import unicodedata

import sqlalchemy as sa

from alembic import op

revision = "d2f0410a32b2"
down_revision = "d2f0410a31a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    duplicate_table_precreated = "document_duplicate_suggestions" in inspector.get_table_names()
    existing_columns = {item["name"] for item in inspector.get_columns("user_documents")}
    if "raw_asset_checksum" not in existing_columns:
        op.add_column(
            "user_documents", sa.Column("raw_asset_checksum", sa.String(64), nullable=True)
        )
    if "content_fingerprint" not in existing_columns:
        op.add_column(
            "user_documents", sa.Column("content_fingerprint", sa.String(64), nullable=True)
        )
    if "fingerprint_version" not in existing_columns:
        op.add_column(
            "user_documents", sa.Column("fingerprint_version", sa.String(50), nullable=True)
        )
    existing_indexes = {item["name"] for item in inspector.get_indexes("user_documents")}
    if "ix_user_documents_raw_asset_checksum" not in existing_indexes:
        op.create_index(
            "ix_user_documents_raw_asset_checksum", "user_documents", ["raw_asset_checksum"]
        )
    if "ix_user_documents_content_fingerprint" not in existing_indexes:
        op.create_index(
            "ix_user_documents_content_fingerprint", "user_documents", ["content_fingerprint"]
        )

    documents = sa.table(
        "user_documents",
        sa.column("id", sa.String()),
        sa.column("moderation_details", sa.JSON()),
        sa.column("raw_asset_checksum", sa.String()),
        sa.column("content_fingerprint", sa.String()),
        sa.column("fingerprint_version", sa.String()),
    )
    connection = op.get_bind()
    for row in connection.execute(sa.select(documents.c.id, documents.c.moderation_details)):
        details = row.moderation_details if isinstance(row.moderation_details, dict) else {}
        record = details.get("content_knowledge_v1", {})
        current_id = record.get("current_revision_id")
        revision_row = next(
            (
                item
                for item in record.get("revisions", [])
                if isinstance(item, dict) and item.get("revision_id") == current_id
            ),
            {},
        )
        visible_text = "\n".join(
            item.get("text", "")
            for item in revision_row.get("source_spans", [])
            if isinstance(item, dict) and _learner_visible(item.get("text", ""))
        )
        normalized = " ".join(unicodedata.normalize("NFKC", visible_text).casefold().split())
        connection.execute(
            documents.update()
            .where(documents.c.id == row.id)
            .values(
                raw_asset_checksum=details.get("raw_asset_checksum"),
                content_fingerprint=(
                    hashlib.sha256(normalized.encode("utf-8")).hexdigest()
                    if revision_row
                    else None
                ),
                fingerprint_version=("normalized-content-v1" if revision_row else None),
            )
        )

    if duplicate_table_precreated:
        return

    op.create_table(
        "document_duplicate_suggestions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("pseudonym_id", sa.String(32), sa.ForeignKey("users.pseudonym_id"), nullable=False),
        sa.Column("primary_document_id", sa.String(36), sa.ForeignKey("user_documents.id"), nullable=False),
        sa.Column("candidate_document_id", sa.String(36), sa.ForeignKey("user_documents.id"), nullable=False),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("fingerprint_version", sa.String(50), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(30), server_default="pending", nullable=False),
        sa.Column("resolution_reason", sa.String(100), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "primary_document_id",
            "candidate_document_id",
            "fingerprint_version",
            name="uq_document_duplicate_pair_policy",
        ),
    )
    op.create_index(
        "ix_duplicate_suggestions_owner_status",
        "document_duplicate_suggestions",
        ["pseudonym_id", "status"],
    )


def downgrade() -> None:
    op.drop_table("document_duplicate_suggestions")
    op.drop_index("ix_user_documents_content_fingerprint", table_name="user_documents")
    op.drop_index("ix_user_documents_raw_asset_checksum", table_name="user_documents")
    op.drop_column("user_documents", "fingerprint_version")
    op.drop_column("user_documents", "content_fingerprint")
    op.drop_column("user_documents", "raw_asset_checksum")


def _learner_visible(text: str) -> bool:
    lowered = text.casefold()
    return not any(
        marker in lowered
        for marker in ("[grader-only]", "reference answer:", "参考答案：", "参考答案:")
    )

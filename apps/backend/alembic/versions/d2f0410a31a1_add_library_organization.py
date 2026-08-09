"""add P1-04A library organization and search projection

Revision ID: d2f0410a31a1
Revises: e30c06a1b2c3
Create Date: 2026-08-09 12:45:00.000000

Additive/forward strategy: original filenames, raw assets and material revisions
remain untouched.  New current profile fields are backfilled from legacy rows.
"""

from __future__ import annotations

import unicodedata

import sqlalchemy as sa

from alembic import op

revision = "d2f0410a31a1"
down_revision = "e30c06a1b2c3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    expected_tables = {
        "library_tags",
        "library_collections",
        "document_tag_assignments",
        "document_collection_assignments",
        "library_search_projections",
        "library_command_receipts",
    }
    precreated = expected_tables & set(inspector.get_table_names())
    if precreated and precreated != expected_tables:
        raise RuntimeError(f"partial precreated P1-04A schema: {sorted(precreated)}")
    existing_columns = {item["name"] for item in inspector.get_columns("user_documents")}
    if "display_title" not in existing_columns:
        op.add_column("user_documents", sa.Column("display_title", sa.String(255), nullable=True))
    if "metadata_version" not in existing_columns:
        op.add_column(
            "user_documents",
            sa.Column("metadata_version", sa.Integer(), server_default="1", nullable=False),
        )
    if "author" not in existing_columns:
        op.add_column("user_documents", sa.Column("author", sa.String(200), nullable=True))
    if "language" not in existing_columns:
        op.add_column("user_documents", sa.Column("language", sa.String(35), nullable=True))
    op.execute(
        sa.text(
            "UPDATE user_documents SET display_title = original_filename "
            "WHERE display_title IS NULL"
        )
    )
    if precreated:
        _backfill_precreated_search()
        return

    op.create_table(
        "library_tags",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("pseudonym_id", sa.String(32), sa.ForeignKey("users.pseudonym_id"), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("normalized_name", sa.String(80), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("is_archived", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("pseudonym_id", "normalized_name", name="uq_library_tag_owner_name"),
    )
    op.create_index(
        "ix_library_tags_owner_archived", "library_tags", ["pseudonym_id", "is_archived"]
    )

    op.create_table(
        "library_collections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("pseudonym_id", sa.String(32), sa.ForeignKey("users.pseudonym_id"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("normalized_name", sa.String(120), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("is_archived", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "pseudonym_id", "normalized_name", name="uq_library_collection_owner_name"
        ),
    )
    op.create_index(
        "ix_library_collections_owner_archived",
        "library_collections",
        ["pseudonym_id", "is_archived"],
    )

    op.create_table(
        "document_tag_assignments",
        sa.Column("document_id", sa.String(36), sa.ForeignKey("user_documents.id"), primary_key=True),
        sa.Column("tag_id", sa.String(36), sa.ForeignKey("library_tags.id"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "document_collection_assignments",
        sa.Column("document_id", sa.String(36), sa.ForeignKey("user_documents.id"), primary_key=True),
        sa.Column(
            "collection_id", sa.String(36), sa.ForeignKey("library_collections.id"), primary_key=True
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "library_search_projections",
        sa.Column("document_id", sa.String(36), sa.ForeignKey("user_documents.id"), primary_key=True),
        sa.Column("pseudonym_id", sa.String(32), sa.ForeignKey("users.pseudonym_id"), nullable=False),
        sa.Column("revision_id", sa.String(36), nullable=True),
        sa.Column("index_version", sa.String(50), nullable=False),
        sa.Column("normalized_title", sa.String(255), nullable=False),
        sa.Column("normalized_body", sa.Text(), server_default="", nullable=False),
        sa.Column("source_span_refs", sa.JSON(), nullable=False),
        sa.Column("freshness", sa.String(20), server_default="AVAILABLE", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_library_search_owner_title",
        "library_search_projections",
        ["pseudonym_id", "normalized_title"],
    )
    op.create_index(
        "ix_library_search_owner_freshness",
        "library_search_projections",
        ["pseudonym_id", "freshness"],
    )

    documents = sa.table(
        "user_documents",
        sa.column("id", sa.String()),
        sa.column("pseudonym_id", sa.String()),
        sa.column("original_filename", sa.String()),
        sa.column("display_title", sa.String()),
        sa.column("processing_status", sa.String()),
        sa.column("moderation_status", sa.String()),
        sa.column("moderation_details", sa.JSON()),
        sa.column("is_deleted", sa.Boolean()),
    )
    projections = sa.table(
        "library_search_projections",
        sa.column("document_id", sa.String()),
        sa.column("pseudonym_id", sa.String()),
        sa.column("revision_id", sa.String()),
        sa.column("index_version", sa.String()),
        sa.column("normalized_title", sa.String()),
        sa.column("normalized_body", sa.Text()),
        sa.column("source_span_refs", sa.JSON()),
        sa.column("freshness", sa.String()),
    )
    connection = op.get_bind()
    for row in connection.execute(sa.select(documents)):
        details = row.moderation_details if isinstance(row.moderation_details, dict) else {}
        record = details.get("content_knowledge_v1", {})
        current_id = record.get("current_revision_id")
        revision_row = next(
            (
                item
                for item in record.get("revisions", [])
                if isinstance(item, dict) and item.get("revision_id") == current_id
            ),
            None,
        )
        visible_spans = []
        if (
            revision_row
            and row.processing_status == "completed"
            and row.moderation_status != "rejected"
        ):
            visible_spans = [
                item
                for item in revision_row.get("source_spans", [])
                if isinstance(item, dict) and _learner_visible(item.get("text", ""))
            ]
        connection.execute(
            projections.insert().values(
                document_id=row.id,
                pseudonym_id=row.pseudonym_id,
                revision_id=current_id,
                index_version="library-lexical-v1",
                normalized_title=_normalize(row.display_title or row.original_filename),
                normalized_body=_normalize("\n".join(item["text"] for item in visible_spans)),
                source_span_refs=[str(item["span_id"]) for item in visible_spans],
                freshness="MISSING" if row.is_deleted else "AVAILABLE",
            )
        )

    op.create_table(
        "library_command_receipts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("pseudonym_id", sa.String(32), sa.ForeignKey("users.pseudonym_id"), nullable=False),
        sa.Column("command_type", sa.String(80), nullable=False),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("payload_digest", sa.String(64), nullable=False),
        sa.Column("result_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "pseudonym_id",
            "command_type",
            "idempotency_key",
            name="uq_library_receipt_owner_command_key",
        ),
    )


def downgrade() -> None:
    op.drop_table("library_command_receipts")
    op.drop_table("library_search_projections")
    op.drop_table("document_collection_assignments")
    op.drop_table("document_tag_assignments")
    op.drop_table("library_collections")
    op.drop_table("library_tags")
    op.drop_column("user_documents", "language")
    op.drop_column("user_documents", "author")
    op.drop_column("user_documents", "metadata_version")
    op.drop_column("user_documents", "display_title")


def _normalize(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def _learner_visible(text: str) -> bool:
    lowered = text.casefold()
    return not any(
        marker in lowered
        for marker in ("[grader-only]", "reference answer:", "参考答案：", "参考答案:")
    )


def _backfill_precreated_search() -> None:
    bind = op.get_bind()
    metadata = sa.MetaData()
    documents = sa.Table("user_documents", metadata, autoload_with=bind)
    projections = sa.Table("library_search_projections", metadata, autoload_with=bind)
    existing = set(bind.execute(sa.select(projections.c.document_id)).scalars())
    for row in bind.execute(sa.select(documents)).mappings():
        if row["id"] in existing:
            continue
        details = row["moderation_details"] if isinstance(row["moderation_details"], dict) else {}
        record = details.get("content_knowledge_v1", {})
        current_id = record.get("current_revision_id")
        revision_row = next(
            (
                item
                for item in record.get("revisions", [])
                if isinstance(item, dict) and item.get("revision_id") == current_id
            ),
            None,
        )
        visible_spans = []
        if (
            revision_row
            and row["processing_status"] == "completed"
            and row["moderation_status"] != "rejected"
        ):
            visible_spans = [
                item
                for item in revision_row.get("source_spans", [])
                if isinstance(item, dict) and _learner_visible(item.get("text", ""))
            ]
        bind.execute(
            projections.insert().values(
                document_id=row["id"],
                pseudonym_id=row["pseudonym_id"],
                revision_id=current_id,
                index_version="library-lexical-v1",
                normalized_title=_normalize(row["display_title"] or row["original_filename"]),
                normalized_body=_normalize("\n".join(item["text"] for item in visible_spans)),
                source_span_refs=[str(item["span_id"]) for item in visible_spans],
                freshness="MISSING" if row["is_deleted"] else "AVAILABLE",
            )
        )

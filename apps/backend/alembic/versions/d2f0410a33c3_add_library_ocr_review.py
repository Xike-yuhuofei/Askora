"""add P1-04C durable OCR candidate and review records

Revision ID: d2f0410a33c3
Revises: d2f0410a32b2
Create Date: 2026-08-09 12:47:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "d2f0410a33c3"
down_revision = "d2f0410a32b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    existing_tables = set(sa.inspect(op.get_bind()).get_table_names())
    ocr_tables = {"document_ocr_runs", "document_ocr_candidates"}
    precreated = existing_tables & ocr_tables
    if precreated:
        if precreated != ocr_tables:
            raise RuntimeError(f"partial precreated P1-04C schema: {sorted(precreated)}")
        return
    op.create_table(
        "document_ocr_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("user_documents.id"), nullable=False),
        sa.Column("pseudonym_id", sa.String(32), sa.ForeignKey("users.pseudonym_id"), nullable=False),
        sa.Column("input_revision_id", sa.String(36), nullable=True),
        sa.Column("raw_checksum", sa.String(64), nullable=False),
        sa.Column("engine", sa.String(50), nullable=False),
        sa.Column("engine_version", sa.String(100), nullable=False),
        sa.Column("languages", sa.JSON(), nullable=False),
        sa.Column("policy_version", sa.String(50), nullable=False),
        sa.Column("status", sa.String(30), server_default="pending", nullable=False),
        sa.Column("page_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("candidate_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("reason_codes", sa.JSON(), nullable=False),
        sa.Column("error_code", sa.String(100), nullable=True),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("pseudonym_id", "idempotency_key", name="uq_ocr_run_owner_key"),
    )
    op.create_index(
        "ix_document_ocr_runs_document_status", "document_ocr_runs", ["document_id", "status"]
    )
    op.create_table(
        "document_ocr_candidates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), sa.ForeignKey("document_ocr_runs.id"), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("block_index", sa.Integer(), nullable=False),
        sa.Column("bbox", sa.JSON(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("image_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), server_default="candidate", nullable=False),
        sa.Column("corrected_text", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("run_id", "page_number", "block_index", name="uq_ocr_run_page_block"),
    )
    op.create_index(
        "ix_document_ocr_candidates_run_status",
        "document_ocr_candidates",
        ["run_id", "status"],
    )


def downgrade() -> None:
    op.drop_table("document_ocr_candidates")
    op.drop_table("document_ocr_runs")

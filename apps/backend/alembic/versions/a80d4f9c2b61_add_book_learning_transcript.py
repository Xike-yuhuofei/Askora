"""add SYS08 book learning transcript projection

Revision ID: a80d4f9c2b61
Revises: 9b4c2d7e1a60
Create Date: 2026-08-08
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a80d4f9c2b61"
down_revision: str | None = "9b4c2d7e1a60"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _assert_compatible_existing_table(
    table_name: str,
    *,
    required_columns: set[str],
    required_unique_constraints: set[str],
) -> None:
    """Fail closed when app startup created a table that does not match this revision."""
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns(table_name)}
    unique_constraints = {
        constraint["name"]
        for constraint in inspector.get_unique_constraints(table_name)
        if constraint.get("name")
    }
    missing_columns = required_columns - columns
    missing_constraints = required_unique_constraints - unique_constraints
    if missing_columns or missing_constraints:
        raise RuntimeError(
            f"existing {table_name} is incompatible with {revision}: "
            f"missing columns={sorted(missing_columns)}, "
            f"missing unique constraints={sorted(missing_constraints)}"
        )


def _ensure_index(table_name: str, index_name: str, columns: list[str]) -> None:
    inspector = sa.inspect(op.get_bind())
    existing = {index["name"] for index in inspector.get_indexes(table_name)}
    if index_name not in existing:
        op.create_index(index_name, table_name, columns, unique=False)


def upgrade() -> None:
    existing_tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "book_learning_advance_records" not in existing_tables:
        op.create_table(
            "book_learning_advance_records",
            sa.Column("advance_record_id", sa.String(length=36), nullable=False),
            sa.Column("schema_version", sa.String(length=20), nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("document_id", sa.String(length=36), nullable=False),
            sa.Column("idempotency_key", sa.String(length=200), nullable=False),
            sa.Column("applied_command", sa.String(length=80), nullable=False),
            sa.Column("response_payload", sa.JSON(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("advance_record_id"),
            sa.UniqueConstraint(
                "user_id",
                "idempotency_key",
                name="uq_book_advance_user_idempotency",
            ),
        )
    else:
        _assert_compatible_existing_table(
            "book_learning_advance_records",
            required_columns={
                "advance_record_id",
                "schema_version",
                "user_id",
                "document_id",
                "idempotency_key",
                "applied_command",
                "response_payload",
                "created_at",
            },
            required_unique_constraints={"uq_book_advance_user_idempotency"},
        )
    _ensure_index(
        "book_learning_advance_records",
        "ix_book_advance_user_document",
        ["user_id", "document_id"],
    )
    for column in ("document_id", "user_id"):
        _ensure_index(
            "book_learning_advance_records",
            f"ix_book_learning_advance_records_{column}",
            [column],
        )

    if "book_learning_transcript_turns" not in existing_tables:
        op.create_table(
            "book_learning_transcript_turns",
            sa.Column("turn_record_id", sa.String(length=36), nullable=False),
            sa.Column("schema_version", sa.String(length=20), nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("goal_id", sa.String(length=36), nullable=False),
            sa.Column("plan_id", sa.String(length=36), nullable=False),
            sa.Column("plan_version", sa.Integer(), nullable=False),
            sa.Column("activity_id", sa.String(length=36), nullable=False),
            sa.Column("session_id", sa.String(length=36), nullable=False),
            sa.Column("turn_id", sa.String(length=200), nullable=False),
            sa.Column("turn_number", sa.Integer(), nullable=False),
            sa.Column("turn_kind", sa.String(length=32), nullable=False),
            sa.Column("idempotency_key", sa.String(length=200), nullable=False),
            sa.Column("learner_text", sa.Text(), nullable=True),
            sa.Column("response_payload", sa.JSON(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("turn_record_id"),
            sa.UniqueConstraint(
                "session_id",
                "turn_id",
                name="uq_book_transcript_session_turn_id",
            ),
            sa.UniqueConstraint(
                "session_id",
                "turn_number",
                name="uq_book_transcript_session_turn_number",
            ),
            sa.UniqueConstraint(
                "user_id",
                "idempotency_key",
                name="uq_book_transcript_user_idempotency",
            ),
        )
    else:
        _assert_compatible_existing_table(
            "book_learning_transcript_turns",
            required_columns={
                "turn_record_id",
                "schema_version",
                "user_id",
                "goal_id",
                "plan_id",
                "plan_version",
                "activity_id",
                "session_id",
                "turn_id",
                "turn_number",
                "turn_kind",
                "idempotency_key",
                "learner_text",
                "response_payload",
                "created_at",
            },
            required_unique_constraints={
                "uq_book_transcript_session_turn_id",
                "uq_book_transcript_session_turn_number",
                "uq_book_transcript_user_idempotency",
            },
        )
    _ensure_index(
        "book_learning_transcript_turns",
        "ix_book_transcript_user_activity_turn",
        ["user_id", "activity_id", "turn_number"],
    )
    for column in ("activity_id", "goal_id", "plan_id", "session_id", "user_id"):
        _ensure_index(
            "book_learning_transcript_turns",
            f"ix_book_learning_transcript_turns_{column}",
            [column],
        )


def downgrade() -> None:
    for column in ("user_id", "session_id", "plan_id", "goal_id", "activity_id"):
        op.drop_index(
            f"ix_book_learning_transcript_turns_{column}",
            table_name="book_learning_transcript_turns",
        )
    op.drop_index(
        "ix_book_transcript_user_activity_turn",
        table_name="book_learning_transcript_turns",
    )
    op.drop_table("book_learning_transcript_turns")
    for column in ("user_id", "document_id"):
        op.drop_index(
            f"ix_book_learning_advance_records_{column}",
            table_name="book_learning_advance_records",
        )
    op.drop_index(
        "ix_book_advance_user_document",
        table_name="book_learning_advance_records",
    )
    op.drop_table("book_learning_advance_records")

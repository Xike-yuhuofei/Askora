"""Add workspace_id to learner evidence / mastery / learner-state / review / assessment records (XIK-177 / EXEC-062)

Additive, non-destructive migration implementing WSP-030..WSP-035:

- adds a nullable ``workspace_id`` attribution column to the owner-global
  learner and assessment / review tables so legacy data can be backfilled
  deterministically into the default Workspace (application-layer bootstrap,
  same as XIK-171);
- makes the canonical mastery version uniqueness key Workspace-scoped so two
  Workspaces can keep independent version histories for the same
  (user, knowledge_unit) pair;
- replaces the legacy owner-global UNIQUE INDEX on assessment attempt
  ``idempotency_key`` and learner ``source_result_id`` with a Workspace-scoped
  compound unique constraint, and reinstates a matching non-unique index so the
  migrated schema matches ``Base.metadata.create_all`` (``alembic check`` clean);
- adds Workspace-scoped query indexes.

The migration is additive-first and idempotent: every ADD COLUMN / ADD INDEX /
constraint change is guarded so it also succeeds when the schema was already
materialised by ``Base.metadata.create_all`` at application startup. Backfill of
the default Workspace happens in the application bootstrap/service layer, not
here. No NOT NULL is added to existing columns, no data is rewritten and no
stable evidence/estimate/state ID is regenerated.

Revision ID: x062d0e0a001
Revises: w171d0e0a001
Create Date: 2026-08-10 23:30:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "x062d0e0a001"
down_revision: str | None = "w171d0e0a001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: Tables that gain a nullable workspace attribution column.
_WORKSPACE_ATTRIBUTION_TABLES = [
    "learner_evidence",
    "canonical_mastery_estimate_versions",
    "learner_state_versions",
    "review_schedule_versions",
    "review_observations",
    "canonical_assessment_attempts",
    "canonical_assessment_result_versions",
]

_MASTERY_TABLE = "canonical_mastery_estimate_versions"
_MASTERY_CONSTRAINT = "uq_canonical_mastery_version"
_MASTERY_WS_COLS = ["workspace_id", "user_id", "knowledge_unit_id", "version"]
_MASTERY_OWNER_COLS = ["user_id", "knowledge_unit_id", "version"]

#: ``review_schedule_versions.idx_review_latest`` gains the Workspace column so
#: the "latest review per unit" query is Workspace-isolated (WSP-035).
_REVIEW_INDEX_TABLE = "review_schedule_versions"
_REVIEW_INDEX_NAME = "idx_review_latest"
_REVIEW_INDEX_WS_COLS = ["workspace_id", "user_id", "knowledge_unit_id", "version"]
_REVIEW_INDEX_OWNER_COLS = ["user_id", "knowledge_unit_id", "version"]

#: Owner-global UNIQUE INDEX -> Workspace-scoped compound unique constraint swaps.
#: Each entry carries the index name to drop, the workspace-scoped constraint to
#: create, the compound column set, and the column(s) to reinstate as a plain
#: (non-unique) index so the result matches ``create_all``.
_UNIQUE_INDEX_REBASES = [
    {
        "table": "canonical_assessment_attempts",
        "index_name": "ix_canonical_assessment_attempts_idempotency_key",
        "constraint": "uq_canonical_attempt_workspace_idempotency",
        "new_cols": ["workspace_id", "idempotency_key"],
        "keep_index_cols": ["idempotency_key"],
    },
    {
        "table": "learner_evidence",
        "index_name": "ix_learner_evidence_source_result_id",
        "constraint": "uq_learner_evidence_workspace_source_result",
        "new_cols": ["workspace_id", "source_result_id"],
        "keep_index_cols": ["source_result_id"],
    },
]


def _existing_tables(bind) -> set[str]:
    return {t for t in sa.inspect(bind).get_table_names()}


def _existing_columns(bind, table: str) -> set[str]:
    if table not in _existing_tables(bind):
        return set()
    return {c["name"] for c in sa.inspect(bind).get_columns(table)}


def _existing_indexes(bind, table: str) -> set[str]:
    if table not in _existing_tables(bind):
        return set()
    return {i["name"] for i in sa.inspect(bind).get_indexes(table)}


def _unique_constraint_col_sets(bind, table: str) -> list[list[str]]:
    if table not in _existing_tables(bind):
        return []
    return [
        sorted(c["column_names"] or [])
        for c in sa.inspect(bind).get_unique_constraints(table)
    ]


def _unique_index_names(bind, table: str) -> set[str]:
    if table not in _existing_tables(bind):
        return set()
    return {i["name"] for i in sa.inspect(bind).get_indexes(table) if i.get("unique")}


def _index_col_sets(bind, table: str) -> dict[str, list[str]]:
    if table not in _existing_tables(bind):
        return {}
    return {i["name"]: sorted(i["column_names"] or []) for i in sa.inspect(bind).get_indexes(table)}


def _add_index_guarded(index_name: str, table: str, *columns, **kwargs) -> None:
    bind = op.get_bind()
    if index_name in _existing_indexes(bind, table):
        return
    op.create_index(index_name, table, list(columns), **kwargs)


def _add_column_guarded(table: str, column: sa.Column) -> None:
    bind = op.get_bind()
    if column.name in _existing_columns(bind, table):
        return
    op.add_column(table, column)


def _rebase_owner_unique_index_to_workspace(*, spec: dict) -> None:
    """Replace a legacy owner-global UNIQUE INDEX with a Workspace-scoped
    compound unique constraint on SQLite (batch table rebuild), then reinstate
    a non-unique index on the original column(s) so the final schema matches
    ``Base.metadata.create_all``. No-op when already scoped or not present."""
    bind = op.get_bind()
    table = spec["table"]
    index_name = spec["index_name"]
    constraint = spec["constraint"]
    new_cols = spec["new_cols"]
    keep_index_cols = spec["keep_index_cols"]

    if table not in _existing_tables(bind):
        return
    if sorted(new_cols) in _unique_constraint_col_sets(bind, table):
        return
    if index_name not in _unique_index_names(bind, table):
        return

    with op.batch_alter_table(table) as batch:
        batch.drop_index(index_name)
        batch.create_unique_constraint(constraint, new_cols)
    # Reinstate the original column(s) as a plain (non-unique) index to mirror
    # the model's ``index=True`` columns.
    _add_index_guarded(index_name, table, *keep_index_cols)


def upgrade() -> None:
    bind = op.get_bind()

    for table in _WORKSPACE_ATTRIBUTION_TABLES:
        _add_column_guarded(
            table,
            sa.Column(
                "workspace_id",
                sa.String(length=36),
                nullable=True,
                server_default=sa.null(),
            ),
        )
        _add_index_guarded(f"ix_{table}_workspace_id", table, "workspace_id")

    # Rebuild review_schedule_versions.idx_review_latest to include workspace_id
    # so the "latest review per unit" query index is Workspace-isolated.
    _col_sets = _index_col_sets(bind, _REVIEW_INDEX_TABLE)
    _cur = _col_sets.get(_REVIEW_INDEX_NAME)
    if _cur == sorted(_REVIEW_INDEX_OWNER_COLS):
        op.drop_index(_REVIEW_INDEX_NAME, table_name=_REVIEW_INDEX_TABLE)
        op.create_index(_REVIEW_INDEX_NAME, _REVIEW_INDEX_TABLE, _REVIEW_INDEX_WS_COLS)

    # Make the canonical mastery version uniqueness key Workspace-scoped.
    # SQLite cannot ALTER a unique constraint in place, so a batch (table
    # rebuild) is required when the old owner-global constraint is present.
    if _MASTERY_TABLE in _existing_tables(bind):
        col_sets = _unique_constraint_col_sets(bind, _MASTERY_TABLE)
        needs_rebuild = sorted(_MASTERY_OWNER_COLS) in col_sets and sorted(
            _MASTERY_WS_COLS
        ) not in col_sets
        if needs_rebuild:
            with op.batch_alter_table(_MASTERY_TABLE) as batch:
                batch.drop_constraint(_MASTERY_CONSTRAINT, type_="unique")
                batch.create_unique_constraint(_MASTERY_CONSTRAINT, _MASTERY_WS_COLS)

    # Rebase legacy owner-global attempt-idempotency and evidence-source-result
    # UNIQUE INDEXes into Workspace-scoped compound keys.
    for spec in _UNIQUE_INDEX_REBASES:
        _rebase_owner_unique_index_to_workspace(spec=spec)


def _restore_owner_unique_index(*, spec: dict) -> None:
    """Reverse a Workspace-scoped compound unique into the legacy owner-global
    UNIQUE INDEX (used by downgrade). No-op when already in legacy form."""
    bind = op.get_bind()
    table = spec["table"]
    index_name = spec["index_name"]
    constraint = spec["constraint"]
    new_cols = spec["new_cols"]
    keep_index_cols = spec["keep_index_cols"]

    if table not in _existing_tables(bind):
        return
    if sorted(new_cols) not in _unique_constraint_col_sets(bind, table):
        return
    with op.batch_alter_table(table) as batch:
        batch.drop_constraint(constraint, type_="unique")
        batch.drop_index(index_name)
        batch.create_index(index_name, keep_index_cols, unique=True)


def downgrade() -> None:
    op.drop_index("ix_review_observations_workspace_id", table_name="review_observations")
    op.drop_column("review_observations", "workspace_id")
    _col_sets = _index_col_sets(op.get_bind(), _REVIEW_INDEX_TABLE)
    if _col_sets.get(_REVIEW_INDEX_NAME) == sorted(_REVIEW_INDEX_WS_COLS):
        op.drop_index(_REVIEW_INDEX_NAME, table_name=_REVIEW_INDEX_TABLE)
        op.create_index(_REVIEW_INDEX_NAME, _REVIEW_INDEX_TABLE, _REVIEW_INDEX_OWNER_COLS)
    op.drop_index("ix_review_schedule_versions_workspace_id", table_name="review_schedule_versions")
    op.drop_column("review_schedule_versions", "workspace_id")
    op.drop_index(
        "ix_canonical_assessment_result_versions_workspace_id",
        table_name="canonical_assessment_result_versions",
    )
    op.drop_column("canonical_assessment_result_versions", "workspace_id")
    op.drop_index(
        "ix_canonical_assessment_attempts_workspace_id", table_name="canonical_assessment_attempts"
    )
    # Restore the legacy owner-global attempt idempotency unique index.
    if sorted(_UNIQUE_INDEX_REBASES[0]["new_cols"]) in _unique_constraint_col_sets(
        op.get_bind(), _UNIQUE_INDEX_REBASES[0]["table"]
    ):
        _restore_owner_unique_index(spec=_UNIQUE_INDEX_REBASES[0])
    op.drop_column("canonical_assessment_attempts", "workspace_id")
    op.drop_index("ix_learner_state_versions_workspace_id", table_name="learner_state_versions")
    op.drop_column("learner_state_versions", "workspace_id")
    op.drop_index("ix_learner_evidence_workspace_id", table_name="learner_evidence")
    # Restore the legacy owner-global evidence source-result unique index.
    if sorted(_UNIQUE_INDEX_REBASES[1]["new_cols"]) in _unique_constraint_col_sets(
        op.get_bind(), _UNIQUE_INDEX_REBASES[1]["table"]
    ):
        _restore_owner_unique_index(spec=_UNIQUE_INDEX_REBASES[1])
    op.drop_column("learner_evidence", "workspace_id")
    # Mastery: restore the owner-global unique constraint via batch rebuild.
    with op.batch_alter_table(_MASTERY_TABLE) as batch:
        batch.drop_constraint(_MASTERY_CONSTRAINT, type_="unique")
        batch.create_unique_constraint(_MASTERY_CONSTRAINT, _MASTERY_OWNER_COLS)
    op.drop_index(
        "ix_canonical_mastery_estimate_versions_workspace_id",
        table_name=_MASTERY_TABLE,
    )
    op.drop_column(_MASTERY_TABLE, "workspace_id")

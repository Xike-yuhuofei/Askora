"""Reconcile redundant Workspace membership uniqueness constraints.

``project_materials`` and ``learning_session_materials`` already use their
membership column pairs as composite primary keys.  The same-column named
UNIQUE constraints created by ``w171d0e0a001`` are therefore redundant.  Some
PostgreSQL reflection/autogenerate paths expose those constraints separately,
which leaves a fresh migrated database different from canonical ORM metadata.

This forward-fix removes only the redundant physical constraints.  Composite
primary keys, foreign keys, indexes, rows and WSP-012/WSP-013 semantics remain
unchanged.  Historical migrations stay immutable.

Revision ID: w171r0e0a002
Revises: x174e0e0a002
Create Date: 2026-08-11 12:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "w171r0e0a002"
down_revision: str | None = "x174e0e0a002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_REDUNDANT_CONSTRAINTS = (
    ("project_materials", "uq_project_material", ["project_id", "material_id"]),
    (
        "learning_session_materials",
        "uq_learning_session_material",
        ["session_id", "material_id"],
    ),
)


def _unique_constraint_names(bind: sa.engine.Connection, table_name: str) -> set[str]:
    try:
        constraints = sa.inspect(bind).get_unique_constraints(table_name)
    except sa.exc.NoSuchTableError:
        return set()
    return {
        str(constraint["name"])
        for constraint in constraints
        if constraint.get("name") is not None
    }


def _drop_unique_constraint(table_name: str, constraint_name: str) -> None:
    bind = op.get_bind()
    if constraint_name not in _unique_constraint_names(bind, table_name):
        return
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.drop_constraint(constraint_name, type_="unique")
        return
    op.drop_constraint(constraint_name, table_name, type_="unique")


def _create_unique_constraint(
    table_name: str, constraint_name: str, columns: list[str]
) -> None:
    bind = op.get_bind()
    if constraint_name in _unique_constraint_names(bind, table_name):
        return
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.create_unique_constraint(constraint_name, columns)
        return
    op.create_unique_constraint(constraint_name, table_name, columns)


def upgrade() -> None:
    for table_name, constraint_name, _columns in _REDUNDANT_CONSTRAINTS:
        _drop_unique_constraint(table_name, constraint_name)


def downgrade() -> None:
    for table_name, constraint_name, columns in _REDUNDANT_CONSTRAINTS:
        _create_unique_constraint(table_name, constraint_name, columns)

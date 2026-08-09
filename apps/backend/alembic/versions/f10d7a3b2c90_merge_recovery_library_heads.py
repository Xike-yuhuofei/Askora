"""merge P1-07 recovery and P1-04 library migration heads

Revision ID: f10d7a3b2c90
Revises: c71e5a2d9f40, d2f0410a33c3
Create Date: 2026-08-09 14:00:00.000000

This no-op revision records that both additive owner migrations are required.
Downgrade only removes the merge marker; each owner branch retains its own
forward-fix and rollback semantics.
"""

from __future__ import annotations

from collections.abc import Sequence

revision: str = "f10d7a3b2c90"
down_revision: tuple[str, str] = ("c71e5a2d9f40", "d2f0410a33c3")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Merge two already-applied additive branches without changing schema."""


def downgrade() -> None:
    """Remove only the merge marker and expose the two owner heads again."""

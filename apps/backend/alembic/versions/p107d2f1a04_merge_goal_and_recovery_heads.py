"""merge goal-management and P1-07 recovery integration heads

Revision ID: p107d2f1a04
Revises: p107f36c1a03, d2f1010b38b2
Create Date: 2026-08-09 20:45:00.000000

This revision reconciles independently merged P1-01 goal-management and
P1-07 recovery histories. It creates or removes no schema objects.
"""

from __future__ import annotations

from collections.abc import Sequence

revision: str = "p107d2f1a04"
down_revision: tuple[str, str] = ("p107f36c1a03", "d2f1010b38b2")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

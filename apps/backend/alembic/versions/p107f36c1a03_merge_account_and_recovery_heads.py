"""merge account lifecycle and P1-07 recovery integration heads

Revision ID: p107f36c1a03
Revises: p107f1061a02, f36c91b807d3
Create Date: 2026-08-09 19:30:00.000000

This revision reconciles independently merged account-lifecycle and P1-07
recovery histories. It creates or removes no schema objects.
"""

from __future__ import annotations

from collections.abc import Sequence

revision: str = "p107f36c1a03"
down_revision: tuple[str, str] = ("p107f1061a02", "f36c91b807d3")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

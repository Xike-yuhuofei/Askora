"""merge onboarding and P1-07 recovery integration heads

Revision ID: p107f1061a02
Revises: m103f1061a01, p103c5a0d003
Create Date: 2026-08-09 18:30:00.000000

This revision reconciles independently merged onboarding/data-control and
P1-07 recovery histories. It creates or removes no schema objects.
"""

from __future__ import annotations

from collections.abc import Sequence

revision: str = "p107f1061a02"
down_revision: tuple[str, str] = ("m103f1061a01", "p103c5a0d003")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

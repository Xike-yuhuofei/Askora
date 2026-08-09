"""merge P1-03 data control with the P1-07/library migration head

Revision ID: p103m4a8c002
Revises: f10d7a3b2c90, p103d4c0e001
Create Date: 2026-08-09 14:46:00.000000

This revision changes no data. It preserves both independently governed
histories while restoring the single-head upgrade contract.
"""

from __future__ import annotations

revision = "p103m4a8c002"
down_revision = ("f10d7a3b2c90", "p103d4c0e001")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

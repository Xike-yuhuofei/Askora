"""Stable error contract shared by the Web data-control maintenance boundary."""

from __future__ import annotations

from app.contracts.data_control import DataControlErrorCode


class RecoveryError(RuntimeError):
    """Stable, non-sensitive failure surfaced by the maintenance boundary."""

    def __init__(self, code: DataControlErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

"""Injectable time source for deterministic delayed/review transitions."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol


class TimeSource(Protocol):
    def now(self) -> datetime: ...


class FixedTimeSource:
    def __init__(self, value: datetime) -> None:
        if value.utcoffset() is None:
            raise ValueError("fixed policy time must be timezone-aware")
        self._value = value

    def now(self) -> datetime:
        return self._value

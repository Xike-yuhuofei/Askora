"""Sanitized one-line diagnostics for the Electron bootstrap boundary."""

from __future__ import annotations

import json
import sys
from typing import Literal

from sqlalchemy.exc import IntegrityError, OperationalError

STARTUP_DIAGNOSTIC_PREFIX = "ASKORA_STARTUP_DIAGNOSTIC "


class DatabaseMigrationRequiredError(RuntimeError):
    """Raised by migration compatibility gates before normal readiness."""


def classify_database_startup_error(exc: BaseException) -> tuple[str, bool]:
    if isinstance(exc, DatabaseMigrationRequiredError):
        return "BOOTSTRAP_DATABASE_MIGRATION_REQUIRED", True
    if isinstance(exc, IntegrityError):
        return "BOOTSTRAP_DATABASE_INTEGRITY_FAILED", False
    if isinstance(exc, OperationalError):
        return "BOOTSTRAP_DATABASE_UNAVAILABLE", True
    return "BOOTSTRAP_DATABASE_UNAVAILABLE", True


def emit_startup_diagnostic(
    code: str,
    *,
    retryable: bool,
    data_safety: Literal["preserved", "unknown"] = "unknown",
) -> None:
    """Emit only allowlisted fields; never include paths, SQL, secrets or traceback."""
    payload = {
        "schema_version": "1.0",
        "code": code,
        "retryable": retryable,
        "data_safety": data_safety,
    }
    print(
        f"{STARTUP_DIAGNOSTIC_PREFIX}{json.dumps(payload, separators=(',', ':'))}",
        file=sys.stderr,
        flush=True,
    )

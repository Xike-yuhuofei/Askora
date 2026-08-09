"""Electron startup channel is strict and secret-free."""

import json

from sqlalchemy.exc import OperationalError

from app.core.startup_diagnostics import (
    STARTUP_DIAGNOSTIC_PREFIX,
    DatabaseMigrationRequiredError,
    classify_database_startup_error,
    emit_startup_diagnostic,
)


def test_database_startup_errors_are_typed() -> None:
    assert classify_database_startup_error(DatabaseMigrationRequiredError()) == (
        "BOOTSTRAP_DATABASE_MIGRATION_REQUIRED",
        True,
    )
    operational = OperationalError("select", {"password": "secret"}, RuntimeError("down"))
    assert classify_database_startup_error(operational) == (
        "BOOTSTRAP_DATABASE_UNAVAILABLE",
        True,
    )


def test_startup_diagnostic_emits_only_allowlisted_fields(capsys) -> None:
    emit_startup_diagnostic("BOOTSTRAP_DATABASE_UNAVAILABLE", retryable=True, data_safety="unknown")
    output = capsys.readouterr().err.strip()
    assert output.startswith(STARTUP_DIAGNOSTIC_PREFIX)
    assert json.loads(output.removeprefix(STARTUP_DIAGNOSTIC_PREFIX)) == {
        "schema_version": "1.0",
        "code": "BOOTSTRAP_DATABASE_UNAVAILABLE",
        "retryable": True,
        "data_safety": "unknown",
    }
    assert "/Users/" not in output
    assert "password" not in output

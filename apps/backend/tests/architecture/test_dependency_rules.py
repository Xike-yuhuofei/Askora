from __future__ import annotations

from pathlib import Path

from tests.architecture.import_rules import (
    LEGACY_ALLOWLIST,
    inspect_imports,
    partition_allowlisted,
)

APP_ROOT = Path(__file__).resolve().parents[2] / "app"


def test_no_unallowlisted_cross_owner_or_adapter_imports() -> None:
    """DEP-003/023/050/051 and EXEC001-AC-006."""
    violations = inspect_imports(APP_ROOT)
    unexpected, allowed = partition_allowlisted(violations)

    assert unexpected == [], "\n".join(
        f"{item.rule}: {item.path}:{item.line} imports {item.module}" for item in unexpected
    )
    assert {item.key for item in allowed} == {item.key for item in LEGACY_ALLOWLIST}
    assert all(item.todo_owner and item.removal_exec for item in LEGACY_ALLOWLIST)


def test_deliberate_assessment_violation_fixture_is_reported(tmp_path) -> None:
    """TEST-AC-005: the AST rule demonstrably fails on a prohibited import."""
    app_root = tmp_path / "app"
    fixture = app_root / "services" / "assessment" / "fixture.py"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        "from app.services.kt.knowledge_tracing_service import get_kt_service\n",
        encoding="utf-8",
    )

    violations = inspect_imports(app_root)

    assert len(violations) == 1
    assert violations[0].rule == "ASSESSMENT_NO_LEARNER_WRITE"
    assert violations[0].path == "app/services/assessment/fixture.py"


def test_deliberate_contract_sdk_violation_fixture_is_reported(tmp_path) -> None:
    """DEP-003: contracts cannot depend on Redis/provider adapters."""
    app_root = tmp_path / "app"
    fixture = app_root / "contracts" / "fixture.py"
    fixture.parent.mkdir(parents=True)
    fixture.write_text("import redis\n", encoding="utf-8")

    violations = inspect_imports(app_root)

    assert len(violations) == 1
    assert violations[0].rule == "DOMAIN_CONTRACTS_NO_ADAPTER_SDK"

"""API → canonical query/read-model boundary regression (EXEC-007 T2)."""

from __future__ import annotations

from pathlib import Path

from tests.architecture.import_rules import LEGACY_ALLOWLIST, inspect_imports

APP_ROOT = Path(__file__).resolve().parents[2] / "app"


def test_users_api_no_longer_imports_legacy_profile_orm() -> None:
    """EXEC007-AC-001/003: GET /users/profile must not import UserProfile ORM."""
    source = (APP_ROOT / "api" / "v1" / "users.py").read_text(encoding="utf-8")
    assert "app.models.profile" not in source
    assert "app.queries.profile" in source

    violations = inspect_imports(APP_ROOT)
    assert not any(
        violation.rule == "API_NO_LEARNER_PERSISTENCE"
        and violation.module == "app.models.profile"
        for violation in violations
    )


def test_api_direct_learner_persistence_read_is_blocked(tmp_path) -> None:
    """EXEC007-AC-003: AST rule blocks restoring a direct API learner read."""
    app_root = tmp_path / "app"
    fixture = app_root / "api" / "v1" / "users_fixture.py"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(
        "from app.models.profile import UserProfile\n",
        encoding="utf-8",
    )

    violations = inspect_imports(app_root)

    assert len(violations) == 1
    assert violations[0].rule == "API_NO_LEARNER_PERSISTENCE"
    assert violations[0].module == "app.models.profile"


def test_api_no_learner_persistence_allowance_remains() -> None:
    """EXEC007-AC-003: API_NO_LEARNER_PERSISTENCE allowance is fully retired."""
    assert not any(
        item.rule == "API_NO_LEARNER_PERSISTENCE" for item in LEGACY_ALLOWLIST
    )
"""EXEC-007 CI evidence contract regression (v2: Required/Optional split)."""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
REQUIRED_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci-required.yml"
OPTIONAL_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci-optional.yml"


def _commands(job: dict) -> str:
    return "\n".join(step.get("run", "") for step in job["steps"])


def test_exec007_required_workflow_is_persistent_and_independently_auditable() -> None:
    """EXEC007-AC-005/006: Required gates are durable GitHub checks."""
    workflow = yaml.safe_load(REQUIRED_WORKFLOW.read_text(encoding="utf-8"))
    jobs = workflow["jobs"]

    expected_names = {
        "documentation": "Documentation links",
        "backend-tests": "Backend tests",
        "backend-quality": "Code quality",
        "backend-migration": "Migration validation",
        "frontend": "Frontend test & build",
        "dependency-audit": "Dependency audit",
    }
    assert {job: jobs[job]["name"] for job in expected_names} == expected_names

    backend_test_commands = _commands(jobs["backend-tests"])
    assert "uv run pytest tests/ -m required" in backend_test_commands
    assert "--cov-fail-under" not in backend_test_commands

    quality_commands = _commands(jobs["backend-quality"])
    assert "uv run ruff check" in quality_commands
    assert "uv run black --check" in quality_commands
    assert "uv run mypy app --no-error-summary" in quality_commands

    migration_commands = _commands(jobs["backend-migration"])
    assert "uv run alembic upgrade head" in migration_commands
    assert "uv run alembic check" in migration_commands
    assert "uv run alembic downgrade base" in migration_commands

    assert "npm run build" in _commands(jobs["frontend"])

    required_needs = {
        "documentation",
        "backend-tests",
        "backend-quality",
        "backend-migration",
        "frontend",
        "dependency-audit",
    }
    assert set(jobs["required-aggregate"]["needs"]) == required_needs


def test_exec007_optional_workflow_is_separate_from_required() -> None:
    """EXEC057-AC-009: Optional workflow is independent of Required."""
    workflow = yaml.safe_load(OPTIONAL_WORKFLOW.read_text(encoding="utf-8"))
    jobs = workflow["jobs"]

    expected_names = {
        "postgres-compat": "Optional / PostgreSQL compatibility",
        "container-build": "Optional / Container build",
        "py312-compat": "Optional / Python 3.12 compatibility",
    }
    assert {job: jobs[job]["name"] for job in expected_names} == expected_names

    postgres_commands = _commands(jobs["postgres-compat"])
    assert "test_postgres_decision_trace_compatibility.py" in postgres_commands

    py312_commands = _commands(jobs["py312-compat"])
    assert 'python-version: "3.12"' not in py312_commands
    # python-version is a separate input step, not in commands
    assert "uv run pytest tests/ -m required" in py312_commands


def test_exec057_required_has_no_external_runtime_dependencies() -> None:
    """EXEC057-AC-008: Required workflow has no Redis/Postgres/Docker/AI key."""
    workflow = yaml.safe_load(REQUIRED_WORKFLOW.read_text(encoding="utf-8"))

    workflow_text = REQUIRED_WORKFLOW.read_text(encoding="utf-8")

    assert "redis" not in workflow_text.lower()
    assert "postgres" not in workflow_text.lower()
    assert "docker" not in workflow_text.lower()
    assert "redis_url" not in workflow_text.lower()
    assert "postgres" not in workflow.get("jobs", {})


def test_exec057_required_uses_sqlite_only() -> None:
    """EXEC057-AC-008: Required workflow uses SQLite only."""
    workflow_text = REQUIRED_WORKFLOW.read_text(encoding="utf-8")

    assert "sqlite+aiosqlite" in workflow_text
    assert "DATABASE_URL" in workflow_text
    assert "sqlite" in workflow_text.lower()

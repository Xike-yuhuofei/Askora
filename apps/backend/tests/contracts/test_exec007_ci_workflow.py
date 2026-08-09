"""EXEC-007 CI evidence contract regression."""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def _commands(job: dict) -> str:
    return "\n".join(step.get("run", "") for step in job["steps"])


def test_exec007_ci_jobs_are_persistent_and_independently_auditable() -> None:
    """EXEC007-AC-005/006: required gates are durable GitHub checks."""
    workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    jobs = workflow["jobs"]

    expected_names = {
        "backend-tests": "Backend tests / Python ${{ matrix.python-version }}",
        "backend-quality": (
            "Ruff, formatting and type baseline / Python ${{ matrix.python-version }}"
        ),
        "alembic": "Alembic migration validation",
        "backend-postgres-contract": "PostgreSQL persistence contract",
        "frontend": "Frontend build",
        "frontend-dependency-audit": "Frontend dependency audit",
        "dependency-audit": "Python dependency audit",
    }
    assert {job: jobs[job]["name"] for job in expected_names} == expected_names

    backend_test_commands = _commands(jobs["backend-tests"])
    assert "uv run pytest tests" in backend_test_commands
    assert "--cov-fail-under=45" in backend_test_commands

    quality_commands = _commands(jobs["backend-quality"])
    assert "uv run ruff check" in quality_commands
    assert "uv run python ../../.github/workflows/check_black_baseline.py" in quality_commands
    assert "uv run mypy app --no-error-summary" in quality_commands

    alembic_commands = _commands(jobs["alembic"])
    assert "uv run alembic upgrade head" in alembic_commands
    assert "uv run alembic check" in alembic_commands
    assert "uv run alembic downgrade base" in alembic_commands

    postgres_commands = _commands(jobs["backend-postgres-contract"])
    assert "uv run alembic upgrade head" in postgres_commands
    assert "test_postgres_decision_trace_compatibility.py" in postgres_commands

    assert "npm run build" in _commands(jobs["frontend"])
    assert "npm audit --audit-level=high" in _commands(jobs["frontend-dependency-audit"])
    assert "uv run pip-audit --progress-spinner=off" in _commands(jobs["dependency-audit"])

    required_needs = set(expected_names)
    assert required_needs <= set(jobs["container-build"]["needs"])

from __future__ import annotations

import ast
from pathlib import Path

from app.contracts.learning import MasteryEstimate, ReviewSchedule


def test_next_due_at_has_one_canonical_calculation_owner() -> None:
    app_root = Path("app")
    writers: list[str] = []
    for path in app_root.rglob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = node.func.id if isinstance(node.func, ast.Name) else None
            if name == "ReviewSchedule" and any(
                keyword.arg == "next_due_at" for keyword in node.keywords
            ):
                writers.append(str(path))
    assert writers == ["app/domains/review_scheduler/scheduler.py"]


def test_planner_cannot_calculate_memory_state_or_due_time() -> None:
    planner_source = Path("app/domains/learning_planner/planner.py").read_text()
    assert "next_due_at" not in planner_source
    assert "ReviewScheduler" not in planner_source
    assert "stability" not in planner_source
    assert "retrievability" not in planner_source
    assert "next_due_at" in ReviewSchedule.model_fields
    assert "next_due_at" not in MasteryEstimate.model_fields

"""UI-01 workspace API/query ownership regression tests."""

from __future__ import annotations

import ast
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2] / "app"


def test_ui_data_ac_007_workspace_api_is_transport_only() -> None:
    """UI-DATA-AC-007/API-001: API imports query, not owner ORM models."""
    source = (APP_ROOT / "api" / "v1" / "workspace.py").read_text(encoding="utf-8")
    assert "app.queries.workspace" in source
    assert "app.models.planning" not in source
    assert "app.models.assessment" not in source
    assert "app.models.dialog" not in source


def test_ui_data_ac_007_query_is_read_only_and_does_not_guess_plan_ownership() -> None:
    """UI-DATA-AC-007: query has no writes or unsafe plan/activity reads."""
    source = (APP_ROOT / "queries" / "workspace.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    planning_imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module == "app.models.planning"
        for alias in node.names
    }
    assert planning_imports == {"ReviewScheduleRecord"}
    assert ".add(" not in source
    assert ".commit(" not in source
    assert ".flush(" not in source
    assert ".delete(" not in source

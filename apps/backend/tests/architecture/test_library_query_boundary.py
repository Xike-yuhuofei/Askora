"""UI-02A library API/query ownership regression tests."""

from __future__ import annotations

import ast
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2] / "app"


def test_ui02a_workspace_api_remains_transport_only() -> None:
    """API-001/UI-DATA-AC-007: transport imports query, not content ORM."""
    source = (APP_ROOT / "api" / "v1" / "workspace.py").read_text(encoding="utf-8")
    assert "app.queries.library" in source
    assert "app.models.document" not in source
    assert "DocumentService" not in source


def test_ui02a_library_query_is_read_only_and_has_no_cross_owner_write() -> None:
    """STATE-001/UI02A-VSLICE-AC-011: page assembly has no mutation calls."""
    source = (APP_ROOT / "queries" / "library.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_models = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("app.models")
        for alias in node.names
    }
    assert imported_models == {
        "ModerationStatus",
        "ProcessingStatus",
        "User",
        "UserDocument",
    }
    assert ".add(" not in source
    assert ".commit(" not in source
    assert ".flush(" not in source
    assert ".delete(" not in source

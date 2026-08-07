"""Static ownership regressions for EXEC-002."""

from __future__ import annotations

import ast
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]


def _attribute_assignments(path: Path, attribute: str) -> list[int]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    lines: list[int] = []
    for node in ast.walk(tree):
        targets: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        elif isinstance(node, ast.AugAssign):
            targets = [node.target]
        for target in targets:
            if isinstance(target, ast.Attribute) and target.attr == attribute:
                lines.append(target.lineno)
    return lines


def test_exec002_dialog_has_no_canonical_mastery_write():
    """EXEC002-AC-003/VSLICE-012: DialogService cannot assign mastery_estimate."""
    path = BACKEND / "app/services/dialog/dialog_service.py"
    assert _attribute_assignments(path, "mastery_estimate") == []


def test_exec002_dialog_has_no_direct_socratic_production_import():
    """VSLICE-011: the production adapter imports only the canonical facade."""
    path = BACKEND / "app/services/dialog/dialog_service.py"
    source = path.read_text(encoding="utf-8")
    assert "services.dialog.socratic_engine" not in source
    assert "_should_use_orchestrator" not in source
    assert "get_learning_orchestration_facade" in source


def test_exec002_orchestrator_rejects_engine_mastery_writes():
    """SYS08-002/STATE-031: execution may report but cannot apply mastery deltas."""
    path = BACKEND / "app/engines/orchestrator.py"
    source = path.read_text(encoding="utf-8")
    assert "shared.mastery_vector[" not in source
    assert "shared.mastery_confidence[" not in source
    assert "legacy_mastery_update_rejected" in source
    adapter = (BACKEND / "app/engines/socratic_adapter.py").read_text(encoding="utf-8")
    assert ".update_mastery(" not in adapter

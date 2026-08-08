"""EXEC-018 ownership and derived-projection architecture checks."""

from __future__ import annotations

import ast
from pathlib import Path

from app.core.database import Base

APP_ROOT = Path(__file__).resolve().parents[2] / "app"


def test_exec018_projections_are_sys01_pure_and_not_second_truth_tables() -> None:
    """D02-AC-003/006: working projections stay derived and EvidenceSpan is a value ref."""
    source = (APP_ROOT / "domains" / "content_knowledge" / "projections.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    imports = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    assert not any(module.startswith("sqlalchemy") for module in imports)
    assert "app.domains.retrieval" not in imports
    assert "evidence_spans" not in Base.metadata.tables
    assert "semantic_units" not in Base.metadata.tables
    assert "hierarchy_nodes" not in Base.metadata.tables


def test_exec018_hierarchy_projection_cannot_publish_prerequisite_truth() -> None:
    """D02-AC-005: hierarchy builder has no relation owner or publish dependency."""
    source = (APP_ROOT / "domains" / "content_knowledge" / "projections.py").read_text(
        encoding="utf-8"
    )
    assert "KnowledgeRelation" not in source
    assert "prerequisite_id" not in source
    assert "target_knowledge_unit_id" not in source
    assert "app.domains.planning" not in source

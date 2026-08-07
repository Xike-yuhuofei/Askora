"""EXEC-008 architecture ownership and canonical-schema regression tests."""

from __future__ import annotations

import ast
from pathlib import Path

from app.contracts import (
    ActualAssistanceRecordedPayloadV03,
    AssessmentAttemptV03,
    AssessmentResultV03,
    MasteryEstimate,
    StrategyFamily,
    TeachingActionV03,
    TeachingContextV03,
)

APP_ROOT = Path(__file__).resolve().parents[2] / "app"


def test_strategy_family_has_one_canonical_definition() -> None:
    """EXEC008-AC-001/002, DEP-002: no second top-level v0.3 enum."""
    definitions: list[Path] = []
    for path in APP_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if any(
            isinstance(node, ast.ClassDef) and node.name == "StrategyFamily"
            for node in ast.walk(tree)
        ):
            definitions.append(path.relative_to(APP_ROOT))
    assert definitions == [Path("contracts/adaptive.py")]
    assert len(StrategyFamily) == 6


def test_v03_canonical_writers_expose_no_legacy_integer_or_strategy_fields() -> None:
    """EXEC008-AC-009, DEP-204, VSLICE-311."""
    forbidden = {
        "strategy_id",
        "action_type",
        "scaffold_level",
        "hint_level",
        "answer_exposure_max",
        "propensity",
    }
    assert forbidden.isdisjoint(TeachingActionV03.model_fields)
    assert forbidden.isdisjoint(TeachingContextV03.model_fields)
    assert forbidden.isdisjoint(AssessmentResultV03.model_fields)
    assert forbidden.isdisjoint(AssessmentAttemptV03.model_fields)
    assert forbidden.isdisjoint(ActualAssistanceRecordedPayloadV03.model_fields)


def test_teaching_stage_is_not_learner_or_assessment_truth() -> None:
    """EXEC008-AC-005, STATE-201, SYS03-220."""
    assert "teaching_stage" not in MasteryEstimate.model_fields
    assert "strategy_family" not in MasteryEstimate.model_fields
    assert "teaching_stage" not in AssessmentResultV03.model_fields
    assert "strategy_family" not in AssessmentResultV03.model_fields

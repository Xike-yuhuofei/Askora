from __future__ import annotations

from pathlib import Path

from app.contracts.adaptive import StrategyFamily, TeachingStage

BACKEND_ROOT = Path(__file__).parents[2]
POLICY_ROOT = BACKEND_ROOT / "app" / "domains" / "teaching_policy"


def test_policy_domain_has_no_llm_or_legacy_selector_dependency() -> None:
    source = "\n".join(path.read_text() for path in POLICY_ROOT.glob("*.py"))
    assert "app.services.dialog" not in source
    assert "app.engines" not in source
    assert "ChatOrchestrator" not in source
    assert "import random" not in source
    assert "from random" not in source


def test_teaching_stage_is_derived_policy_control_not_learner_truth() -> None:
    learner_source = (
        BACKEND_ROOT / "app" / "domains" / "learner_model" / "projector.py"
    ).read_text()
    assert "TeachingStage" not in learner_source
    assert len(TeachingStage) == 8
    assert len(StrategyFamily) == 6

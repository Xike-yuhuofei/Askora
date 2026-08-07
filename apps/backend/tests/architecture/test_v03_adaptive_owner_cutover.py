from __future__ import annotations

from pathlib import Path

BACKEND_ROOT = Path(__file__).parents[2]


def test_adaptive_facade_has_one_sys05_final_action_call_and_no_legacy_selector() -> None:
    source = (BACKEND_ROOT / "app" / "orchestration" / "learning_facade.py").read_text()
    assert source.count("self._policy_kernel.decide(") == 1
    assert "StrategySelector" not in source
    assert "strategy_selector" not in source
    assert '"final_action_owner": "SYS05"' in source


def test_legacy_socratic_is_explicitly_compatibility_only_for_v03_ownership() -> None:
    source = (BACKEND_ROOT / "app" / "engines" / "socratic_adapter.py").read_text()
    assert "legacy v0.2 rendering/move adapter" in source
    assert "cannot emit TeachingActionV03" in source
    assert "from app.contracts.adaptive import TeachingActionV03" not in source


def test_sys03_adaptive_eligibility_does_not_write_mastery_projection() -> None:
    source = (
        BACKEND_ROOT / "app" / "domains" / "learner_model" / "adaptive_eligibility.py"
    ).read_text()
    assert "WeightedBKTProjector" not in source
    assert "from app.contracts.learning import MasteryEstimate" not in source
    assert "return MasteryEstimate(" not in source
    assert "model_router" not in source


def test_domain_adapters_do_not_import_orchestration_layer() -> None:
    for relative in (
        "app/domains/assessment/adaptive_service.py",
        "app/domains/learner_model/adaptive_eligibility.py",
        "app/domains/retrieval/adaptive_evidence_service.py",
    ):
        assert "app.orchestration" not in (BACKEND_ROOT / relative).read_text()


def test_ordinary_and_streaming_share_single_execute_method() -> None:
    source = (BACKEND_ROOT / "app" / "orchestration" / "learning_facade.py").read_text()
    assert source.count("await self._execute_turn(request)") == 2

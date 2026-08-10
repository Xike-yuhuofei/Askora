from __future__ import annotations

from pathlib import Path

BACKEND_ROOT = Path(__file__).parents[2]


def test_adaptive_facade_exposes_single_sys05_policy_composition_path() -> None:
    """Production adaptive entry must route through the SYS05-owned policy
    composition (Case A bootstrap + Case B SequentialTeachingPolicy) and never
    fall back to a legacy StrategySelector or direct legacy engine.
    """

    source = (BACKEND_ROOT / "app" / "orchestration" / "learning_facade.py").read_text()
    assert "StrategySelector" not in source
    assert "strategy_selector" not in source
    assert '"final_action_owner": "SYS05"' in source
    assert "sequential_policy_state_v03" in source
    assert "sequential_transition_reason_v03" in source
    assert "_reconstruct_sequential_policy_state" in source
    assert "FixedTimeSource(context.decision_time)" in source or "FixedTimeSource(decision_time)" in source


def test_sequential_policy_accepts_injected_time_source_for_replay() -> None:
    """SequentialTeachingPolicy.decide MUST accept an injected time_source so
    production code can pin replay time to TeachingContext.decision_time.
    """

    source = (
        BACKEND_ROOT / "app" / "domains" / "teaching_policy" / "sequential.py"
    ).read_text()
    assert "time_source: TimeSource | None = None" in source
    assert "active_time_source = time_source or self._time_source" in source


def test_sequential_state_helper_rebuilds_continuity_from_trace() -> None:
    """Facade helper MUST rebuild evidence_opportunities_since_transition and
    observed_material_evidence_keys from the previous immutable DecisionTrace
    so sequential decisions remain deterministic.
    """

    source = (BACKEND_ROOT / "app" / "orchestration" / "learning_facade.py").read_text()
    assert "_reconstruct_sequential_policy_state" in source
    assert "evidence_opportunities_since_transition" in source
    assert "observed_material_evidence_keys" in source


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

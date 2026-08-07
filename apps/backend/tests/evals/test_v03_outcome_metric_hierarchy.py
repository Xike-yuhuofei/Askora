from __future__ import annotations

from app.domains.teaching_policy.outcome_evaluation import (
    PRIMARY_LEARNING_OUTCOMES,
    PROCESS_EXPERIENCE_METRICS,
    OutcomeMetricTier,
    metric_tier,
)


def test_primary_learning_outcomes_are_separate_from_process_diagnostics() -> None:
    assert PRIMARY_LEARNING_OUTCOMES == {
        "NO_HINT_INDEPENDENT_SUCCESS",
        "DELAYED_INDEPENDENT_PERFORMANCE",
        "INDEPENDENT_TRANSFER",
        "UNIT_TIME_CAPABILITY_GAIN",
    }
    assert PROCESS_EXPERIENCE_METRICS == {
        "ENGAGEMENT",
        "CONVERSATION_TURNS",
        "LIKES",
        "HINT_COUNT",
        "TOKENS",
        "SESSION_DURATION",
    }
    assert PRIMARY_LEARNING_OUTCOMES.isdisjoint(PROCESS_EXPERIENCE_METRICS)
    assert metric_tier("DELAYED_INDEPENDENT_PERFORMANCE") is OutcomeMetricTier.PRIMARY_LEARNING
    assert metric_tier("ENGAGEMENT") is OutcomeMetricTier.PROCESS_EXPERIENCE

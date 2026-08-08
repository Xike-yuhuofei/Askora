"""EXEC-022 owner-boundary source checks."""

from __future__ import annotations

from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]


def test_sys06_diagnostic_planner_has_no_grader_or_mastery_writer() -> None:
    source = (BACKEND / "app/domains/learning_planner/diagnostic.py").read_text()
    assert "answer_key" not in source
    assert "AssessmentResult(" not in source
    assert "WeightedBKTProjector" not in source
    assert "MasteryEstimateRecord" not in source
    assert "LearningPlan(" not in source


def test_diagnostic_application_reuses_existing_owner_services() -> None:
    source = (BACKEND / "app/services/assessment/diagnostic_bootstrap.py").read_text()
    assert "CanonicalAssessmentService" in source
    assert "DiagnosticLearnerStateService" in source
    assert "LearningPlanner" in source
    assert "score_submission_with_attempt" in source
    assert "project_assessment" in source
    assert "LearnerModelRepository" not in source
    assert "LearningPlanRecord" not in source
    assert "MasteryEstimateRecord" not in source

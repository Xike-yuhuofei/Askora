"""STATE-AC-300/DEP-300..302 static onboarding ownership evidence."""

from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]


def test_onboarding_preference_writer_is_confined_to_platform_adapter() -> None:
    writers: list[str] = []
    for path in (BACKEND / "app").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "OnboardingPreferenceRecord(" in text:
            writers.append(str(path.relative_to(BACKEND)))
    assert sorted(writers) == [
        "app/models/onboarding.py",
        "app/repositories/onboarding_preferences.py",
    ]


def test_onboarding_query_has_no_cross_owner_write_or_frontend_inference() -> None:
    query = (BACKEND / "app/queries/onboarding.py").read_text(encoding="utf-8")
    forbidden = (
        "LearningGoalRecord(",
        "LearningActivityStateRecord(",
        "UserDocument(",
        "BookLearningTranscriptTurnRecord(",
        "model_router",
        "localStorage",
    )
    assert not [token for token in forbidden if token in query]
    assert "FirstActivityCompletionProjectionV1" in query
    assert "BookLearningTranscriptTurn" in query

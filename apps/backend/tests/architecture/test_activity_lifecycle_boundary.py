"""Static ownership boundary for canonical lifecycle writers."""

from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]


def test_lifecycle_state_writers_are_confined_to_sys06_adapters() -> None:
    writers: list[str] = []
    for path in (BACKEND / "app").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "LearningActivityStateRecord(" in text:
            writers.append(str(path.relative_to(BACKEND)))
    assert sorted(writers) == [
        "app/infrastructure/activity_lifecycle.py",
        "app/models/planning.py",
    ]


def test_ui_and_sys08_do_not_infer_completion_from_transcript() -> None:
    query = (BACKEND / "app/queries/workspace.py").read_text(encoding="utf-8")
    book_query = (BACKEND / "app/queries/book_learning.py").read_text(encoding="utf-8")
    assert "ActivityLifecycleRepository" in query
    assert "ActivityLifecycleRepository" in book_query
    assert 'event_type == "ActivitySelected"' not in book_query

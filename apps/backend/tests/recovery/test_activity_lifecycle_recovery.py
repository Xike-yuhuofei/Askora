"""Restart recovery is latest-state based, never transcript/event recency based."""

from pathlib import Path


def test_activity_query_has_no_legacy_payload_or_event_fallback() -> None:
    backend = Path(__file__).resolve().parents[2]
    workspace = (backend / "app/queries/workspace.py").read_text(encoding="utf-8")
    lifecycle = (backend / "app/infrastructure/activity_lifecycle.py").read_text(
        encoding="utf-8"
    )
    assert "LEGACY_ACTIVITY_STATE_UNMIGRATED" in workspace
    assert "LearningActivityStateRecord.version.desc()" in lifecycle
    assert "ActivitySelected" not in workspace

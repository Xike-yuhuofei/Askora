"""P1-07 recovery remains a control plane, not a ninth owner."""

from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]


def test_recovery_service_routes_only_to_registered_owner_commands() -> None:
    source = (BACKEND / "app/services/recovery.py").read_text()
    assert "DocumentService" in source
    assert "OutboxRepository" in source
    for forbidden in (
        "MasteryEstimateRecord",
        "LearnerStateRecord",
        "AssessmentResult",
        "LearningPlanRecord",
        "ReviewScheduleRecord",
    ):
        assert forbidden not in source
    assert ".status = OutboxStatus.PENDING" not in source
    assert "original_task.status =" not in source


def test_recovery_api_is_transport_only() -> None:
    source = (BACKEND / "app/api/v1/recovery.py").read_text()
    assert "RecoveryQueryService" in source
    assert "RecoveryActionService" in source
    assert "app.models." not in source.replace("from app.models.user import User", "")
    assert "update(" not in source

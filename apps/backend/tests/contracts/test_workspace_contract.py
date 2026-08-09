"""UI-DATA/UI01 strict workspace contract tests."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from app.contracts.workspace import (
    CompatibilityQuickStartV1,
    EvidenceProfileDataV1,
    EvidenceProfileResponseV1,
    GoalListDataV1,
    GoalListResponseV1,
    LegacyEvidenceCompatibilityV1,
    TodayWorkspaceDataV1,
    TodayWorkspaceResponseV1,
)


def _valid_response() -> TodayWorkspaceResponseV1:
    return TodayWorkspaceResponseV1(
        generated_at=datetime(2026, 8, 8, tzinfo=timezone.utc),
        correlation_id="request-1",
        data=TodayWorkspaceDataV1(
            local_date=date(2026, 8, 8),
            timezone="Asia/Shanghai",
            view_state="PARTIAL",
            compatibility_quick_start=CompatibilityQuickStartV1(),
        ),
        source_status=(),
    )


def test_ui_data_ac_001_workspace_contract_is_strict_and_versioned() -> None:
    """UI-DATA-AC-001: the public query response is immutable and strict."""
    response = _valid_response()
    assert response.schema_version == "1.0"
    with pytest.raises(ValidationError):
        TodayWorkspaceResponseV1.model_validate(
            {**response.model_dump(mode="json"), "unexpected": True}
        )
    with pytest.raises(ValidationError):
        TodayWorkspaceResponseV1.model_validate(
            {**response.model_dump(mode="json"), "schema_version": "2.0"}
        )


def test_ui_data_ac_002_workspace_contract_rejects_naive_datetime() -> None:
    """UI-DATA-AC-002/DOMAIN-004: timestamps must be timezone-aware."""
    payload = _valid_response().model_dump()
    payload["generated_at"] = datetime(2026, 8, 8)
    with pytest.raises(ValidationError):
        TodayWorkspaceResponseV1.model_validate(payload)


def test_ui02b_workspace_contracts_are_strict_versioned_and_honest() -> None:
    """UI02B-VSLICE-AC-001/005: public read contracts stay strict and label-free."""
    goals = GoalListResponseV1(
        generated_at=datetime(2026, 8, 9, tzinfo=timezone.utc),
        correlation_id="request-goals",
        data=GoalListDataV1(view_state="EMPTY"),
        source_status=(),
    )
    assert goals.schema_version == "1.0"
    with pytest.raises(ValidationError):
        GoalListResponseV1.model_validate({**goals.model_dump(mode="json"), "unexpected": True})

    evidence = EvidenceProfileResponseV1(
        generated_at=datetime(2026, 8, 9, tzinfo=timezone.utc),
        correlation_id="request-evidence",
        data=EvidenceProfileDataV1(
            view_state="EMPTY",
            knowledge_units_assessed=0,
            legacy_compatibility=LegacyEvidenceCompatibilityV1(),
        ),
        source_status=(),
    )
    assert evidence.data.legacy_compatibility.visible_by_default is False
    assert evidence.data.entries == ()

"""UI-DATA/UI01 strict workspace contract tests."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from app.contracts.workspace import (
    CompatibilityQuickStartV1,
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

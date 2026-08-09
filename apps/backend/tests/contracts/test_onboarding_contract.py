"""ONBOARD-AC-001..004 strict public contract evidence."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.contracts.onboarding import (
    OnboardingJourneyViewV1,
    OnboardingNextActionV1,
    OnboardingPreferenceCommandV1,
    OnboardingPreferenceV1,
    OnboardingStepViewV1,
    SourceObservationV1,
)

NOW = datetime(2026, 8, 9, 13, 0, tzinfo=timezone.utc)


def _preference() -> OnboardingPreferenceV1:
    return OnboardingPreferenceV1(
        journey_id="first-learning-v1",
        preference_version=1,
        visibility="ACTIVE",
        created_at=NOW,
        updated_at=NOW,
    )


def test_onboard_ac_001_contract_is_strict_versioned_and_single_action() -> None:
    source = SourceObservationV1(
        source_system="SYS08",
        availability="MISSING",
        reason_codes=("MODEL_CONFIGURATION_QUERY_UNAVAILABLE",),
    )
    response = OnboardingJourneyViewV1(
        generated_at=NOW,
        journey_state="ACTIVE",
        should_enter_welcome=True,
        preference=_preference(),
        boundary_notice={
            "notice_version": "privacy-and-model-v1",
            "acknowledged": False,
            "data_control_route": None,
            "model_settings_route": "/settings#model",
        },
        steps=(
            OnboardingStepViewV1(
                step="MODEL",
                state="NOT_STARTED",
                title="模型",
                summary="尚未验证模型",
                source_status=(source,),
            ),
        ),
        next_action=OnboardingNextActionV1(
            action_code="ACKNOWLEDGE_BOUNDARIES",
            kind="command",
            label="我已了解",
        ),
        correlation_id="request-1",
    )
    assert response.schema_version == "1.0"
    assert response.journey_id == "first-learning-v1"
    assert response.next_action.action_code == "ACKNOWLEDGE_BOUNDARIES"
    with pytest.raises(ValidationError):
        OnboardingJourneyViewV1.model_validate(
            {**response.model_dump(mode="json"), "unexpected": True}
        )
    with pytest.raises(ValidationError):
        OnboardingJourneyViewV1.model_validate(
            {**response.model_dump(mode="json"), "schema_version": "2.0"}
        )


def test_onboard_ac_002_preference_rejects_domain_truth_fields() -> None:
    with pytest.raises(ValidationError):
        OnboardingPreferenceV1.model_validate(
            {
                **_preference().model_dump(mode="json"),
                "activity_ref": "forbidden",
            }
        )


def test_onboard_020_preference_command_is_versioned_and_idempotent() -> None:
    command = OnboardingPreferenceCommandV1(
        expected_preference_version=1,
        action="DISMISS",
        idempotency_key="dismiss-1",
    )
    assert command.schema_version == "1.0"
    with pytest.raises(ValidationError):
        OnboardingPreferenceCommandV1.model_validate(
            {**command.model_dump(mode="json"), "idempotency_key": ""}
        )


def test_onboarding_contract_rejects_naive_datetime() -> None:
    payload = _preference().model_dump()
    payload["created_at"] = datetime(2026, 8, 9, 13, 0)
    with pytest.raises(ValidationError):
        OnboardingPreferenceV1.model_validate(payload)

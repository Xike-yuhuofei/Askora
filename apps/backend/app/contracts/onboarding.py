"""P1-06 strict presentation preference and owner-fact journey contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from app.contracts.adaptive import AvailabilityStatus, VersionedRef
from app.contracts.base import ContractModel

JourneyId = Literal["first-learning-v1"]
PreferenceVisibility = Literal["ACTIVE", "DISMISSED"]
DismissedReason = Literal["USER_DEFERRED", "COMPLETED_JOURNEY", "LEGACY_EXISTING_USER_BACKFILL"]
OnboardingStep = Literal["MODEL", "MATERIAL", "GOAL", "FIRST_ACTIVITY"]
OnboardingStepState = Literal["NOT_STARTED", "IN_PROGRESS", "COMPLETE", "BLOCKED", "STALE"]
OnboardingJourneyState = Literal["ACTIVE", "COMPLETE", "BLOCKED", "PARTIAL", "STALE"]
OnboardingActionCode = Literal[
    "ACKNOWLEDGE_BOUNDARIES",
    "OPEN_MODEL_SETTINGS",
    "OPEN_LIBRARY",
    "SELECT_MATERIAL",
    "OPEN_MATERIAL_LEARNING",
    "CONTINUE_GOAL_SETUP",
    "CONTINUE_DIAGNOSTIC",
    "START_ACTIVITY",
    "RESUME_ACTIVITY",
    "COMPLETE_ACTIVITY",
    "OPEN_WELCOME",
    "OPEN_TODAY",
    "WAIT",
    "RECOVER",
    "NONE",
]


class OnboardingPreferenceV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    journey_id: JourneyId = "first-learning-v1"
    preference_version: int = Field(ge=1)
    visibility: PreferenceVisibility
    boundary_notice_version_acknowledged: str | None = Field(default=None, max_length=100)
    dismissed_reason: DismissedReason | None = None
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def validate_dismissal(self) -> OnboardingPreferenceV1:
        if self.visibility == "ACTIVE" and self.dismissed_reason is not None:
            raise ValueError("active preference cannot have a dismissed reason")
        if self.visibility == "DISMISSED" and self.dismissed_reason is None:
            raise ValueError("dismissed preference requires a reason")
        return self


class SourceObservationV1(ContractModel):
    source_system: Literal["PLATFORM_EXPERIENCE", "SYS08", "SYS01", "SYS06", "DATA_CONTROL"]
    availability: AvailabilityStatus
    source_ref: str | None = None
    observed_at: datetime | None = None
    reason_codes: tuple[str, ...] = ()


class OnboardingStepViewV1(ContractModel):
    step: OnboardingStep
    state: OnboardingStepState
    title: str = Field(min_length=1, max_length=80)
    summary: str = Field(min_length=1, max_length=300)
    source_status: tuple[SourceObservationV1, ...]


class RecoveryActionProjectionV1(ContractModel):
    """Typed read projection of the P1-07 RecoveryActionV1 public fields."""

    action_code: str = Field(min_length=1, max_length=80)
    label: str = Field(min_length=1, max_length=120)
    kind: Literal["command", "navigate", "wait", "client"]
    enabled: bool
    disabled_reason_code: str | None = None
    endpoint: str | None = None
    method: Literal["POST"] | None = None
    route: str | None = None
    requires_idempotency_key: bool = False
    requires_confirmation: bool = False


class OnboardingNextActionV1(ContractModel):
    action_code: OnboardingActionCode
    kind: Literal["command", "navigate", "wait", "recover", "none"]
    label: str = Field(min_length=1, max_length=120)
    enabled: bool = True
    route: str | None = None
    resource_ref: str | None = None
    recovery_action: RecoveryActionProjectionV1 | None = None
    reason_codes: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_action_payload(self) -> OnboardingNextActionV1:
        if self.kind == "recover" and self.recovery_action is None:
            raise ValueError("recover action requires a server-provided recovery action")
        if self.kind != "recover" and self.recovery_action is not None:
            raise ValueError("only recover actions may carry recovery_action")
        return self


class BoundaryNoticeV1(ContractModel):
    notice_version: str = Field(min_length=1, max_length=100)
    acknowledged: bool
    data_control_route: str | None = None
    model_settings_route: str


class OnboardingJourneyViewV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    journey_id: JourneyId = "first-learning-v1"
    generated_at: datetime
    journey_state: OnboardingJourneyState
    should_enter_welcome: bool
    preference: OnboardingPreferenceV1
    boundary_notice: BoundaryNoticeV1
    steps: tuple[OnboardingStepViewV1, ...]
    next_action: OnboardingNextActionV1
    correlation_id: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def require_unique_ordered_steps(self) -> OnboardingJourneyViewV1:
        expected = ("MODEL", "MATERIAL", "GOAL", "FIRST_ACTIVITY")
        actual = tuple(item.step for item in self.steps)
        if len(actual) == 4 and actual != expected:
            raise ValueError("four-step journey must use the frozen order")
        if len(set(actual)) != len(actual):
            raise ValueError("onboarding steps must be unique")
        return self


class OnboardingPreferenceCommandV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    journey_id: JourneyId = "first-learning-v1"
    expected_preference_version: int = Field(ge=1)
    action: Literal["ACKNOWLEDGE_BOUNDARIES", "DISMISS", "REOPEN", "FINISH_AND_DISMISS"]
    notice_version: str | None = Field(default=None, max_length=100)
    idempotency_key: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def validate_notice(self) -> OnboardingPreferenceCommandV1:
        if self.action == "ACKNOWLEDGE_BOUNDARIES" and not self.notice_version:
            raise ValueError("boundary acknowledgment requires an exact notice version")
        return self


class FirstActivityCompletionProjectionV1(ContractModel):
    user_ref: str
    activity_ref: VersionedRef
    state_ref: VersionedRef
    status: Literal["completed"] = "completed"
    completed_at: datetime
    completion_source_type: Literal["accepted_model_transcript"] = "accepted_model_transcript"
    completion_source_ref: VersionedRef

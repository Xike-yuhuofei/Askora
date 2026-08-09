"""SYS06 canonical LearningActivity lifecycle v1 contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.contracts.adaptive import VersionedRef
from app.contracts.base import ContractModel

ActivityStatus = Literal["planned", "available", "active", "completed", "skipped", "superseded"]


class LearningActivityStateV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    activity_id: UUID
    version: int = Field(ge=1)
    plan_id: UUID
    plan_version: int = Field(ge=1)
    status: ActivityStatus
    previous_status: ActivityStatus | None = None
    transition_reason: str = Field(min_length=1, max_length=200)
    source_refs: tuple[VersionedRef, ...] = ()
    actor_type: Literal["system", "learner"]
    started_at: datetime | None = None
    completed_at: datetime | None = None
    correlation_id: UUID
    created_at: datetime


class StartLearningActivityV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    activity_id: UUID
    expected_state_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)


class CompleteLearningActivityV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    activity_id: UUID
    expected_state_version: int = Field(ge=1)
    completion_intent: Literal["learner_finished"]
    transcript_turn_refs: tuple[VersionedRef, ...] = Field(min_length=1)
    idempotency_key: str = Field(min_length=1, max_length=200)


class ActivityExecutionCapabilityV1(ContractModel):
    can_start: bool
    can_resume: bool
    can_complete: bool
    product_route: str
    reason_codes: tuple[str, ...] = ()


class ActivityLifecycleDataV1(ContractModel):
    state: LearningActivityStateV1
    goal_id: UUID
    activity_type: str
    title: str
    estimated_duration_minutes: int = Field(ge=0)
    knowledge_unit_ids: tuple[UUID, ...]
    execution: ActivityExecutionCapabilityV1


class ActivityLifecycleResponseV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    data: ActivityLifecycleDataV1
    next_activity_ref: VersionedRef | None = None
    plan_status: Literal["active", "superseded", "completed", "paused"]
    correlation_id: str

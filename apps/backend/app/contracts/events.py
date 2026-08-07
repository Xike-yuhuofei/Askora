"""LearningEventEnvelope v1 公共合同。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, field_validator

from app.contracts.adaptive import AssistanceSnapshotV03, VersionedRef
from app.contracts.base import ContractModel


class EventActor(ContractModel):
    actor_type: Literal["learner", "system", "model", "reviewer"]
    actor_id: str
    device_id: str | None = None


class EventContext(ContractModel):
    user_id: UUID
    session_id: UUID | None = None
    goal_id: UUID | None = None
    knowledge_unit_ids: list[UUID]
    assessment_attempt_id: UUID | None = None
    content_revision_ids: list[UUID]


class EventProvenance(ContractModel):
    source: Literal["ui", "api", "orchestrator", "worker", "migration", "domain"]
    model_provider: str | None = None
    model_name: str | None = None
    model_snapshot: str | None = None
    prompt_id: str | None = None
    prompt_version: str | None = None
    policy_version: str | None = None
    projection_version: str | None = None
    algorithm_version: str | None = None


class EventTrace(ContractModel):
    trace_id: str
    span_id: str | None = None


class EventPrivacy(ContractModel):
    classification: Literal["public", "personal", "sensitive"]
    external_processing: bool
    retention_class: Literal["core_learning", "diagnostic", "temporary"]


class LearningEventEnvelope(ContractModel):
    """EVENT-001..017：不可变、可追溯且版本显式的学习事实。"""

    event_id: UUID
    event_type: str = Field(min_length=1)
    schema_version: Literal["1.0"] = "1.0"
    aggregate_type: str = Field(min_length=1)
    aggregate_id: UUID | str
    aggregate_version: int = Field(ge=1)
    sequence: int = Field(ge=1)
    occurred_at: datetime
    recorded_at: datetime
    idempotency_key: str = Field(min_length=1)
    correlation_id: UUID
    causation_id: UUID | None = None
    actor: EventActor
    context: EventContext
    payload: dict[str, Any]
    provenance: EventProvenance
    trace: EventTrace
    privacy: EventPrivacy

    @field_validator("aggregate_id", mode="before")
    @classmethod
    def normalize_aggregate_id(cls, value: UUID | str) -> str:
        """保证 UUID/string 标识经过 JSON/SQLite 往返后表示稳定。"""
        return str(value)


class EventProvenanceV03(ContractModel):
    source: Literal["ui", "api", "orchestrator", "worker", "migration", "domain"]
    model_provider: str | None = None
    model_name: str | None = None
    model_snapshot: str | None = None
    prompt_id: str | None = None
    prompt_version: str | None = None
    policy_version: str | None = None
    policy_bundle_ref: VersionedRef | None = None
    projection_version: str | None = None
    algorithm_version: str | None = None


class ActualAssistanceRecordedPayloadV03(ContractModel):
    """EVENT-201/SYS08-202 actual experience, not the planned envelope."""

    teaching_action_ref: VersionedRef
    rendered_response_ref: VersionedRef | None = None
    attempt_ref: VersionedRef | None = None
    actual_assistance: AssistanceSnapshotV03
    integrity_reason_codes: tuple[str, ...] = ()


class LearningEventEnvelopeV03(ContractModel):
    """EVENT-200..231 v0.3 append-only event envelope."""

    event_id: UUID
    event_type: str = Field(min_length=1)
    schema_version: str = Field(default="3.0", pattern=r"^3\.")
    aggregate_type: str = Field(min_length=1)
    aggregate_id: UUID | str
    aggregate_version: int = Field(ge=1)
    sequence: int = Field(ge=1)
    occurred_at: datetime
    recorded_at: datetime
    idempotency_key: str = Field(min_length=1)
    correlation_id: UUID
    causation_id: UUID | None = None
    actor: EventActor
    context: EventContext
    producer_system: Literal["SYS01", "SYS02", "SYS03", "SYS04", "SYS05", "SYS06", "SYS07", "SYS08"]
    payload: dict[str, Any]
    provenance: EventProvenanceV03
    trace: EventTrace
    privacy: EventPrivacy

    @field_validator("aggregate_id", mode="before")
    @classmethod
    def normalize_aggregate_id(cls, value: UUID | str) -> str:
        return str(value)

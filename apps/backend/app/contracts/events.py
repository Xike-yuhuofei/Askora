"""LearningEventEnvelope v1 公共合同。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, field_validator

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

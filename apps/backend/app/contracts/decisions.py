"""DecisionTrace v1 公共合同。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, field_validator

from app.contracts.base import ContractModel


class DecisionInput(ContractModel):
    entity_type: str
    entity_id: UUID | str
    version: str | int | None = None

    @field_validator("entity_id", mode="before")
    @classmethod
    def normalize_entity_id(cls, value: UUID | str) -> str:
        return str(value)


class DecisionAlgorithm(ContractModel):
    algorithm_id: str
    algorithm_version: str
    model_inference_ids: list[UUID]
    prompt_versions: list[str]


class DecisionExperiment(ContractModel):
    experiment_id: str | None = None
    variant_id: str | None = None
    propensity: float | None = Field(default=None, ge=0.0, le=1.0)


class DecisionTrace(ContractModel):
    """DECISION-001..091：领域系统提交、4.8 原样持久化的审计记录。"""

    decision_id: UUID
    decision_type: str = Field(min_length=1)
    schema_version: Literal["1.0"] = "1.0"
    owner_system: Literal[
        "content_knowledge",
        "retrieval",
        "learner_model",
        "assessment",
        "teaching_policy",
        "learning_planner",
        "review_scheduler",
        "ai_orchestration",
    ]
    inputs: list[DecisionInput]
    candidates: list[dict[str, Any]]
    selected: dict[str, Any]
    constraints: list[dict[str, Any]]
    reason_codes: list[str] = Field(min_length=1)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    algorithm: DecisionAlgorithm
    experiment: DecisionExperiment
    created_at: datetime
    correlation_id: UUID
    trace_id: str

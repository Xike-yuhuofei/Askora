"""SPEC-D06 additive Book-to-Learning application/API contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.contracts.adaptive import EvidenceBundleV03, TeachingActionV03, VersionedRef
from app.contracts.assessment import AssistanceSnapshot
from app.contracts.base import ContractModel
from app.contracts.model_execution import ModelExecutionV1

BookLearningReadinessState = Literal[
    "PROCESSING",
    "CONTENT_PARTIAL",
    "READY_FOR_GOAL",
    "GOAL_CONFIRMATION_REQUIRED",
    "DIAGNOSIS_REQUIRED",
    "DIAGNOSING",
    "PLAN_READY",
    "READY_TO_LEARN",
    "BLOCKED",
]


class BookLearningOwnerRefV1(ContractModel):
    owner_system: Literal["SYS01", "SYS02", "SYS03", "SYS04", "SYS05", "SYS06", "SYS08"]
    ref: VersionedRef
    status: str
    reason_codes: tuple[str, ...] = ()


class BookLearningReadinessV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    document_id: UUID
    state: BookLearningReadinessState
    owner_refs: tuple[BookLearningOwnerRefV1, ...]
    reason_codes: tuple[str, ...] = Field(min_length=1)
    next_commands: tuple[str, ...]
    generated_at: datetime
    correlation_id: str


class LearnerVisibleDiagnosticItemV1(ContractModel):
    """UI02B1-030 safe SYS04 projection; grader-only fields are structurally absent."""

    item_ref: VersionedRef
    need_id: UUID
    need_version: int = Field(ge=1)
    item_type: Literal["exact", "multiple_choice"]
    prompt: str = Field(min_length=1)
    options: tuple[str, ...] = ()


class CreateBookLearningGoalRequestV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    intent: str = Field(min_length=1, max_length=2000)
    application_context: str | None = Field(default=None, max_length=500)
    deadline_at: datetime | None = None
    weekly_time_budget_minutes: int | None = Field(default=None, ge=1, le=10_080)
    idempotency_key: str = Field(min_length=1, max_length=200)


class ConfirmBookLearningGoalRequestV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    confirmed_by_user: bool
    idempotency_key: str = Field(min_length=1, max_length=200)


class MapBookLearningGoalRequestV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    idempotency_key: str = Field(min_length=1, max_length=200)


class StartBookDiagnosticRequestV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    mapping_id: UUID
    mapping_version: int = Field(ge=1)
    subgraph_id: UUID
    subgraph_version: int = Field(ge=1)
    target_knowledge_unit_id: UUID
    max_attempts: int = Field(default=3, ge=1, le=20)
    idempotency_key: str = Field(min_length=1, max_length=200)


class SubmitBookDiagnosticResponseV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    expected_need_version: int = Field(ge=1)
    response: Any
    assistance: AssistanceSnapshot
    idempotency_key: str = Field(min_length=1, max_length=200)


class GenerateBookPlanRequestV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    need_id: UUID
    idempotency_key: str = Field(min_length=1, max_length=200)


class SelectBookActivityRequestV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    goal_id: UUID
    idempotency_key: str = Field(min_length=1, max_length=200)


class AdvanceBookLearningRequestV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    idempotency_key: str = Field(min_length=1, max_length=200)


class StartBookTeachingRequestV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    goal_id: UUID
    plan_id: UUID
    plan_version: int = Field(ge=1)
    activity_id: UUID
    session_id: UUID | None = None
    turn_id: str = Field(min_length=1, max_length=200)
    turn_kind: Literal["learner", "system_start"] = "learner"
    learner_text: str | None = Field(default=None, max_length=20_000)
    idempotency_key: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def enforce_turn_input_boundary(self) -> StartBookTeachingRequestV1:
        text = (self.learner_text or "").strip()
        if self.turn_kind == "learner" and not text:
            raise ValueError("learner turn requires learner_text")
        if self.turn_kind == "system_start" and self.learner_text is not None:
            raise ValueError("system_start text is server-owned")
        return self


class BookLearningOperationResponseV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    operation: str
    owner_refs: tuple[BookLearningOwnerRefV1, ...]
    payload: dict[str, Any]
    correlation_id: str


class BookLearningTeachingResponseV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    reply_text: str
    teaching_action: TeachingActionV03
    evidence_bundle: EvidenceBundleV03
    owner_refs: tuple[BookLearningOwnerRefV1, ...]
    session_id: UUID
    turn_id: str
    turn_number: int = Field(ge=1)
    turn_kind: Literal["learner", "system_start"]
    accepted_at: datetime
    correlation_id: str
    model_execution: ModelExecutionV1 | None = None


class BookLearningTranscriptEvidenceV1(ContractModel):
    evidence_id: UUID
    source_span_ids: tuple[UUID, ...] = Field(min_length=1)
    pedagogical_role: str
    excerpt: str = Field(min_length=1, max_length=2_000)


class BookLearningTranscriptTurnV1(ContractModel):
    turn_id: str
    turn_number: int = Field(ge=1)
    turn_kind: Literal["learner", "system_start"]
    learner_text: str | None = None
    reply_text: str
    teaching_action_ref: VersionedRef
    evidence_bundle_ref: VersionedRef
    evidence: tuple[BookLearningTranscriptEvidenceV1, ...] = ()
    accepted_at: datetime
    model_execution: ModelExecutionV1 | None = None


class BookLearningTranscriptV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    session_id: UUID
    activity_ref: VersionedRef
    turns: tuple[BookLearningTranscriptTurnV1, ...]
    next_turn_number: int = Field(ge=1)
    correlation_id: str

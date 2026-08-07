"""SYS06/SYS07 的公共输入与派生投影合同。"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.contracts.base import ContractModel


class ReviewObservation(ContractModel):
    observation_id: UUID
    user_id: UUID
    knowledge_unit_id: UUID
    observed_at: datetime
    actual_reviewed_at: datetime
    retrieval_required: bool
    independence: Literal["independent", "assisted", "answer_exposed"]
    hint_level: int = Field(ge=0)
    answer_seen_before_attempt: bool
    assessment_confidence: float = Field(ge=0.0, le=1.0)
    outcome: Literal["success", "partial", "failure"]
    delay_seconds: int = Field(ge=0)
    source_evidence_id: UUID
    source_event_ids: list[UUID]


class ReviewDueCandidate(ContractModel):
    schedule_id: UUID
    schedule_version: int = Field(ge=1)
    user_id: UUID
    knowledge_unit_id: UUID
    status: Literal["not_due", "due", "overdue"]
    recommended_due_at: datetime | None
    projected_at: datetime
    urgency: float = Field(ge=0.0)


class ConfirmedLearningGoal(ContractModel):
    goal_id: UUID
    objective_id: UUID
    target_knowledge_unit_ids: list[UUID]
    confirmed_at: datetime

"""SYS04 的版本化评估题目与作答合同。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field

from app.contracts.base import ContractModel


class AssessmentItemV1(ContractModel):
    """首期确定性题型；答案键仅供 grader 使用。"""

    item_id: UUID
    version: str
    knowledge_unit_id: UUID
    item_type: Literal["multiple_choice", "exact"]
    prompt: str
    options: list[str] = Field(default_factory=list)
    answer_key: str
    difficulty: float = Field(ge=0.0)
    status: Literal["active", "retired"] = "active"


class AssistanceSnapshot(ContractModel):
    """提交瞬间冻结的帮助与暴露状态。"""

    hint_level: int = Field(ge=0)
    assistance_class: Literal["none", "hint", "worked_step", "full_solution"]
    source_visible: bool
    answer_visible: bool
    response_revision: int = Field(ge=1)
    response_time_ms: int = Field(ge=0)


class ResponseRevision(ContractModel):
    revision: int = Field(ge=1)
    raw_response: Any
    normalized_response: str
    submitted_at: datetime


class AssessmentAttempt(ContractModel):
    attempt_id: UUID
    user_id: UUID
    item_id: UUID
    item_version: str
    raw_response: Any
    normalized_response: str
    response_revisions: list[ResponseRevision]
    assistance: AssistanceSnapshot
    status: Literal["submitted", "scored", "scoring_failed"]
    submitted_at: datetime
    idempotency_key: str

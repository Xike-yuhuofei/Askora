"""SYS04 首期确定性评分实现。"""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import NAMESPACE_URL, UUID, uuid5

from app.contracts.assessment import (
    AssessmentAttempt,
    AssessmentItemV1,
    AssistanceSnapshot,
    ResponseRevision,
)
from app.contracts.learning import AssessmentResult


class ScoringUnavailableError(RuntimeError):
    """评分基础设施不可用；不得转译成用户答错。"""


def _normalize(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value).strip()).casefold()


class AssessmentScoringService:
    """Exact/MCQ deterministic grader；无模型与网络依赖。"""

    EVALUATOR_VERSION = "deterministic-exact/1.0"

    def submit(
        self,
        *,
        item: AssessmentItemV1,
        user_id: UUID,
        response: Any,
        assistance: AssistanceSnapshot,
        idempotency_key: str,
        submitted_at: datetime | None = None,
        workspace_id: UUID | None = None,
    ) -> AssessmentAttempt:
        if item.status != "active":
            raise ValueError("ASSESSMENT_ITEM_NOT_ACTIVE")
        timestamp = submitted_at or datetime.now(timezone.utc)
        scope = f"{workspace_id}:" if workspace_id else ""
        attempt_id = uuid5(NAMESPACE_URL, f"askora:attempt:{scope}{user_id}:{idempotency_key}")
        return AssessmentAttempt(
            attempt_id=attempt_id,
            user_id=user_id,
            item_id=item.item_id,
            item_version=item.version,
            raw_response=response,
            normalized_response=_normalize(response),
            response_revisions=[
                ResponseRevision(
                    revision=assistance.response_revision,
                    raw_response=response,
                    normalized_response=_normalize(response),
                    submitted_at=timestamp,
                )
            ],
            assistance=assistance,
            status="submitted",
            submitted_at=timestamp,
            idempotency_key=idempotency_key,
        )

    def revise(
        self,
        *,
        attempt: AssessmentAttempt,
        response: Any,
        assistance: AssistanceSnapshot,
        submitted_at: datetime | None = None,
    ) -> AssessmentAttempt:
        expected_revision = len(attempt.response_revisions) + 1
        if assistance.response_revision != expected_revision:
            raise ValueError("ASSESSMENT_RESPONSE_REVISION_CONFLICT")
        timestamp = submitted_at or datetime.now(timezone.utc)
        normalized = _normalize(response)
        revision = ResponseRevision(
            revision=expected_revision,
            raw_response=response,
            normalized_response=normalized,
            submitted_at=timestamp,
        )
        return attempt.model_copy(
            update={
                "raw_response": response,
                "normalized_response": normalized,
                "response_revisions": [*attempt.response_revisions, revision],
                "assistance": assistance,
                "submitted_at": timestamp,
            }
        )

    def score(
        self,
        *,
        item: AssessmentItemV1,
        attempt: AssessmentAttempt,
        result_version: int = 1,
        supersedes_result_id: UUID | None = None,
        clock: Callable[[], datetime] | None = None,
        infrastructure_probe: Callable[[], None] | None = None,
    ) -> AssessmentResult:
        if attempt.item_id != item.item_id or attempt.item_version != item.version:
            raise ValueError("ASSESSMENT_ITEM_VERSION_MISMATCH")
        if infrastructure_probe is not None:
            try:
                infrastructure_probe()
            except Exception as exc:
                raise ScoringUnavailableError("ASSESSMENT_SCORING_UNAVAILABLE") from exc

        correct = attempt.normalized_response == _normalize(item.answer_key)
        if (
            attempt.assistance.answer_visible
            or attempt.assistance.assistance_class == "full_solution"
        ):
            independence: Literal["independent", "assisted", "answer_exposed"] = "answer_exposed"
        elif attempt.assistance.assistance_class == "none":
            independence = "independent"
        else:
            independence = "assisted"
        result_id = uuid5(
            NAMESPACE_URL,
            f"askora:assessment-result:{attempt.attempt_id}:{result_version}",
        )
        created_at = (clock or (lambda: datetime.now(timezone.utc)))()
        return AssessmentResult(
            result_id=result_id,
            result_version=result_version,
            attempt_id=attempt.attempt_id,
            item_id=item.item_id,
            item_version=item.version,
            score=1.0 if correct else 0.0,
            passed=correct,
            correctness="correct" if correct else "incorrect",
            rubric_scores={"exact_match": 1.0 if correct else 0.0},
            error_type=None if correct else "unknown",
            misconception_evidence=[],
            independence=independence,
            assessment_confidence=1.0,
            evaluator_versions=[self.EVALUATOR_VERSION],
            reason_codes=["DETERMINISTIC_EXACT_MATCH"],
            reviewer_result="accepted",
            created_at=created_at,
            supersedes_result_id=supersedes_result_id,
        )

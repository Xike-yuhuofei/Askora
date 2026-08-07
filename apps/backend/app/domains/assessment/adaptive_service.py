"""SYS04 v0.3 assessment recording from actual SYS08 assistance facts."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal
from uuid import NAMESPACE_URL, UUID, uuid5

from app.contracts.adaptive import (
    AssessmentAttemptV03,
    AssessmentDiagnosisV03,
    AssessmentResultV03,
    AssistanceSnapshotV03,
    ErrorType,
    TeachingActionV03,
    ValidationObligation,
    VersionedRef,
)
from app.contracts.base import ContractModel


class AdaptiveAssessmentLink(ContractModel):
    teaching_action_ref: VersionedRef
    rendered_response_ref: VersionedRef
    validation_obligation: ValidationObligation
    validation_obligation_id: UUID | None = None


class AdaptiveAssessmentRecord(ContractModel):
    attempt: AssessmentAttemptV03
    result: AssessmentResultV03
    link: AdaptiveAssessmentLink


def _normalize(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value).strip()).casefold()


class AdaptiveAssessmentService:
    evaluator_version = "v03-deterministic-exact/1.0"

    def assess_exact(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        item_id: UUID,
        item_version: str,
        assessment_type: Literal["diagnostic", "formative", "summative", "review", "transfer"],
        response: Any,
        expected_answer: Any,
        teaching_action: TeachingActionV03,
        actual_assistance: AssistanceSnapshotV03,
        teaching_action_ref: VersionedRef,
        rendered_response_ref: VersionedRef,
        started_at: datetime,
        submitted_at: datetime,
        idempotency_key: str,
        assessment_confidence: float,
        diagnostic_error_type: ErrorType = ErrorType.UNKNOWN,
        diagnostic_confidence: float | None = None,
        validation_obligation_id: UUID | None = None,
    ) -> AdaptiveAssessmentRecord:
        if teaching_action_ref.entity_id != str(teaching_action.action_id):
            raise ValueError("SYS04_EXECUTION_ACTION_REF_MISMATCH")
        normalized = _normalize(response)
        correct = normalized == _normalize(expected_answer)
        attempt_id = uuid5(
            NAMESPACE_URL,
            f"askora:v03:attempt:{user_id}:{session_id}:{idempotency_key}",
        )
        response_time_ms = max(0, int((submitted_at - started_at).total_seconds() * 1000))
        attempt = AssessmentAttemptV03(
            attempt_id=attempt_id,
            user_id=user_id,
            session_id=session_id,
            item_id=item_id,
            item_version=item_version,
            assessment_type=assessment_type,
            started_at=started_at,
            first_response_at=submitted_at,
            submitted_at=submitted_at,
            response_time_ms=response_time_ms,
            raw_response=response,
            normalized_response=normalized,
            revision_count=0,
            assistance=actual_assistance,
            idempotency_key=idempotency_key,
        )
        result_id = uuid5(
            NAMESPACE_URL,
            f"askora:v03:assessment-result:{attempt_id}:1:{self.evaluator_version}",
        )
        result = AssessmentResultV03(
            result_id=result_id,
            result_version=1,
            attempt_id=attempt_id,
            item_id=item_id,
            item_version=item_version,
            score=1.0 if correct else 0.0,
            passed=correct,
            correctness="correct" if correct else "incorrect",
            rubric_scores={"exact_match": 1.0 if correct else 0.0},
            assessment_confidence=assessment_confidence,
            diagnosis=AssessmentDiagnosisV03(
                error_type=ErrorType.UNKNOWN if correct else diagnostic_error_type,
                diagnostic_confidence=diagnostic_confidence,
                needs_probe=(not correct and diagnostic_error_type is ErrorType.UNKNOWN),
                reason_codes=(
                    (
                        "CORRECT_NO_ERROR_ATTRIBUTION"
                        if correct
                        else "V03_DETERMINISTIC_DIAGNOSIS_INPUT"
                    ),
                ),
            ),
            assistance=actual_assistance,
            evaluator_versions=(self.evaluator_version,),
            reviewer_result="accepted",
            created_at=submitted_at,
        )
        link = AdaptiveAssessmentLink(
            teaching_action_ref=teaching_action_ref,
            rendered_response_ref=rendered_response_ref,
            validation_obligation=teaching_action.validation_obligation,
            validation_obligation_id=validation_obligation_id,
        )
        return AdaptiveAssessmentRecord(attempt=attempt, result=result, link=link)

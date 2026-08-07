"""SYS03 v0.3 evidence eligibility using actual assistance only."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import Field, model_validator

from app.contracts.adaptive import (
    AssessmentAttemptV03,
    AssessmentResultV03,
    AssistanceSnapshotV03,
    AssistanceState,
    LearnerEvidenceV03,
    VersionedRef,
)
from app.contracts.base import ContractModel


class AdaptiveEvidenceEligibilityProfile(ContractModel):
    profile_version: str = Field(min_length=1)
    minimum_assessment_confidence: float = Field(ge=0.0, le=1.0)
    independence_weights: dict[AssistanceState, float]
    novelty_weights: dict[str, float]

    @model_validator(mode="after")
    def enforce_assistance_weight_safety(self) -> AdaptiveEvidenceEligibilityProfile:
        required = set(AssistanceState)
        if set(self.independence_weights) != required:
            raise ValueError("eligibility profile must define all assistance states exactly")
        if self.independence_weights[AssistanceState.ANSWER_EXPOSED] != 0.0:
            raise ValueError("ANSWER_EXPOSED must have zero independent evidence weight")
        if not (
            self.independence_weights[AssistanceState.INDEPENDENT]
            >= self.independence_weights[AssistanceState.ASSISTED]
            >= 0.0
        ):
            raise ValueError("assistance weights must be monotonic and non-negative")
        return self


@dataclass(frozen=True)
class AdaptiveEvidenceDecision:
    accepted: bool
    reason_codes: tuple[str, ...]
    evidence: LearnerEvidenceV03 | None


_ASSISTANCE_RANK = {
    AssistanceState.INDEPENDENT: 0,
    AssistanceState.ASSISTED: 1,
    AssistanceState.ANSWER_EXPOSED: 2,
}


class AdaptiveEvidenceEligibility:
    """Produces evidence; it never writes or projects MasteryEstimate itself."""

    def decide(
        self,
        *,
        result: AssessmentResultV03,
        attempt: AssessmentAttemptV03,
        actual_assistance: AssistanceSnapshotV03 | None,
        profile: AdaptiveEvidenceEligibilityProfile,
        knowledge_unit_id: UUID,
        dimension: Literal["recall", "routine_application", "transfer", "explanation"],
        novelty: Literal["repeated", "near_variant", "far_variant"],
        delay_seconds: int,
        source_event_refs: tuple[VersionedRef, ...],
        item_difficulty: float | None = None,
    ) -> AdaptiveEvidenceDecision:
        if actual_assistance is None:
            return AdaptiveEvidenceDecision(
                accepted=False,
                reason_codes=("V03_ASSISTANCE_UNKNOWN_CONSERVATIVE_REJECT",),
                evidence=None,
            )
        if result.attempt_id != attempt.attempt_id or result.item_version != attempt.item_version:
            return AdaptiveEvidenceDecision(False, ("V03_ATTEMPT_RESULT_MISMATCH",), None)
        if result.reviewer_result != "accepted" or result.correctness == "unscorable":
            return AdaptiveEvidenceDecision(False, ("V03_ASSESSMENT_NOT_ELIGIBLE",), None)
        if result.assessment_confidence < profile.minimum_assessment_confidence:
            return AdaptiveEvidenceDecision(False, ("V03_ASSESSMENT_CONFIDENCE_TOO_LOW",), None)
        if not source_event_refs:
            return AdaptiveEvidenceDecision(False, ("V03_MISSING_AUDIT_EVENT",), None)

        states = (
            actual_assistance.assistance_state,
            attempt.assistance.assistance_state,
            result.assistance.assistance_state,
        )
        effective_state = max(states, key=lambda state: _ASSISTANCE_RANK[state])
        reason_codes = [profile.profile_version]
        if len(set(states)) > 1:
            reason_codes.append("V03_ASSISTANCE_MISMATCH_CONSERVATIVE_MAX")
        if effective_state is AssistanceState.ANSWER_EXPOSED:
            reason_codes.append("V03_ANSWER_EXPOSED_ZERO_INDEPENDENT_WEIGHT")
        elif effective_state is AssistanceState.ASSISTED:
            reason_codes.append("V03_ASSISTED_EVIDENCE_DISCOUNTED")
        else:
            reason_codes.append("V03_INDEPENDENT_EVIDENCE")

        independence_weight = profile.independence_weights.get(effective_state)
        novelty_weight = profile.novelty_weights.get(novelty)
        if independence_weight is None or novelty_weight is None:
            return AdaptiveEvidenceDecision(False, ("V03_ELIGIBILITY_PROFILE_INCOMPLETE",), None)
        evidence_weight = independence_weight * novelty_weight * result.assessment_confidence
        outcome: Literal["success", "partial", "failure"] = (
            "success"
            if result.correctness == "correct"
            else "partial" if result.correctness == "partial" else "failure"
        )
        evidence = LearnerEvidenceV03(
            evidence_id=uuid5(NAMESPACE_URL, f"askora:v03:learner-evidence:{result.result_id}"),
            user_id=attempt.user_id,
            knowledge_unit_id=knowledge_unit_id,
            attempt_ref=VersionedRef(
                entity_type="assessment_attempt",
                entity_id=str(attempt.attempt_id),
                version=attempt.attempt_schema_version,
            ),
            result_ref=VersionedRef(
                entity_type="assessment_result",
                entity_id=str(result.result_id),
                version=result.result_version,
            ),
            accepted_at=result.created_at,
            dimension=dimension,
            outcome=outcome,
            score=result.score,
            confidence=result.assessment_confidence,
            assistance_state=effective_state,
            delay_seconds=delay_seconds,
            novelty=novelty,
            evidence_weight=evidence_weight,
            item_difficulty=item_difficulty,
            source_event_refs=source_event_refs,
            eligibility_reason_codes=tuple(reason_codes),
            eligibility_algorithm_version=profile.profile_version,
        )
        return AdaptiveEvidenceDecision(True, tuple(reason_codes), evidence)

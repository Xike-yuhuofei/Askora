"""版本化、可重放且不依赖在线模型的 canonical mastery projector。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal
from uuid import NAMESPACE_URL, UUID, uuid5

from app.contracts.assessment import AssessmentAttempt
from app.contracts.learning import AssessmentResult, LearnerEvidence, MasteryEstimate


@dataclass(frozen=True)
class EvidenceDecision:
    accepted: bool
    reason_codes: tuple[str, ...]
    evidence: LearnerEvidence | None


class EvidenceEligibility:
    """SYS03 独立接纳；权重表是 baseline v1 的公共算法参数。"""

    ALGORITHM_VERSION = "evidence-eligibility/1.0"
    INDEPENDENCE_WEIGHTS = {"independent": 1.0, "assisted": 0.35, "answer_exposed": 0.0}
    NOVELTY_WEIGHTS = {"repeated": 0.5, "near_variant": 0.8, "far_variant": 1.0}

    def decide(
        self,
        *,
        result: AssessmentResult,
        attempt: AssessmentAttempt,
        knowledge_unit_id: UUID,
        dimension: Literal["recall", "routine_application", "transfer", "explanation"],
        novelty: Literal["repeated", "near_variant", "far_variant"],
        delay_seconds: int,
        source_event_ids: list[UUID],
        item_difficulty: float | None = None,
    ) -> EvidenceDecision:
        if result.attempt_id != attempt.attempt_id or result.item_version != attempt.item_version:
            return EvidenceDecision(False, ("ITEM_OR_ATTEMPT_VERSION_MISMATCH",), None)
        if result.reviewer_result != "accepted":
            return EvidenceDecision(False, ("ASSESSMENT_NOT_ACCEPTED",), None)
        if result.correctness == "unscorable":
            return EvidenceDecision(False, ("ASSESSMENT_UNSCORABLE",), None)
        if result.assessment_confidence < 0.5:
            return EvidenceDecision(False, ("ASSESSMENT_CONFIDENCE_TOO_LOW",), None)
        if not source_event_ids:
            return EvidenceDecision(False, ("MISSING_AUDIT_EVENT",), None)

        independence_weight = self.INDEPENDENCE_WEIGHTS[result.independence]
        novelty_weight = self.NOVELTY_WEIGHTS[novelty]
        evidence_weight = independence_weight * novelty_weight * result.assessment_confidence
        reason_codes = [self.ALGORITHM_VERSION]
        if result.independence == "answer_exposed":
            reason_codes.append("ANSWER_EXPOSED_ZERO_WEIGHT")
        elif result.independence == "assisted":
            reason_codes.append("ASSISTED_EVIDENCE_DISCOUNTED")
        else:
            reason_codes.append("INDEPENDENT_EVIDENCE")

        evidence_id = uuid5(NAMESPACE_URL, f"askora:evidence:{result.result_id}")
        outcome: Literal["success", "partial", "failure"] = (
            "success"
            if result.correctness == "correct"
            else "partial"
            if result.correctness == "partial"
            else "failure"
        )
        evidence = LearnerEvidence(
            evidence_id=evidence_id,
            user_id=attempt.user_id,
            knowledge_unit_id=knowledge_unit_id,
            attempt_id=attempt.attempt_id,
            result_id=result.result_id,
            accepted_at=result.created_at,
            dimension=dimension,
            outcome=outcome,
            score=result.score,
            confidence=result.assessment_confidence,
            independence=result.independence,
            delay_seconds=delay_seconds,
            novelty=novelty,
            evidence_weight=evidence_weight,
            item_difficulty=item_difficulty,
            source_event_ids=source_event_ids,
            eligibility_reason_codes=reason_codes,
        )
        return EvidenceDecision(True, tuple(reason_codes), evidence)


class WeightedBKTProjector:
    """SYS03 canonical baseline；固定参数、纯函数、排序重放。"""

    ALGORITHM_ID = "weighted-bkt"
    ALGORITHM_VERSION = "1.0"
    P_INIT = 0.30
    P_TRANSIT = 0.15
    P_SLIP = 0.10
    P_GUESS = 0.20

    def project(
        self,
        *,
        user_id: UUID,
        knowledge_unit_id: UUID,
        evidence: list[LearnerEvidence],
        version: int,
        invalidated_evidence_ids: set[UUID] | None = None,
    ) -> MasteryEstimate:
        invalidated = invalidated_evidence_ids or set()
        ordered = sorted(
            (item for item in evidence if item.evidence_id not in invalidated),
            key=lambda item: (item.accepted_at, str(item.evidence_id)),
        )
        probability = self.P_INIT
        effective_weight = 0.0
        for item in ordered:
            if item.outcome == "success":
                likelihood_mastered = 1.0 - self.P_SLIP
                likelihood_unmastered = self.P_GUESS
            elif item.outcome == "failure":
                likelihood_mastered = self.P_SLIP
                likelihood_unmastered = 1.0 - self.P_GUESS
            else:
                likelihood_mastered = likelihood_unmastered = 0.5
            denominator = probability * likelihood_mastered + (1 - probability) * likelihood_unmastered
            observed = probability if denominator == 0 else probability * likelihood_mastered / denominator
            weighted = probability + item.evidence_weight * (observed - probability)
            probability = weighted + (1.0 - weighted) * self.P_TRANSIT * item.evidence_weight
            probability = min(1.0, max(0.0, probability))
            effective_weight += item.evidence_weight

        independent_successes = [
            item
            for item in ordered
            if item.independence == "independent" and item.outcome == "success"
        ]
        delayed = [item for item in ordered if item.delay_seconds >= 86_400 and item.outcome == "success"]
        transfers = [
            item for item in ordered if item.dimension == "transfer" and item.outcome == "success"
        ]
        assisted_weight = sum(
            item.evidence_weight for item in ordered if item.independence != "independent"
        )
        source_ids = [item.evidence_id for item in ordered]
        created_at = max(
            (item.accepted_at for item in ordered),
            default=datetime(1970, 1, 1, tzinfo=timezone.utc),
        )
        estimate_id = uuid5(
            NAMESPACE_URL,
            "askora:mastery:"
            + ":".join(
                [
                    str(user_id),
                    str(knowledge_unit_id),
                    str(version),
                    self.ALGORITHM_VERSION,
                    *[str(item_id) for item_id in source_ids],
                ]
            ),
        )
        return MasteryEstimate(
            estimate_id=estimate_id,
            version=version,
            user_id=user_id,
            knowledge_unit_id=knowledge_unit_id,
            competence_probability=probability,
            confidence=effective_weight / (effective_weight + 2.0),
            independent_success_count=len(independent_successes),
            hint_dependency_score=assisted_weight / effective_weight if effective_weight else 0.0,
            last_independent_success_at=(
                max(item.accepted_at for item in independent_successes)
                if independent_successes
                else None
            ),
            delayed_recall_evidence_count=len(delayed),
            transfer_evidence_count=len(transfers),
            active_misconception_ids=[],
            evidence_count=len(ordered),
            effective_evidence_weight=effective_weight,
            algorithm_id=self.ALGORITHM_ID,
            algorithm_version=self.ALGORITHM_VERSION,
            source_evidence_ids=source_ids,
            created_at=created_at,
        )

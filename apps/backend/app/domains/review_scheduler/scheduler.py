"""无在线模型依赖的 FSRS-compatible 可解释 baseline。"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal
from uuid import NAMESPACE_URL, uuid5

from app.contracts.learning import LearnerEvidence, ReviewSchedule
from app.contracts.planning import ReviewDueCandidate, ReviewObservation


@dataclass(frozen=True)
class ReviewScheduleDecision:
    schedule: ReviewSchedule
    reason_codes: tuple[str, ...]
    prior_state: dict[str, float | None]
    new_state: dict[str, float | None]


def observation_from_evidence(evidence: LearnerEvidence) -> ReviewObservation:
    """将 SYS03 已接纳证据适配成可审计复习观察，不重新判分。"""
    return ReviewObservation(
        observation_id=uuid5(NAMESPACE_URL, f"askora:review-observation:{evidence.evidence_id}"),
        user_id=evidence.user_id,
        knowledge_unit_id=evidence.knowledge_unit_id,
        observed_at=evidence.accepted_at,
        actual_reviewed_at=evidence.accepted_at,
        retrieval_required=evidence.dimension in {"recall", "routine_application"},
        independence=evidence.independence,
        hint_level=0 if evidence.independence == "independent" else 1,
        answer_seen_before_attempt=evidence.independence == "answer_exposed",
        assessment_confidence=evidence.confidence,
        outcome=evidence.outcome,
        delay_seconds=evidence.delay_seconds,
        source_evidence_id=evidence.evidence_id,
        source_event_ids=evidence.source_event_ids,
    )


class ReviewScheduler:
    """SYS07 唯一 next_due_at 计算器。"""

    MEMORY_MODEL = "fsrs-compatible-exponential"
    MODEL_VERSION = "1.0"
    FALLBACK_MODEL = "simple-exponential"
    FALLBACK_VERSION = "1.0"

    def update(
        self,
        *,
        observation: ReviewObservation,
        prior: ReviewSchedule | None,
        version: int,
        desired_retention: float = 0.90,
        parameters: dict[str, float] | None = None,
    ) -> ReviewScheduleDecision:
        retention = min(0.95, max(0.75, desired_retention))
        reasons = ["REVIEW_OBSERVATION_APPLIED"]
        if retention != desired_retention:
            reasons.append("DESIRED_RETENTION_CLAMPED")
        try:
            params = parameters or {
                "initial_stability": 1.0,
                "success_growth": 1.8,
                "failure_decay": 0.45,
                "assisted_growth": 1.12,
            }
            required = {
                "initial_stability",
                "success_growth",
                "failure_decay",
                "assisted_growth",
            }
            if set(params) != required or any(value <= 0 for value in params.values()):
                raise ValueError("invalid scheduler parameters")
            model, model_version = self.MEMORY_MODEL, self.MODEL_VERSION
        except (TypeError, ValueError):
            params = {
                "initial_stability": 1.0,
                "success_growth": 1.5,
                "failure_decay": 0.5,
                "assisted_growth": 1.05,
            }
            model, model_version = self.FALLBACK_MODEL, self.FALLBACK_VERSION
            reasons.append("MEMORY_MODEL_FALLBACK")

        prior_stability = (
            prior.stability if prior and prior.stability else params["initial_stability"]
        )
        prior_difficulty = prior.difficulty if prior and prior.difficulty else 5.0
        valid_independent = (
            observation.retrieval_required
            and observation.independence == "independent"
            and not observation.answer_seen_before_attempt
            and observation.hint_level == 0
            and observation.assessment_confidence >= 0.5
        )
        if observation.outcome == "failure":
            stability = max(0.25, prior_stability * params["failure_decay"])
            difficulty = min(10.0, prior_difficulty + 0.7)
            quality = observation.assessment_confidence
            reasons.append("RETRIEVAL_FAILURE_SHORTENED")
        elif observation.outcome == "success" and valid_independent:
            delay_factor = 1.0 + min(observation.delay_seconds / 604_800, 1.0) * 0.25
            stability = prior_stability * params["success_growth"] * delay_factor
            difficulty = max(1.0, prior_difficulty - 0.3)
            quality = observation.assessment_confidence
            reasons.append("INDEPENDENT_RECALL_EXTENDED")
        elif observation.independence == "answer_exposed" or observation.answer_seen_before_attempt:
            stability = max(0.25, prior_stability * 0.8)
            difficulty = min(10.0, prior_difficulty + 0.2)
            quality = 0.0
            reasons.append("ANSWER_EXPOSED_NOT_VALID_RECALL")
        else:
            stability = prior_stability * params["assisted_growth"]
            difficulty = prior_difficulty
            quality = observation.assessment_confidence * 0.35
            reasons.append("ASSISTED_RECALL_DISCOUNTED")

        # Exponential forgetting R(t)=exp(-t/S); solve t=-S*ln(target retention).
        interval_days = max(0.25, -stability * math.log(retention) * 10.0)
        recommended_due = observation.observed_at + timedelta(days=interval_days)
        elapsed_days = max(observation.delay_seconds / 86_400, 0.0)
        retrievability = math.exp(-elapsed_days / max(stability, 0.01))
        source_events = sorted(
            {
                *(prior.source_event_ids if prior else []),
                *observation.source_event_ids,
            },
            key=str,
        )
        schedule_id = uuid5(
            NAMESPACE_URL,
            f"askora:review-schedule:{observation.user_id}:{observation.knowledge_unit_id}",
        )
        schedule = ReviewSchedule(
            schedule_id=schedule_id,
            version=version,
            user_id=observation.user_id,
            knowledge_unit_id=observation.knowledge_unit_id,
            memory_model=model,
            model_version=model_version,
            difficulty=difficulty,
            stability=stability,
            retrievability=retrievability,
            desired_retention=retention,
            last_valid_retrieval_at=(
                observation.actual_reviewed_at
                if valid_independent
                else prior.last_valid_retrieval_at if prior else None
            ),
            next_due_at=recommended_due,
            review_priority=max(0.0, 1.0 - retrievability),
            evidence_quality=quality,
            source_event_ids=source_events,
            created_at=observation.observed_at,
        )
        return ReviewScheduleDecision(
            schedule=schedule,
            reason_codes=tuple(reasons),
            prior_state={"stability": prior_stability, "difficulty": prior_difficulty},
            new_state={"stability": stability, "difficulty": difficulty},
        )


def project_due(schedule: ReviewSchedule, *, at: datetime) -> ReviewDueCandidate:
    """LIFE-120：时间流逝只形成派生投影，不写新 schedule row。"""
    if schedule.next_due_at is None or at < schedule.next_due_at:
        status: Literal["not_due", "due", "overdue"] = "not_due"
        urgency = 0.0
    else:
        overdue_seconds = max(0.0, (at - schedule.next_due_at).total_seconds())
        status = "overdue" if overdue_seconds >= 86_400 else "due"
        urgency = 1.0 + overdue_seconds / 86_400
    return ReviewDueCandidate(
        schedule_id=schedule.schedule_id,
        schedule_version=schedule.version,
        user_id=schedule.user_id,
        knowledge_unit_id=schedule.knowledge_unit_id,
        status=status,
        recommended_due_at=schedule.next_due_at,
        projected_at=at,
        urgency=urgency,
    )

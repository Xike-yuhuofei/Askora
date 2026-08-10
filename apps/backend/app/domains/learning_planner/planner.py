"""首期可解释 greedy + hard prerequisite repair planner。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import NAMESPACE_URL, UUID, uuid5

from app.contracts.learning import LearningActivity, LearningPlan
from app.contracts.planning import ConfirmedLearningGoal, ReviewDueCandidate

ActivityType = Literal[
    "learn_new",
    "prerequisite_remediation",
    "diagnostic",
    "practice",
    "delayed_review",
    "transfer_check",
    "metacognitive_review",
]


@dataclass(frozen=True)
class PlannerDecision:
    plan: LearningPlan
    activities: tuple[LearningActivity, ...]
    scoring_trace: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class _Candidate:
    kind: ActivityType
    knowledge_unit_id: UUID
    duration: int
    priority: float
    reason_codes: tuple[str, ...]


class LearningPlanner:
    """SYS06 owner；只消费 ReviewDueCandidate，不导入或调用 SYS07 scheduler。"""

    PLANNER_VERSION = "heuristic-greedy/1.0"
    WEIGHTS = {
        "goal_relevance": 1.0,
        "mastery_gap": 0.8,
        "review_urgency": 0.9,
        "uncertainty": 0.7,
        "prerequisite": 1.1,
    }
    DURATIONS = {
        "diagnostic": 5,
        "prerequisite_remediation": 12,
        "learn_new": 15,
        "delayed_review": 8,
        "transfer_check": 10,
    }

    @staticmethod
    def _mastery_bucket(value: float | None) -> str:
        if value is None:
            return "unknown"
        if value < 0.70:
            return "low"
        if value < 0.85:
            return "developing"
        return "mastered"

    def generate(
        self,
        *,
        goal: ConfirmedLearningGoal,
        prerequisites: dict[UUID, list[UUID]],
        mastery: dict[UUID, float | None],
        due_candidates: list[ReviewDueCandidate],
        time_budget_minutes: int,
        learner_state_version: int,
        knowledge_graph_version: str,
        version: int,
        created_at: datetime,
        reason_codes: list[str] | None = None,
    ) -> PlannerDecision:
        del created_at  # plan contract has no timestamp; caller persists it separately.
        plan_id = uuid5(NAMESPACE_URL, f"askora:learning-plan:{goal.goal_id}")
        candidates: list[_Candidate] = []

        for due in due_candidates:
            if due.status not in {"due", "overdue"}:
                continue
            candidates.append(
                _Candidate(
                    kind="delayed_review",
                    knowledge_unit_id=due.knowledge_unit_id,
                    duration=self.DURATIONS["delayed_review"],
                    priority=self.WEIGHTS["review_urgency"] * due.urgency,
                    reason_codes=(
                        "PLAN_REVIEW_OVERDUE" if due.status == "overdue" else "PLAN_REVIEW_DUE",
                    ),
                )
            )

        for target_id in sorted(goal.target_knowledge_unit_ids, key=str):
            unmet = []
            unknown = []
            for prerequisite_id in sorted(prerequisites.get(target_id, []), key=str):
                bucket = self._mastery_bucket(mastery.get(prerequisite_id))
                if bucket == "unknown":
                    unknown.append(prerequisite_id)
                elif bucket in {"low", "developing"}:
                    unmet.append(prerequisite_id)
            if unknown:
                for prerequisite_id in unknown:
                    candidates.append(
                        _Candidate(
                            kind="diagnostic",
                            knowledge_unit_id=prerequisite_id,
                            duration=self.DURATIONS["diagnostic"],
                            priority=self.WEIGHTS["prerequisite"] + self.WEIGHTS["uncertainty"],
                            reason_codes=("PLAN_PREREQUISITE_UNKNOWN", "PLAN_DIAGNOSTIC_REQUIRED"),
                        )
                    )
                continue
            if unmet:
                for prerequisite_id in unmet:
                    candidates.append(
                        _Candidate(
                            kind="prerequisite_remediation",
                            knowledge_unit_id=prerequisite_id,
                            duration=self.DURATIONS["prerequisite_remediation"],
                            priority=self.WEIGHTS["prerequisite"] + self.WEIGHTS["mastery_gap"],
                            reason_codes=("PLAN_HARD_PREREQUISITE_UNMET",),
                        )
                    )
                continue

            target_bucket = self._mastery_bucket(mastery.get(target_id))
            if target_bucket == "unknown":
                kind: ActivityType = "diagnostic"
                reasons = ("PLAN_TARGET_STATE_UNKNOWN",)
                priority = self.WEIGHTS["goal_relevance"] + self.WEIGHTS["uncertainty"]
            elif target_bucket == "mastered":
                kind = "transfer_check"
                reasons = ("PLAN_TRANSFER_EVIDENCE_NEEDED",)
                priority = self.WEIGHTS["goal_relevance"]
            else:
                kind = "learn_new"
                reasons = ("PLAN_MASTERY_GAP",)
                priority = self.WEIGHTS["goal_relevance"] + self.WEIGHTS["mastery_gap"]
            candidates.append(
                _Candidate(
                    kind=kind,
                    knowledge_unit_id=target_id,
                    duration=self.DURATIONS[kind],
                    priority=priority,
                    reason_codes=reasons,
                )
            )

        candidates.sort(key=lambda item: (-item.priority, item.kind, str(item.knowledge_unit_id)))
        remaining = max(0, time_budget_minutes)
        selected: list[_Candidate] = []
        seen: set[tuple[str, UUID]] = set()
        for candidate in candidates:
            identity = (candidate.kind, candidate.knowledge_unit_id)
            if identity in seen or candidate.duration > remaining:
                continue
            selected.append(candidate)
            seen.add(identity)
            remaining -= candidate.duration
        if not selected and candidates:
            selected.append(min(candidates, key=lambda item: (item.duration, -item.priority)))

        activities = tuple(
            LearningActivity(
                activity_id=uuid5(
                    NAMESPACE_URL,
                    f"askora:activity:{plan_id}:{version}:{item.kind}:{item.knowledge_unit_id}",
                ),
                plan_id=plan_id,
                plan_version=version,
                objective_id=goal.objective_id,
                type=item.kind,
                knowledge_unit_ids=[item.knowledge_unit_id],
                estimated_duration_minutes=item.duration,
                priority=item.priority,
                reason_codes=list(item.reason_codes),
                status="planned",
            )
            for item in selected
        )
        review_versions = sorted(
            {
                f"{candidate.schedule_id}:{candidate.schedule_version}"
                for candidate in due_candidates
                if candidate.status in {"due", "overdue"}
            }
        )
        plan = LearningPlan(
            plan_id=plan_id,
            version=version,
            learning_goal_id=goal.goal_id,
            planning_horizon={"kind": "daily", "time_budget_minutes": time_budget_minutes},
            objective_ids=[goal.objective_id],
            activity_ids=[activity.activity_id for activity in activities],
            constraints={"hard_prerequisites": True, "time_budget_minutes": time_budget_minutes},
            assumptions={"planner_version": self.PLANNER_VERSION, "weights": self.WEIGHTS},
            created_from_learner_state_version=learner_state_version,
            knowledge_graph_version=knowledge_graph_version,
            review_schedule_version=",".join(review_versions) if review_versions else None,
            reason_codes=reason_codes or ["PLAN_INITIAL_GENERATION"],
            status="active",
        )
        trace = tuple(
            {
                "kind": item.kind,
                "knowledge_unit_id": str(item.knowledge_unit_id),
                "priority": item.priority,
                "duration": item.duration,
                "selected": item in selected,
            }
            for item in candidates
        )
        return PlannerDecision(plan=plan, activities=activities, scoring_trace=trace)

    @staticmethod
    def is_material_change(
        *, prior_mastery: dict[UUID, float | None], new_mastery: dict[UUID, float | None]
    ) -> bool:
        keys = set(prior_mastery) | set(new_mastery)
        for key in keys:
            before, after = prior_mastery.get(key), new_mastery.get(key)
            if before is None or after is None:
                if before != after:
                    return True
            elif abs(before - after) >= 0.05:
                return True
        return False

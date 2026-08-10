from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.contracts.planning import ConfirmedLearningGoal, ReviewDueCandidate
from app.domains.learning_planner import LearningPlanner

NOW = datetime(2026, 8, 7, 11, 0, tzinfo=timezone.utc)


def _goal(target_id):
    return ConfirmedLearningGoal(
        goal_id=uuid4(),
        objective_id=uuid4(),
        target_knowledge_unit_ids=[target_id],
        confirmed_at=NOW,
    )


def test_planner_repairs_unmet_prerequisite_and_unknown_state() -> None:
    planner = LearningPlanner()
    target, prerequisite = uuid4(), uuid4()
    goal = _goal(target)
    unknown = planner.generate(
        goal=goal,
        prerequisites={target: [prerequisite]},
        mastery={prerequisite: None},
        due_candidates=[],
        time_budget_minutes=30,
        learner_state_version=1,
        knowledge_graph_version="kg-1",
        version=1,
        created_at=NOW,
    )
    unmet = planner.generate(
        goal=goal,
        prerequisites={target: [prerequisite]},
        mastery={prerequisite: 0.4},
        due_candidates=[],
        time_budget_minutes=30,
        learner_state_version=2,
        knowledge_graph_version="kg-1",
        version=2,
        created_at=NOW,
    )
    assert [activity.type for activity in unknown.activities] == ["diagnostic"]
    assert [activity.type for activity in unmet.activities] == ["prerequisite_remediation"]
    assert all(
        target not in activity.knowledge_unit_ids
        for activity in (*unknown.activities, *unmet.activities)
    )


def test_planner_consumes_due_candidate_without_modifying_schedule_state() -> None:
    planner = LearningPlanner()
    target, review_unit, user_id = uuid4(), uuid4(), uuid4()
    due = ReviewDueCandidate(
        schedule_id=uuid4(),
        schedule_version=4,
        user_id=user_id,
        knowledge_unit_id=review_unit,
        status="overdue",
        recommended_due_at=NOW - timedelta(days=2),
        projected_at=NOW,
        urgency=3.0,
    )
    before = due.model_dump()
    decision = planner.generate(
        goal=_goal(target),
        prerequisites={},
        mastery={target: 0.5},
        due_candidates=[due],
        time_budget_minutes=30,
        learner_state_version=3,
        knowledge_graph_version="kg-1",
        version=1,
        created_at=NOW,
    )
    assert "delayed_review" in [activity.type for activity in decision.activities]
    assert all(
        activity.objective_id == decision.plan.objective_ids[0] for activity in decision.activities
    )
    assert all(activity.reason_codes for activity in decision.activities)
    assert decision.plan.review_schedule_version == f"{due.schedule_id}:4"
    assert due.model_dump() == before


def test_planner_replay_budget_and_small_change_stability() -> None:
    planner = LearningPlanner()
    target = uuid4()
    goal = _goal(target)
    kwargs = dict(
        goal=goal,
        prerequisites={},
        mastery={target: 0.5},
        due_candidates=[],
        time_budget_minutes=15,
        learner_state_version=7,
        knowledge_graph_version="kg-7",
        version=1,
        created_at=NOW,
    )
    first = planner.generate(**kwargs)
    replayed = planner.generate(**kwargs)
    assert replayed == first
    assert sum(item.estimated_duration_minutes for item in first.activities) <= 15
    assert not planner.is_material_change(prior_mastery={target: 0.50}, new_mastery={target: 0.53})
    assert planner.is_material_change(prior_mastery={target: 0.50}, new_mastery={target: 0.60})

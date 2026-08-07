from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.contracts.planning import ConfirmedLearningGoal, ReviewObservation
from app.core.database import Base
from app.infrastructure.outbox import OutboxProducer
from app.infrastructure.planning_records import LearningPlanRepository, ReviewScheduleRepository
from app.models.ledger import OutboxTaskRecord
from app.orchestration.review_planning import ReviewPlanningApplication

NOW = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_schedule_plan_and_pending_due_work_survive_restart(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'review-plan.db'}"
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    user_id, knowledge_unit_id = uuid4(), uuid4()
    goal = ConfirmedLearningGoal(
        goal_id=uuid4(),
        objective_id=uuid4(),
        target_knowledge_unit_ids=[knowledge_unit_id],
        confirmed_at=NOW,
    )
    observation = ReviewObservation(
        observation_id=uuid4(),
        user_id=user_id,
        knowledge_unit_id=knowledge_unit_id,
        observed_at=NOW,
        actual_reviewed_at=NOW - timedelta(minutes=1),
        retrieval_required=True,
        independence="independent",
        hint_level=0,
        answer_seen_before_attempt=False,
        assessment_confidence=1.0,
        outcome="success",
        delay_seconds=86_400,
        source_evidence_id=uuid4(),
        source_event_ids=[uuid4()],
    )

    async with factory() as session:
        application = ReviewPlanningApplication(
            ReviewScheduleRepository(session),
            LearningPlanRepository(session),
            OutboxProducer(session),
        )
        schedule = await application.apply_review_observation(observation)
        duplicate = await application.apply_review_observation(observation)
        assert duplicate == schedule
        invalidated_event_id = uuid4()
        invalidated_observation = observation.model_copy(
            update={
                "observation_id": uuid4(),
                "observed_at": NOW + timedelta(days=1),
                "actual_reviewed_at": NOW + timedelta(days=1),
                "outcome": "failure",
                "source_evidence_id": uuid4(),
                "source_event_ids": [invalidated_event_id],
            }
        )
        second_schedule = await application.apply_review_observation(invalidated_observation)
        schedule = await application.recompute_after_observation_invalidation(
            observation_id=invalidated_observation.observation_id,
            user_id=user_id,
            knowledge_unit_id=knowledge_unit_id,
        )
        assert schedule.version == second_schedule.version + 1
        assert invalidated_event_id not in schedule.source_event_ids
        assert schedule.source_event_ids == observation.source_event_ids
        first_plan = await application.generate_plan(
            goal=goal,
            user_id=user_id,
            prerequisites={},
            mastery={knowledge_unit_id: 0.6},
            time_budget_minutes=30,
            learner_state_version=1,
            knowledge_graph_version="kg-1",
            at=schedule.next_due_at + timedelta(days=2),
            idempotency_key="plan-command-1",
        )
        same_plan = await application.generate_plan(
            goal=goal,
            user_id=user_id,
            prerequisites={},
            mastery={knowledge_unit_id: 0.6},
            time_budget_minutes=30,
            learner_state_version=1,
            knowledge_graph_version="kg-1",
            at=schedule.next_due_at + timedelta(days=2),
            idempotency_key="plan-command-1",
        )
        assert same_plan == first_plan
        await session.commit()

    await engine.dispose()
    restarted_engine = create_async_engine(database_url)
    restarted_factory = async_sessionmaker(restarted_engine, expire_on_commit=False)
    async with restarted_factory() as session:
        restored_schedule = await ReviewScheduleRepository(session).latest(
            user_id=user_id, knowledge_unit_id=knowledge_unit_id
        )
        plan_versions = await LearningPlanRepository(session).list_versions(goal.goal_id)
        pending = (
            await session.scalars(
                select(OutboxTaskRecord).where(OutboxTaskRecord.status == "pending")
            )
        ).all()
        assert restored_schedule == schedule
        assert len(plan_versions) == 1
        assert plan_versions[0].version == 1
        assert any(task.type == "review.due.check" for task in pending)
        assert any(task.type == "learning.plan.generated" for task in pending)

        restarted_application = ReviewPlanningApplication(
            ReviewScheduleRepository(session),
            LearningPlanRepository(session),
            OutboxProducer(session),
        )
        second_plan = await restarted_application.generate_plan(
            goal=goal,
            user_id=user_id,
            prerequisites={},
            mastery={knowledge_unit_id: 0.9},
            time_budget_minutes=30,
            learner_state_version=2,
            knowledge_graph_version="kg-1",
            at=schedule.next_due_at + timedelta(days=3),
            idempotency_key="plan-command-2",
            reason_codes=["PLAN_MASTERY_MATERIAL_CHANGE"],
        )
        await session.commit()
        versions = await LearningPlanRepository(session).list_versions(goal.goal_id)
        assert second_plan.version == 2
        assert [plan.status for plan in versions] == ["superseded", "active"]
    await restarted_engine.dispose()

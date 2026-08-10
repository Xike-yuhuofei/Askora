"""SQLite owner/transition/idempotency/progression integration evidence."""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.contracts.activity_lifecycle import (
    CompleteLearningActivityV1,
    StartLearningActivityV1,
)
from app.contracts.adaptive import VersionedRef
from app.contracts.learning import LearningActivity, LearningPlan
from app.contracts.planning import LearningGoalV1
from app.core.database import Base
from app.core.exceptions import BusinessError, ResourceNotFoundError
from app.infrastructure.activity_lifecycle import ActivityLifecycleRepository
from app.models.book_learning import BookLearningTranscriptTurnRecord
from app.models.ledger import LearningEventRecord, OutboxTaskRecord
from app.models.planning import LearningActivityRecord, LearningGoalRecord, LearningPlanRecord
from app.models.user import User
from app.services.activity_lifecycle import ActivityLifecycleService
from app.services.owner.canonical_identity import canonical_user_id

NOW = datetime(2026, 8, 9, 6, 0, tzinfo=timezone.utc)
POSTGRES_TEST_URL = os.environ.get("ASKORA_POSTGRES_TEST_URL")


async def _seed(session, *, owner_suffix: str = "", commit: bool = True):
    user = User(
        id=f"activity-owner{owner_suffix}",
        pseudonym_id=f"activity-owner-pseudo{owner_suffix}",
    )
    other = User(
        id=f"activity-other{owner_suffix}",
        pseudonym_id=f"activity-other-pseudo{owner_suffix}",
    )
    goal_id, plan_id, objective_id = uuid4(), uuid4(), uuid4()
    first_id, second_id = uuid4(), uuid4()
    owner_id = canonical_user_id(user.id)
    goal = LearningGoalV1(
        goal_id=goal_id,
        version=1,
        user_id=owner_id,
        title="理解函数",
        topic="函数",
        target_capabilities=("解释变化",),
        success_criteria=("独立分析",),
        source_document_ids=(),
        status="active",
        confirmed_by_user=True,
        created_at=NOW,
        confirmed_at=NOW,
        reason_codes=("GOAL_USER_CONFIRMED",),
    )
    plan = LearningPlan(
        plan_id=plan_id,
        version=1,
        learning_goal_id=goal_id,
        planning_horizon={},
        objective_ids=[objective_id],
        activity_ids=[first_id, second_id],
        constraints={},
        assumptions={},
        created_from_learner_state_version=0,
        knowledge_graph_version="graph:1",
        reason_codes=[],
        status="active",
    )
    activities = [
        LearningActivity(
            activity_id=first_id,
            plan_id=plan_id,
            plan_version=1,
            objective_id=objective_id,
            type="learn_new",
            knowledge_unit_ids=[uuid4()],
            estimated_duration_minutes=10,
            priority=2,
            reason_codes=[],
            status="planned",
        ),
        LearningActivity(
            activity_id=second_id,
            plan_id=plan_id,
            plan_version=1,
            objective_id=objective_id,
            type="practice",
            knowledge_unit_ids=[uuid4()],
            estimated_duration_minutes=10,
            priority=1,
            reason_codes=[],
            status="planned",
        ),
    ]
    session.add_all([user, other])
    session.add(
        LearningGoalRecord(
            id=f"{goal_id}:1",
            goal_id=str(goal_id),
            user_id=str(owner_id),
            version=1,
            status="active",
            idempotency_key="goal-1",
            payload=goal.model_dump(mode="json"),
        )
    )
    session.add(
        LearningPlanRecord(
            id=f"{plan_id}:1",
            plan_id=str(plan_id),
            learning_goal_id=str(goal_id),
            idempotency_key="plan-1",
            version=1,
            status="active",
            payload=plan.model_dump(mode="json"),
        )
    )
    for activity in activities:
        session.add(
            LearningActivityRecord(
                id=str(activity.activity_id),
                plan_id=str(plan_id),
                plan_version=1,
                priority=activity.priority,
                payload=activity.model_dump(mode="json"),
            )
        )
        await ActivityLifecycleRepository(session).initialize(
            activity_id=activity.activity_id,
            plan_id=plan_id,
            plan_version=1,
            status="planned",
            correlation_id=uuid4(),
            created_at=NOW,
        )
    if commit:
        await session.commit()
    else:
        await session.flush()
    return user, other, goal, plan, activities


def _postgres_async_url(value: str) -> str:
    if value.startswith("postgresql+asyncpg://"):
        return value
    if value.startswith("postgresql://"):
        return value.replace("postgresql://", "postgresql+asyncpg://", 1)
    raise ValueError("ASKORA_POSTGRES_TEST_URL must use PostgreSQL")


@pytest.mark.asyncio
async def test_start_complete_and_next_available_are_atomic_and_idempotent(tmp_path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'activity.db'}")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as session:
        user, other, goal, plan, activities = await _seed(session)
        service = ActivityLifecycleService(session)
        selected = await service.select_next(
            user=user,
            goal_id=goal.goal_id,
            idempotency_key="select-1",
            correlation_id=uuid4(),
            now=NOW,
        )
        assert selected.data.state.status == "available"
        assert selected.data.state.version == 2

        started = await service.start(
            user=user,
            command=StartLearningActivityV1(
                activity_id=activities[0].activity_id,
                expected_state_version=2,
                idempotency_key="start-1",
            ),
            correlation_id=uuid4(),
            now=NOW,
        )
        assert started.data.state.status == "active"
        assert started.data.execution.can_resume is True
        turn_ref = VersionedRef(
            entity_type="BookLearningTranscriptTurn",
            entity_id="learner-turn-1",
            version=1,
        )
        session.add(
            BookLearningTranscriptTurnRecord(
                turn_record_id=str(uuid4()),
                user_id=str(canonical_user_id(user.id)),
                goal_id=str(goal.goal_id),
                plan_id=str(plan.plan_id),
                plan_version=1,
                activity_id=str(activities[0].activity_id),
                session_id=str(uuid4()),
                turn_id="learner-turn-1",
                turn_number=1,
                turn_kind="learner",
                idempotency_key="turn-1",
                learner_text="我的理解",
                response_payload={},
                created_at=NOW,
            )
        )
        await session.flush()
        command = CompleteLearningActivityV1(
            activity_id=activities[0].activity_id,
            expected_state_version=3,
            completion_intent="learner_finished",
            transcript_turn_refs=(turn_ref,),
            idempotency_key="complete-1",
        )
        completed = await service.complete(
            user=user, command=command, correlation_id=uuid4(), now=NOW
        )
        replay = await service.complete(user=user, command=command, correlation_id=uuid4(), now=NOW)
        assert replay == completed
        assert completed.data.state.status == "completed"
        assert completed.next_activity_ref is not None
        next_state = await ActivityLifecycleRepository(session).latest(activities[1].activity_id)
        assert next_state is not None and next_state.status == "available"
        assert next_state.version == 2
        restored = await service.get(
            user=user,
            activity_id=activities[0].activity_id,
            correlation_id=uuid4(),
        )
        assert restored.next_activity_ref == completed.next_activity_ref
        assert await session.scalar(select(func.count(LearningEventRecord.event_id))) == 4
        assert await session.scalar(select(func.count(OutboxTaskRecord.id))) == 4

        with pytest.raises(ResourceNotFoundError):
            await service.get(
                user=other,
                activity_id=activities[0].activity_id,
                correlation_id=uuid4(),
            )
        with pytest.raises(BusinessError) as conflict:
            await service.start(
                user=user,
                command=StartLearningActivityV1(
                    activity_id=activities[0].activity_id,
                    expected_state_version=4,
                    idempotency_key="start-1",
                ),
                correlation_id=uuid4(),
            )
        assert conflict.value.error_code == "ACTIVITY_IDEMPOTENCY_CONFLICT"
    await engine.dispose()


@pytest.mark.asyncio
async def test_unsupported_activity_and_cross_activity_transcript_fail_closed(tmp_path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'activity-fail.db'}")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as session:
        user, _other, goal, _plan, activities = await _seed(session)
        # Change only immutable test definition before lifecycle commands.
        record = await session.get(LearningActivityRecord, str(activities[0].activity_id))
        assert record is not None
        payload = dict(record.payload)
        payload["type"] = "diagnostic"
        record.payload = payload
        service = ActivityLifecycleService(session)
        selected = await service.select_next(
            user=user,
            goal_id=goal.goal_id,
            idempotency_key="select-diagnostic",
            correlation_id=uuid4(),
        )
        started = await service.start(
            user=user,
            command=StartLearningActivityV1(
                activity_id=activities[0].activity_id,
                expected_state_version=selected.data.state.version,
                idempotency_key="start-diagnostic",
            ),
            correlation_id=uuid4(),
        )
        with pytest.raises(BusinessError) as required:
            await service.complete(
                user=user,
                command=CompleteLearningActivityV1(
                    activity_id=activities[0].activity_id,
                    expected_state_version=started.data.state.version,
                    completion_intent="learner_finished",
                    transcript_turn_refs=(
                        VersionedRef(
                            entity_type="BookLearningTranscriptTurn",
                            entity_id="missing",
                            version=1,
                        ),
                    ),
                    idempotency_key="complete-diagnostic",
                ),
                correlation_id=uuid4(),
            )
        assert required.value.error_code == "ACTIVITY_COMPLETION_EVIDENCE_REQUIRED"
    await engine.dispose()


@pytest.mark.asyncio
async def test_transcript_reference_must_match_current_owner_and_activity(tmp_path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'activity-owner-ref.db'}")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as session:
        user, other, goal, plan, activities = await _seed(session)
        service = ActivityLifecycleService(session)
        selected = await service.select_next(
            user=user,
            goal_id=goal.goal_id,
            idempotency_key="select-owner-ref",
            correlation_id=uuid4(),
        )
        started = await service.start(
            user=user,
            command=StartLearningActivityV1(
                activity_id=activities[0].activity_id,
                expected_state_version=selected.data.state.version,
                idempotency_key="start-owner-ref",
            ),
            correlation_id=uuid4(),
        )
        invalid_ref = VersionedRef(
            entity_type="BookLearningTranscriptTurn",
            entity_id="wrong-activity-turn",
            version=1,
        )
        session.add(
            BookLearningTranscriptTurnRecord(
                turn_record_id=str(uuid4()),
                user_id=str(canonical_user_id(user.id)),
                goal_id=str(goal.goal_id),
                plan_id=str(plan.plan_id),
                plan_version=1,
                activity_id=str(activities[1].activity_id),
                session_id=str(uuid4()),
                turn_id=invalid_ref.entity_id,
                turn_number=1,
                turn_kind="learner",
                idempotency_key="wrong-activity-turn",
                learner_text="不属于当前活动",
                response_payload={},
                created_at=NOW,
            )
        )
        await session.flush()
        with pytest.raises(BusinessError) as mismatch:
            await service.complete(
                user=user,
                command=CompleteLearningActivityV1(
                    activity_id=activities[0].activity_id,
                    expected_state_version=started.data.state.version,
                    completion_intent="learner_finished",
                    transcript_turn_refs=(invalid_ref,),
                    idempotency_key="complete-owner-ref",
                ),
                correlation_id=uuid4(),
            )
        assert mismatch.value.error_code == "ACTIVITY_COMPLETION_EVIDENCE_REQUIRED"

        session.add(
            BookLearningTranscriptTurnRecord(
                turn_record_id=str(uuid4()),
                user_id=str(canonical_user_id(other.id)),
                goal_id=str(goal.goal_id),
                plan_id=str(plan.plan_id),
                plan_version=1,
                activity_id=str(activities[0].activity_id),
                session_id=str(uuid4()),
                turn_id="wrong-owner-turn",
                turn_number=1,
                turn_kind="learner",
                idempotency_key="wrong-owner-turn",
                learner_text="不属于当前用户",
                response_payload={},
                created_at=NOW,
            )
        )
        await session.flush()
        with pytest.raises(BusinessError) as cross_owner:
            await service.complete(
                user=user,
                command=CompleteLearningActivityV1(
                    activity_id=activities[0].activity_id,
                    expected_state_version=started.data.state.version,
                    completion_intent="learner_finished",
                    transcript_turn_refs=(
                        VersionedRef(
                            entity_type="BookLearningTranscriptTurn",
                            entity_id="wrong-owner-turn",
                            version=1,
                        ),
                    ),
                    idempotency_key="complete-cross-owner",
                ),
                correlation_id=uuid4(),
            )
        assert cross_owner.value.error_code == "ACTIVITY_COMPLETION_EVIDENCE_REQUIRED"
    await engine.dispose()


@pytest.mark.asyncio
async def test_concurrent_duplicate_start_advances_once(tmp_path, monkeypatch) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'activity-race.db'}")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as seed_session:
        user, _other, goal, _plan, activities = await _seed(seed_session)
        selected = await ActivityLifecycleService(seed_session).select_next(
            user=user,
            goal_id=goal.goal_id,
            idempotency_key="select-race",
            correlation_id=uuid4(),
        )
        await seed_session.commit()

    command = StartLearningActivityV1(
        activity_id=activities[0].activity_id,
        expected_state_version=selected.data.state.version,
        idempotency_key="start-race",
    )

    async def invoke():
        async with factory() as session:
            current_user = await session.get(User, "activity-owner")
            assert current_user is not None
            result = await ActivityLifecycleService(session).start(
                user=current_user,
                command=command,
                correlation_id=uuid4(),
            )
            await session.commit()
            return result

    first, second = await asyncio.gather(invoke(), invoke())
    assert first == second

    async with factory() as replay_session:
        current_user = await replay_session.get(User, "activity-owner")
        assert current_user is not None
        replay_service = ActivityLifecycleService(replay_session)
        persisted_replay = replay_service._replay
        replay_attempts = 0

        async def replay_after_preflight_miss(**kwargs):
            nonlocal replay_attempts
            replay_attempts += 1
            if replay_attempts == 1:
                return None
            return await persisted_replay(**kwargs)

        monkeypatch.setattr(replay_service, "_replay", replay_after_preflight_miss)
        delayed_replay = await replay_service.start(
            user=current_user,
            command=command,
            correlation_id=uuid4(),
        )
        assert delayed_replay == first
        assert replay_attempts == 2

    async with factory() as verify_session:
        states = await ActivityLifecycleRepository(verify_session).latest_for_plan(
            plan_id=first.data.state.plan_id,
            plan_version=first.data.state.plan_version,
        )
        assert states[activities[0].activity_id].version == 3
        started_events = await verify_session.scalar(
            select(func.count(LearningEventRecord.event_id)).where(
                LearningEventRecord.event_type == "ActivityStarted"
            )
        )
        assert started_events == 1
    await engine.dispose()


@pytest.mark.skipif(
    not POSTGRES_TEST_URL,
    reason="ASKORA_POSTGRES_TEST_URL is required for PostgreSQL lifecycle evidence",
)
@pytest.mark.asyncio
async def test_postgres_lifecycle_state_event_and_outbox_are_transactional() -> None:
    assert POSTGRES_TEST_URL is not None
    engine = create_async_engine(_postgres_async_url(POSTGRES_TEST_URL))
    factory = async_sessionmaker(engine, expire_on_commit=False)
    suffix = f"-{uuid4().hex[:8]}"
    async with factory() as session:
        transaction = await session.begin()
        try:
            initial_outbox_count = await session.scalar(select(func.count(OutboxTaskRecord.id)))
            user, _other, goal, _plan, activities = await _seed(
                session,
                owner_suffix=suffix,
                commit=False,
            )
            service = ActivityLifecycleService(session)
            selected = await service.select_next(
                user=user,
                goal_id=goal.goal_id,
                idempotency_key=f"select-postgres{suffix}",
                correlation_id=uuid4(),
                now=NOW,
            )
            started = await service.start(
                user=user,
                command=StartLearningActivityV1(
                    activity_id=activities[0].activity_id,
                    expected_state_version=selected.data.state.version,
                    idempotency_key=f"start-postgres{suffix}",
                ),
                correlation_id=uuid4(),
                now=NOW,
            )
            assert started.data.state.status == "active"
            assert (
                await session.scalar(
                    select(func.count(LearningEventRecord.event_id)).where(
                        LearningEventRecord.aggregate_id == str(activities[0].activity_id)
                    )
                )
                == 2
            )
            assert await session.scalar(select(func.count(OutboxTaskRecord.id))) == (
                initial_outbox_count + 2
            )
        finally:
            await transaction.rollback()
    await engine.dispose()

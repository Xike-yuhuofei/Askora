"""SQLite integration coverage for UI-02B workspace product views."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.contracts.learning import LearningActivity, LearningPlan
from app.contracts.planning import LearningGoalV1
from app.core.database import Base
from app.core.exceptions import ResourceNotFoundError
from app.models.assessment import MasteryEstimateRecord
from app.models.document import ModerationStatus, ProcessingStatus, UserDocument
from app.models.planning import (
    LearningActivityRecord,
    LearningActivityStateRecord,
    LearningGoalRecord,
    LearningPlanRecord,
)
from app.models.user import User
from app.queries.workspace import WorkspaceTodayQueryService
from app.services.auth.canonical_identity import canonical_user_id

NOW = datetime(2026, 8, 9, 2, 0, tzinfo=timezone.utc)


def _engine_and_factory(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'workspace-product.db'}")

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine, async_sessionmaker(engine, expire_on_commit=False)


def _goal(*, goal_id: UUID, user_id: UUID, version: int, title: str) -> LearningGoalV1:
    return LearningGoalV1(
        goal_id=goal_id,
        version=version,
        user_id=user_id,
        title=title,
        topic="函数",
        target_capabilities=("解释函数变化",),
        success_criteria=("能够独立分析一个新函数",),
        source_document_ids=(),
        weekly_time_budget_minutes=90,
        status="active",
        confirmed_by_user=True,
        created_at=NOW - timedelta(days=2 - version),
        confirmed_at=NOW - timedelta(days=2),
        supersedes_version=version - 1 if version > 1 else None,
        reason_codes=("GOAL_USER_CONFIRMED",),
    )


def _plan_and_activities(goal_id: UUID):
    plan_id = uuid4()
    objective_id = uuid4()
    first_id = uuid4()
    second_id = uuid4()
    plan = LearningPlan(
        plan_id=plan_id,
        version=1,
        learning_goal_id=goal_id,
        planning_horizon={"kind": "daily"},
        objective_ids=[objective_id],
        activity_ids=[second_id, first_id],
        constraints={"hard_prerequisites": True},
        assumptions={"planner_version": "test/1.0"},
        created_from_learner_state_version=3,
        knowledge_graph_version="graph:1",
        reason_codes=["PLAN_INITIAL_GENERATION"],
        status="active",
    )
    first = LearningActivity(
        activity_id=first_id,
        plan_id=plan_id,
        plan_version=1,
        objective_id=objective_id,
        type="learn_new",
        knowledge_unit_ids=[uuid4()],
        estimated_duration_minutes=15,
        priority=10.0,
        reason_codes=["PLAN_MASTERY_GAP"],
        status="planned",
    )
    second = LearningActivity(
        activity_id=second_id,
        plan_id=plan_id,
        plan_version=1,
        objective_id=objective_id,
        type="diagnostic",
        knowledge_unit_ids=[uuid4()],
        estimated_duration_minutes=5,
        priority=1.0,
        reason_codes=["PLAN_TARGET_STATE_UNKNOWN"],
        status="available",
    )
    return plan, first, second


def _persist_goal(goal: LearningGoalV1) -> LearningGoalRecord:
    return LearningGoalRecord(
        id=f"{goal.goal_id}:{goal.version}",
        goal_id=str(goal.goal_id),
        user_id=str(goal.user_id),
        version=goal.version,
        status=goal.status,
        idempotency_key=f"goal:{goal.goal_id}:v{goal.version}",
        payload=goal.model_dump(mode="json"),
    )


def _persist_plan(plan: LearningPlan) -> LearningPlanRecord:
    return LearningPlanRecord(
        id=f"{plan.plan_id}:{plan.version}",
        plan_id=str(plan.plan_id),
        learning_goal_id=str(plan.learning_goal_id),
        idempotency_key=f"plan:{plan.plan_id}:v{plan.version}",
        version=plan.version,
        status=plan.status,
        payload=plan.model_dump(mode="json"),
    )


def _persist_activity(activity: LearningActivity) -> LearningActivityRecord:
    return LearningActivityRecord(
        id=str(activity.activity_id),
        plan_id=str(activity.plan_id),
        plan_version=activity.plan_version,
        priority=activity.priority,
        payload=activity.model_dump(mode="json"),
    )


def _persist_activity_state(activity: LearningActivity) -> LearningActivityStateRecord:
    return LearningActivityStateRecord(
        id=f"{activity.activity_id}:1",
        activity_id=str(activity.activity_id),
        version=1,
        plan_id=str(activity.plan_id),
        plan_version=activity.plan_version,
        status=activity.status,
        previous_status=None,
        transition_reason="TEST_CANONICAL_INITIAL_STATE",
        source_refs=[],
        actor_type="system",
        correlation_id=str(uuid4()),
        created_at=NOW,
    )


@pytest.mark.asyncio
async def test_ui02b_views_use_latest_owner_state_and_canonical_plan_order(tmp_path) -> None:
    """UI02B-AC-001..005: latest/owner/order/missing/label semantics are exact."""
    engine, factory = _engine_and_factory(tmp_path)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    user = User(id="local-user", pseudonym_id="workspace-product-user")
    other = User(id="other-user", pseudonym_id="workspace-product-other")
    owner_id = canonical_user_id(user.id)
    other_owner_id = canonical_user_id(other.id)
    goal_id = uuid4()
    goal_v1 = _goal(goal_id=goal_id, user_id=owner_id, version=1, title="旧目标标题")
    goal_v2 = _goal(goal_id=goal_id, user_id=owner_id, version=2, title="理解函数变化")
    private_goal = _goal(goal_id=uuid4(), user_id=other_owner_id, version=1, title="其他用户目标")
    plan, first, second = _plan_and_activities(goal_id)
    knowledge_unit_id = second.knowledge_unit_ids[0]

    async with factory() as session:
        session.add_all([user, other])
        await session.flush()
        session.add_all(
            [
                _persist_goal(goal_v1),
                _persist_goal(goal_v2),
                _persist_goal(private_goal),
                _persist_plan(plan),
                    _persist_activity(first),
                    _persist_activity(second),
                    _persist_activity_state(first),
                    _persist_activity_state(second),
            ]
        )
        session.add_all(
            [
                MasteryEstimateRecord(
                    id=str(uuid4()),
                    user_id=str(owner_id),
                    knowledge_unit_id=str(knowledge_unit_id),
                    version=1,
                    payload={"competence_probability": 0.25, "confidence": 0.4},
                ),
                MasteryEstimateRecord(
                    id=str(uuid4()),
                    user_id=str(owner_id),
                    knowledge_unit_id=str(knowledge_unit_id),
                    version=2,
                    payload={
                        "competence_probability": 0.62,
                        "confidence": 0.78,
                        "independent_success_count": 2,
                        "delayed_recall_evidence_count": 1,
                        "transfer_evidence_count": 0,
                        "evidence_count": 4,
                        "effective_evidence_weight": 2.5,
                        "active_misconception_ids": [],
                        "algorithm_id": "weighted-bkt",
                        "algorithm_version": "1.0",
                    },
                ),
                MasteryEstimateRecord(
                    id=str(uuid4()),
                    user_id=str(other_owner_id),
                    knowledge_unit_id=str(uuid4()),
                    version=1,
                    payload={"competence_probability": 0.99},
                ),
            ]
        )
        session.add(
            UserDocument(
                id=str(uuid4()),
                pseudonym_id=user.pseudonym_id,
                original_filename="functions.md",
                file_extension="md",
                file_size_bytes=100,
                storage_path="test-only",
                processing_status=ProcessingStatus.COMPLETED,
                moderation_status=ModerationStatus.APPROVED,
                moderation_details={
                    "content_knowledge_v1": {
                        "current_revision_id": "revision-1",
                        "revisions": [
                            {
                                "revision_id": "revision-1",
                                "knowledge_units": [
                                    {
                                        "knowledge_unit_id": str(knowledge_unit_id),
                                        "canonical_name": "函数变化",
                                        "revision": 3,
                                    }
                                ],
                            }
                        ],
                    }
                },
            )
        )
        await session.commit()

        query = WorkspaceTodayQueryService(session, clock=lambda: NOW)
        goals = await query.list_goals(user, correlation_id="goals")
        path = await query.get_path(user, goal_id=None, correlation_id="path")
        evidence = await query.get_evidence(user, correlation_id="evidence")
        today = await query.get_today(user, timezone_name="Asia/Shanghai", correlation_id="today")

        assert [item.title for item in goals.data.goals] == ["理解函数变化"]
        assert path.data.view_state == "PARTIAL"
        assert path.data.learning_path is not None
        assert [item.type for item in path.data.learning_path.activities] == [
            "diagnostic",
            "learn_new",
        ]
        assert path.data.learning_path.objectives[0].capability is None
        assert path.data.learning_path.objectives[0].reason_codes == (
            "OBJECTIVE_METADATA_UNAVAILABLE",
        )
        assert evidence.data.knowledge_units_assessed == 1
        assert evidence.data.entries[0].label == "函数变化"
        assert evidence.data.entries[0].knowledge_unit_ref.endswith(":v3")
        assert evidence.data.entries[0].competence_probability == 0.62
        assert evidence.data.entries[0].product_label is None
        assert today.data.active_goal is not None
        assert today.data.active_goal.title == "理解函数变化"
        assert today.data.current_activity is not None
        assert today.data.current_activity.type == "diagnostic"
        assert today.data.current_activity.launch_state == "REQUIRES_START_COMMAND"

        with pytest.raises(ResourceNotFoundError):
            await query.get_path(user, goal_id=private_goal.goal_id, correlation_id="private")

    await engine.dispose()


@pytest.mark.asyncio
async def test_ui02b_multiple_current_plans_require_explicit_goal_scope(tmp_path) -> None:
    """ADR-0006/UI02B-AC-004: the query never invents a unique current plan."""
    engine, factory = _engine_and_factory(tmp_path)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    user = User(id=str(uuid4()), pseudonym_id="multi-plan-user")
    owner_id = UUID(user.id)
    goals = [
        _goal(goal_id=uuid4(), user_id=owner_id, version=1, title="目标一"),
        _goal(goal_id=uuid4(), user_id=owner_id, version=1, title="目标二"),
    ]
    plan_groups = [_plan_and_activities(goal.goal_id) for goal in goals]
    async with factory() as session:
        session.add(user)
        session.add_all([_persist_goal(goal) for goal in goals])
        for plan, first, second in plan_groups:
                session.add_all(
                    [
                        _persist_plan(plan),
                        _persist_activity(first),
                        _persist_activity(second),
                        _persist_activity_state(first),
                        _persist_activity_state(second),
                    ]
                )
        await session.commit()

        query = WorkspaceTodayQueryService(session, clock=lambda: NOW)
        unscoped = await query.get_path(user, goal_id=None, correlation_id="unscoped")
        scoped = await query.get_path(user, goal_id=goals[0].goal_id, correlation_id="scoped")

        assert unscoped.data.view_state == "PARTIAL"
        assert unscoped.data.learning_path is None
        assert len(unscoped.data.available_goal_refs) == 2
        assert unscoped.data.reason_codes == ("MULTIPLE_CURRENT_PLANS_REQUIRE_GOAL_SCOPE",)
        assert scoped.data.learning_path is not None
        assert scoped.data.learning_path.goal_ref.endswith(f"{goals[0].goal_id}:v1")

    await engine.dispose()


@pytest.mark.asyncio
async def test_ui02b_http_queries_are_private_versioned_and_current_user_scoped(tmp_path) -> None:
    """EXEC029-AC-002: all additive endpoints are private strict v1 queries."""
    from httpx import ASGITransport, AsyncClient

    from app.core.database import get_db
    from app.main import app as fastapi_app
    from app.services.auth.dependencies import get_current_user

    engine, factory = _engine_and_factory(tmp_path)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    user_id = str(uuid4())
    async with factory() as session:
        session.add(User(id=user_id, pseudonym_id="workspace-http-product"))
        await session.commit()

    async def override_get_db():
        async with factory() as session:
            yield session

    async def override_get_current_user():
        async with factory() as session:
            user = await session.get(User, user_id)
            assert user is not None
            return user

    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[get_current_user] = override_get_current_user
    try:
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            responses = [
                await client.get("/api/v1/workspace/goals"),
                await client.get("/api/v1/workspace/path"),
                await client.get("/api/v1/workspace/evidence"),
            ]
            missing_scope = await client.get(
                "/api/v1/workspace/path", params={"goal_id": str(uuid4())}
            )
        for response in responses:
            assert response.status_code == 200, response.text
            assert response.headers["cache-control"] == "private, no-store"
            assert response.json()["schema_version"] == "1.0"
        assert missing_scope.status_code == 404
    finally:
        fastapi_app.dependency_overrides.clear()
    await engine.dispose()

"""EXEC-069 canonical Learning Context Drawer query coverage."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.contracts.adaptive import (
    ActionModifier,
    AnswerExposure,
    HintSpecificity,
    InteractionMove,
    PolicyBundleV03,
    ScaffoldControl,
    StrategyFamily,
    TeachingActionV03,
    TeachingContextV03,
    TeachingStage,
    ValidationObligation,
    VersionedRef,
)
from app.contracts.learning import LearningActivity, LearningPlan
from app.contracts.planning import LearningGoalV1
from app.core.database import Base
from app.core.exceptions import ResourceNotFoundError
from app.infrastructure.adaptive_records import AdaptiveContractRepository
from app.models.planning import (
    LearningActivityRecord,
    LearningActivityStateRecord,
    LearningGoalRecord,
    LearningPlanRecord,
)
from app.models.user import User
from app.queries.workspace import WorkspaceTodayQueryService
from app.services.owner.canonical_identity import canonical_user_id
from tests.fixtures.v03_policy_factory import make_bundle, make_context

NOW = datetime(2026, 8, 11, 8, 30, tzinfo=timezone.utc)


def _engine_and_factory(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'ui04-context.db'}")

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine, async_sessionmaker(engine, expire_on_commit=False)


def _goal(owner_id: UUID, workspace_id: str) -> tuple[LearningGoalV1, LearningGoalRecord]:
    goal = LearningGoalV1(
        goal_id=uuid4(),
        version=1,
        user_id=owner_id,
        title="理解线性变换",
        topic="线性代数",
        target_capabilities=("解释线性变换",),
        success_criteria=("能够独立解释一个新例子",),
        source_document_ids=(),
        status="active",
        confirmed_by_user=True,
        created_at=NOW,
        confirmed_at=NOW,
        reason_codes=("GOAL_USER_CONFIRMED",),
    )
    return goal, LearningGoalRecord(
        id=f"{goal.goal_id}:1",
        goal_id=str(goal.goal_id),
        user_id=str(owner_id),
        workspace_id=workspace_id,
        version=1,
        status="active",
        idempotency_key=f"ui04-goal:{goal.goal_id}",
        payload=goal.model_dump(mode="json"),
    )


def _plan(goal_id: UUID) -> tuple[LearningPlan, tuple[LearningActivity, LearningActivity]]:
    plan_id = uuid4()
    objective_id = uuid4()
    first = LearningActivity(
        activity_id=uuid4(),
        plan_id=plan_id,
        plan_version=1,
        objective_id=objective_id,
        type="practice",
        knowledge_unit_ids=(uuid4(),),
        estimated_duration_minutes=12,
        priority=10,
        reason_codes=("PLAN_MASTERY_GAP",),
        status="active",
    )
    second = LearningActivity(
        activity_id=uuid4(),
        plan_id=plan_id,
        plan_version=1,
        objective_id=objective_id,
        type="transfer_check",
        knowledge_unit_ids=(uuid4(),),
        estimated_duration_minutes=8,
        priority=8,
        reason_codes=("PLAN_TRANSFER_EVIDENCE_NEEDED",),
        status="planned",
    )
    plan = LearningPlan(
        plan_id=plan_id,
        version=1,
        learning_goal_id=goal_id,
        planning_horizon={"kind": "daily"},
        objective_ids=(objective_id,),
        activity_ids=(first.activity_id, second.activity_id),
        constraints={},
        assumptions={"planner_version": "ui04-test/1.0"},
        created_from_learner_state_version=1,
        knowledge_graph_version="graph:1",
        reason_codes=("PLAN_INITIAL_GENERATION",),
        status="active",
    )
    return plan, (first, second)


def _plan_records(plan: LearningPlan, activities: tuple[LearningActivity, ...]) -> list[object]:
    records: list[object] = [
        LearningPlanRecord(
            id=f"{plan.plan_id}:1",
            plan_id=str(plan.plan_id),
            learning_goal_id=str(plan.learning_goal_id),
            idempotency_key=f"ui04-plan:{plan.plan_id}",
            version=1,
            status="active",
            payload=plan.model_dump(mode="json"),
        )
    ]
    for activity in activities:
        records.extend(
            [
                LearningActivityRecord(
                    id=str(activity.activity_id),
                    plan_id=str(plan.plan_id),
                    plan_version=1,
                    priority=activity.priority,
                    payload=activity.model_dump(mode="json"),
                ),
                LearningActivityStateRecord(
                    id=f"{activity.activity_id}:1",
                    activity_id=str(activity.activity_id),
                    version=1,
                    plan_id=str(plan.plan_id),
                    plan_version=1,
                    status=activity.status,
                    previous_status=None,
                    transition_reason="TEST_INITIAL_STATE",
                    source_refs=[],
                    actor_type="system",
                    correlation_id=str(uuid4()),
                    created_at=NOW,
                ),
            ]
        )
    return records


def _action_for(
    activity: LearningActivity,
) -> tuple[TeachingActionV03, TeachingContextV03, PolicyBundleV03]:
    base_context = make_context({"case_id": "ui04-learning-context"})
    activity_ref = VersionedRef(
        entity_type="LearningActivity",
        entity_id=str(activity.activity_id),
        version=activity.plan_version,
    )
    objective_ref = VersionedRef(
        entity_type="LearningObjective",
        entity_id=str(activity.objective_id),
        version=activity.plan_version,
    )
    context = base_context.model_copy(
        update={
            "learning_activity_ref": activity_ref,
            "learning_objective_ref": objective_ref,
            "source_refs": (activity_ref, objective_ref, *base_context.source_refs),
        }
    )
    bundle = make_bundle()
    return (
        TeachingActionV03(
            action_id=uuid4(),
            learning_objective_ref=objective_ref,
            learning_activity_ref=activity_ref,
            strategy_family=StrategyFamily.GUIDED_PRACTICE,
            strategy_version="guided-1",
            teaching_stage=TeachingStage.GUIDED_PRACTICE,
            interaction_moves=(InteractionMove.SOCRATIC_PROBE,),
            action_modifiers=ActionModifier(self_explanation=True),
            scaffold_control=ScaffoldControl.MEDIUM,
            hint_specificity=HintSpecificity.CONCEPTUAL_STRATEGIC,
            answer_exposure=AnswerExposure.NONE,
            evidence_requirements=("routine_application",),
            expected_evidence_type="routine_application",
            success_condition={"score_gte": 0.8},
            failure_condition={"attempts_gte": 3},
            max_attempts=3,
            validation_obligation=ValidationObligation.NONE,
            reason_codes=("TEACH_GUIDED_PRACTICE",),
            policy_bundle_ref=VersionedRef(
                entity_type="PolicyBundle",
                entity_id=bundle.bundle_id,
                version=bundle.policy_version,
            ),
            teaching_context_ref=VersionedRef(
                entity_type="TeachingContext",
                entity_id=str(context.context_id),
                version=context.context_schema_version,
            ),
            decision_id=uuid4(),
            created_at=NOW,
        ),
        context,
        bundle,
    )


@pytest.mark.asyncio
async def test_exec069_learning_context_ready_partial_stale_and_provenance(tmp_path) -> None:
    """EXEC069-AC-003/004, UXA-DATA-220..223: exact owner refs and honest states."""
    engine, factory = _engine_and_factory(tmp_path)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    user = User(id=str(uuid4()), pseudonym_id="ui04-context-user")
    owner_id = canonical_user_id(user.id)
    workspace_id = str(uuid4())
    goal, goal_record = _goal(owner_id, workspace_id)
    plan, activities = _plan(goal.goal_id)

    async with factory() as session:
        session.add(user)
        session.add(goal_record)
        session.add_all(_plan_records(plan, activities))
        await session.commit()

        query = WorkspaceTodayQueryService(session, workspace_id=workspace_id, clock=lambda: NOW)
        partial = await query.get_learning_context(
            user,
            activity_id=activities[0].activity_id,
            correlation_id="partial",
        )
        assert partial.data.view_state == "PARTIAL"
        assert partial.data.stage_name is None
        assert len(partial.data.next_directions) == 2
        assert all(item.source_system.value == "SYS06" for item in partial.data.next_directions)

        action, context, bundle = _action_for(activities[0])
        repository = AdaptiveContractRepository(session)
        await repository.publish_policy_bundle(bundle)
        await repository.save_context(context)
        await repository.save_action(action)
        await session.commit()

        ready = await query.get_learning_context(
            user,
            activity_id=activities[0].activity_id,
            correlation_id="ready",
        )
        assert ready.data.view_state == "READY"
        assert ready.data.stage_name == "引导练习"
        assert ready.data.stage_goal == "在引导下完成当前任务"
        assert ready.data.stage_source is not None
        assert ready.data.stage_source.source_system.value == "SYS05"
        assert str(action.action_id) in ready.data.stage_source.source_ref
        assert ready.data.stage_goal_source is not None
        assert ready.data.stage_goal_source.presentation_version == "ui-stage-copy/1.0"
        assert [item.label for item in ready.data.next_directions] == [
            "练习与巩固",
            "迁移应用",
        ]

        session.add(
            LearningActivityStateRecord(
                id=f"{activities[0].activity_id}:2",
                activity_id=str(activities[0].activity_id),
                version=2,
                plan_id=str(plan.plan_id),
                plan_version=1,
                status="completed",
                previous_status="active",
                transition_reason="TEST_COMPLETED",
                source_refs=[],
                actor_type="learner",
                correlation_id=str(uuid4()),
                created_at=NOW,
            )
        )
        await session.commit()
        stale = await query.get_learning_context(
            user,
            activity_id=activities[0].activity_id,
            correlation_id="stale",
        )
        assert stale.data.view_state == "STALE"

        with pytest.raises(ResourceNotFoundError):
            await WorkspaceTodayQueryService(
                session, workspace_id=str(uuid4()), clock=lambda: NOW
            ).get_learning_context(
                user,
                activity_id=activities[0].activity_id,
                correlation_id="foreign-workspace",
            )

    await engine.dispose()


@pytest.mark.asyncio
async def test_exec069_learning_context_missing_without_current_activity(tmp_path) -> None:
    """UXA-SCREEN-123: no plan/activity remains explicit MISSING."""
    engine, factory = _engine_and_factory(tmp_path)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    user = User(id=str(uuid4()), pseudonym_id="ui04-context-empty")
    async with factory() as session:
        session.add(user)
        await session.commit()
        result = await WorkspaceTodayQueryService(
            session, workspace_id=str(uuid4()), clock=lambda: NOW
        ).get_learning_context(user, activity_id=None, correlation_id="missing")
        assert result.data.view_state == "MISSING"
        assert result.data.next_directions == ()
        assert result.data.stage_ref is None
    await engine.dispose()

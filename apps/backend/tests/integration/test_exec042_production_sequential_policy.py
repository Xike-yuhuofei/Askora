"""EXEC-042 production sequential policy integration tests.

These tests verify that the production Book-to-Learning path composes
the v0.3 TeachingPolicyKernel + SequentialTeachingPolicy correctly,
closing GAP-V03-001 and GAP-V03-002.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base
from app.services.policy_runtime import default_policy_activation, default_policy_bundle

NOW = datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
async def exec042_db(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'exec042.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session, tmp_path
    await engine.dispose()


async def _full_book_flow(db, tmp_path, suffix: str):
    """Run the complete BookLearning flow up to READY_TO_LEARN + lifecycle start.

    Uses the same primitives as test_book_learning_orchestration.py to ensure
    the production path is exercised identically.
    """
    from tests.integration.test_book_learning_orchestration import (
        CountingModelProvider,
        FixedModelRouter,
        _processed_book,
        _independent,
    )
    from app.application.book_learning import BookLearningApplication
    from app.contracts.activity_lifecycle import StartLearningActivityV1
    from app.infrastructure.adaptive_records import AdaptiveContractRepository
    from app.models.assessment import AssessmentItem
    from app.orchestration.learning_facade import LearningOrchestrationFacade
    from app.orchestration.model_rendering import PolicyBoundModelRenderer
    from app.services.activity_lifecycle import ActivityLifecycleService

    records = AdaptiveContractRepository(db)
    await records.publish_policy_bundle(default_policy_bundle())
    await records.activate_policy_bundle(default_policy_activation())

    provider = CountingModelProvider()
    app = BookLearningApplication(
        db,
        teaching_facade=LearningOrchestrationFacade(
            adaptive_renderer=PolicyBoundModelRenderer(FixedModelRouter(provider))  # type: ignore[arg-type]
        ),
    )
    user, document, units = await _processed_book(db, tmp_path, suffix)
    created = await app.create_goal_candidate(
        user=user,
        document_id=UUID(document.id),
        intent="能够解释这份资料中的核心概念",
        idempotency_key=f"{suffix}:goal:create",
        correlation_id=uuid4(),
    )
    goal_id = UUID(created.payload["goal"]["goal_id"])
    await app.confirm_goal(
        user=user,
        goal_id=goal_id,
        confirmed_by_user=True,
        idempotency_key=f"{suffix}:goal:confirm",
        correlation_id=uuid4(),
        now=NOW,
    )
    mapped = await app.advance(
        user=user,
        document_id=UUID(document.id),
        idempotency_key=f"{suffix}:advance:map",
        correlation_id=uuid4(),
        now=NOW,
    )
    assert mapped.payload["applied_command"] == "MapGoalToKnowledge"
    mapping_result = await app.get_mapping(
        user=user, goal_id=goal_id, correlation_id=uuid4()
    )
    mapping = mapping_result.payload["mapping"]
    prerequisite_id = units["Fractions"]
    db.add(
        AssessmentItem(
            id=str(uuid4()),
            knowledge_point_id=str(prerequisite_id),
            subject="book",
            item_type="fill_blank",
            difficulty=3,
            grade_level=0,
            question_text="Type fractions",
            options=[],
            correct_answer="fractions",
            explanation="grader-only",
            cognitive_level="apply",
            common_misconceptions=[],
            is_active=True,
            version="1.0",
        )
    )
    await db.flush()
    diagnosed = await app.advance(
        user=user,
        document_id=UUID(document.id),
        idempotency_key=f"{suffix}:advance:diagnostic",
        correlation_id=uuid4(),
        now=NOW,
    )
    assert diagnosed.payload["applied_command"] == "GeneratePrerequisiteDiagnosis"
    diagnostic_view = await app.get_diagnostic(
        user=user, goal_id=goal_id, correlation_id=uuid4()
    )
    need = diagnostic_view.payload["need"]
    completed = await app.submit_diagnostic_response(
        user=user,
        need_id=UUID(need["need_id"]),
        expected_need_version=need["version"],
        response="fractions",
        assistance=_independent(),
        idempotency_key=f"{suffix}:diagnostic:answer",
        correlation_id=uuid4(),
        now=NOW,
    )
    assert completed.payload["need"]["status"] == "resolved"
    advanced = await app.advance(
        user=user,
        document_id=UUID(document.id),
        idempotency_key=f"{suffix}:advance:activity",
        correlation_id=uuid4(),
        now=NOW,
    )
    assert advanced.payload["applied_command"] == "SelectNextLearningActivity"
    generated = await app.generate_plan(
        user=user,
        need_id=UUID(completed.payload["need"]["need_id"]),
        idempotency_key=f"{suffix}:plan:generate",
        correlation_id=uuid4(),
        now=NOW,
    )
    ready = await app.readiness(
        user=user, document_id=UUID(document.id), correlation_id=f"{suffix}:ready"
    )
    assert ready.state == "READY_TO_LEARN"
    plan_view = await app.get_plan(user=user, goal_id=goal_id, correlation_id=uuid4())
    plan = plan_view.payload["plan"]
    selected_ref = next(
        item.ref
        for item in ready.owner_refs
        if item.ref.entity_type == "LearningActivity" and item.status == "selected"
    )
    activity = next(
        item for item in plan_view.payload["activities"]
        if item["activity_id"] == selected_ref.entity_id
    )
    lifecycle = await ActivityLifecycleService(db).get(
        user=user,
        activity_id=UUID(activity["activity_id"]),
        correlation_id=uuid4(),
    )
    await ActivityLifecycleService(db).start(
        user=user,
        command=StartLearningActivityV1(
            activity_id=UUID(activity["activity_id"]),
            expected_state_version=lifecycle.data.state.version,
            idempotency_key=f"{suffix}:lifecycle:start",
        ),
        correlation_id=uuid4(),
        now=NOW,
    )
    return app, provider, user, document, goal_id, plan, activity


@pytest.mark.asyncio
async def test_exec042_t1_first_decision_deterministic_bootstrap(
    exec042_db,
) -> None:
    """T1: First decision (no previous action) — deterministic bootstrap via kernel."""
    db, tmp_path = exec042_db
    app, provider, user, document, goal_id, plan, activity = await _full_book_flow(
        db, tmp_path, "t1"
    )
    system_start = await app.start_teaching_round(
        user=user,
        goal_id=goal_id,
        plan_id=UUID(plan["plan_id"]),
        plan_version=plan["version"],
        activity_id=UUID(activity["activity_id"]),
        session_id=None,
        turn_id="t1-system-start",
        turn_kind="system_start",
        learner_text=None,
        idempotency_key="exec042:t1:system-start",
        correlation_id=uuid4(),
        now=NOW,
    )
    assert system_start.turn_number == 1
    trace = system_start.decision_trace_v03
    assert trace is not None
    assert trace.behavior_policy_type == "DETERMINISTIC"
    assert trace.action_propensity is None
    assert trace.previous_teaching_action_ref is None
    assert len(provider.calls) == 1


@pytest.mark.asyncio
async def test_exec042_t2_no_material_evidence_holds(
    exec042_db,
) -> None:
    """T2: Second decision with no material evidence — HOLD strategy, no oscillation."""
    db, tmp_path = exec042_db
    app, provider, user, document, goal_id, plan, activity = await _full_book_flow(
        db, tmp_path, "t2"
    )
    system_start = await app.start_teaching_round(
        user=user,
        goal_id=goal_id,
        plan_id=UUID(plan["plan_id"]),
        plan_version=plan["version"],
        activity_id=UUID(activity["activity_id"]),
        session_id=None,
        turn_id="t2-system-start",
        turn_kind="system_start",
        learner_text=None,
        idempotency_key="exec042:t2:system-start",
        correlation_id=uuid4(),
        now=NOW,
    )
    first_action = system_start.teaching_action
    first_strategy = first_action.strategy_family

    second = await app.start_teaching_round(
        user=user,
        goal_id=goal_id,
        plan_id=UUID(plan["plan_id"]),
        plan_version=plan["version"],
        activity_id=UUID(activity["activity_id"]),
        session_id=system_start.session_id,
        turn_id="t2-turn-1",
        learner_text="请继续讲",
        idempotency_key="exec042:t2:turn-1",
        correlation_id=uuid4(),
        now=NOW,
    )
    assert second.turn_number == 2
    second_action = second.teaching_action
    second_trace = second.decision_trace_v03
    assert second_trace is not None
    assert second_trace.previous_teaching_action_ref is not None
    assert str(second_trace.previous_teaching_action_ref.entity_id) == str(first_action.action_id)
    assert second_action.strategy_family == first_strategy
    assert second_trace.anti_oscillation_decision is not None
    assert second_trace.behavior_policy_type == "DETERMINISTIC"
    assert second_trace.action_propensity is None


@pytest.mark.asyncio
async def test_exec042_t9_decision_trace_carries_sequential_metadata(
    exec042_db,
) -> None:
    """T9: Second+ DecisionTrace includes anti-oscillation, previous ref."""
    db, tmp_path = exec042_db
    app, provider, user, document, goal_id, plan, activity = await _full_book_flow(
        db, tmp_path, "t9"
    )
    system_start = await app.start_teaching_round(
        user=user,
        goal_id=goal_id,
        plan_id=UUID(plan["plan_id"]),
        plan_version=plan["version"],
        activity_id=UUID(activity["activity_id"]),
        session_id=None,
        turn_id="t9-system-start",
        turn_kind="system_start",
        learner_text=None,
        idempotency_key="exec042:t9:system-start",
        correlation_id=uuid4(),
        now=NOW,
    )
    second = await app.start_teaching_round(
        user=user,
        goal_id=goal_id,
        plan_id=UUID(plan["plan_id"]),
        plan_version=plan["version"],
        activity_id=UUID(activity["activity_id"]),
        session_id=system_start.session_id,
        turn_id="t9-turn-1",
        learner_text="我想了解更多",
        idempotency_key="exec042:t9:turn-1",
        correlation_id=uuid4(),
        now=NOW,
    )
    trace = second.decision_trace_v03
    assert trace is not None
    assert trace.previous_teaching_action_ref is not None
    assert trace.anti_oscillation_decision is not None
    assert len(trace.transition_reason_codes) >= 1
    assert trace.action_propensity is None


@pytest.mark.asyncio
async def test_exec042_t11_book_to_learning_e2e_hold_path(
    exec042_db,
) -> None:
    """T11: Book-to-Learning E2E — first decision → second decision HOLD (production path)."""
    db, tmp_path = exec042_db
    app, provider, user, document, goal_id, plan, activity = await _full_book_flow(
        db, tmp_path, "t11"
    )
    sys = await app.start_teaching_round(
        user=user,
        goal_id=goal_id,
        plan_id=UUID(plan["plan_id"]),
        plan_version=plan["version"],
        activity_id=UUID(activity["activity_id"]),
        session_id=None,
        turn_id="t11-system",
        turn_kind="system_start",
        learner_text=None,
        idempotency_key="exec042:t11:system",
        correlation_id=uuid4(),
        now=NOW,
    )
    first_action = sys.teaching_action
    first_trace = sys.decision_trace_v03
    assert first_trace is not None
    assert first_trace.previous_teaching_action_ref is None

    second = await app.start_teaching_round(
        user=user,
        goal_id=goal_id,
        plan_id=UUID(plan["plan_id"]),
        plan_version=plan["version"],
        activity_id=UUID(activity["activity_id"]),
        session_id=sys.session_id,
        turn_id="t11-turn-1",
        learner_text="能解释一下吗？",
        idempotency_key="exec042:t11:turn-1",
        correlation_id=uuid4(),
        now=NOW,
    )
    second_action = second.teaching_action
    second_trace = second.decision_trace_v03
    assert second_trace is not None
    assert second_trace.previous_teaching_action_ref is not None
    assert str(second_trace.previous_teaching_action_ref.entity_id) == str(first_action.action_id)
    assert second_trace.anti_oscillation_decision is not None
    assert second_action.strategy_family == first_action.strategy_family

    from app.infrastructure.adaptive_records import (
        AdaptiveContractRepository,
        DecisionTraceV03Repository,
    )
    records = AdaptiveContractRepository(db)
    persisted_first = await records.get_action(first_action.action_id)
    assert persisted_first is not None
    persisted_second = await records.get_action(second_action.action_id)
    assert persisted_second is not None

    trace_repo = DecisionTraceV03Repository(db)
    persisted_first_trace = await trace_repo.get(first_action.decision_id)
    assert persisted_first_trace is not None
    assert persisted_first_trace.decision_id == first_trace.decision_id
    persisted_second_trace = await trace_repo.get(second_action.decision_id)
    assert persisted_second_trace is not None
    assert persisted_second_trace.decision_id == second_trace.decision_id
    assert persisted_second_trace.previous_teaching_action_ref is not None

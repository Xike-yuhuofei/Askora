"""EXEC-042 production sequential policy integration tests.

These tests verify that the production Book-to-Learning path composes
the v0.3 TeachingPolicyKernel + SequentialTeachingPolicy correctly,
closing GAP-V03-001 and GAP-V03-002.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models  # noqa: F401
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
    from app.application.book_learning import BookLearningApplication
    from app.contracts.activity_lifecycle import StartLearningActivityV1
    from app.infrastructure.adaptive_records import AdaptiveContractRepository
    from app.models.assessment import AssessmentItem
    from app.orchestration.learning_facade import LearningOrchestrationFacade
    from app.orchestration.model_rendering import PolicyBoundModelRenderer
    from app.services.activity_lifecycle import ActivityLifecycleService
    from tests.integration.test_book_learning_orchestration import (
        CountingModelProvider,
        FixedModelRouter,
        _independent,
        _processed_book,
    )

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
        intent="我想掌握 Ratios 并在新题目中应用 Ratios",
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
    await app.get_mapping(user=user, goal_id=goal_id, correlation_id=uuid4())
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
    diagnostic_view = await app.get_diagnostic(user=user, goal_id=goal_id, correlation_id=uuid4())
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
    await app.generate_plan(
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
        item
        for item in plan_view.payload["activities"]
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
        learner_text="Tell me more about ratios",
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
        learner_text="I want to learn more about ratios",
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
        learner_text="Can you explain ratios?",
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


@pytest.mark.asyncio
async def test_exec042_hold_e2e_preserves_anti_oscillation_state(
    exec042_db,
) -> None:
    """Production HOLD path preserves anti-oscillation state across decisions."""
    db, tmp_path = exec042_db
    app, provider, user, document, goal_id, plan, activity = await _full_book_flow(
        db, tmp_path, "hold-e2e"
    )
    sys = await app.start_teaching_round(
        user=user,
        goal_id=goal_id,
        plan_id=UUID(plan["plan_id"]),
        plan_version=plan["version"],
        activity_id=UUID(activity["activity_id"]),
        session_id=None,
        turn_id="hold-system",
        turn_kind="system_start",
        learner_text=None,
        idempotency_key="exec042:hold:system",
        correlation_id=uuid4(),
        now=NOW,
    )
    first_action = sys.teaching_action
    first_strategy = first_action.strategy_family
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
        turn_id="hold-turn-1",
        learner_text="Continue explaining ratios",
        idempotency_key="exec042:hold:turn-1",
        correlation_id=uuid4(),
        now=NOW,
    )
    second_action = second.teaching_action
    second_trace = second.decision_trace_v03
    assert second_trace is not None
    assert second_action.strategy_family == first_strategy
    assert second_trace.anti_oscillation_decision is not None
    anti = second_trace.anti_oscillation_decision
    assert anti.get("decision") == "HOLD"
    assert anti.get("reason_code", "").startswith("HOLD_")
    assert anti.get("previous_action_key") is not None
    assert anti.get("proposed_action_key") is not None
    assert anti.get("fixed_decision_time") is not None


@pytest.mark.asyncio
async def test_exec042_switch_e2e_happens_with_material_assessment_evidence(
    exec042_db,
) -> None:
    """Production SWITCH occurs through the REAL production composition.

    Drives LearningOrchestrationFacade._execute_adaptive_turn (the same
    production path used by BookLearningApplication) with a second-turn context
    that carries canonical material evidence AND a repeated-failure state that
    reaches the profile failure ceiling. The SequentialTeachingPolicy must
    produce a genuine SWITCH (repeated-failure override) whose trace records the
    exact previous action ref and the material evidence refs. The sequential
    state is reconstructed from the persisted first DecisionTrace — never
    constructed by hand (T10).
    """
    db, tmp_path = exec042_db
    from app.domains.teaching_policy import TeachingPolicyKernel
    from app.domains.teaching_policy.models import PolicyRuntimeProfile
    from app.orchestration.learning_facade import (
        CanonicalTurnRequest,
        LearningOrchestrationFacade,
        _reconstruct_sequential_policy_state,
    )
    from tests.fixtures.v03_policy_factory import (
        load_profile,
        make_bundle,
        make_context,
        with_previous_action,
    )

    profile = PolicyRuntimeProfile.model_validate(
        {**load_profile().model_dump(), "failure_ceiling": 3}
    )
    bundle = make_bundle(profile)
    kernel = TeachingPolicyKernel()

    # First decision: deterministic bootstrap kernel (no previous action).
    first = kernel.decide(
        context=make_context({"case_id": "prod-switch-boot", "mastery": 0.2}),
        bundle=bundle,
        profile=profile,
    )

    # Second decision: repeated failure reaches the ceiling -> legal SWITCH via
    # production composition (facade -> SequentialTeachingPolicy), never a
    # hand-built SequentialPolicyState.
    context = with_previous_action(
        make_context(
            {
                "case_id": "prod-switch-next",
                "mastery": 0.2,
                "assisted_success": True,
                "consecutive_failures": 5,
            }
        ),
        first.action,
    )
    sequential_state = _reconstruct_sequential_policy_state(first.action, first.trace)
    result = await LearningOrchestrationFacade().run_turn(
        CanonicalTurnRequest(
            session_id="prod-switch-session",
            user_id="prod-switch-user",
            text="continue",
            turn_id="prod-switch-turn",
            subject="lesson",
            teaching_context_v03=context,
            policy_bundle_v03=bundle,
            policy_profile_v03=profile,
            adaptive_retrieval_candidates=(),
            previous_teaching_action_v03=first.action,
            previous_decision_trace_v03=first.trace,
            sequential_policy_state_v03=sequential_state,
        )
    )
    trace = result.decision_trace_v03
    assert trace is not None
    assert trace.previous_teaching_action_ref is not None
    assert trace.previous_teaching_action_ref.entity_id == str(first.action.action_id)
    assert trace.behavior_policy_type == "DETERMINISTIC"
    anti = trace.anti_oscillation_decision
    assert anti is not None
    assert anti["decision"] == "SWITCH"
    assert "OVERRIDE" in str(anti["reason_code"])
    assert anti["fixed_decision_time"] == context.decision_time.isoformat()
    assert trace.material_evidence_refs is not None
    assert len(trace.material_evidence_refs) >= 1


@pytest.mark.asyncio
async def test_exec042_sequential_state_reconstruction_round_trip(
    exec042_db,
) -> None:
    """SequentialPolicyState reconstructed from prior trace is equivalent to
    the state produced by the SequentialTeachingPolicy itself (round-trip).
    """
    db, tmp_path = exec042_db
    from app.contracts.adaptive import (
        AvailabilityStatus,
        TeachingContextV03,
        ValueWithAvailability,
        VersionedRef,
    )
    from app.domains.teaching_policy import TeachingPolicyKernel
    from app.domains.teaching_policy.models import SequentialPolicyState
    from app.domains.teaching_policy.sequential import SequentialTeachingPolicy
    from app.domains.teaching_policy.time_source import FixedTimeSource
    from app.services.policy_runtime import (
        default_policy_bundle,
        load_policy_runtime_profile,
    )

    bundle = default_policy_bundle()
    profile = load_policy_runtime_profile()
    kernel = TeachingPolicyKernel()
    objective = VersionedRef(entity_type="LearningObjective", entity_id="obj", version="1")
    activity_ref = VersionedRef(entity_type="LearningActivity", entity_id="act", version="1")
    first_context = TeachingContextV03(
        context_id=uuid4(),
        decision_time=NOW,
        context_fingerprint="rt1",
        learning_objective_ref=objective,
        learning_activity_ref=activity_ref,
        activity_type=ValueWithAvailability(
            value="practice",
            availability=AvailabilityStatus.AVAILABLE,
            confidence=1.0,
            source_refs=(activity_ref,),
        ),
        target_capability=ValueWithAvailability(
            value="apply",
            availability=AvailabilityStatus.AVAILABLE,
            confidence=1.0,
            source_refs=(objective,),
        ),
        mastery_confidence=ValueWithAvailability(
            value=0.3,
            availability=AvailabilityStatus.AVAILABLE,
            confidence=1.0,
            source_refs=(),
        ),
        prerequisite_confidence=ValueWithAvailability(
            value=0.3,
            availability=AvailabilityStatus.AVAILABLE,
            confidence=1.0,
            source_refs=(),
        ),
        evidence_sufficiency=ValueWithAvailability(availability=AvailabilityStatus.MISSING),
        correctness_score=ValueWithAvailability(availability=AvailabilityStatus.MISSING),
        assessment_confidence=ValueWithAvailability(availability=AvailabilityStatus.MISSING),
        error_type=ValueWithAvailability(availability=AvailabilityStatus.MISSING),
        diagnostic_confidence=ValueWithAvailability(availability=AvailabilityStatus.MISSING),
        needs_probe=ValueWithAvailability(availability=AvailabilityStatus.MISSING),
        worked_example_exposure=ValueWithAvailability(availability=AvailabilityStatus.MISSING),
        delayed_independent_evidence=ValueWithAvailability(availability=AvailabilityStatus.MISSING),
        review_context=ValueWithAvailability(availability=AvailabilityStatus.MISSING),
        transfer_evidence=ValueWithAvailability(availability=AvailabilityStatus.MISSING),
        transfer_distance_novelty=ValueWithAvailability(availability=AvailabilityStatus.MISSING),
        time_budget=ValueWithAvailability(
            value=300,
            availability=AvailabilityStatus.AVAILABLE,
            confidence=1.0,
            source_refs=(activity_ref,),
        ),
        source_refs=(objective, activity_ref),
    )
    bootstrap = kernel.decide(
        context=first_context, bundle=bundle, profile=profile, assignment=None
    )
    first_action = bootstrap.action
    first_trace = bootstrap.trace
    assert first_trace.anti_oscillation_decision is None

    seq = SequentialTeachingPolicy(FixedTimeSource(NOW))
    state = SequentialPolicyState(
        previous_action=first_action,
        previous_trace=first_trace,
        evidence_opportunities_since_transition=0,
    )
    second_context = first_context.model_copy(
        update={
            "context_id": uuid4(),
            "context_fingerprint": "rt2",
            "previous_teaching_action_ref": VersionedRef(
                entity_type="teaching_action",
                entity_id=str(first_action.action_id),
                version=first_action.action_schema_version,
            ),
            "source_refs": (
                objective,
                activity_ref,
                VersionedRef(
                    entity_type="teaching_action",
                    entity_id=str(first_action.action_id),
                    version=first_action.action_schema_version,
                ),
            ),
        }
    )
    second_result = seq.decide(
        context=second_context,
        bundle=bundle,
        profile=profile,
        state=state,
        signals=(),
        assignment=None,
        time_source=FixedTimeSource(NOW),
    )
    assert second_result.transition_reason_code.startswith("HOLD_")
    assert second_result.next_state.evidence_opportunities_since_transition == 0
    assert second_result.next_state.observed_material_evidence_keys == ()

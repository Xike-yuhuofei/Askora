"""EXEC-008 v0.3 immutable persistence/writer tests."""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models  # noqa: F401 - register all metadata
from app.contracts import (
    ActualAssistanceRecordedPayloadV03,
    AnswerExposure,
    AssessmentAttemptV03,
    AssessmentDiagnosisV03,
    AssessmentResultV03,
    AssistanceSnapshotV03,
    AssistanceState,
    BehaviorPolicyType,
    DecisionAlgorithm,
    DecisionTraceV03,
    ErrorType,
    EventActor,
    EventContext,
    EventPrivacy,
    EventProvenanceV03,
    EventTrace,
    HintSpecificity,
    LearningEventEnvelopeV03,
    PolicyBundleActivationV03,
    ReplayabilityStatus,
    ScaffoldControl,
    VersionedRef,
)
from app.core.database import Base
from app.infrastructure.adaptive_records import (
    AdaptiveContractRepository,
    AssessmentRecordV03Repository,
    DecisionTraceV03Repository,
    ImmutableContractConflict,
    LearningEventV03Repository,
)
from tests.contracts.test_v03_adaptive_contracts import _action, _bundle, _context, _now


@pytest.mark.asyncio
async def test_v03_context_bundle_action_and_trace_round_trip_is_idempotent(tmp_path) -> None:
    """EXEC008-AC-005..010, PERSIST-030/040, DECISION-250."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'v03-records.db'}")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    context = _context()
    bundle = _bundle()
    action = _action(context, bundle)
    assistance = AssistanceSnapshotV03(
        scaffold_control=ScaffoldControl.LOW,
        hint_specificity=HintSpecificity.ORIENTATION,
        answer_exposure=AnswerExposure.NONE,
        assistance_state=AssistanceState.ASSISTED,
    )
    attempt = AssessmentAttemptV03(
        attempt_id=uuid4(),
        user_id=uuid4(),
        session_id=uuid4(),
        item_id=uuid4(),
        item_version="3.0",
        assessment_type="formative",
        started_at=_now(),
        first_response_at=_now(),
        submitted_at=_now(),
        response_time_ms=1200,
        raw_response="42",
        normalized_response="42",
        revision_count=0,
        assistance=assistance,
        idempotency_key=f"attempt:{uuid4()}",
    )
    result = AssessmentResultV03(
        result_id=uuid4(),
        result_version=1,
        attempt_id=attempt.attempt_id,
        item_id=attempt.item_id,
        item_version=attempt.item_version,
        score=1.0,
        passed=True,
        correctness="correct",
        rubric_scores={},
        assessment_confidence=1.0,
        diagnosis=AssessmentDiagnosisV03(
            error_type=ErrorType.UNKNOWN,
            diagnostic_confidence=None,
            reason_codes=("NO_ERROR_DIAGNOSIS_REQUIRED",),
        ),
        assistance=assistance,
        evaluator_versions=("exact-3",),
        reviewer_result="accepted",
        created_at=_now(),
    )
    assistance_event = LearningEventEnvelopeV03(
        event_id=uuid4(),
        event_type="ActualAssistanceRecorded",
        aggregate_type="Attempt",
        aggregate_id=attempt.attempt_id,
        aggregate_version=1,
        sequence=1,
        occurred_at=_now(),
        recorded_at=_now(),
        idempotency_key=f"actual-assistance:{attempt.attempt_id}",
        correlation_id=uuid4(),
        actor=EventActor(actor_type="system", actor_id="SYS08"),
        context=EventContext(
            user_id=attempt.user_id,
            session_id=attempt.session_id,
            assessment_attempt_id=attempt.attempt_id,
            knowledge_unit_ids=[],
            content_revision_ids=[],
        ),
        producer_system="SYS08",
        payload=ActualAssistanceRecordedPayloadV03(
            teaching_action_ref=VersionedRef(
                entity_type="TeachingAction", entity_id=action.action_id, version="3.0"
            ),
            attempt_ref=VersionedRef(
                entity_type="Attempt", entity_id=attempt.attempt_id, version="3.0"
            ),
            actual_assistance=assistance,
        ).model_dump(mode="json"),
        provenance=EventProvenanceV03(source="orchestrator"),
        trace=EventTrace(trace_id="trace-assistance-persistence"),
        privacy=EventPrivacy(
            classification="personal",
            external_processing=False,
            retention_class="core_learning",
        ),
    )
    activation = PolicyBundleActivationV03(
        activation_id=uuid4(),
        bundle_ref=action.policy_bundle_ref,
        activated_at=_now(),
        reason_codes=("POLICY_BUNDLE_ACTIVATED",),
    )
    trace = DecisionTraceV03(
        decision_id=action.decision_id,
        decision_type="teaching_action_selection",
        owner_system="SYS05",
        decision_time=_now(),
        teaching_context_ref=action.teaching_context_ref,
        teaching_context_schema_version=context.context_schema_version,
        context_fingerprint=context.context_fingerprint,
        context_source_refs=context.source_refs,
        policy_bundle_ref=action.policy_bundle_ref,
        policy_bundle_hash=bundle.content_digest,
        policy_version=bundle.policy_version,
        strategy_family=action.strategy_family,
        strategy_version=action.strategy_version,
        derived_teaching_stage=action.teaching_stage,
        stage_mapper_version=bundle.stage_mapper_version,
        available_actions=({"action_ref": "guided"},),
        selected_teaching_action_ref=VersionedRef(
            entity_type="TeachingAction", entity_id=action.action_id, version="3.0"
        ),
        behavior_policy_type=BehaviorPolicyType.DETERMINISTIC,
        action_propensity=None,
        algorithm=DecisionAlgorithm(
            algorithm_id="b3", algorithm_version="3.0", model_inference_ids=[], prompt_versions=[]
        ),
        reason_codes=("TEACH_GUIDED_PRACTICE",),
        replayability_status=ReplayabilityStatus.FULL,
        correlation_id=uuid4(),
        trace_id="trace-v03-persistence",
        created_at=_now(),
    )

    async with factory() as session:
        contracts = AdaptiveContractRepository(session)
        assessments = AssessmentRecordV03Repository(session)
        events = LearningEventV03Repository(session)
        traces = DecisionTraceV03Repository(session)
        await contracts.save_context(context)
        await contracts.publish_policy_bundle(bundle)
        await contracts.activate_policy_bundle(activation)
        await contracts.save_action(action)
        await assessments.save_attempt(attempt)
        await assessments.save_result(result)
        await events.append(assistance_event)
        await traces.append(trace)
        await session.commit()

    async with factory() as session:
        contracts = AdaptiveContractRepository(session)
        assessments = AssessmentRecordV03Repository(session)
        events = LearningEventV03Repository(session)
        traces = DecisionTraceV03Repository(session)
        assert await contracts.save_context(context) == context
        assert await contracts.publish_policy_bundle(bundle) == bundle
        assert await contracts.save_action(action) == action
        assert await assessments.save_attempt(attempt) == attempt
        assert await assessments.save_result(result) == result
        assert await events.append(assistance_event) == assistance_event
        assert await events.get(assistance_event.event_id) == assistance_event
        assert await traces.append(trace) == trace
        restored = await traces.get(trace.decision_id)
        assert restored == trace
        assert restored is not None
        assert restored.action_propensity is None
        await session.commit()

    async with factory() as session:
        contracts = AdaptiveContractRepository(session)
        changed = action.model_copy(update={"reason_codes": ("SEMANTIC_OVERWRITE",)})
        with pytest.raises(ImmutableContractConflict):
            await contracts.save_action(changed)

    await engine.dispose()

from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models  # noqa: F401 - register all metadata
from app.contracts.adaptive import (
    AnswerExposure,
    AssistanceState,
    AttributionScope,
    ContaminationStatus,
    HintSpecificity,
    LearningTrajectoryV03,
    OutcomeObservationV03,
    ScaffoldControl,
    TeachingEpisodeV03,
    VersionedRef,
)
from app.core.database import Base
from app.domains.teaching_policy.kernel import TeachingPolicyKernel
from app.domains.teaching_policy.outcome_evaluation import (
    ExperimentAnalysisEligibility,
    OutcomeAttributionProfile,
    OutcomeAttributionValidator,
)
from app.infrastructure.adaptive_records import (
    AdaptiveContractRepository,
    DecisionTraceV03Repository,
)
from tests.fixtures.v03_policy_factory import (
    NOW,
    fixed_uuid,
    load_profile,
    make_assignment,
    make_bundle,
    make_context,
    ref,
)


def exact_ref(entity_type: str, entity_id: object, version: str | int) -> VersionedRef:
    return VersionedRef(entity_type=entity_type, entity_id=str(entity_id), version=version)


def linked_records():
    profile = load_profile()
    bundle = make_bundle(profile)
    context = make_context({"case_id": "outcome", "mastery": 0.9})
    decision = TeachingPolicyKernel().decide(context=context, bundle=bundle, profile=profile)
    action_ref = exact_ref("teaching_action", decision.action.action_id, "3.0")
    bundle_ref = exact_ref("policy_bundle", bundle.bundle_id, bundle.policy_version)
    episode = TeachingEpisodeV03(
        episode_id=fixed_uuid("episode"),
        user_id=fixed_uuid("user"),
        learning_objective_ref=context.learning_objective_ref,
        teaching_action_refs=(action_ref,),
        started_at=NOW,
        ended_at=NOW + timedelta(minutes=20),
        policy_bundle_refs=(bundle_ref,),
    )
    episode_ref = exact_ref("teaching_episode", episode.episode_id, episode.episode_schema_version)
    trajectory = LearningTrajectoryV03(
        trajectory_id=fixed_uuid("trajectory"),
        user_id=episode.user_id,
        learning_goal_ref=ref("learning_goal", "goal"),
        episode_refs=(episode_ref,),
        started_at=NOW,
        ended_at=NOW + timedelta(days=1),
    )
    trajectory_ref = exact_ref(
        "learning_trajectory", trajectory.trajectory_id, trajectory.trajectory_schema_version
    )
    outcome = OutcomeObservationV03(
        outcome_id=fixed_uuid("outcome"),
        outcome_type="DELAYED_INDEPENDENT_PERFORMANCE",
        measurement_reference=ref("assessment_result", "delayed-result"),
        independence=True,
        assistance_state=AssistanceState.INDEPENDENT,
        scaffold_control=ScaffoldControl.NONE,
        hint_specificity=HintSpecificity.NONE,
        answer_exposure=AnswerExposure.NONE,
        actual_delay_seconds=86_400,
        score=0.9,
        success=True,
        measurement_confidence=0.95,
        active_learning_time_seconds=900,
        time_cost_seconds=1200,
        hint_cost=0.0,
        contamination_status=ContaminationStatus.CLEAN,
        attribution_scope=AttributionScope.EPISODE_ASSOCIATED,
        teaching_episode_ref=episode_ref,
        learning_trajectory_ref=trajectory_ref,
        observed_at=NOW + timedelta(days=1),
    )
    return context, bundle, decision, episode, trajectory, outcome


@pytest.mark.asyncio
async def test_episode_trajectory_outcome_persist_exact_refs_without_trace_rewrite(
    tmp_path,
) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'outcomes.db'}")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    context, bundle, decision, episode, trajectory, outcome = linked_records()
    validated = OutcomeAttributionValidator().validate(
        outcome=outcome,
        profile=OutcomeAttributionProfile(
            profile_version="attribution-1", meaningful_delay_seconds=3600
        ),
        episode=episode,
        trajectory=trajectory,
    )
    async with factory() as session:
        contracts = AdaptiveContractRepository(session)
        traces = DecisionTraceV03Repository(session)
        await contracts.save_context(context)
        await contracts.publish_policy_bundle(bundle)
        await contracts.save_action(decision.action)
        await traces.append(decision.trace)
        trace_before = await traces.get(decision.trace.decision_id)
        await contracts.save_episode(episode)
        await contracts.save_trajectory(trajectory)
        await contracts.save_outcome(validated.outcome)
        await session.commit()
        stored = await contracts.get_outcome(outcome.outcome_id)
        trace_after = await traces.get(decision.trace.decision_id)

    assert stored == outcome
    assert trace_before == trace_after == decision.trace
    assert stored is not None
    assert stored.measurement_reference == outcome.measurement_reference
    assert stored.assistance_state is AssistanceState.INDEPENDENT
    assert stored.actual_delay_seconds == 86_400
    assert stored.teaching_episode_ref is not None
    assert stored.learning_trajectory_ref is not None
    await engine.dispose()


def test_delayed_outcome_is_not_last_touch_action_direct() -> None:
    _context, _bundle, _decision, episode, trajectory, outcome = linked_records()
    payload = outcome.model_dump()
    payload["attribution_scope"] = AttributionScope.ACTION_DIRECT
    direct = OutcomeObservationV03.model_validate(payload)
    with pytest.raises(ValueError, match="DELAYED_OUTCOME_CANNOT_DEFAULT_LAST_TOUCH"):
        OutcomeAttributionValidator().validate(
            outcome=direct,
            profile=OutcomeAttributionProfile(
                profile_version="attribution-1", meaningful_delay_seconds=3600
            ),
            episode=episode,
            trajectory=trajectory,
        )


def test_experimentally_causal_requires_positive_identification_evidence() -> None:
    _context, _bundle, _decision, episode, trajectory, outcome = linked_records()
    base_context, assignment = make_assignment(make_context({"case_id": "experiment"}))
    assert base_context.experiment_assignment_ref is not None
    payload = outcome.model_dump()
    payload.update(
        {
            "attribution_scope": AttributionScope.EXPERIMENTALLY_CAUSAL,
            "experiment_association": base_context.experiment_assignment_ref,
        }
    )
    causal = OutcomeObservationV03.model_validate(payload)
    validator = OutcomeAttributionValidator()
    profile = OutcomeAttributionProfile(
        profile_version="attribution-1", meaningful_delay_seconds=3600
    )
    with pytest.raises(ValueError, match="CAUSAL_ATTRIBUTION_REQUIRES"):
        validator.validate(outcome=causal, profile=profile, episode=episode, trajectory=trajectory)
    eligibility = ExperimentAnalysisEligibility(
        assignment_ref=base_context.experiment_assignment_ref,
        analysis_plan_ref=ref("analysis_plan", "pre-registered"),
        assignment_integrity_verified=True,
        analysis_unit_eligible=True,
        outcome_definition_pre_registered=True,
        reason_codes=("PRE_REGISTERED_RANDOMIZED_ANALYSIS",),
    )
    validated = validator.validate(
        outcome=causal,
        profile=profile,
        episode=episode,
        trajectory=trajectory,
        assignment=assignment,
        experiment_eligibility=eligibility,
    )
    assert "EXPERIMENT_IDENTIFICATION_EVIDENCE_VERIFIED" in validated.reason_codes


def test_assignment_probability_never_becomes_action_propensity() -> None:
    profile = load_profile()
    context, assignment = make_assignment(make_context({"case_id": "probability-separation"}))
    decision = TeachingPolicyKernel().decide(
        context=context,
        bundle=make_bundle(profile),
        profile=profile,
        assignment=assignment,
    )
    assert assignment.assignment_probability == 0.5
    assert decision.trace.experiment_assignment_probability == 0.5
    assert decision.trace.action_propensity is None

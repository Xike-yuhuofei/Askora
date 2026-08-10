from __future__ import annotations

from datetime import timedelta

import pytest

from app.contracts.adaptive import (
    AssistanceState,
    AttributionScope,
    ContaminationStatus,
    LearningTrajectoryV03,
    OutcomeObservationV03,
    StrategyFamily,
    TeachingEpisodeV03,
    VersionedRef,
)
from app.contracts.planning import ReviewObservation
from app.domains.assessment import AdaptiveAssessmentService
from app.domains.learner_model import (
    AdaptiveEvidenceEligibility,
    AdaptiveEvidenceEligibilityProfile,
    WeightedBKTProjector,
)
from app.domains.review_scheduler import ReviewScheduler
from app.domains.teaching_policy.outcome_evaluation import (
    OutcomeAttributionProfile,
    OutcomeAttributionValidator,
)
from app.orchestration.learning_facade import LearningOrchestrationFacade
from tests.fixtures.v03_execution_factory import TightRenderer, adaptive_request
from tests.fixtures.v03_policy_factory import (
    NOW,
    fixed_uuid,
    load_profile,
    make_bundle,
    make_context,
    ref,
    with_previous_action,
)


@pytest.mark.asyncio
async def test_policy_to_actual_assistance_to_learner_evidence_e2e() -> None:
    turn = await LearningOrchestrationFacade(adaptive_renderer=TightRenderer()).run_turn(
        adaptive_request()
    )
    assert turn.teaching_action_v03 is not None
    assert turn.decision_trace_v03 is not None
    assert turn.evidence_bundle_v03 is not None
    assert turn.adaptive_execution_v03 is not None
    action = turn.teaching_action_v03
    execution = turn.adaptive_execution_v03

    assessment = AdaptiveAssessmentService().assess_exact(
        user_id=fixed_uuid("e2e-user"),
        session_id=fixed_uuid("e2e-session"),
        item_id=fixed_uuid("e2e-item"),
        item_version="1",
        assessment_type="formative",
        response="correct",
        expected_answer="correct",
        teaching_action=action,
        actual_assistance=execution.actual_assistance,
        teaching_action_ref=execution.teaching_action_ref,
        rendered_response_ref=VersionedRef(
            entity_type="rendered_response",
            entity_id=str(execution.response_id),
            version=execution.response_version,
        ),
        started_at=NOW + timedelta(days=1),
        submitted_at=NOW + timedelta(days=1, seconds=30),
        idempotency_key="v03-e2e-attempt",
        assessment_confidence=0.95,
        diagnostic_confidence=0.2,
    )
    evidence = AdaptiveEvidenceEligibility().decide(
        result=assessment.result,
        attempt=assessment.attempt,
        actual_assistance=execution.actual_assistance,
        profile=AdaptiveEvidenceEligibilityProfile(
            profile_version="e2e-eligibility-1",
            minimum_assessment_confidence=0.5,
            independence_weights={
                AssistanceState.INDEPENDENT: 1.0,
                AssistanceState.ASSISTED: 0.35,
                AssistanceState.ANSWER_EXPOSED: 0.0,
            },
            novelty_weights={"repeated": 0.5, "near_variant": 0.8, "far_variant": 1.0},
        ),
        knowledge_unit_id=fixed_uuid("knowledge-unit"),
        dimension="routine_application",
        novelty="far_variant",
        delay_seconds=86_400,
        source_event_refs=(ref("learning_event", "e2e-actual-assistance"),),
    )
    assert evidence.accepted
    assert evidence.evidence is not None
    assert evidence.evidence.assistance_state is execution.actual_assistance.assistance_state
    estimate = WeightedBKTProjector().project(
        user_id=assessment.attempt.user_id,
        knowledge_unit_id=evidence.evidence.knowledge_unit_id,
        evidence=[evidence.evidence],
        version=1,
    )
    assert estimate.source_evidence_ids == [evidence.evidence.evidence_id]
    assert estimate.evidence_count == 1
    assert estimate.hint_dependency_score == 0.0
    assert estimate.delayed_recall_evidence_count == 1

    observation = ReviewObservation(
        observation_id=fixed_uuid("e2e-v03-review-observation"),
        user_id=assessment.attempt.user_id,
        knowledge_unit_id=evidence.evidence.knowledge_unit_id,
        observed_at=assessment.result.created_at,
        actual_reviewed_at=assessment.result.created_at,
        retrieval_required=True,
        independence="independent",
        hint_level=0,
        answer_seen_before_attempt=False,
        assessment_confidence=assessment.result.assessment_confidence,
        outcome="success",
        delay_seconds=evidence.evidence.delay_seconds,
        source_evidence_id=evidence.evidence.evidence_id,
        source_event_ids=[fixed_uuid("e2e-actual-assistance")],
    )
    review = ReviewScheduler().update(observation=observation, prior=None, version=1)
    assert review.schedule.next_due_at is not None
    assert "INDEPENDENT_RECALL_EXTENDED" in review.reason_codes

    profile = load_profile()
    next_context = with_previous_action(
        make_context(
            {
                "case_id": "e2e-v03-next",
                "mastery": estimate.competence_probability,
                "independent_success": True,
                "delayed_independent": True,
                "review_context": True,
            }
        ),
        action,
    )
    # Second+ production decision MUST go through SequentialTeachingPolicy via
    # the production reconstruction helper, never a direct kernel call.
    from app.domains.teaching_policy.sequential import SequentialTeachingPolicy
    from app.domains.teaching_policy.time_source import FixedTimeSource
    from app.orchestration.learning_facade import _reconstruct_sequential_policy_state

    sequential_state = _reconstruct_sequential_policy_state(
        previous_action=action,
        previous_trace=turn.decision_trace_v03,
    )
    next_decision = (
        SequentialTeachingPolicy(FixedTimeSource(NOW))
        .decide(
            context=next_context,
            bundle=make_bundle(profile),
            profile=profile,
            state=sequential_state,
            signals=(),
        )
        .decision
    )
    assert next_decision.action.strategy_family is StrategyFamily.RETRIEVAL_PRACTICE

    action_ref = VersionedRef(
        entity_type="teaching_action",
        entity_id=str(action.action_id),
        version=action.action_schema_version,
    )
    episode = TeachingEpisodeV03(
        episode_id=fixed_uuid("e2e-v03-episode"),
        user_id=assessment.attempt.user_id,
        learning_objective_ref=action.learning_objective_ref,
        teaching_action_refs=(action_ref,),
        started_at=NOW,
        ended_at=assessment.result.created_at,
        policy_bundle_refs=(action.policy_bundle_ref,),
    )
    episode_ref = VersionedRef(
        entity_type="teaching_episode",
        entity_id=str(episode.episode_id),
        version=episode.episode_schema_version,
    )
    trajectory = LearningTrajectoryV03(
        trajectory_id=fixed_uuid("e2e-v03-trajectory"),
        user_id=assessment.attempt.user_id,
        learning_goal_ref=ref("learning_goal", "e2e-v03-goal"),
        episode_refs=(episode_ref,),
        started_at=NOW,
        ended_at=assessment.result.created_at,
    )
    trajectory_ref = VersionedRef(
        entity_type="learning_trajectory",
        entity_id=str(trajectory.trajectory_id),
        version=trajectory.trajectory_schema_version,
    )
    outcome = OutcomeObservationV03(
        outcome_id=fixed_uuid("e2e-v03-outcome"),
        outcome_type="DELAYED_INDEPENDENT_PERFORMANCE",
        measurement_reference=VersionedRef(
            entity_type="assessment_result",
            entity_id=str(assessment.result.result_id),
            version=assessment.result.result_version,
        ),
        independence=True,
        assistance_state=execution.actual_assistance.assistance_state,
        scaffold_control=execution.actual_assistance.scaffold_control,
        hint_specificity=execution.actual_assistance.hint_specificity,
        answer_exposure=execution.actual_assistance.answer_exposure,
        actual_delay_seconds=evidence.evidence.delay_seconds,
        score=assessment.result.score,
        success=assessment.result.passed,
        measurement_confidence=assessment.result.assessment_confidence,
        active_learning_time_seconds=assessment.attempt.response_time_ms // 1000,
        time_cost_seconds=assessment.attempt.response_time_ms // 1000,
        hint_cost=0.0,
        contamination_status=ContaminationStatus.CLEAN,
        attribution_scope=AttributionScope.EPISODE_ASSOCIATED,
        teaching_episode_ref=episode_ref,
        learning_trajectory_ref=trajectory_ref,
        observed_at=assessment.result.created_at,
    )
    validated_outcome = OutcomeAttributionValidator().validate(
        outcome=outcome,
        profile=OutcomeAttributionProfile(
            profile_version="e2e-attribution/1.0", meaningful_delay_seconds=3_600
        ),
        episode=episode,
        trajectory=trajectory,
    )
    assert validated_outcome.outcome.measurement_reference.entity_id == str(
        assessment.result.result_id
    )
    assert "EPISODE_ASSOCIATION_ONLY_NOT_CAUSAL" in validated_outcome.reason_codes

    correlation_chain = {
        "correlation_id": turn.correlation_id,
        "teaching_context": str(turn.decision_trace_v03.teaching_context_ref.entity_id),
        "policy_bundle": str(action.policy_bundle_ref.entity_id),
        "decision_trace": str(turn.decision_trace_v03.decision_id),
        "teaching_action": str(action.action_id),
        "evidence_bundle": str(turn.evidence_bundle_v03.bundle_id),
        "rendered_response": str(execution.response_id),
        "attempt": str(assessment.attempt.attempt_id),
        "assessment_result": str(assessment.result.result_id),
        "learner_evidence": str(evidence.evidence.evidence_id),
        "mastery_estimate": str(estimate.estimate_id),
        "review_schedule": str(review.schedule.schedule_id),
        "next_decision": str(next_decision.trace.decision_id),
        "teaching_episode": str(episode.episode_id),
        "learning_trajectory": str(trajectory.trajectory_id),
        "outcome_observation": str(outcome.outcome_id),
    }
    assert all(correlation_chain.values())
    assert len(set(correlation_chain.values())) == len(correlation_chain)
    assert turn.engine_debug == {
        **turn.engine_debug,
        "final_action_owner": "SYS05",
        "retrieval_owner": "SYS02",
        "execution_owner": "SYS08",
    }

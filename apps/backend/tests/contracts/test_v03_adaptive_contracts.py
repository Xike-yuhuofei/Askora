"""EXEC-008 v0.3 canonical contract and writer-cutover tests."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.contracts import (
    ActionModifier,
    ActualAssistanceRecordedPayloadV03,
    AnswerExposure,
    AssessmentDiagnosisV03,
    AssessmentResultV03,
    AssistanceSnapshotV03,
    AssistanceState,
    AttributionScope,
    AvailabilityStatus,
    BehaviorPolicyType,
    ContaminationStatus,
    DecisionAlgorithm,
    DecisionFeatureV03,
    DecisionTraceV03,
    ErrorType,
    EventActor,
    EventContext,
    EventPrivacy,
    EventProvenanceV03,
    EventTrace,
    ExperimentAssignmentV03,
    HintSpecificity,
    InteractionMove,
    LearningEventEnvelopeV03,
    OutcomeObservationV03,
    PolicyBundleV03,
    ReplayabilityStatus,
    ScaffoldControl,
    StrategyFamily,
    TeachingActionV03,
    TeachingContextV03,
    TeachingStage,
    ValidationObligation,
    ValueWithAvailability,
    VersionedRef,
)


def _now() -> datetime:
    return datetime(2026, 8, 7, 14, 0, tzinfo=timezone.utc)


def _ref(entity_type: str, version: str | int = 1) -> VersionedRef:
    return VersionedRef(entity_type=entity_type, entity_id=uuid4(), version=version)


def _available(value: object, ref: VersionedRef) -> ValueWithAvailability:
    return ValueWithAvailability(
        value=value,
        availability=AvailabilityStatus.AVAILABLE,
        confidence=0.9,
        source_refs=(ref,),
    )


def _missing() -> ValueWithAvailability:
    return ValueWithAvailability(value=None, availability=AvailabilityStatus.MISSING)


def _context() -> TeachingContextV03:
    objective = _ref("LearningObjective", 3)
    activity = _ref("LearningActivity", 2)
    assessment = _ref("AssessmentResult", 4)
    return TeachingContextV03(
        context_id=uuid4(),
        decision_time=_now(),
        context_fingerprint="sha256:context-fixture",
        learning_objective_ref=objective,
        learning_activity_ref=activity,
        activity_type=_available("practice", activity),
        target_capability=_available("routine_application", objective),
        mastery_confidence=_missing(),
        prerequisite_confidence=_missing(),
        evidence_sufficiency=_available("LOW", assessment),
        recent_assessment_result_ref=assessment,
        correctness_score=_available(0.5, assessment),
        assessment_confidence=_available(0.95, assessment),
        error_type=_available(ErrorType.UNKNOWN.value, assessment),
        diagnostic_confidence=ValueWithAvailability(
            value=0.2,
            availability=AvailabilityStatus.LOW_CONFIDENCE,
            confidence=0.2,
            source_refs=(assessment,),
        ),
        needs_probe=_available(True, assessment),
        worked_example_exposure=_missing(),
        delayed_independent_evidence=_missing(),
        review_context=_missing(),
        transfer_evidence=_missing(),
        transfer_distance_novelty=_missing(),
        time_budget=_available(600, activity),
        source_refs=(objective, activity, assessment),
    )


def _bundle() -> PolicyBundleV03:
    return PolicyBundleV03(
        bundle_id="policy-b3-2026-08-07",
        policy_version="3.0.0",
        hard_rule_set_version="hard-1",
        stage_mapper_version="stage-1",
        candidate_table_version="candidate-1",
        feature_schema_version="feature-1",
        normalization_version="norm-1",
        weight_profile_version="weights-1",
        anti_oscillation_profile_version="anti-1",
        tie_break_version="tie-1",
        fallback_profile_version="fallback-1",
        subject_profile_version=None,
        content_digest="sha256:policy-fixture",
        published_at=_now(),
    )


def _action(context: TeachingContextV03, bundle: PolicyBundleV03) -> TeachingActionV03:
    return TeachingActionV03(
        action_id=uuid4(),
        learning_objective_ref=context.learning_objective_ref,
        learning_activity_ref=context.learning_activity_ref,
        strategy_family=StrategyFamily.GUIDED_PRACTICE,
        strategy_version="guided-1",
        teaching_stage=TeachingStage.GUIDED_PRACTICE,
        interaction_moves=(InteractionMove.SOCRATIC_PROBE,),
        action_modifiers=ActionModifier(self_explanation=True),
        scaffold_control=ScaffoldControl.MEDIUM,
        hint_specificity=HintSpecificity.CONCEPTUAL_STRATEGIC,
        answer_exposure=AnswerExposure.NONE,
        evidence_requirements=("example",),
        expected_evidence_type="routine_application",
        success_condition={"score_gte": 0.8},
        failure_condition={"attempts_gte": 3},
        max_attempts=3,
        time_budget_seconds=600,
        validation_obligation=ValidationObligation.NONE,
        reason_codes=("TEACH_GUIDED_PRACTICE",),
        policy_bundle_ref=VersionedRef(
            entity_type="PolicyBundle", entity_id=bundle.bundle_id, version=bundle.policy_version
        ),
        teaching_context_ref=VersionedRef(
            entity_type="TeachingContext",
            entity_id=context.context_id,
            version=context.context_schema_version,
        ),
        decision_id=uuid4(),
        created_at=_now(),
    )


def test_strategy_family_is_exactly_six_and_socratic_is_only_a_move() -> None:
    """EXEC008-AC-001/002, DOMAIN-083..086, SYS05-201..203."""
    assert {item.value for item in StrategyFamily} == {
        "EXPLICIT_INSTRUCTION",
        "GUIDED_PRACTICE",
        "FADING_PRACTICE",
        "RETRIEVAL_PRACTICE",
        "ERROR_REMEDIATION",
        "TRANSFER_CHALLENGE",
    }
    assert InteractionMove.SOCRATIC_PROBE.value == "SOCRATIC_PROBE"
    with pytest.raises(ValueError):
        StrategyFamily("SOCRATIC_PROBING")
    with pytest.raises(ValueError):
        StrategyFamily("PRODUCTIVE_FAILURE")


def test_v03_assistance_and_diagnosis_are_orthogonal_and_strict() -> None:
    """EXEC008-AC-003/004, DOMAIN-061..074, SYS04-210..224."""
    assistance = AssistanceSnapshotV03(
        scaffold_control=ScaffoldControl.LOW,
        hint_specificity=HintSpecificity.ORIENTATION,
        answer_exposure=AnswerExposure.NONE,
        assistance_state=AssistanceState.ASSISTED,
    )
    result = AssessmentResultV03(
        result_id=uuid4(),
        result_version=1,
        attempt_id=uuid4(),
        item_id=uuid4(),
        item_version="3.0",
        score=0.7,
        passed=None,
        correctness="partial",
        rubric_scores={"method": 0.7},
        assessment_confidence=0.98,
        diagnosis=AssessmentDiagnosisV03(
            error_type=ErrorType.UNKNOWN,
            diagnostic_confidence=0.2,
            needs_probe=True,
            reason_codes=("DIAGNOSIS_UNCERTAIN",),
        ),
        assistance=assistance,
        evaluator_versions=("exact-3",),
        reviewer_result="accepted",
        created_at=_now(),
    )
    assert result.assessment_confidence != result.diagnosis.diagnostic_confidence
    assert result.assistance.assistance_state is AssistanceState.ASSISTED
    with pytest.raises(ValueError):
        ErrorType("condition_omission")


def test_teaching_context_and_policy_bundle_are_frozen_exact_version_contracts() -> None:
    """EXEC008-AC-005/006, DOMAIN-088/089, SYS05-210..212/300..303."""
    context = _context()
    bundle = _bundle()
    assert context.source_refs[0].version == 3
    assert context.mastery_confidence.availability is AvailabilityStatus.MISSING
    with pytest.raises(ValidationError):
        context.context_fingerprint = "changed"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        bundle.policy_version = "3.0.1"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        ValueWithAvailability(value=0, availability=AvailabilityStatus.MISSING)
    with pytest.raises(ValidationError):
        VersionedRef(entity_type="LearnerState", entity_id=uuid4(), version="")


def test_v03_writer_serializes_no_legacy_strategy_or_integer_support_fields() -> None:
    """EXEC008-AC-009/VSLICE-311: new canonical writer has no dual-write."""
    action = _action(_context(), _bundle())
    payload = action.model_dump(mode="json")
    serialized = action.model_dump_json()
    assert payload["strategy_family"] == "GUIDED_PRACTICE"
    assert "strategy_id" not in serialized
    assert "scaffold_level" not in serialized
    assert "hint_level" not in serialized
    assert "answer_exposure_max" not in serialized
    assert payload["interaction_moves"] == ["SOCRATIC_PROBE"]


def test_decision_trace_v03_separates_assignment_from_action_probability() -> None:
    """EXEC008-AC-007, DECISION-200/210..212."""
    context = _context()
    bundle = _bundle()
    action = _action(context, bundle)
    assignment = ExperimentAssignmentV03(
        assignment_id=uuid4(),
        experiment_id="b2-vs-b3",
        experiment_version="1",
        unit_ref="local-user",
        variant_id="b3",
        assignment_probability=0.5,
        assigned_at=_now(),
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
        features=(
            DecisionFeatureV03(
                feature_name="stage_fit",
                value=1.0,
                availability=AvailabilityStatus.AVAILABLE,
                confidence=1.0,
                feature_version="feature-1",
                source_refs=context.source_refs,
            ),
        ),
        candidate_scores=({"action_ref": "guided", "score": 1.0},),
        selected_teaching_action_ref=VersionedRef(
            entity_type="TeachingAction", entity_id=action.action_id, version="3.0"
        ),
        experiment_assignment_ref=VersionedRef(
            entity_type="ExperimentAssignment", entity_id=assignment.assignment_id, version="3.0"
        ),
        experiment_assignment_probability=assignment.assignment_probability,
        behavior_policy_type=BehaviorPolicyType.DETERMINISTIC,
        action_propensity=None,
        algorithm=DecisionAlgorithm(
            algorithm_id="b3-policy",
            algorithm_version="3.0",
            model_inference_ids=[],
            prompt_versions=[],
        ),
        reason_codes=("TEACH_GUIDED_PRACTICE",),
        replayability_status=ReplayabilityStatus.FULL,
        correlation_id=uuid4(),
        trace_id="trace-v03-contract",
        created_at=_now(),
    )
    assert trace.experiment_assignment_probability == 0.5
    assert trace.action_propensity is None
    with pytest.raises(ValidationError):
        DecisionTraceV03.model_validate({**trace.model_dump(mode="json"), "action_propensity": 1.0})


def test_outcome_contract_does_not_infer_causal_attribution_without_experiment() -> None:
    """DOMAIN-111..113: outcome and experiment are additive, separate contracts."""
    base = {
        "outcome_id": uuid4(),
        "outcome_type": "delayed_independent_performance",
        "measurement_reference": _ref("AssessmentResult", 2),
        "independence": True,
        "assistance_state": AssistanceState.INDEPENDENT,
        "scaffold_control": ScaffoldControl.NONE,
        "hint_specificity": HintSpecificity.NONE,
        "answer_exposure": AnswerExposure.NONE,
        "actual_delay_seconds": 86400,
        "score": 1.0,
        "success": True,
        "measurement_confidence": 1.0,
        "contamination_status": ContaminationStatus.CLEAN,
        "observed_at": _now(),
    }
    outcome = OutcomeObservationV03(
        **base,
        attribution_scope=AttributionScope.EPISODE_ASSOCIATED,
    )
    assert outcome.attribution_scope is AttributionScope.EPISODE_ASSOCIATED
    with pytest.raises(ValidationError):
        OutcomeObservationV03(
            **base,
            attribution_scope=AttributionScope.EXPERIMENTALLY_CAUSAL,
        )


def test_v03_actual_assistance_event_uses_canonical_axes_and_owner() -> None:
    """EVENT-200/201, EXEC008-AC-003/009."""
    assistance = AssistanceSnapshotV03(
        scaffold_control=ScaffoldControl.LOW,
        hint_specificity=HintSpecificity.ORIENTATION,
        answer_exposure=AnswerExposure.NONE,
        assistance_state=AssistanceState.ASSISTED,
    )
    payload = ActualAssistanceRecordedPayloadV03(
        teaching_action_ref=_ref("TeachingAction", "3.0"),
        actual_assistance=assistance,
    )
    event = LearningEventEnvelopeV03(
        event_id=uuid4(),
        event_type="ActualAssistanceRecorded",
        aggregate_type="Attempt",
        aggregate_id=uuid4(),
        aggregate_version=1,
        sequence=1,
        occurred_at=_now(),
        recorded_at=_now(),
        idempotency_key=f"actual-assistance:{uuid4()}",
        correlation_id=uuid4(),
        actor=EventActor(actor_type="system", actor_id="SYS08"),
        context=EventContext(user_id=uuid4(), knowledge_unit_ids=[], content_revision_ids=[]),
        producer_system="SYS08",
        payload=payload.model_dump(mode="json"),
        provenance=EventProvenanceV03(
            source="orchestrator", policy_bundle_ref=_ref("PolicyBundle", "3.0.0")
        ),
        trace=EventTrace(trace_id="trace-assistance-v03"),
        privacy=EventPrivacy(
            classification="personal",
            external_processing=False,
            retention_class="core_learning",
        ),
    )
    serialized = event.model_dump_json()
    assert event.producer_system == "SYS08"
    assert "scaffold_level" not in serialized
    assert "hint_level" not in serialized
    assert "answer_exposure_max" not in serialized

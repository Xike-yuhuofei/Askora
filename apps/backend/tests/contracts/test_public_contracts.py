"""EXEC-001 T1 public contract coverage."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.contracts import (
    AssessmentResult,
    DecisionAlgorithm,
    DecisionExperiment,
    DecisionInput,
    DecisionTrace,
    EventActor,
    EventContext,
    EventPrivacy,
    EventProvenance,
    EventTrace,
    EvidenceBundle,
    EvidenceItem,
    LearnerEvidence,
    LearningActivity,
    LearningEventEnvelope,
    LearningPlan,
    MasteryEstimate,
    ReviewSchedule,
    TeachingAction,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def make_event(**overrides) -> LearningEventEnvelope:
    data = {
        "event_id": uuid4(),
        "event_type": "ResponseSubmitted",
        "schema_version": "1.0",
        "aggregate_type": "Attempt",
        "aggregate_id": uuid4(),
        "aggregate_version": 1,
        "sequence": 1,
        "occurred_at": _now(),
        "recorded_at": _now(),
        "idempotency_key": f"submit:{uuid4()}",
        "correlation_id": uuid4(),
        "causation_id": None,
        "actor": EventActor(actor_type="learner", actor_id="local-user"),
        "context": EventContext(user_id=uuid4(), knowledge_unit_ids=[], content_revision_ids=[]),
        "payload": {
            "attempt_id": str(uuid4()),
            "assistance_snapshot": {
                "max_hint_level": 2,
                "assistance_class": "conceptual",
                "source_visible": True,
                "answer_visible": False,
            },
            "response_hash": "sha256:fixture",
        },
        "provenance": EventProvenance(source="api"),
        "trace": EventTrace(trace_id="trace-contract"),
        "privacy": EventPrivacy(
            classification="personal",
            external_processing=False,
            retention_class="core_learning",
        ),
    }
    data.update(overrides)
    return LearningEventEnvelope(**data)


def test_event_v1_is_strict_immutable_and_preserves_assistance_snapshot() -> None:
    """EVENT-002/EVENT-032/EVENT-AC-006: history is frozen and auditable."""
    event = make_event()

    assert event.schema_version == "1.0"
    assert event.payload["assistance_snapshot"]["answer_visible"] is False
    with pytest.raises(ValidationError):
        event.sequence = 2  # type: ignore[misc]


def test_unknown_event_major_and_naive_datetime_are_rejected() -> None:
    """EVENT-AC-007/SCHEMA-AC-002/DOMAIN-004."""
    with pytest.raises(ValidationError):
        make_event(schema_version="2.0")
    with pytest.raises(ValidationError):
        make_event(occurred_at=datetime(2026, 8, 7, 10, 0, 0))


def test_decision_trace_v1_requires_reason_code_and_rejects_unknown_major() -> None:
    """DECISION-020/SCHEMA-003: trace keeps machine-queryable reasons."""
    base = {
        "decision_id": uuid4(),
        "decision_type": "TeachingActionSelected",
        "owner_system": "teaching_policy",
        "inputs": [DecisionInput(entity_type="LearnerState", entity_id=uuid4(), version=4)],
        "candidates": [{"action": "hint"}, {"action": "practice"}],
        "selected": {"action": "hint"},
        "constraints": [{"type": "hard", "answer_exposure_max": 2}],
        "reason_codes": ["TEACH_HIGH_HINT_DEPENDENCY"],
        "confidence": None,
        "algorithm": DecisionAlgorithm(
            algorithm_id="teaching-policy",
            algorithm_version="1.0",
            model_inference_ids=[],
            prompt_versions=[],
        ),
        "experiment": DecisionExperiment(),
        "created_at": _now(),
        "correlation_id": uuid4(),
        "trace_id": "trace-decision",
    }
    trace = DecisionTrace(**base)
    assert trace.selected == {"action": "hint"}
    with pytest.raises(ValidationError):
        DecisionTrace(**{**base, "schema_version": "2.0"})
    with pytest.raises(ValidationError):
        DecisionTrace(**{**base, "reason_codes": []})


def test_shared_learning_contracts_follow_canonical_field_semantics() -> None:
    """DEP-002/DOMAIN-070..100: public objects have one strict schema."""
    now = _now()
    user_id = uuid4()
    knowledge_unit_id = uuid4()
    attempt_id = uuid4()
    result_id = uuid4()
    event_id = uuid4()
    evidence_id = uuid4()
    plan_id = uuid4()
    activity_id = uuid4()
    objective_id = uuid4()

    assessment = AssessmentResult(
        result_id=result_id,
        result_version=1,
        attempt_id=attempt_id,
        item_id=uuid4(),
        item_version="1.0",
        score=0.8,
        passed=True,
        correctness="partial",
        rubric_scores={"method": 0.8},
        error_type="expression_incomplete",
        misconception_evidence=[],
        independence="independent",
        assessment_confidence=0.9,
        evaluator_versions=["exact-1.0"],
        reason_codes=["ASSESS_PARTIAL_EXPRESSION"],
        reviewer_result="accepted",
        created_at=now,
    )
    evidence = LearnerEvidence(
        evidence_id=evidence_id,
        user_id=user_id,
        knowledge_unit_id=knowledge_unit_id,
        attempt_id=attempt_id,
        result_id=result_id,
        accepted_at=now,
        dimension="routine_application",
        outcome="partial",
        score=assessment.score,
        confidence=0.9,
        independence="independent",
        delay_seconds=60,
        novelty="near_variant",
        evidence_weight=0.7,
        item_difficulty=0.5,
        source_event_ids=[event_id],
        eligibility_reason_codes=["EVIDENCE_AUDITABLE"],
    )
    mastery = MasteryEstimate(
        estimate_id=uuid4(),
        version=1,
        user_id=user_id,
        knowledge_unit_id=knowledge_unit_id,
        competence_probability=0.65,
        confidence=0.6,
        independent_success_count=1,
        hint_dependency_score=0.1,
        last_independent_success_at=now,
        delayed_recall_evidence_count=0,
        transfer_evidence_count=0,
        active_misconception_ids=[],
        evidence_count=1,
        effective_evidence_weight=0.7,
        algorithm_id="weighted-bkt",
        algorithm_version="1.0",
        source_evidence_ids=[evidence.evidence_id],
        created_at=now,
    )
    activity = LearningActivity(
        activity_id=activity_id,
        plan_id=plan_id,
        plan_version=1,
        objective_id=objective_id,
        type="practice",
        knowledge_unit_ids=[knowledge_unit_id],
        estimated_duration_minutes=10,
        priority=0.8,
        reason_codes=["PLAN_PRACTICE_GAP"],
        status="available",
    )
    plan = LearningPlan(
        plan_id=plan_id,
        version=1,
        learning_goal_id=uuid4(),
        planning_horizon={"days": 1},
        objective_ids=[objective_id],
        activity_ids=[activity.activity_id],
        constraints={},
        assumptions={},
        created_from_learner_state_version=1,
        knowledge_graph_version="1.0",
        review_schedule_version=None,
        reason_codes=["PLAN_PRACTICE_GAP"],
        status="active",
    )
    action = TeachingAction(
        action_id=uuid4(),
        learning_objective_id=objective_id,
        learning_activity_id=activity_id,
        strategy_id="guided-practice",
        strategy_version="1.0",
        action_type="practice",
        scaffold_level=1,
        hint_level=1,
        answer_exposure_max=2,
        evidence_requirements=["example"],
        expected_evidence_type="routine_application",
        success_condition={"score_gte": 0.8},
        failure_condition={"attempts_gte": 3},
        max_attempts=3,
        time_budget_seconds=600,
        reason_codes=["TEACH_GUIDED_PRACTICE"],
        policy_version="1.0",
        decision_id=uuid4(),
    )
    bundle = EvidenceBundle(
        bundle_id=uuid4(),
        request_id=uuid4(),
        teaching_action_id=action.action_id,
        assessment_context_id=None,
        source_scope={"document_ids": []},
        index_versions={"lexical": "1"},
        items=[
            EvidenceItem(
                evidence_id=uuid4(),
                source_span_ids=[uuid4()],
                knowledge_unit_ids=[knowledge_unit_id],
                pedagogical_role="example",
                content="synthetic public fixture",
                relevance=0.9,
                confidence=0.8,
                exposure_level=1,
                allowed_use="learner_visible",
            )
        ],
        conflicts=[],
        missing_roles=[],
        bundle_confidence=0.8,
        retrieval_trace_id=uuid4(),
    )
    review = ReviewSchedule(
        schedule_id=uuid4(),
        version=1,
        user_id=user_id,
        knowledge_unit_id=knowledge_unit_id,
        memory_model="simple-baseline",
        model_version="1.0",
        difficulty=0.4,
        stability=1.0,
        retrievability=0.8,
        desired_retention=0.9,
        last_valid_retrieval_at=now,
        next_due_at=now,
        review_priority=0.6,
        evidence_quality=0.7,
        source_event_ids=[event_id],
        created_at=now,
    )

    assert mastery.source_evidence_ids == [evidence_id]
    assert plan.activity_ids == [activity_id]
    assert bundle.items[0].exposure_level <= action.answer_exposure_max
    assert review.knowledge_unit_id == knowledge_unit_id

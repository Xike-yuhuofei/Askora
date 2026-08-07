"""Fixed constructors for EXEC-009 deterministic policy tests."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from app.contracts.adaptive import (
    AnswerExposure,
    AssessmentAttemptV03,
    AssessmentDiagnosisV03,
    AssessmentResultV03,
    AssistanceSnapshotV03,
    AssistanceState,
    AvailabilityStatus,
    ErrorType,
    ExperimentAssignmentV03,
    HintSpecificity,
    PolicyBundleV03,
    ScaffoldControl,
    TeachingActionV03,
    TeachingContextV03,
    ValueWithAvailability,
    VersionedRef,
)
from app.domains.teaching_policy.models import PolicyRuntimeProfile

FIXTURE_DIR = Path(__file__).parent / "v03_policy"
NOW = datetime(2026, 8, 7, 8, 0, tzinfo=timezone.utc)


def fixed_uuid(name: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"askora:exec009:{name}")


def ref(entity_type: str, name: str, version: str = "1") -> VersionedRef:
    return VersionedRef(entity_type=entity_type, entity_id=str(fixed_uuid(name)), version=version)


def available(value: Any, confidence: float | None = 1.0) -> ValueWithAvailability:
    return ValueWithAvailability(
        value=value,
        availability=AvailabilityStatus.AVAILABLE,
        confidence=confidence,
        source_refs=(ref("fixture", "source"),),
    )


def missing() -> ValueWithAvailability:
    return ValueWithAvailability(value=None, availability=AvailabilityStatus.MISSING)


def load_profile() -> PolicyRuntimeProfile:
    return PolicyRuntimeProfile.model_validate_json((FIXTURE_DIR / "profile.json").read_text())


def make_bundle(profile: PolicyRuntimeProfile | None = None) -> PolicyBundleV03:
    profile = profile or load_profile()
    return PolicyBundleV03(
        bundle_id="exec009-bundle",
        policy_version=profile.policy_version,
        hard_rule_set_version=profile.hard_rule_set_version,
        stage_mapper_version=profile.stage_mapper_version,
        candidate_table_version=profile.candidate_table_version,
        feature_schema_version=profile.feature_schema_version,
        normalization_version=profile.normalization_version,
        weight_profile_version=profile.weight_profile_version,
        anti_oscillation_profile_version="anti-1",
        tie_break_version=profile.tie_break_version,
        fallback_profile_version=profile.fallback_profile_version,
        subject_profile_version=None,
        content_digest=profile.content_digest,
        published_at=NOW,
    )


def load_cases(name: str) -> list[dict[str, Any]]:
    return json.loads((FIXTURE_DIR / name).read_text())


def make_context(case: dict[str, Any] | None = None) -> TeachingContextV03:
    case = case or {}
    case_id = str(case.get("case_id", "base"))
    objective = ref("learning_objective", f"objective-{case_id}")
    activity = ref("learning_activity", f"activity-{case_id}")
    success_ref = ref("assessment_result", f"success-{case_id}")
    mastery = float(case.get("mastery", 0.2))
    diagnostic_confidence = float(case.get("diagnostic_confidence", 0.9))
    transfer = bool(case.get("transfer_evidence", False))
    transfer_novelty = case.get("transfer_novelty")
    history = {
        "hint_dependency_risk": 0.2,
        "consecutive_failures": int(case.get("consecutive_failures", 0)),
        "last_scaffold_control": str(case.get("last_scaffold_control", "NONE")),
    }
    source_refs = [objective, activity, ref("fixture", "source")]
    if case.get("independent_success") or case.get("assisted_success"):
        source_refs.append(success_ref)
    return TeachingContextV03(
        context_id=fixed_uuid(f"context-{case_id}"),
        decision_time=NOW,
        context_fingerprint=f"sha256:context-{case_id}",
        learning_objective_ref=objective,
        learning_activity_ref=activity,
        activity_type=available(case.get("activity_type", "lesson")),
        target_capability=available("apply"),
        mastery_confidence=available(mastery, 0.9),
        prerequisite_confidence=available(float(case.get("prerequisite_confidence", 0.9))),
        evidence_sufficiency=available(0.8),
        correctness_score=available(0.5),
        assessment_confidence=available(0.9),
        error_type=available(case.get("error_type", ErrorType.UNKNOWN.value)),
        diagnostic_confidence=available(diagnostic_confidence, diagnostic_confidence),
        needs_probe=available(bool(case.get("needs_probe", False))),
        assistance_history_summary=history,
        worked_example_exposure=available(False),
        independent_success_history=(success_ref,) if case.get("independent_success") else (),
        assisted_success_history=(success_ref,) if case.get("assisted_success") else (),
        delayed_independent_evidence=available(bool(case.get("delayed_independent", False))),
        review_context=available(True) if case.get("review_context") else missing(),
        transfer_evidence=available(True) if transfer else missing(),
        transfer_distance_novelty=(
            available(float(transfer_novelty)) if transfer_novelty is not None else missing()
        ),
        direct_answer_request=bool(case.get("direct_answer_request", False)),
        time_budget=available(600),
        source_refs=tuple(source_refs),
    )


def make_assignment(
    context: TeachingContextV03,
) -> tuple[TeachingContextV03, ExperimentAssignmentV03]:
    assignment = ExperimentAssignmentV03(
        assignment_id=fixed_uuid("assignment"),
        experiment_id="exp-policy",
        experiment_version="1",
        unit_ref="private-user",
        variant_id="control",
        assignment_probability=0.5,
        assigned_at=NOW,
    )
    assignment_ref = VersionedRef(
        entity_type="experiment_assignment",
        entity_id=str(assignment.assignment_id),
        version=assignment.assignment_schema_version,
    )
    payload = context.model_dump()
    payload["experiment_assignment_ref"] = assignment_ref
    payload["source_refs"] = (*context.source_refs, assignment_ref)
    return TeachingContextV03.model_validate(payload), assignment


def with_previous_action(
    context: TeachingContextV03, previous: TeachingActionV03
) -> TeachingContextV03:
    previous_ref = VersionedRef(
        entity_type="teaching_action",
        entity_id=str(previous.action_id),
        version=previous.action_schema_version,
    )
    retained_sources = tuple(
        source
        for source in context.source_refs
        if source.entity_type not in {"learning_objective", "learning_activity"}
    )
    payload = context.model_dump()
    payload.update(
        {
            "learning_objective_ref": previous.learning_objective_ref,
            "learning_activity_ref": previous.learning_activity_ref,
            "previous_teaching_action_ref": previous_ref,
            "source_refs": (
                previous.learning_objective_ref,
                previous.learning_activity_ref,
                *retained_sources,
                previous_ref,
            ),
        }
    )
    return TeachingContextV03.model_validate(payload)


def make_assessment_pair(
    *,
    name: str,
    assistance_state: AssistanceState,
    passed: bool = True,
    seconds_after_base: int = 60,
) -> tuple[AssessmentAttemptV03, AssessmentResultV03]:
    if assistance_state is AssistanceState.INDEPENDENT:
        scaffold = ScaffoldControl.NONE
        hint = HintSpecificity.NONE
        exposure = AnswerExposure.NONE
    elif assistance_state is AssistanceState.ASSISTED:
        scaffold = ScaffoldControl.MEDIUM
        hint = HintSpecificity.ORIENTATION
        exposure = AnswerExposure.NONE
    else:
        scaffold = ScaffoldControl.HIGH
        hint = HintSpecificity.BOTTOM_OUT
        exposure = AnswerExposure.COMPLETE
    assistance = AssistanceSnapshotV03(
        scaffold_control=scaffold,
        hint_specificity=hint,
        answer_exposure=exposure,
        assistance_state=assistance_state,
    )
    submitted = NOW + timedelta(seconds=seconds_after_base)
    attempt = AssessmentAttemptV03(
        attempt_id=fixed_uuid(f"attempt-{name}"),
        user_id=fixed_uuid("user"),
        session_id=fixed_uuid("session"),
        item_id=fixed_uuid("item"),
        item_version="1",
        assessment_type="formative",
        started_at=submitted - timedelta(seconds=30),
        first_response_at=submitted - timedelta(seconds=10),
        submitted_at=submitted,
        response_time_ms=20_000,
        raw_response="answer",
        normalized_response="answer",
        revision_count=0,
        assistance=assistance,
        idempotency_key=f"attempt-{name}",
    )
    result = AssessmentResultV03(
        result_id=fixed_uuid(f"result-{name}"),
        result_version=1,
        attempt_id=attempt.attempt_id,
        item_id=attempt.item_id,
        item_version=attempt.item_version,
        score=1.0 if passed else 0.0,
        passed=passed,
        correctness="correct" if passed else "incorrect",
        rubric_scores={},
        assessment_confidence=0.95,
        diagnosis=AssessmentDiagnosisV03(
            error_type=ErrorType.UNKNOWN,
            diagnostic_confidence=0.2,
            needs_probe=not passed,
            reason_codes=("FIXTURE_DIAGNOSIS",),
        ),
        assistance=assistance,
        evaluator_versions=("fixture-grader-1",),
        reviewer_result="accepted",
        created_at=submitted + timedelta(seconds=1),
    )
    return attempt, result

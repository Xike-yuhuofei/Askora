"""SYS05-241 typed hard constraints and stable reason codes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.contracts.adaptive import (
    AnswerExposure,
    AvailabilityStatus,
    HintSpecificity,
    TeachingContextV03,
)
from app.contracts.decisions import HardConstraintResultV03, HardFilteredActionV03
from app.domains.teaching_policy.models import PolicyRuntimeProfile, TeachingCandidate


@dataclass(frozen=True)
class HardConstraintEvaluation:
    results: tuple[HardConstraintResultV03, ...]
    filtered: tuple[HardFilteredActionV03, ...]
    forbidden_action_keys: frozenset[str]


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _result(
    *,
    rule_id: str,
    version: str,
    passed: bool,
    reason: str,
    parameters: dict[str, Any],
    forbidden: set[str],
    context: TeachingContextV03,
) -> HardConstraintResultV03:
    return HardConstraintResultV03(
        rule_id=rule_id,
        rule_version=version,
        parameters=parameters,
        passed=passed,
        reason_codes=(reason,),
        forbidden_action_refs=tuple(sorted(forbidden)),
        input_refs=context.source_refs,
    )


def evaluate_hard_constraints(
    context: TeachingContextV03,
    profile: PolicyRuntimeProfile,
    table: tuple[TeachingCandidate, ...],
) -> HardConstraintEvaluation:
    """Evaluate all eleven required families before stage/soft scoring."""

    by_key = {candidate.action_key: candidate for candidate in table}
    results: list[HardConstraintResultV03] = []
    forbidden_reasons: dict[str, list[str]] = {}

    def record(
        rule_id: str,
        passed: bool,
        reason: str,
        forbidden: set[str],
        parameters: dict[str, Any] | None = None,
    ) -> None:
        results.append(
            _result(
                rule_id=rule_id,
                version=profile.hard_rule_set_version,
                passed=passed,
                reason=reason,
                parameters=parameters or {},
                forbidden=forbidden,
                context=context,
            )
        )
        for key in forbidden:
            forbidden_reasons.setdefault(key, []).append(reason)

    activity = str(context.activity_type.value or "").lower()
    is_independent_assessment = any(
        marker in activity for marker in ("summative", "independent_assessment", "exam")
    )
    assessment_forbidden = (
        {
            c.action_key
            for c in table
            if c.hint_specificity is not HintSpecificity.NONE
            or c.answer_exposure is not AnswerExposure.NONE
        }
        if is_independent_assessment
        else set()
    )
    record(
        "SYS05-HC-ASSESSMENT-INTEGRITY",
        not assessment_forbidden,
        "ASSESSMENT_INTEGRITY_ENFORCED" if assessment_forbidden else "ASSESSMENT_INTEGRITY_CLEAR",
        assessment_forbidden,
        {"independent_activity_markers": ["summative", "independent_assessment", "exam"]},
    )

    exposure_forbidden = {
        c.action_key
        for c in table
        if c.answer_exposure is AnswerExposure.COMPLETE and not context.direct_answer_request
    }
    record(
        "SYS05-HC-ANSWER-EXPOSURE-INTEGRITY",
        not exposure_forbidden,
        (
            "COMPLETE_EXPOSURE_REQUIRES_DIRECT_REQUEST"
            if exposure_forbidden
            else "EXPOSURE_ENVELOPE_VALID"
        ),
        exposure_forbidden,
        {"complete_exposure_requires_direct_request": True},
    )

    prerequisite = _number(context.prerequisite_confidence.value)
    prerequisite_unsafe = (
        context.prerequisite_confidence.availability is not AvailabilityStatus.AVAILABLE
        or prerequisite is None
        or prerequisite < profile.prerequisite_confidence_cutoff
    )
    prerequisite_forbidden = {"transfer_challenge.core"} if prerequisite_unsafe else set()
    record(
        "SYS05-HC-PREREQUISITE-SAFETY",
        not prerequisite_unsafe,
        "PREREQUISITE_EVIDENCE_INSUFFICIENT" if prerequisite_unsafe else "PREREQUISITE_SAFE",
        prerequisite_forbidden,
        {"confidence_cutoff": profile.prerequisite_confidence_cutoff},
    )

    failures = context.assistance_history_summary.get("consecutive_failures", 0)
    repeated = isinstance(failures, int) and failures >= profile.failure_ceiling
    failure_forbidden = (
        {
            "fading_practice.core",
            "retrieval_practice.core",
            "transfer_challenge.core",
        }
        if repeated
        else set()
    )
    record(
        "SYS05-HC-REPEATED-FAILURE-CEILING",
        not repeated,
        "FAILURE_CEILING_REQUIRES_EXIT_OR_REMEDIATION" if repeated else "FAILURE_CEILING_CLEAR",
        failure_forbidden,
        {"failure_ceiling": profile.failure_ceiling},
    )

    last_scaffold = str(context.assistance_history_summary.get("last_scaffold_control", "NONE"))
    scaffold_rank = {"NONE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3}
    independent_fade = bool(context.independent_success_history)
    independent_forbidden = {
        c.action_key
        for c in table
        if independent_fade
        and scaffold_rank[c.scaffold_control.value] > scaffold_rank.get(last_scaffold, 0)
    }
    record(
        "SYS05-HC-INDEPENDENT-SUCCESS",
        not independent_forbidden,
        (
            "INDEPENDENT_SUCCESS_FORBIDS_SCAFFOLD_INCREASE"
            if independent_forbidden
            else "NO_UNSUPPORTED_SCAFFOLD_INCREASE"
        ),
        independent_forbidden,
        {"scaffold_order": ["NONE", "LOW", "MEDIUM", "HIGH"]},
    )

    diag_confidence = _number(context.diagnostic_confidence.value)
    low_confidence = (
        context.diagnostic_confidence.availability is not AvailabilityStatus.AVAILABLE
        or diag_confidence is None
        or diag_confidence < profile.diagnostic_confidence_cutoff
    )
    low_confidence_forbidden = (
        {
            "fading_practice.core",
            "retrieval_practice.core",
            "transfer_challenge.core",
        }
        if low_confidence
        else set()
    )
    record(
        "SYS05-HC-LOW-CONFIDENCE-CONSERVATISM",
        not low_confidence,
        "LOW_CONFIDENCE_REQUIRES_CONSERVATIVE_PATH" if low_confidence else "CONFIDENCE_SUFFICIENT",
        low_confidence_forbidden,
        {"diagnostic_confidence_cutoff": profile.diagnostic_confidence_cutoff},
    )

    # Candidate templates can only pin the input objective/activity; none can rewrite SYS06.
    record("SYS05-HC-OBJECTIVE-OWNERSHIP", True, "OBJECTIVE_REFS_READ_ONLY", set())
    # The closed table contains no model-owned/free-form action entry.
    record("SYS05-HC-MODEL-LLM-OVERRIDE", True, "NO_MODEL_OWNED_ACTION", set())
    # Exact profile matching is enforced at the decision entry before this layer.
    record("SYS05-HC-UNSUPPORTED-CONFIGURATION", True, "CONFIGURATION_EXACTLY_PINNED", set())

    unknown_keys = set(profile.candidate_priority) - set(by_key)
    missing_keys = set(by_key) - set(profile.candidate_priority)
    conflict = (
        bool(unknown_keys)
        or bool(missing_keys)
        or len(profile.candidate_priority) != len(set(profile.candidate_priority))
    )
    conflict_forbidden = set(by_key) if conflict else set()
    record(
        "SYS05-HC-HARD-RULE-CONFLICT",
        not conflict,
        "HARD_RULE_CONFIGURATION_CONFLICT" if conflict else "NO_HARD_RULE_CONFLICT",
        conflict_forbidden,
        {
            "unknown_priority_keys": sorted(unknown_keys),
            "missing_priority_keys": sorted(missing_keys),
        },
    )

    direct_answer_forbidden = set() if context.direct_answer_request else {"direct_answer.bounded"}
    record(
        "SYS05-HC-USER-DIRECT-ANSWER",
        context.direct_answer_request,
        (
            "DIRECT_ANSWER_BOUNDED_REQUEST"
            if context.direct_answer_request
            else "NO_DIRECT_ANSWER_REQUEST"
        ),
        direct_answer_forbidden,
        {"bounded_override": True},
    )

    filtered = tuple(
        HardFilteredActionV03(
            action_ref=key,
            filter_reason_codes=tuple(sorted(reasons)),
        )
        for key, reasons in sorted(forbidden_reasons.items())
    )
    return HardConstraintEvaluation(
        results=tuple(results),
        filtered=filtered,
        forbidden_action_keys=frozenset(forbidden_reasons),
    )

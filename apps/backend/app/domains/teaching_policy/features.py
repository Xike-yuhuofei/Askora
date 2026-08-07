"""Deterministic feature provenance and fixed-range normalization."""

from __future__ import annotations

from typing import Any

from app.contracts.adaptive import AvailabilityStatus, ErrorType, TeachingContextV03, TeachingStage
from app.contracts.decisions import DecisionFeatureV03
from app.domains.teaching_policy.models import (
    CandidateFeatureSet,
    PolicyDecisionError,
    PolicyFailureCode,
    PolicyRuntimeProfile,
    TeachingCandidate,
)


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _feature(
    *,
    name: str,
    value: float | None,
    availability: AvailabilityStatus,
    confidence: float | None,
    context: TeachingContextV03,
    profile: PolicyRuntimeProfile,
) -> DecisionFeatureV03:
    return DecisionFeatureV03(
        feature_name=name,
        value=value,
        availability=availability,
        confidence=confidence,
        feature_version=profile.feature_schema_version,
        source_refs=context.source_refs,
    )


def build_candidate_features(
    context: TeachingContextV03,
    stage: TeachingStage,
    candidate: TeachingCandidate,
    profile: PolicyRuntimeProfile,
) -> CandidateFeatureSet:
    """Build audit-friendly soft features from decision-time facts only."""

    needs_probe = context.needs_probe.value is True
    known_error = context.error_type.value not in {None, ErrorType.UNKNOWN, ErrorType.UNKNOWN.value}
    dependency = _number(context.assistance_history_summary.get("hint_dependency_risk"))
    dependency_availability = (
        AvailabilityStatus.AVAILABLE if dependency is not None else AvailabilityStatus.MISSING
    )
    family_proxy = {
        "EXPLICIT_INSTRUCTION": 0.55,
        "GUIDED_PRACTICE": 0.65,
        "FADING_PRACTICE": 0.75,
        "RETRIEVAL_PRACTICE": 0.9,
        "ERROR_REMEDIATION": 0.7,
        "TRANSFER_CHALLENGE": 1.0,
    }[candidate.strategy_family.value]
    scaffold_cost = {"NONE": 0.0, "LOW": 0.25, "MEDIUM": 0.6, "HIGH": 1.0}[
        candidate.scaffold_control.value
    ]
    time_cost = {
        "explicit_instruction.core": 0.8,
        "guided_practice.core": 0.6,
        "fading_practice.core": 0.45,
        "retrieval_practice.core": 0.3,
        "error_remediation.core": 0.7,
        "transfer_challenge.core": 1.0,
        "direct_answer.bounded": 0.2,
    }[candidate.action_key]
    values = (
        _feature(
            name="stage_fit",
            value=1.0 if stage in candidate.allowed_stages else 0.0,
            availability=AvailabilityStatus.AVAILABLE,
            confidence=1.0,
            context=context,
            profile=profile,
        ),
        _feature(
            name="diagnostic_value",
            value=(
                (
                    1.0
                    if needs_probe
                    and candidate.strategy_family.value in {"GUIDED_PRACTICE", "ERROR_REMEDIATION"}
                    else 0.0
                )
                if context.needs_probe.availability is AvailabilityStatus.AVAILABLE
                else None
            ),
            availability=context.needs_probe.availability,
            confidence=context.needs_probe.confidence,
            context=context,
            profile=profile,
        ),
        _feature(
            name="remediation_fit",
            value=(
                (
                    1.0
                    if known_error and candidate.strategy_family.value == "ERROR_REMEDIATION"
                    else 0.0
                )
                if context.error_type.availability is AvailabilityStatus.AVAILABLE
                else None
            ),
            availability=context.error_type.availability,
            confidence=context.diagnostic_confidence.confidence,
            context=context,
            profile=profile,
        ),
        _feature(
            name="review_fit",
            value=(
                (1.0 if candidate.strategy_family.value == "RETRIEVAL_PRACTICE" else 0.0)
                if context.review_context.availability is AvailabilityStatus.AVAILABLE
                else None
            ),
            availability=context.review_context.availability,
            confidence=context.review_context.confidence,
            context=context,
            profile=profile,
        ),
        _feature(
            name="learning_value_proxy",
            value=family_proxy,
            availability=AvailabilityStatus.AVAILABLE,
            confidence=None,
            context=context,
            profile=profile,
        ),
        _feature(
            name="direct_request_fit",
            value=(
                1.0
                if context.direct_answer_request and candidate.action_key == "direct_answer.bounded"
                else 0.0
            ),
            availability=AvailabilityStatus.AVAILABLE,
            confidence=1.0,
            context=context,
            profile=profile,
        ),
        _feature(
            name="hint_dependency_risk",
            value=dependency * scaffold_cost if dependency is not None else None,
            availability=dependency_availability,
            confidence=None,
            context=context,
            profile=profile,
        ),
        _feature(
            name="cognitive_load_penalty",
            value=scaffold_cost,
            availability=AvailabilityStatus.AVAILABLE,
            confidence=None,
            context=context,
            profile=profile,
        ),
        _feature(
            name="time_cost",
            value=time_cost,
            availability=AvailabilityStatus.AVAILABLE,
            confidence=None,
            context=context,
            profile=profile,
        ),
    )
    return CandidateFeatureSet(action_key=candidate.action_key, features=values)


def normalize_feature(feature: DecisionFeatureV03, profile: PolicyRuntimeProfile) -> float | None:
    """Use immutable profile bounds; never candidate-set dynamic min-max."""

    if feature.value is None:
        return None
    bounds = profile.normalization_ranges.get(feature.feature_name)
    if bounds is None:
        raise PolicyDecisionError(
            PolicyFailureCode.NORMALIZATION_FAILURE,
            f"no fixed normalization range for {feature.feature_name}",
        )
    normalized = (feature.value - bounds.minimum) / (bounds.maximum - bounds.minimum)
    return round(min(1.0, max(0.0, normalized)), 12)

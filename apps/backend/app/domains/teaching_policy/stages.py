"""Versioned deterministic TeachingStage derivation."""

from __future__ import annotations

from typing import Any

from app.contracts.adaptive import AvailabilityStatus, ErrorType, TeachingContextV03, TeachingStage
from app.domains.teaching_policy.models import PolicyRuntimeProfile


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def derive_teaching_stage(
    context: TeachingContextV03, profile: PolicyRuntimeProfile
) -> TeachingStage:
    """Map only the frozen snapshot; no SYS03 state is written or inferred later."""

    critical = (
        context.mastery_confidence,
        context.evidence_sufficiency,
        context.assessment_confidence,
    )
    if any(
        item.availability
        in {AvailabilityStatus.MISSING, AvailabilityStatus.STALE, AvailabilityStatus.LOW_CONFIDENCE}
        for item in critical
    ):
        return TeachingStage.DIAGNOSE

    needs_probe = context.needs_probe.value is True
    diagnostic_confidence = _number(context.diagnostic_confidence.value)
    if needs_probe or diagnostic_confidence is None:
        return TeachingStage.DIAGNOSE
    if diagnostic_confidence < profile.diagnostic_confidence_cutoff:
        return TeachingStage.DIAGNOSE

    error = context.error_type.value
    if error not in {None, ErrorType.UNKNOWN.value, ErrorType.UNKNOWN}:
        return TeachingStage.ERROR_REMEDIATION

    if context.transfer_evidence.availability is AvailabilityStatus.AVAILABLE:
        novelty = _number(context.transfer_distance_novelty.value)
        if novelty is not None and novelty >= profile.transfer_novelty_cutoff:
            return TeachingStage.TRANSFER_CHALLENGE

    if context.review_context.availability is AvailabilityStatus.AVAILABLE:
        delayed = context.delayed_independent_evidence.value is True
        return TeachingStage.DELAYED_RETRIEVAL if delayed else TeachingStage.RETRIEVAL_PRACTICE

    mastery = _number(context.mastery_confidence.value)
    if mastery is not None and mastery >= profile.mastery_threshold:
        return TeachingStage.RETRIEVAL_PRACTICE
    if context.independent_success_history:
        return TeachingStage.FADING_PRACTICE
    if context.assisted_success_history:
        return TeachingStage.GUIDED_PRACTICE
    return TeachingStage.EXPLICIT_INSTRUCTION

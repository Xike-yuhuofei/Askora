"""Typed material-evidence classification for sequential policy decisions."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import Field

from app.contracts.adaptive import VersionedRef
from app.contracts.base import ContractModel
from app.domains.teaching_policy.models import PolicyRuntimeProfile


class EvidenceSignalKind(StrEnum):
    ASSESSMENT_RESULT = "ASSESSMENT_RESULT"
    INDEPENDENT_ATTEMPT = "INDEPENDENT_ATTEMPT"
    DIAGNOSTIC_PROBE = "DIAGNOSTIC_PROBE"
    LEARNER_STATE_UPDATE = "LEARNER_STATE_UPDATE"
    EXPLICIT_USER_REQUEST = "EXPLICIT_USER_REQUEST"
    PREREQUISITE_EVIDENCE = "PREREQUISITE_EVIDENCE"
    ASSISTANCE_EVENT = "ASSISTANCE_EVENT"
    REVIEW_DELAY_TRANSITION = "REVIEW_DELAY_TRANSITION"
    CHAT_TURN = "CHAT_TURN"
    WORDING_VARIATION = "WORDING_VARIATION"
    RERENDER = "RERENDER"
    SAME_CONTEXT_REEVALUATION = "SAME_CONTEXT_REEVALUATION"
    WALL_CLOCK_DRIFT = "WALL_CLOCK_DRIFT"


MATERIAL_KINDS = frozenset(
    {
        EvidenceSignalKind.ASSESSMENT_RESULT,
        EvidenceSignalKind.INDEPENDENT_ATTEMPT,
        EvidenceSignalKind.DIAGNOSTIC_PROBE,
        EvidenceSignalKind.LEARNER_STATE_UPDATE,
        EvidenceSignalKind.EXPLICIT_USER_REQUEST,
        EvidenceSignalKind.PREREQUISITE_EVIDENCE,
        EvidenceSignalKind.ASSISTANCE_EVENT,
    }
)


class EvidenceSignal(ContractModel):
    signal_id: str = Field(min_length=1)
    kind: EvidenceSignalKind
    evidence_ref: VersionedRef | None = None
    occurred_at: datetime
    attributes: dict[str, Any] = Field(default_factory=dict)


class ClassifiedEvidence(ContractModel):
    signal_id: str
    kind: EvidenceSignalKind
    material: bool
    reason_code: str
    evidence_ref: VersionedRef | None = None


def classify_material_evidence(
    signals: tuple[EvidenceSignal, ...],
    profile: PolicyRuntimeProfile,
    now: datetime,
) -> tuple[ClassifiedEvidence, ...]:
    classified: list[ClassifiedEvidence] = []
    for signal in signals:
        if signal.kind in MATERIAL_KINDS:
            material = signal.evidence_ref is not None
            reason = "MATERIAL_EXACT_EVIDENCE" if material else "NON_MATERIAL_MISSING_EXACT_REF"
        elif signal.kind is EvidenceSignalKind.REVIEW_DELAY_TRANSITION:
            started_at = signal.attributes.get("delay_started_at")
            if isinstance(started_at, str):
                started_at = datetime.fromisoformat(started_at)
            elapsed = (
                (now - started_at).total_seconds()
                if isinstance(started_at, datetime)
                and started_at.utcoffset() is not None
                and now.utcoffset() is not None
                else -1
            )
            material = (
                signal.evidence_ref is not None and elapsed >= profile.meaningful_delay_seconds
            )
            reason = (
                "MATERIAL_MEANINGFUL_REVIEW_DELAY"
                if material
                else "NON_MATERIAL_DELAY_WINDOW_NOT_MET"
            )
        else:
            material = False
            reason = f"NON_MATERIAL_{signal.kind.value}"
        classified.append(
            ClassifiedEvidence(
                signal_id=signal.signal_id,
                kind=signal.kind,
                material=material,
                reason_code=reason,
                evidence_ref=signal.evidence_ref,
            )
        )
    return tuple(classified)


def distinct_material_opportunities(classified: tuple[ClassifiedEvidence, ...]) -> int:
    keys = {
        (
            item.kind.value,
            item.evidence_ref.entity_type,
            item.evidence_ref.entity_id,
            str(item.evidence_ref.version),
        )
        for item in classified
        if item.material and item.evidence_ref is not None
    }
    return len(keys)

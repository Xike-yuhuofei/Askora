"""SYS03 LearnerState aggregate projection over exact MasteryEstimate versions."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from uuid import NAMESPACE_URL, UUID, uuid5

from app.contracts.adaptive import VersionedRef
from app.contracts.learning import LearnerStateV1, MasteryEstimate


class LearnerStateProjector:
    """Pure, replayable aggregate projection; it does not estimate mastery."""

    ALGORITHM_BUNDLE_VERSION = "learner-state-aggregate-v1"
    UNCERTAINTY_PROFILE_VERSION = "diagnostic-current-evidence-v1"
    MIN_CURRENT_CONFIDENCE = 0.25

    def project(
        self,
        *,
        user_id: UUID,
        estimates: Sequence[MasteryEstimate],
        version: int,
        created_from_event_sequence: int,
        created_at: datetime,
    ) -> LearnerStateV1:
        ordered = tuple(
            sorted(
                (item for item in estimates if item.user_id == user_id),
                key=lambda item: (str(item.knowledge_unit_id), item.version),
            )
        )
        uncertain = tuple(
            item.knowledge_unit_id
            for item in ordered
            if item.competence_probability is None or item.confidence < self.MIN_CURRENT_CONFIDENCE
        )
        return LearnerStateV1(
            learner_state_id=uuid5(NAMESPACE_URL, f"askora:learner-state:{user_id}"),
            version=version,
            user_id=user_id,
            mastery_estimate_ids=tuple(item.estimate_id for item in ordered),
            mastery_estimate_refs=tuple(
                VersionedRef(
                    entity_type="MasteryEstimate",
                    entity_id=str(item.estimate_id),
                    version=item.version,
                )
                for item in ordered
            ),
            learner_progress_summary={
                "knowledge_unit_count": len(ordered),
                "accepted_evidence_count": sum(item.evidence_count for item in ordered),
            },
            uncertainty_summary={
                "profile_version": self.UNCERTAINTY_PROFILE_VERSION,
                "uncertain_knowledge_unit_ids": [str(item) for item in uncertain],
                "minimum_current_confidence": self.MIN_CURRENT_CONFIDENCE,
            },
            created_from_event_sequence=created_from_event_sequence,
            algorithm_bundle_version=self.ALGORITHM_BUNDLE_VERSION,
            created_at=created_at,
        )

"""SYS03 application service：接纳 evidence 并写 canonical MasteryEstimate。"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.assessment import AssessmentAttempt
from app.contracts.learning import AssessmentResult, MasteryEstimate
from app.domains.learner_model import EvidenceEligibility, WeightedBKTProjector
from app.infrastructure.learning_records import LearnerModelRepository
from app.infrastructure.outbox import OutboxProducer


class CanonicalLearnerProjectorService:
    def __init__(self, session: AsyncSession) -> None:
        self._records = LearnerModelRepository(session)
        self._outbox = OutboxProducer(session)
        self._eligibility = EvidenceEligibility()
        self._projector = WeightedBKTProjector()

    async def project_assessment(
        self,
        *,
        result: AssessmentResult,
        attempt: AssessmentAttempt,
        knowledge_unit_id: UUID,
        source_event_ids: list[UUID],
        dimension: Literal["recall", "routine_application", "transfer", "explanation"] = (
            "routine_application"
        ),
        novelty: Literal["repeated", "near_variant", "far_variant"] = "near_variant",
        delay_seconds: int = 0,
        item_difficulty: float | None = None,
    ) -> MasteryEstimate | None:
        decision = self._eligibility.decide(
            result=result,
            attempt=attempt,
            knowledge_unit_id=knowledge_unit_id,
            dimension=dimension,
            novelty=novelty,
            delay_seconds=delay_seconds,
            item_difficulty=item_difficulty,
            source_event_ids=source_event_ids,
        )
        if not decision.accepted or decision.evidence is None:
            await self._records.save_rejection(
                result=result,
                attempt=attempt,
                knowledge_unit_id=knowledge_unit_id,
                reason_codes=decision.reason_codes,
            )
            await self._outbox.enqueue(
                task_type="learner.evidence.rejected",
                schema_version="1.0",
                payload={
                    "attempt_id": str(attempt.attempt_id),
                    "result_id": str(result.result_id),
                    "reason_codes": list(decision.reason_codes),
                },
                idempotency_key=f"evidence-rejected:{result.result_id}",
            )
            return None
        evidence = await self._records.save_evidence(decision.evidence)
        evidence_stream = await self._records.list_evidence(
            user_id=evidence.user_id,
            knowledge_unit_id=evidence.knowledge_unit_id,
        )
        version = await self._records.next_version(
            user_id=evidence.user_id,
            knowledge_unit_id=evidence.knowledge_unit_id,
        )
        estimate = self._projector.project(
            user_id=evidence.user_id,
            knowledge_unit_id=evidence.knowledge_unit_id,
            evidence=evidence_stream,
            version=version,
        )
        estimate = await self._records.save_mastery(estimate)
        await self._outbox.enqueue(
            task_type="learner.mastery.updated",
            schema_version="1.0",
            payload=estimate.model_dump(mode="json"),
            idempotency_key=f"mastery-updated:{estimate.estimate_id}",
        )
        return estimate

    async def recompute_after_invalidation(
        self, *, user_id: UUID, knowledge_unit_id: UUID, evidence_id: UUID
    ) -> MasteryEstimate:
        await self._records.invalidate_evidence(evidence_id)
        evidence_stream = await self._records.list_evidence(
            user_id=user_id,
            knowledge_unit_id=knowledge_unit_id,
        )
        version = await self._records.next_version(
            user_id=user_id,
            knowledge_unit_id=knowledge_unit_id,
        )
        estimate = self._projector.project(
            user_id=user_id,
            knowledge_unit_id=knowledge_unit_id,
            evidence=evidence_stream,
            version=version,
        )
        return await self._records.save_mastery(estimate)

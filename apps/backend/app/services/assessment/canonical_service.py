"""SYS04 application service：Attempt/Result state 与 outbox 同 transaction。"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.assessment import AssessmentItemV1, AssistanceSnapshot
from app.contracts.learning import AssessmentResult
from app.domains.assessment import AssessmentScoringService
from app.infrastructure.learning_records import AssessmentRecordRepository
from app.infrastructure.outbox import OutboxProducer


class CanonicalAssessmentService:
    def __init__(self, session: AsyncSession) -> None:
        self._records = AssessmentRecordRepository(session)
        self._outbox = OutboxProducer(session)
        self._scorer = AssessmentScoringService()

    async def score_submission(
        self,
        *,
        item: AssessmentItemV1,
        user_id: UUID,
        response: Any,
        assistance: AssistanceSnapshot,
        idempotency_key: str,
        correlation_id: str = "",
    ) -> AssessmentResult:
        attempt = self._scorer.submit(
            item=item,
            user_id=user_id,
            response=response,
            assistance=assistance,
            idempotency_key=idempotency_key,
        )
        attempt = await self._records.save_attempt(attempt)
        result = self._scorer.score(item=item, attempt=attempt)
        result = await self._records.save_result(result)
        await self._outbox.enqueue(
            task_type="assessment.result.project",
            schema_version="1.0",
            payload={
                "attempt": attempt.model_dump(mode="json"),
                "result": result.model_dump(mode="json"),
                "knowledge_unit_id": str(item.knowledge_unit_id),
                "item_difficulty": item.difficulty,
                "correlation_id": correlation_id,
            },
            idempotency_key=f"assessment-result-project:{result.result_id}",
        )
        return result

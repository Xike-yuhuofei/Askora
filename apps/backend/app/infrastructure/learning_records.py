"""SYS04 Attempt/Result 与 SYS03 Evidence/Mastery 的 durable repositories。"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.assessment import AssessmentAttempt
from app.contracts.learning import AssessmentResult, LearnerEvidence, MasteryEstimate
from app.models.assessment import (
    CanonicalAssessmentAttemptRecord,
    CanonicalAssessmentResultRecord,
    LearnerEvidenceRecord,
    MasteryEstimateRecord,
)
from app.models.dialog import DialogSession


class AssessmentRecordRepository:
    """由调用方 transaction 管理；写 state 后可在同一 transaction enqueue outbox。"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_attempt(self, attempt: AssessmentAttempt) -> AssessmentAttempt:
        existing = await self._session.scalar(
            select(CanonicalAssessmentAttemptRecord).where(
                CanonicalAssessmentAttemptRecord.idempotency_key == attempt.idempotency_key
            )
        )
        if existing is not None:
            return AssessmentAttempt.model_validate(existing.payload)
        self._session.add(
            CanonicalAssessmentAttemptRecord(
                id=str(attempt.attempt_id),
                idempotency_key=attempt.idempotency_key,
                user_id=str(attempt.user_id),
                item_id=str(attempt.item_id),
                item_version=attempt.item_version,
                payload=attempt.model_dump(mode="json"),
            )
        )
        await self._session.flush()
        return attempt

    async def save_result(self, result: AssessmentResult) -> AssessmentResult:
        existing = await self._session.get(CanonicalAssessmentResultRecord, str(result.result_id))
        if existing is not None:
            return AssessmentResult.model_validate(existing.payload)
        self._session.add(
            CanonicalAssessmentResultRecord(
                id=str(result.result_id),
                attempt_id=str(result.attempt_id),
                result_version=result.result_version,
                supersedes_result_id=(
                    str(result.supersedes_result_id) if result.supersedes_result_id else None
                ),
                payload=result.model_dump(mode="json"),
            )
        )
        await self._session.flush()
        return result


class LearnerModelRepository:
    """canonical learner truth repository；唯一持久化 MasteryEstimate 的 port。"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_evidence(self, evidence: LearnerEvidence) -> LearnerEvidence:
        if evidence.result_id is None:
            raise ValueError("ASSESSMENT_RESULT_ID_REQUIRED")
        existing = await self._session.scalar(
            select(LearnerEvidenceRecord).where(
                LearnerEvidenceRecord.source_result_id == str(evidence.result_id)
            )
        )
        if existing is not None:
            if existing.status != "accepted":
                raise ValueError("ASSESSMENT_RESULT_ALREADY_REJECTED")
            return LearnerEvidence.model_validate(existing.payload)
        self._session.add(
            LearnerEvidenceRecord(
                id=str(evidence.evidence_id),
                source_result_id=str(evidence.result_id),
                user_id=str(evidence.user_id),
                knowledge_unit_id=str(evidence.knowledge_unit_id),
                status="accepted",
                reason_codes=evidence.eligibility_reason_codes,
                payload=evidence.model_dump(mode="json"),
            )
        )
        await self._session.flush()
        return evidence

    async def save_rejection(
        self,
        *,
        result: AssessmentResult,
        attempt: AssessmentAttempt,
        knowledge_unit_id: UUID,
        reason_codes: tuple[str, ...],
    ) -> None:
        existing = await self._session.scalar(
            select(LearnerEvidenceRecord).where(
                LearnerEvidenceRecord.source_result_id == str(result.result_id)
            )
        )
        if existing is not None:
            return
        rejection_id = uuid5(NAMESPACE_URL, f"askora:evidence-rejection:{result.result_id}")
        self._session.add(
            LearnerEvidenceRecord(
                id=str(rejection_id),
                source_result_id=str(result.result_id),
                user_id=str(attempt.user_id),
                knowledge_unit_id=str(knowledge_unit_id),
                status="rejected",
                reason_codes=list(reason_codes),
                payload={
                    "decision_id": str(rejection_id),
                    "attempt_id": str(attempt.attempt_id),
                    "result_id": str(result.result_id),
                    "reason_codes": list(reason_codes),
                },
            )
        )
        await self._session.flush()

    async def list_evidence(
        self, *, user_id: UUID, knowledge_unit_id: UUID
    ) -> list[LearnerEvidence]:
        records = (
            await self._session.scalars(
                select(LearnerEvidenceRecord)
                .where(
                    LearnerEvidenceRecord.user_id == str(user_id),
                    LearnerEvidenceRecord.knowledge_unit_id == str(knowledge_unit_id),
                    LearnerEvidenceRecord.status == "accepted",
                    LearnerEvidenceRecord.invalidated_at.is_(None),
                )
                .order_by(LearnerEvidenceRecord.created_at, LearnerEvidenceRecord.id)
            )
        ).all()
        return [LearnerEvidence.model_validate(record.payload) for record in records]

    async def invalidate_evidence(self, evidence_id: UUID) -> None:
        record = await self._session.get(LearnerEvidenceRecord, str(evidence_id))
        if record is None:
            raise KeyError(f"evidence not found: {evidence_id}")
        record.invalidated_at = datetime.now(timezone.utc)
        await self._session.flush()

    async def next_version(self, *, user_id: UUID, knowledge_unit_id: UUID) -> int:
        latest = await self._session.scalar(
            select(func.max(MasteryEstimateRecord.version)).where(
                MasteryEstimateRecord.user_id == str(user_id),
                MasteryEstimateRecord.knowledge_unit_id == str(knowledge_unit_id),
            )
        )
        return int(latest or 0) + 1

    async def save_mastery(self, estimate: MasteryEstimate) -> MasteryEstimate:
        existing = await self._session.get(MasteryEstimateRecord, str(estimate.estimate_id))
        if existing is not None:
            return MasteryEstimate.model_validate(existing.payload)
        self._session.add(
            MasteryEstimateRecord(
                id=str(estimate.estimate_id),
                user_id=str(estimate.user_id),
                knowledge_unit_id=str(estimate.knowledge_unit_id),
                version=estimate.version,
                payload=estimate.model_dump(mode="json"),
            )
        )
        await self._session.flush()
        return estimate

    async def latest_mastery(
        self, *, user_id: UUID, knowledge_unit_id: UUID
    ) -> MasteryEstimate | None:
        record = await self._session.scalar(
            select(MasteryEstimateRecord)
            .where(
                MasteryEstimateRecord.user_id == str(user_id),
                MasteryEstimateRecord.knowledge_unit_id == str(knowledge_unit_id),
            )
            .order_by(MasteryEstimateRecord.version.desc())
            .limit(1)
        )
        return MasteryEstimate.model_validate(record.payload) if record else None

    async def sync_legacy_dialog_projection(
        self, *, dialog_session_id: UUID, estimate: MasteryEstimate
    ) -> None:
        """迁移期只读投影；删除条件：前端改读 SYS03 learner-state query。"""
        dialog = await self._session.get(DialogSession, str(dialog_session_id))
        if dialog is None:
            raise KeyError(f"dialog session not found: {dialog_session_id}")
        dialog.mastery_estimate = estimate.competence_probability or 0.0
        await self._session.flush()

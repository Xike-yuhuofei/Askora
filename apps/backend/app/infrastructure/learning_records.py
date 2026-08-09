"""SYS04 Attempt/Result 与 SYS03 Evidence/Mastery 的 durable repositories。"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.assessment import AssessmentAttempt
from app.contracts.learning import (
    AssessmentResult,
    LearnerEvidence,
    LearnerStateV1,
    MasteryEstimate,
)
from app.models.assessment import (
    CanonicalAssessmentAttemptRecord,
    CanonicalAssessmentResultRecord,
    LearnerEvidenceRecord,
    LearnerStateRecord,
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

    async def list_latest_mastery(
        self, *, user_id: UUID, knowledge_unit_ids: tuple[UUID, ...]
    ) -> list[MasteryEstimate]:
        if not knowledge_unit_ids:
            return []
        records = (
            await self._session.scalars(
                select(MasteryEstimateRecord)
                .where(
                    MasteryEstimateRecord.user_id == str(user_id),
                    MasteryEstimateRecord.knowledge_unit_id.in_(
                        [str(item) for item in knowledge_unit_ids]
                    ),
                )
                .order_by(
                    MasteryEstimateRecord.knowledge_unit_id,
                    MasteryEstimateRecord.version.desc(),
                )
            )
        ).all()
        latest: dict[str, MasteryEstimateRecord] = {}
        for record in records:
            latest.setdefault(record.knowledge_unit_id, record)
        return [MasteryEstimate.model_validate(item.payload) for item in latest.values()]

    async def list_all_latest_mastery(self, *, user_id: UUID) -> list[MasteryEstimate]:
        records = (
            await self._session.scalars(
                select(MasteryEstimateRecord)
                .where(MasteryEstimateRecord.user_id == str(user_id))
                .order_by(
                    MasteryEstimateRecord.knowledge_unit_id,
                    MasteryEstimateRecord.version.desc(),
                )
            )
        ).all()
        latest: dict[str, MasteryEstimateRecord] = {}
        for record in records:
            latest.setdefault(record.knowledge_unit_id, record)
        return [MasteryEstimate.model_validate(item.payload) for item in latest.values()]

    async def mastery_for_source_result(
        self, *, result_id: UUID, user_id: UUID, knowledge_unit_id: UUID
    ) -> MasteryEstimate | None:
        evidence = await self._session.scalar(
            select(LearnerEvidenceRecord).where(
                LearnerEvidenceRecord.source_result_id == str(result_id),
                LearnerEvidenceRecord.user_id == str(user_id),
                LearnerEvidenceRecord.knowledge_unit_id == str(knowledge_unit_id),
                LearnerEvidenceRecord.status == "accepted",
            )
        )
        if evidence is None:
            return None
        latest = await self.latest_mastery(
            user_id=user_id,
            knowledge_unit_id=knowledge_unit_id,
        )
        if latest is None or UUID(evidence.id) not in latest.source_evidence_ids:
            return None
        return latest

    async def next_learner_state_version(self, user_id: UUID) -> int:
        latest = await self._session.scalar(
            select(func.max(LearnerStateRecord.version)).where(
                LearnerStateRecord.user_id == str(user_id)
            )
        )
        return int(latest or 0) + 1

    async def save_learner_state(self, state: LearnerStateV1) -> LearnerStateV1:
        record_id = f"{state.learner_state_id}:{state.version}"
        existing = await self._session.get(LearnerStateRecord, record_id)
        if existing is not None:
            return LearnerStateV1.model_validate(existing.payload)
        self._session.add(
            LearnerStateRecord(
                id=record_id,
                learner_state_id=str(state.learner_state_id),
                user_id=str(state.user_id),
                version=state.version,
                payload=state.model_dump(mode="json"),
            )
        )
        await self._session.flush()
        return state

    async def latest_learner_state(self, user_id: UUID) -> LearnerStateV1 | None:
        record = await self._session.scalar(
            select(LearnerStateRecord)
            .where(LearnerStateRecord.user_id == str(user_id))
            .order_by(LearnerStateRecord.version.desc())
            .limit(1)
        )
        return LearnerStateV1.model_validate(record.payload) if record else None

    async def get_learner_state(
        self, *, learner_state_id: UUID, version: int, user_id: UUID
    ) -> LearnerStateV1 | None:
        record = await self._session.scalar(
            select(LearnerStateRecord).where(
                LearnerStateRecord.learner_state_id == str(learner_state_id),
                LearnerStateRecord.version == version,
                LearnerStateRecord.user_id == str(user_id),
            )
        )
        return LearnerStateV1.model_validate(record.payload) if record else None

    async def sync_legacy_dialog_projection(
        self, *, dialog_session_id: UUID, estimate: MasteryEstimate
    ) -> None:
        """迁移期只读投影；删除条件：前端改读 SYS03 learner-state query。"""
        dialog = await self._session.get(DialogSession, str(dialog_session_id))
        if dialog is None:
            raise KeyError(f"dialog session not found: {dialog_session_id}")
        dialog.mastery_estimate = estimate.competence_probability or 0.0
        await self._session.flush()

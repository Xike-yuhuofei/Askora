"""Read-only SYS04 AssessmentItem selection for deterministic diagnostics."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.adaptive import VersionedRef
from app.contracts.assessment import AssessmentItemV1
from app.contracts.book_learning import LearnerVisibleDiagnosticItemV1
from app.models.assessment import AssessmentItem


class DiagnosticAssessmentItemQuery:
    """Selects only active deterministic items; answer keys remain grader-only."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def select_active(
        self, *, knowledge_unit_id: UUID, excluded_item_ids: tuple[UUID, ...] = ()
    ) -> AssessmentItemV1 | None:
        query = select(AssessmentItem).where(
            AssessmentItem.knowledge_point_id == str(knowledge_unit_id),
            AssessmentItem.is_active.is_(True),
            AssessmentItem.item_type.in_(["multiple_choice", "fill_blank"]),
        )
        if excluded_item_ids:
            query = query.where(AssessmentItem.id.not_in([str(item) for item in excluded_item_ids]))
        record = await self._session.scalar(
            query.order_by(AssessmentItem.difficulty.desc(), AssessmentItem.id).limit(1)
        )
        return self._to_contract(record) if record is not None else None

    async def get_exact(self, *, item_id: UUID, version: str) -> AssessmentItemV1 | None:
        record = await self._session.scalar(
            select(AssessmentItem).where(
                AssessmentItem.id == str(item_id),
                AssessmentItem.version == version,
            )
        )
        return self._to_contract(record) if record is not None else None

    async def get_learner_visible(
        self,
        *,
        item_id: UUID,
        version: str,
        need_id: UUID,
        need_version: int,
    ) -> LearnerVisibleDiagnosticItemV1 | None:
        """UI02B1-030/031 exposes prompt/options without answer or grader metadata."""

        item = await self.get_exact(item_id=item_id, version=version)
        if item is None or item.status != "active":
            return None
        return LearnerVisibleDiagnosticItemV1(
            item_ref=VersionedRef(
                entity_type="AssessmentItem",
                entity_id=str(item.item_id),
                version=item.version,
            ),
            need_id=need_id,
            need_version=need_version,
            item_type=item.item_type,
            prompt=item.prompt,
            options=tuple(item.options),
        )

    @staticmethod
    def _to_contract(record: AssessmentItem) -> AssessmentItemV1:
        return AssessmentItemV1(
            item_id=UUID(record.id),
            version=record.version,
            knowledge_unit_id=UUID(record.knowledge_point_id),
            item_type="multiple_choice" if record.item_type == "multiple_choice" else "exact",
            prompt=record.question_text,
            options=[str(item) for item in record.options],
            answer_key=record.correct_answer,
            difficulty=max(0.0, min(1.0, record.difficulty / 5.0)),
            status="active" if record.is_active else "retired",
        )

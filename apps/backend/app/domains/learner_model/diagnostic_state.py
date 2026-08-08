"""SYS03 owner service used by prerequisite diagnostic application workflows."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Protocol
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.assessment import AssessmentAttempt
from app.contracts.learning import AssessmentResult, LearnerStateV1, MasteryEstimate
from app.domains.learner_model.state_projector import LearnerStateProjector
from app.infrastructure.learning_records import LearnerModelRepository


class CanonicalMasteryProjectionPort(Protocol):
    async def project_assessment(
        self,
        *,
        result: AssessmentResult,
        attempt: AssessmentAttempt,
        knowledge_unit_id: UUID,
        source_event_ids: list[UUID],
        dimension: Literal["recall", "routine_application", "transfer", "explanation"],
        novelty: Literal["repeated", "near_variant", "far_variant"],
        delay_seconds: int,
        item_difficulty: float | None,
        correlation_id: str,
    ) -> MasteryEstimate | None: ...


class DiagnosticLearnerStateService:
    """Only SYS03 code persists diagnostic evidence projections and LearnerState."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        mastery_projector: CanonicalMasteryProjectionPort,
    ) -> None:
        self._repo = LearnerModelRepository(session)
        self._mastery_projector = mastery_projector
        self._state_projector = LearnerStateProjector()

    async def current_state(
        self,
        *,
        user_id: UUID,
        knowledge_unit_ids: tuple[UUID, ...],
        created_at: datetime,
    ) -> tuple[LearnerStateV1, list[MasteryEstimate]]:
        all_estimates = await self._repo.list_all_latest_mastery(user_id=user_id)
        state = await self._ensure_state(
            user_id=user_id, estimates=all_estimates, created_at=created_at
        )
        scope = set(knowledge_unit_ids)
        estimates = [item for item in all_estimates if item.knowledge_unit_id in scope]
        return state, estimates

    async def project_assessment(
        self,
        *,
        result: AssessmentResult,
        attempt: AssessmentAttempt,
        knowledge_unit_id: UUID,
        source_event_id: UUID,
        item_difficulty: float | None,
        correlation_id: UUID,
        knowledge_unit_ids: tuple[UUID, ...],
        created_at: datetime,
    ) -> tuple[MasteryEstimate | None, LearnerStateV1, list[MasteryEstimate]]:
        estimate = await self._repo.mastery_for_source_result(
            result_id=result.result_id,
            user_id=attempt.user_id,
            knowledge_unit_id=knowledge_unit_id,
        )
        if estimate is None:
            estimate = await self._mastery_projector.project_assessment(
                result=result,
                attempt=attempt,
                knowledge_unit_id=knowledge_unit_id,
                source_event_ids=[source_event_id],
                dimension="routine_application",
                novelty="far_variant",
                delay_seconds=0,
                item_difficulty=item_difficulty,
                correlation_id=str(correlation_id),
            )
        state, estimates = await self.current_state(
            user_id=attempt.user_id,
            knowledge_unit_ids=knowledge_unit_ids,
            created_at=created_at,
        )
        return estimate, state, estimates

    async def get_state(self, *, user_id: UUID, version: int) -> LearnerStateV1 | None:
        return await self._repo.get_learner_state(
            learner_state_id=uuid5(NAMESPACE_URL, f"askora:learner-state:{user_id}"),
            version=version,
            user_id=user_id,
        )

    async def _ensure_state(
        self,
        *,
        user_id: UUID,
        estimates: list[MasteryEstimate],
        created_at: datetime,
    ) -> LearnerStateV1:
        latest = await self._repo.latest_learner_state(user_id)
        estimate_ids = tuple(
            item.estimate_id
            for item in sorted(estimates, key=lambda item: str(item.knowledge_unit_id))
        )
        if latest is not None and latest.mastery_estimate_ids == estimate_ids:
            return latest
        version = await self._repo.next_learner_state_version(user_id)
        state = self._state_projector.project(
            user_id=user_id,
            estimates=estimates,
            version=version,
            created_from_event_sequence=sum(item.evidence_count for item in estimates),
            created_at=created_at,
        )
        return await self._repo.save_learner_state(state)

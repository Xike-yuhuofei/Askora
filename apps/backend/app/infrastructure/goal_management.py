"""Persistence adapter for SYS06 P1-01 goal management streams."""

from __future__ import annotations

from typing import TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.goal_management import (
    FocusedLearningGoalStateV1,
    GoalChangePreviewV1,
    LearningGoalDefinitionV2,
    LearningGoalDraftV1,
    LearningGoalStateV1,
    LearningPlanStateV1,
)
from app.models.goal_management import (
    FocusedGoalStateRecord,
    GoalChangePreviewRecord,
    GoalDefinitionRecord,
    GoalDraftRecord,
    GoalManagementCommandReceiptRecord,
    GoalPlanStateRecord,
    GoalStateRecord,
)

T = TypeVar("T", bound=BaseModel)


class GoalManagementRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def replay(
        self,
        *,
        user_id: UUID,
        idempotency_key: str,
        payload_digest: str,
        response_model: type[T],
    ) -> T | None:
        record = await self.session.scalar(
            select(GoalManagementCommandReceiptRecord).where(
                GoalManagementCommandReceiptRecord.user_id == str(user_id),
                GoalManagementCommandReceiptRecord.idempotency_key == idempotency_key,
            )
        )
        if record is None:
            return None
        if record.payload_digest != payload_digest:
            raise ValueError("GOAL_IDEMPOTENCY_CONFLICT")
        return response_model.model_validate(record.response_payload)

    async def receipt(
        self,
        *,
        user_id: UUID,
        command_type: str,
        idempotency_key: str,
        payload_digest: str,
        response: BaseModel,
    ) -> None:
        self.session.add(
            GoalManagementCommandReceiptRecord(
                receipt_id=str(uuid4()),
                user_id=str(user_id),
                command_type=command_type,
                idempotency_key=idempotency_key,
                payload_digest=payload_digest,
                response_type=type(response).__name__,
                response_payload=response.model_dump(mode="json"),
            )
        )
        await self.session.flush()

    async def latest_draft(self, *, draft_id: UUID, user_id: UUID) -> LearningGoalDraftV1 | None:
        record = await self.session.scalar(
            select(GoalDraftRecord)
            .where(
                GoalDraftRecord.draft_id == str(draft_id),
                GoalDraftRecord.user_id == str(user_id),
            )
            .order_by(GoalDraftRecord.draft_version.desc())
            .limit(1)
        )
        return LearningGoalDraftV1.model_validate(record.payload) if record else None

    async def save_draft(self, draft: LearningGoalDraftV1) -> None:
        self.session.add(
            GoalDraftRecord(
                id=f"{draft.draft_id}:{draft.draft_version}",
                draft_id=str(draft.draft_id),
                user_id=str(draft.user_id),
                goal_id=str(draft.goal_id),
                draft_version=draft.draft_version,
                status=draft.status,
                payload=draft.model_dump(mode="json"),
            )
        )
        await self.session.flush()

    async def latest_pending_draft_for_goal(
        self, *, goal_id: UUID, user_id: UUID
    ) -> LearningGoalDraftV1 | None:
        record = await self.session.scalar(
            select(GoalDraftRecord)
            .where(
                GoalDraftRecord.goal_id == str(goal_id),
                GoalDraftRecord.user_id == str(user_id),
                GoalDraftRecord.status == "approved_pending_boundary",
            )
            .order_by(GoalDraftRecord.draft_version.desc())
            .limit(1)
        )
        return LearningGoalDraftV1.model_validate(record.payload) if record else None

    async def get_preview(
        self, *, preview_id: UUID, version: int, user_id: UUID
    ) -> GoalChangePreviewV1 | None:
        record = await self.session.scalar(
            select(GoalChangePreviewRecord).where(
                GoalChangePreviewRecord.preview_id == str(preview_id),
                GoalChangePreviewRecord.preview_version == version,
                GoalChangePreviewRecord.user_id == str(user_id),
            )
        )
        return GoalChangePreviewV1.model_validate(record.payload) if record else None

    async def save_preview(self, preview: GoalChangePreviewV1, *, user_id: UUID) -> None:
        self.session.add(
            GoalChangePreviewRecord(
                id=f"{preview.preview_id}:{preview.preview_version}",
                preview_id=str(preview.preview_id),
                preview_version=preview.preview_version,
                draft_id=str(preview.draft_id),
                user_id=str(user_id),
                payload=preview.model_dump(mode="json"),
            )
        )
        await self.session.flush()

    async def next_definition_version(self, goal_id: UUID) -> int:
        value = await self.session.scalar(
            select(func.max(GoalDefinitionRecord.definition_version)).where(
                GoalDefinitionRecord.goal_id == str(goal_id)
            )
        )
        return int(value or 0) + 1

    async def latest_definition(
        self, *, goal_id: UUID, user_id: UUID
    ) -> LearningGoalDefinitionV2 | None:
        record = await self.session.scalar(
            select(GoalDefinitionRecord)
            .where(
                GoalDefinitionRecord.goal_id == str(goal_id),
                GoalDefinitionRecord.user_id == str(user_id),
            )
            .order_by(GoalDefinitionRecord.definition_version.desc())
            .limit(1)
        )
        return LearningGoalDefinitionV2.model_validate(record.payload) if record else None

    async def save_definition(self, definition: LearningGoalDefinitionV2) -> None:
        self.session.add(
            GoalDefinitionRecord(
                id=f"{definition.goal_id}:{definition.definition_version}",
                goal_id=str(definition.goal_id),
                user_id=str(definition.user_id),
                definition_version=definition.definition_version,
                semantic_fingerprint=definition.semantic_fingerprint,
                payload=definition.model_dump(mode="json"),
            )
        )
        await self.session.flush()

    async def latest_state(
        self, *, goal_id: UUID, user_id: UUID, lock: bool = False
    ) -> LearningGoalStateV1 | None:
        query = (
            select(GoalStateRecord)
            .where(
                GoalStateRecord.goal_id == str(goal_id),
                GoalStateRecord.user_id == str(user_id),
            )
            .order_by(GoalStateRecord.state_version.desc())
            .limit(1)
        )
        if lock:
            query = query.with_for_update()
        record = await self.session.scalar(query)
        return LearningGoalStateV1.model_validate(record.payload) if record else None

    async def save_state(self, state: LearningGoalStateV1, *, user_id: UUID) -> None:
        self.session.add(
            GoalStateRecord(
                id=f"{state.goal_id}:{state.state_version}",
                goal_id=str(state.goal_id),
                user_id=str(user_id),
                state_version=state.state_version,
                status=state.status,
                definition_version=state.definition_version,
                payload=state.model_dump(mode="json"),
            )
        )
        await self.session.flush()

    async def save_plan_state(self, state: LearningPlanStateV1) -> None:
        self.session.add(
            GoalPlanStateRecord(
                id=f"{state.plan_id}:{state.plan_version}:{state.state_version}",
                plan_id=str(state.plan_id),
                plan_version=state.plan_version,
                state_version=state.state_version,
                status=state.status,
                payload=state.model_dump(mode="json"),
            )
        )
        await self.session.flush()

    async def latest_focus(self, *, user_id: UUID) -> FocusedLearningGoalStateV1 | None:
        record = await self.session.scalar(
            select(FocusedGoalStateRecord)
            .where(FocusedGoalStateRecord.user_id == str(user_id))
            .order_by(FocusedGoalStateRecord.focus_version.desc())
            .limit(1)
        )
        return FocusedLearningGoalStateV1.model_validate(record.payload) if record else None

    async def save_focus(self, focus: FocusedLearningGoalStateV1) -> None:
        self.session.add(
            FocusedGoalStateRecord(
                id=f"{focus.user_id}:{focus.focus_version}",
                user_id=str(focus.user_id),
                focus_version=focus.focus_version,
                goal_id=str(focus.goal_id) if focus.goal_id else None,
                payload=focus.model_dump(mode="json"),
            )
        )
        await self.session.flush()

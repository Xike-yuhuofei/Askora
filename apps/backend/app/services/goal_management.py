"""SYS06 P1-01 goal draft, preview, apply and focus service."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from typing import Literal, cast
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.adaptive import VersionedRef
from app.contracts.goal_management import (
    ApplyGoalDraftCommandV1,
    CognitiveProcess,
    CreateEditGoalDraftCommandV1,
    CreateGoalDraftCommandV1,
    FocusedLearningGoalStateV1,
    GoalApplyResultV1,
    GoalChangePreviewV1,
    GoalDetailV1,
    GoalFieldDiffV1,
    GoalSourceViewV1,
    GoalStatus,
    GoalTargetCardV1,
    LearningGoalDefinitionV2,
    LearningGoalDraftV1,
    LearningGoalStateV1,
    LearningPlanStateV1,
    PreviewGoalDraftCommandV1,
    SuccessCriterionInputV1,
    SuccessCriterionV1,
    SuggestSuccessCriteriaResponseV1,
    UpdateGoalDraftCommandV1,
)
from app.contracts.planning import (
    ConfirmedLearningGoal,
    GoalKnowledgeMappingV1,
    GoalSpecificKnowledgeSubgraphV1,
    GoalTargetEvidenceV1,
    LearningGoalV1,
)
from app.core.exceptions import BusinessError, ResourceNotFoundError
from app.domains.content_knowledge import CONTENT_RECORD_KEY
from app.domains.learning_planner.goal_mapping import CLOSURE_POLICY_VERSION, MAPPER_VERSION
from app.domains.learning_planner.planner import LearningPlanner
from app.infrastructure.activity_lifecycle import ActivityLifecycleRepository
from app.infrastructure.goal_management import GoalManagementRepository
from app.infrastructure.planning_records import GoalPlanningRepository, LearningPlanRepository
from app.models.document import ModerationStatus, ProcessingStatus, UserDocument
from app.models.planning import LearningActivityRecord, LearningPlanRecord
from app.models.user import User
from app.queries.goal_knowledge import GoalKnowledgeQueryService, PublishedGoalKnowledgeScope
from app.services.activity_lifecycle import ActivityLifecycleService
from app.services.auth.canonical_identity import canonical_user_id

_UNMEASURABLE = ("了解", "理解", "熟悉", "看完", "读完", "understand", "familiar", "read")


def _error(code: str, message: str, status: int = HTTPStatus.CONFLICT) -> BusinessError:
    return BusinessError(message=message, error_code=code, status_code=status)


def _digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def _ref(entity_type: str, entity_id: UUID | str, version: str | int) -> VersionedRef:
    return VersionedRef(entity_type=entity_type, entity_id=str(entity_id), version=version)


class GoalManagementService:
    """One SYS06 writer for Definition/State/Draft/Preview/Focus and plan cutover."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = GoalManagementRepository(session)
        self.legacy = GoalPlanningRepository(session)
        self.plans = LearningPlanRepository(session)
        self.knowledge = GoalKnowledgeQueryService(session)

    async def create_draft(
        self,
        *,
        user: User,
        command: CreateGoalDraftCommandV1,
        correlation_id: UUID,
        now: datetime,
    ) -> LearningGoalDraftV1:
        del correlation_id
        owner_id = canonical_user_id(user.id)
        digest = _digest(command.model_dump(mode="json"))
        replay = await self.repo.replay(
            user_id=owner_id,
            idempotency_key=command.idempotency_key,
            payload_digest=digest,
            response_model=LearningGoalDraftV1,
        )
        if replay is not None:
            return replay
        await self._owned_documents(user, command.source_document_ids)
        goal_id = uuid5(NAMESPACE_URL, f"askora:goal-v2:{owner_id}:{command.idempotency_key}")
        draft = LearningGoalDraftV1(
            draft_id=uuid5(goal_id, "draft"),
            draft_version=1,
            user_id=owner_id,
            goal_id=goal_id,
            base_definition_version=None,
            status="draft",
            title=command.title,
            topic=command.topic,
            target_capabilities=command.target_capabilities,
            application_context=command.application_context,
            deadline_at=command.deadline_at,
            weekly_time_budget_minutes=command.weekly_time_budget_minutes,
            success_criteria=command.success_criteria,
            source_document_ids=tuple(dict.fromkeys(command.source_document_ids)),
            created_at=now,
        )
        await self.repo.save_draft(draft)
        await self.repo.receipt(
            user_id=owner_id,
            command_type="CreateGoalDraftV1",
            idempotency_key=command.idempotency_key,
            payload_digest=digest,
            response=draft,
        )
        return draft

    async def get_draft(self, *, user: User, draft_id: UUID) -> LearningGoalDraftV1:
        draft = await self.repo.latest_draft(
            draft_id=draft_id, user_id=canonical_user_id(user.id)
        )
        if draft is None:
            raise ResourceNotFoundError("目标草稿")
        return draft

    async def create_edit_draft(
        self,
        *,
        user: User,
        goal_id: UUID,
        command: CreateEditGoalDraftCommandV1,
        correlation_id: UUID,
        now: datetime,
    ) -> LearningGoalDraftV1:
        del correlation_id
        owner_id = canonical_user_id(user.id)
        digest = _digest({"goal_id": str(goal_id), **command.model_dump(mode="json")})
        replay = await self.repo.replay(
            user_id=owner_id,
            idempotency_key=command.idempotency_key,
            payload_digest=digest,
            response_model=LearningGoalDraftV1,
        )
        if replay is not None:
            return replay
        definition = await self.repo.latest_definition(goal_id=goal_id, user_id=owner_id)
        state = await self.repo.latest_state(goal_id=goal_id, user_id=owner_id)
        if definition is None or state is None:
            raise ResourceNotFoundError("学习目标")
        if state.state_version != command.expected_state_version:
            raise _error("GOAL_VERSION_CONFLICT", "目标状态已更新，请刷新后重试")
        selected_target_ids: tuple[UUID, ...] = ()
        if state.mapping_ref is not None:
            mapping = await self.legacy.get_mapping_version(
                mapping_id=UUID(state.mapping_ref.entity_id),
                version=int(state.mapping_ref.version),
            )
            if mapping is not None:
                selected_target_ids = mapping.selected_target_ids
        draft_id = uuid5(goal_id, f"edit-draft:{command.idempotency_key}")
        draft = LearningGoalDraftV1(
            draft_id=draft_id,
            draft_version=1,
            user_id=owner_id,
            goal_id=goal_id,
            base_definition_version=definition.definition_version,
            status="draft",
            title=definition.title,
            topic=definition.topic,
            target_capabilities=definition.target_capabilities,
            application_context=definition.application_context,
            deadline_at=definition.deadline_at,
            weekly_time_budget_minutes=definition.weekly_time_budget_minutes,
            success_criteria=tuple(
                SuccessCriterionInputV1.model_validate(
                    item.model_dump(exclude={"target_refs"})
                )
                for item in definition.success_criteria
            ),
            source_document_ids=definition.source_document_ids,
            selected_target_ids=selected_target_ids,
            targets_confirmed=bool(selected_target_ids),
            created_at=now,
        )
        await self.repo.save_draft(draft)
        await self.repo.receipt(
            user_id=owner_id,
            command_type="CreateEditGoalDraftV1",
            idempotency_key=command.idempotency_key,
            payload_digest=digest,
            response=draft,
        )
        return draft

    async def get_goal_detail(self, *, user: User, goal_id: UUID) -> GoalDetailV1:
        owner_id = canonical_user_id(user.id)
        definition = await self.repo.latest_definition(goal_id=goal_id, user_id=owner_id)
        state = await self.repo.latest_state(goal_id=goal_id, user_id=owner_id)
        if definition is None or state is None:
            raise ResourceNotFoundError("学习目标")
        focus = await self.repo.latest_focus(user_id=owner_id)
        return GoalDetailV1(
            definition=definition,
            state=state,
            focused=focus is not None and focus.goal_id == goal_id,
        )

    @staticmethod
    def suggest_criteria(
        *, topic: str, cognitive_processes: tuple[CognitiveProcess, ...]
    ) -> SuggestSuccessCriteriaResponseV1:
        templates = {
            "recall": ("不查看资料，独立回忆并准确列出 {topic} 的关键要点", ("delayed_independent_recall",)),
            "understand": ("不查看资料，独立解释 {topic} 并说明关键关系", ("independent_explanation", "delayed_independent")),
            "explain": ("面向未学习者独立解释 {topic}，并回应一个追问", ("independent_explanation", "delayed_independent")),
            "apply": ("独立运用 {topic} 解决一个未见过的具体问题", ("independent_application", "novel_context")),
            "transfer": ("在足够新颖的情境中独立迁移运用 {topic}", ("independent_transfer", "novel_context")),
        }
        criteria: list[SuccessCriterionInputV1] = []
        for process in cognitive_processes:
            statement, requirements = templates[process]
            criteria.append(
                SuccessCriterionInputV1(
                    criterion_id=uuid5(NAMESPACE_URL, f"goal-criterion:{topic}:{process}"),
                    cognitive_process=process,
                    statement=statement.format(topic=topic),
                    evidence_requirements=requirements,
                )
            )
        return SuggestSuccessCriteriaResponseV1(criteria=tuple(criteria))

    async def update_draft(
        self,
        *,
        user: User,
        draft_id: UUID,
        command: UpdateGoalDraftCommandV1,
        correlation_id: UUID,
        now: datetime,
    ) -> LearningGoalDraftV1:
        del correlation_id
        owner_id = canonical_user_id(user.id)
        digest = _digest({"draft_id": str(draft_id), **command.model_dump(mode="json")})
        replay = await self.repo.replay(
            user_id=owner_id,
            idempotency_key=command.idempotency_key,
            payload_digest=digest,
            response_model=LearningGoalDraftV1,
        )
        if replay is not None:
            return replay
        current = await self.get_draft(user=user, draft_id=draft_id)
        if current.draft_version != command.expected_draft_version:
            raise _error("GOAL_VERSION_CONFLICT", "目标草稿已更新，请刷新后重试")
        if current.status in {"applied", "cancelled"}:
            raise _error("GOAL_VERSION_CONFLICT", "目标草稿已结束")
        fields = command.model_fields_set - {"expected_draft_version", "idempotency_key"}
        updates: dict[str, object] = {
            field: getattr(command, field) for field in fields if getattr(command, field) is not None
        }
        for nullable in ("application_context", "deadline_at", "weekly_time_budget_minutes"):
            if nullable in fields:
                updates[nullable] = getattr(command, nullable)
        if "source_document_ids" in updates:
            if command.source_document_ids is None:
                raise _error("GOAL_VERSION_CONFLICT", "资料版本已更新，请刷新后重试")
            source_ids = tuple(dict.fromkeys(command.source_document_ids))
            await self._owned_documents(user, source_ids)
            updates["source_document_ids"] = source_ids
            if "selected_target_ids" not in fields:
                updates.update(selected_target_ids=(), targets_confirmed=False)
        if "success_criteria" in fields or "target_capabilities" in fields:
            if "selected_target_ids" not in fields:
                updates["targets_confirmed"] = False
        updated = current.model_copy(
            update={
                **updates,
                "draft_version": current.draft_version + 1,
                "status": "draft",
                "pending_preview_id": None,
                "block_reason_codes": (),
                "created_at": now,
            }
        )
        await self.repo.save_draft(updated)
        await self.repo.receipt(
            user_id=owner_id,
            command_type="UpdateGoalDraftV1",
            idempotency_key=command.idempotency_key,
            payload_digest=digest,
            response=updated,
        )
        return updated

    async def suggest_targets(
        self, *, user: User, draft_id: UUID
    ) -> tuple[GoalTargetCardV1, ...]:
        draft = await self.get_draft(user=user, draft_id=draft_id)
        scope = await self.knowledge.load_scope(
            user=user, source_document_ids=draft.source_document_ids
        )
        documents = await self._owned_documents(user, draft.source_document_ids)
        by_id = {UUID(item.id): item for item in documents}
        cards: list[GoalTargetCardV1] = []
        for unit in scope.units:
            document = by_id[unit.source_document_id]
            cards.append(
                GoalTargetCardV1(
                    target_id=unit.knowledge_unit_id,
                    target_ref=self._unit_ref(unit.knowledge_unit_ref, unit.knowledge_unit_id),
                    name=unit.canonical_name,
                    source_name=document.display_title or document.original_filename,
                    evidence_excerpt=self._evidence_excerpt(document, unit.source_span_ids),
                    recommended_reason="来自所选资料的已发布知识，并可追溯原文证据",
                )
            )
        return tuple(cards)

    async def preview_draft(
        self,
        *,
        user: User,
        draft_id: UUID,
        command: PreviewGoalDraftCommandV1,
        correlation_id: UUID,
        now: datetime,
    ) -> GoalChangePreviewV1:
        del correlation_id
        owner_id = canonical_user_id(user.id)
        digest = _digest({"draft_id": str(draft_id), **command.model_dump(mode="json")})
        replay = await self.repo.replay(
            user_id=owner_id,
            idempotency_key=command.idempotency_key,
            payload_digest=digest,
            response_model=GoalChangePreviewV1,
        )
        if replay is not None:
            return replay
        draft = await self.get_draft(user=user, draft_id=draft_id)
        if draft.draft_version != command.expected_draft_version:
            raise _error("GOAL_VERSION_CONFLICT", "目标草稿已更新，请刷新后重试")
        for criterion in draft.success_criteria:
            if any(marker in criterion.statement.casefold() for marker in _UNMEASURABLE):
                raise _error("GOAL_CRITERION_UNMEASURABLE", "成功标准必须可独立测量")
        source_views, scope = await self._source_scope(user, draft.source_document_ids)
        if any(item.status != "executable" for item in source_views):
            raise _error("GOAL_SOURCE_NOT_EXECUTABLE", "所选资料尚不能用于目标确认")
        cards = await self.suggest_targets(user=user, draft_id=draft_id)
        card_ids = {item.target_id for item in cards}
        if (
            not draft.targets_confirmed
            or not draft.selected_target_ids
            or not set(draft.selected_target_ids).issubset(card_ids)
        ):
            raise _error(
                "GOAL_TARGET_CONFIRMATION_REQUIRED",
                "请明确勾选并确认学习重点",
            )
        current_definition = await self.repo.latest_definition(
            goal_id=draft.goal_id, user_id=owner_id
        )
        current_state = await self.repo.latest_state(goal_id=draft.goal_id, user_id=owner_id)
        active_activity_ref = await self._active_activity_ref(draft.goal_id)
        input_refs = [
            _ref("MaterialRevision", value.split(":revision:")[1].split(":")[0], value)
            for value in scope.knowledge_graph_versions
        ]
        if current_definition is not None:
            input_refs.append(
                _ref("LearningGoalDefinition", draft.goal_id, current_definition.definition_version)
            )
        if current_state is not None:
            input_refs.append(_ref("LearningGoalState", draft.goal_id, current_state.state_version))
            if current_state.mapping_ref is not None:
                input_refs.append(current_state.mapping_ref)
            if current_state.plan_ref is not None:
                input_refs.append(current_state.plan_ref)
        if active_activity_ref is not None:
            input_refs.append(active_activity_ref)
        before = current_definition.model_dump(mode="json") if current_definition else {}
        after = {
            "title": draft.title,
            "topic": draft.topic,
            "target_capabilities": draft.target_capabilities,
            "application_context": draft.application_context,
            "deadline_at": draft.deadline_at,
            "weekly_time_budget_minutes": draft.weekly_time_budget_minutes,
            "success_criteria": [item.model_dump(mode="json") for item in draft.success_criteria],
            "source_document_ids": draft.source_document_ids,
            "selected_target_ids": draft.selected_target_ids,
        }
        diffs = tuple(
            GoalFieldDiffV1(field=field, before=before.get(field), after=value)
            for field, value in after.items()
            if before.get(field) != value
        )
        preview_id = uuid5(draft.draft_id, f"preview:{draft.draft_version}")
        preview = GoalChangePreviewV1(
            preview_id=preview_id,
            preview_version=1,
            draft_id=draft.draft_id,
            draft_version=draft.draft_version,
            goal_id=draft.goal_id,
            input_refs=tuple(input_refs),
            field_diffs=diffs,
            sources=source_views,
            target_cards=tuple(item for item in cards if item.target_id in draft.selected_target_ids),
            selected_target_ids=draft.selected_target_ids,
            plan_impact={
                "creates_new_mapping": True,
                "creates_new_plan": True,
                "old_plan_effect": "superseded_after_new_plan_ready",
            },
            effective_timing="activity_boundary" if active_activity_ref else "immediate",
            active_activity_ref=active_activity_ref,
            expires_at=now + timedelta(hours=24),
            created_at=now,
        )
        await self.repo.save_preview(preview, user_id=owner_id)
        preview_draft = draft.model_copy(
            update={
                "draft_version": draft.draft_version + 1,
                "status": "preview_ready",
                "pending_preview_id": preview.preview_id,
                "created_at": now,
            }
        )
        await self.repo.save_draft(preview_draft)
        # The preview pins the input draft version; apply accepts it even though status projection advanced.
        await self.repo.receipt(
            user_id=owner_id,
            command_type="PreviewGoalDraftV1",
            idempotency_key=command.idempotency_key,
            payload_digest=digest,
            response=preview,
        )
        return preview

    async def apply_draft(
        self,
        *,
        user: User,
        draft_id: UUID,
        command: ApplyGoalDraftCommandV1,
        correlation_id: UUID,
        now: datetime,
    ) -> GoalApplyResultV1:
        owner_id = canonical_user_id(user.id)
        digest = _digest({"draft_id": str(draft_id), **command.model_dump(mode="json")})
        replay = await self.repo.replay(
            user_id=owner_id,
            idempotency_key=command.idempotency_key,
            payload_digest=digest,
            response_model=GoalApplyResultV1,
        )
        if replay is not None:
            return replay
        draft = await self.get_draft(user=user, draft_id=draft_id)
        preview = await self.repo.get_preview(
            preview_id=command.preview_id,
            version=command.expected_preview_version,
            user_id=owner_id,
        )
        if preview is None or preview.draft_id != draft_id:
            raise _error("GOAL_PREVIEW_STALE", "目标预览已失效，请重新预览")
        expected_projection_version = command.expected_draft_version + 1
        if (
            preview.draft_version != command.expected_draft_version
            or draft.draft_version != expected_projection_version
            or draft.pending_preview_id != preview.preview_id
            or draft.status != "preview_ready"
            or preview.expires_at <= now
        ):
            raise _error("GOAL_PREVIEW_STALE", "目标预览已失效，请重新预览")
        current_activity = await self._active_activity_ref(draft.goal_id)
        if current_activity != preview.active_activity_ref:
            raise _error("GOAL_PREVIEW_STALE", "活动版本已变化，请重新预览")
        if current_activity is not None and command.boundary_mode == "normal_boundary":
            pending = draft.model_copy(
                update={
                    "draft_version": draft.draft_version + 1,
                    "status": "approved_pending_boundary",
                    "created_at": now,
                }
            )
            await self.repo.save_draft(pending)
            result = GoalApplyResultV1(
                draft_id=draft_id,
                draft_version=pending.draft_version,
                goal_id=draft.goal_id,
                status="approved_pending_boundary",
                definition_ref=None,
                mapping_ref=None,
                plan_ref=None,
                activity_ref=current_activity,
                reason_codes=("GOAL_WAITING_ACTIVITY_BOUNDARY",),
            )
        else:
            if current_activity is not None:
                await self._supersede_active_activity(
                    current_activity, correlation_id=correlation_id, now=now
                )
            result = await self._apply_now(
                user=user,
                draft=draft,
                preview=preview,
                set_focused=command.set_focused,
                correlation_id=correlation_id,
                idempotency_key=command.idempotency_key,
                now=now,
            )
        await self.repo.receipt(
            user_id=owner_id,
            command_type="ApplyGoalDraftV1",
            idempotency_key=command.idempotency_key,
            payload_digest=digest,
            response=result,
        )
        return result

    async def get_focused_goal(self, *, user: User) -> FocusedLearningGoalStateV1:
        owner_id = canonical_user_id(user.id)
        focus = await self.repo.latest_focus(user_id=owner_id)
        if focus is None:
            return FocusedLearningGoalStateV1(
                user_id=owner_id,
                focus_version=1,
                goal_id=None,
                reason_codes=("GOAL_FOCUS_NOT_SET",),
                correlation_id=uuid5(owner_id, "focus-not-set"),
                created_at=datetime.now(timezone.utc),
            )
        return focus

    async def apply_pending_at_boundary(
        self,
        *,
        user: User,
        completed_activity_id: UUID,
        correlation_id: UUID,
        now: datetime,
    ) -> VersionedRef | None:
        activity = await self.session.get(LearningActivityRecord, str(completed_activity_id))
        if activity is None:
            return None
        plan_record = await self.session.scalar(
            select(LearningPlanRecord).where(
                LearningPlanRecord.plan_id == activity.plan_id,
                LearningPlanRecord.version == activity.plan_version,
            )
        )
        if plan_record is None:
            return None
        owner_id = canonical_user_id(user.id)
        pending = await self.repo.latest_pending_draft_for_goal(
            goal_id=UUID(plan_record.learning_goal_id), user_id=owner_id
        )
        if pending is None or pending.pending_preview_id is None:
            return None
        preview = await self.repo.get_preview(
            preview_id=pending.pending_preview_id, version=1, user_id=owner_id
        )
        if preview is None:
            return None
        result = await self._apply_now(
            user=user,
            draft=pending,
            preview=preview,
            set_focused=False,
            correlation_id=correlation_id,
            idempotency_key=(
                f"goal-boundary:{pending.draft_id}:v{pending.draft_version}:"
                f"{completed_activity_id}"
            ),
            now=now,
        )
        return result.activity_ref

    async def _apply_now(
        self,
        *,
        user: User,
        draft: LearningGoalDraftV1,
        preview: GoalChangePreviewV1,
        set_focused: bool,
        correlation_id: UUID,
        idempotency_key: str,
        now: datetime,
    ) -> GoalApplyResultV1:
        owner_id = canonical_user_id(user.id)
        scope = await self.knowledge.load_scope(
            user=user, source_document_ids=draft.source_document_ids
        )
        selected = {item.knowledge_unit_id: item for item in scope.units}
        if not set(draft.selected_target_ids).issubset(selected):
            raise _error("GOAL_PREVIEW_STALE", "资料知识版本已变化，请重新预览")
        definition_version = await self.repo.next_definition_version(draft.goal_id)
        target_refs = tuple(
            self._unit_ref(selected[item].knowledge_unit_ref, item)
            for item in draft.selected_target_ids
        )
        definition_payload = {
            "title": draft.title,
            "topic": draft.topic,
            "target_capabilities": draft.target_capabilities,
            "application_context": draft.application_context,
            "success_criteria": [item.model_dump(mode="json") for item in draft.success_criteria],
            "source_document_ids": draft.source_document_ids,
            "deadline_at": draft.deadline_at,
            "weekly_time_budget_minutes": draft.weekly_time_budget_minutes,
            "selected_target_ids": draft.selected_target_ids,
        }
        definition = LearningGoalDefinitionV2(
            goal_id=draft.goal_id,
            definition_version=definition_version,
            user_id=owner_id,
            title=draft.title,
            topic=draft.topic,
            target_capabilities=draft.target_capabilities,
            application_context=draft.application_context,
            success_criteria=tuple(
                SuccessCriterionV1(**item.model_dump(), target_refs=target_refs)
                for item in draft.success_criteria
            ),
            source_document_ids=draft.source_document_ids,
            deadline_at=draft.deadline_at,
            weekly_time_budget_minutes=draft.weekly_time_budget_minutes,
            semantic_fingerprint=_digest(definition_payload),
            created_at=now,
            supersedes_definition_version=draft.base_definition_version,
            reason_codes=("GOAL_DRAFT_APPLIED",),
        )
        await self.repo.save_definition(definition)

        legacy_version = await self.legacy.next_goal_version(draft.goal_id)
        legacy_goal = LearningGoalV1(
            goal_id=draft.goal_id,
            version=legacy_version,
            user_id=owner_id,
            title=draft.title,
            topic=draft.topic,
            target_capabilities=draft.target_capabilities,
            application_context=draft.application_context,
            success_criteria=tuple(item.statement for item in draft.success_criteria),
            source_document_ids=draft.source_document_ids,
            deadline_at=draft.deadline_at,
            weekly_time_budget_minutes=draft.weekly_time_budget_minutes,
            status="active",
            confirmed_by_user=True,
            created_at=now,
            confirmed_at=now,
            supersedes_version=legacy_version - 1 if legacy_version > 1 else None,
            reason_codes=("GOAL_V2_COMPATIBILITY_SNAPSHOT",),
        )
        await self.legacy.save_goal(
            legacy_goal, idempotency_key=f"goal-v2-legacy:{idempotency_key}"
        )
        mapping_version = await self.legacy.next_mapping_version(draft.goal_id)
        mapping_id = uuid5(draft.goal_id, "goal-knowledge-mapping")
        target_evidence = tuple(
            GoalTargetEvidenceV1(
                knowledge_unit_id=item,
                knowledge_unit_ref=selected[item].knowledge_unit_ref,
                source_document_id=selected[item].source_document_id,
                material_revision_id=selected[item].material_revision_id,
                source_span_ids=selected[item].source_span_ids,
                rank_positions={"explicit_user_selection": index + 1},
                fusion_score=1.0,
                reason_codes=("GOAL_TARGET_EXPLICITLY_CONFIRMED",),
            )
            for index, item in enumerate(draft.selected_target_ids)
        )
        mapping = GoalKnowledgeMappingV1(
            mapping_id=mapping_id,
            mapping_version=mapping_version,
            goal_id=draft.goal_id,
            goal_version=legacy_version,
            source_document_ids=scope.authorized_document_ids,
            knowledge_graph_versions=scope.knowledge_graph_versions,
            candidate_target_ids=draft.selected_target_ids,
            selected_target_ids=draft.selected_target_ids,
            excluded_target_ids=(),
            target_evidence=target_evidence,
            confidence=None,
            reason_codes=("GOAL_TARGET_EXPLICITLY_CONFIRMED",),
            mapper_version=f"{MAPPER_VERSION}+explicit-target-v1",
            status="confirmed",
            created_at=now,
        )
        await self.legacy.save_mapping(
            mapping, idempotency_key=f"goal-v2-mapping:{idempotency_key}"
        )
        relation_refs = tuple(
            self._relation_ref(item.relation_ref, item.relation_id)
            for item in scope.relations
            if item.target_knowledge_unit_id in draft.selected_target_ids
        )
        prerequisites = tuple(
            sorted(
                {
                    item.prerequisite_id
                    for item in scope.relations
                    if item.target_knowledge_unit_id in draft.selected_target_ids
                },
                key=str,
            )
        )
        subgraph = GoalSpecificKnowledgeSubgraphV1(
            subgraph_id=uuid5(mapping_id, "goal-subgraph"),
            version=mapping_version,
            goal_mapping_ref=_ref("GoalKnowledgeMapping", mapping_id, mapping_version),
            target_knowledge_unit_ids=draft.selected_target_ids,
            included_prerequisite_ids=prerequisites,
            relation_refs=relation_refs,
            knowledge_graph_versions=scope.knowledge_graph_versions,
            closure_policy_version=CLOSURE_POLICY_VERSION,
            reason_codes=("GOAL_EXPLICIT_TARGET_CLOSURE",),
            created_at=now,
        )
        await self.legacy.save_subgraph(subgraph)
        plan_version = await self.plans.next_version(draft.goal_id)
        objective_id = uuid5(draft.goal_id, f"objective:{definition_version}")
        planner_goal = ConfirmedLearningGoal(
            goal_id=draft.goal_id,
            objective_id=objective_id,
            target_knowledge_unit_ids=list(draft.selected_target_ids),
            confirmed_at=now,
        )
        prerequisite_map: dict[UUID, list[UUID]] = {}
        for relation in scope.relations:
            prerequisite_map.setdefault(relation.target_knowledge_unit_id, []).append(
                relation.prerequisite_id
            )
        decision = LearningPlanner().generate(
            goal=planner_goal,
            prerequisites=prerequisite_map,
            mastery={item: None for item in (*draft.selected_target_ids, *prerequisites)},
            due_candidates=[],
            time_budget_minutes=max(5, (draft.weekly_time_budget_minutes or 70) // 7),
            learner_state_version=1,
            knowledge_graph_version=",".join(scope.knowledge_graph_versions),
            version=plan_version,
            created_at=now,
            reason_codes=["GOAL_DEFINITION_APPLIED"],
        )
        plan = await self.plans.save(
            decision, idempotency_key=f"goal-v2-plan:{idempotency_key}"
        )
        activity_response = await ActivityLifecycleService(self.session).select_next(
            user=user,
            goal_id=draft.goal_id,
            idempotency_key=f"goal-v2-select:{idempotency_key}",
            correlation_id=correlation_id,
            now=now,
        )
        prior_state = await self.repo.latest_state(goal_id=draft.goal_id, user_id=owner_id)
        next_state_version = (prior_state.state_version if prior_state else 0) + 1
        if prior_state is None:
            confirmed = LearningGoalStateV1(
                goal_id=draft.goal_id,
                state_version=next_state_version,
                status="confirmed",
                definition_version=definition_version,
                mapping_ref=_ref("GoalKnowledgeMapping", mapping_id, mapping_version),
                plan_ref=_ref("LearningPlan", plan.plan_id, plan.version),
                previous_status=None,
                reason_codes=("GOAL_CONFIRMED_BY_APPLY",),
                correlation_id=correlation_id,
                created_at=now,
            )
            await self.repo.save_state(confirmed, user_id=owner_id)
            next_state_version += 1
            previous_status = "confirmed"
        else:
            previous_status = prior_state.status
        active = LearningGoalStateV1(
            goal_id=draft.goal_id,
            state_version=next_state_version,
            status="active",
            definition_version=definition_version,
            mapping_ref=_ref("GoalKnowledgeMapping", mapping_id, mapping_version),
            plan_ref=_ref("LearningPlan", plan.plan_id, plan.version),
            previous_status=cast(GoalStatus, previous_status),
            reason_codes=("GOAL_PLAN_ACTIVATED",),
            correlation_id=correlation_id,
            created_at=now,
        )
        await self.repo.save_state(active, user_id=owner_id)
        await self.repo.save_plan_state(
            LearningPlanStateV1(
                plan_id=plan.plan_id,
                plan_version=plan.version,
                state_version=1,
                status="active",
                previous_status=None,
                reason_codes=("GOAL_PLAN_ACTIVATED",),
                correlation_id=correlation_id,
                created_at=now,
            )
        )
        if set_focused:
            prior_focus = await self.repo.latest_focus(user_id=owner_id)
            await self.repo.save_focus(
                FocusedLearningGoalStateV1(
                    user_id=owner_id,
                    focus_version=(prior_focus.focus_version if prior_focus else 0) + 1,
                    goal_id=draft.goal_id,
                    reason_codes=("GOAL_FOCUS_EXPLICITLY_SET",),
                    correlation_id=correlation_id,
                    created_at=now,
                )
            )
        applied_draft = draft.model_copy(
            update={
                "draft_version": draft.draft_version + 1,
                "status": "applied",
                "created_at": now,
            }
        )
        await self.repo.save_draft(applied_draft)
        return GoalApplyResultV1(
            draft_id=draft.draft_id,
            draft_version=applied_draft.draft_version,
            goal_id=draft.goal_id,
            status="applied",
            definition_ref=_ref("LearningGoalDefinition", draft.goal_id, definition_version),
            mapping_ref=_ref("GoalKnowledgeMapping", mapping_id, mapping_version),
            plan_ref=_ref("LearningPlan", plan.plan_id, plan.version),
            activity_ref=_ref(
                "LearningActivity",
                activity_response.data.state.activity_id,
                activity_response.data.state.plan_version,
            ),
            reason_codes=("GOAL_CHANGE_APPLIED",),
        )

    async def _owned_documents(
        self, user: User, document_ids: tuple[UUID, ...]
    ) -> list[UserDocument]:
        unique = tuple(dict.fromkeys(document_ids))
        documents = (
            await self.session.scalars(
                select(UserDocument).where(
                    UserDocument.id.in_([str(item) for item in unique]),
                    UserDocument.pseudonym_id == user.pseudonym_id,
                )
            )
        ).all()
        if len(documents) != len(unique):
            raise ResourceNotFoundError("资料")
        return list(documents)

    async def _source_scope(
        self, user: User, source_ids: tuple[UUID, ...]
    ) -> tuple[tuple[GoalSourceViewV1, ...], PublishedGoalKnowledgeScope]:
        documents = await self._owned_documents(user, source_ids)
        scope = await self.knowledge.load_scope(user=user, source_document_ids=source_ids)
        authorized = set(scope.authorized_document_ids)
        views = []
        for document in sorted(documents, key=lambda item: item.id):
            document_id = UUID(document.id)
            record = (document.moderation_details or {}).get(CONTENT_RECORD_KEY, {})
            revision_id = record.get("current_revision_id")
            reason_codes: tuple[str, ...]
            status: Literal["executable", "waiting", "blocked"]
            if document.is_deleted:
                status = "blocked"
                reason_codes = ("GOAL_SOURCE_ARCHIVED",)
            elif document.moderation_status in {
                ModerationStatus.REJECTED,
                ModerationStatus.REQUIRES_REVIEW,
            }:
                status = "blocked"
                reason_codes = ("GOAL_SOURCE_MODERATION_BLOCKED",)
            elif document.processing_status in {
                ProcessingStatus.PENDING,
                ProcessingStatus.PROCESSING,
            }:
                status = "waiting"
                reason_codes = ("GOAL_SOURCE_PROCESSING",)
            elif document.processing_status != ProcessingStatus.COMPLETED:
                status = "blocked"
                reason_codes = ("GOAL_SOURCE_PROCESSING_FAILED",)
            elif document_id not in authorized or not any(
                item.source_document_id == document_id for item in scope.units
            ):
                status = "waiting"
                reason_codes = ("GOAL_SOURCE_NO_PUBLISHED_KNOWLEDGE",)
            else:
                status = "executable"
                reason_codes = ("GOAL_SOURCE_EXECUTABLE",)
            views.append(
                GoalSourceViewV1(
                    document_id=document_id,
                    display_name=document.display_title or document.original_filename,
                    status=status,
                    reason_codes=reason_codes,
                    revision_ref=(
                        _ref("MaterialRevision", revision_id, revision_id) if revision_id else None
                    ),
                )
            )
        return tuple(views), scope

    async def _active_activity_ref(self, goal_id: UUID) -> VersionedRef | None:
        plan_record = await self.session.scalar(
            select(LearningPlanRecord)
            .where(
                LearningPlanRecord.learning_goal_id == str(goal_id),
                LearningPlanRecord.status == "active",
            )
            .order_by(LearningPlanRecord.version.desc())
            .limit(1)
        )
        if plan_record is None:
            return None
        states = await ActivityLifecycleRepository(self.session).latest_for_plan(
            plan_id=UUID(plan_record.plan_id), plan_version=plan_record.version
        )
        active = next((item for item in states.values() if item.status == "active"), None)
        return (
            _ref("LearningActivityState", active.activity_id, active.version) if active else None
        )

    async def _supersede_active_activity(
        self, activity_ref: VersionedRef, *, correlation_id: UUID, now: datetime
    ) -> None:
        activity_id = UUID(activity_ref.entity_id)
        states = ActivityLifecycleRepository(self.session)
        prior = await states.latest(activity_id, for_update=True)
        if prior is None or prior.version != activity_ref.version or prior.status != "active":
            raise _error("GOAL_PREVIEW_STALE", "活动版本已变化，请重新预览")
        await states.append(
            prior.model_copy(
                update={
                    "version": prior.version + 1,
                    "status": "superseded",
                    "previous_status": "active",
                    "transition_reason": "GOAL_REPLAN_EXPLICIT_SWITCH",
                    "actor_type": "learner",
                    "correlation_id": correlation_id,
                    "created_at": now,
                    "completed_at": None,
                }
            )
        )

    @staticmethod
    def _unit_ref(raw: str, unit_id: UUID) -> VersionedRef:
        version: str | int = 1
        if ":v" in raw:
            suffix = raw.rsplit(":v", 1)[1]
            version = int(suffix) if suffix.isdigit() else suffix
        return _ref("KnowledgeUnit", unit_id, version)

    @staticmethod
    def _relation_ref(raw: str, relation_id: UUID) -> VersionedRef:
        version: str | int = 1
        if ":v" in raw:
            suffix = raw.rsplit(":v", 1)[1]
            version = int(suffix) if suffix.isdigit() else suffix
        return _ref("KnowledgeRelation", relation_id, version)

    @staticmethod
    def _evidence_excerpt(document: UserDocument, span_ids: tuple[UUID, ...]) -> str:
        record = (document.moderation_details or {}).get(CONTENT_RECORD_KEY, {})
        revision = next(
            (
                item
                for item in record.get("revisions", [])
                if item.get("revision_id") == record.get("current_revision_id")
            ),
            None,
        )
        if revision is None:
            return "已发布来源证据"
        wanted = {str(item) for item in span_ids}
        text = " ".join(
            str(item.get("text", ""))
            for item in revision.get("source_spans", [])
            if str(item.get("span_id")) in wanted
        )
        return " ".join(text.split())[:240] or "已发布来源证据"

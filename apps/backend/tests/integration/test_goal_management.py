"""P1-01A multi-source draft, preview and safe apply integration."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.contracts.activity_lifecycle import StartLearningActivityV1
from app.contracts.goal_management import (
    ApplyGoalDraftCommandV1,
    CreateEditGoalDraftCommandV1,
    CreateGoalDraftCommandV1,
    PreviewGoalDraftCommandV1,
    SuccessCriterionInputV1,
    UpdateGoalDraftCommandV1,
)
from app.core.database import Base
from app.core.exceptions import AppError, BusinessError
from app.infrastructure.activity_lifecycle import ActivityLifecycleRepository
from app.models.planning import LearningPlanRecord
from app.models.user import User
from app.services.activity_lifecycle import ActivityLifecycleService
from app.services.documents.document_service import DocumentService
from app.services.goal_management import GoalManagementService
from app.services.storage.local_storage import LocalFileStorage


async def _db(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'goal-management.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


async def _published_document(session, storage, user, name, heading, body):
    documents = DocumentService(session)
    documents.storage = storage
    document = await documents.upload_document(
        user.pseudonym_id,
        name,
        f"# {heading}\n\n{body}".encode(),
    )
    await documents.process_document(document.id)
    return document


def _criterion(statement: str) -> SuccessCriterionInputV1:
    return SuccessCriterionInputV1(
        criterion_id=uuid4(),
        cognitive_process="explain",
        statement=statement,
        evidence_requirements=("independent_explanation", "delayed_independent"),
    )


@pytest.mark.asyncio
async def test_multi_source_requires_measurable_criterion_and_explicit_targets(tmp_path) -> None:
    engine, factory = await _db(tmp_path)
    async with factory() as session:
        user = User(id=str(uuid4()), pseudonym_id="goal-owner")
        other = User(id=str(uuid4()), pseudonym_id="goal-other")
        session.add_all([user, other])
        await session.commit()
        storage = LocalFileStorage(str(tmp_path / "documents"))
        first = await _published_document(
            session, storage, user, "thermo.md", "热力学第二定律", "熵增描述孤立系统演化。"
        )
        second = await _published_document(
            session, storage, user, "transfer.md", "热机应用", "热机效率受冷热源温度约束。"
        )
        private = await _published_document(
            session, storage, other, "private.md", "私密", "不得跨用户选择。"
        )
        service = GoalManagementService(session)
        now = datetime.now(timezone.utc)
        draft = await service.create_draft(
            user=user,
            command=CreateGoalDraftCommandV1(
                source_document_ids=(UUID(first.id), UUID(second.id)),
                title="热力学迁移应用",
                topic="热力学",
                target_capabilities=("解释", "应用"),
                application_context="分析热机",
                deadline_at=None,
                weekly_time_budget_minutes=90,
                success_criteria=(_criterion("理解热力学"),),
                idempotency_key="goal-draft-create-001",
            ),
            correlation_id=uuid4(),
            now=now,
        )
        with pytest.raises(BusinessError) as unmeasurable:
            await service.preview_draft(
                user=user,
                draft_id=draft.draft_id,
                command=PreviewGoalDraftCommandV1(
                    expected_draft_version=draft.draft_version,
                    idempotency_key="goal-preview-unmeasurable",
                ),
                correlation_id=uuid4(),
                now=now,
            )
        assert unmeasurable.value.error_code == "GOAL_CRITERION_UNMEASURABLE"

        with pytest.raises(AppError) as private_source:
            await service.update_draft(
                user=user,
                draft_id=draft.draft_id,
                command=UpdateGoalDraftCommandV1(
                    expected_draft_version=draft.draft_version,
                    source_document_ids=(UUID(first.id), UUID(private.id)),
                    success_criteria=(_criterion("独立解释热力学第二定律并给出新例子"),),
                    idempotency_key="goal-draft-private-source",
                ),
                correlation_id=uuid4(),
                now=now,
            )
        assert private_source.value.error_code == "DATA-0001"

        draft = await service.update_draft(
            user=user,
            draft_id=draft.draft_id,
            command=UpdateGoalDraftCommandV1(
                expected_draft_version=draft.draft_version,
                success_criteria=(_criterion("独立解释热力学第二定律并给出新例子"),),
                idempotency_key="goal-draft-update-001",
            ),
            correlation_id=uuid4(),
            now=now,
        )
        with pytest.raises(BusinessError) as targets:
            await service.preview_draft(
                user=user,
                draft_id=draft.draft_id,
                command=PreviewGoalDraftCommandV1(
                    expected_draft_version=draft.draft_version,
                    idempotency_key="goal-preview-target-required",
                ),
                correlation_id=uuid4(),
                now=now,
            )
        assert targets.value.error_code == "GOAL_TARGET_CONFIRMATION_REQUIRED"

        cards = await service.suggest_targets(user=user, draft_id=draft.draft_id)
        assert len(cards) >= 2
        draft = await service.update_draft(
            user=user,
            draft_id=draft.draft_id,
            command=UpdateGoalDraftCommandV1(
                expected_draft_version=draft.draft_version,
                selected_target_ids=tuple(card.target_id for card in cards[:2]),
                targets_confirmed=True,
                idempotency_key="goal-draft-targets-001",
            ),
            correlation_id=uuid4(),
            now=now,
        )
        preview = await service.preview_draft(
            user=user,
            draft_id=draft.draft_id,
            command=PreviewGoalDraftCommandV1(
                expected_draft_version=draft.draft_version,
                idempotency_key="goal-preview-001",
            ),
            correlation_id=uuid4(),
            now=now,
        )
        assert preview.effective_timing == "immediate"
        assert len(preview.input_refs) >= 2
        applied = await service.apply_draft(
            user=user,
            draft_id=draft.draft_id,
            command=ApplyGoalDraftCommandV1(
                expected_draft_version=preview.draft_version,
                expected_preview_version=preview.preview_version,
                preview_id=preview.preview_id,
                boundary_mode="normal_boundary",
                set_focused=True,
                idempotency_key="goal-apply-001",
            ),
            correlation_id=uuid4(),
            now=now,
        )
        assert applied.status == "applied"
        assert applied.definition_ref is not None
        assert applied.mapping_ref is not None
        assert applied.plan_ref is not None
        assert (await service.get_focused_goal(user=user)).goal_id == applied.goal_id

        replay = await service.apply_draft(
            user=user,
            draft_id=draft.draft_id,
            command=ApplyGoalDraftCommandV1(
                expected_draft_version=preview.draft_version,
                expected_preview_version=preview.preview_version,
                preview_id=preview.preview_id,
                boundary_mode="normal_boundary",
                set_focused=True,
                idempotency_key="goal-apply-001",
            ),
            correlation_id=uuid4(),
            now=now,
        )
        assert replay == applied

        activity_id = UUID(applied.activity_ref.entity_id)
        activity_states = ActivityLifecycleRepository(session)
        available = await activity_states.latest(activity_id)
        active_response = await ActivityLifecycleService(session).start(
            user=user,
            command=StartLearningActivityV1(
                activity_id=activity_id,
                expected_state_version=available.version,
                idempotency_key="goal-boundary-start-001",
            ),
            correlation_id=uuid4(),
            now=now,
        )
        detail = await service.get_goal_detail(user=user, goal_id=applied.goal_id)
        edit = await service.create_edit_draft(
            user=user,
            goal_id=applied.goal_id,
            command=CreateEditGoalDraftCommandV1(
                expected_state_version=detail.state.state_version,
                idempotency_key="goal-boundary-edit-001",
            ),
            correlation_id=uuid4(),
            now=now,
        )
        edit = await service.update_draft(
            user=user,
            draft_id=edit.draft_id,
            command=UpdateGoalDraftCommandV1(
                expected_draft_version=edit.draft_version,
                weekly_time_budget_minutes=120,
                idempotency_key="goal-boundary-budget-001",
            ),
            correlation_id=uuid4(),
            now=now,
        )
        boundary_preview = await service.preview_draft(
            user=user,
            draft_id=edit.draft_id,
            command=PreviewGoalDraftCommandV1(
                expected_draft_version=edit.draft_version,
                idempotency_key="goal-boundary-preview-001",
            ),
            correlation_id=uuid4(),
            now=now,
        )
        assert boundary_preview.effective_timing == "activity_boundary"
        pending = await service.apply_draft(
            user=user,
            draft_id=edit.draft_id,
            command=ApplyGoalDraftCommandV1(
                expected_draft_version=boundary_preview.draft_version,
                expected_preview_version=boundary_preview.preview_version,
                preview_id=boundary_preview.preview_id,
                boundary_mode="normal_boundary",
                set_focused=False,
                idempotency_key="goal-boundary-approve-001",
            ),
            correlation_id=uuid4(),
            now=now,
        )
        assert pending.status == "approved_pending_boundary"
        active = active_response.data.state
        await activity_states.append(
            active.model_copy(
                update={
                    "version": active.version + 1,
                    "status": "completed",
                    "previous_status": "active",
                    "transition_reason": "TEST_ACTIVITY_COMPLETED",
                    "completed_at": now,
                    "created_at": now,
                }
            )
        )
        next_ref = await service.apply_pending_at_boundary(
            user=user,
            completed_activity_id=activity_id,
            correlation_id=uuid4(),
            now=now,
        )
        assert next_ref is not None
        active_plans = (
            await session.scalars(
                select(LearningPlanRecord).where(
                    LearningPlanRecord.learning_goal_id == str(applied.goal_id),
                    LearningPlanRecord.status == "active",
                )
            )
        ).all()
        assert len(active_plans) == 1

        next_available = await activity_states.latest(UUID(next_ref.entity_id))
        assert next_available is not None
        next_active = await ActivityLifecycleService(session).start(
            user=user,
            command=StartLearningActivityV1(
                activity_id=UUID(next_ref.entity_id),
                expected_state_version=next_available.version,
                idempotency_key="goal-explicit-switch-start",
            ),
            correlation_id=uuid4(),
            now=now,
        )
        detail = await service.get_goal_detail(user=user, goal_id=applied.goal_id)
        explicit_edit = await service.create_edit_draft(
            user=user,
            goal_id=applied.goal_id,
            command=CreateEditGoalDraftCommandV1(
                expected_state_version=detail.state.state_version,
                idempotency_key="goal-explicit-switch-edit",
            ),
            correlation_id=uuid4(),
            now=now,
        )
        explicit_edit = await service.update_draft(
            user=user,
            draft_id=explicit_edit.draft_id,
            command=UpdateGoalDraftCommandV1(
                expected_draft_version=explicit_edit.draft_version,
                deadline_at=now,
                idempotency_key="goal-explicit-switch-deadline",
            ),
            correlation_id=uuid4(),
            now=now,
        )
        explicit_preview = await service.preview_draft(
            user=user,
            draft_id=explicit_edit.draft_id,
            command=PreviewGoalDraftCommandV1(
                expected_draft_version=explicit_edit.draft_version,
                idempotency_key="goal-explicit-switch-preview",
            ),
            correlation_id=uuid4(),
            now=now,
        )
        switched = await service.apply_draft(
            user=user,
            draft_id=explicit_edit.draft_id,
            command=ApplyGoalDraftCommandV1(
                expected_draft_version=explicit_preview.draft_version,
                expected_preview_version=explicit_preview.preview_version,
                preview_id=explicit_preview.preview_id,
                boundary_mode="supersede_active",
                set_focused=False,
                idempotency_key="goal-explicit-switch-apply",
            ),
            correlation_id=uuid4(),
            now=now,
        )
        assert switched.status == "applied"
        superseded = await activity_states.latest(next_active.data.state.activity_id)
        assert superseded is not None
        assert superseded.status == "superseded"
        assert superseded.completed_at is None
    await engine.dispose()


@pytest.mark.asyncio
async def test_processing_source_can_be_saved_but_blocks_preview(tmp_path) -> None:
    engine, factory = await _db(tmp_path)
    async with factory() as session:
        user = User(id=str(uuid4()), pseudonym_id="goal-waiting-owner")
        session.add(user)
        await session.commit()
        storage = LocalFileStorage(str(tmp_path / "documents"))
        documents = DocumentService(session)
        documents.storage = storage
        pending = await documents.upload_document(
            user.pseudonym_id, "pending.md", b"# Pending\n\nWaiting for processing."
        )
        service = GoalManagementService(session)
        now = datetime.now(timezone.utc)
        draft = await service.create_draft(
            user=user,
            command=CreateGoalDraftCommandV1(
                source_document_ids=(UUID(pending.id),),
                title="等待资料",
                topic="等待",
                target_capabilities=("解释",),
                success_criteria=(_criterion("独立解释等待资料中的核心概念"),),
                idempotency_key="goal-waiting-create",
            ),
            correlation_id=uuid4(),
            now=now,
        )
        assert draft.status == "draft"
        with pytest.raises(BusinessError) as blocked:
            await service.preview_draft(
                user=user,
                draft_id=draft.draft_id,
                command=PreviewGoalDraftCommandV1(
                    expected_draft_version=draft.draft_version,
                    idempotency_key="goal-waiting-preview",
                ),
                correlation_id=uuid4(),
                now=now,
            )
        assert blocked.value.error_code == "GOAL_SOURCE_NOT_EXECUTABLE"
    await engine.dispose()


@pytest.mark.asyncio
async def test_stale_preview_conflicts_without_replacing_current_plan(tmp_path) -> None:
    engine, factory = await _db(tmp_path)
    async with factory() as session:
        user = User(id=str(uuid4()), pseudonym_id="goal-stale-owner")
        session.add(user)
        await session.commit()
        storage = LocalFileStorage(str(tmp_path / "documents"))
        document = await _published_document(
            session, storage, user, "source.md", "能量守恒", "能量在封闭系统中守恒。"
        )
        service = GoalManagementService(session)
        draft = await service.create_draft(
            user=user,
            command=CreateGoalDraftCommandV1(
                source_document_ids=(UUID(document.id),),
                title="能量守恒",
                topic="物理",
                target_capabilities=("解释",),
                application_context=None,
                deadline_at=None,
                weekly_time_budget_minutes=60,
                success_criteria=(_criterion("独立解释能量守恒并解决一个新问题"),),
                idempotency_key="goal-stale-create",
            ),
            correlation_id=uuid4(),
            now=datetime.now(timezone.utc),
        )
        cards = await service.suggest_targets(user=user, draft_id=draft.draft_id)
        draft = await service.update_draft(
            user=user,
            draft_id=draft.draft_id,
            command=UpdateGoalDraftCommandV1(
                expected_draft_version=draft.draft_version,
                selected_target_ids=(cards[0].target_id,),
                targets_confirmed=True,
                idempotency_key="goal-stale-target",
            ),
            correlation_id=uuid4(),
            now=datetime.now(timezone.utc),
        )
        preview = await service.preview_draft(
            user=user,
            draft_id=draft.draft_id,
            command=PreviewGoalDraftCommandV1(
                expected_draft_version=draft.draft_version,
                idempotency_key="goal-stale-preview",
            ),
            correlation_id=uuid4(),
            now=datetime.now(timezone.utc),
        )
        latest = await service.get_draft(user=user, draft_id=draft.draft_id)
        await service.update_draft(
            user=user,
            draft_id=draft.draft_id,
            command=UpdateGoalDraftCommandV1(
                expected_draft_version=latest.draft_version,
                weekly_time_budget_minutes=120,
                idempotency_key="goal-stale-update",
            ),
            correlation_id=uuid4(),
            now=datetime.now(timezone.utc),
        )
        with pytest.raises(BusinessError) as stale:
            await service.apply_draft(
                user=user,
                draft_id=draft.draft_id,
                command=ApplyGoalDraftCommandV1(
                    expected_draft_version=preview.draft_version,
                    expected_preview_version=preview.preview_version,
                    preview_id=preview.preview_id,
                    boundary_mode="normal_boundary",
                    set_focused=False,
                    idempotency_key="goal-stale-apply",
                ),
                correlation_id=uuid4(),
                now=datetime.now(timezone.utc),
            )
        assert stale.value.error_code == "GOAL_PREVIEW_STALE"
    await engine.dispose()

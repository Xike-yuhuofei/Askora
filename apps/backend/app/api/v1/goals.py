"""Authenticated transport adapter for P1-01 SYS06 goal management."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import NAMESPACE_URL, UUID, uuid5

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.goal_management import (
    ApplyGoalDraftCommandV1,
    ConfirmGoalAchievementCommandV1,
    CreateEditGoalDraftCommandV1,
    CreateGoalDraftCommandV1,
    EvaluateGoalAchievementCommandV1,
    FocusedLearningGoalStateV1,
    GoalAchievementEvaluationV1,
    GoalAchievementWorkspaceV1,
    GoalApplyResultV1,
    GoalAssessmentActivityV1,
    GoalChangePreviewV1,
    GoalDetailV1,
    GoalLifecycleCommandV1,
    GoalLifecycleResultV1,
    GoalTargetCardsResponseV1,
    LearningGoalDraftV1,
    PreviewGoalDraftCommandV1,
    ScheduleGoalAssessmentsCommandV1,
    SubmitGoalAssessmentCommandV1,
    SuggestSuccessCriteriaRequestV1,
    SuggestSuccessCriteriaResponseV1,
    UpdateGoalDraftCommandV1,
)
from app.core.database import get_db
from app.models.user import User
from app.services.goal_management import GoalManagementService
from app.services.owner.dependencies import get_current_owner_projection

router = APIRouter(prefix="/goals", tags=["目标管理"])


def _correlation_id(request: Request) -> UUID:
    raw = request.headers.get("X-Correlation-ID") or str(
        getattr(request.state, "request_id", "unknown")
    )
    try:
        return UUID(raw)
    except ValueError:
        return uuid5(NAMESPACE_URL, f"askora:goal-http:{raw}")


def _now() -> datetime:
    return datetime.now(timezone.utc)


@router.post("/criteria/suggest", response_model=SuggestSuccessCriteriaResponseV1)
async def suggest_success_criteria(
    body: SuggestSuccessCriteriaRequestV1,
    current_user: User = Depends(get_current_owner_projection),
) -> SuggestSuccessCriteriaResponseV1:
    del current_user
    return GoalManagementService.suggest_criteria(
        topic=body.topic, cognitive_processes=body.cognitive_processes
    )


@router.post("/drafts", response_model=LearningGoalDraftV1, status_code=status.HTTP_201_CREATED)
async def create_goal_draft(
    body: CreateGoalDraftCommandV1,
    request: Request,
    current_user: User = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
) -> LearningGoalDraftV1:
    result = await GoalManagementService(db).create_draft(
        user=current_user,
        command=body,
        correlation_id=_correlation_id(request),
        now=_now(),
    )
    await db.commit()
    return result


@router.get("/drafts/{draft_id}", response_model=LearningGoalDraftV1)
async def get_goal_draft(
    draft_id: UUID,
    response: Response,
    current_user: User = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
) -> LearningGoalDraftV1:
    result = await GoalManagementService(db).get_draft(user=current_user, draft_id=draft_id)
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.patch("/drafts/{draft_id}", response_model=LearningGoalDraftV1)
async def update_goal_draft(
    draft_id: UUID,
    body: UpdateGoalDraftCommandV1,
    request: Request,
    current_user: User = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
) -> LearningGoalDraftV1:
    result = await GoalManagementService(db).update_draft(
        user=current_user,
        draft_id=draft_id,
        command=body,
        correlation_id=_correlation_id(request),
        now=_now(),
    )
    await db.commit()
    return result


@router.get("/drafts/{draft_id}/targets", response_model=GoalTargetCardsResponseV1)
async def get_goal_target_cards(
    draft_id: UUID,
    response: Response,
    current_user: User = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
) -> GoalTargetCardsResponseV1:
    service = GoalManagementService(db)
    draft = await service.get_draft(user=current_user, draft_id=draft_id)
    targets = await service.suggest_targets(user=current_user, draft_id=draft_id)
    response.headers["Cache-Control"] = "private, no-store"
    return GoalTargetCardsResponseV1(
        draft_id=draft_id, draft_version=draft.draft_version, targets=targets
    )


@router.post("/drafts/{draft_id}/preview", response_model=GoalChangePreviewV1)
async def preview_goal_draft(
    draft_id: UUID,
    body: PreviewGoalDraftCommandV1,
    request: Request,
    current_user: User = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
) -> GoalChangePreviewV1:
    result = await GoalManagementService(db).preview_draft(
        user=current_user,
        draft_id=draft_id,
        command=body,
        correlation_id=_correlation_id(request),
        now=_now(),
    )
    await db.commit()
    return result


@router.post("/drafts/{draft_id}/apply", response_model=GoalApplyResultV1)
async def apply_goal_draft(
    draft_id: UUID,
    body: ApplyGoalDraftCommandV1,
    request: Request,
    current_user: User = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
) -> GoalApplyResultV1:
    result = await GoalManagementService(db).apply_draft(
        user=current_user,
        draft_id=draft_id,
        command=body,
        correlation_id=_correlation_id(request),
        now=_now(),
    )
    await db.commit()
    return result


@router.post("/{goal_id}/drafts", response_model=LearningGoalDraftV1)
async def create_edit_goal_draft(
    goal_id: UUID,
    body: CreateEditGoalDraftCommandV1,
    request: Request,
    current_user: User = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
) -> LearningGoalDraftV1:
    result = await GoalManagementService(db).create_edit_draft(
        user=current_user,
        goal_id=goal_id,
        command=body,
        correlation_id=_correlation_id(request),
        now=_now(),
    )
    await db.commit()
    return result


@router.get("/focus", response_model=FocusedLearningGoalStateV1)
async def get_focused_goal(
    response: Response,
    current_user: User = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
) -> FocusedLearningGoalStateV1:
    result = await GoalManagementService(db).get_focused_goal(user=current_user)
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.post("/{goal_id}/pause", response_model=GoalLifecycleResultV1)
async def pause_goal(
    goal_id: UUID,
    body: GoalLifecycleCommandV1,
    request: Request,
    current_user: User = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
) -> GoalLifecycleResultV1:
    result = await GoalManagementService(db).pause_goal(
        user=current_user,
        goal_id=goal_id,
        command=body,
        correlation_id=_correlation_id(request),
        now=_now(),
    )
    await db.commit()
    return result


@router.post("/{goal_id}/resume", response_model=GoalLifecycleResultV1)
async def resume_goal(
    goal_id: UUID,
    body: GoalLifecycleCommandV1,
    request: Request,
    current_user: User = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
) -> GoalLifecycleResultV1:
    result = await GoalManagementService(db).resume_goal(
        user=current_user,
        goal_id=goal_id,
        command=body,
        correlation_id=_correlation_id(request),
        now=_now(),
    )
    await db.commit()
    return result


@router.post("/{goal_id}/archive", response_model=GoalLifecycleResultV1)
async def archive_goal(
    goal_id: UUID,
    body: GoalLifecycleCommandV1,
    request: Request,
    current_user: User = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
) -> GoalLifecycleResultV1:
    result = await GoalManagementService(db).archive_goal(
        user=current_user,
        goal_id=goal_id,
        command=body,
        correlation_id=_correlation_id(request),
        now=_now(),
    )
    await db.commit()
    return result


@router.post("/{goal_id}/copy", response_model=GoalLifecycleResultV1)
async def copy_archived_goal(
    goal_id: UUID,
    body: GoalLifecycleCommandV1,
    request: Request,
    current_user: User = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
) -> GoalLifecycleResultV1:
    result = await GoalManagementService(db).copy_archived_goal(
        user=current_user,
        goal_id=goal_id,
        command=body,
        correlation_id=_correlation_id(request),
        now=_now(),
    )
    await db.commit()
    return result


@router.post("/{goal_id}/assessments", response_model=GoalAchievementWorkspaceV1)
async def schedule_goal_assessments(
    goal_id: UUID,
    body: ScheduleGoalAssessmentsCommandV1,
    request: Request,
    current_user: User = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
) -> GoalAchievementWorkspaceV1:
    result = await GoalManagementService(db).schedule_goal_assessments(
        user=current_user,
        goal_id=goal_id,
        command=body,
        correlation_id=_correlation_id(request),
        now=_now(),
    )
    await db.commit()
    return result


@router.get("/{goal_id}/achievement", response_model=GoalAchievementWorkspaceV1)
async def get_goal_achievement_workspace(
    goal_id: UUID,
    response: Response,
    current_user: User = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
) -> GoalAchievementWorkspaceV1:
    result = await GoalManagementService(db).get_achievement_workspace(
        user=current_user, goal_id=goal_id, now=_now()
    )
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.post(
    "/{goal_id}/assessments/{activity_id}/submit",
    response_model=GoalAssessmentActivityV1,
)
async def submit_goal_assessment(
    goal_id: UUID,
    activity_id: UUID,
    body: SubmitGoalAssessmentCommandV1,
    request: Request,
    current_user: User = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
) -> GoalAssessmentActivityV1:
    result = await GoalManagementService(db).submit_goal_assessment(
        user=current_user,
        goal_id=goal_id,
        activity_id=activity_id,
        command=body,
        correlation_id=_correlation_id(request),
        now=_now(),
    )
    await db.commit()
    return result


@router.post("/{goal_id}/achievement/evaluate", response_model=GoalAchievementEvaluationV1)
async def evaluate_goal_achievement(
    goal_id: UUID,
    body: EvaluateGoalAchievementCommandV1,
    request: Request,
    current_user: User = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
) -> GoalAchievementEvaluationV1:
    result = await GoalManagementService(db).evaluate_goal_achievement(
        user=current_user,
        goal_id=goal_id,
        command=body,
        correlation_id=_correlation_id(request),
        now=_now(),
    )
    await db.commit()
    return result


@router.post("/{goal_id}/achieve", response_model=GoalLifecycleResultV1)
async def confirm_goal_achievement(
    goal_id: UUID,
    body: ConfirmGoalAchievementCommandV1,
    request: Request,
    current_user: User = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
) -> GoalLifecycleResultV1:
    result = await GoalManagementService(db).confirm_goal_achievement(
        user=current_user,
        goal_id=goal_id,
        command=body,
        correlation_id=_correlation_id(request),
        now=_now(),
    )
    await db.commit()
    return result


@router.get("/{goal_id}", response_model=GoalDetailV1)
async def get_goal_detail(
    goal_id: UUID,
    response: Response,
    current_user: User = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
) -> GoalDetailV1:
    result = await GoalManagementService(db).get_goal_detail(user=current_user, goal_id=goal_id)
    response.headers["Cache-Control"] = "private, no-store"
    return result

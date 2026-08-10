"""Minimal authenticated Book-to-Learning transport adapters."""

from __future__ import annotations

from collections.abc import Awaitable
from typing import NoReturn, TypeVar
from uuid import NAMESPACE_URL, UUID, uuid5

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.book_learning import (
    BookLearningApplication,
    BookLearningApplicationError,
)
from app.contracts.book_learning import (
    AdvanceBookLearningRequestV1,
    BookLearningOperationResponseV1,
    BookLearningReadinessV1,
    BookLearningTeachingResponseV1,
    BookLearningTranscriptV1,
    ConfirmBookLearningGoalRequestV1,
    CreateBookLearningGoalRequestV1,
    GenerateBookPlanRequestV1,
    MapBookLearningGoalRequestV1,
    SelectBookActivityRequestV1,
    StartBookDiagnosticRequestV1,
    StartBookTeachingRequestV1,
    SubmitBookDiagnosticResponseV1,
)
from app.contracts.recovery import RecoveryIssueViewV1
from app.core.database import get_db
from app.core.exceptions import BusinessError
from app.queries.recovery import RecoveryQueryService
from app.services.auth.dependencies import OwnerProjection, get_current_owner_projection
from app.services.recovery import RecoveryIncidentService

router = APIRouter(prefix="/book-learning", tags=["书籍自适应学习"])
T = TypeVar("T")


def get_book_learning_application(db: AsyncSession = Depends(get_db)) -> BookLearningApplication:
    return BookLearningApplication(db)


def _correlation_id(request: Request) -> UUID:
    raw = request.headers.get("X-Correlation-ID") or str(
        getattr(request.state, "request_id", "unknown")
    )
    try:
        return UUID(raw)
    except ValueError:
        return uuid5(NAMESPACE_URL, f"askora:http-correlation:{raw}")


async def _execute(command: Awaitable[T]) -> T:
    try:
        return await command
    except BookLearningApplicationError as exc:
        _raise_application_error(exc)
    except ValueError as exc:
        raise BusinessError(
            message=str(exc),
            error_code="BIZ-0023",
            status_code=status.HTTP_409_CONFLICT,
        ) from exc


def _raise_application_error(
    exc: BookLearningApplicationError,
    *,
    correlation_id: str | None = None,
    recovery_issue: RecoveryIssueViewV1 | None = None,
) -> NoReturn:
    code = exc.code
    status_code = (
        status.HTTP_429_TOO_MANY_REQUESTS
        if code == "AI_PROVIDER_RATE_LIMITED"
        else (
            status.HTTP_503_SERVICE_UNAVAILABLE
            if code.startswith(("POLICY_RUNTIME_", "AI_"))
            else status.HTTP_409_CONFLICT
        )
    )
    raise BusinessError(
        message=code,
        error_code=code,
        status_code=status_code,
        detail={"legacy_code": "BIZ-0023"},
        category=exc.category,
        retryable=exc.retryable,
        correlation_id=correlation_id,
        recovery={
            "issue_ref": recovery_issue.issue_ref if recovery_issue is not None else None,
            "retry_after_seconds": exc.retry_after_seconds,
            "actions": (
                [action.model_dump(mode="json") for action in recovery_issue.actions]
                if recovery_issue is not None
                else []
            ),
        },
    ) from exc


@router.get(
    "/{document_id}/readiness",
    response_model=BookLearningReadinessV1,
    summary="获取书籍学习就绪状态",
)
async def get_readiness(
    document_id: UUID,
    request: Request,
    response: Response,
    current_user: OwnerProjection = Depends(get_current_owner_projection),
    application: BookLearningApplication = Depends(get_book_learning_application),
) -> BookLearningReadinessV1:
    result = await application.readiness(
        user=current_user,
        document_id=document_id,
        correlation_id=str(_correlation_id(request)),
    )
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.post(
    "/{document_id}/advance",
    response_model=BookLearningOperationResponseV1,
    summary="安全推进一个无需用户输入的书籍学习步骤",
)
async def advance_book_learning(
    document_id: UUID,
    body: AdvanceBookLearningRequestV1,
    request: Request,
    current_user: OwnerProjection = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
    application: BookLearningApplication = Depends(get_book_learning_application),
) -> BookLearningOperationResponseV1:
    result = await _execute(
        application.advance(
            user=current_user,
            document_id=document_id,
            idempotency_key=body.idempotency_key,
            correlation_id=_correlation_id(request),
        )
    )
    await db.commit()
    return result


@router.get(
    "/goals/{goal_id}",
    response_model=BookLearningOperationResponseV1,
    summary="获取当前学习目标",
)
async def get_goal(
    goal_id: UUID,
    request: Request,
    response: Response,
    current_user: OwnerProjection = Depends(get_current_owner_projection),
    application: BookLearningApplication = Depends(get_book_learning_application),
) -> BookLearningOperationResponseV1:
    result = await _execute(
        application.get_goal(
            user=current_user, goal_id=goal_id, correlation_id=_correlation_id(request)
        )
    )
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.get(
    "/goals/{goal_id}/mapping",
    response_model=BookLearningOperationResponseV1,
    summary="获取当前目标知识映射",
)
async def get_mapping(
    goal_id: UUID,
    request: Request,
    response: Response,
    current_user: OwnerProjection = Depends(get_current_owner_projection),
    application: BookLearningApplication = Depends(get_book_learning_application),
) -> BookLearningOperationResponseV1:
    result = await _execute(
        application.get_mapping(
            user=current_user, goal_id=goal_id, correlation_id=_correlation_id(request)
        )
    )
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.get(
    "/goals/{goal_id}/diagnostic",
    response_model=BookLearningOperationResponseV1,
    summary="获取当前先修诊断状态",
)
async def get_diagnostic(
    goal_id: UUID,
    request: Request,
    response: Response,
    current_user: OwnerProjection = Depends(get_current_owner_projection),
    application: BookLearningApplication = Depends(get_book_learning_application),
) -> BookLearningOperationResponseV1:
    result = await _execute(
        application.get_diagnostic(
            user=current_user, goal_id=goal_id, correlation_id=_correlation_id(request)
        )
    )
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.get(
    "/goals/{goal_id}/plan",
    response_model=BookLearningOperationResponseV1,
    summary="获取当前学习计划与活动",
)
async def get_plan(
    goal_id: UUID,
    request: Request,
    response: Response,
    current_user: OwnerProjection = Depends(get_current_owner_projection),
    application: BookLearningApplication = Depends(get_book_learning_application),
) -> BookLearningOperationResponseV1:
    result = await _execute(
        application.get_plan(
            user=current_user, goal_id=goal_id, correlation_id=_correlation_id(request)
        )
    )
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.post(
    "/{document_id}/goals",
    response_model=BookLearningOperationResponseV1,
    summary="创建学习目标候选",
)
async def create_goal_candidate(
    document_id: UUID,
    body: CreateBookLearningGoalRequestV1,
    request: Request,
    current_user: OwnerProjection = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
    application: BookLearningApplication = Depends(get_book_learning_application),
) -> BookLearningOperationResponseV1:
    correlation_id = _correlation_id(request)
    result = await _execute(
        application.create_goal_candidate(
            user=current_user,
            document_id=document_id,
            intent=body.intent,
            application_context=body.application_context,
            deadline_at=body.deadline_at,
            weekly_time_budget_minutes=body.weekly_time_budget_minutes,
            idempotency_key=body.idempotency_key,
            correlation_id=correlation_id,
        )
    )
    await db.commit()
    return result


@router.post(
    "/goals/{goal_id}/confirm",
    response_model=BookLearningOperationResponseV1,
    summary="确认学习目标",
)
async def confirm_goal(
    goal_id: UUID,
    body: ConfirmBookLearningGoalRequestV1,
    request: Request,
    current_user: OwnerProjection = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
    application: BookLearningApplication = Depends(get_book_learning_application),
) -> BookLearningOperationResponseV1:
    result = await _execute(
        application.confirm_goal(
            user=current_user,
            goal_id=goal_id,
            confirmed_by_user=body.confirmed_by_user,
            idempotency_key=body.idempotency_key,
            correlation_id=_correlation_id(request),
        )
    )
    await db.commit()
    return result


@router.post(
    "/goals/{goal_id}/mapping",
    response_model=BookLearningOperationResponseV1,
    summary="映射目标并构建先修子图",
)
async def map_goal(
    goal_id: UUID,
    body: MapBookLearningGoalRequestV1,
    request: Request,
    current_user: OwnerProjection = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
    application: BookLearningApplication = Depends(get_book_learning_application),
) -> BookLearningOperationResponseV1:
    result = await _execute(
        application.map_goal(
            user=current_user,
            goal_id=goal_id,
            idempotency_key=body.idempotency_key,
            correlation_id=_correlation_id(request),
        )
    )
    await db.commit()
    return result


@router.post(
    "/diagnostics",
    response_model=BookLearningOperationResponseV1,
    summary="生成先修诊断与初始计划",
)
async def start_diagnostic(
    body: StartBookDiagnosticRequestV1,
    request: Request,
    current_user: OwnerProjection = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
    application: BookLearningApplication = Depends(get_book_learning_application),
) -> BookLearningOperationResponseV1:
    result = await _execute(
        application.start_diagnostic(
            user=current_user,
            mapping_id=body.mapping_id,
            mapping_version=body.mapping_version,
            subgraph_id=body.subgraph_id,
            subgraph_version=body.subgraph_version,
            target_knowledge_unit_id=body.target_knowledge_unit_id,
            max_attempts=body.max_attempts,
            idempotency_key=body.idempotency_key,
            correlation_id=_correlation_id(request),
        )
    )
    await db.commit()
    return result


@router.post(
    "/diagnostics/{need_id}/responses",
    response_model=BookLearningOperationResponseV1,
    summary="提交先修诊断回答",
)
async def submit_diagnostic_response(
    need_id: UUID,
    body: SubmitBookDiagnosticResponseV1,
    request: Request,
    current_user: OwnerProjection = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
    application: BookLearningApplication = Depends(get_book_learning_application),
) -> BookLearningOperationResponseV1:
    result = await _execute(
        application.submit_diagnostic_response(
            user=current_user,
            need_id=need_id,
            expected_need_version=body.expected_need_version,
            response=body.response,
            assistance=body.assistance,
            idempotency_key=body.idempotency_key,
            correlation_id=_correlation_id(request),
        )
    )
    await db.commit()
    return result


@router.post(
    "/plans",
    response_model=BookLearningOperationResponseV1,
    summary="生成或重放当前学习计划",
)
async def generate_plan(
    body: GenerateBookPlanRequestV1,
    request: Request,
    current_user: OwnerProjection = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
    application: BookLearningApplication = Depends(get_book_learning_application),
) -> BookLearningOperationResponseV1:
    result = await _execute(
        application.generate_plan(
            user=current_user,
            need_id=body.need_id,
            idempotency_key=body.idempotency_key,
            correlation_id=_correlation_id(request),
        )
    )
    await db.commit()
    return result


@router.post(
    "/activities/select",
    response_model=BookLearningOperationResponseV1,
    summary="选择下一个学习活动",
)
async def select_next_activity(
    body: SelectBookActivityRequestV1,
    request: Request,
    current_user: OwnerProjection = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
    application: BookLearningApplication = Depends(get_book_learning_application),
) -> BookLearningOperationResponseV1:
    result = await _execute(
        application.select_next_activity(
            user=current_user,
            goal_id=body.goal_id,
            idempotency_key=body.idempotency_key,
            correlation_id=_correlation_id(request),
        )
    )
    await db.commit()
    return result


@router.get(
    "/activities/{activity_id}/transcript",
    response_model=BookLearningTranscriptV1,
    summary="获取当前学习活动的可恢复教学记录",
)
async def get_activity_transcript(
    activity_id: UUID,
    request: Request,
    response: Response,
    current_user: OwnerProjection = Depends(get_current_owner_projection),
    application: BookLearningApplication = Depends(get_book_learning_application),
) -> BookLearningTranscriptV1:
    result = await _execute(
        application.get_transcript(
            user=current_user,
            activity_id=activity_id,
            correlation_id=_correlation_id(request),
        )
    )
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.post(
    "/activities/{activity_id}/start",
    response_model=BookLearningTeachingResponseV1,
    summary="进入 canonical 自适应教学回合",
)
async def start_teaching_round(
    activity_id: UUID,
    body: StartBookTeachingRequestV1,
    request: Request,
    current_user: OwnerProjection = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
    application: BookLearningApplication = Depends(get_book_learning_application),
) -> BookLearningTeachingResponseV1:
    if activity_id != body.activity_id:
        raise BusinessError(
            message="LEARNING_ACTIVITY_PATH_BODY_MISMATCH",
            error_code="BIZ-0023",
            status_code=status.HTTP_409_CONFLICT,
        )
    correlation_id = _correlation_id(request)
    try:
        result = await application.start_teaching_round(
            user=current_user,
            goal_id=body.goal_id,
            plan_id=body.plan_id,
            plan_version=body.plan_version,
            activity_id=activity_id,
            session_id=body.session_id,
            turn_id=body.turn_id,
            turn_kind=body.turn_kind,
            learner_text=body.learner_text,
            idempotency_key=body.idempotency_key,
            correlation_id=correlation_id,
        )
    except BookLearningApplicationError as exc:
        await db.rollback()
        recovery_issue = None
        if exc.code.startswith("AI_"):
            await RecoveryIncidentService(db).record_model_failure(
                current_user,
                activity_id=str(activity_id),
                code=exc.code,
                retryable=exc.retryable,
                retry_after_seconds=exc.retry_after_seconds,
                correlation_id=str(correlation_id),
            )
            recovery_issue = next(
                (
                    issue
                    for issue in (
                        await RecoveryQueryService(db).list_issues(
                            current_user, correlation_id=str(correlation_id)
                        )
                    ).issues
                    if issue.issue_ref == f"provider:{activity_id}"
                ),
                None,
            )
        _raise_application_error(
            exc,
            correlation_id=str(correlation_id),
            recovery_issue=recovery_issue,
        )
    await RecoveryIncidentService(db).resolve_model_issue(
        current_user,
        activity_id=str(activity_id),
        correlation_id=str(correlation_id),
    )
    await db.commit()
    return result

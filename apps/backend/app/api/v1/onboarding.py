"""P1-06 onboarding transport adapters."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.onboarding import (
    OnboardingJourneyViewV1,
    OnboardingPreferenceCommandV1,
)
from app.core.database import get_db
from app.models.user import User
from app.queries.onboarding import (
    DatabaseDataControlQuery,
    OnboardingJourneyQueryService,
)
from app.services.auth.dependencies import get_current_user
from app.services.llm.model_configuration import DatabaseModelConfigurationQuery
from app.services.onboarding import OnboardingPreferenceService

router = APIRouter(prefix="/onboarding", tags=["首次使用引导"])


def _correlation_id(request: Request) -> str:
    return str(getattr(request.state, "request_id", "unknown"))


@router.get(
    "/journey",
    response_model=OnboardingJourneyViewV1,
    summary="获取事实驱动的首次学习旅程",
)
async def get_onboarding_journey(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OnboardingJourneyViewV1:
    result = await OnboardingJourneyQueryService(
        db,
        model_configuration=DatabaseModelConfigurationQuery(db),
        data_control=DatabaseDataControlQuery(db),
    ).get_journey(
        current_user, correlation_id=_correlation_id(request)
    )
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.post(
    "/preferences",
    response_model=OnboardingJourneyViewV1,
    summary="更新首次引导展示偏好",
)
async def update_onboarding_preference(
    body: OnboardingPreferenceCommandV1,
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OnboardingJourneyViewV1:
    result = await OnboardingPreferenceService(
        db,
        model_configuration=DatabaseModelConfigurationQuery(db),
        data_control=DatabaseDataControlQuery(db),
    ).apply(
        user=current_user,
        command=body,
        correlation_id=_correlation_id(request),
    )
    response.headers["Cache-Control"] = "private, no-store"
    return result

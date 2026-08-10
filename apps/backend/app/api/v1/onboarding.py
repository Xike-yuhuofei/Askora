"""P1-06 onboarding transport adapters."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.onboarding import (
    OnboardingJourneyViewV1,
    OnboardingPreferenceCommandV1,
)
from app.core.database import get_db
from app.queries.onboarding import (
    DatabaseDataControlQuery,
    OnboardingJourneyQueryService,
    UnavailableModelConfigurationQuery,
)
from app.services.auth.dependencies import OwnerProjection, get_current_owner_projection
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
    current_user: OwnerProjection = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
) -> OnboardingJourneyViewV1:
    result = await OnboardingJourneyQueryService(
        db,
        model_configuration=UnavailableModelConfigurationQuery(),
        data_control=DatabaseDataControlQuery(db),
    ).get_journey(current_user, correlation_id=_correlation_id(request))
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
    current_user: OwnerProjection = Depends(get_current_owner_projection),
    db: AsyncSession = Depends(get_db),
) -> OnboardingJourneyViewV1:
    result = await OnboardingPreferenceService(
        db,
        model_configuration=UnavailableModelConfigurationQuery(),
        data_control=DatabaseDataControlQuery(db),
    ).apply(
        user=current_user,
        command=body,
        correlation_id=_correlation_id(request),
    )
    response.headers["Cache-Control"] = "private, no-store"
    return result

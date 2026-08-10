"""Presentation-only onboarding preference commands."""

from __future__ import annotations

import hashlib
import json

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.onboarding import (
    OnboardingJourneyViewV1,
    OnboardingPreferenceCommandV1,
)
from app.core.exceptions import BusinessError
from app.models.user import User
from app.queries.onboarding import (
    BOUNDARY_NOTICE_VERSION,
    JOURNEY_ID,
    DataControlQuery,
    ModelConfigurationQuery,
    OnboardingJourneyQueryService,
)


def _error(code: str, message: str, *, status_code: int = 409) -> BusinessError:
    return BusinessError(message=message, error_code=code, status_code=status_code)


class OnboardingPreferenceService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        journey_query: OnboardingJourneyQueryService | None = None,
        model_configuration: ModelConfigurationQuery | None = None,
        data_control: DataControlQuery | None = None,
    ) -> None:
        self._session = session
        self._journey = journey_query or OnboardingJourneyQueryService(
            session,
            model_configuration=model_configuration,
            data_control=data_control,
        )
        self._preferences = self._journey.preferences

    async def apply(
        self,
        *,
        user: User,
        command: OnboardingPreferenceCommandV1,
        correlation_id: str,
    ) -> OnboardingJourneyViewV1:
        digest = hashlib.sha256(
            json.dumps(
                command.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()
        receipt = await self._preferences.get_receipt(
            user_id=str(user.id),
            journey_id=command.journey_id,
            idempotency_key=command.idempotency_key,
        )
        if receipt is not None:
            if receipt.command_digest != digest:
                raise _error(
                    "ONBOARDING_PREFERENCE_VERSION_CONFLICT",
                    "重复请求使用了不同内容",
                )
            return await self._journey.get_journey(user, correlation_id=correlation_id)

        now = self._journey.now()
        await self._preferences.get_or_create_active(
            user_id=str(user.id), journey_id=JOURNEY_ID, now=now
        )
        record = await self._preferences.get(user_id=str(user.id), journey_id=JOURNEY_ID)
        if record is None:
            raise _error(
                "ONBOARDING_PREFERENCE_NOT_FOUND",
                "首次引导偏好暂时不可用",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if record.preference_version != command.expected_preference_version:
            raise _error(
                "ONBOARDING_PREFERENCE_VERSION_CONFLICT",
                "首次引导状态已更新，请刷新后重试",
            )

        values: dict[str, str | None] = {}
        if command.action == "ACKNOWLEDGE_BOUNDARIES":
            if command.notice_version != BOUNDARY_NOTICE_VERSION:
                raise _error(
                    "ONBOARDING_SCHEMA_UNSUPPORTED",
                    "数据与模型说明版本已更新，请刷新后确认",
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )
            values["boundary_notice_version_acknowledged"] = BOUNDARY_NOTICE_VERSION
        elif command.action == "DISMISS":
            values.update(visibility="DISMISSED", dismissed_reason="USER_DEFERRED")
        elif command.action == "REOPEN":
            values.update(visibility="ACTIVE", dismissed_reason=None)
        elif command.action == "FINISH_AND_DISMISS":
            current = await self._journey.get_journey(user, correlation_id=correlation_id)
            if current.journey_state != "COMPLETE":
                raise _error(
                    "ONBOARDING_COMPLETION_PRECONDITION_FAILED",
                    "第一项学习活动尚未完成",
                )
            values.update(visibility="DISMISSED", dismissed_reason="COMPLETED_JOURNEY")
        else:  # pragma: no cover - strict contract prevents unknown actions
            raise _error("ONBOARDING_SCHEMA_UNSUPPORTED", "不支持的首次引导动作")

        updated = await self._preferences.update_if_version(
            user_id=str(user.id),
            journey_id=JOURNEY_ID,
            expected_version=command.expected_preference_version,
            now=now,
            values=values,
        )
        if updated is None:
            concurrent_receipt = await self._preferences.get_receipt(
                user_id=str(user.id),
                journey_id=command.journey_id,
                idempotency_key=command.idempotency_key,
            )
            if concurrent_receipt is not None and concurrent_receipt.command_digest == digest:
                return await self._journey.get_journey(user, correlation_id=correlation_id)
            raise _error(
                "ONBOARDING_PREFERENCE_VERSION_CONFLICT",
                "首次引导状态已更新，请刷新后重试",
            )
        await self._preferences.append_receipt(
            user_id=str(user.id),
            journey_id=command.journey_id,
            idempotency_key=command.idempotency_key,
            command_digest=digest,
            action=command.action,
            resulting_preference_version=updated.preference_version,
            now=now,
        )
        return await self._journey.get_journey(user, correlation_id=correlation_id)

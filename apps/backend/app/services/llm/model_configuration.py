"""SYS08-owned model configuration query projection.

Reads the active runtime model router to report whether a provider is configured and
ready for canonical learning. This module is part of the model router domain (SYS08)
and is the only place that may touch router private state / provider credential
presence; onboarding depends on the clean ``ModelConfigurationQuery`` protocol and
falls back to static observations, never reaching into the router itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.adaptive import AvailabilityStatus
from app.models.user import User


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ModelConfigurationObservation:
    availability: AvailabilityStatus | str
    state: str | None = None
    revision: int | None = None
    runtime_ready: bool = False
    runtime_revision: int | None = None
    verified_at: datetime | None = None
    source_ref: str | None = None
    reason_codes: tuple[str, ...] = ()


class DatabaseModelConfigurationQuery:
    """Real model configuration query backed by the runtime model router."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_summary(self, user: User) -> ModelConfigurationObservation:
        del self, user
        try:
            from app.services.llm.model_router import get_model_router

            router = get_model_router()
            providers = router._providers
            available_providers = [
                p for p in providers.values() if getattr(p, "api_key", None)
            ]
            if not available_providers:
                return ModelConfigurationObservation(
                    availability="MISSING",
                    reason_codes=(),
                )
            return ModelConfigurationObservation(
                availability="AVAILABLE",
                state="ACTIVE",
                revision=1,
                runtime_ready=True,
                runtime_revision=1,
                verified_at=_now(),
                source_ref="ModelRouter:current",
                reason_codes=(),
            )
        except Exception as e:
            import logging

            logging.getLogger(__name__).error(
                "ModelConfigurationQuery error: %s", e, exc_info=True
            )
            return ModelConfigurationObservation(
                availability="MISSING",
                reason_codes=("MODEL_CONFIGURATION_QUERY_UNAVAILABLE",),
            )

"""Required evidence for safe onboarding degradation when SYS08 summary is unavailable."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.user import User
from app.queries.onboarding import (
    DataControlObservation,
    OnboardingJourneyQueryService,
    StaticDataControlQuery,
)

NOW = datetime(2026, 8, 10, 6, 30, tzinfo=timezone.utc)


@pytest.mark.required
@pytest.mark.sqlite_integration
@pytest.mark.asyncio
async def test_unavailable_sys08_summary_does_not_force_broken_welcome(tmp_path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'onboarding-degraded.db'}")
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            user = User(
                id=str(uuid4()),
                pseudonym_id=uuid4().hex,
                phone_hash=uuid4().hex,
                password_hash="hash",
            )
            session.add(user)
            await session.flush()

            query = OnboardingJourneyQueryService(
                session,
                data_control=StaticDataControlQuery(
                    DataControlObservation(
                        availability="AVAILABLE",
                        route="/settings/data",
                        source_ref="DataControlCapability:1",
                    )
                ),
                clock=lambda: NOW,
            )
            view = await query.get_journey(user, correlation_id="sys08-unavailable")

            assert view.journey_state == "PARTIAL"
            assert view.should_enter_welcome is False
            assert view.steps[0].state == "NOT_STARTED"
            assert view.steps[0].source_status[0].reason_codes == (
                "MODEL_CONFIGURATION_QUERY_UNAVAILABLE",
            )
    finally:
        await engine.dispose()

"""ONBOARD-AC-007/SEC-320 onboarding leakage and ownership evidence."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.contracts.onboarding import OnboardingPreferenceV1
from app.core.database import Base
from app.models.user import User

BACKEND = Path(__file__).resolve().parents[2]


def test_public_preference_has_no_secret_or_domain_reference_fields() -> None:
    fields = set(OnboardingPreferenceV1.model_fields)
    forbidden = {
        "api_key",
        "key_fragment",
        "prompt",
        "path",
        "document_ref",
        "goal_ref",
        "plan_ref",
        "activity_ref",
        "transcript_ref",
        "step_completion",
    }
    assert fields.isdisjoint(forbidden)


def test_onboarding_modules_do_not_read_environment_or_absolute_storage_path() -> None:
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            BACKEND / "app/contracts/onboarding.py",
            BACKEND / "app/queries/onboarding.py",
            BACKEND / "app/services/onboarding.py",
        )
    )
    assert "os.environ" not in text
    assert ".storage_path" not in text
    assert "api_key" not in text.lower()


@pytest.mark.asyncio
async def test_onboarding_http_is_authenticated_current_user_and_no_store(tmp_path) -> None:
    from httpx import ASGITransport, AsyncClient

    from app.core.database import get_db
    from app.main import app as fastapi_app
    from app.services.auth.dependencies import get_current_user

    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'http.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    user_id = str(uuid4())
    async with factory() as session:
        session.add(User(id=user_id, pseudonym_id=uuid4().hex))
        await session.commit()

    async def override_get_db():
        async with factory() as session:
            yield session
            await session.commit()

    async def override_get_current_user():
        async with factory() as session:
            user = await session.get(User, user_id)
            assert user is not None
            return user

    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[get_current_user] = override_get_current_user
    try:
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/onboarding/journey")
            assert response.status_code == 200, response.text
            assert response.headers["cache-control"] == "private, no-store"
            assert response.json()["schema_version"] == "1.0"

            del fastapi_app.dependency_overrides[get_current_user]
            unauthorized = await client.get("/api/v1/onboarding/journey")
            assert unauthorized.status_code == 401
            assert user_id not in unauthorized.text
    finally:
        fastapi_app.dependency_overrides.clear()
        await engine.dispose()

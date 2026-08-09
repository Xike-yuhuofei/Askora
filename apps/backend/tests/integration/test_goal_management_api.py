"""P1-01A authenticated API projection and privacy tests."""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app as fastapi_app
from app.models.user import User
from app.services.auth.dependencies import get_current_user


@pytest.mark.asyncio
async def test_goal_api_is_authenticated_versioned_and_private(tmp_path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'goal-api.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    user_id = str(uuid4())
    async with factory() as session:
        session.add(User(id=user_id, pseudonym_id="goal-api-owner"))
        await session.commit()

    async def override_get_db():
        async with factory() as session:
            yield session

    async def override_get_current_user():
        async with factory() as session:
            user = await session.get(User, user_id)
            assert user is not None
            return user

    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[get_current_user] = override_get_current_user
    try:
        async with AsyncClient(
            transport=ASGITransport(app=fastapi_app), base_url="http://test"
        ) as client:
            criteria = await client.post(
                "/api/v1/goals/criteria/suggest",
                json={"topic": "热力学", "cognitive_processes": ["recall", "apply"]},
            )
            focus = await client.get("/api/v1/goals/focus")
            missing = await client.get(f"/api/v1/goals/{uuid4()}")
        assert criteria.status_code == 200
        assert criteria.json()["schema_version"] == "1.0"
        assert [item["cognitive_process"] for item in criteria.json()["criteria"]] == [
            "recall",
            "apply",
        ]
        assert focus.status_code == 200
        assert focus.headers["cache-control"] == "private, no-store"
        assert focus.json()["goal_id"] is None
        assert missing.status_code == 404
        assert missing.json()["error"]["code"] == "DATA-0001"
    finally:
        fastapi_app.dependency_overrides.clear()
        await engine.dispose()

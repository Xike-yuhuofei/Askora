"""A provider failure response links to the durable owner-scoped issue."""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.v1.book_learning import get_book_learning_application
from app.application.book_learning import BookLearningApplicationError
from app.core.database import Base, get_db
from app.main import app as fastapi_app
from app.models.user import User
from app.services.auth.dependencies import get_current_user


class RateLimitedTeachingApplication:
    async def start_teaching_round(self, **_kwargs):
        raise BookLearningApplicationError(
            "AI_PROVIDER_RATE_LIMITED",
            category="transient",
            retryable=True,
            retry_after_seconds=17,
        )


@pytest.mark.asyncio
async def test_provider_error_envelope_links_the_persisted_recovery_issue(tmp_path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'entrypoint.db'}")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as session:
        owner = User(id=str(uuid4()), pseudonym_id="entrypoint-owner")
        session.add(owner)
        await session.commit()

        async def override_get_db():
            yield session

        async def override_get_current_user():
            return owner

        def override_application():
            return RateLimitedTeachingApplication()

        fastapi_app.dependency_overrides[get_db] = override_get_db
        fastapi_app.dependency_overrides[get_current_user] = override_get_current_user
        fastapi_app.dependency_overrides[get_book_learning_application] = override_application
        activity_id = uuid4()
        correlation_id = uuid4()
        try:
            async with AsyncClient(
                transport=ASGITransport(app=fastapi_app), base_url="http://test"
            ) as client:
                response = await client.post(
                    f"/api/v1/book-learning/activities/{activity_id}/start",
                    headers={"X-Correlation-ID": str(correlation_id)},
                    json={
                        "schema_version": "1.0",
                        "goal_id": str(uuid4()),
                        "plan_id": str(uuid4()),
                        "plan_version": 1,
                        "activity_id": str(activity_id),
                        "session_id": None,
                        "turn_id": "turn-rate-limited",
                        "turn_kind": "learner",
                        "learner_text": "请解释这个概念",
                        "idempotency_key": "rate-limited-entrypoint",
                    },
                )
        finally:
            fastapi_app.dependency_overrides.clear()

        assert response.status_code == 429
        error = response.json()["error"]
        assert error["code"] == "AI_PROVIDER_RATE_LIMITED"
        assert error["correlation_id"] == str(correlation_id)
        assert error["recovery"] == {
            "issue_ref": f"provider:{activity_id}",
            "retry_after_seconds": 17,
            "actions": [
                {
                    "action_code": "wait_until",
                    "label": "等待后再试",
                    "kind": "wait",
                    "enabled": True,
                    "disabled_reason_code": None,
                    "endpoint": None,
                    "method": None,
                    "route": None,
                    "requires_idempotency_key": False,
                    "requires_confirmation": False,
                },
                {
                    "action_code": "open_activity",
                    "label": "返回学习活动",
                    "kind": "navigate",
                    "enabled": True,
                    "disabled_reason_code": None,
                    "endpoint": None,
                    "method": None,
                    "route": f"/learn/{activity_id}",
                    "requires_idempotency_key": False,
                    "requires_confirmation": False,
                },
            ],
        }
    await engine.dispose()

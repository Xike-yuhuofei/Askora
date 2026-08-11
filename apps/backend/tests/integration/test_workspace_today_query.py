"""SQLite/API integration tests for the UI-01 Today workspace query."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.contracts.learning import ReviewSchedule
from app.contracts.workspace import CreateWorkspaceV1, WorkspaceTransitionGuardV1
from app.core.database import Base
from app.models.dialog import DialogSession, SessionStatus
from app.models.planning import ReviewScheduleRecord
from app.models.user import User
from app.queries.workspace import WorkspaceTodayQueryService
from app.services.local_identity import ensure_local_owner
from app.services.workspace.selection import WorkspaceSelectionService

NOW = datetime(2026, 8, 8, 1, 30, tzinfo=timezone.utc)


def _engine_and_factory(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'workspace.db'}")

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine, async_sessionmaker(engine, expire_on_commit=False)


def _review_record(
    *,
    user_id: str,
    workspace_id: str,
    knowledge_unit_id: str,
    version: int,
    due_at: datetime,
) -> ReviewScheduleRecord:
    schedule_id = uuid4()
    schedule = ReviewSchedule(
        schedule_id=schedule_id,
        version=version,
        user_id=user_id,
        knowledge_unit_id=knowledge_unit_id,
        memory_model="fsrs-compatible",
        model_version="1.0",
        desired_retention=0.9,
        next_due_at=due_at,
        review_priority=0.8,
        evidence_quality=0.75,
        source_event_ids=[],
        created_at=NOW - timedelta(days=1),
    )
    return ReviewScheduleRecord(
        id=f"{schedule_id}:{version}",
        schedule_id=str(schedule_id),
        user_id=user_id,
        workspace_id=workspace_id,
        knowledge_unit_id=knowledge_unit_id,
        version=version,
        next_due_at=due_at,
        payload=schedule.model_dump(mode="json"),
    )


@pytest.mark.asyncio
async def test_ui01_today_query_is_current_user_scoped_and_source_honest(tmp_path) -> None:
    """UI01/UI02B-AC-002/006: no cross-user leak or fake SYS06 state."""
    engine, factory = _engine_and_factory(tmp_path)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    user_id = str(uuid4())
    other_id = str(uuid4())
    workspace_id = str(uuid4())
    other_workspace_id = str(uuid4())
    due_unit = str(uuid4())
    future_unit = str(uuid4())
    async with factory() as session:
        user = User(id=user_id, pseudonym_id="workspace-user")
        other = User(id=other_id, pseudonym_id="other-user")
        session.add_all([user, other])
        session.add_all(
            [
                DialogSession(
                    id=str(uuid4()),
                    user_id=user_id,
                    workspace_id=workspace_id,
                    pseudonym_id=user.pseudonym_id,
                    subject="math",
                    knowledge_point_id="functions",
                    status=SessionStatus.ACTIVE,
                ),
                DialogSession(
                    id=str(uuid4()),
                    user_id=other_id,
                    workspace_id=other_workspace_id,
                    pseudonym_id=other.pseudonym_id,
                    subject="private-other",
                    status=SessionStatus.ACTIVE,
                ),
                _review_record(
                    user_id=user_id,
                    workspace_id=workspace_id,
                    knowledge_unit_id=due_unit,
                    version=1,
                    due_at=NOW - timedelta(hours=1),
                ),
                _review_record(
                    user_id=user_id,
                    workspace_id=workspace_id,
                    knowledge_unit_id=future_unit,
                    version=1,
                    due_at=NOW + timedelta(days=1),
                ),
                _review_record(
                    user_id=other_id,
                    workspace_id=other_workspace_id,
                    knowledge_unit_id=str(uuid4()),
                    version=1,
                    due_at=NOW - timedelta(days=1),
                ),
            ]
        )
        await session.commit()

        result = await WorkspaceTodayQueryService(
            session, workspace_id=workspace_id, clock=lambda: NOW
        ).get_today(
            user,
            timezone_name="Asia/Shanghai",
            correlation_id="request-1",
        )

    assert result.data.local_date.isoformat() == "2026-08-08"
    assert result.data.active_goal is None
    assert result.data.current_activity is None
    assert len(result.data.review_due_candidates) == 1
    assert due_unit in result.data.review_due_candidates[0].knowledge_unit_ref
    assert [item.subject for item in result.data.compatibility_quick_start.recent_sessions] == [
        "math"
    ]
    statuses = {item.source_system.value: item for item in result.source_status}
    assert statuses["SYS06"].availability.value == "MISSING"
    assert statuses["SYS06"].reason_codes == ("CURRENT_PLAN_NOT_AVAILABLE",)
    assert statuses["LEGACY_COMPATIBILITY"].availability.value == "AVAILABLE"
    await engine.dispose()


@pytest.mark.asyncio
async def test_ui01_today_http_contract_is_private_and_rejects_bad_timezone(tmp_path) -> None:
    """EXEC015-AC-002: HTTP response is strict, private, and validates timezone."""
    from httpx import ASGITransport, AsyncClient

    from app.core.database import get_db
    from app.main import app as fastapi_app
    from app.services.owner.dependencies import get_current_owner_projection

    engine, factory = _engine_and_factory(tmp_path)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    user_id = str(uuid4())
    async with factory() as session:
        session.add(User(id=user_id, pseudonym_id="workspace-http-user"))
        await session.commit()
        owner = await ensure_local_owner(session)
        await WorkspaceSelectionService(session).create(
            owner_id=owner.owner_id,
            command=CreateWorkspaceV1(
                display_name="测试课程",
                transition_guard=WorkspaceTransitionGuardV1(
                    composer_draft="CLEAR",
                    stream="CLEAR",
                    user_note="CLEAR",
                    material_position="PRESERVED",
                ),
                idempotency_key="workspace-today-http-course",
            ),
            correlation_id=uuid4(),
        )
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
    fastapi_app.dependency_overrides[get_current_owner_projection] = override_get_current_user
    try:
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/workspace/today", params={"timezone": "Asia/Shanghai"}
            )
            invalid = await client.get(
                "/api/v1/workspace/today", params={"timezone": "Not/A_Timezone"}
            )
        assert response.status_code == 200, response.text
        assert response.headers["cache-control"] == "private, no-store"
        assert response.json()["schema_version"] == "1.0"
        assert invalid.status_code == 422
        assert invalid.json()["error"]["code"] == "BIZ-0002"
    finally:
        fastapi_app.dependency_overrides.clear()
    await engine.dispose()

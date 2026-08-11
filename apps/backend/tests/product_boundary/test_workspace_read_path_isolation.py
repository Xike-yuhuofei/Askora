"""Conformance: UI read-path Workspace isolation (XIK-176 / EXEC067-AC-004).

Covers the read-only aggregation queries (goals / evidence / today) that must
never leak LearnerEvidence / Mastery / Review from another Workspace, and the
runtime boundary that ordinary local reading requires no Login/Redis/Postgres.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.contracts.learning import ReviewSchedule
from app.core.database import Base
from app.models.assessment import MasteryEstimateRecord
from app.models.dialog import DialogSession, SessionStatus
from app.models.planning import ReviewScheduleRecord
from app.models.user import User
from app.queries.workspace import WorkspaceTodayQueryService
from app.services.owner.canonical_identity import canonical_user_id

NOW = datetime(2026, 8, 11, 2, 0, tzinfo=timezone.utc)


def _engine_and_factory(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'workspace-read.db'}")

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


@pytest.mark.required
@pytest.mark.asyncio
async def test_read_path_evidence_mastery_and_review_are_workspace_isolated(tmp_path) -> None:
    """EXEC067-AC-004: the same LocalOwner + KU in different Workspaces never mixes."""
    engine, factory = _engine_and_factory(tmp_path)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    user = User(id="read-owner", pseudonym_id="read-path-user")
    owner_id = str(canonical_user_id(user.id))
    ws_a = str(uuid4())
    ws_b = str(uuid4())
    ku_a = str(uuid4())
    ku_b = str(uuid4())

    async with factory() as session:
        session.add(user)
        session.add_all(
            [
                MasteryEstimateRecord(
                    id=str(uuid4()),
                    user_id=owner_id,
                    workspace_id=ws_a,
                    knowledge_unit_id=ku_a,
                    version=1,
                    payload={"competence_probability": 0.9, "confidence": 0.8},
                ),
                MasteryEstimateRecord(
                    id=str(uuid4()),
                    user_id=owner_id,
                    workspace_id=ws_b,
                    knowledge_unit_id=ku_b,
                    version=1,
                    payload={"competence_probability": 0.1, "confidence": 0.2},
                ),
                _review_record(
                    user_id=owner_id,
                    workspace_id=ws_a,
                    knowledge_unit_id=ku_a,
                    version=1,
                    due_at=NOW - timedelta(hours=1),
                ),
                _review_record(
                    user_id=owner_id,
                    workspace_id=ws_b,
                    knowledge_unit_id=ku_b,
                    version=1,
                    due_at=NOW - timedelta(hours=1),
                ),
                DialogSession(
                    id=str(uuid4()),
                    user_id="read-owner",
                    workspace_id=ws_a,
                    pseudonym_id=user.pseudonym_id,
                    subject="workspace-a",
                    status=SessionStatus.ACTIVE,
                ),
                DialogSession(
                    id=str(uuid4()),
                    user_id="read-owner",
                    workspace_id=ws_b,
                    pseudonym_id=user.pseudonym_id,
                    subject="workspace-b",
                    status=SessionStatus.ACTIVE,
                ),
            ]
        )
        await session.commit()

        evidence_a = await WorkspaceTodayQueryService(
            session, workspace_id=ws_a, clock=lambda: NOW
        ).get_evidence(user, correlation_id="a")
        evidence_b = await WorkspaceTodayQueryService(
            session, workspace_id=ws_b, clock=lambda: NOW
        ).get_evidence(user, correlation_id="b")

        a_refs = {item.knowledge_unit_ref for item in evidence_a.data.entries}
        b_refs = {item.knowledge_unit_ref for item in evidence_b.data.entries}
        assert len(evidence_a.data.entries) == 1
        assert len(evidence_b.data.entries) == 1
        assert ku_a in next(iter(a_refs))  # entry belongs to Workspace A's KU
        assert ku_b in next(iter(b_refs))  # entry belongs to Workspace B's KU
        assert a_refs.isdisjoint(b_refs)  # no shared KU across Workspaces

        today_a = await WorkspaceTodayQueryService(
            session, workspace_id=ws_a, clock=lambda: NOW
        ).get_today(user, timezone_name="Asia/Shanghai", correlation_id="a")
        today_b = await WorkspaceTodayQueryService(
            session, workspace_id=ws_b, clock=lambda: NOW
        ).get_today(user, timezone_name="Asia/Shanghai", correlation_id="b")

        assert len(today_a.data.review_due_candidates) == 1
        assert ku_a in today_a.data.review_due_candidates[0].knowledge_unit_ref
        assert len(today_b.data.review_due_candidates) == 1
        assert ku_b in today_b.data.review_due_candidates[0].knowledge_unit_ref
        assert today_a.data.compatibility_quick_start.recent_sessions[0].subject == "workspace-a"
        assert today_b.data.compatibility_quick_start.recent_sessions[0].subject == "workspace-b"

    await engine.dispose()


@pytest.mark.required
@pytest.mark.asyncio
async def test_read_path_requires_exact_workspace_id(tmp_path) -> None:
    """A read-path query cannot be constructed without an exact Workspace scope."""
    engine, factory = _engine_and_factory(tmp_path)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    user = User(id="read-owner-2", pseudonym_id="read-path-user-2")
    async with factory() as session:
        session.add(user)
        await session.commit()
        with pytest.raises(TypeError):
            WorkspaceTodayQueryService(session, clock=lambda: NOW)  # type: ignore[call-arg]

    await engine.dispose()

"""EXEC-002 canonical dialog/orchestration behavior tests."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models  # noqa: F401
from app.core.database import Base
from app.models.dialog import DialogMessage, DialogSession, SessionStatus
from app.models.user import User, UserRole, UserStatus
from app.orchestration import CanonicalStreamEvent, CanonicalTurnRequest, CanonicalTurnResult
from app.services.dialog.dialog_service import DialogService


class RecordingFacade:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[tuple[str, CanonicalTurnRequest]] = []

    @staticmethod
    def _result(request: CanonicalTurnRequest) -> CanonicalTurnResult:
        return CanonicalTurnResult(
            reply_text="canonical reply",
            engine_id="socratic",
            flow_stage="learn",
            switched_to=None,
            decision_trace=("stay_in_current_engine",),
            engine_debug={
                "input_tokens": 3,
                "output_tokens": 5,
                "mastery_delta": 999.0,
            },
            execution_snapshot={
                "last_hint_level_used": 2,
                "mastery_vector": {"kp-1": 1.0},
            },
            correlation_id=request.correlation_id,
        )

    async def run_turn(self, request: CanonicalTurnRequest) -> CanonicalTurnResult:
        self.calls.append(("run", request))
        if self.fail:
            raise RuntimeError("provider unavailable")
        return self._result(request)

    async def stream_turn(
        self, request: CanonicalTurnRequest
    ) -> AsyncIterator[CanonicalStreamEvent]:
        self.calls.append(("stream", request))
        if self.fail:
            raise RuntimeError("provider unavailable")
        result = self._result(request)
        yield CanonicalStreamEvent(type="content", content=result.reply_text)
        yield CanonicalStreamEvent(type="final", result=result)


@pytest.fixture
async def canonical_dialog_db(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'canonical-dialog.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


async def _seed_dialog(db, *, suffix: str, mastery: float = 0.42):
    user = User(
        id=f"user-{suffix}",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        pseudonym_id=f"pseudo-{suffix}",
    )
    session = DialogSession(
        id=f"session-{suffix}",
        user_id=user.id,
        pseudonym_id=user.pseudonym_id,
        knowledge_point_id="kp-1",
        status=SessionStatus.ACTIVE,
        mastery_estimate=mastery,
    )
    db.add_all([user, session])
    await db.commit()
    return user, session


@pytest.mark.asyncio
async def test_api_ac_001_normal_and_stream_share_canonical_facade(canonical_dialog_db):
    """API-AC-001/SYS08-AC-001: both transports delegate to the canonical facade."""
    facade = RecordingFacade()
    user_normal, session_normal = await _seed_dialog(canonical_dialog_db, suffix="normal")
    user_stream, session_stream = await _seed_dialog(canonical_dialog_db, suffix="stream")

    normal = await DialogService(canonical_dialog_db, facade=facade).send_message(
        session_normal,
        user_normal,
        "same teaching input",
        correlation_id="corr-normal",
    )
    chunks = [
        chunk
        async for chunk in DialogService(
            canonical_dialog_db, facade=facade
        ).stream_message(
            session_stream,
            user_stream,
            "same teaching input",
            correlation_id="corr-stream",
        )
    ]

    assert [kind for kind, _request in facade.calls] == ["run", "stream"]
    assert {request.text for _kind, request in facade.calls} == {"same teaching input"}
    assert normal["message"]["strategy"] == chunks[-1]["strategy"] == "socratic"
    assert normal["message"]["content"] == chunks[-1]["response"] == "canonical reply"


@pytest.mark.asyncio
async def test_exec002_ac_003_engine_mastery_delta_cannot_change_dialog_mastery(
    canonical_dialog_db,
):
    """VSLICE-012: even an extreme legacy mastery_delta is execution-only data."""
    facade = RecordingFacade()
    user, session = await _seed_dialog(canonical_dialog_db, suffix="mastery", mastery=0.42)

    result = await DialogService(canonical_dialog_db, facade=facade).send_message(
        session,
        user,
        "inject a large mastery delta",
    )

    await canonical_dialog_db.refresh(session)
    assert session.mastery_estimate == 0.42
    assert result["session"]["mastery_estimate"] == 0.42
    assert result["session"]["mastery_semantics"] == "legacy_readonly_until_sys03_projection"


@pytest.mark.asyncio
async def test_exec002_ac_005_stream_reconnect_is_idempotent(canonical_dialog_db):
    """API-031: reconnect with the same key replays one persisted completion."""
    facade = RecordingFacade()
    user, session = await _seed_dialog(canonical_dialog_db, suffix="reconnect")
    service = DialogService(canonical_dialog_db, facade=facade)

    first = [
        chunk
        async for chunk in service.stream_message(
            session, user, "hello", idempotency_key="stream-key-1"
        )
    ]
    second = [
        chunk
        async for chunk in service.stream_message(
            session, user, "hello", idempotency_key="stream-key-1"
        )
    ]

    message_count = await canonical_dialog_db.scalar(
        select(func.count()).select_from(DialogMessage).where(DialogMessage.session_id == session.id)
    )
    assert len(facade.calls) == 1
    assert message_count == 2
    assert first[-1]["message_id"] == second[-1]["message_id"]
    assert second[-1]["idempotent_replay"] is True


@pytest.mark.asyncio
async def test_exec002_ac_006_model_failure_does_not_write_mastery_or_messages(
    canonical_dialog_db,
):
    """SYS05-AC-007: provider failure creates no learner state or dialog completion."""
    facade = RecordingFacade(fail=True)
    user, session = await _seed_dialog(canonical_dialog_db, suffix="failure", mastery=0.37)
    session_id = session.id

    with pytest.raises(RuntimeError, match="provider unavailable"):
        await DialogService(canonical_dialog_db, facade=facade).send_message(
            session,
            user,
            "this will fail",
        )

    persisted_session = await canonical_dialog_db.get(DialogSession, session_id)
    message_count = await canonical_dialog_db.scalar(
        select(func.count()).select_from(DialogMessage).where(DialogMessage.session_id == session_id)
    )
    assert persisted_session is not None
    assert persisted_session.mastery_estimate == 0.37
    assert message_count == 0

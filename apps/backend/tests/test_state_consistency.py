"""知识追踪和对话状态一致性的回归测试。"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models  # noqa: F401
from app.core.database import Base
from app.core.exceptions import SessionNotActiveError
from app.models.dialog import DialogMessage, DialogSession, MessageRole, SessionStatus
from app.models.user import User, UserRole, UserStatus
from app.services.dialog.dialog_service import DialogService
from app.services.documents.embedding_service import EmbeddingResult, EmbeddingService
from app.services.kt.knowledge_tracing_service import KnowledgeTracingService
from app.services.llm.model_router import ChatMessage, DoubaoProvider


class FailingRedis:
    def get(self, _key):
        raise ConnectionError("offline")

    def setex(self, _key, _ttl, _value):
        raise ConnectionError("offline")


def test_kt_memory_fallback_preserves_previous_update():
    service = KnowledgeTracingService()
    service._redis = FailingRedis()

    first = service.update_mastery("user-1", "kp-1", True)
    second = service.update_mastery("user-1", "kp-1", True)

    assert first.n_attempts == 1
    assert second.n_attempts == 2
    assert second.p > first.p


def test_embedding_cache_honors_configured_ttl():
    service = EmbeddingService()
    service._cache_ttl = 1
    fresh = EmbeddingResult("fresh", [1.0], "test", 1)
    stale = EmbeddingResult("stale", [1.0], "test", 1, created_at=time.monotonic() - 2)

    assert service._is_cache_expired(fresh) is False
    assert service._is_cache_expired(stale) is True


@pytest.mark.asyncio
async def test_doubao_stream_uses_remote_sse_when_key_is_configured(monkeypatch):
    class FakeResponse:
        async def __aenter__(self):
            return self

        async def __aexit__(self, _exc_type, _exc, _traceback):
            return False

        def raise_for_status(self):
            return None

        async def aiter_lines(self):
            yield 'data: {"choices":[{"delta":{"content":"你"}}]}'
            yield 'data: {"choices":[{"delta":{"content":"好"}}]}'
            yield "data: [DONE]"

    class FakeClient:
        def __init__(self):
            self.payload = None

        def stream(self, _method, _url, json):
            self.payload = json
            return FakeResponse()

    provider = DoubaoProvider()
    provider.api_key = "configured-test-key"
    fake_client = FakeClient()
    monkeypatch.setattr(provider, "_get_client", AsyncMock(return_value=fake_client))

    chunks = [
        chunk
        async for chunk in provider.stream_chat_completion(
            [ChatMessage(role="user", content="你好")]
        )
    ]

    assert "".join(chunk.content for chunk in chunks) == "你好"
    assert chunks[-1].is_final is True
    assert fake_client.payload["stream"] is True


@pytest.fixture
async def dialog_db(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'dialog.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_dialog_latest_history_returns_most_recent_in_chronological_order(dialog_db):
    user = User(
        id="user-1",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        pseudonym_id="pseudonym-1",
    )
    session = DialogSession(
        id="session-1",
        user_id=user.id,
        pseudonym_id=user.pseudonym_id,
        status=SessionStatus.ACTIVE,
    )
    dialog_db.add_all([user, session])
    start = datetime.now(timezone.utc)
    for index in range(25):
        dialog_db.add(
            DialogMessage(
                id=f"message-{index}",
                session_id=session.id,
                user_id=user.id,
                role=MessageRole.USER if index % 2 == 0 else MessageRole.ASSISTANT,
                content=str(index),
                turn_number=index // 2 + 1,
                created_at=start + timedelta(seconds=index),
            )
        )
    await dialog_db.commit()

    messages = await DialogService(dialog_db).get_session_messages(
        session.id,
        limit=20,
        latest=True,
    )

    assert [message.content for message in messages] == [str(i) for i in range(5, 25)]


@pytest.mark.asyncio
async def test_ended_dialog_rejects_new_message_before_engine_call(dialog_db):
    user = User(
        id="user-2",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        pseudonym_id="pseudonym-2",
    )
    session = DialogSession(
        id="session-2",
        user_id=user.id,
        pseudonym_id=user.pseudonym_id,
        status=SessionStatus.ENDED,
    )
    dialog_db.add_all([user, session])
    await dialog_db.commit()

    with pytest.raises(SessionNotActiveError):
        await DialogService(dialog_db).send_message(session, user, "不应写入")

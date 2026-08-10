"""
对话服务 - 会话管理与对话流转（简化版）
移除了内容审核依赖，仅保留核心会话管理与引擎交互
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.rendering import RenderPayloadV1, markdown_render_payload
from app.core.exceptions import SessionNotActiveError
from app.core.logging import get_logger
from app.core.redis_client import (
    RedisKeys,
    get_redis_client,
    is_redis_available,
    mark_redis_unavailable,
)
from app.models.dialog import (
    DialogMessage,
    DialogSession,
    MessageRole,
    SessionStatus,
)
from app.models.user import User
from app.orchestration import (
    CanonicalTurnRequest,
    CanonicalTurnResult,
    LearningOrchestrationFacade,
    get_learning_orchestration_facade,
)

logger = get_logger(__name__)
_session_message_locks: dict[str, asyncio.Lock] = {}


def _get_session_message_lock(session_id: str) -> asyncio.Lock:
    """私人单进程部署中的会话级写锁。数据库唯一约束提供第二层保护。"""
    return _session_message_locks.setdefault(session_id, asyncio.Lock())


class DialogService:
    """Legacy dialog transport adapter for the canonical learning facade."""

    def __init__(
        self,
        db: AsyncSession,
        facade: LearningOrchestrationFacade | None = None,
    ):
        self.db = db
        self.facade = facade or get_learning_orchestration_facade()

    async def create_session(
        self,
        user: User,
        subject: str = "general",
        knowledge_point_id: Optional[str] = None,
    ) -> DialogSession:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        session = DialogSession(
            id=session_id,
            user_id=user.id,
            pseudonym_id=user.pseudonym_id,
            subject=subject,
            knowledge_point_id=knowledge_point_id,
            status=SessionStatus.ACTIVE,
            current_hint_level=2,
            model_provider="qwen",
            model_name="qwen-turbo",
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        await self._cache_session_state(session)
        return session

    async def get_session(self, session_id: str) -> Optional[DialogSession]:
        """获取会话"""
        result = await self.db.execute(
            select(DialogSession).where(
                DialogSession.id == session_id,
                DialogSession.status != SessionStatus.DELETED,
            )
        )
        return result.scalar_one_or_none()

    async def get_user_sessions(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[DialogSession]:
        """获取用户的会话列表"""
        result = await self.db.execute(
            select(DialogSession)
            .where(
                DialogSession.user_id == user_id,
                DialogSession.status != SessionStatus.DELETED,
            )
            .order_by(DialogSession.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_session_messages(
        self,
        session_id: str,
        limit: int = 50,
        offset: int = 0,
        latest: bool = False,
    ) -> list[DialogMessage]:
        """获取会话消息列表"""
        order = DialogMessage.created_at.desc() if latest else DialogMessage.created_at.asc()
        result = await self.db.execute(
            select(DialogMessage)
            .where(DialogMessage.session_id == session_id)
            .order_by(order)
            .limit(limit)
            .offset(offset)
        )
        messages = list(result.scalars().all())
        return list(reversed(messages)) if latest else messages

    async def send_message(
        self,
        session: DialogSession,
        user: User,
        content: str,
        *,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> dict:
        """Execute a non-streaming turn through the canonical facade."""
        async with _get_session_message_lock(session.id):
            await self.db.refresh(session)
            if session.status != SessionStatus.ACTIVE:
                raise SessionNotActiveError()
            return await self._send_message_unlocked(
                session,
                user,
                content,
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
            )

    async def _send_message_unlocked(
        self,
        session: DialogSession,
        user: User,
        content: str,
        *,
        idempotency_key: str | None,
        correlation_id: str | None,
    ) -> dict:
        """Execute one canonical turn while holding the session write lock."""
        correlation = correlation_id or str(uuid.uuid4())
        user_message_id, assistant_message_id = self._turn_message_ids(session.id, idempotency_key)
        replay = await self._load_idempotent_completion(assistant_message_id)
        if replay is not None:
            return self._build_response_dict_from_message(
                session=session,
                ai_msg=replay,
                correlation_id=correlation,
                idempotent_replay=True,
            )

        try:
            await self._add_message(
                session=session,
                role=MessageRole.USER,
                content=content,
                message_id=user_message_id,
            )
            result = await self.facade.run_turn(
                self._build_turn_request(session, user, content, correlation)
            )
            return await self._complete_canonical_turn(
                session=session,
                result=result,
                assistant_message_id=assistant_message_id,
            )
        except Exception:
            await self.db.rollback()
            raise

    @staticmethod
    def _build_response_dict_from_orchestrator(
        *, session: DialogSession, ai_msg: DialogMessage, result: CanonicalTurnResult
    ) -> dict:
        usage = result.engine_debug
        return {
            "session": {
                "id": session.id,
                "turn_count": session.turn_count,
                "current_hint_level": session.current_hint_level,
                "mastery_estimate": session.mastery_estimate,
                "orchestrator_engine_id": result.engine_id,
                "orchestrator_switched_to": result.switched_to,
                "mastery_semantics": "legacy_readonly_until_sys03_projection",
            },
            "message": {
                "id": ai_msg.id,
                "role": ai_msg.role.value,
                "content": ai_msg.content,
                "render_payload": ai_msg.render_payload,
                "turn_number": ai_msg.turn_number,
                "strategy": ai_msg.strategy,
                "hint_level": ai_msg.hint_level,
                "created_at": ai_msg.created_at.isoformat(),
            },
            "usage": {
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
                "ttft_ms": usage.get("ttft_ms"),
                "generation_ms": usage.get("generation_ms", 0),
            },
            "correlation_id": result.correlation_id,
            "idempotent_replay": False,
        }

    @staticmethod
    def _build_response_dict_from_message(
        *,
        session: DialogSession,
        ai_msg: DialogMessage,
        correlation_id: str,
        idempotent_replay: bool,
    ) -> dict:
        return {
            "session": {
                "id": session.id,
                "turn_count": session.turn_count,
                "current_hint_level": session.current_hint_level,
                "mastery_estimate": session.mastery_estimate,
                "mastery_semantics": "legacy_readonly_until_sys03_projection",
                "orchestrator_engine_id": ai_msg.strategy,
                "orchestrator_switched_to": None,
            },
            "message": {
                "id": ai_msg.id,
                "role": ai_msg.role.value,
                "content": ai_msg.content,
                "render_payload": ai_msg.render_payload,
                "turn_number": ai_msg.turn_number,
                "strategy": ai_msg.strategy,
                "hint_level": ai_msg.hint_level,
                "created_at": ai_msg.created_at.isoformat(),
            },
            "usage": {
                "input_tokens": ai_msg.input_tokens,
                "output_tokens": ai_msg.output_tokens,
                "total_tokens": ai_msg.total_tokens,
                "ttft_ms": ai_msg.ttft_ms,
                "generation_ms": ai_msg.generation_ms,
            },
            "correlation_id": correlation_id,
            "idempotent_replay": idempotent_replay,
        }

    async def _complete_canonical_turn(
        self,
        *,
        session: DialogSession,
        result: CanonicalTurnResult,
        assistant_message_id: str,
    ) -> dict:
        usage = result.engine_debug
        render_payload = result.render_payload or markdown_render_payload(result.reply_text)
        ai_msg = await self._add_message(
            session=session,
            role=MessageRole.ASSISTANT,
            content=result.reply_text,
            render_payload=render_payload,
            message_id=assistant_message_id,
            strategy=result.engine_id,
            hint_level=result.execution_snapshot.get("last_hint_level_used"),
            input_tokens=int(usage.get("input_tokens", 0)),
            output_tokens=int(usage.get("output_tokens", 0)),
            total_tokens=int(usage.get("input_tokens", 0)) + int(usage.get("output_tokens", 0)),
            ttft_ms=usage.get("ttft_ms"),
            generation_ms=usage.get("generation_ms", 0),
        )
        session.turn_count += 1
        session.total_tokens += ai_msg.total_tokens
        session.current_strategy = result.engine_id
        session.current_hint_level = result.execution_snapshot.get(
            "last_hint_level_used", session.current_hint_level
        )
        # VSLICE-012: Dialog/Orchestrator execution state never writes canonical mastery.
        session.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self._cache_session_state(session)
        return self._build_response_dict_from_orchestrator(
            session=session,
            ai_msg=ai_msg,
            result=result,
        )

    def _build_turn_request(
        self,
        session: DialogSession,
        user: User,
        content: str,
        correlation_id: str,
    ) -> CanonicalTurnRequest:
        return CanonicalTurnRequest(
            session_id=session.id,
            user_id=user.id,
            text=content,
            turn_id=f"dialog_turn_{session.turn_count + 1}",
            subject=session.subject,
            knowledge_point_id=session.knowledge_point_id,
            learner_persona=self._infer_learner_persona(session),
            correlation_id=correlation_id,
        )

    @staticmethod
    def _turn_message_ids(session_id: str, idempotency_key: str | None) -> tuple[str, str]:
        if not idempotency_key:
            return str(uuid.uuid4()), str(uuid.uuid4())
        scope = f"askora-dialog:{session_id}:{idempotency_key}"
        return (
            str(uuid.uuid5(uuid.NAMESPACE_URL, f"{scope}:user")),
            str(uuid.uuid5(uuid.NAMESPACE_URL, f"{scope}:assistant")),
        )

    async def _load_idempotent_completion(self, message_id: str) -> DialogMessage | None:
        result = await self.db.execute(
            select(DialogMessage).where(
                DialogMessage.id == message_id,
                DialogMessage.role == MessageRole.ASSISTANT,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _infer_learner_persona(session: DialogSession) -> str:
        """从 session 元数据推断 learner_persona"""
        metadata = getattr(session, "metadata", None) or {}
        if isinstance(metadata, dict) and metadata.get("learner_persona"):
            return str(metadata["learner_persona"])
        return "k12_high"

    async def stream_message(
        self,
        session: DialogSession,
        user: User,
        content: str,
        *,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ):
        """Execute a streaming transport over the canonical teaching path."""

        async with _get_session_message_lock(session.id):
            await self.db.refresh(session)
            if session.status != SessionStatus.ACTIVE:
                raise SessionNotActiveError()
            async for chunk in self._stream_message_unlocked(
                session,
                user,
                content,
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
            ):
                yield chunk

    async def _stream_message_unlocked(
        self,
        session: DialogSession,
        user: User,
        content: str,
        *,
        idempotency_key: str | None,
        correlation_id: str | None,
    ):
        """Adapt canonical facade events without a direct Socratic streaming path."""
        correlation = correlation_id or str(uuid.uuid4())
        user_message_id, assistant_message_id = self._turn_message_ids(session.id, idempotency_key)
        replay = await self._load_idempotent_completion(assistant_message_id)
        if replay is not None:
            yield {"type": "content", "content": replay.content}
            yield {
                "type": "final",
                "response": replay.content,
                "render_payload": replay.render_payload,
                "strategy": replay.strategy,
                "hint_level": replay.hint_level,
                "message_id": replay.id,
                "correlation_id": correlation,
                "idempotent_replay": True,
            }
            return

        try:
            await self._add_message(
                session=session,
                role=MessageRole.USER,
                content=content,
                message_id=user_message_id,
            )
            result: CanonicalTurnResult | None = None
            async for event in self.facade.stream_turn(
                self._build_turn_request(session, user, content, correlation)
            ):
                if event.type == "content":
                    yield {"type": "content", "content": event.content}
                elif event.type == "final":
                    result = event.result
            if result is None:
                raise RuntimeError("canonical stream completed without a final result")
            response = await self._complete_canonical_turn(
                session=session,
                result=result,
                assistant_message_id=assistant_message_id,
            )
            yield {
                "type": "final",
                "response": result.reply_text,
                "render_payload": response["message"]["render_payload"],
                "strategy": result.engine_id,
                "hint_level": session.current_hint_level,
                "message_id": response["message"]["id"],
                "correlation_id": correlation,
                "idempotent_replay": False,
            }
        except Exception:
            await self.db.rollback()
            raise

    async def _add_message(
        self,
        session: DialogSession,
        role: MessageRole,
        content: str,
        render_payload: RenderPayloadV1 | None = None,
        message_id: str | None = None,
        strategy: Optional[str] = None,
        hint_level: Optional[int] = None,
        intent: Optional[str] = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        total_tokens: int = 0,
        ttft_ms: Optional[int] = None,
        generation_ms: Optional[int] = None,
    ) -> DialogMessage:
        """添加消息到会话"""
        msg = DialogMessage(
            id=message_id or str(uuid.uuid4()),
            session_id=session.id,
            user_id=session.user_id,
            role=role,
            content=content,
            render_payload=(
                render_payload.model_dump(mode="json") if render_payload is not None else None
            ),
            turn_number=session.turn_count + 1,
            strategy=strategy,
            hint_level=hint_level,
            intent=intent,
            moderation_result={},
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            ttft_ms=ttft_ms,
            generation_ms=generation_ms,
        )
        self.db.add(msg)
        await self.db.flush()
        return msg

    async def end_session(self, session: DialogSession) -> DialogSession:
        """结束会话"""
        if session.status == SessionStatus.ENDED:
            return session
        session.status = SessionStatus.ENDED
        session.ended_at = datetime.now(timezone.utc)
        created_at = session.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        session.duration_seconds = int((session.ended_at - created_at).total_seconds())
        await self.db.commit()

        if is_redis_available() is False:
            return session

        try:
            redis = get_redis_client()
            if redis is None:
                return session
            key = RedisKeys.format(RedisKeys.SESSION, session_id=session.id)
            await redis.delete(key)
        except Exception as e:
            mark_redis_unavailable()
            logger.warning(
                "redis_session_cache_delete_failed",
                session_id=session.id,
                error_type=type(e).__name__,
            )

        return session

    async def _cache_session_state(self, session: DialogSession) -> None:
        """缓存会话状态到 Redis"""
        if is_redis_available() is False:
            return
        try:
            redis = get_redis_client()
            if redis is None:
                return
            key = RedisKeys.format(RedisKeys.SESSION, session_id=session.id)

            state = {
                "id": session.id,
                "user_id": session.user_id,
                "pseudonym_id": session.pseudonym_id,
                "subject": session.subject,
                "status": session.status.value,
                "current_hint_level": session.current_hint_level,
                "current_strategy": session.current_strategy,
                "mastery_estimate": session.mastery_estimate,
                "turn_count": session.turn_count,
            }

            import json

            await redis.setex(
                key,
                RedisKeys.SESSION_TTL,
                json.dumps(state, ensure_ascii=False),
            )
        except Exception as e:
            mark_redis_unavailable()
            logger.warning(
                "redis_session_cache_failed",
                session_id=session.id,
                error_type=type(e).__name__,
            )

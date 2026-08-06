"""
对话服务 - 会话管理与对话流转（简化版）
移除了内容审核依赖，仅保留核心会话管理与引擎交互
"""

from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
from app.services.dialog.socratic_engine import (
    EngineInput,
    EngineOutput,
    SocraticEngine,
    get_socratic_engine,
)

# Orchestrator 接入点
try:
    from app.engines import FlowStage, LearnerTurn, OrchestratorTurnResult, get_orchestrator

    _ORCHESTRATOR_AVAILABLE = True
except Exception as _import_exc:
    _ORCHESTRATOR_AVAILABLE = False
    logger = get_logger(__name__)
    logger.warning("orchestrator_import_failed", error_type=type(_import_exc).__name__)

logger = get_logger(__name__)
_session_message_locks: dict[str, asyncio.Lock] = {}


def _get_session_message_lock(session_id: str) -> asyncio.Lock:
    """私人单进程部署中的会话级写锁。数据库唯一约束提供第二层保护。"""
    return _session_message_locks.setdefault(session_id, asyncio.Lock())


def _should_use_orchestrator(session: DialogSession) -> bool:
    """判断当前会话是否走 Orchestrator 路径"""
    if not _ORCHESTRATOR_AVAILABLE:
        return False
    metadata = getattr(session, "metadata", None) or {}
    if isinstance(metadata, dict) and metadata.get("use_orchestrator"):
        return True
    return os.environ.get("ASKORA_USE_ORCHESTRATOR", "").lower() in {"1", "true", "yes", "on"}


class DialogService:
    """对话服务（简化版）"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.engine: Optional[SocraticEngine] = None

    def _get_engine(self) -> SocraticEngine:
        if self.engine is None:
            self.engine = get_socratic_engine()
        return self.engine

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
    ) -> dict:
        """发送消息并获取 AI 回复"""
        async with _get_session_message_lock(session.id):
            await self.db.refresh(session)
            if session.status != SessionStatus.ACTIVE:
                raise SessionNotActiveError()
            return await self._send_message_unlocked(session, user, content)

    async def _send_message_unlocked(
        self,
        session: DialogSession,
        user: User,
        content: str,
    ) -> dict:
        """在已持有会话写锁的情况下执行一轮非流式对话。"""
        # 1. 保存用户消息
        await self._add_message(
            session=session,
            role=MessageRole.USER,
            content=content,
        )

        # 2. 获取对话历史
        history = await self.get_session_messages(session.id, limit=20, latest=True)

        # 3. 判断是否走 Orchestrator 路径
        use_orch = _should_use_orchestrator(session)
        if use_orch:
            orchestrator_result = await self._run_via_orchestrator(
                session=session,
                user=user,
                content=content,
                history=history,
            )
            logger.info("dialog_orchestrator_path_hit", session_id=session.id)
            return orchestrator_result

        # 4. 调用引擎生成回复
        engine_output = await self._run_via_socratic_direct(
            session=session,
            user=user,
            content=content,
            history=history,
        )

        # 5. 保存 AI 消息
        ai_msg = await self._add_message(
            session=session,
            role=MessageRole.ASSISTANT,
            content=engine_output.response,
            strategy=engine_output.strategy,
            hint_level=engine_output.hint_level,
            input_tokens=engine_output.input_tokens,
            output_tokens=engine_output.output_tokens,
            total_tokens=engine_output.total_tokens,
            generation_ms=engine_output.generation_ms,
        )

        # 6. 更新会话状态
        session.turn_count += 1
        session.total_tokens += engine_output.total_tokens
        session.current_hint_level = engine_output.next_hint_level
        session.current_strategy = engine_output.strategy
        session.mastery_estimate = max(
            0.0, min(1.0, session.mastery_estimate + engine_output.mastery_delta)
        )
        session.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self._cache_session_state(session)

        return self._build_response_dict(
            session=session,
            ai_msg=ai_msg,
            engine_output=engine_output,
        )

    async def _run_via_socratic_direct(
        self,
        session: DialogSession,
        user: User,
        content: str,
        history: list[DialogMessage],
    ) -> EngineOutput:
        """直接调用 SocraticEngine"""
        engine = self._get_engine()
        engine_input = EngineInput(
            session_id=session.id,
            user_id=user.id,
            user_input=content,
            turn_number=session.turn_count + 1,
            subject=session.subject,
            knowledge_point_id=session.knowledge_point_id,
            hint_level=session.current_hint_level,
        )
        return await engine.generate_response(
            input_data=engine_input,
            conversation_history=history,
        )

    async def _run_via_orchestrator(
        self,
        session: DialogSession,
        user: User,
        content: str,
        history: list[DialogMessage],
    ) -> dict:
        """通过 Orchestrator 调度引擎"""
        if not _ORCHESTRATOR_AVAILABLE:
            raise RuntimeError("orchestrator not available")

        orchestrator = get_orchestrator()

        # 确保 Orchestrator session 存在
        orch_sessions = getattr(orchestrator, "_sessions", {})
        if session.id not in orch_sessions:
            await orchestrator.create_session(
                session_id=session.id,
                subject=session.subject,
                knowledge_point_id=session.knowledge_point_id,
                initial_stage=FlowStage.LEARN,
                learner_persona=self._infer_learner_persona(session),
                learner_preferences={},
                extras={
                    "user_id": user.id,
                    "pseudonym_id": session.pseudonym_id,
                    "source": "dialog_service",
                },
            )
            logger.info("dialog_orchestrator_session_auto_created", session_id=session.id)

        # 组装 LearnerTurn
        history_tail: list = []
        for m in history[-5:]:
            history_tail.append((m.role.value, m.content))

        learner_turn = LearnerTurn(
            text=content.strip(),
            turn_id=f"dialog_turn_{session.turn_count + 1}",
            attachments=[],
        )

        # 调用 Orchestrator
        result: OrchestratorTurnResult = await orchestrator.run_turn(
            session_id=session.id,
            learner_turn=learner_turn,
        )

        # 保存 AI 消息
        ai_msg = await self._add_message(
            session=session,
            role=MessageRole.ASSISTANT,
            content=result.reply_text,
            strategy=result.engine_id,
            hint_level=None,
            input_tokens=result.engine_debug.get("input_tokens", 0),
            output_tokens=result.engine_debug.get("output_tokens", 0),
            total_tokens=result.engine_debug.get("input_tokens", 0)
            + result.engine_debug.get("output_tokens", 0),
            generation_ms=result.engine_debug.get("generation_ms", 0),
        )

        # 更新会话状态
        session.turn_count += 1
        usage = result.engine_debug
        session.total_tokens += usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
        session.current_strategy = result.engine_id
        snapshot = result.shared_ctx_snapshot
        session.current_hint_level = snapshot.get(
            "last_hint_level_used", session.current_hint_level
        )
        session.mastery_estimate = float(
            snapshot.get("mastery_vector", {}).get(
                session.knowledge_point_id or "", session.mastery_estimate
            )
        )
        session.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self._cache_session_state(session)

        return self._build_response_dict_from_orchestrator(
            session=session,
            ai_msg=ai_msg,
            result=result,
        )

    @staticmethod
    def _build_response_dict(
        *, session: DialogSession, ai_msg: DialogMessage, engine_output: EngineOutput
    ) -> dict:
        return {
            "session": {
                "id": session.id,
                "turn_count": session.turn_count,
                "current_hint_level": session.current_hint_level,
                "mastery_estimate": session.mastery_estimate,
            },
            "message": {
                "id": ai_msg.id,
                "role": ai_msg.role.value,
                "content": ai_msg.content,
                "turn_number": ai_msg.turn_number,
                "strategy": ai_msg.strategy,
                "hint_level": ai_msg.hint_level,
                "created_at": ai_msg.created_at.isoformat(),
            },
            "usage": {
                "input_tokens": engine_output.input_tokens,
                "output_tokens": engine_output.output_tokens,
                "total_tokens": engine_output.total_tokens,
                "ttft_ms": engine_output.ttft_ms,
                "generation_ms": engine_output.generation_ms,
            },
        }

    @staticmethod
    def _build_response_dict_from_orchestrator(
        *, session: DialogSession, ai_msg: DialogMessage, result: OrchestratorTurnResult
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
            },
            "message": {
                "id": ai_msg.id,
                "role": ai_msg.role.value,
                "content": ai_msg.content,
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
        }

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
    ):
        """流式对话"""

        async with _get_session_message_lock(session.id):
            await self.db.refresh(session)
            if session.status != SessionStatus.ACTIVE:
                raise SessionNotActiveError()
            async for chunk in self._stream_message_unlocked(session, user, content):
                yield chunk

    async def _stream_message_unlocked(
        self,
        session: DialogSession,
        user: User,
        content: str,
    ):
        """在已持有会话写锁的情况下执行一轮流式对话。"""
        import time

        start_time = time.time()

        # 保存用户消息
        await self._add_message(
            session=session,
            role=MessageRole.USER,
            content=content,
        )

        # 获取对话历史
        history = await self.get_session_messages(session.id, limit=20, latest=True)

        # 流式调用引擎
        engine = self._get_engine()
        engine_input = EngineInput(
            session_id=session.id,
            user_id=user.id,
            user_input=content,
            turn_number=session.turn_count + 1,
            subject=session.subject,
            knowledge_point_id=session.knowledge_point_id,
            hint_level=session.current_hint_level,
        )

        full_response = ""
        ttft_ms = None
        strategy = None
        hint_level = session.current_hint_level

        async for chunk in engine.stream_response(
            input_data=engine_input,
            conversation_history=history,
        ):
            chunk_type = chunk.get("type")

            if chunk_type == "content":
                full_response += chunk.get("content", "")
                if ttft_ms is None and chunk.get("content"):
                    ttft_ms = int((time.time() - start_time) * 1000)
                yield {
                    "type": "content",
                    "content": chunk.get("content", ""),
                }

            elif chunk_type == "final":
                full_response = chunk.get("response", full_response)
                strategy = chunk.get("strategy")
                hint_level = chunk.get("hint_level", hint_level)
                ttft_ms = chunk.get("ttft_ms", ttft_ms)
                yield {
                    "type": "final",
                    "response": full_response,
                    "strategy": strategy,
                    "hint_level": hint_level,
                }

        # 保存 AI 消息
        generation_ms = int((time.time() - start_time) * 1000)
        await self._add_message(
            session=session,
            role=MessageRole.ASSISTANT,
            content=full_response,
            strategy=strategy,
            hint_level=hint_level,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            ttft_ms=ttft_ms,
            generation_ms=generation_ms,
        )

        # 更新会话状态
        session.turn_count += 1
        session.current_hint_level = hint_level or session.current_hint_level
        session.current_strategy = strategy or session.current_strategy
        session.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self._cache_session_state(session)

    async def _add_message(
        self,
        session: DialogSession,
        role: MessageRole,
        content: str,
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
            id=str(uuid.uuid4()),
            session_id=session.id,
            user_id=session.user_id,
            role=role,
            content=content,
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

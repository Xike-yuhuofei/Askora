"""
Orchestrator 会话状态持久化仓库 (Redis-backed)

将 LearningFlowOrchestrator 的会话状态 (SharedContext + 各引擎私有状态)
持久化到 Redis，避免服务重启导致的会话丢失。

Redis Key 规范：askora:engine:session:{session_id}
Value: JSON (序列化 SharedContext + EngineStates + 元数据)

设计原则：
- 单例封装：OrchestratorRepository 作为独立模块，通过 `get_orchestrator_repository()` 获取
- 优雅降级：Redis 不可用时自动 fallback 到内存实现（方便本地开发）
- TTL 自动过期：默认 24 小时，活跃会话通过 touch 更新过期时间
- 序列化友好：enum 自动 to/from value，set 自动 to/from list
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, is_dataclass
from typing import Any, Optional, cast

from app.core.logging import get_logger

logger = get_logger(__name__)

# Redis Key 前缀
_KEY_PREFIX = "askora:engine:session:"
_KEY_TTL_SECONDS = 86400  # 24 小时

# 全局单例
_REPOSITORY: Optional["OrchestratorRepository"] = None


def get_orchestrator_repository() -> "OrchestratorRepository":
    """获取编排器仓库单例"""
    global _REPOSITORY
    if _REPOSITORY is None:
        _REPOSITORY = OrchestratorRepository()
    return _REPOSITORY


class OrchestratorRepository:
    """Orchestrator 会话状态持久化仓库"""

    def __init__(self) -> None:
        self._redis_client = None
        self._memory_fallback: dict[str, tuple[dict[str, Any], dict[str, dict[str, Any]]]] = {}
        self._redis_available: Optional[bool] = None

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    async def load_session(
        self, session_id: str
    ) -> Optional[tuple[dict[str, Any], dict[str, dict[str, Any]]]]:
        """
        加载一个 Orchestrator 会话。
        返回 (shared_ctx_dict, engine_states_dict) 或 None (会话不存在)。
        """
        key = _KEY_PREFIX + session_id
        raw = await self._redis_get(key)
        if raw is None:
            # 查内存 fallback
            return self._memory_fallback.get(session_id)

        try:
            data = json.loads(raw)
            shared_dict = data.get("shared_ctx", {})
            engine_states = data.get("engine_states", {})
            return (shared_dict, engine_states)
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            logger.warning(
                "orchestrator_session_deser_failed", session_id=session_id, error=str(exc)
            )
            return None

    async def save_session(
        self,
        session_id: str,
        shared_ctx_dict: dict[str, Any],
        engine_states: dict[str, dict[str, Any]],
    ) -> None:
        """
        保存一个 Orchestrator 会话到 Redis (同时写入内存 fallback)。
        """
        data = {
            "shared_ctx": self._prepare_for_json(shared_ctx_dict),
            "engine_states": self._prepare_for_json(engine_states),
            "updated_at": time.time(),
        }
        payload = json.dumps(data, ensure_ascii=False, default=str)

        # 写入 Redis
        await self._redis_setex(_KEY_PREFIX + session_id, _KEY_TTL_SECONDS, payload)
        # 同时写入内存 fallback (Redis 挂了也能跑)
        self._memory_fallback[session_id] = (shared_ctx_dict, engine_states)

        # 清理过旧的 fallback（保留最近 100 个）
        if len(self._memory_fallback) > 100:
            keys_sorted = sorted(
                self._memory_fallback,
                key=lambda key: self._memory_fallback[key][0].get("updated_at", 0),
            )
            for old_key in keys_sorted[: len(keys_sorted) - 80]:
                self._memory_fallback.pop(old_key, None)

    async def delete_session(self, session_id: str) -> None:
        """删除一个会话 (Redis + 内存)"""
        await self._redis_delete(_KEY_PREFIX + session_id)
        self._memory_fallback.pop(session_id, None)
        logger.info("orchestrator_session_deleted", session_id=session_id)

    async def touch_session(self, session_id: str) -> None:
        """续期会话 TTL (活跃会话自动延长有效期)"""
        await self._redis_expire(_KEY_PREFIX + session_id, _KEY_TTL_SECONDS)

    async def count_active_sessions(self) -> int:
        """估算活跃会话数 (Redis 部分基于 scan，内存部分基于 fallback 长度)"""
        mem_count = len(self._memory_fallback)
        # 注意：这里不做全量 Redis scan，性能考虑
        return mem_count

    # ------------------------------------------------------------------
    # Redis 交互 (带优雅降级)
    # ------------------------------------------------------------------

    async def _redis_get(self, key: str) -> Optional[str]:
        client = self._get_client()
        if client is None:
            return None
        try:
            return await client.get(key)
        except Exception as exc:  # noqa: BLE001
            self._mark_redis_unavailable(exc)
            return None

    async def _redis_setex(self, key: str, ttl: int, value: str) -> None:
        client = self._get_client()
        if client is None:
            return
        try:
            await client.set(key, value, ex=ttl)
        except Exception as exc:  # noqa: BLE001
            self._mark_redis_unavailable(exc)

    async def _redis_delete(self, key: str) -> None:
        client = self._get_client()
        if client is None:
            return
        try:
            await client.delete(key)
        except Exception as exc:  # noqa: BLE001
            self._mark_redis_unavailable(exc)

    async def _redis_expire(self, key: str, ttl: int) -> None:
        client = self._get_client()
        if client is None:
            return
        try:
            await client.expire(key, ttl)
        except Exception as exc:  # noqa: BLE001
            self._mark_redis_unavailable(exc)

    def _get_client(self):
        if self._redis_available is False:
            return None
        if self._redis_client is None:
            try:
                from app.core.redis_client import get_redis_client

                self._redis_client = get_redis_client()
                self._redis_available = True
            except Exception as exc:  # noqa: BLE001
                logger.warning("orchestrator_redis_init_failed", error_type=type(exc).__name__)
                self._redis_available = False
                return None
        return self._redis_client

    def _mark_redis_unavailable(self, exc: Exception) -> None:
        if self._redis_available is not False:
            logger.warning(
                "orchestrator_redis_became_unavailable_fallback_to_memory", error=str(exc)
            )
            self._redis_available = False

    # ------------------------------------------------------------------
    # 序列化辅助
    # ------------------------------------------------------------------

    def _prepare_for_json(self, obj: Any) -> Any:
        """将对象递归转换为 JSON 安全的结构（enum → value, set → list, datetime → isoformat）"""
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, (list, tuple)):
            return [self._prepare_for_json(item) for item in obj]
        if isinstance(obj, set):
            return [self._prepare_for_json(item) for item in sorted(obj, key=lambda x: str(x))]
        if isinstance(obj, dict):
            return {str(k): self._prepare_for_json(v) for k, v in obj.items()}
        if is_dataclass(obj):
            return self._prepare_for_json(asdict(cast(Any, obj)))
        if hasattr(obj, "value"):
            # Enum
            return obj.value
        if hasattr(obj, "isoformat"):
            # datetime
            return obj.isoformat()
        # 其他：转字符串 (安全兜底)
        try:
            return str(obj)
        except Exception:
            return repr(obj)


__all__ = ["OrchestratorRepository", "get_orchestrator_repository"]

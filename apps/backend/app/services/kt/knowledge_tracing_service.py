"""
基于 BKT (Bayesian Knowledge Tracing) 的知识追踪服务

BKT 模型是经典的知识追踪模型，假设学生对某个知识点的掌握状态是二元的（掌握/未掌握），
通过学生的答题表现（对/错）来动态估计掌握概率 p(L)。

简化的 BKT 更新公式：
- 答对时: p(L) = p(L) + (1 - p(L)) * p(T)  (假设不会遗忘，只增不减)
  实际应用中加入 p(S) slip 因子: p(L) = p(L) * (1 - p(S)) / (p(L) * (1 - p(S)) + (1 - p(L)) * p(G))
- 答错时: p(L) = p(L) * (1 - p(T)) / (p(L) * (1 - p(S)) + (1 - p(L)) * p(G))

为了 MVP 简化，我们使用调整后的加减法公式来模拟 BKT 行为。
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Optional

import redis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# BKT 默认参数
DEFAULT_P_INIT = 0.3  # 初始掌握度
DEFAULT_P_TRANSIT = 0.15  # 学习转化率
DEFAULT_P_SLIP = 0.1  # 失误率（掌握的情况下答错）
DEFAULT_P_GUESS = 0.2  # 猜测率（未掌握的情况下答对）

# Redis Key 前缀
_KT_KEY_PREFIX = "askora:kt:"
_KT_KEY_TTL = 86400 * 7  # 7 天


@dataclass
class MasteryEstimate:
    """掌握度估计"""

    kp_id: str
    p: float  # 掌握度 (0~1)
    n_attempts: int = 0
    n_correct: int = 0
    n_wrong: int = 0
    last_updated: float = 0.0


class KnowledgeTracingService:
    """
    基于 BKT 模型的知识追踪服务
    """

    def __init__(
        self,
        p_init: float = DEFAULT_P_INIT,
        p_transit: float = DEFAULT_P_TRANSIT,
        p_slip: float = DEFAULT_P_SLIP,
        p_guess: float = DEFAULT_P_GUESS,
    ):
        self.p_init = p_init
        self.p_transit = p_transit
        self.p_slip = p_slip
        self.p_guess = p_guess
        self._redis = (
            redis.Redis.from_url(
                settings.redis_url,
                password=settings.redis_password,
                decode_responses=True,
                socket_connect_timeout=0.2,
                socket_timeout=0.2,
            )
            if settings.redis_url
            else None
        )
        self._redis_available: Optional[bool] = None
        self._memory_store: dict[str, dict] = {}  # Redis 不可用时的内存降级

    def _get_key(self, user_id: str, kp_id: str) -> str:
        return f"{_KT_KEY_PREFIX}{user_id}:{kp_id}"

    def _load_state(self, user_id: str, kp_id: str) -> dict:
        """加载用户对某知识点的当前状态"""
        key = self._get_key(user_id, kp_id)
        if self._redis and self._redis_available is not False:
            try:
                data = self._redis.get(key)
                self._redis_available = True
                if data:
                    return json.loads(data)
            except Exception as e:
                self._redis_available = False
                logger.warning("kt_redis_unavailable_using_memory", error_type=type(e).__name__)

        # Fallback to memory
        return self._memory_store.get(
            key,
            {
                "p": self.p_init,
                "n_attempts": 0,
                "n_correct": 0,
                "n_wrong": 0,
                "last_updated": 0.0,
            },
        )

    def _save_state(self, user_id: str, kp_id: str, state: dict) -> None:
        """保存用户对某知识点的状态"""
        key = self._get_key(user_id, kp_id)
        state["last_updated"] = time.time()

        # 内存中始终保留最新值，Redis 短暂失败也不会回退到旧状态。
        self._memory_store[key] = state.copy()

        if self._redis and self._redis_available is not False:
            try:
                self._redis.setex(key, _KT_KEY_TTL, json.dumps(state))
                self._redis_available = True
                return
            except Exception as e:
                self._redis_available = False
                logger.warning("kt_redis_unavailable_using_memory", error_type=type(e).__name__)

    def get_mastery(self, user_id: str, kp_id: str) -> MasteryEstimate:
        """获取用户对某知识点的掌握度估计"""
        state = self._load_state(user_id, kp_id)
        return MasteryEstimate(
            kp_id=kp_id,
            p=state["p"],
            n_attempts=state["n_attempts"],
            n_correct=state["n_correct"],
            n_wrong=state["n_wrong"],
            last_updated=state.get("last_updated", 0.0),
        )

    def update_mastery(
        self,
        user_id: str,
        kp_id: str,
        is_correct: bool,
        response_time: float = 0.0,
        hint_level: int = 0,
    ) -> MasteryEstimate:
        """
        根据一次答题情况更新掌握度

        Args:
            user_id: 用户 ID
            kp_id: 知识点 ID
            is_correct: 是否答对
            response_time: 响应时间 (秒)
            hint_level: 使用的提示级别 (1-5)，越高提示越多，真实掌握度修正越保守

        Returns:
            更新后的掌握度估计
        """
        state = self._load_state(user_id, kp_id)
        old_p = state["p"]

        # 动态调整因子：使用的提示越多，真实掌握的可能性越低
        # 使用提示时，即使答对，掌握度提升也较少
        hint_penalty = max(0.3, 1.0 - (hint_level - 1) * 0.15) if hint_level > 0 else 1.0

        if is_correct:
            # 答对：掌握度提升
            # 使用简化 BKT 公式: p_new = p_old + (1 - p_old) * p_transit * hint_penalty
            p_gain = (1.0 - old_p) * self.p_transit * hint_penalty
            new_p = min(1.0, old_p + p_gain)
            state["n_correct"] += 1
        else:
            # 答错：掌握度下降
            # 使用简化 BKT 公式: p_new = p_old * (1 - p_slip)
            p_loss = old_p * self.p_slip
            new_p = max(0.0, old_p - p_loss)
            state["n_wrong"] += 1

        state["p"] = round(new_p, 4)
        state["n_attempts"] += 1

        self._save_state(user_id, kp_id, state)
        return self.get_mastery(user_id, kp_id)

    def batch_get_mastery(self, user_id: str, kp_ids: list[str]) -> dict[str, MasteryEstimate]:
        """批量获取多个知识点的掌握度"""
        return {kp_id: self.get_mastery(user_id, kp_id) for kp_id in kp_ids}

    def reset_mastery(self, user_id: str, kp_id: str) -> None:
        """重置某知识点的掌握度"""
        key = self._get_key(user_id, kp_id)
        default_state = {
            "p": self.p_init,
            "n_attempts": 0,
            "n_correct": 0,
            "n_wrong": 0,
            "last_updated": time.time(),
        }
        if self._redis and self._redis_available is not False:
            try:
                self._redis.delete(key)
            except Exception as e:
                self._redis_available = False
                logger.warning("kt_redis_delete_failed_using_memory", error_type=type(e).__name__)
        self._memory_store[key] = default_state


# 单例模式
_kt_service: Optional[KnowledgeTracingService] = None


def get_kt_service() -> KnowledgeTracingService:
    """获取知识追踪服务单例"""
    global _kt_service
    if _kt_service is None:
        _kt_service = KnowledgeTracingService()
    return _kt_service

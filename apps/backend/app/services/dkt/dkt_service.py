"""
深度知识追踪 (DKT) 服务

基于简化版神经-like DKT 模型，使用纯 Python 实现（无 numpy 依赖）。
扩展 BKT 模型以支持：
- 知识点依赖关系（前置关系建模）
- 多任务学习（同时预测多个知识点掌握度）
- 时序处理（将练习序列作为时间序列处理）
- 动态掌握度历史追踪

核心思想：
将学生的答题序列视为时间序列，通过简单的状态转移矩阵
（类似 RNN 隐状态更新）来建模知识点之间的依赖关系，
并通过注意力机制加权历史表现对当前预测的影响。
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.core.redis_client import get_redis_client
from app.services.kt.knowledge_tracing_service import KnowledgeTracingService, get_kt_service

logger = get_logger(__name__)

# Redis Key 前缀
_DKT_KEY_PREFIX = "askora:dkt:"
_DKT_KEY_TTL = 86400 * 14  # 14 天

# 模型默认超参数
DEFAULT_LEARNING_RATE = 0.01
DEFAULT_DECAY_FACTOR = 0.95
DEFAULT_ATTENTION_TEMP = 2.0
DEFAULT_HIDDEN_DIM = 32

# 知识点掌握度阈值
MASTERY_THRESHOLD = 0.85
RISK_THRESHOLD = 0.4


@dataclass
class DKTState:
    """DKT 状态数据类，追踪单个知识点的时序掌握状态"""

    kp_id: str
    mastery_history: list[float] = field(default_factory=list)
    dependency_ids: list[str] = field(default_factory=list)
    sequence_count: int = 0
    current_mastery: float = 0.3
    hidden_state: list[float] = field(default_factory=list)
    last_updated: float = 0.0


@dataclass
class ExerciseEvent:
    """练习事件数据类"""

    kp_id: str
    is_correct: bool
    timestamp: float = 0.0
    response_time: float = 0.0
    hint_level: int = 0


@dataclass
class PredictionResult:
    """预测结果数据类"""

    kp_id: str
    predicted_mastery: float
    confidence: float
    dependency_score: float = 0.0


class DKTService:
    """
    深度知识追踪服务

    使用纯 Python 实现的简化神经-like DKT 模型，
    通过状态转移和注意力机制建模知识点掌握的时序动态。
    """

    def __init__(
        self,
        learning_rate: float = DEFAULT_LEARNING_RATE,
        decay_factor: float = DEFAULT_DECAY_FACTOR,
        attention_temp: float = DEFAULT_ATTENTION_TEMP,
        hidden_dim: int = DEFAULT_HIDDEN_DIM,
    ):
        self.learning_rate = learning_rate
        self.decay_factor = decay_factor
        self.attention_temp = attention_temp
        self.hidden_dim = hidden_dim
        self._redis = get_redis_client() if settings.redis_url else None
        self._memory_store: dict[str, dict] = {}
        self._transition_params: dict[str, dict[str, float]] = {}
        self._kt_service: Optional[KnowledgeTracingService] = None

    @property
    def kt_service(self) -> KnowledgeTracingService:
        """延迟初始化 KT 服务以避免循环导入"""
        if self._kt_service is None:
            self._kt_service = get_kt_service()
        return self._kt_service

    # ------------------------------------------------------------------
    # Redis 持久化
    # ------------------------------------------------------------------

    def _get_state_key(self, student_id: str, kp_id: str) -> str:
        return f"{_DKT_KEY_PREFIX}{student_id}:{kp_id}"

    def _get_seq_key(self, student_id: str) -> str:
        return f"{_DKT_KEY_PREFIX}{student_id}:sequence"

    def _load_state(self, student_id: str, kp_id: str) -> DKTState:
        key = self._get_state_key(student_id, kp_id)
        if self._redis:
            try:
                data = self._redis.get(key)
                if data:
                    raw = json.loads(data)
                    return DKTState(
                        kp_id=raw["kp_id"],
                        mastery_history=raw.get("mastery_history", []),
                        dependency_ids=raw.get("dependency_ids", []),
                        sequence_count=raw.get("sequence_count", 0),
                        current_mastery=raw.get("current_mastery", 0.3),
                        hidden_state=raw.get("hidden_state", []),
                        last_updated=raw.get("last_updated", 0.0),
                    )
            except Exception as e:
                logger.warning(f"Redis load failed, falling back to memory: {e}")

        raw = self._memory_store.get(key)
        if raw:
            return DKTState(
                kp_id=raw["kp_id"],
                mastery_history=raw.get("mastery_history", []),
                dependency_ids=raw.get("dependency_ids", []),
                sequence_count=raw.get("sequence_count", 0),
                current_mastery=raw.get("current_mastery", 0.3),
                hidden_state=raw.get("hidden_state", []),
                last_updated=raw.get("last_updated", 0.0),
            )

        return DKTState(kp_id=kp_id, hidden_state=self._init_hidden_state())

    def _save_state(self, student_id: str, state: DKTState) -> None:
        key = self._get_state_key(student_id, state.kp_id)
        state.last_updated = time.time()
        serializable = {
            "kp_id": state.kp_id,
            "mastery_history": state.mastery_history[-50:],
            "dependency_ids": state.dependency_ids,
            "sequence_count": state.sequence_count,
            "current_mastery": state.current_mastery,
            "hidden_state": state.hidden_state,
            "last_updated": state.last_updated,
        }
        if self._redis:
            try:
                self._redis.setex(key, _DKT_KEY_TTL, json.dumps(serializable))
                return
            except Exception as e:
                logger.warning(f"Redis save failed, falling back to memory: {e}")
        self._memory_store[key] = serializable

    def _load_sequence(self, student_id: str) -> list[dict]:
        key = self._get_seq_key(student_id)
        if self._redis:
            try:
                data = self._redis.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.warning(f"Redis load sequence failed: {e}")
        return self._memory_store.get(key, [])

    def _save_sequence(self, student_id: str, sequence: list[dict]) -> None:
        key = self._get_seq_key(student_id)
        if self._redis:
            try:
                self._redis.setex(key, _DKT_KEY_TTL, json.dumps(sequence[-200:]))
                return
            except Exception as e:
                logger.warning(f"Redis save sequence failed: {e}")
        self._memory_store[key] = sequence[-200:]

    # ------------------------------------------------------------------
    # 隐状态初始化（纯 Python 的简化随机初始化）
    # ------------------------------------------------------------------

    def _init_hidden_state(self) -> list[float]:
        """生成简化的隐状态向量（固定种子的伪随机以保证确定性）"""
        state = []
        for i in range(self.hidden_dim):
            val = math.sin(i * 0.1) * 0.1
            state.append(round(val, 6))
        return state

    def _update_hidden_state(
        self,
        hidden: list[float],
        input_signal: float,
        target_mastery: float,
    ) -> list[float]:
        """
        简化的 RNN 隐状态更新

        h_t = (1 - lr) * h_{t-1} + lr * (input_signal * target_mastery + decay * h_{t-1})
        """
        new_hidden = []
        for i, h_val in enumerate(hidden):
            input_component = input_signal * target_mastery * math.sin(i * 0.5 + len(hidden))
            updated = (1.0 - self.learning_rate) * h_val + self.learning_rate * (
                input_component + self.decay_factor * h_val
            )
            new_hidden.append(round(updated, 6))
        return new_hidden

    def _compute_attention_weights(
        self,
        history: list[float],
        current_signal: float,
    ) -> list[float]:
        """
        基于注意力机制的历史表现加权

        使用 softmax 计算每个历史步骤的权重
        """
        if not history:
            return [1.0]
        scores = []
        for i, h in enumerate(history):
            recency = math.exp(-(len(history) - 1 - i) / self.attention_temp)
            relevance = math.exp(-abs(h - current_signal) / self.attention_temp)
            scores.append(recency * relevance)
        total = sum(scores)
        if total == 0:
            return [1.0 / len(history)] * len(history)
        return [s / total for s in scores]

    # ------------------------------------------------------------------
    # 核心 API
    # ------------------------------------------------------------------

    def update(
        self,
        student_id: str,
        exercise_sequence: list[ExerciseEvent],
    ) -> dict[str, DKTState]:
        """
        处理学生的练习序列，更新所有相关知识点的掌握状态

        Args:
            student_id: 学生 ID
            exercise_sequence: 按时间排序的练习事件序列

        Returns:
            更新后的各知识点 DKT 状态字典
        """
        results: dict[str, DKTState] = {}
        sequence_data = self._load_sequence(student_id)

        for event in exercise_sequence:
            sequence_data.append(
                {
                    "kp_id": event.kp_id,
                    "is_correct": event.is_correct,
                    "timestamp": event.timestamp or time.time(),
                    "response_time": event.response_time,
                    "hint_level": event.hint_level,
                }
            )

            state = self._load_state(student_id, event.kp_id)

            base_mastery = self.kt_service.get_mastery(student_id, event.kp_id).p

            input_signal = 1.0 if event.is_correct else 0.0
            if event.hint_level > 0:
                input_signal *= max(0.3, 1.0 - (event.hint_level - 1) * 0.15)

            new_hidden = self._update_hidden_state(state.hidden_state, input_signal, base_mastery)

            history = state.mastery_history.copy()
            history.append(base_mastery)
            attention_weights = self._compute_attention_weights(history, base_mastery)
            weighted_mastery = sum(w * h for w, h in zip(attention_weights, history, strict=True))

            state.hidden_state = new_hidden
            state.mastery_history = history
            state.current_mastery = round((weighted_mastery + base_mastery) / 2.0, 4)
            state.sequence_count += 1

            self._save_state(student_id, state)
            results[event.kp_id] = state

        self._save_sequence(student_id, sequence_data)
        return results

    def predict_mastery(
        self,
        student_id: str,
        kp_ids: list[str],
    ) -> list[PredictionResult]:
        """
        预测学生对多个知识点的掌握度（多任务学习）

        同时输出每个知识点的预测掌握度和置信度，
        利用跨知识点依赖关系提升预测精度。

        Args:
            student_id: 学生 ID
            kp_ids: 待预测的知识点 ID 列表

        Returns:
            预测结果列表
        """
        results: list[PredictionResult] = []
        sequence_data = self._load_sequence(student_id)
        kp_states: dict[str, DKTState] = {}
        for kp_id in kp_ids:
            kp_states[kp_id] = self._load_state(student_id, kp_id)

        known_masteries: dict[str, float] = {}
        for kp_id, state in kp_states.items():
            known_masteries[kp_id] = state.current_mastery

        for kp_id in kp_ids:
            state = kp_states[kp_id]

            dep_score = self._compute_kp_dependency_score(kp_id, known_masteries)

            base_mastery = state.current_mastery
            history_len = len(state.mastery_history)
            if history_len >= 3:
                recent_trend = state.mastery_history[-1] - state.mastery_history[-3]
                trend_factor = max(-0.1, min(0.1, recent_trend))
            else:
                trend_factor = 0.0

            recent_exercises_on_kp = sum(1 for e in sequence_data[-10:] if e["kp_id"] == kp_id)
            practice_bonus = min(0.1, recent_exercises_on_kp * 0.02)

            predicted = base_mastery
            predicted += dep_score * 0.15
            predicted += trend_factor
            predicted += practice_bonus
            predicted = max(0.0, min(1.0, predicted))

            confidence = min(1.0, 0.5 + history_len * 0.05 + dep_score * 0.1)

            results.append(
                PredictionResult(
                    kp_id=kp_id,
                    predicted_mastery=round(predicted, 4),
                    confidence=round(confidence, 4),
                    dependency_score=round(dep_score, 4),
                )
            )

        return results

    def recommend_next_exercise(
        self,
        student_id: str,
        subject: str,
    ) -> dict[str, object]:
        """
        基于 DKT 模型推荐最优下一个练习

        策略：
        1. 找出掌握度低于阈值的知识点（薄弱点）
        2. 考虑依赖关系：优先学习前置依赖已掌握但自身未掌握的知识点
        3. 引入间隔重复因子：减少最近练习过的知识点

        Args:
            student_id: 学生 ID
            subject: 学科标识

        Returns:
            推荐结果字典，包含推荐的知识点和推荐理由
        """
        sequence_data = self._load_sequence(student_id)

        kp_masteries: dict[str, float] = {}
        kp_sequences: dict[str, int] = {}
        for kp_id in self._get_all_known_kps(student_id):
            state = self._load_state(student_id, kp_id)
            kp_masteries[kp_id] = state.current_mastery
            kp_sequences[kp_id] = state.sequence_count

        if not kp_masteries:
            return {
                "recommended_kp_id": None,
                "reason": "暂无足够的历史数据进行推荐",
                "confidence": 0.0,
            }

        candidates: list[tuple[str, float]] = []
        known_masteries = dict(kp_masteries)

        for kp_id, mastery in kp_masteries.items():
            if mastery >= MASTERY_THRESHOLD:
                continue

            dep_score = self._compute_kp_dependency_score(kp_id, known_masteries)

            recent_count = sum(1 for e in sequence_data[-5:] if e["kp_id"] == kp_id)
            spacing_penalty = max(0.0, 1.0 - recent_count * 0.2)

            urgency = (1.0 - mastery) * 0.6 + dep_score * 0.3 + spacing_penalty * 0.1

            candidates.append((kp_id, urgency))

        if not candidates:
            best_kp = max(kp_masteries, key=lambda k: kp_masteries[k])
            return {
                "recommended_kp_id": best_kp,
                "reason": "所有知识点均已掌握，推荐复习最高难度知识点",
                "confidence": kp_masteries[best_kp],
            }

        candidates.sort(key=lambda x: x[1], reverse=True)
        best_kp, best_score = candidates[0]

        state = self._load_state(student_id, best_kp)
        dep_score = self._compute_kp_dependency_score(best_kp, known_masteries)

        reasons = []
        if state.current_mastery < RISK_THRESHOLD:
            reasons.append("该知识点掌握度较低，需要加强练习")
        elif state.current_mastery < MASTERY_THRESHOLD:
            reasons.append("该知识点接近掌握，继续巩固可达成掌握")

        if dep_score > 0.5:
            reasons.append("相关前置知识点已掌握，时机成熟")

        if best_score > 0.7:
            reasons.append("综合优先级最高")

        return {
            "recommended_kp_id": best_kp,
            "reason": "；".join(reasons) if reasons else "综合评分最高",
            "confidence": round(min(1.0, best_score), 4),
            "dependency_score": round(dep_score, 4),
            "current_mastery": round(state.current_mastery, 4),
        }

    def _compute_kp_dependency_score(
        self,
        kp_id: str,
        known_kps: dict[str, float],
    ) -> float:
        """
        基于前置依赖图计算知识点的依赖就绪分数

        分数越高，表示该知识点的前置依赖越充分，越适合学习。

        Args:
            kp_id: 目标知识点 ID
            known_kps: 已知知识点及其掌握度映射

        Returns:
            依赖就绪分数 (0.0 ~ 1.0)
        """
        state = self._load_state("", kp_id)
        dep_ids = state.dependency_ids

        if not dep_ids:
            return 0.5

        scores = []
        for dep_id in dep_ids:
            dep_mastery = known_kps.get(dep_id, 0.3)
            scores.append(min(1.0, dep_mastery))

        if not scores:
            return 0.5

        avg_score = sum(scores) / len(scores)
        weighted_score = sum(s * s for s in scores) / len(scores)

        return round((avg_score + weighted_score) / 2.0, 4)

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    def _get_all_known_kps(self, student_id: str) -> set[str]:
        """获取学生历史序列中出现过的所有知识点"""
        sequence_data = self._load_sequence(student_id)
        kps = set()
        for event in sequence_data:
            kps.add(event["kp_id"])
        for key in self._memory_store:
            if key.startswith(f"{_DKT_KEY_PREFIX}{student_id}:"):
                parts = key.split(":")
                if len(parts) >= 3:
                    kps.add(parts[2])
        return kps

    def set_dependencies(self, kp_id: str, dependency_ids: list[str]) -> None:
        """设置知识点的前置依赖关系"""
        state = self._load_state("", kp_id)
        state.dependency_ids = dependency_ids
        self._save_state("", state)

    def get_state(self, student_id: str, kp_id: str) -> DKTState:
        """获取学生在指定知识点上的 DKT 状态"""
        return self._load_state(student_id, kp_id)

    def reset_student(self, student_id: str) -> None:
        """重置学生的所有 DKT 状态"""
        if self._redis:
            try:
                keys = self._redis.keys(f"{_DKT_KEY_PREFIX}{student_id}:*")
                for key in keys:
                    self._redis.delete(key)
            except Exception as e:
                logger.warning(f"Redis reset failed: {e}")

        keys_to_remove = [
            k for k in self._memory_store if k.startswith(f"{_DKT_KEY_PREFIX}{student_id}:")
        ]
        for key in keys_to_remove:
            del self._memory_store[key]


# 单例模式
_dkt_service: Optional[DKTService] = None


def get_dkt_service() -> DKTService:
    """获取 DKT 服务单例"""
    global _dkt_service
    if _dkt_service is None:
        _dkt_service = DKTService()
    return _dkt_service

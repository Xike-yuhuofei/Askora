"""
评估服务 (Assessment Service)

支持三种评估模式:
1. 诊断性评估 (Diagnostic): 课前测试，识别知识盲区
2. 形成性评估 (Formative): 课中微测，与 Quiz 引擎集成
3. 总结性评估 (Summative): 课后综合测试，生成学习报告

此文件是 legacy compatibility surface；canonical 流程由 SYS04 生成单次测量，
再由 SYS03 接纳证据并计算 mastery。
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.core.redis_client import get_redis_client

logger = get_logger(__name__)

_ASSESSMENT_KEY_PREFIX = "askora:assessment:"
_ASSESSMENT_KEY_TTL = 86400 * 30

VALID_ASSESSMENT_TYPES = {"diagnostic", "formative", "summative"}
VALID_ITEM_TYPES = {"mcq", "fill_blank", "short_answer", "problem_solving"}
VALID_COGNITIVE_LEVELS = {"remember", "understand", "apply", "analyze", "evaluate", "create"}

_MISCONCEPTION_PATTERNS: dict[str, list[str]] = {
    "linear_equation": [
        "移项时忘记变号",
        "分配律应用错误",
        "等式两边同时除以未知数时丢失解",
        "分数系数处理不当",
    ],
    "quadratic_equation": [
        "求根公式符号错误",
        "判别式判断错误",
        "因式分解不完整",
        "忽略二次项系数不为零的条件",
    ],
    "function": [
        "定义域与值域混淆",
        "函数单调性判断错误",
        "复合函数内外层混淆",
        "反函数求解步骤缺失",
    ],
}


@dataclass
class AssessmentConfig:
    """评估配置"""

    assessment_type: str
    subject: str
    kp_ids: list[str]
    difficulty_range: tuple[float, float] = (0.2, 0.8)
    item_count: int = 10
    time_limit_sec: int = 600


@dataclass
class AssessmentItem:
    """评估题目"""

    id: str
    kp_id: str
    type: str
    question: str
    options: list[str] = field(default_factory=list)
    correct_answer: str = ""
    difficulty: float = 0.5
    cognitive_level: str = "understand"


@dataclass
class ItemResult:
    """单题答题结果"""

    item_id: str
    kp_id: str
    user_answer: str
    is_correct: bool
    response_time_ms: int = 0
    selected_option: Optional[str] = None


@dataclass
class AssessmentResult:
    """评估结果"""

    id: str
    user_id: str
    assessment_type: str
    total_items: int
    correct_count: int
    score: float
    mastery_estimates: dict[str, float] = field(default_factory=dict)
    misconceptions: list[str] = field(default_factory=list)
    item_results: list[ItemResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "assessment_type": self.assessment_type,
            "total_items": self.total_items,
            "correct_count": self.correct_count,
            "score": self.score,
            "mastery_estimates": self.mastery_estimates,
            "misconceptions": self.misconceptions,
            "item_results": [
                {
                    "item_id": ir.item_id,
                    "kp_id": ir.kp_id,
                    "user_answer": ir.user_answer,
                    "is_correct": ir.is_correct,
                    "response_time_ms": ir.response_time_ms,
                    "selected_option": ir.selected_option,
                }
                for ir in self.item_results
            ],
        }


# ──────────────────────────────────────────────────────────────
# 题库: 30+ 道代数题目 (线性方程 / 二次方程 / 函数)
# ──────────────────────────────────────────────────────────────

_ITEM_BANK: list[AssessmentItem] = [
    # ── 线性方程 (10 题) ──
    AssessmentItem(
        id="alg_lin_001",
        kp_id="kp_linear_easy",
        type="mcq",
        question="解方程: 2x + 3 = 11",
        options=["x = 2", "x = 3", "x = 4", "x = 5"],
        correct_answer="x = 4",
        difficulty=0.2,
        cognitive_level="remember",
    ),
    AssessmentItem(
        id="alg_lin_002",
        kp_id="kp_linear_easy",
        type="mcq",
        question="解方程: 3(x - 2) = 9",
        options=["x = 3", "x = 4", "x = 5", "x = 6"],
        correct_answer="x = 5",
        difficulty=0.25,
        cognitive_level="understand",
    ),
    AssessmentItem(
        id="alg_lin_003",
        kp_id="kp_linear_easy",
        type="fill_blank",
        question="解方程: 5x - 7 = 3x + 1, x = ____",
        options=[],
        correct_answer="4",
        difficulty=0.3,
        cognitive_level="apply",
    ),
    AssessmentItem(
        id="alg_lin_004",
        kp_id="kp_linear_medium",
        type="mcq",
        question="解方程: (x/2) + (x/3) = 10",
        options=["x = 10", "x = 12", "x = 14", "x = 16"],
        correct_answer="x = 12",
        difficulty=0.4,
        cognitive_level="apply",
    ),
    AssessmentItem(
        id="alg_lin_005",
        kp_id="kp_linear_medium",
        type="fill_blank",
        question="解方程: 0.5(x - 4) = 0.3(x + 2), x = ____",
        options=[],
        correct_answer="14",
        difficulty=0.45,
        cognitive_level="apply",
    ),
    AssessmentItem(
        id="alg_lin_006",
        kp_id="kp_linear_medium",
        type="mcq",
        question="若 3x + 2 = 5x - 8, 则 x = ?",
        options=["x = 3", "x = 4", "x = 5", "x = 6"],
        correct_answer="x = 5",
        difficulty=0.35,
        cognitive_level="understand",
    ),
    AssessmentItem(
        id="alg_lin_007",
        kp_id="kp_linear_hard",
        type="short_answer",
        question="解方程: (2x+1)/3 - (5x-1)/6 = 7/12",
        options=[],
        correct_answer="x = -1/4",
        difficulty=0.6,
        cognitive_level="analyze",
    ),
    AssessmentItem(
        id="alg_lin_008",
        kp_id="kp_linear_hard",
        type="short_answer",
        question="解方程: |3x - 6| = 12",
        options=[],
        correct_answer="x = 6 或 x = -2",
        difficulty=0.7,
        cognitive_level="analyze",
    ),
    AssessmentItem(
        id="alg_lin_009",
        kp_id="kp_linear_hard",
        type="problem_solving",
        question="已知关于 x 的方程 2(x - a) = 3x + 4 的解是正数, 求 a 的取值范围",
        options=[],
        correct_answer="a < -2",
        difficulty=0.75,
        cognitive_level="evaluate",
    ),
    AssessmentItem(
        id="alg_lin_010",
        kp_id="kp_linear_medium",
        type="mcq",
        question="若方程 2x + 3m = 2x - 3 的解为 x = 1, 则 m = ?",
        options=["m = -1", "m = 1", "m = -3", "m = 3"],
        correct_answer="m = -3",
        difficulty=0.5,
        cognitive_level="apply",
    ),
    # ── 二次方程 (12 题) ──
    AssessmentItem(
        id="alg_qua_001",
        kp_id="kp_quadratic_easy",
        type="mcq",
        question="解方程: x² = 16",
        options=["x = 4", "x = -4", "x = 4 或 x = -4", "x = 16"],
        correct_answer="x = 4 或 x = -4",
        difficulty=0.2,
        cognitive_level="remember",
    ),
    AssessmentItem(
        id="alg_qua_002",
        kp_id="kp_quadratic_easy",
        type="mcq",
        question="解方程: x² - 5x + 6 = 0",
        options=["x = 1, 6", "x = 2, 3", "x = -2, -3", "x = 0, 5"],
        correct_answer="x = 2, 3",
        difficulty=0.3,
        cognitive_level="understand",
    ),
    AssessmentItem(
        id="alg_qua_003",
        kp_id="kp_quadratic_easy",
        type="fill_blank",
        question="解方程: x² - 9 = 0, x = ____ (写出所有解)",
        options=[],
        correct_answer="3, -3",
        difficulty=0.25,
        cognitive_level="remember",
    ),
    AssessmentItem(
        id="alg_qua_004",
        kp_id="kp_quadratic_medium",
        type="mcq",
        question="用求根公式解: x² - 4x + 3 = 0",
        options=["x = 1, 3", "x = 1, -3", "x = -1, 3", "x = -1, -3"],
        correct_answer="x = 1, 3",
        difficulty=0.4,
        cognitive_level="apply",
    ),
    AssessmentItem(
        id="alg_qua_005",
        kp_id="kp_quadratic_medium",
        type="fill_blank",
        question="解方程: 2x² - 8x + 6 = 0, x = ____",
        options=[],
        correct_answer="1, 3",
        difficulty=0.45,
        cognitive_level="apply",
    ),
    AssessmentItem(
        id="alg_qua_006",
        kp_id="kp_quadratic_medium",
        type="mcq",
        question="若方程 x² + (k-1)x - k = 0 有一个根为 2, 则 k = ?",
        options=["k = -2", "k = 2", "k = -3", "k = 3"],
        correct_answer="k = 2",
        difficulty=0.5,
        cognitive_level="analyze",
    ),
    AssessmentItem(
        id="alg_qua_007",
        kp_id="kp_quadratic_medium",
        type="mcq",
        question="方程 x² - 2x + 3 = 0 的判别式 Δ 为?",
        options=["Δ = -8", "Δ = 8", "Δ = -4", "Δ = 4"],
        correct_answer="Δ = -8",
        difficulty=0.35,
        cognitive_level="understand",
    ),
    AssessmentItem(
        id="alg_qua_008",
        kp_id="kp_quadratic_hard",
        type="short_answer",
        question="解方程: 3x² - 2x - 1 = 0 (用求根公式)",
        options=[],
        correct_answer="x = 1 或 x = -1/3",
        difficulty=0.6,
        cognitive_level="apply",
    ),
    AssessmentItem(
        id="alg_qua_009",
        kp_id="kp_quadratic_hard",
        type="short_answer",
        question="已知方程 x² + mx + m - 1 = 0 有两个相等的实数根, 求 m 的值",
        options=[],
        correct_answer="m = 2",
        difficulty=0.7,
        cognitive_level="analyze",
    ),
    AssessmentItem(
        id="alg_qua_010",
        kp_id="kp_quadratic_hard",
        type="problem_solving",
        question="设 α, β 是方程 x² - 3x - 2 = 0 的两个根, 求 α² + β² 的值",
        options=[],
        correct_answer="13",
        difficulty=0.75,
        cognitive_level="evaluate",
    ),
    AssessmentItem(
        id="alg_qua_011",
        kp_id="kp_quadratic_medium",
        type="fill_blank",
        question="方程 x² - 6x + 9 = 0 的解为 x = ____",
        options=[],
        correct_answer="3 (重根)",
        difficulty=0.4,
        cognitive_level="understand",
    ),
    AssessmentItem(
        id="alg_qua_012",
        kp_id="kp_quadratic_easy",
        type="mcq",
        question="下列哪个是完全平方公式?",
        options=[
            "x² + 2xy + y² = (x+y)²",
            "x² - y² = (x-y)²",
            "x² + y² = (x+y)²",
            "x² - 2xy + y² = (x+y)²",
        ],
        correct_answer="x² + 2xy + y² = (x+y)²",
        difficulty=0.3,
        cognitive_level="remember",
    ),
    # ── 函数 (10 题) ──
    AssessmentItem(
        id="alg_func_001",
        kp_id="kp_function_easy",
        type="mcq",
        question="函数 f(x) = 2x + 1 中, f(3) = ?",
        options=["5", "6", "7", "8"],
        correct_answer="7",
        difficulty=0.2,
        cognitive_level="remember",
    ),
    AssessmentItem(
        id="alg_func_002",
        kp_id="kp_function_easy",
        type="mcq",
        question="函数 y = x² 的图像开口方向是?",
        options=["向上", "向下", "向左", "向右"],
        correct_answer="向上",
        difficulty=0.2,
        cognitive_level="remember",
    ),
    AssessmentItem(
        id="alg_func_003",
        kp_id="kp_function_easy",
        type="fill_blank",
        question="函数 f(x) = √(x-1) 的定义域为 ____",
        options=[],
        correct_answer="x ≥ 1",
        difficulty=0.3,
        cognitive_level="understand",
    ),
    AssessmentItem(
        id="alg_func_004",
        kp_id="kp_function_medium",
        type="mcq",
        question="函数 y = -x² + 4x - 3 的最大值为?",
        options=["1", "2", "3", "4"],
        correct_answer="1",
        difficulty=0.45,
        cognitive_level="apply",
    ),
    AssessmentItem(
        id="alg_func_005",
        kp_id="kp_function_medium",
        type="fill_blank",
        question="函数 f(x) = x² - 2x - 3 的最小值为 ____",
        options=[],
        correct_answer="-4",
        difficulty=0.4,
        cognitive_level="apply",
    ),
    AssessmentItem(
        id="alg_func_006",
        kp_id="kp_function_medium",
        type="mcq",
        question="若函数 f(x) = kx + b 在 R 上单调递增, 则?",
        options=["k > 0", "k < 0", "k = 0", "k ≥ 0"],
        correct_answer="k > 0",
        difficulty=0.35,
        cognitive_level="understand",
    ),
    AssessmentItem(
        id="alg_func_007",
        kp_id="kp_function_medium",
        type="fill_blank",
        question="函数 f(x) = 1/(x-2) 的值域为 ____",
        options=[],
        correct_answer="y ≠ 0",
        difficulty=0.5,
        cognitive_level="analyze",
    ),
    AssessmentItem(
        id="alg_func_008",
        kp_id="kp_function_hard",
        type="short_answer",
        question="求函数 f(x) = x + 4/x (x > 0) 的最小值",
        options=[],
        correct_answer="4",
        difficulty=0.6,
        cognitive_level="analyze",
    ),
    AssessmentItem(
        id="alg_func_009",
        kp_id="kp_function_hard",
        type="problem_solving",
        question="已知函数 f(x) = ax² + bx + c 过点 (0,1), (1,3), (-1,1), 求 f(x) 的解析式",
        options=[],
        correct_answer="f(x) = x² + x + 1",
        difficulty=0.7,
        cognitive_level="evaluate",
    ),
    AssessmentItem(
        id="alg_func_010",
        kp_id="kp_function_hard",
        type="short_answer",
        question="讨论函数 f(x) = x³ - 3x 的单调性",
        options=[],
        correct_answer="在 (-∞,-1) 和 (1,+∞) 上递增, 在 (-1,1) 上递减",
        difficulty=0.75,
        cognitive_level="evaluate",
    ),
    AssessmentItem(
        id="alg_func_011",
        kp_id="kp_function_easy",
        type="mcq",
        question="下列哪个函数是正比例函数?",
        options=["y = 2x", "y = 2x + 1", "y = 2/x", "y = x²"],
        correct_answer="y = 2x",
        difficulty=0.2,
        cognitive_level="remember",
    ),
    AssessmentItem(
        id="alg_func_012",
        kp_id="kp_function_medium",
        type="mcq",
        question="函数 y = |x| 的图像关于什么对称?",
        options=["x 轴", "y 轴", "原点", "直线 y = x"],
        correct_answer="y 轴",
        difficulty=0.3,
        cognitive_level="understand",
    ),
]

_KP_TO_MISCONCEPTION_KEY: dict[str, str] = {
    "kp_linear_easy": "linear_equation",
    "kp_linear_medium": "linear_equation",
    "kp_linear_hard": "linear_equation",
    "kp_quadratic_easy": "quadratic_equation",
    "kp_quadratic_medium": "quadratic_equation",
    "kp_quadratic_hard": "quadratic_equation",
    "kp_function_easy": "function",
    "kp_function_medium": "function",
    "kp_function_hard": "function",
}


class AssessmentService:
    """
    评估服务

    提供诊断性评估、形成性评估和总结性评估的完整支持。
    集成 BKT 模型进行知识点掌握度估计，通过错误模式分析
    识别常见学习误区。
    """

    def __init__(self) -> None:
        self._redis = get_redis_client() if settings.redis_url else None
        self._redis_available = False
        self._memory_store: dict[str, dict] = {}
        self._item_index: dict[str, AssessmentItem] = {item.id: item for item in _ITEM_BANK}
        self._kp_items: dict[str, list[AssessmentItem]] = {}
        for item in _ITEM_BANK:
            self._kp_items.setdefault(item.kp_id, []).append(item)

    # ──────────────────────────────────────────────────────────
    # Redis 持久化
    # ──────────────────────────────────────────────────────────

    def _get_assessment_key(self, assessment_id: str) -> str:
        return f"{_ASSESSMENT_KEY_PREFIX}instance:{assessment_id}"

    def _get_result_key(self, result_id: str) -> str:
        return f"{_ASSESSMENT_KEY_PREFIX}result:{result_id}"

    def _is_redis_available(self) -> bool:
        if self._redis is None:
            return False
        if self._redis_available:
            return True
        try:
            import asyncio

            loop = asyncio.get_event_loop()
            if loop.is_running():
                return False
            loop.run_until_complete(self._redis.ping())
            self._redis_available = True
            return True
        except RuntimeError:
            return False
        except Exception:
            return False

    def _save_assessment(self, assessment_id: str, data: dict) -> None:
        key = self._get_assessment_key(assessment_id)
        if self._is_redis_available():
            try:
                redis: Any = self._redis
                redis.setex(key, _ASSESSMENT_KEY_TTL, json.dumps(data))
                return
            except Exception as e:
                logger.warning(f"Redis save assessment failed: {e}")
        self._memory_store[key] = data

    def _load_assessment(self, assessment_id: str) -> Optional[dict]:
        key = self._get_assessment_key(assessment_id)
        if self._is_redis_available():
            try:
                redis: Any = self._redis
                data = redis.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.warning(f"Redis load assessment failed: {e}")
        return self._memory_store.get(key)

    def _save_result(self, result_id: str, data: dict) -> None:
        key = self._get_result_key(result_id)
        if self._is_redis_available():
            try:
                redis: Any = self._redis
                redis.setex(key, _ASSESSMENT_KEY_TTL, json.dumps(data))
                return
            except Exception as e:
                logger.warning(f"Redis save result failed: {e}")
        self._memory_store[key] = data

    def _load_result(self, result_id: str) -> Optional[dict]:
        key = self._get_result_key(result_id)
        if self._is_redis_available():
            try:
                redis: Any = self._redis
                data = redis.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.warning(f"Redis load result failed: {e}")
        return self._memory_store.get(key)

    # ──────────────────────────────────────────────────────────
    # 诊断性评估 (Diagnostic)
    # ──────────────────────────────────────────────────────────

    def create_diagnostic(
        self,
        user_id: str,
        subject: str,
        kp_ids: list[str],
    ) -> dict:
        """
        创建诊断性评估 — 课前测试，用于识别知识盲区。

        策略：选取难度 0.2~0.5 的题目，覆盖所有指定知识点，
        以基础题和中等题为主，快速定位学生的薄弱环节。

        Args:
            user_id: 用户 ID
            subject: 学科 (e.g., "algebra")
            kp_ids: 需要评估的知识点 ID 列表

        Returns:
            包含评估 ID 和题目列表的字典
        """
        config = AssessmentConfig(
            assessment_type="diagnostic",
            subject=subject,
            kp_ids=kp_ids,
            difficulty_range=(0.1, 0.5),
            item_count=min(30, len(kp_ids) * 3),
            time_limit_sec=600,
        )

        items = self._select_items(
            kp_ids=kp_ids,
            difficulty_range=(0.1, 0.5),
            count=config.item_count,
            subject=subject,
        )

        assessment_id = f"diag_{uuid.uuid4().hex[:12]}"

        data = {
            "assessment_id": assessment_id,
            "user_id": user_id,
            "assessment_type": "diagnostic",
            "subject": subject,
            "kp_ids": kp_ids,
            "config": {
                "difficulty_range": [0.1, 0.5],
                "item_count": config.item_count,
                "time_limit_sec": config.time_limit_sec,
            },
            "items": [self._item_to_dict(item) for item in items],
            "created_at": time.time(),
            "status": "created",
        }

        self._save_assessment(assessment_id, data)
        logger.info(f"Diagnostic assessment created: {assessment_id} for user {user_id}")

        return {
            "assessment_id": assessment_id,
            "assessment_type": "diagnostic",
            "subject": subject,
            "item_count": len(items),
            "items": data["items"],
            "time_limit_sec": config.time_limit_sec,
        }

    # ──────────────────────────────────────────────────────────
    # 形成性评估 (Formative)
    # ──────────────────────────────────────────────────────────

    def run_formative(
        self,
        user_id: str,
        session_id: str,
        quiz_results: list[dict],
    ) -> dict:
        """
        处理形成性评估 — 课中微测结果。

        接收来自 Quiz 引擎的答题结果，实时更新知识点掌握度，
        并返回当前学习状态和下一步推荐。

        Args:
            user_id: 用户 ID
            session_id: 学习会话 ID
            quiz_results: Quiz 答题结果列表，每项包含:
                - kp_id: 知识点 ID
                - item_id: 题目 ID
                - is_correct: 是否答对
                - response_time_ms: 响应时间
                - selected_option: 选择的选项

        Returns:
            包含掌握度更新和推荐的字典
        """
        if not quiz_results:
            return {
                "session_id": session_id,
                "mastery_updates": {},
                "recommendations": [],
                "message": "没有需要处理的答题结果",
            }

        item_results: list[ItemResult] = []
        kp_updates: dict[str, list[bool]] = {}

        for result in quiz_results:
            item_result = ItemResult(
                item_id=result.get("item_id", ""),
                kp_id=result.get("kp_id", ""),
                user_answer=result.get("user_answer", ""),
                is_correct=result.get("is_correct", False),
                response_time_ms=result.get("response_time_ms", 0),
                selected_option=result.get("selected_option"),
            )
            item_results.append(item_result)
            kp_updates.setdefault(item_result.kp_id, []).append(item_result.is_correct)

        # SYS04 不拥有 mastery 或 teaching recommendation。保留空字段仅兼容旧调用方；
        # canonical 结果通过 assessment.result.project outbox 交给 SYS03。
        mastery_updates: dict[str, float] = {}
        recommendations: list[dict] = []

        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "assessment_type": "formative",
            "item_results": [self._item_result_to_dict(ir) for ir in item_results],
            "mastery_updates": mastery_updates,
            "recommendations": recommendations,
            "processed_at": time.time(),
        }

        self._save_assessment(session_id, session_data)
        logger.info(
            f"Formative assessment processed: session={session_id}, "
            f"items={len(item_results)}, learner_projection=pending"
        )

        return {
            "session_id": session_id,
            "mastery_updates": mastery_updates,
            "recommendations": recommendations,
            "total_items": len(item_results),
        }

    # ──────────────────────────────────────────────────────────
    # 总结性评估 (Summative)
    # ──────────────────────────────────────────────────────────

    def create_summative(
        self,
        user_id: str,
        subject: str,
        kp_ids: list[str],
        mastery_data: Optional[dict[str, float]] = None,
    ) -> dict:
        """
        创建总结性评估 — 课后综合测试。

        策略：根据知识点掌握度数据动态选题，掌握度高的知识点
        选较难题，掌握度低的知识点选基础题，确保全面考察。

        Args:
            user_id: 用户 ID
            subject: 学科
            kp_ids: 需要评估的知识点 ID 列表
            mastery_data: 各知识点的当前掌握度 (可选)

        Returns:
            包含评估 ID 和题目列表的字典
        """
        if mastery_data is None:
            mastery_data = {}

        item_count = min(30, len(kp_ids) * 4)

        items = self._select_items_adaptive(
            kp_ids=kp_ids,
            mastery_data=mastery_data,
            total_count=item_count,
        )

        assessment_id = f"summ_{uuid.uuid4().hex[:12]}"

        data = {
            "assessment_id": assessment_id,
            "user_id": user_id,
            "assessment_type": "summative",
            "subject": subject,
            "kp_ids": kp_ids,
            "mastery_data": mastery_data,
            "config": {
                "difficulty_strategy": "adaptive",
                "item_count": item_count,
                "time_limit_sec": 900,
            },
            "items": [self._item_to_dict(item) for item in items],
            "created_at": time.time(),
            "status": "created",
        }

        self._save_assessment(assessment_id, data)
        logger.info(
            f"Summative assessment created: {assessment_id} for user {user_id}, "
            f"items={len(items)}"
        )

        return {
            "assessment_id": assessment_id,
            "assessment_type": "summative",
            "subject": subject,
            "item_count": len(items),
            "items": data["items"],
            "time_limit_sec": 900,
        }

    # ──────────────────────────────────────────────────────────
    # 评分与掌握度估计
    # ──────────────────────────────────────────────────────────

    def grade_assessment(
        self,
        assessment_id: str,
        answers: dict[str, str],
    ) -> AssessmentResult:
        """
        批改评估答卷，自动评分并计算知识点掌握度估计。

        Args:
            assessment_id: 评估 ID
            answers: 答案字典 {item_id: user_answer}

        Returns:
            AssessmentResult 评估结果对象
        """
        assessment_data = self._load_assessment(assessment_id)
        if assessment_data is None:
            raise ValueError(f"Assessment not found: {assessment_id}")

        items_data = assessment_data.get("items", [])
        item_results: list[ItemResult] = []
        correct_count = 0

        for item_data in items_data:
            item_id = item_data["id"]
            user_answer = answers.get(item_id, "")
            correct_answer = item_data.get("correct_answer", "")
            item_type = item_data.get("type", "")
            kp_id = item_data.get("kp_id", "")

            is_correct = self._check_answer(user_answer, correct_answer, item_type)
            if is_correct:
                correct_count += 1

            item_results.append(
                ItemResult(
                    item_id=item_id,
                    kp_id=kp_id,
                    user_answer=user_answer,
                    is_correct=is_correct,
                    response_time_ms=0,
                )
            )

        total = len(items_data)
        score = round(correct_count / total, 4) if total > 0 else 0.0

        # Legacy result column remains for schema compatibility but is no longer a truth source.
        mastery_estimates: dict[str, float] = {}

        misconceptions = self._detect_misconceptions(item_results)

        result_id = f"res_{uuid.uuid4().hex[:12]}"

        result = AssessmentResult(
            id=result_id,
            user_id=assessment_data.get("user_id", ""),
            assessment_type=assessment_data.get("assessment_type", ""),
            total_items=total,
            correct_count=correct_count,
            score=score,
            mastery_estimates=mastery_estimates,
            misconceptions=misconceptions,
            item_results=item_results,
        )

        saved_data = result.to_dict()
        saved_data["graded_at"] = time.time()
        self._save_result(result_id, saved_data)

        logger.info(
            f"Assessment graded: {assessment_id}, score={score:.2f}, "
            f"correct={correct_count}/{total}, misconceptions={len(misconceptions)}"
        )

        return result

    # ──────────────────────────────────────────────────────────
    # 学习报告生成
    # ──────────────────────────────────────────────────────────

    def generate_report(self, result_id: str) -> dict:
        """
        基于评估结果生成结构化学习报告。

        报告包含：
        - 总体表现分析
        - 各知识点掌握度详情
        - 常见误区诊断
        - 学习建议与下一步行动

        Args:
            result_id: 评估结果 ID

        Returns:
            结构化学习报告字典
        """
        result_data = self._load_result(result_id)
        if result_data is None:
            raise ValueError(f"Result not found: {result_id}")

        score = result_data.get("score", 0.0)
        mastery_estimates = result_data.get("mastery_estimates", {})
        misconceptions = result_data.get("misconceptions", [])
        assessment_type = result_data.get("assessment_type", "")

        if score >= 0.85:
            level = "excellent"
            summary = "表现优秀，已达到掌握标准"
        elif score >= 0.7:
            level = "good"
            summary = "表现良好，个别知识点需要巩固"
        elif score >= 0.5:
            level = "passing"
            summary = "基本合格，存在明显的知识漏洞"
        else:
            level = "needs_improvement"
            summary = "需要加强学习，基础知识掌握不牢"

        kp_details: list[dict] = []
        for kp_id, p in mastery_estimates.items():
            status = "mastered" if p >= 0.85 else "learning" if p >= 0.5 else "weak"
            kp_details.append(
                {
                    "kp_id": kp_id,
                    "mastery": round(p, 4),
                    "status": status,
                }
            )

        kp_details.sort(key=lambda x: x["mastery"])

        recommendations: list[dict] = []
        for kp in kp_details:
            if kp["status"] == "weak":
                recommendations.append(
                    {
                        "kp_id": kp["kp_id"],
                        "action": "remediation",
                        "description": f"针对 {kp['kp_id']} 进行专项练习，掌握度仅 {kp['mastery']:.0%}",
                        "priority": "high",
                    }
                )
            elif kp["status"] == "learning":
                recommendations.append(
                    {
                        "kp_id": kp["kp_id"],
                        "action": "practice",
                        "description": f"继续巩固 {kp['kp_id']}，通过更多练习达到掌握",
                        "priority": "medium",
                    }
                )

        if not recommendations:
            recommendations.append(
                {
                    "action": "challenge",
                    "description": "所有知识点均已掌握，建议挑战更高难度题目",
                    "priority": "low",
                }
            )

        report = {
            "report_id": f"rpt_{result_id}",
            "result_id": result_id,
            "assessment_type": assessment_type,
            "summary": summary,
            "performance_level": level,
            "overall_score": round(score, 4),
            "total_items": result_data.get("total_items", 0),
            "correct_count": result_data.get("correct_count", 0),
            "mastery_details": kp_details,
            "misconceptions": misconceptions,
            "recommendations": recommendations,
            "generated_at": time.time(),
        }

        logger.info(
            f"Report generated: result={result_id}, level={level}, "
            f"recommendations={len(recommendations)}"
        )

        return report

    # ──────────────────────────────────────────────────────────
    # 内部方法
    # ──────────────────────────────────────────────────────────

    def _select_items(
        self,
        kp_ids: list[str],
        difficulty_range: tuple[float, float],
        count: int,
        subject: str,
    ) -> list[AssessmentItem]:
        """
        从题库中选题，保证难度均衡和知识点覆盖。

        策略：
        1. 计算每个知识点的目标题目数
        2. 从每个知识点的题目池中按难度筛选
        3. 当可用题数不足时，从相邻难度区间补充

        Args:
            kp_ids: 知识点 ID 列表
            difficulty_range: 难度范围 (min, max)
            count: 目标题目数
            subject: 学科

        Returns:
            选中的题目列表
        """
        selected: list[AssessmentItem] = []
        min_diff, max_diff = difficulty_range

        if not kp_ids:
            return selected

        per_kp = max(1, count // len(kp_ids))
        remainder = count % len(kp_ids)

        for idx, kp_id in enumerate(kp_ids):
            kp_items = self._kp_items.get(kp_id, [])
            if not kp_items:
                continue

            target = per_kp + (1 if idx < remainder else 0)

            in_range = [item for item in kp_items if min_diff <= item.difficulty <= max_diff]
            if not in_range:
                extended_min = max(0.0, min_diff - 0.2)
                extended_max = min(1.0, max_diff + 0.2)
                in_range = [
                    item for item in kp_items if extended_min <= item.difficulty <= extended_max
                ]
            if not in_range:
                in_range = list(kp_items)

            in_range.sort(key=lambda x: x.difficulty)

            chosen = in_range[:target]
            if len(chosen) < target:
                for item in in_range:
                    if item not in chosen and len(chosen) < target:
                        chosen.append(item)

            selected.extend(chosen)

        if len(selected) < count:
            used_ids = {item.id for item in selected}
            all_candidates = [
                item
                for item in _ITEM_BANK
                if item.id not in used_ids and min_diff - 0.1 <= item.difficulty <= max_diff + 0.1
            ]
            all_candidates.sort(key=lambda x: (x.difficulty, x.id))
            for item in all_candidates:
                if len(selected) >= count:
                    break
                selected.append(item)

        return selected[:count]

    def _select_items_adaptive(
        self,
        kp_ids: list[str],
        mastery_data: dict[str, float],
        total_count: int,
    ) -> list[AssessmentItem]:
        """
        自适应选题：根据掌握度调整难度。

        - 掌握度 < 0.3 → 难度 0.1~0.4 (基础)
        - 掌握度 0.3~0.7 → 难度 0.3~0.7 (中等)
        - 掌握度 > 0.7 → 难度 0.6~0.9 (挑战)

        Args:
            kp_ids: 知识点 ID 列表
            mastery_data: 各知识点掌握度
            total_count: 总题目数

        Returns:
            选中的题目列表
        """
        items: list[AssessmentItem] = []
        per_kp = max(1, total_count // len(kp_ids))

        for kp_id in kp_ids:
            p = mastery_data.get(kp_id, 0.3)

            if p < 0.3:
                diff_range = (0.0, 0.4)
            elif p < 0.7:
                diff_range = (0.25, 0.7)
            else:
                diff_range = (0.5, 0.95)

            kp_items = self._kp_items.get(kp_id, [])
            if not kp_items:
                continue

            min_diff, max_diff = diff_range
            candidates = [item for item in kp_items if min_diff <= item.difficulty <= max_diff]
            if not candidates:
                candidates = list(kp_items)

            candidates.sort(key=lambda x: x.difficulty)
            items.extend(candidates[:per_kp])

        return items[:total_count]

    def _compute_mastery_estimates(
        self,
        item_results: list[ItemResult],
        kp_mastery: dict[str, float],
    ) -> dict[str, float]:
        """
        基于 BKT 模型计算各知识点的掌握度估计。

        结合当前答题表现和已有掌握度数据，使用 BKT 更新规则
        计算每个知识点的后验掌握概率。

        Args:
            item_results: 答题结果列表
            kp_mastery: 各知识点的当前掌握度 {kp_id: p}

        Returns:
            更新后的掌握度估计 {kp_id: p}
        """
        KT_P_INIT = 0.3
        KT_P_TRANSIT = 0.15
        KT_P_SLIP = 0.1

        grouped: dict[str, list[ItemResult]] = {}
        for result in item_results:
            grouped.setdefault(result.kp_id, []).append(result)

        estimates: dict[str, float] = {}

        for kp_id, results in grouped.items():
            p = kp_mastery.get(kp_id, KT_P_INIT)

            for result in results:
                if result.is_correct:
                    p_gain = (1.0 - p) * KT_P_TRANSIT
                    p = min(1.0, p + p_gain)
                else:
                    p_loss = p * KT_P_SLIP
                    p = max(0.0, p - p_loss)

            estimates[kp_id] = round(p, 4)

        for kp_id in kp_mastery:
            if kp_id not in estimates:
                estimates[kp_id] = round(kp_mastery[kp_id], 4)

        return estimates

    def _detect_misconceptions(
        self,
        item_results: list[ItemResult],
    ) -> list[str]:
        """
        分析答题错误模式，识别常见学习误区。

        根据错题所属的知识点类别，匹配预设的误区模式库，
        输出诊断性的误区描述。

        Args:
            item_results: 答题结果列表

        Returns:
            检测到的误区描述列表
        """
        wrong_kps: dict[str, int] = {}
        for result in item_results:
            if not result.is_correct:
                wrong_kps[result.kp_id] = wrong_kps.get(result.kp_id, 0) + 1

        if not wrong_kps:
            return []

        misconceptions: list[str] = []
        seen: set[str] = set()

        for kp_id, wrong_count in wrong_kps.items():
            category = _KP_TO_MISCONCEPTION_KEY.get(kp_id)
            if category and wrong_count >= 2:
                patterns = _MISCONCEPTION_PATTERNS.get(category, [])
                for pattern in patterns:
                    if pattern not in seen:
                        misconceptions.append(f"[{category}] {pattern}")
                        seen.add(pattern)

        for kp_id, wrong_count in wrong_kps.items():
            if wrong_count >= 3:
                generic = f"知识点 {kp_id} 连续 {wrong_count} 题出错，建议回顾基础概念"
                if generic not in seen:
                    misconceptions.append(generic)
                    seen.add(generic)

        return misconceptions

    # ──────────────────────────────────────────────────────────
    # 工具方法
    # ──────────────────────────────────────────────────────────

    def _check_answer(
        self,
        user_answer: str,
        correct_answer: str,
        item_type: str,
    ) -> bool:
        """
        检查用户答案是否正确。

        对于选择题，直接比较；对于填空/简答题，做模糊匹配。

        Args:
            user_answer: 用户答案
            correct_answer: 正确答案
            item_type: 题目类型

        Returns:
            是否正确
        """
        if not user_answer or not correct_answer:
            return False

        norm_user = self._normalize_answer(user_answer)
        norm_correct = self._normalize_answer(correct_answer)

        if item_type == "mcq":
            return norm_user == norm_correct

        if item_type == "fill_blank":
            if norm_user == norm_correct:
                return True
            correct_parts = [self._normalize_answer(p.strip()) for p in correct_answer.split(",")]
            correct_parts = [p for p in correct_parts if p]
            if norm_user in correct_parts:
                return True
            if norm_correct in norm_user or norm_user in norm_correct:
                return True
            return False

        if item_type in ("short_answer", "problem_solving"):
            if norm_user == norm_correct:
                return True
            if self._similarity(norm_user, norm_correct) > 0.85:
                return True
            correct_parts = [self._normalize_answer(p.strip()) for p in correct_answer.split(",")]
            for part in correct_parts:
                if part and self._similarity(norm_user, part) > 0.85:
                    return True
            return False

        return norm_user == norm_correct

    @staticmethod
    def _normalize_answer(answer: str) -> str:
        return " ".join(answer.strip().lower().split())

    @staticmethod
    def _similarity(a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        if a == b:
            return 1.0
        len_a, len_b = len(a), len(b)
        if abs(len_a - len_b) > max(len_a, len_b) * 0.3:
            return 0.0
        matches = sum(1 for ca, cb in zip(a, b, strict=False) if ca == cb)
        return matches / max(len_a, len_b)

    @staticmethod
    def _item_to_dict(item: AssessmentItem) -> dict:
        return {
            "id": item.id,
            "kp_id": item.kp_id,
            "type": item.type,
            "question": item.question,
            "options": item.options,
            "correct_answer": item.correct_answer,
            "difficulty": item.difficulty,
            "cognitive_level": item.cognitive_level,
        }

    @staticmethod
    def _item_result_to_dict(result: ItemResult) -> dict:
        return {
            "item_id": result.item_id,
            "kp_id": result.kp_id,
            "user_answer": result.user_answer,
            "is_correct": result.is_correct,
            "response_time_ms": result.response_time_ms,
            "selected_option": result.selected_option,
        }


# 单例模式
_assessment_service: Optional[AssessmentService] = None


def get_assessment_service() -> AssessmentService:
    """获取评估服务单例"""
    global _assessment_service
    if _assessment_service is None:
        _assessment_service = AssessmentService()
    return _assessment_service

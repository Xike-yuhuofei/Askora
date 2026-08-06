"""
Drill (练习) 教学引擎

特点：
1. 变式练习：基于核心知识点生成多种变体题目
2. 错题巩固：优先练习学生做错的题目
3. 自适应难度：根据答题表现动态调整题目难度
4. 即时反馈：提供即时的对错判定和针对性指导
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Optional

from app.core.logging import get_logger
from app.engines._registry import register_engine
from app.engines.base import (
    CognitiveLevel,
    EngineSideEffect,
    EngineStepResult,
    FlowStage,
    LearnerTurn,
    SharedContext,
    TaskOpenness,
    TeachingEngine,
    TransitionSuggestion,
    TransitionType,
)

logger = get_logger(__name__)


@dataclass
class ErrorBookEntry:
    """错题本条目"""

    question_id: str
    wrong_count: int = 0
    last_wrong_at: float = 0.0
    user_answer: str = ""
    error_type: str = ""  # calculation_error, concept_error, careless_error
    variant_generated: bool = False


@dataclass
class DrillEngineState:
    """Drill 引擎的私有状态"""

    current_question: Optional[dict] = None
    question_answered: bool = False

    mastered_questions: list[str] = field(default_factory=list)
    wrong_questions: list[str] = field(default_factory=list)
    error_book: dict[str, ErrorBookEntry] = field(default_factory=dict)

    total_attempts: int = 0
    correct_count: int = 0
    wrong_count: int = 0
    consecutive_correct: int = 0
    consecutive_wrong: int = 0

    current_difficulty: int = 2
    dialogue_history: list[dict] = field(default_factory=list)
    turn_count: int = 0


@register_engine
class DrillEngine(TeachingEngine[DrillEngineState]):
    """练习引擎 (Drill Engine)"""

    engine_id: str = "drill"
    engine_name: str = "练习引擎"
    supported_cognitive_levels: list[CognitiveLevel] = [
        CognitiveLevel.PRACTICE,
        CognitiveLevel.CREATE,
    ]
    supported_openness: list[TaskOpenness] = [TaskOpenness.CLOSED, TaskOpenness.SEMI_STRUCTURED]

    def __init__(self):
        # 预置题库 (MVP 阶段，后续将接入数据库)
        self._question_bank = self._build_question_bank()

    def _build_question_bank(self) -> dict:
        """构建预置题库"""
        return {
            "algebra_linear": [
                {
                    "id": "alg_lin_001",
                    "type": "choice",
                    "difficulty": 1,
                    "content": "方程 x + 5 = 12 的解是：",
                    "options": ["A. x = 5", "B. x = 7", "C. x = 17", "D. x = 60"],
                    "answer": "B",
                    "explanation": "移项得 x = 12 - 5 = 7",
                    "knowledge_point": "kp_algebra_transposition",
                },
                {
                    "id": "alg_lin_002",
                    "type": "choice",
                    "difficulty": 2,
                    "content": "方程 3x - 7 = 2x + 5 的解是：",
                    "options": ["A. x = 10", "B. x = 12", "C. x = 2", "D. x = -2"],
                    "answer": "A",
                    "explanation": "移项得 3x - 2x = 5 + 7, x = 12",
                    "knowledge_point": "kp_algebra_transposition",
                },
                {
                    "id": "alg_lin_003",
                    "type": "short_answer",
                    "difficulty": 2,
                    "content": "解方程：2(x - 3) = 4x + 6",
                    "answer": "x = -6",
                    "explanation": "展开得 2x - 6 = 4x + 6，移项得 -2x = 12，x = -6",
                    "knowledge_point": "kp_algebra_transposition",
                },
                {
                    "id": "alg_lin_004",
                    "type": "choice",
                    "difficulty": 3,
                    "content": "若方程 (a-1)x = 3 是一元一次方程，则 a 的值为：",
                    "options": ["A. a = 1", "B. a ≠ 1", "C. a = 0", "D. a ≠ 0"],
                    "answer": "B",
                    "explanation": "一元一次方程要求系数不为0，所以 a - 1 ≠ 0，即 a ≠ 1",
                    "knowledge_point": "kp_algebra_linear_equation",
                },
                {
                    "id": "alg_lin_005",
                    "type": "short_answer",
                    "difficulty": 3,
                    "content": "解方程：(x/2) + (x/3) = 10",
                    "answer": "x = 12",
                    "explanation": "通分得 3x/6 + 2x/6 = 10，5x/6 = 10，x = 12",
                    "knowledge_point": "kp_algebra_linear_equation",
                },
            ],
            "geometry_pythagorean": [
                {
                    "id": "geo_pyth_001",
                    "type": "choice",
                    "difficulty": 1,
                    "content": "直角三角形两条直角边分别为 3cm 和 4cm，斜边长度为：",
                    "options": ["A. 5cm", "B. 6cm", "C. 7cm", "D. 12cm"],
                    "answer": "A",
                    "explanation": "根据勾股定理：c² = 3² + 4² = 9 + 16 = 25，c = 5cm",
                    "knowledge_point": "kp_geometry_pythagorean",
                },
                {
                    "id": "geo_pyth_002",
                    "type": "short_answer",
                    "difficulty": 2,
                    "content": "直角三角形斜边为 13cm，一条直角边为 5cm，另一条直角边为多少？",
                    "answer": "12cm",
                    "explanation": "根据勾股定理：b² = 13² - 5² = 169 - 25 = 144，b = 12cm",
                    "knowledge_point": "kp_geometry_pythagorean",
                },
            ],
        }

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------
    async def on_enter(self, shared_ctx: SharedContext) -> None:
        """进入练习引擎时初始化状态"""
        logger.info("DrillEngine initialized for practice session")

    # ------------------------------------------------------------------
    # can_handle
    # ------------------------------------------------------------------
    async def can_handle(self, flow_stage: FlowStage, shared_ctx: SharedContext) -> float:
        # Drill 引擎专门用于 DRILL 阶段
        if flow_stage == FlowStage.DRILL:
            return 0.95

        # 在其他阶段也可处理，但评分较低
        stage_scores = {
            FlowStage.VALIDATE: 0.5,
            FlowStage.LEARN: 0.3,
            FlowStage.INQUIRE: 0.2,
            FlowStage.DIAGNOSE: 0.1,
            FlowStage.PRODUCE: 0.1,
        }
        return stage_scores.get(flow_stage, 0.2)

    # ------------------------------------------------------------------
    # build_initial_state
    # ------------------------------------------------------------------
    def build_initial_state(self, shared_ctx: SharedContext) -> DrillEngineState:
        """初始化练习引擎状态"""
        return DrillEngineState(
            current_question=None,
            question_answered=False,
            mastered_questions=[],
            wrong_questions=[],
            total_attempts=0,
            correct_count=0,
            wrong_count=0,
            consecutive_correct=0,
            consecutive_wrong=0,
        )

    # ------------------------------------------------------------------
    # step
    # ------------------------------------------------------------------
    async def step(
        self,
        learner_input: LearnerTurn,
        flow_stage: FlowStage,
        shared_ctx: SharedContext,
        engine_state: DrillEngineState,
    ) -> EngineStepResult:
        t0 = time.time()

        user_text = learner_input.text.strip()
        # 如果当前没有题目，生成第一道题
        if not engine_state.current_question or engine_state.question_answered:
            question = self._select_next_question(engine_state, shared_ctx)
            engine_state.current_question = question
            engine_state.question_answered = False

            # 输出题目
            reply_text = self._format_question(question)
            gen_ms = int((time.time() - t0) * 1000)

            return self._build_step_result(
                reply_text=reply_text,
                engine_state=engine_state,
                mastery_delta=0.0,
                generation_ms=gen_ms,
                reason="question_presented",
            )

        # 有题目等待作答
        question = engine_state.current_question
        is_correct = self._check_answer(user_text, question)

        # 更新统计
        engine_state.total_attempts += 1
        engine_state.question_answered = True

        if is_correct:
            engine_state.correct_count += 1
            engine_state.consecutive_correct += 1
            engine_state.consecutive_wrong = 0
            mastery_delta = 0.05
            qid = question["id"]
            if qid in engine_state.error_book:
                engine_state.error_book[qid].wrong_count = max(
                    0, engine_state.error_book[qid].wrong_count - 1
                )
                if engine_state.error_book[qid].wrong_count <= 0:
                    engine_state.mastered_questions.append(qid)
                    engine_state.error_book.pop(qid, None)
            (
                engine_state.mastered_questions.append(qid)
                if qid not in engine_state.mastered_questions
                else None
            )
        else:
            engine_state.wrong_count += 1
            engine_state.consecutive_wrong += 1
            engine_state.consecutive_correct = 0
            mastery_delta = -0.03
            qid = question["id"]
            engine_state.wrong_questions.append(qid)
            error_type = self._classify_error(user_text, question)
            if qid in engine_state.error_book:
                engine_state.error_book[qid].wrong_count += 1
                engine_state.error_book[qid].last_wrong_at = time.time()
                engine_state.error_book[qid].user_answer = user_text
                engine_state.error_book[qid].error_type = error_type
            else:
                engine_state.error_book[qid] = ErrorBookEntry(
                    question_id=qid,
                    wrong_count=1,
                    last_wrong_at=time.time(),
                    user_answer=user_text,
                    error_type=error_type,
                )

        # 构建反馈
        feedback = self._build_feedback(is_correct, question, engine_state)

        # 更新对话历史
        engine_state.turn_count += 1
        engine_state.dialogue_history.extend(
            [
                {"role": "user", "content": user_text, "turn": engine_state.turn_count},
                {"role": "assistant", "content": feedback, "turn": engine_state.turn_count},
            ]
        )

        gen_ms = int((time.time() - t0) * 1000)

        # 决定是否继续出题或结束
        total_questions = engine_state.correct_count + engine_state.wrong_count

        if total_questions >= 5 or engine_state.consecutive_correct >= 3:
            # 达到练习目标，建议切换回苏格拉底引擎
            transition = TransitionSuggestion(
                type=TransitionType.SWITCH_AND_RETURN,
                target_engine_id="socratic",
                extra_context={
                    "practice_summary": {
                        "total": total_questions,
                        "correct": engine_state.correct_count,
                        "accuracy": engine_state.correct_count / max(total_questions, 1),
                    }
                },
                reason="practice_session_complete",
            )
        else:
            transition = TransitionSuggestion(
                type=TransitionType.STAY,
                reason="continue_practice",
            )

        return EngineStepResult(
            reply_text=feedback,
            engine_state_update={
                "current_question": engine_state.current_question,
                "question_answered": engine_state.question_answered,
                "total_attempts": engine_state.total_attempts,
                "correct_count": engine_state.correct_count,
                "wrong_count": engine_state.wrong_count,
                "consecutive_correct": engine_state.consecutive_correct,
                "consecutive_wrong": engine_state.consecutive_wrong,
            },
            side_effects=EngineSideEffect(
                mastery_updates=(
                    {shared_ctx.knowledge_point_id: mastery_delta}
                    if shared_ctx.knowledge_point_id
                    else {}
                ),
                wrong_streak_delta=(
                    1
                    if not is_correct
                    else (-engine_state.wrong_count if engine_state.wrong_count > 0 else 0)
                ),
                extra={
                    "drill_question_id": question["id"],
                    "drill_is_correct": is_correct,
                    "drill_total_correct": engine_state.correct_count,
                    "drill_total_wrong": engine_state.wrong_count,
                },
            ),
            transition=transition,
            generation_ms=gen_ms,
            engine_debug_info={
                "question_id": question["id"],
                "question_difficulty": question["difficulty"],
                "is_correct": is_correct,
                "total_attempts": engine_state.total_attempts,
            },
        )

    def _classify_error(self, user_answer: str, question: dict) -> str:
        """分析错误类型"""
        import re

        correct_numbers = re.findall(r"[\d.]+", question["answer"].strip().upper())
        user_numbers = re.findall(r"[\d.]+", user_answer.strip().upper())

        if question["type"] == "short_answer" and correct_numbers and user_numbers:
            try:
                correct_val = float(correct_numbers[0])
                user_val = float(user_numbers[0])
                if abs(correct_val - user_val) < 0.5 and abs(correct_val - user_val) > 0.01:
                    return "calculation_error"
            except ValueError:
                pass

        if user_answer.strip().upper() in question.get("answer", "").strip().upper():
            return "careless_error"

        return "concept_error"

    def _generate_variant(self, base_question: dict) -> dict:
        """生成变式练习"""
        import random

        variant = dict(base_question)
        variant["id"] = base_question["id"] + "_v" + str(random.randint(100, 999))

        if base_question["type"] == "choice":
            nums = re.findall(r"[\d.]+", base_question["content"])
            if len(nums) >= 2:
                try:
                    a, b = float(nums[0]), float(nums[1])
                    op = random.choice(["+", "-", "×"])
                    if op == "+":
                        new_content = base_question["content"].replace(
                            f"{a} {op} {b}", f"{a} {op} {b + random.choice([1, 2, 3])}"
                        )
                    elif op == "-":
                        new_content = base_question["content"]
                    else:
                        new_content = base_question["content"]
                    variant["content"] = new_content
                except (ValueError, IndexError):
                    pass

        variant["is_variant"] = True
        variant["base_id"] = base_question["id"]
        variant["difficulty"] = min(base_question["difficulty"] + 1, 5)
        return variant

    def _update_difficulty(self, engine_state: DrillEngineState) -> int:
        """自适应调整难度"""
        if engine_state.consecutive_correct >= 3:
            engine_state.current_difficulty = min(5, engine_state.current_difficulty + 1)
        elif engine_state.consecutive_wrong >= 2:
            engine_state.current_difficulty = max(1, engine_state.current_difficulty - 1)
        return engine_state.current_difficulty

    # ==================================================================
    # Internal helpers
    # ==================================================================
    def _select_next_question(
        self,
        engine_state: DrillEngineState,
        shared_ctx: SharedContext,
    ) -> dict:
        """选择下一道练习题（优先错题本 → 变式练习 → 自适应难度）"""
        import random

        self._update_difficulty(engine_state)

        # 1. 优先选择错题本中的高错误频率题目
        if engine_state.error_book:
            sorted_errors = sorted(
                engine_state.error_book.values(),
                key=lambda e: e.wrong_count,
                reverse=True,
            )
            for entry in sorted_errors:
                if entry.wrong_count >= 2 and not entry.variant_generated:
                    for subject_questions in self._question_bank.values():
                        for q in subject_questions:
                            if q["id"] == entry.question_id:
                                variant = self._generate_variant(q)
                                engine_state.error_book[entry.question_id].variant_generated = True
                                return variant

            for entry in sorted_errors:
                if entry.question_id not in engine_state.mastered_questions:
                    for subject_questions in self._question_bank.values():
                        for q in subject_questions:
                            if q["id"] == entry.question_id:
                                return q

        # 2. 根据知识点和自适应难度选择
        kp_id = shared_ctx.knowledge_point_id
        target_diff = engine_state.current_difficulty
        for questions in self._question_bank.values():
            if kp_id and any(q.get("knowledge_point") == kp_id for q in questions):
                candidates = [
                    q
                    for q in questions
                    if q["id"] not in engine_state.mastered_questions
                    and abs(q["difficulty"] - target_diff) <= 1
                ]
                if candidates:
                    return random.choice(candidates)

        # 3. Fallback: 选择题库中的第一道题
        for questions in self._question_bank.values():
            if questions:
                return questions[0]

        return {
            "id": "drill_fallback_001",
            "type": "choice",
            "difficulty": 2,
            "content": "请计算：15 + 27 = ?",
            "options": ["A. 41", "B. 42", "C. 43", "D. 44"],
            "answer": "B",
            "explanation": "15 + 27 = 42",
            "knowledge_point": "general_math",
        }

    def _format_question(self, question: dict) -> str:
        """格式化题目"""
        parts = ["📝 练习题："]

        if question["type"] == "choice":
            parts.append(question["content"])
            parts.extend(question["options"])
        elif question["type"] == "short_answer":
            parts.append(question["content"])
            parts.append("请在下方输入你的答案：")
        else:
            parts.append(question["content"])

        parts.append(f"\n（难度：{'⭐' * question['difficulty']}）")

        return "\n".join(parts)

    def _check_answer(self, user_answer: str, question: dict) -> bool:
        """检查答案是否正确"""
        correct_answer = question["answer"].strip().upper()
        user_answer = user_answer.strip().upper()

        if question["type"] == "choice":
            # 选择题：提取选项字母
            # 处理 "B" 或 "B." 或 "选项B" 等格式
            clean_user = (
                user_answer.replace(".", "").replace("选项", "").replace("答案是", "").strip()
            )
            return clean_user == correct_answer
        elif question["type"] == "short_answer":
            # 简答题：模糊匹配
            # 提取数值部分进行比较
            import re

            # 从正确答案中提取数值
            correct_numbers = re.findall(r"[\d.]+", correct_answer)
            user_numbers = re.findall(r"[\d.]+", user_answer)

            if correct_numbers and user_numbers:
                # 比较第一个数值
                try:
                    correct_val = float(correct_numbers[0])
                    user_val = float(user_numbers[0])
                    return abs(correct_val - user_val) < 0.01
                except ValueError:
                    pass

            # 直接字符串比较
            return user_answer == correct_answer
        else:
            return user_answer == correct_answer

    def _build_feedback(
        self,
        is_correct: bool,
        question: dict,
        engine_state: DrillEngineState,
    ) -> str:
        """构建反馈信息"""
        if is_correct:
            # 正确反馈
            if engine_state.consecutive_correct >= 3:
                praise = "太棒了！你连续答对了好几道题！"
            elif engine_state.consecutive_correct >= 2:
                praise = "做得不错！继续保持！"
            else:
                praise = "回答正确！"

            return praise
        else:
            # 错误反馈：引导思考，不直接给答案
            hints = [
                "再想想看，你可能需要检查一下计算过程。",
                "这个答案不太对。回顾一下我们之前学的方法，再试一次？",
                "注意一下题目的关键条件，是不是漏了什么？",
                "你的思路可能需要调整。试试用另一种方法来思考。",
            ]

            import random

            hint = random.choice(hints)

            if engine_state.consecutive_wrong >= 2:
                hint += "\n别灰心，学习就是在错误中进步的。"

            return f"❌ 不完全正确。{hint}"

    def _build_step_result(
        self,
        reply_text: str,
        engine_state: DrillEngineState,
        mastery_delta: float,
        generation_ms: int,
        reason: str,
    ) -> EngineStepResult:
        """构建标准的 step 返回结果"""
        return EngineStepResult(
            reply_text=reply_text,
            engine_state_update={
                "current_question": engine_state.current_question,
                "question_answered": engine_state.question_answered,
                "total_attempts": engine_state.total_attempts,
                "correct_count": engine_state.correct_count,
                "wrong_count": engine_state.wrong_count,
            },
            side_effects=EngineSideEffect(
                mastery_updates={},
                extra={
                    "drill_engine_phase": reason,
                },
            ),
            transition=TransitionSuggestion(
                type=TransitionType.STAY,
                reason=reason,
            ),
            generation_ms=generation_ms,
            engine_debug_info={
                "phase": reason,
            },
        )


__all__ = ["DrillEngine", "DrillEngineState", "ErrorBookEntry"]

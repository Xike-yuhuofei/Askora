"""
Quiz 测验引擎 (TEI v1 实现)

设计核心：微验证 / 变式练习 / 错题回炉。
作为教学闭环的「检测器」，负责在 Explain/Socratic 之后快速评估掌握度。

典型调度场景：
1. Socratic 进展良好（mastery_delta > 0.04）→ Quiz 出 3 题微验证 → 正确率 > 80% 返回 Socratic 深入
2. Explain 讲完 → Quiz 检查是否真的懂了
3. Drill 阶段的错题回炉（未来扩展）

Quiz engine (TEI implementation). Micro-validation after Explain/Socratic phases.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Optional

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
from app.services.llm.model_router import ChatMessage, ModelRouter, get_model_router

logger = get_logger(__name__)


@dataclass
class QuizQuestion:
    id: str
    type: str  # "mcq" / "short_answer" / "true_false"
    text: str
    options: list[str] = field(default_factory=list)
    correct_answer: str = ""
    explanation: str = ""


@dataclass
class QuizEngineState:
    """Quiz 引擎私有状态"""

    mode: str = "micro_validation"  # "micro_validation" / "drill"
    questions: list[QuizQuestion] = field(default_factory=list)
    current_index: int = 0
    correct_count: int = 0
    answered_count: int = 0
    total_item_count: int = 3  # 默认 3 题
    kp_name_being_quizzed: str = ""
    last_generated_at: float = 0


@register_engine
class QuizEngine(TeachingEngine[QuizEngineState]):
    """测验引擎：微验证 / 变式练习 / 错题回炉"""

    engine_id: str = "quiz"
    engine_name: str = "测验引擎"
    supported_cognitive_levels: list[CognitiveLevel] = [CognitiveLevel.PRACTICE]
    supported_openness: list[TaskOpenness] = [TaskOpenness.CLOSED, TaskOpenness.SEMI_STRUCTURED]

    def __init__(self):
        self._model_router: Optional[ModelRouter] = None

    async def on_enter(self, shared_ctx: SharedContext) -> None:
        _ = self._ensure_router()

    # ------------------------------------------------------------------
    async def can_handle(self, flow_stage: FlowStage, shared_ctx: SharedContext) -> float:
        stage_score = {
            FlowStage.DIAGNOSE: 0.1,
            FlowStage.LEARN: 0.1,
            FlowStage.INQUIRE: 0.2,
            FlowStage.VALIDATE: 1.0,  # Quiz 最适合在 VALIDATE
            FlowStage.DRILL: 0.8,  # Drill 也可以
            FlowStage.PRODUCE: 0.1,
        }.get(flow_stage, 0.2)

        # 如果有 explained_concept_ids，说明刚讲解过，需要验证 → 提升评分
        has_explained = len(shared_ctx.explained_concept_ids) > 0
        explain_bonus = 0.15 if has_explained else 0.0

        # 如果有未解释的断层，降低评分（Explain 优先）
        unexplained = any(
            g.kp_id not in shared_ctx.explained_concept_ids for g in shared_ctx.identified_gaps
        )
        penalty = 0.3 if (shared_ctx.identified_gaps and unexplained) else 0.0

        score = max(0.0, min(1.0, stage_score + explain_bonus - penalty))
        return score

    # ------------------------------------------------------------------
    def build_initial_state(self, shared_ctx: SharedContext) -> QuizEngineState:
        mode = shared_ctx.extras.get("quiz_mode", "micro_validation")
        total_count = int(shared_ctx.extras.get("item_count", 3))
        # 决定 Quiz 结束后返回哪个引擎
        # 如果是 Socratic 建议来的，返回 Socratic；如果是 Explain 建议来的，返回 Explain
        return QuizEngineState(
            mode=mode,
            questions=[],
            current_index=0,
            correct_count=0,
            answered_count=0,
            total_item_count=total_count,
            kp_name_being_quizzed=(
                (shared_ctx.identified_gaps[0].name if shared_ctx.identified_gaps else "")
                or shared_ctx.knowledge_point_id
                or shared_ctx.subject
            ),
            last_generated_at=0,
        )

    # ------------------------------------------------------------------
    async def step(
        self,
        learner_input: LearnerTurn,
        flow_stage: FlowStage,
        shared_ctx: SharedContext,
        engine_state: QuizEngineState,
    ) -> EngineStepResult:
        t0 = time.time()
        router = self._ensure_router()
        provider = router.route_for_subject(shared_ctx.subject or "general")

        # ===== 第一轮：生成题目 =====
        if engine_state.current_index == 0 and not engine_state.questions:
            # 从 extras 获取上一引擎要求的题目数量
            requested_count = int(
                shared_ctx.extras.get("item_count", engine_state.total_item_count)
            )
            engine_state.total_item_count = max(1, min(10, requested_count))
            engine_state.kp_name_being_quizzed = (
                (shared_ctx.identified_gaps[0].name if shared_ctx.identified_gaps else "")
                or shared_ctx.knowledge_point_id
                or shared_ctx.subject
            )

            questions = await self._generate_questions(
                provider=provider,
                subject=shared_ctx.subject or "general",
                kp_name=engine_state.kp_name_being_quizzed,
                count=engine_state.total_item_count,
                persona=shared_ctx.learner_persona,
            )
            engine_state.questions = questions
            engine_state.last_generated_at = time.time()

            if not questions:
                return self._fallback_no_questions(engine_state)

            first_q = questions[0]
            gen_ms = int((time.time() - t0) * 1000)
            return EngineStepResult(
                reply_text=self._format_question(first_q, engine_state, shared_ctx),
                engine_state_update={
                    "mode": engine_state.mode,
                    "questions": [_q_to_dict(q) for q in engine_state.questions],
                    "current_index": 0,
                    "correct_count": 0,
                    "answered_count": 0,
                    "total_item_count": engine_state.total_item_count,
                    "kp_name_being_quizzed": engine_state.kp_name_being_quizzed,
                    "last_generated_at": engine_state.last_generated_at,
                },
                side_effects=EngineSideEffect(),
                transition=TransitionSuggestion(
                    type=TransitionType.STAY, reason="quiz_generated_first_question"
                ),
                generation_ms=gen_ms,
                engine_debug_info={
                    "quiz_mode": engine_state.mode,
                    "total_questions": len(questions),
                    "kp_quizzed": engine_state.kp_name_being_quizzed,
                },
            )

        # ===== 后续轮次：判定答案 =====
        idx = engine_state.current_index
        if idx >= len(engine_state.questions):
            # 题目做完了：看正确率决定下一步
            gen_ms = int((time.time() - t0) * 1000)
            acc = engine_state.correct_count / max(1, engine_state.answered_count)
            pass_threshold = acc >= 0.8
            prev_engine = shared_ctx.extras.get("prev_engine_before_switch", "")

            summary = f"测验完成！共 {engine_state.answered_count} 题，答对 {engine_state.correct_count} 题，正确率 {acc:.0%}。"
            if pass_threshold:
                summary += " 恭喜掌握良好！我们回到原来的学习方式继续深入。"
            else:
                summary += " 看起来有些地方还不太确定，建议重新讲解或再引导一次。"

            transition = TransitionSuggestion(
                type=(
                    TransitionType.SWITCH_TO
                    if prev_engine and prev_engine in {"socratic", "explain"}
                    else TransitionType.STAY
                ),
                target_engine_id=prev_engine if pass_threshold and prev_engine else None,
                extra_context={
                    "quiz_accuracy": round(acc, 3),
                    "correct": engine_state.correct_count,
                    "total": engine_state.answered_count,
                },
                reason=(
                    "quiz_finished_accuracy_below_threshold"
                    if not pass_threshold
                    else "quiz_finished_pass_return_prev"
                ),
            )
            if not pass_threshold:
                # 答错多 → 建议切回 Explain（不是 Socratic，因为需要重新讲解）
                transition.type = TransitionType.SWITCH_TO
                transition.target_engine_id = "explain"
                transition.reason = "quiz_finished_fail_needs_explain_again"

            # 应用掌握度更新到 SharedContext
            mastery_update = {}
            kp_id = shared_ctx.knowledge_point_id or (
                shared_ctx.identified_gaps[0].kp_id if shared_ctx.identified_gaps else ""
            )
            if kp_id:
                delta = 0.08 if pass_threshold else -0.05
                mastery_update[kp_id] = delta

            return EngineStepResult(
                reply_text=summary,
                engine_state_update=self._state_to_dict(engine_state),
                side_effects=EngineSideEffect(
                    mastery_updates=mastery_update,
                    extra={
                        "quiz_summary": {
                            "accuracy": round(acc, 3),
                            "correct": engine_state.correct_count,
                            "total": engine_state.answered_count,
                        },
                    },
                ),
                transition=transition,
                generation_ms=gen_ms,
                engine_debug_info={
                    "quiz_summary": {
                        "accuracy": round(acc, 3),
                        "correct": engine_state.correct_count,
                        "total": engine_state.answered_count,
                    },
                    "pass_threshold": pass_threshold,
                },
            )

        # 判定当前题目的答案
        current_q = engine_state.questions[idx]
        is_correct = self._check_answer(current_q, learner_input.text)
        engine_state.answered_count += 1
        if is_correct:
            engine_state.correct_count += 1

        gen_ms = int((time.time() - t0) * 1000)

        feedback = self._format_feedback(is_correct, current_q)
        engine_state.current_index += 1

        # 如果还有下一题，展示下一题
        if engine_state.current_index < len(engine_state.questions):
            next_q = engine_state.questions[engine_state.current_index]
            reply_text = f"{feedback}\n\n**第 {engine_state.current_index + 1}/{len(engine_state.questions)} 题**：\n\n{self._format_question(next_q, engine_state, shared_ctx)}"
            transition = TransitionSuggestion(
                type=TransitionType.STAY, reason="quiz_answer_continue_next"
            )
        else:
            # 最后一题
            reply_text = feedback
            transition = TransitionSuggestion(
                type=TransitionType.STAY, reason="quiz_answer_last_awaiting_summary"
            )

        return EngineStepResult(
            reply_text=reply_text,
            engine_state_update=self._state_to_dict(engine_state),
            side_effects=EngineSideEffect(extra={"quiz_last_answer_correct": is_correct}),
            transition=transition,
            generation_ms=gen_ms,
            engine_debug_info={
                "quiz_current_index": engine_state.current_index,
                "quiz_is_correct": is_correct,
            },
        )

    # ==================================================================
    # helpers
    # ==================================================================
    async def _generate_questions(
        self,
        provider,
        subject: str,
        kp_name: str,
        count: int,
        persona: str,
    ) -> list[QuizQuestion]:
        persona_lang_map = {
            "preschool": "用简单的口语和短句子",
            "k12_primary": "适合小学生，用词简单",
            "k12_high": "适合中学生，可使用学科术语",
            "higher_ed": "适合大学生，严谨且有深度",
            "professional": "适合职场人士，注重实用场景",
            "adult_general": "适合成人，平衡实用与理论",
            "senior": "适合银发学习者，节奏放慢，避免术语",
            "": "通用水平",
        }
        lang_hint = persona_lang_map.get(persona, persona_lang_map[""])

        system_prompt = f"""你是一位教学测验出题专家。请为知识点「{kp_name or subject}」生成 {count} 道检测学生理解程度的题目。

学科：{subject}
受众：{lang_hint}

要求：
1. 至少包含 50% 的选择题 (mcq)，其余可以是简答题 (short_answer)
2. 每道题必须：
   - 有题干 (text)
   - 选择题有 options 数组 (2-4 个选项)
   - 有 correct_answer (选择题填正确选项内容，简答题填标准答案关键词)
   - 有 explanation (简短的正确答案解释)
3. 不要生成过于冗长的题目，每题题干控制在 1-3 句话
4. 题目难度递增，从基础到进阶

请严格输出 JSON 格式，结构如下：
```json
[
  {{
    "id": "q1",
    "type": "mcq",
    "text": "题干...",
    "options": ["选项A", "选项B", "选项C", "选项D"],
    "correct_answer": "正确选项内容",
    "explanation": "解释..."
  }},
  {{
    "id": "q2",
    "type": "short_answer",
    "text": "题干...",
    "options": [],
    "correct_answer": "标准答案",
    "explanation": "解释..."
  }}
]
```

直接输出 JSON 数组，不要任何额外文字。"""

        user_prompt = f"请为「{kp_name or subject}」生成 {count} 道检测理解的题目。"
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_prompt),
        ]

        try:
            resp = await provider.chat_completion(messages)
            content = (resp.content or "").strip()
            # 提取 JSON（可能有 markdown 包裹）
            questions = self._parse_questions(content)
            logger.info("quiz_questions_generated", count=len(questions), kp=kp_name)
            return questions
        except Exception as exc:  # noqa: BLE001
            logger.exception("quiz_llm_generate_failed", error_type=type(exc).__name__)
            return []

    @staticmethod
    def _parse_questions(content: str) -> list[QuizQuestion]:
        """从 LLM 输出中解析题目 JSON"""
        text = content.strip()
        # 尝试直接解析
        try:
            return QuizEngine._questions_from_json(text)
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

        # 尝试剥离 markdown 代码块
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[-1].strip() == "```":
                lines = lines[1:-1]
            elif lines[0].startswith("```"):
                lines = lines[1:]
            text = "\n".join(lines).strip()

            try:
                return QuizEngine._questions_from_json(text)
            except (json.JSONDecodeError, KeyError, TypeError):
                pass

        # 尝试找第一个 [ 开始到最后一个 ] 结束
        bracket_start = text.find("[")
        bracket_end = text.rfind("]")
        if bracket_start >= 0 and bracket_end > bracket_start:
            json_str = text[bracket_start : bracket_end + 1]
            try:
                return QuizEngine._questions_from_json(json_str)
            except (json.JSONDecodeError, KeyError, TypeError):
                pass

        logger.warning("quiz_question_parse_failed", content_preview=text[:200])
        return []

    @staticmethod
    def _questions_from_json(json_str: str) -> list[QuizQuestion]:
        raw = json.loads(json_str)
        questions = []
        for i, q in enumerate(raw):
            questions.append(
                QuizQuestion(
                    id=q.get("id", f"q{i+1}"),
                    type=q.get("type", "mcq"),
                    text=q.get("text", ""),
                    options=q.get("options", []) or [],
                    correct_answer=q.get("correct_answer", ""),
                    explanation=q.get("explanation", ""),
                )
            )
        return questions

    @staticmethod
    def _check_answer(question, user_text: str) -> bool:
        """判断用户答案是否正确"""
        if isinstance(question, dict):
            question = QuizQuestion(**question)
        if not question.correct_answer:
            return False
        correct = question.correct_answer.strip().lower()
        user = user_text.strip().lower()
        # 对于选择题：只要用户选的选项内容出现在 correct_answer 中，或 correct_answer 出现在用户选项中
        if question.type == "mcq" and question.options:
            # 用户可能输入 "A" / "选项A" / 直接输入选项内容
            for opt in question.options:
                opt_lower = opt.lower()
                if opt_lower == user or user in opt_lower or opt_lower in user:
                    return (
                        opt.strip().lower() == correct.lower()
                        or correct.lower() in opt.strip().lower()
                    )
            # 回退：看 correct_answer 是否在 user_text 中
            return correct in user or user in correct
        # 简答题：关键词匹配
        keywords = [k.strip() for k in correct.replace("，", ",").split(",") if k.strip()]
        if not keywords:
            return correct in user or user in correct
        hit = sum(1 for k in keywords if k in user)
        return hit >= max(1, len(keywords) // 2)

    @staticmethod
    def _format_question(q, state: QuizEngineState, shared: SharedContext) -> str:
        """格式化题目文本给用户"""
        if isinstance(q, dict):
            q = QuizQuestion(**q)
        progress = f"进度 {state.current_index + 1}/{state.total_item_count}"
        lines = [f"**{progress}**", "", q.text]
        if q.type == "mcq" and q.options:
            for i, opt in enumerate(q.options):
                letter = chr(65 + i)
                lines.append(f"  {letter}. {opt}")
            lines.append("\n请输入选项字母 (A/B/C/D) 或直接输入选项内容。")
        elif q.type == "true_false":
            lines.append("\n请输入「是」或「否」。")
        else:
            lines.append("\n请在下方输入你的答案。")
        return "\n".join(lines)

    @staticmethod
    def _format_feedback(is_correct: bool, q) -> str:
        """格式化答题反馈"""
        if isinstance(q, dict):
            q = QuizQuestion(**q)
        if is_correct:
            emoji = "✅"
            prefix = "回答正确！"
        else:
            emoji = "❌"
            prefix = "不太对哦。"
        explanation = f"  \n_解析_：{q.explanation}" if q.explanation else ""
        correct_show = f"  \n_正确答案_：{q.correct_answer}" if not is_correct else ""
        return f"{emoji} {prefix}{correct_show}{explanation}"

    def _state_to_dict(self, state: QuizEngineState) -> dict[str, Any]:
        return {
            "mode": state.mode,
            "questions": [_q_to_dict(q) for q in state.questions],
            "current_index": state.current_index,
            "correct_count": state.correct_count,
            "answered_count": state.answered_count,
            "total_item_count": state.total_item_count,
            "kp_name_being_quizzed": state.kp_name_being_quizzed,
            "last_generated_at": state.last_generated_at,
        }

    def _ensure_router(self) -> ModelRouter:
        if self._model_router is None:
            self._model_router = get_model_router()
        return self._model_router

    def _fallback_no_questions(self, engine_state: QuizEngineState) -> EngineStepResult:
        return EngineStepResult(
            reply_text=(
                "抱歉，我在准备测验题的时候遇到了一点小问题。"
                "我们要不要先换一种方式来确认你对这个知识点的理解？"
            ),
            engine_state_update=self._state_to_dict(engine_state),
            side_effects=EngineSideEffect(extra={"quiz_question_generation_failed": True}),
            transition=TransitionSuggestion(
                type=TransitionType.STAY, reason="quiz_question_gen_failed_stay"
            ),
            engine_debug_info={"fallback": True},
        )


def _q_to_dict(q) -> dict[str, Any]:
    if isinstance(q, dict):
        return q
    return {
        "id": q.id,
        "type": q.type,
        "text": q.text,
        "options": q.options,
        "correct_answer": q.correct_answer,
        "explanation": q.explanation,
    }


__all__ = ["QuizEngine", "QuizEngineState", "QuizQuestion"]

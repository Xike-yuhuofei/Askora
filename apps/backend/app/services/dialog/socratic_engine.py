"""
苏格拉底教学引擎核心
输入解析 → 策略选择 → 渐次提示生成 → 反思触发 → 输出验证

核心设计原则:
1. 从不直接给答案，通过提问引导思考
2. 5 级渐次提示协议（级别越高，提示越具体）
3. 级别变更带滞回约束，避免跳级
4. 基础输出验证（本地规则检查）
"""

from __future__ import annotations

import enum
import re
import time
from dataclasses import dataclass, field
from typing import Optional

from app.core.logging import get_logger
from app.models.dialog import DialogMessage, MessageRole
from app.services.llm.model_router import ChatMessage, ModelRouter, get_model_router

logger = get_logger(__name__)


class HintLevel(int, enum.Enum):
    """渐次提示级别（1-5 级）"""

    LEVEL_1 = 1  # 元认知提问 - "你怎么看？"
    LEVEL_2 = 2  # 概念澄清 - "这个概念的定义是什么？"
    LEVEL_3 = 3  # 思路引导 - "你可以从 X 角度思考"
    LEVEL_4 = 4  # 步骤提示 - "第一步是..."
    LEVEL_5 = 5  # 定向提示 - 指向错误位置，但不给正确操作


class TeachingStrategy(str, enum.Enum):
    """教学策略类型"""

    CLARIFICATION = "clarification"
    PROBLEM_DECOMPOSITION = "decomposition"
    ANALOGY = "analogy"
    COUNTEREXAMPLE = "counterexample"
    REFLECTION = "reflection"
    ERROR_ANALYSIS = "error_analysis"
    SOCRATIC_QUESTIONING = "socratic_questioning"


@dataclass
class LearnerState:
    """学习者状态（会话级）"""

    user_id: str
    pseudonym_id: str
    subject: str = "general"
    current_kp_id: Optional[str] = None
    mastery_estimate: float = 0.0
    current_hint_level: int = HintLevel.LEVEL_2.value
    current_strategy: str = TeachingStrategy.SOCRATIC_QUESTIONING.value
    hint_escalation_count: int = 0
    wrong_streak: int = 0
    engagement_level: float = 0.7
    recent_topics: list[str] = field(default_factory=list)


@dataclass
class EngineInput:
    """引擎输入"""

    session_id: str
    user_id: str
    user_input: str
    turn_number: int
    subject: str = "general"
    knowledge_point_id: Optional[str] = None
    hint_level: int = HintLevel.LEVEL_2.value


@dataclass
class EngineOutput:
    """引擎输出"""

    response: str
    strategy: str
    hint_level: int
    intent: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    ttft_ms: Optional[int] = None
    generation_ms: int = 0
    next_hint_level: int = HintLevel.LEVEL_2.value
    mastery_delta: float = 0.0


class SocraticEngine:
    """
    苏格拉底式教学引擎（简化版）
    移除了内容审核依赖，仅保留核心对话引导逻辑
    """

    SYSTEM_PROMPT_TEMPLATE = """你是一位专业的苏格拉底式教学导师。你的核心原则是：
1. **永远不直接给出答案**，而是通过提问引导学生自己思考
2. 根据学生的理解程度调整提示深度（共 5 级，1 级最抽象，5 级最具体）
3. 关注学生的思维过程，而不仅仅是结果
4. 鼓励学生反思和元认知

**当前学科**: {subject}
**当前知识点**: {kp_name}
**学生掌握度估计**: {mastery:.0%}
**当前提示级别**: {hint_level}/5

**提示级别说明**:
- 级别 1: 元认知提问 - 引导学生思考自己的思考过程
- 级别 2: 概念澄清 - 帮助学生厘清基本概念
- 级别 3: 思路引导 - 给出思考方向但不给出步骤
- 级别 4: 步骤提示 - 指出具体步骤但不给出计算
- 级别 5: 定向提示 - 指出错误位置，但不给出正确做法

请用中文回答，保持温和鼓励的语气。每次回复控制在 2-4 句话，最后以一个开放性问题结尾。"""

    def __init__(self):
        self.model_router: Optional[ModelRouter] = None

    def _get_model_router(self) -> ModelRouter:
        if self.model_router is None:
            self.model_router = get_model_router()
        return self.model_router

    async def generate_response(
        self,
        input_data: EngineInput,
        conversation_history: list[DialogMessage],
    ) -> EngineOutput:
        """生成苏格拉底式回复"""
        start_time = time.time()

        # 1. 输入解析
        intent = self._parse_intent(input_data.user_input)

        # 2. 策略选择
        strategy, hint_level = self._select_strategy(
            intent=intent,
            current_hint_level=input_data.hint_level,
            wrong_streak=0,
            mastery_estimate=0.5,
        )

        # 3. 构建 Prompt
        messages = self._build_prompt(
            user_input=input_data.user_input,
            conversation_history=conversation_history,
            subject=input_data.subject,
            hint_level=hint_level,
            strategy=strategy,
            kp_name=input_data.knowledge_point_id or "general",
            mastery=0.5,
        )

        # 4. 调用 LLM
        model_router = self._get_model_router()
        provider = model_router.route_for_subject(input_data.subject)
        llm_response = await provider.chat_completion(messages)

        generation_ms = int((time.time() - start_time) * 1000)

        # 5. 输出验证
        validated_response = self._validate_output(
            text=llm_response.content,
            hint_level=hint_level,
        )

        # 6. 计算下一级别
        next_hint_level = self._calculate_next_level(
            current_level=hint_level,
            intent=intent,
            response_quality=validated_response["quality_score"],
        )

        # 7. 掌握度更新估计
        mastery_delta = self._estimate_mastery_delta(
            intent=intent,
            hint_level=hint_level,
            response=validated_response["text"],
        )

        return EngineOutput(
            response=validated_response["text"],
            strategy=strategy,
            hint_level=hint_level,
            intent=intent,
            input_tokens=llm_response.input_tokens,
            output_tokens=llm_response.output_tokens,
            total_tokens=llm_response.total_tokens,
            generation_ms=generation_ms,
            next_hint_level=next_hint_level,
            mastery_delta=mastery_delta,
        )

    async def stream_response(
        self,
        input_data: EngineInput,
        conversation_history: list[DialogMessage],
    ):
        """流式生成苏格拉底式回复"""
        start_time = time.time()

        # 1. 输入解析
        intent = self._parse_intent(input_data.user_input)

        # 2. 策略选择
        strategy, hint_level = self._select_strategy(
            intent=intent,
            current_hint_level=input_data.hint_level,
            wrong_streak=0,
            mastery_estimate=0.5,
        )

        # 3. 构建 Prompt
        messages = self._build_prompt(
            user_input=input_data.user_input,
            conversation_history=conversation_history,
            subject=input_data.subject,
            hint_level=hint_level,
            strategy=strategy,
            kp_name=input_data.knowledge_point_id or "general",
            mastery=0.5,
        )

        # 4. 流式调用 LLM
        model_router = self._get_model_router()
        provider = model_router.route_for_subject(input_data.subject)

        ttft_ms = None
        first_chunk = True
        accumulated_text = ""

        async for chunk in provider.stream_chat_completion(messages):
            if first_chunk and chunk.content:
                ttft_ms = int((time.time() - start_time) * 1000)
                first_chunk = False

            accumulated_text += chunk.content

            yield {
                "type": "content",
                "content": chunk.content,
                "is_final": chunk.is_final,
            }

            if chunk.is_final:
                break

        # 最终输出
        yield {
            "type": "final",
            "response": accumulated_text,
            "strategy": strategy,
            "hint_level": hint_level,
            "intent": intent,
            "ttft_ms": ttft_ms,
            "generation_ms": int((time.time() - start_time) * 1000),
            "next_hint_level": self._calculate_next_level(hint_level, intent, 0.7),
        }

    def _parse_intent(self, user_input: str) -> str:
        """解析用户输入意图"""
        input_lower = user_input.lower()

        if any(
            kw in input_lower for kw in ["不懂", "不会", "不明白", "困惑", "难", "不知道", "不理解"]
        ):
            return "confusion"
        if any(kw in input_lower for kw in ["答案", "结果", "选什么", "等于", "是多少"]):
            return "answer_seeking"
        if any(kw in input_lower for kw in ["为什么", "怎么", "如何", "解释", "讲解"]):
            return "explanation_request"
        if any(
            kw in input_lower for kw in ["我觉得", "我认为", "应该是", "可能是", "选", "答案是"]
        ):
            return "student_answer"
        if any(kw in input_lower for kw in ["跳过", "下一题", "换一个", "不想做"]):
            return "disengagement"
        if any(kw in input_lower for kw in ["我错在哪里", "哪里错了", "为什么错了"]):
            return "reflection"

        return "general_inquiry"

    def _select_strategy(
        self, intent: str, current_hint_level: int, wrong_streak: int, mastery_estimate: float
    ) -> tuple[str, int]:
        """选择教学策略和提示级别"""
        strategy_map = {
            "confusion": TeachingStrategy.CLARIFICATION.value,
            "answer_seeking": TeachingStrategy.SOCRATIC_QUESTIONING.value,
            "explanation_request": TeachingStrategy.ANALOGY.value,
            "student_answer": TeachingStrategy.ERROR_ANALYSIS.value,
            "disengagement": TeachingStrategy.REFLECTION.value,
            "reflection": TeachingStrategy.REFLECTION.value,
            "general_inquiry": TeachingStrategy.SOCRATIC_QUESTIONING.value,
        }
        strategy = strategy_map.get(intent, TeachingStrategy.SOCRATIC_QUESTIONING.value)

        new_level = current_hint_level
        if wrong_streak >= 2:
            new_level = min(HintLevel.LEVEL_5.value, current_hint_level + 1)
        elif intent in {"explanation_request", "general_inquiry"}:
            new_level = max(HintLevel.LEVEL_1.value, current_hint_level - 1)
        elif intent == "student_answer":
            if mastery_estimate < 0.3:
                new_level = min(HintLevel.LEVEL_5.value, current_hint_level + 1)
            elif mastery_estimate > 0.7:
                new_level = max(HintLevel.LEVEL_1.value, current_hint_level - 1)

        level_diff = new_level - current_hint_level
        if abs(level_diff) > 1:
            new_level = current_hint_level + (1 if level_diff > 0 else -1)

        return strategy, new_level

    def _build_prompt(
        self,
        user_input: str,
        conversation_history: list[DialogMessage],
        subject: str,
        hint_level: int,
        strategy: str,
        kp_name: str,
        mastery: float,
    ) -> list[ChatMessage]:
        """构建对话 Prompt"""
        system_prompt = self.SYSTEM_PROMPT_TEMPLATE.format(
            subject=subject,
            kp_name=kp_name,
            mastery=mastery,
            hint_level=hint_level,
        )

        messages = [ChatMessage(role="system", content=system_prompt)]
        for msg in conversation_history[-20:]:
            if msg.role in {MessageRole.USER, MessageRole.ASSISTANT}:
                messages.append(ChatMessage(role=msg.role.value, content=msg.content))
        messages.append(ChatMessage(role="user", content=user_input))

        return messages

    def _validate_output(self, text: str, hint_level: int) -> dict:
        """输出验证（简化版，移除内容审核依赖）"""
        quality_score = 0.5

        if text.strip().endswith(("？", "?", "呢", "吗")):
            quality_score += 0.2

        if 50 < len(text) < 300:
            quality_score += 0.1

        answer_patterns = [r"答案是", r"正确答案", r"结果为", r"选[A-D]", r"等于[\d\.]+"]
        for pattern in answer_patterns:
            if re.search(pattern, text):
                quality_score -= 0.3
                break

        quality_score = max(0.0, min(1.0, quality_score))
        return {"text": text, "passed": quality_score >= 0.3, "quality_score": quality_score}

    def _calculate_next_level(
        self, current_level: int, intent: str, response_quality: float
    ) -> int:
        """计算下一轮提示级别"""
        delta = 0
        if intent == "student_answer":
            if response_quality > 0.7:
                delta = -1
            elif response_quality < 0.4:
                delta = 1

        delta = max(-1, min(1, delta))
        next_level = current_level + delta
        return max(HintLevel.LEVEL_1.value, min(HintLevel.LEVEL_5.value, next_level))

    def _estimate_mastery_delta(self, intent: str, hint_level: int, response: str) -> float:
        """估计掌握度变化"""
        delta = 0.01
        if intent == "student_answer":
            delta = 0.05 if hint_level <= 2 else 0.02
        if intent == "confusion":
            delta = -0.02
        return delta


# 全局单例
_socratic_engine: Optional[SocraticEngine] = None


def get_socratic_engine() -> SocraticEngine:
    """获取苏格拉底引擎单例"""
    global _socratic_engine
    if _socratic_engine is None:
        _socratic_engine = SocraticEngine()
    return _socratic_engine

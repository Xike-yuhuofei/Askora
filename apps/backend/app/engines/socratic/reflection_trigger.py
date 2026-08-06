"""
反思触发模块 (Reflection Trigger)
在关键时机引导学生进行元认知反思，促进深度学习

三种反思模式：
1. 事后反思 (Post-session Reflection): 会话结束时总结学习过程
2. 过程中反思 (In-process Reflection): 关键节点暂停，引导思考学习策略
3. 自我解释 (Self-explanation): 答对但需要深化时，要求解释解题思路
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from app.core.logging import get_logger
from app.engines.socratic.input_parser import ParsedInput

logger = get_logger(__name__)


class ReflectionType(str, Enum):
    """反思类型"""

    POST_SESSION = "post_session"  # 事后反思
    IN_PROCESS = "in_process"  # 过程中反思
    SELF_EXPLANATION = "self_explanation"  # 自我解释


@dataclass
class ReflectionDecision:
    """反思决策"""

    should_trigger: bool
    reflection_type: Optional[ReflectionType]
    reason: str
    prompt: str


@dataclass
class ReflectionSession:
    """会话级反思状态跟踪"""

    cooldown_turns: int = 0
    reflections_triggered: int = 0
    last_reflection_turn: int = 0
    stall_reason: Optional[str] = None


class ReflectionTrigger:
    """
    反思触发器

    在特定条件下触发元认知反思，帮助学生：
    - 监控自己的学习过程
    - 评估学习策略的有效性
    - 深化对概念的理解
    """

    # 触发阈值
    MAX_WRONG_BEFORE_REFLECTION = 3  # 连续错误 N 次后触发过程中反思
    MIN_SESSION_LENGTH = 5  # 会话至少多少轮后才考虑触发

    # 会话级反思控制
    COOLDOWN_TURNS = 10
    MAX_REFLECTIONS_PER_SESSION = 3
    POST_SESSION_MIN_TURNS = 8

    # 反思提示模板
    POST_SESSION_PROMPTS = [
        "我们今天的学习快要结束了。回顾一下，你觉得今天最重要的收获是什么？还有什么疑问没有解决吗？",
        "这节课进行得差不多了。你能总结一下我们讨论了哪些主要问题吗？",
        "在结束之前，我想请你想一想：通过这次学习，你的想法有什么改变吗？",
    ]

    IN_PROCESS_PROMPTS = [
        "我们暂停一下。回顾一下到目前为止的对话，你觉得问题出在哪里？是不是需要换个思路？",
        "让我们先停下来想想。之前的尝试没有成功，你觉得可能是什么原因？我们可以怎么调整？",
        "注意到了吗？我们似乎在同一个地方卡住了。你觉得现在最好的做法是什么？",
    ]

    SELF_EXPLANATION_PROMPTS = [
        "很好，你答对了！不过我很好奇，能请你说说你是怎么得出这个答案的吗？",
        "做得好！但我想更深入了解你的思路。你能用自己的话解释一下为什么是这个答案吗？",
        "答对了！这很棒。现在，能不能不用刚才的方法，试试用另一种方式来解释这个答案？",
    ]

    def __init__(self):
        self._consecutive_wrong: int = 0
        self._consecutive_correct: int = 0
        self._session_turns: int = 0
        self._reflection_triggered_this_session: bool = False
        self._reflection_session: ReflectionSession = ReflectionSession()

    def classify_stall_reason(
        self,
        parsed_input: ParsedInput,
        consecutive_wrong: int,
        progress_made: float,
    ) -> str:
        if consecutive_wrong >= self.MAX_WRONG_BEFORE_REFLECTION:
            return "repeated_errors"
        if progress_made < 0.1:
            return "no_progress"
        if parsed_input.emotional_state in ("frustrated", "anxious"):
            return "frustration"
        return "no_progress"

    def should_self_explain(
        self,
        previous_correct: bool,
        mastery: float,
        attempt_count: int,
    ) -> tuple[bool, str]:
        if not previous_correct:
            return False, "need_correct_answer"
        if mastery >= 0.8:
            return False, "mastery_already_high"
        if attempt_count > 5:
            return True, "deeper_explanation_needed_after_recent_attempts"
        if 0.3 < mastery < 0.6:
            return True, "solid_answer_but_mastery_incomplete"
        return False, "not_applicable"

    def generate_structured_reflection(
        self,
        mastery_map: dict,
        topics_covered: list,
    ) -> str:
        weak_topics = [t for t, m in mastery_map.items() if m < 0.5]
        strong_topics = [t for t, m in mastery_map.items() if m >= 0.7]
        parts = ["本次学习总结："]
        if strong_topics:
            parts.append(f"✅ 已掌握：{', '.join(strong_topics)}")
        if weak_topics:
            parts.append(f"⚠️ 需加强：{', '.join(weak_topics)}")
        parts.append(f"📚 涉及主题数：{len(topics_covered)}")
        return "\n".join(parts)

    def should_trigger(
        self,
        parsed_input: ParsedInput,
        mastery: float = 0.5,
        is_session_end: bool = False,
        previous_correct: Optional[bool] = None,
        context: Optional[dict] = None,
    ) -> ReflectionDecision:
        """
        判断是否应该触发反思

        Args:
            parsed_input: 解析后的学生输入
            mastery: 当前掌握度
            is_session_end: 是否是会话结束
            previous_correct: 上一次答题是否正确
            context: 额外上下文

        Returns:
            ReflectionDecision: 反思决策
        """
        context = context or {}
        progress_made: float = context.get("progress_made", 0.0)
        attempt_count: int = context.get("attempt_count", 0)

        self._session_turns += 1

        if self._reflection_session.cooldown_turns > 0:
            self._reflection_session.cooldown_turns -= 1

        if previous_correct is not None:
            if previous_correct:
                self._consecutive_correct += 1
                self._consecutive_wrong = 0
            else:
                self._consecutive_wrong += 1
                self._consecutive_correct = 0

        if is_session_end and self._session_turns >= self.POST_SESSION_MIN_TURNS:
            return self._create_reflection_decision(
                ReflectionType.POST_SESSION,
                "会话结束时的事后反思",
            )

        if (
            self._reflection_session.cooldown_turns == 0
            and self._reflection_session.reflections_triggered < self.MAX_REFLECTIONS_PER_SESSION
        ):
            stall_reason = self.classify_stall_reason(
                parsed_input,
                self._consecutive_wrong,
                progress_made,
            )
            self._reflection_session.stall_reason = stall_reason

            if self._consecutive_wrong >= self.MAX_WRONG_BEFORE_REFLECTION:
                return self._create_reflection_decision(
                    ReflectionType.IN_PROCESS,
                    f"连续 {self._consecutive_wrong} 次错误，触发过程中反思 (停滞原因: {stall_reason})",
                )

        if (
            self._reflection_session.cooldown_turns == 0
            and self._reflection_session.reflections_triggered < self.MAX_REFLECTIONS_PER_SESSION
        ):
            if previous_correct is not None and previous_correct:
                should_trigger_self, self_reason = self.should_self_explain(
                    previous_correct,
                    mastery,
                    attempt_count,
                )
                if should_trigger_self:
                    return self._create_reflection_decision(
                        ReflectionType.SELF_EXPLANATION,
                        f"触发自我解释: {self_reason}",
                    )

        return ReflectionDecision(
            should_trigger=False,
            reflection_type=None,
            reason="未达到触发条件",
            prompt="",
        )

    def _create_reflection_decision(
        self,
        reflection_type: ReflectionType,
        reason: str,
    ) -> ReflectionDecision:
        """创建反思决策"""
        prompt = self._generate_reflection_prompt(reflection_type)

        self._reflection_triggered_this_session = True
        self._reflection_session.cooldown_turns = self.COOLDOWN_TURNS
        self._reflection_session.reflections_triggered += 1
        self._reflection_session.last_reflection_turn = self._session_turns
        logger.info(f"Triggering {reflection_type.value}: {reason}")

        return ReflectionDecision(
            should_trigger=True,
            reflection_type=reflection_type,
            reason=reason,
            prompt=prompt,
        )

    def _generate_reflection_prompt(self, reflection_type: ReflectionType) -> str:
        """生成反思提示"""
        import random

        if reflection_type == ReflectionType.POST_SESSION:
            prompts = self.POST_SESSION_PROMPTS
        elif reflection_type == ReflectionType.IN_PROCESS:
            prompts = self.IN_PROCESS_PROMPTS
        elif reflection_type == ReflectionType.SELF_EXPLANATION:
            prompts = self.SELF_EXPLANATION_PROMPTS
        else:
            prompts = self.IN_PROCESS_PROMPTS

        return random.choice(prompts)

    def get_reflection_prompt(self, reflection_type: ReflectionType) -> str:
        """获取指定类型的反思提示"""
        return self._generate_reflection_prompt(reflection_type)

    def reset_session(self) -> None:
        """重置会话状态"""
        self._consecutive_wrong = 0
        self._consecutive_correct = 0
        self._session_turns = 0
        self._reflection_triggered_this_session = False
        self._reflection_session = ReflectionSession()

    def reset(self) -> None:
        """完全重置"""
        self.reset_session()

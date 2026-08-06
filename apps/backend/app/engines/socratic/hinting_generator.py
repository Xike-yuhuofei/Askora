"""
渐次提示生成器 (Graduated Hinting Generator)
实现五级提示协议，根据学生表现动态调整提示级别

提示级别说明：
Level 1: 元认知引导（最抽象，激发思考）
Level 2: 概念澄清（引导关注核心概念）
Level 3: 策略提示（提供思维方向）
Level 4: 结构提示（提供思考框架）
Level 5: 定向提示（最具体，接近答案但不直接给）
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.core.logging import get_logger
from app.engines.socratic.input_parser import ParsedInput

logger = get_logger(__name__)


@dataclass
class HintDecision:
    """提示决策结果"""

    level: int  # 1-5
    reason: str
    adjustment: str  # "maintain", "elevate", "de_escalate"
    message: str


class HintingGenerator:
    """
    渐次提示生成器

    根据学生的掌握度、表现历史和当前状态，
    动态决定最合适的提示级别
    """

    # 提示级别对应的提示描述
    HINT_DESCRIPTIONS = {
        1: "元认知引导：引导学生自己思考和监控学习过程",
        2: "概念澄清：帮助学生聚焦于核心概念和定义",
        3: "策略提示：提供解题或思考的方向和策略",
        4: "结构提示：提供详细的思考框架和步骤指引",
        5: "定向提示：提供非常具体的引导，接近答案但不直接给出",
    }

    # 升级和降级的阈值
    ELEVATION_THRESHOLD = 2  # 连续 N 次无进展后升级
    DE_ESCALATION_THRESHOLD = 2  # 连续 N 次正确后降级

    def __init__(self):
        self._current_level: int = 2
        self._consecutive_wrong: int = 0
        self._consecutive_correct: int = 0
        self._consecutive_no_response: int = 0
        self._help_request_count: int = 0
        self._frustration_count: int = 0
        self._history: list[HintDecision] = []

    def get_current_level(self) -> int:
        return self._current_level

    def classify_response(self, parsed_input: ParsedInput, previous_correct: Optional[bool]) -> str:
        if parsed_input.intent == "request_hint" or parsed_input.confusion_type == "not_understand":
            self._help_request_count += 1
            return "asking_for_help"
        if parsed_input.intent == "no_response" or parsed_input.intent_confidence == 0:
            self._consecutive_no_response += 1
            return "no_response"
        if previous_correct is True:
            return "correct"
        if previous_correct is False:
            return "wrong"
        if parsed_input.intent_confidence < 0.5:
            return "partial"
        return "wrong"

    def generate_hint_content(self, level: int, concept: str, student_state: str = "") -> str:
        contents = {
            1: f"关于「{concept}」，你可以先思考它的核心定义是什么？你之前学过哪些相关的知识？能否用自己的话描述一下？",
            2: f"让我们聚焦关键。「{concept}」的关键特征是什么？它和相关概念有什么区别？请尝试用一句话概括。",
            3: f"解决「{concept}」相关问题时，可以考虑以下方向：\n1) 已知条件有哪些？\n2) 目标是什么？\n3) 从已知到目标的路径可能有哪些？",
            4: f"关于「{concept}」，请按以下步骤思考：\n第一步：识别它的关键组成部分。\n第二步：分析各部分之间的关系。\n第三步：尝试建立联系。\n第四步：验证你的结论。",
            5: f"「{concept}」的一个关键要点是：它涉及[具体方面]。尝试从[具体角度]入手，关注[具体特征]。这将引导你接近答案。",
        }
        content = contents.get(level, contents[3])
        if student_state:
            content += f"\n\n（之前的情况：{student_state}）"
        return content

    def get_hint_progression(self) -> list[dict]:
        return [
            {
                "level": h.level,
                "reason": h.reason,
                "adjustment": h.adjustment,
                "message": h.message,
            }
            for h in self._history
        ]

    def decide(
        self,
        parsed_input: ParsedInput,
        mastery: float = 0.5,
        previous_correct: Optional[bool] = None,
        context: Optional[dict] = None,
        concept: str = "",
    ) -> HintDecision:
        context = context or {}

        if previous_correct is not None:
            if previous_correct:
                self._consecutive_correct += 1
                self._consecutive_wrong = 0
                self._consecutive_no_response = 0
            else:
                self._consecutive_wrong += 1
                self._consecutive_correct = 0

        response_type = self.classify_response(parsed_input, previous_correct)

        if parsed_input.emotional_state == "frustrated":
            self._frustration_count += 1

        base_level = self._calculate_base_level(mastery)
        adjustment = self._calculate_adjustment(parsed_input, mastery, previous_correct, context)

        new_level = base_level + adjustment

        if response_type == "asking_for_help" or parsed_input.confusion_type == "not_understand":
            new_level = max(new_level, 4)

        new_level = max(1, min(5, new_level))

        if new_level > self._current_level:
            change_type = "elevate"
            reason = f"提示级别升级: {self._current_level} -> {new_level}"
        elif new_level < self._current_level:
            change_type = "de_escalate"
            reason = f"提示级别降级: {self._current_level} -> {new_level}"
        else:
            change_type = "maintain"
            reason = f"提示级别保持: {new_level}"

        old_level = self._current_level
        self._current_level = new_level

        decision = HintDecision(
            level=new_level,
            reason=reason,
            adjustment=change_type,
            message=self.HINT_DESCRIPTIONS[new_level],
        )

        self._history.append(decision)
        if len(self._history) > 50:
            self._history.pop(0)

        logger.info(
            f"Hint level: {old_level} -> {new_level} ({change_type}), mastery={mastery:.2f}, response={response_type}"
        )

        return decision

    def compute_hint_text(self, decision: HintDecision, concept: str) -> str:
        return self.generate_hint_content(decision.level, concept)

    def _calculate_base_level(self, mastery: float) -> int:
        """基于掌握度计算基础提示级别"""
        if mastery < 0.2:
            return 4  # 极低掌握度：较具体的提示
        elif mastery < 0.4:
            return 3  # 低掌握度：策略提示
        elif mastery < 0.6:
            return 2  # 中等掌握度：概念澄清
        elif mastery < 0.8:
            return 2  # 中高掌握度：保持概念澄清
        else:
            return 1  # 高掌握度：元认知引导

    def _calculate_adjustment(
        self,
        parsed_input: ParsedInput,
        mastery: float,
        previous_correct: Optional[bool],
        context: dict,
    ) -> int:
        adjustment = 0

        if self._consecutive_wrong >= 3:
            adjustment += 2
        elif self._consecutive_wrong >= 2:
            adjustment += 1

        if self._consecutive_correct >= 2:
            adjustment -= 1
            if mastery > 0.7:
                adjustment -= 1

        if parsed_input.intent == "request_hint":
            adjustment += 2

        if parsed_input.intent == "express_confidence" and mastery > 0.5:
            adjustment -= 1

        if parsed_input.emotional_state == "frustrated":
            adjustment += 1

        if parsed_input.confusion_type == "not_understand":
            adjustment += 2

        if parsed_input.confusion_type == "calculation_error":
            adjustment += 1

        if len(self._history) == 0:
            suggested = parsed_input.suggested_hint_level
            if suggested > 0:
                adjustment = suggested - 2

        return adjustment

    def reset(self) -> None:
        self._current_level = 2
        self._consecutive_wrong = 0
        self._consecutive_correct = 0
        self._consecutive_no_response = 0
        self._help_request_count = 0
        self._frustration_count = 0
        self._history.clear()

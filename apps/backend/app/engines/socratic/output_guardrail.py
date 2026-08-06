"""
输出验证模块 (Output Guardrail)
确保 LLM 生成的回复符合苏格拉底教学法要求，防止答案泄露

三层验证机制：
1. 规则引擎：检查是否包含直接答案或禁止模式
2. Schema 验证：检查回复格式是否符合要求（必须是问句）
3. LLM 分类器：（MVP 阶段用规则模拟，后续接入 LLM 二次验证）

降级策略：连续 3 次验证失败后返回安全模板
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """验证结果"""

    is_valid: bool
    reason: str
    violation_type: str  # "none", "answer_leak", "format_violation", "safety_violation"
    retry_suggestion: Optional[str] = None


class OutputGuardrail:
    """
    输出验证护栏

    确保所有 AI 输出都经过教学法过滤
    """

    # 答案泄露检测模式
    ANSWER_LEAK_PATTERNS = [
        # 直接给出答案
        r"(?:答案|结果|解|答)[是为：:]\s*\S+",
        r"(?:the\s+(?:answer|result|solution)\s+is)\s+\S+",
        # 直接给出解法
        r"(?:解法|做法|方法)[是为：:]\s*\S+",
        r"(?:the\s+(?:solution|method)\s+is)\s+\S+",
        # 给出具体数值
        r"(?:等于|等于是|值为|结果是)\s*\d+",
        r"(?:equals?|is\s+equal\s+to)\s*\d+",
        # 过度解释
        r"(?:让我(?:来)?(?:详细)?(?:解释|说明|讲解))",
        r"(?:let me(?:\s+explain|\s+show|\s+tell))",
        r"(?:简单来说|其实就是|换句话说)",
        # 禁止的直接指导
        r"(?:你应该|你需要|你必须|你要)\s*\S+",
        r"(?:you\s+(?:should|need\s+to|must|have\s+to))\s+\S+",
        # 具体步骤指令
        r"(?:第一步|第二步|第三步|首先|然后|接着)\s*(?:你|你需要|你应该)?",
    ]

    # 格式验证：必须是问句或引导性语句
    QUESTION_PATTERNS = [
        r"[？?]$",
        r"^(?:你|您|我们|能|可以|是否|有没有|什么|怎么|为什么|如果)",
        r"(?:能|可以|是否|有没有|什么|怎么|为什么)\s+(?:想想|考虑|思考|回忆|注意|发现)",
    ]

    # 安全风险模式
    SAFETY_PATTERNS = [
        r"(?:放弃|算了|没用|学不会|太难了)",  # 避免强化负面情绪
        r"(?:考试|测试|评分)",  # 避免增加考试焦虑
    ]

    # 最大重试次数
    MAX_VALIDATION_RETRIES = 3

    def __init__(self):
        self._validation_count: int = 0
        self._fail_count: int = 0

    def validate(self, text: str) -> ValidationResult:
        """
        验证回复是否符合要求

        Args:
            text: LLM 生成的回复

        Returns:
            ValidationResult: 验证结果
        """
        if not text or not text.strip():
            return ValidationResult(
                is_valid=False,
                reason="回复为空",
                violation_type="format_violation",
                retry_suggestion="请生成一个引导性的问题",
            )

        text = text.strip()

        # 1. 规则引擎检查：答案泄露
        leak_check = self._check_answer_leak(text)
        if not leak_check.is_valid:
            self._fail_count += 1
            logger.warning("output_guardrail_rejected", violation_type=leak_check.violation_type)
            return leak_check

        # 2. 格式检查：是否为问句
        format_check = self._check_format(text)
        if not format_check.is_valid:
            self._fail_count += 1
            logger.warning("output_guardrail_rejected", violation_type=format_check.violation_type)
            return format_check

        # 3. 安全检查
        safety_check = self._check_safety(text)
        if not safety_check.is_valid:
            self._fail_count += 1
            logger.warning("output_guardrail_rejected", violation_type=safety_check.violation_type)
            return safety_check

        # 全部通过
        self._fail_count = 0
        return ValidationResult(
            is_valid=True,
            reason="验证通过",
            violation_type="none",
        )

    def _check_answer_leak(self, text: str) -> ValidationResult:
        """检查是否泄露答案"""
        for pattern in self.ANSWER_LEAK_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return ValidationResult(
                    is_valid=False,
                    reason=f"检测到答案泄露模式: '{match.group()}'",
                    violation_type="answer_leak",
                    retry_suggestion="请用提问的方式引导学生思考，而不是直接给出答案或解法",
                )
        return ValidationResult(is_valid=True, reason="未检测到答案泄露", violation_type="none")

    def _check_format(self, text: str) -> ValidationResult:
        """检查回复格式"""
        is_question = False
        for pattern in self.QUESTION_PATTERNS:
            if re.search(pattern, text):
                is_question = True
                break

        if not is_question:
            return ValidationResult(
                is_valid=False,
                reason="回复不是引导性问题",
                violation_type="format_violation",
                retry_suggestion="回复必须是一个问题或以引导性语句开头",
            )

        # 检查长度（避免过长或过短）
        if len(text) < 5:
            return ValidationResult(
                is_valid=False,
                reason="回复过短",
                violation_type="format_violation",
                retry_suggestion="回复应该是一个完整的引导性问题",
            )

        if len(text) > 200:
            return ValidationResult(
                is_valid=False,
                reason="回复过长",
                violation_type="format_violation",
                retry_suggestion="回复应该简洁，避免冗长的解释",
            )

        return ValidationResult(is_valid=True, reason="格式正确", violation_type="none")

    def _check_safety(self, text: str) -> ValidationResult:
        """检查安全性"""
        for pattern in self.SAFETY_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return ValidationResult(
                    is_valid=False,
                    reason=f"检测到潜在安全风险: 匹配模式 '{pattern}'",
                    violation_type="safety_violation",
                    retry_suggestion="请保持积极引导的语气，避免负面情绪强化",
                )
        return ValidationResult(is_valid=True, reason="安全检查通过", violation_type="none")

    def should_use_fallback(self) -> bool:
        """判断是否应该使用降级模板"""
        return self._fail_count >= self.MAX_VALIDATION_RETRIES

    def reset(self) -> None:
        """重置验证状态"""
        self._fail_count = 0
        self._validation_count = 0

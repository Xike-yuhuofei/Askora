"""
响应生成模块 (Response Generator)
根据选定的策略和提示级别，构造 Prompt 并调用 LLM 生成苏格拉底式回复
"""

from __future__ import annotations

from typing import Optional

from app.core.logging import get_logger
from app.engines.socratic.input_parser import ParsedInput

logger = get_logger(__name__)


class ResponseGenerator:
    """
    响应生成器

    MVP 实现：
    - 构造苏格拉底式 Prompt
    - 调用 LLM (通过 model_router) 生成回复
    - 支持降级策略
    """

    # 安全降级模板（在 LLM 不可用或验证失败时使用）
    SAFE_TEMPLATES = [
        "让我们一起来思考这个问题。首先，你能告诉我你是怎么想的吗？",
        "这是一个好问题。在回答之前，我想先了解一下：你对这个问题已经有什么想法了吗？",
        "我们一步一步来。你觉得这个问题的关键是什么？",
        "很好，你提出了这个问题。为了更好地帮助你，能请你说说你卡在哪里了吗？",
    ]

    def __init__(self, llm_client=None):
        self._llm_client = llm_client

    def generate(
        self,
        strategy: dict,
        hint_level: int,
        parsed_input: ParsedInput,
        conversation_history: Optional[list[dict]] = None,
        mastery: float = 0.5,
        retry_count: int = 0,
    ) -> str:
        """
        生成苏格拉底式回复

        Args:
            strategy: 选中的策略模板
            hint_level: 提示级别 (1-5)
            parsed_input: 解析后的学生输入
            conversation_history: 对话历史
            mastery: 当前掌握度
            retry_count: 重试次数（用于降级判断）

        Returns:
            生成的回复文本
        """
        # 1. 构造 Prompt
        prompt = self._build_prompt(
            strategy, hint_level, parsed_input, conversation_history, mastery
        )

        # 2. 调用 LLM
        try:
            response = self._call_llm(prompt)
            if response:
                return response.strip()
        except Exception as e:
            logger.exception("socratic_llm_generation_failed", error_type=type(e).__name__)

        # 3. 降级处理
        return self._fallback_response(retry_count)

    def _build_prompt(
        self,
        strategy: dict,
        hint_level: int,
        parsed_input: ParsedInput,
        conversation_history: Optional[list[dict]],
        mastery: float,
    ) -> str:
        """构造完整的 Prompt"""
        # 基础指令
        system_instruction = self._get_system_instruction()

        # 策略模板
        strategy_prompt = strategy.get("prompt_template", "")

        # 上下文信息
        context_info = self._build_context_block(
            parsed_input, hint_level, mastery, conversation_history
        )

        # 替换模板中的变量
        concept = (
            parsed_input.knowledge_points[0]["name"]
            if parsed_input.knowledge_points
            else "这个概念"
        )
        student_state = self._describe_student_state(parsed_input, mastery)

        strategy_prompt = strategy_prompt.replace("{concept}", concept)
        strategy_prompt = strategy_prompt.replace("{student_state}", student_state)
        strategy_prompt = strategy_prompt.replace("{hint_level}", str(hint_level))

        # 组合最终 Prompt
        full_prompt = f"""{system_instruction}

--- 当前策略 ---
{strategy_prompt}

--- 学生信息 ---
{context_info}

--- 学生最新输入 ---
"{parsed_input.text}"

--- 要求 ---
请根据以上策略和学生状态，生成一个苏格拉底式的回应。
严格遵守以下规则：
1. 只能用一个问题回应，不能给多个问题
2. 绝对不能直接给出答案或解释
3. 问题要自然、有引导性
4. 问题要与当前提示级别 (Level {hint_level}) 相匹配
5. 用中文回应"""

        return full_prompt

    def _get_system_instruction(self) -> str:
        """获取系统指令"""
        return """你是一位苏格拉底式的教师。你的教学方法是通过精心设计的问题来引导学生自己发现真理，而不是直接传授知识。

核心原则：
1. 永远不要直接给答案或解释
2. 通过提问引导学生思考
3. 承认学生的思考过程，肯定正确的推理
4. 对错误不直接纠正，而是引导学生自我发现
5. 保持耐心和鼓励的态度"""

    def _build_context_block(
        self,
        parsed_input: ParsedInput,
        hint_level: int,
        mastery: float,
        conversation_history: Optional[list[dict]],
    ) -> str:
        """构建上下文信息块"""
        lines = []

        # 学习目标
        goal_map = {
            "concept_clarification": "澄清概念",
            "method_guidance": "掌握方法",
            "error_correction": "纠正错误",
        }
        lines.append(f"- 学习目标: {goal_map.get(parsed_input.suggested_goal, '学习')}")

        # 意图
        lines.append(f"- 学生意图: {parsed_input.intent}")

        # 掌握度
        mastery_desc = (
            "极低"
            if mastery < 0.2
            else (
                "较低"
                if mastery < 0.4
                else "中等" if mastery < 0.6 else "较高" if mastery < 0.8 else "很高"
            )
        )
        lines.append(f"- 掌握度: {mastery:.2f} ({mastery_desc})")

        # 提示级别
        lines.append(f"- 提示级别: Level {hint_level}")

        # 情感状态
        lines.append(f"- 情感状态: {parsed_input.emotional_state}")

        # 对话历史长度
        if conversation_history:
            lines.append(f"- 历史对话轮数: {len(conversation_history)}")

        return "\n".join(lines)

    def _describe_student_state(self, parsed_input: ParsedInput, mastery: float) -> str:
        """描述学生当前状态"""
        parts = []

        # 掌握度描述
        if mastery < 0.3:
            parts.append("对基础概念还不熟悉")
        elif mastery < 0.5:
            parts.append("有一定基础但理解不够深入")
        elif mastery < 0.7:
            parts.append("基本理解但需要深化")
        else:
            parts.append("掌握较好可以进一步挑战")

        # 意图描述
        intent_desc = {
            "confusion_expression": "表达了困惑",
            "request_explanation": "请求详细解释",
            "request_hint": "请求提示",
            "ask_question": "提出了一个问题",
            "express_confidence": "表现出自信",
            "frustration": "感到挫败",
            "general_input": "提供了输入",
        }
        parts.append(intent_desc.get(parsed_input.intent, "进行了学习活动"))

        return "，".join(parts)

    def _call_llm(self, prompt: str) -> Optional[str]:
        """调用 LLM"""
        if self._llm_client:
            return self._llm_client.generate(prompt)

        # Mock 实现：基于简单规则生成回复
        return self._mock_response(prompt)

    def _mock_response(self, prompt: str) -> str:
        """Mock 响应生成（用于开发测试）"""
        # 从 Prompt 中提取关键信息
        import re

        hint_level_match = re.search(r"Level (\d)", prompt)
        level = int(hint_level_match.group(1)) if hint_level_match else 2

        # 根据提示级别生成不同的引导性问题
        mock_responses = {
            1: [
                "你觉得这个问题的核心是什么？",
                "如果从不同的角度来看，你会有什么想法？",
                "能描述一下你现在的思路吗？",
            ],
            2: [
                "你能回忆一下相关的概念是什么吗？",
                "这个问题涉及到哪些基本原理？",
                "之前学过的什么知识可能可以用上？",
            ],
            3: [
                "你觉得第一步应该做什么？",
                "能不能先列出你知道的条件？",
                "试着从最简单的情况开始想想看？",
            ],
            4: [
                "首先，把题目中给出的条件一一列出来。",
                "然后，回忆一下相关的公式或规则。",
                "试着按照以下步骤思考：先确定已知条件，再找未知量。",
            ],
            5: [
                "仔细看一下题目中的数字和单位。注意单位是否一致。",
                "先算出方程两边同时加上相同的数，等式仍然成立。试试在方程两边同时加上 5。",
                "看清楚题目要求的是什么。题目要求的是 x 的值，而不是 x+3 的值。",
            ],
        }

        import random

        responses = mock_responses.get(level, mock_responses[2])
        return random.choice(responses)

    def _fallback_response(self, retry_count: int) -> str:
        """降级响应"""
        # 根据重试次数选择不同的降级模板
        index = min(retry_count, len(self.SAFE_TEMPLATES) - 1)
        logger.warning(f"Using fallback response (attempt {retry_count + 1})")
        return self.SAFE_TEMPLATES[index]

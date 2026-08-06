"""
输入解析模块 (Input Parser)
负责理解学生输入的深层含义，包括：
- 意图识别 (intent detection)
- 知识点定位 (knowledge point localization)
- 困惑识别 (confusion detection)
- 情感状态推断 (emotion inference)
- 认知水平推断 (cognitive level inference)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ParsedInput:
    """解析后的学生输入"""

    text: str
    intent: str = (
        "unknown"  # confusion_expression, request_explanation, request_hint, ask_question, express_confidence, frustration, etc.
    )
    intent_confidence: float = 0.0

    knowledge_points: list[dict] = field(
        default_factory=list
    )  # [{"id": "...", "name": "...", "confidence": 0.9}]
    confusion_type: str = (
        "none"  # none, conceptual_misunderstanding, method_error, calculation_error
    )
    confusion_detail: str = ""

    emotional_state: str = "neutral"  # neutral, frustrated, curious, confident, anxious
    cognitive_level: str = (
        "comprehension"  # knowledge, comprehension, application, analysis, evaluation, creation
    )

    suggested_goal: str = (
        "concept_clarification"  # concept_clarification, method_guidance, error_correction
    )
    suggested_hint_level: int = 2  # 初始建议提示级别
    urgency: str = "normal"  # normal, high, critical


class InputParser:
    """
    输入解析器

    MVP 实现：规则匹配 + 可选的 LLM 辅助
    后续版本将集成 LLM 分类器和知识图谱实体链接
    """

    # 意图关键词映射
    INTENT_PATTERNS = {
        "confusion_expression": [
            r"不太理解",
            r"不明白",
            r"搞不懂",
            r"懵了",
            r"糊涂",
            r"什么意思",
            r"为什么",
            r"怎么回事",
            r"不懂",
            r"不清楚",
        ],
        "request_explanation": [
            r"给我讲讲",
            r"解释一下",
            r"告诉我",
            r"介绍一下",
            r"什么是",
            r"讲解",
            r"详细说",
            r"展开说说",
        ],
        "request_hint": [
            r"提示",
            r"给点提示",
            r"怎么办",
            r"接下来怎么做",
            r"帮我想想",
            r"下一步",
            r"卡住了",
            r"没思路",
        ],
        "ask_question": [
            r"吗\?$",
            r"呢\?$",
            r"？$",
            r"\?$",
            r"会不会",
            r"能不能",
            r"是不是",
            r"对不对",
        ],
        "express_confidence": [
            r"我懂了",
            r"我明白了",
            r"原来如此",
            r"知道了",
            r"会了",
            r"简单",
            r"没问题",
            r"这还不简单",
        ],
        "frustration": [
            r"太难了",
            r"不会做",
            r"做不出来",
            r"放弃",
            r"学不下去",
            r"烦死了",
            r"讨厌",
            r"没用",
            r"怎么这么难",
        ],
    }

    # 困惑类型关键词
    CONFUSION_PATTERNS = {
        "conceptual_misunderstanding": [
            r"概念",
            r"定义",
            r"是什么",
            r"什么意思",
            r"不理解.*概念",
        ],
        "method_error": [
            r"方法",
            r"步骤",
            r"怎么做",
            r"流程",
            r"操作",
        ],
        "calculation_error": [
            r"算错",
            r"算不对",
            r"结果不对",
            r"数字",
            r"计算",
        ],
    }

    # 情感词
    EMOTION_PATTERNS = {
        "frustrated": [r"太难", r"不会", r"做不出", r"放弃", r"烦死", r"讨厌"],
        "curious": [r"为什么", r"怎么", r"什么", r"好奇", r"有意思"],
        "confident": [r"懂了", r"明白", r"会了", r"简单", r"没问题"],
        "anxious": [r"考试", r"担心", r"怕", r"紧张", r"焦虑"],
    }

    def parse(self, text: str) -> ParsedInput:
        """
        解析学生输入

        Args:
            text: 学生输入的文本

        Returns:
            ParsedInput: 结构化的解析结果
        """
        text = text.strip()
        result = ParsedInput(text=text)

        # 1. 意图识别
        result.intent, result.intent_confidence = self._identify_intent(text)

        # 2. 知识点定位 (MVP: 基于关键字/ID 匹配)
        result.knowledge_points = self._locate_knowledge_points(text)

        # 3. 困惑识别
        result.confusion_type, result.confusion_detail = self._detect_confusion(text)

        # 4. 情感推断
        result.emotional_state = self._infer_emotion(text)

        # 5. 认知水平推断 (简化版)
        result.cognitive_level = self._infer_cognitive_level(text)

        # 6. 建议目标和提示级别
        result.suggested_goal = self._suggest_goal(result.intent, result.confusion_type)
        result.suggested_hint_level = self._suggest_hint_level(
            result.intent, result.confusion_type, result.emotional_state
        )

        return result

    def _identify_intent(self, text: str) -> tuple[str, float]:
        """识别用户意图"""
        scores: dict[str, int] = {}

        for intent, patterns in self.INTENT_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text):
                    score += 1
            scores[intent] = score

        if scores:
            best_intent = max(scores, key=lambda intent: scores[intent])
            if scores[best_intent] > 0:
                confidence = min(1.0, scores[best_intent] / 3.0)
                return best_intent, confidence

        return "general_input", 0.1

    def _locate_knowledge_points(self, text: str) -> list[dict]:
        """定位知识点 (MVP: 使用预置知识点匹配)"""
        # 预置知识点映射表
        KP_MAP = {
            "移项": {"id": "kp_algebra_transposition", "name": "移项法则"},
            "等式性质": {"id": "kp_algebra_equation_properties", "name": "等式性质"},
            "勾股定理": {"id": "kp_geometry_pythagorean", "name": "勾股定理"},
            "一元一次方程": {"id": "kp_algebra_linear_equation", "name": "一元一次方程"},
            "分数": {"id": "kp_math_fractions", "name": "分数运算"},
            "阅读理解": {"id": "kp_chinese_reading_comprehension", "name": "阅读理解"},
            "写作": {"id": "kp_chinese_writing", "name": "议论文写作"},
            "牛顿": {"id": "kp_physics_newton_laws", "name": "牛顿运动定律"},
            "光合作用": {"id": "kp_biology_photosynthesis", "name": "光合作用"},
        }

        found_kps = []
        for keyword, kp_info in KP_MAP.items():
            if keyword in text:
                kp_with_confidence = {**kp_info, "confidence": 0.9}
                found_kps.append(kp_with_confidence)

        return found_kps

    def _detect_confusion(self, text: str) -> tuple[str, str]:
        """识别困惑类型"""
        for confusion_type, patterns in self.CONFUSION_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    return confusion_type, text

        # 如果表达了困惑情绪
        if re.search(r"不太理解|不明白|搞不懂|为什么", text):
            return "conceptual_misunderstanding", text

        return "none", ""

    def _infer_emotion(self, text: str) -> str:
        """推断情感状态"""
        scores: dict[str, int] = {}

        for emotion, patterns in self.EMOTION_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text):
                    score += 1
            scores[emotion] = score

        if scores:
            best_emotion = max(scores, key=lambda emotion: scores[emotion])
            if scores[best_emotion] > 0:
                return best_emotion

        return "neutral"

    def _infer_cognitive_level(self, text: str) -> str:
        """推断认知水平 (基于 Bloom 分类法)"""
        # 简化规则
        if re.search(r"是什么|什么意思|定义", text):
            return "knowledge"
        elif re.search(r"理解|明白|为什么", text):
            return "comprehension"
        elif re.search(r"怎么做|怎么做|步骤", text):
            return "application"
        elif re.search(r"分析|对比|区别", text):
            return "analysis"
        elif re.search(r"评价|好坏|对错", text):
            return "evaluation"
        elif re.search(r"创造|设计|写", text):
            return "creation"
        else:
            return "comprehension"

    def _suggest_goal(self, intent: str, confusion_type: str) -> str:
        """建议学习目标"""
        if intent == "request_explanation" or confusion_type == "conceptual_misunderstanding":
            return "concept_clarification"
        elif intent == "request_hint" or confusion_type == "method_error":
            return "method_guidance"
        elif confusion_type == "calculation_error":
            return "error_correction"
        elif intent == "confusion_expression":
            return "concept_clarification"
        else:
            return "concept_clarification"

    def _suggest_hint_level(self, intent: str, confusion_type: str, emotion: str) -> int:
        """建议初始提示级别 (1-5)"""
        # 默认 Level 2
        level = 2

        # 如果表达了强困惑或沮丧，升级提示
        if intent in ("confusion_expression", "frustration"):
            level = 3
        if emotion == "frustrated":
            level = 3
        if confusion_type == "calculation_error":
            level = 4  # 计算错误需要更具体的提示

        # 如果是求解释，用较抽象的引导
        if intent == "request_explanation":
            level = 1

        return level

"""
策略选择器模块 (Strategy Selector)
根据当前上下文（解析结果、掌握度、历史）选择最优教学策略
"""

from __future__ import annotations

from typing import Optional

from app.core.logging import get_logger
from app.engines.socratic.input_parser import ParsedInput

logger = get_logger(__name__)


class StrategySelector:
    """
    策略选择器

    MVP 实现：基于规则的加权评分选择
    后续将引入强化学习优化层
    """

    def __init__(self, strategy_library):
        self.library = strategy_library
        self._last_strategy_id: Optional[str] = None
        self._strategy_history: list[str] = []  # 最近使用的策略ID

    def select(
        self,
        parsed_input: ParsedInput,
        mastery: float = 0.5,
        context: Optional[dict] = None,
    ) -> dict:
        """
        选择最佳策略

        Args:
            parsed_input: 解析后的学生输入
            mastery: 当前掌握度 (0-1)
            context: 额外上下文 (对话历史、情感状态等)

        Returns:
            选中的策略字典
        """
        context = context or {}

        # 1. 获取候选策略
        candidates = self._get_candidates(parsed_input)

        if not candidates:
            # Fallback: 返回默认策略
            fallback = self.library.get_strategy("strat_guide_self_reflection")
            if fallback:
                logger.warning("No matching strategy found, using fallback")
                return fallback
            raise ValueError("No strategies available in library")

        # 2. 计算每个候选的评分
        scored_candidates = []
        for strategy in candidates:
            score = self._calculate_score(strategy, parsed_input, mastery, context)
            scored_candidates.append((strategy, score))

        # 3. 选择得分最高的策略
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        best_strategy, best_score = scored_candidates[0]

        logger.info(f"Selected strategy: {best_strategy['id']} with score {best_score:.3f}")

        # 4. 更新历史
        self._last_strategy_id = best_strategy["id"]
        self._strategy_history.append(best_strategy["id"])
        if len(self._strategy_history) > 20:
            self._strategy_history.pop(0)

        return best_strategy

    def _get_candidates(self, parsed_input: ParsedInput) -> list[dict]:
        """获取候选策略集"""
        candidates = []

        # 根据输入的意图和目标，确定可能的策略分类
        level_1_goals = self._infer_level_1_goals(parsed_input)
        level_2_skills = self._infer_level_2_skills(parsed_input)

        # 尝试精确匹配
        for goal in level_1_goals:
            for skill in level_2_skills:
                exact_matches = self.library.find_strategies(
                    level_1_goal=goal,
                    level_2_skill=skill,
                )
                candidates.extend(exact_matches)

        # 如果没有精确匹配，放宽条件
        if not candidates:
            for goal in level_1_goals:
                broader_matches = self.library.find_strategies(level_1_goal=goal)
                candidates.extend(broader_matches)

        # 如果还是没有，返回所有策略
        if not candidates:
            candidates = self.library.get_all_active_strategies()

        return candidates

    def _infer_level_1_goals(self, parsed_input: ParsedInput) -> list[str]:
        """推断可能的一级目标"""
        goals = []

        # 基于意图
        intent_goal_map = {
            "confusion_expression": ["core_guidance", "monitoring"],
            "request_explanation": ["core_guidance", "planning"],
            "request_hint": ["planning", "core_guidance"],
            "ask_question": ["core_guidance"],
            "express_confidence": ["evaluation", "monitoring"],
            "frustration": ["core_guidance", "monitoring"],
            "general_input": ["core_guidance"],
        }

        goals.extend(intent_goal_map.get(parsed_input.intent, ["core_guidance"]))

        # 基于学习目标
        goal_map = {
            "concept_clarification": ["core_guidance", "monitoring"],
            "method_guidance": ["planning", "core_guidance"],
            "error_correction": ["monitoring", "evaluation"],
        }
        goals.extend(goal_map.get(parsed_input.suggested_goal, ["core_guidance"]))

        # 去重并保持顺序
        seen = set()
        unique_goals = []
        for g in goals:
            if g not in seen:
                seen.add(g)
                unique_goals.append(g)

        return unique_goals

    def _infer_level_2_skills(self, parsed_input: ParsedInput) -> list[str]:
        """推断可能的二级技能"""
        skills = []

        # 基于困惑类型
        confusion_skill_map = {
            "conceptual_misunderstanding": ["viewpoint_clarification", "self_reflection"],
            "method_error": ["strategy_selection", "process_check"],
            "calculation_error": ["process_check", "evidence_verification"],
        }
        skills.extend(
            confusion_skill_map.get(
                parsed_input.confusion_type, ["viewpoint_clarification", "self_reflection"]
            )
        )

        # 基于意图
        intent_skill_map = {
            "confusion_expression": ["viewpoint_clarification"],
            "request_explanation": ["viewpoint_clarification", "self_reflection"],
            "request_hint": ["strategy_selection"],
            "ask_question": ["viewpoint_clarification"],
            "express_confidence": ["evidence_verification"],
            "frustration": ["self_reflection", "viewpoint_clarification"],
        }
        skills.extend(intent_skill_map.get(parsed_input.intent, []))

        # 去重
        seen = set()
        unique_skills = []
        for s in skills:
            if s not in seen:
                seen.add(s)
                unique_skills.append(s)

        return unique_skills if unique_skills else ["self_reflection"]

    def _calculate_score(
        self,
        strategy: dict,
        parsed_input: ParsedInput,
        mastery: float,
        context: dict,
    ) -> float:
        """
        计算策略的综合得分

        评分因子：
        1. 类别匹配度 (0.4)
        2. 掌握度适配 (0.3)
        3. 历史多样性 (0.2)
        4. 情绪适配 (0.1)
        """
        score = 0.0

        # 1. 类别匹配度
        category_score = self._category_match_score(strategy, parsed_input)
        score += category_score * 0.4

        # 2. 掌握度适配
        mastery_score = self._mastery_fit_score(strategy, mastery, parsed_input)
        score += mastery_score * 0.3

        # 3. 历史多样性
        diversity_score = self._diversity_score(strategy)
        score += diversity_score * 0.2

        # 4. 情绪适配
        emotion_score = self._emotion_fit_score(strategy, parsed_input)
        score += emotion_score * 0.1

        return min(1.0, score)

    def _category_match_score(self, strategy: dict, parsed_input: ParsedInput) -> float:
        """类别匹配评分"""
        score = 0.0

        # 检查一级目标匹配
        goals = self._infer_level_1_goals(parsed_input)
        if strategy.get("level_1_goal") in goals:
            score += 0.5
        elif strategy.get("level_1_goal") == "core_guidance":
            score += 0.3  # core_guidance 是通用选项

        # 检查二级技能匹配
        skills = self._infer_level_2_skills(parsed_input)
        if strategy.get("level_2_skill") in skills:
            score += 0.5

        return score

    def _mastery_fit_score(
        self, strategy: dict, mastery: float, parsed_input: ParsedInput
    ) -> float:
        """掌握度适配评分"""
        score = 0.0
        level_1 = strategy.get("level_1_goal", "")

        if mastery < 0.3:
            # 低掌握度：需要更基础的引导
            if level_1 in ("core_guidance", "monitoring"):
                score = 0.8
            elif level_1 == "planning":
                score = 0.6
            else:
                score = 0.3
        elif mastery < 0.6:
            # 中等掌握度：多样化探索
            if level_1 in ("planning", "core_guidance"):
                score = 0.7
            elif level_1 == "monitoring":
                score = 0.6
            else:
                score = 0.4
        else:
            # 高掌握度：鼓励评估和反思
            if level_1 in ("evaluation", "core_guidance"):
                score = 0.9
            elif level_1 == "monitoring":
                score = 0.7
            else:
                score = 0.5

        # 如果用户表达了自信，优先选择评估类策略
        if parsed_input.intent == "express_confidence" and level_1 == "evaluation":
            score += 0.3

        return min(1.0, score)

    def _diversity_score(self, strategy: dict) -> float:
        """多样性评分 (避免重复使用相同策略)"""
        if not self._strategy_history:
            return 0.5

        strategy_id = strategy.get("id", "")

        # 最近使用的策略给予低评分
        if strategy_id in self._strategy_history[-3:]:
            return 0.1

        # 历史中使用过的策略给予中等评分
        if strategy_id in self._strategy_history:
            return 0.3

        # 未使用过的策略给予高评分
        return 0.8

    def _emotion_fit_score(self, strategy: dict, parsed_input: ParsedInput) -> float:
        """情绪适配评分"""
        score = 0.0
        emotion = parsed_input.emotional_state
        level_1 = strategy.get("level_1_goal", "")

        if emotion == "frustrated":
            # 学生沮丧，需要更多共情和引导
            if level_1 in ("core_guidance", "monitoring"):
                score = 0.9
            else:
                score = 0.4
        elif emotion == "confident":
            # 学生自信，可以挑战更高层次
            if level_1 == "evaluation":
                score = 0.9
            elif level_1 == "core_guidance":
                score = 0.6
            else:
                score = 0.4
        elif emotion == "curious":
            # 学生好奇，鼓励探索
            if level_1 in ("core_guidance", "planning"):
                score = 0.8
            else:
                score = 0.5
        else:
            # 中性情绪
            score = 0.6

        return score

    def reset_history(self) -> None:
        """重置策略历史"""
        self._last_strategy_id = None
        self._strategy_history.clear()

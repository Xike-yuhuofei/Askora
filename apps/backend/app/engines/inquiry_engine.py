"""
Inquiry (探究) 教学引擎

特点：
1. 基于问题的探究式学习
2. 引导学生提出假设、设计验证方案、得出结论
3. 支持开放式和半结构化探究任务
4. 培养学生的批判性思维和研究能力
"""

from __future__ import annotations

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


# 探究阶段
class InquiryPhase:
    THEME_SETTING = "theme_setting"  # 设置探究主题
    HYPOTHESIS = "hypothesis"  # 提出假设
    RESEARCH_DESIGN = "research_design"  # 设计验证方案
    EVIDENCE_GATHERING = "evidence_gathering"  # 收集证据
    ANALYSIS = "analysis"  # 分析讨论
    CONCLUSION = "conclusion"  # 得出结论
    REFLECTION = "reflection"  # 反思总结


@dataclass
class InquiryEngineState:
    """Inquiry 引擎的私有状态"""

    # 探究配置
    topic: str = ""
    phase: str = InquiryPhase.THEME_SETTING
    goal: str = ""

    # 探究进度
    hypothesis: str = ""
    research_plan: str = ""
    findings: list[str] = field(default_factory=list)
    conclusion: str = ""

    # 统计
    turn_count: int = 0
    completed_phases: list[str] = field(default_factory=list)

    # 会话历史
    dialogue_history: list[dict] = field(default_factory=list)


@register_engine
class InquiryEngine(TeachingEngine[InquiryEngineState]):
    """探究式学习引擎 (Inquiry Engine)"""

    engine_id: str = "inquiry"
    engine_name: str = "探究引擎"
    supported_cognitive_levels: list[CognitiveLevel] = [CognitiveLevel.GUIDE, CognitiveLevel.CREATE]
    supported_openness: list[TaskOpenness] = [TaskOpenness.OPEN, TaskOpenness.SEMI_STRUCTURED]

    def __init__(self):
        self._phase_prompts = self._build_phase_prompts()
        self._theme_library = self._build_theme_library()

    def _build_theme_library(self) -> dict:
        """构建探究主题库"""
        return {
            "math_patterns": {
                "id": "math_patterns",
                "subject": "math",
                "title": "数学规律探究",
                "description": "发现和验证数学中的有趣规律",
                "difficulty": 2,
                "theme_prompt": "观察下面这组等式：\n1 + 2 + 1 = 4 = 2²\n1 + 2 + 3 + 2 + 1 = 9 = 3²\n1 + 2 + 3 + 4 + 3 + 2 + 1 = 16 = 4²\n\n你发现了什么规律？能验证并证明你的发现吗？",
                "guiding_questions": [
                    "这些等式的结果有什么特点？",
                    "你能再写出下一个等式吗？",
                    "这个规律对所有正整数都成立吗？",
                    "如何证明你的猜想？",
                ],
                "extensions": [
                    "如果中间的数不是最大的，规律还成立吗？",
                    "如果把加法改成乘法，会有什么结果？",
                ],
                "expected_outcome": "学生发现对称数列求和等于中间数的平方，并能给出归纳证明",
            },
            "physics_ballistics": {
                "id": "physics_ballistics",
                "subject": "physics",
                "title": "抛体运动探究",
                "description": "探究抛体运动的规律和影响因素",
                "difficulty": 3,
                "theme_prompt": "如果你从地面以不同角度抛出一个球，什么角度能让球飞得最远？\n\n请探究：抛体的飞行距离与发射角度之间的关系。",
                "guiding_questions": [
                    "球的运动可以分解为哪两个方向？",
                    "飞行时间由什么决定？",
                    "水平距离如何计算？",
                    "理论上最优角度是多少？实际情况呢？",
                ],
                "extensions": [
                    "如果考虑空气阻力，最优角度会如何变化？",
                    "如果从高处抛出，最优角度会改变吗？",
                ],
                "expected_outcome": "学生理解斜抛运动的分解方法，推导最优角度为45度",
            },
            "biology_photosynthesis": {
                "id": "biology_photosynthesis",
                "subject": "biology",
                "title": "光合作用探究",
                "description": "探究影响光合作用速率的因素",
                "difficulty": 3,
                "theme_prompt": "植物通过光合作用制造食物。哪些因素会影响光合作用的快慢？\n\n请设计实验探究光照强度对光合作用速率的影响。",
                "guiding_questions": [
                    "光合作用的原料和产物是什么？",
                    "如何测量光合作用速率？",
                    "光照强度增加，光合速率会一直增加吗？",
                    "还有哪些因素会影响光合速率？",
                ],
                "extensions": [
                    "温度如何影响光合作用？",
                    "CO₂浓度增加会有什么影响？",
                ],
                "expected_outcome": "学生理解光合作用基本原理，设计对照实验，分析光饱和现象",
            },
            "chinese_argumentation": {
                "id": "chinese_argumentation",
                "subject": "chinese",
                "title": "议论文论证探究",
                "description": "探究如何构建有力的论证",
                "difficulty": 2,
                "theme_prompt": "有人认为'科技发展使人类更幸福'，也有人不同意。\n\n请探究：如何构建一个有力的论证来支持或反驳这个观点？",
                "guiding_questions": [
                    "什么是有力的论证？需要哪些要素？",
                    "你能想到哪些支持和反对的论据？",
                    "如何评估论据的可靠性？",
                    "如何回应反方观点？",
                ],
                "extensions": [
                    "这个问题的答案因时代而异吗？",
                    "不同文化背景下，'幸福'的定义是否不同？",
                ],
                "expected_outcome": "学生理解论证结构，能构建包含论点、论据、推理的完整论证",
            },
            "programming_algorithm": {
                "id": "programming_algorithm",
                "subject": "programming",
                "title": "算法效率探究",
                "description": "探究不同算法的效率差异",
                "difficulty": 3,
                "theme_prompt": "查找一个数组中的最大值，可以用不同方法实现。\n\n请探究：不同查找算法的时间复杂度和效率差异。",
                "guiding_questions": [
                    "什么是算法的时间复杂度？",
                    "线性查找和二分查找有什么区别？",
                    "二分查找需要什么前提条件？",
                    "如何选择合适的算法？",
                ],
                "extensions": [
                    "如果数据量非常大，应该选择哪种算法？",
                    "空间复杂度和时间复杂度如何权衡？",
                ],
                "expected_outcome": "学生理解时间复杂度概念，能分析不同算法的效率并做出合理选择",
            },
            "chemistry_reaction_rate": {
                "id": "chemistry_reaction_rate",
                "subject": "chemistry",
                "title": "化学反应速率探究",
                "description": "探究影响化学反应速率的因素",
                "difficulty": 3,
                "theme_prompt": "为什么有些化学反应很快发生，有些却很慢？\n\n请探究：影响化学反应速率的因素有哪些？",
                "guiding_questions": [
                    "化学反应速率如何定义和测量？",
                    "温度如何影响反应速率？",
                    "催化剂的作用是什么？",
                    "浓度和表面积有什么影响？",
                ],
                "extensions": [
                    "活化能的概念是什么？",
                    "如何通过实验验证你的假设？",
                ],
                "expected_outcome": "学生理解反应速率理论，能分析温度/浓度/催化剂的影响",
            },
        }

    def get_theme(self, theme_id: str) -> Optional[dict]:
        """获取指定主题"""
        return self._theme_library.get(theme_id)

    def find_themes_by_subject(self, subject: str) -> list[dict]:
        """按学科查找主题"""
        return [t for t in self._theme_library.values() if t["subject"] == subject]

    def list_available_themes(self) -> list[str]:
        """列出所有可用主题"""
        return list(self._theme_library.keys())

    def get_theme_prompt(self, theme_id: str) -> str:
        """获取主题的引导问题"""
        theme = self._theme_library.get(theme_id)
        if theme:
            return theme["theme_prompt"]
        return ""

    def _build_phase_prompts(self) -> dict:
        """构建各阶段的引导提示"""
        return {
            InquiryPhase.THEME_SETTING: {
                "prompt": "今天我们来做一个有趣的探究活动！\n\n我想让你思考一个问题：\n{topic_prompt}\n\n你觉得这个问题有趣吗？你想探究这个方向吗？",
                "follow_up": "好的！让我们开始吧。在开始之前，你觉得探究这个问题的关键是什么？你想通过探究得到什么？",
            },
            InquiryPhase.HYPOTHESIS: {
                "prompt": "很好！现在我们要进入探究的第一步：提出假设。\n\n基于你目前的了解，对于这个问题，你有什么初步的想法或假设吗？\n\n例如：\n- 你认为会是什么原因导致的？\n- 你觉得可能的解释有哪些？",
                "follow_up": "这个假设很有意思！你能再详细说说，为什么你会有这样的想法？有什么依据吗？",
            },
            InquiryPhase.RESEARCH_DESIGN: {
                "prompt": "现在我们有了一个好的假设。接下来，我们需要思考如何验证这个假设。\n\n你能设计一个方案来检验你的假设吗？可以考虑：\n- 你将用什么方法来验证？\n- 需要收集哪些数据或证据？\n- 你可能会遇到什么困难？",
                "follow_up": "这个方案设计得不错！你觉得这个方案有什么不足之处吗？有没有其他方法也可以验证你的假设？",
            },
            InquiryPhase.EVIDENCE_GATHERING: {
                "prompt": "现在是收集证据的阶段。根据你的研究方案，你需要做些什么？\n\n告诉我：\n- 你打算从哪里获取信息？\n- 你将如何记录和整理你发现的内容？\n- 你在收集过程中遇到了什么问题吗？",
                "follow_up": "你收集到的这些证据很有价值！根据目前的发现，你的假设还成立吗？需要修改吗？",
            },
            InquiryPhase.ANALYSIS: {
                "prompt": "收集完证据后，最重要的一步是分析和讨论。\n\n基于你收集到的证据：\n- 你的假设得到支持了吗？还是被推翻了？\n- 你发现了什么有趣的模式或关系？\n- 有没有出乎意料的结果？",
                "follow_up": "你的分析很有深度！你觉得从这些证据中，我们可以得出什么结论？你的分析过程中有什么关键的转折点吗？",
            },
            InquiryPhase.CONCLUSION: {
                "prompt": "现在是得出结论的时候了。\n\n根据你的整个探究过程，你能总结一下你的发现吗？\n\n请告诉我：\n- 你最终的结论是什么？\n- 这个结论的依据是什么？\n- 你的结论有什么局限或不足吗？",
                "follow_up": "恭喜你完成了这次探究！你的结论很有说服力。通过这次探究，你学到了什么新的方法或思维方式吗？",
            },
            InquiryPhase.REFLECTION: {
                "prompt": "最后，让我们来反思整个探究过程。\n\n你觉得：\n- 这次探究中最有趣的部分是什么？\n- 最大的挑战是什么？\n- 如果重新开始，你会做什么不同的选择？\n- 这次探究让你对这个主题有了什么新的认识？",
                "follow_up": "反思是学习中非常重要的一步。你在这次探究中表现出了很好的探究能力。希望这次经历能帮你在未来的学习中更有效地进行探究！",
            },
        }

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------
    async def on_enter(self, shared_ctx: SharedContext) -> None:
        """进入探究引擎时初始化"""
        logger.info("InquiryEngine initialized for exploration session")

    # ------------------------------------------------------------------
    # can_handle
    # ------------------------------------------------------------------
    async def can_handle(self, flow_stage: FlowStage, shared_ctx: SharedContext) -> float:
        # Inquiry 引擎专门用于 INQUIRE 阶段
        if flow_stage == FlowStage.INQUIRE:
            return 0.95

        # 在其他阶段也可使用，但评分较低
        stage_scores = {
            FlowStage.PRODUCE: 0.6,
            FlowStage.LEARN: 0.4,
            FlowStage.VALIDATE: 0.2,
            FlowStage.DRILL: 0.1,
            FlowStage.DIAGNOSE: 0.1,
        }
        return stage_scores.get(flow_stage, 0.2)

    # ------------------------------------------------------------------
    # build_initial_state
    # ------------------------------------------------------------------
    def build_initial_state(self, shared_ctx: SharedContext) -> InquiryEngineState:
        """初始化探究引擎状态"""
        # 从上下文获取主题
        topic = ""
        if shared_ctx.knowledge_point_id:
            # 简化：使用知识点 ID 作为主题
            kp_names = {
                "kp_algebra_transposition": "代数方程中的移项法则",
                "kp_geometry_pythagorean": "勾股定理的应用",
                "kp_math_fractions": "分数的运算",
                "kp_chinese_reading_comprehension": "阅读理解的方法",
                "kp_physics_newton_laws": "牛顿运动定律",
            }
            topic = kp_names.get(shared_ctx.knowledge_point_id, shared_ctx.knowledge_point_id)

        # 如果没有特定主题，使用通用探究主题
        if not topic:
            topic = "生活中的科学现象"

        return InquiryEngineState(
            topic=topic,
            phase=InquiryPhase.THEME_SETTING,
            goal="",
            hypothesis="",
            research_plan="",
            findings=[],
            conclusion="",
            turn_count=0,
            completed_phases=[],
        )

    # ------------------------------------------------------------------
    # step
    # ------------------------------------------------------------------
    async def step(
        self,
        learner_input: LearnerTurn,
        flow_stage: FlowStage,
        shared_ctx: SharedContext,
        engine_state: InquiryEngineState,
    ) -> EngineStepResult:
        t0 = time.time()

        user_text = learner_input.text.strip()
        # 处理当前阶段
        phase = engine_state.phase
        reply_text = ""
        new_phase = phase
        transition_to_next = False

        if phase == InquiryPhase.THEME_SETTING:
            reply_text, new_phase = self._handle_theme_setting(user_text, engine_state, shared_ctx)

        elif phase == InquiryPhase.HYPOTHESIS:
            reply_text, new_phase = self._handle_hypothesis(user_text, engine_state)

        elif phase == InquiryPhase.RESEARCH_DESIGN:
            reply_text, new_phase = self._handle_research_design(user_text, engine_state)

        elif phase == InquiryPhase.EVIDENCE_GATHERING:
            reply_text, new_phase = self._handle_evidence_gathering(user_text, engine_state)

        elif phase == InquiryPhase.ANALYSIS:
            reply_text, new_phase = self._handle_analysis(user_text, engine_state)

        elif phase == InquiryPhase.CONCLUSION:
            reply_text, new_phase = self._handle_conclusion(user_text, engine_state)

        elif phase == InquiryPhase.REFLECTION:
            reply_text, new_phase, transition_to_next = self._handle_reflection(
                user_text, engine_state
            )

        # 更新状态
        engine_state.phase = new_phase
        engine_state.turn_count += 1

        # 记录完成的阶段
        if new_phase not in engine_state.completed_phases and new_phase != phase:
            engine_state.completed_phases.append(phase)

        # 更新对话历史
        engine_state.dialogue_history.extend(
            [
                {"role": "user", "content": user_text, "turn": engine_state.turn_count},
                {"role": "assistant", "content": reply_text, "turn": engine_state.turn_count},
            ]
        )

        gen_ms = int((time.time() - t0) * 1000)

        # 决定过渡
        if transition_to_next:
            transition = TransitionSuggestion(
                type=TransitionType.SWITCH_AND_RETURN,
                target_engine_id="socratic",
                extra_context={
                    "inquiry_summary": {
                        "topic": engine_state.topic,
                        "phases_completed": len(engine_state.completed_phases),
                        "conclusion": engine_state.conclusion,
                    }
                },
                reason="inquiry_session_complete",
            )
        elif new_phase != phase:
            transition = TransitionSuggestion(
                type=TransitionType.STAY,
                reason=f"inquiry_phase_{new_phase}",
            )
        else:
            transition = TransitionSuggestion(
                type=TransitionType.STAY,
                reason="continue_inquiry",
            )

        return EngineStepResult(
            reply_text=reply_text,
            engine_state_update={
                "topic": engine_state.topic,
                "phase": engine_state.phase,
                "hypothesis": engine_state.hypothesis,
                "findings": engine_state.findings,
                "conclusion": engine_state.conclusion,
                "turn_count": engine_state.turn_count,
                "completed_phases": engine_state.completed_phases,
            },
            side_effects=EngineSideEffect(
                extra={
                    "inquiry_phase": new_phase,
                    "inquiry_topic": engine_state.topic,
                    "phases_completed": len(engine_state.completed_phases),
                },
            ),
            transition=transition,
            generation_ms=gen_ms,
            engine_debug_info={
                "current_phase": new_phase,
                "topic": engine_state.topic,
                "turn_count": engine_state.turn_count,
            },
        )

    # ==================================================================
    # Phase handlers
    # ==================================================================
    def _handle_theme_setting(
        self,
        user_text: str,
        state: InquiryEngineState,
        shared_ctx: SharedContext,
    ) -> tuple[str, str]:
        """处理主题设置阶段"""
        prompts = self._phase_prompts[InquiryPhase.THEME_SETTING]

        # 第一次交互：介绍主题
        if state.turn_count == 0:
            topic_prompt = f"我们要探究的主题是：{state.topic}"
            reply = prompts["prompt"].format(topic_prompt=topic_prompt)
            return reply, InquiryPhase.THEME_SETTING

        # 学生回应后：确认兴趣，进入假设阶段
        reply = prompts["follow_up"]
        return reply, InquiryPhase.HYPOTHESIS

    def _handle_hypothesis(
        self,
        user_text: str,
        state: InquiryEngineState,
    ) -> tuple[str, str]:
        """处理假设阶段"""
        prompts = self._phase_prompts[InquiryPhase.HYPOTHESIS]

        # 记录学生的假设
        if state.turn_count <= 1:
            reply = prompts["prompt"]
            return reply, InquiryPhase.HYPOTHESIS
        else:
            state.hypothesis = user_text[:500]  # 截断存储
            reply = prompts["follow_up"]
            return reply, InquiryPhase.RESEARCH_DESIGN

    def _handle_research_design(
        self,
        user_text: str,
        state: InquiryEngineState,
    ) -> tuple[str, str]:
        """处理研究设计阶段"""
        prompts = self._phase_prompts[InquiryPhase.RESEARCH_DESIGN]

        if state.turn_count <= 2:
            reply = prompts["prompt"]
            return reply, InquiryPhase.RESEARCH_DESIGN
        else:
            state.research_plan = user_text[:500]
            reply = prompts["follow_up"]
            return reply, InquiryPhase.EVIDENCE_GATHERING

    def _handle_evidence_gathering(
        self,
        user_text: str,
        state: InquiryEngineState,
    ) -> tuple[str, str]:
        """处理证据收集阶段"""
        prompts = self._phase_prompts[InquiryPhase.EVIDENCE_GATHERING]

        if state.turn_count <= 3:
            reply = prompts["prompt"]
            return reply, InquiryPhase.EVIDENCE_GATHERING
        else:
            # 记录发现
            state.findings.append(user_text[:200])
            reply = prompts["follow_up"]
            return reply, InquiryPhase.ANALYSIS

    def _handle_analysis(
        self,
        user_text: str,
        state: InquiryEngineState,
    ) -> tuple[str, str]:
        """处理分析阶段"""
        prompts = self._phase_prompts[InquiryPhase.ANALYSIS]

        if state.turn_count <= 4:
            reply = prompts["prompt"]
            return reply, InquiryPhase.ANALYSIS
        else:
            reply = prompts["follow_up"]
            return reply, InquiryPhase.CONCLUSION

    def _handle_conclusion(
        self,
        user_text: str,
        state: InquiryEngineState,
    ) -> tuple[str, str]:
        """处理结论阶段"""
        prompts = self._phase_prompts[InquiryPhase.CONCLUSION]

        if state.turn_count <= 5:
            reply = prompts["prompt"]
            return reply, InquiryPhase.CONCLUSION
        else:
            state.conclusion = user_text[:500]
            reply = prompts["follow_up"]
            return reply, InquiryPhase.REFLECTION

    def _handle_reflection(
        self,
        user_text: str,
        state: InquiryEngineState,
    ) -> tuple[str, str, bool]:
        """处理反思阶段"""
        prompts = self._phase_prompts[InquiryPhase.REFLECTION]

        if state.turn_count <= 6:
            reply = prompts["prompt"]
            return reply, InquiryPhase.REFLECTION, False
        else:
            reply = prompts["follow_up"]
            return reply, InquiryPhase.REFLECTION, True  # 完成，建议返回


__all__ = ["InquiryEngine", "InquiryEngineState", "InquiryPhase"]

"""
苏格拉底教学引擎的 TEI 适配器（MVP 重构版）

基于新实现的苏格拉底引擎子模块：
- InputParser (输入解析)
- StrategyLibrary + StrategySelector (策略选择)
- HintingGenerator (渐次提示)
- ResponseGenerator (响应生成)
- OutputGuardrail (输出验证)
- ReflectionTrigger (反思触发)

替换原有单块逻辑，实现可组合的模块化苏格拉底引擎。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

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
from app.engines.socratic.hinting_generator import HintDecision, HintingGenerator

# 导入苏格拉底子模块
from app.engines.socratic.input_parser import InputParser, ParsedInput
from app.engines.socratic.output_guardrail import OutputGuardrail
from app.engines.socratic.reflection_trigger import ReflectionTrigger
from app.engines.socratic.response_generator import ResponseGenerator
from app.engines.socratic.strategy_library import StrategyLibrary
from app.engines.socratic.strategy_selector import StrategySelector

# 导入知识追踪服务
from app.services.kt import get_kt_service

logger = get_logger(__name__)


@dataclass
class SocraticEngineState:
    """Socratic 引擎的私有状态"""

    # 核心子模块实例（需要在会话间保持状态）
    hinting_level: int = 2
    wrong_streak: int = 0
    right_streak: int = 0
    last_strategy_id: str = ""

    # 对话历史
    dialogue_history: list[dict] = field(default_factory=list)

    # 模块内部状态（序列化时仅保留必要信息）
    turn_count: int = 0
    last_parsed_intent: str = ""
    mastery_snapshot: float = 0.5


@register_engine
class SocraticTeachingEngine(TeachingEngine[SocraticEngineState]):
    """苏格拉底教学引擎的 TEI 适配器（MVP 重构版）"""

    engine_id: str = "socratic"
    engine_name: str = "苏格拉底引导引擎"
    supported_cognitive_levels: list[CognitiveLevel] = [CognitiveLevel.GUIDE]
    supported_openness: list[TaskOpenness] = [TaskOpenness.CLOSED, TaskOpenness.SEMI_STRUCTURED]

    def __init__(self):
        # 初始化苏格拉底子模块
        self.input_parser = InputParser()
        self.strategy_library = StrategyLibrary()
        self.strategy_selector = StrategySelector(self.strategy_library)
        self.hinting_generator = HintingGenerator()
        self.response_generator = ResponseGenerator()
        self.output_guardrail = OutputGuardrail()
        self.reflection_trigger = ReflectionTrigger()

        # 知识追踪服务
        self.kt_service = get_kt_service()

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------
    async def on_enter(self, shared_ctx: SharedContext) -> None:
        """进入引擎时重置子模块状态"""
        self.hinting_generator.reset()
        self.strategy_selector.reset_history()
        self.reflection_trigger.reset()
        self.output_guardrail.reset()
        logger.info("SocraticTeachingEngine initialized for new session")

    # ------------------------------------------------------------------
    # can_handle 适配评分
    # ------------------------------------------------------------------
    async def can_handle(self, flow_stage: FlowStage, shared_ctx: SharedContext) -> float:
        # Socratic 引擎天然适配 INQUIRE 和 LEARN 阶段
        stage_bonus: float = {
            FlowStage.LEARN: 0.8,
            FlowStage.INQUIRE: 1.0,  # 最适配
            FlowStage.VALIDATE: 0.6,
            FlowStage.DIAGNOSE: 0.3,
            FlowStage.DRILL: 0.4,
            FlowStage.PRODUCE: 0.1,
        }.get(flow_stage, 0.5)

        # 断层后继续苏格拉底追问是最优
        gap_then_socratic_bonus = (
            0.15 if (shared_ctx.identified_gaps and shared_ctx.explained_concept_ids) else 0.0
        )

        persona_weights = {
            "k12_primary": 1.20,
            "k12_high": 1.15,
            "higher_ed": 1.05,
            "professional": 0.95,
            "adult_general": 0.90,
            "senior": 0.80,
            "preschool": 0.30,
            "": 1.0,
        }
        persona_weight = persona_weights.get(shared_ctx.learner_persona, 1.0)
        score = min(1.0, stage_bonus * persona_weight + gap_then_socratic_bonus)
        return max(0.0, score)

    # ------------------------------------------------------------------
    # build_initial_state
    # ------------------------------------------------------------------
    def build_initial_state(self, shared_ctx: SharedContext) -> SocraticEngineState:
        """初始化引擎状态"""
        hint_level = shared_ctx.last_hint_level_used or 2
        try:
            hint_level = int(hint_level)
        except (TypeError, ValueError):
            hint_level = 2

        return SocraticEngineState(
            hinting_level=hint_level,
            wrong_streak=shared_ctx.recent_wrong_streak or 0,
            right_streak=0,
            last_strategy_id="",
            dialogue_history=[],
            turn_count=0,
            last_parsed_intent="",
            mastery_snapshot=0.5,
        )

    # ------------------------------------------------------------------
    # step: 核心苏格拉底流程
    # ------------------------------------------------------------------
    async def step(
        self,
        learner_input: LearnerTurn,
        flow_stage: FlowStage,
        shared_ctx: SharedContext,
        engine_state: SocraticEngineState,
    ) -> EngineStepResult:
        t0 = time.time()

        user_id = shared_ctx.extras.get("user_id", "tei_user")
        # 1. 输入解析
        parsed_input = self.input_parser.parse(learner_input.text)

        # 2. 获取当前掌握度
        kp_id = shared_ctx.knowledge_point_id
        mastery = 0.5
        if kp_id:
            mastery_est = self.kt_service.get_mastery(user_id, kp_id)
            mastery = mastery_est.p
            engine_state.mastery_snapshot = mastery

        # 3. 策略选择
        selected_strategy = self.strategy_selector.select(
            parsed_input=parsed_input,
            mastery=mastery,
            context={"wrong_streak": engine_state.wrong_streak},
        )
        engine_state.last_strategy_id = selected_strategy["id"]

        # 4. 渐次提示级别决策
        hint_decision = self.hinting_generator.decide(
            parsed_input=parsed_input,
            mastery=mastery,
            previous_correct=engine_state.last_parsed_intent
            not in ("confusion_expression", "request_hint", "frustration")
            and engine_state.wrong_streak == 0,
        )
        engine_state.hinting_level = hint_decision.level

        # 5. 反思触发检查
        reflection_decision = self.reflection_trigger.should_trigger(
            parsed_input=parsed_input,
            mastery=mastery,
            is_session_end=flow_stage == FlowStage.VALIDATE,  # 简化：进入验证阶段时视为学习结束
            previous_correct=engine_state.wrong_streak == 0 and engine_state.right_streak > 0,
        )

        # 如果需要触发反思，直接返回反思提示
        if reflection_decision.should_trigger:
            gen_ms = int((time.time() - t0) * 1000)
            engine_state.turn_count += 1

            # 更新对话历史
            engine_state.dialogue_history.append(
                {
                    "role": "user",
                    "content": learner_input.text,
                    "turn": engine_state.turn_count,
                }
            )
            engine_state.dialogue_history.append(
                {
                    "role": "assistant",
                    "content": reflection_decision.prompt,
                    "turn": engine_state.turn_count,
                }
            )

            return EngineStepResult(
                reply_text=reflection_decision.prompt,
                engine_state_update={
                    "hinting_level": engine_state.hinting_level,
                    "wrong_streak": engine_state.wrong_streak,
                    "right_streak": engine_state.right_streak,
                    "last_strategy_id": engine_state.last_strategy_id,
                    "turn_count": engine_state.turn_count,
                },
                side_effects=EngineSideEffect(
                    extra={
                        "reflection_triggered": True,
                        "reflection_type": (
                            reflection_decision.reflection_type.value
                            if reflection_decision.reflection_type
                            else ""
                        ),
                    },
                ),
                transition=TransitionSuggestion(
                    type=TransitionType.STAY,
                    reason="reflection_triggered",
                ),
                generation_ms=gen_ms,
            )

        # 6. 响应生成（包含重试和降级逻辑）
        max_retries = 3
        validated_response = ""

        for retry in range(max_retries):
            raw_response = self.response_generator.generate(
                strategy=selected_strategy,
                hint_level=hint_decision.level,
                parsed_input=parsed_input,
                conversation_history=engine_state.dialogue_history[-10:],  # 最近 10 轮
                mastery=mastery,
                retry_count=retry,
            )

            # 7. 输出验证
            validation_result = self.output_guardrail.validate(raw_response)

            if validation_result.is_valid:
                validated_response = raw_response
                break
            elif self.output_guardrail.should_use_fallback():
                # 连续多次验证失败，使用安全降级模板
                validated_response = self.response_generator._fallback_response(max_retries)
                break
            else:
                logger.warning(
                    f"Validation failed (attempt {retry + 1}/{max_retries}): "
                    f"{validation_result.reason}"
                )
        else:
            # 所有重试都失败
            validated_response = self.response_generator._fallback_response(max_retries - 1)

        # 8. 更新掌握度（简化版：根据意图和掌握度变化）
        mastery_delta = self._calculate_mastery_delta(parsed_input, mastery, hint_decision)
        if kp_id:
            is_correct = mastery_delta > 0
            self.kt_service.update_mastery(
                user_id=user_id,
                kp_id=kp_id,
                is_correct=is_correct,
                hint_level=hint_decision.level,
            )

        # 9. 更新错误/正确连击
        if mastery_delta >= 0:
            engine_state.right_streak += 1
            engine_state.wrong_streak = 0
        else:
            engine_state.wrong_streak += 1
            engine_state.right_streak = 0

        engine_state.last_parsed_intent = parsed_input.intent

        # 10. 更新对话历史
        engine_state.turn_count += 1
        engine_state.dialogue_history.append(
            {
                "role": "user",
                "content": learner_input.text,
                "turn": engine_state.turn_count,
            }
        )
        engine_state.dialogue_history.append(
            {
                "role": "assistant",
                "content": validated_response,
                "turn": engine_state.turn_count,
            }
        )

        # 11. 决定过渡建议
        transition = self._decide_transition(
            engine_state=engine_state,
            parsed_input=parsed_input,
            hint_decision=hint_decision,
            mastery_delta=mastery_delta,
            shared_ctx=shared_ctx,
        )

        gen_ms = int((time.time() - t0) * 1000)

        return EngineStepResult(
            reply_text=validated_response,
            engine_state_update={
                "hinting_level": engine_state.hinting_level,
                "wrong_streak": engine_state.wrong_streak,
                "right_streak": engine_state.right_streak,
                "last_strategy_id": engine_state.last_strategy_id,
                "turn_count": engine_state.turn_count,
            },
            side_effects=EngineSideEffect(
                mastery_updates={kp_id: mastery_delta} if kp_id else {},
                wrong_streak_delta=(
                    1
                    if mastery_delta < 0
                    else (-engine_state.wrong_streak if engine_state.wrong_streak > 0 else 0)
                ),
                hint_level_override=hint_decision.level,
                strategy_override=selected_strategy["name"],
                extra={
                    "socratic_intent": parsed_input.intent,
                    "parsed_kps": [kp["id"] for kp in parsed_input.knowledge_points],
                    "hint_level": hint_decision.level,
                    "hint_adjustment": hint_decision.adjustment,
                    "validation_passed": True,
                },
            ),
            transition=transition,
            generation_ms=gen_ms,
            engine_debug_info={
                "strategy_id": selected_strategy["id"],
                "strategy_name": selected_strategy["name"],
                "hint_level": hint_decision.level,
                "hint_reason": hint_decision.reason,
                "mastery_before": mastery,
                "mastery_delta": mastery_delta,
                "wrong_streak": engine_state.wrong_streak,
                "right_streak": engine_state.right_streak,
                "parsed_intent": parsed_input.intent,
                "parsed_emotion": parsed_input.emotional_state,
            },
        )

    # ==================================================================
    # Internal helpers
    # ==================================================================
    def _calculate_mastery_delta(
        self,
        parsed_input: ParsedInput,
        current_mastery: float,
        hint_decision: HintDecision,
    ) -> float:
        """计算掌握度变化（简化版）"""
        delta = 0.0

        # 如果表达了自信，说明掌握度提升
        if parsed_input.intent == "express_confidence":
            delta += 0.05

        # 如果表达了困惑，说明掌握度下降
        if parsed_input.intent in ("confusion_expression", "frustration"):
            delta -= 0.03

        # 如果请求了提示，说明还需要帮助
        if parsed_input.intent == "request_hint":
            delta -= 0.02

        # 提示级别升级说明学生遇到了困难
        if hint_decision.adjustment == "elevate":
            delta -= 0.02
        elif hint_decision.adjustment == "de_escalate":
            delta += 0.03

        return max(-0.1, min(0.1, delta))

    def _decide_transition(
        self,
        engine_state: SocraticEngineState,
        parsed_input: ParsedInput,
        hint_decision: HintDecision,
        mastery_delta: float,
        shared_ctx: SharedContext,
    ) -> TransitionSuggestion:
        """
        决定过渡建议

        规则：
        1. 连续错误 >= 3 且提示级别 >= 5 → SWITCH_AND_RETURN(Explain)
        2. 掌握度提升且提示级别降级 → SWITCH_AND_RETURN(Quiz) 做验证
        3. 默认：保持
        """
        # 规则 1：卡住模式 → 切 Explain
        if engine_state.wrong_streak >= 3 and hint_decision.level >= 5:
            kp_fragment = ""
            if shared_ctx.identified_gaps:
                kp_fragment = (
                    shared_ctx.identified_gaps[0].name
                    if hasattr(shared_ctx.identified_gaps[0], "name")
                    else ""
                )
            return TransitionSuggestion(
                type=TransitionType.SWITCH_AND_RETURN,
                target_engine_id="explain",
                extra_context={
                    "mode": "analogy_migration",
                    "gap_name": kp_fragment,
                },
                reason="socratic_stuck_or_needs_explanation",
            )

        # 规则 2：进展良好 → 切 Quiz 做微验证
        if hint_decision.level <= 2 and mastery_delta > 0.03 and engine_state.right_streak >= 2:
            return TransitionSuggestion(
                type=TransitionType.SWITCH_AND_RETURN,
                target_engine_id="quiz",
                extra_context={"item_count": 3, "validate_mode": True},
                reason="socratic_mastery_progress_do_micro_validation",
            )

        # 规则 3：概念断层未解释 → 切 Explain
        if shared_ctx.identified_gaps:
            explained_ids = shared_ctx.explained_concept_ids
            for gap in shared_ctx.identified_gaps:
                if hasattr(gap, "kp_id") and gap.kp_id not in explained_ids:
                    return TransitionSuggestion(
                        type=TransitionType.SWITCH_AND_RETURN,
                        target_engine_id="explain",
                        reason="concept_gap_needs_explanation",
                    )

        # 默认：保持
        return TransitionSuggestion(
            type=TransitionType.STAY,
            reset_hint_level=hint_decision.level,
            reason="socratic_stay_progressing_normally",
        )


__all__ = ["SocraticTeachingEngine", "SocraticEngineState"]

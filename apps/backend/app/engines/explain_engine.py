"""
Explain 讲解引擎（TEI 实现，第一批第二引擎）。

设计核心：具象→类比→原理→案例→应用场景，五段渐进式讲解。
对比苏格拉底式的「不直接给答案」，Explain 引擎的核心是「清晰高效地建立正确心智模型」。

典型被调度场景：
1. Socratic 卡住（wrong_streak>=3 + hint_level>=5）时，Socratic adapter 建议
   SWITCH_AND_RETURN(explain, mode="analogy_migration")
2. DIAGNOSE（诊断阶段）识别出知识断层后，直接用 Explain 引擎讲解断层概念
3. 用户主动选择「直接讲解」模式时

Explain engine (TEI implementation). 2nd engine onboard to enable orchestration demos.
Core flow: Concrete example → Analogy → Principle → Case → Real-world application
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
from app.services.llm.model_router import ChatMessage, ModelRouter, get_model_router

logger = get_logger(__name__)


EXPLAIN_MODES = {
    # 类比迁移：用一个生活中熟悉的例子作为类比桥梁
    "analogy_migration": {
        "name": "类比迁移讲解",
        "preferred_personas": {"k12_primary", "k12_high", "senior", ""},
        "template_hint": "优先使用生活场景或体育赛事 / 烹饪 / 交通等高度具象的类比",
    },
    # 原理优先：先定义再证明（适合数学物理的定义类概念）
    "principle_first": {
        "name": "原理优先讲解",
        "preferred_personas": {"higher_ed", "professional", "adult_general"},
        "template_hint": "先给出严谨定义 → 推导关键点 → 再给实例",
    },
    # 案例驱动：先讲真实案例再抽象（适合经济 / 管理 / 医学）
    "case_driven": {
        "name": "案例驱动讲解",
        "preferred_personas": {"professional", "higher_ed", "adult_general"},
        "template_hint": "先讲一个完整真实案例 → 抽取其中的概念 → 再泛化",
    },
    # 儿童启蒙：极简语言 + 故事化（适合学前 / 低年级）
    "story_for_kids": {
        "name": "故事化讲解",
        "preferred_personas": {"preschool", "k12_primary"},
        "template_hint": "使用拟人化角色和短故事，避免长句和术语，尽量口语化",
    },
}


@dataclass
class ExplainEngineState:
    current_mode: str = "analogy_migration"
    concept_being_explained: str = ""
    steps_delivered: list[str] = field(default_factory=list)
    last_explained_kp_ids: set[str] = field(default_factory=set)
    llm_calls_made: int = 0


@register_engine
class ExplainEngine(TeachingEngine[ExplainEngineState]):
    """讲解引擎：具象→类比→原理→案例，五段渐进式讲清一个概念"""

    engine_id: str = "explain"
    engine_name: str = "讲解引擎"
    supported_cognitive_levels: list[CognitiveLevel] = [CognitiveLevel.RECEIVE]
    supported_openness: list[TaskOpenness] = [TaskOpenness.CLOSED, TaskOpenness.SEMI_STRUCTURED]

    def __init__(self):
        self._model_router: Optional[ModelRouter] = None

    async def on_enter(self, shared_ctx: SharedContext) -> None:
        _ = self._ensure_router()

    # ------------------------------------------------------------------
    async def can_handle(self, flow_stage: FlowStage, shared_ctx: SharedContext) -> float:
        stage_score = {
            FlowStage.DIAGNOSE: 0.2,
            FlowStage.LEARN: 1.0,  # Explain 最适合在 LEARN 阶段
            FlowStage.INQUIRE: 0.3,
            FlowStage.VALIDATE: 0.1,
            FlowStage.DRILL: 0.1,
            FlowStage.PRODUCE: 0.1,
        }.get(flow_stage, 0.3)

        # 如果存在未解释的知识断层，Explain 适配度提升
        unexplained_gaps = [
            g for g in shared_ctx.identified_gaps if g.kp_id not in shared_ctx.explained_concept_ids
        ]
        gap_bonus = 0.15 if unexplained_gaps else 0.0

        score = stage_score + gap_bonus
        return max(0.0, min(1.0, score))

    # ------------------------------------------------------------------
    def build_initial_state(self, shared_ctx: SharedContext) -> ExplainEngineState:
        mode = _pick_explain_mode(
            requested=shared_ctx.extras.get("requested_explain_mode"),
            persona=shared_ctx.learner_persona,
            has_gaps=bool(shared_ctx.identified_gaps),
        )
        return ExplainEngineState(
            current_mode=mode,
            concept_being_explained=shared_ctx.knowledge_point_id or shared_ctx.subject or "",
            steps_delivered=[],
            last_explained_kp_ids=set(shared_ctx.explained_concept_ids),
            llm_calls_made=0,
        )

    # ------------------------------------------------------------------
    async def step(
        self,
        learner_input: LearnerTurn,
        flow_stage: FlowStage,
        shared_ctx: SharedContext,
        engine_state: ExplainEngineState,
    ) -> EngineStepResult:
        t0 = time.time()
        router = self._ensure_router()
        provider = router.route_for_subject(shared_ctx.subject or "general")

        mode_meta = EXPLAIN_MODES.get(engine_state.current_mode, EXPLAIN_MODES["analogy_migration"])
        target_kp_name = (
            (shared_ctx.identified_gaps[0].name if shared_ctx.identified_gaps else "")
            or shared_ctx.knowledge_point_id
            or engine_state.concept_being_explained
            or learner_input.text
        )

        messages = _build_explain_prompt(
            subject=shared_ctx.subject or "general",
            kp_name=target_kp_name,
            user_question=learner_input.text,
            mode=engine_state.current_mode,
            mode_hint=str(mode_meta["template_hint"]),
            already_explained_kp_ids=engine_state.last_explained_kp_ids,
            persona=shared_ctx.learner_persona,
            steps_done=engine_state.steps_delivered,
        )

        try:
            llm_resp = await provider.chat_completion(messages)
        except Exception as exc:  # noqa: BLE001
            logger.exception("explain_engine_llm_failed", error_type=type(exc).__name__)
            return _fallback_explain_result(engine_state, exc)

        reply = (llm_resp.content or "").strip()
        gen_ms = int((time.time() - t0) * 1000)
        engine_state.llm_calls_made += 1
        engine_state.steps_delivered.append("explain_main_call")

        # 副作用：把这个概念标记为「已解释」
        explained_ids: set[str] = set()
        if shared_ctx.knowledge_point_id:
            explained_ids.add(shared_ctx.knowledge_point_id)
        for g in shared_ctx.identified_gaps:
            explained_ids.add(g.kp_id)
        # 如果没有 kp_id，就用名字做一个 key（退化方案，保证 explained_concept_ids 有东西可追溯）
        if not explained_ids and target_kp_name:
            explained_ids.add("kp_name::" + target_kp_name)

        engine_state.last_explained_kp_ids.update(explained_ids)

        side_effects = EngineSideEffect(
            explained_ids=explained_ids,
            hint_level_override=2,  # 讲完回到引导式，从 Level 2 开始（给学习者一点思考空间）
            extra={
                "explain_mode": engine_state.current_mode,
                "explained_kp_name": target_kp_name,
            },
        )

        # 默认：Explain 讲完了，建议切回原先调用它的引擎（通常是 Socratic，因为 SWITCH_AND_RETURN）
        transition = TransitionSuggestion(
            type=(
                TransitionType.STAY
                if _user_still_asks_for_more_explain(learner_input.text)
                else TransitionType.STAY
            ),
            reason="explain_done_default_stay_orchestrator_decides_switch_back",
        )
        # 如果之前是 SWITCH_AND_RETURN（shared_ctx extras 里能看到），就给出建议返回上一引擎
        prev_engine = shared_ctx.extras.get("prev_engine_before_switch")
        if prev_engine and not _user_still_asks_for_more_explain(learner_input.text):
            transition = TransitionSuggestion(
                type=TransitionType.SWITCH_TO,
                target_engine_id=prev_engine,
                extra_context={"returned_from_explain_mode": engine_state.current_mode},
                reason="explain_done_returning_to_prev_engine_socratic_or_other",
            )

        return EngineStepResult(
            reply_text=reply or "抱歉，刚才我整理得不太好，我们从最基础的生活例子再来一次吧。",
            engine_state_update={
                "current_mode": engine_state.current_mode,
                "concept_being_explained": target_kp_name,
                "steps_delivered": list(engine_state.steps_delivered),
                "last_explained_kp_ids": list(engine_state.last_explained_kp_ids),
                "llm_calls_made": engine_state.llm_calls_made,
            },
            side_effects=side_effects,
            transition=transition,
            input_tokens=llm_resp.input_tokens,
            output_tokens=llm_resp.output_tokens,
            generation_ms=max(llm_resp.latency_ms, gen_ms),
            ttft_ms=getattr(llm_resp, "ttft_ms", None),  # type: ignore[arg-type]
            engine_debug_info={
                "explain_mode": engine_state.current_mode,
                "subject": shared_ctx.subject,
                "kp_name": target_kp_name,
                "explained_ids_count": len(explained_ids),
            },
        )

    # ==================================================================
    def _ensure_router(self) -> ModelRouter:
        if self._model_router is None:
            self._model_router = get_model_router()
        return self._model_router


# ======================================================================
# helpers
# ======================================================================


def _pick_explain_mode(
    requested: Optional[str],
    persona: str,
    has_gaps: bool,
) -> str:
    if requested and requested in EXPLAIN_MODES:
        return requested
    # 按 persona 挑最合适的
    for mode_id, meta in EXPLAIN_MODES.items():
        if persona in meta["preferred_personas"]:
            return mode_id
    return "analogy_migration"  # 默认：类比迁移，普适性最强


def _user_still_asks_for_more_explain(text: str) -> bool:
    """启发式：如果用户追问里含有「再讲一遍」「还是不懂」「另一个例子」，就停在 Explain 引擎多讲一轮"""
    if not text:
        return False
    t = text.lower()
    keywords = [
        "再讲",
        "再解",
        "还是不懂",
        "还是不明白",
        "没懂",
        "听不懂",
        "另一个例子",
        "别的例子",
        "举别的",
        "再举个",
        "再举例",
        "again",
        "once more",
        "another example",
        "more detail",
        "more details",
    ]
    return any(k in t for k in keywords)


def _fallback_explain_result(
    engine_state: ExplainEngineState,
    exc: Exception,
) -> EngineStepResult:
    reason = type(exc).__name__ if exc else "unknown"
    return EngineStepResult(
        reply_text=(
            "我正在整理关于这个概念的讲解内容，但这会儿思路有点卡壳。"
            "能麻烦你先告诉我：你之前在这个问题上最困惑的是哪一步吗？"
        ),
        engine_state_update={
            "current_mode": engine_state.current_mode,
            "concept_being_explained": engine_state.concept_being_explained,
            "steps_delivered": list(engine_state.steps_delivered),
            "last_explained_kp_ids": list(engine_state.last_explained_kp_ids),
            "llm_calls_made": engine_state.llm_calls_made,
        },
        side_effects=EngineSideEffect(extra={"explain_fallback_error": reason}),
        transition=TransitionSuggestion(
            type=TransitionType.STAY, reason="explain_error_please_retry"
        ),
        engine_debug_info={"fallback_reason": reason},
    )


def _build_explain_prompt(
    subject: str,
    kp_name: str,
    user_question: str,
    mode: str,
    mode_hint: str,
    already_explained_kp_ids: set[str],
    persona: str,
    steps_done: list[str],
) -> list[ChatMessage]:
    persona_hint_map = {
        "preschool": "请用学龄前儿童能听懂的语言，词汇尽量简单，多用拟人和小故事",
        "k12_primary": "面向小学低年级学生，语言简单，避免术语，可借用日常生活物品举例",
        "k12_high": "面向中学阶段学生，可以使用适度术语，但要从直观例子过渡到抽象",
        "higher_ed": "面向大学生，可以使用更严谨的定义和推导",
        "professional": "面向职场人士，尽量联系真实工作场景和应用价值",
        "adult_general": "面向成人学习者，强调实用价值和为什么要学",
        "senior": "面向银发学习者，字体心态年轻些，举生活/健康/家庭场景，节奏放慢",
        "": "通用语言，尽量避免不必要的术语",
    }
    persona_hint = persona_hint_map.get(persona, persona_hint_map[""])

    system_prompt = f"""你是一位耐心、结构化的讲解型导师。

**核心任务**：把「{kp_name or '当前主题'}」这个知识点讲清楚，让学习者建立正确的心智模型。

**学科**: {subject}
**讲解模式（遵循此框架）**: {EXPLAIN_MODES.get(mode, {}).get("name", mode)}
**模式要求**: {mode_hint}
**用户画像要求**: {persona_hint}
**已经讲过的概念标识**（不要重复讲这些，假设学习者有印象）: {len(already_explained_kp_ids)} 个
**之前已走过的讲解步骤**: {steps_done}

请按以下结构输出（除非学习者明确打断要求换模式）：
1. [开门见山] 用一句话说明「{kp_name or '这个概念'}」解决什么问题 / 为什么值得学
2. [具象类比] 用一个生活中高度熟悉的事物做类比（{mode_hint}）
3. [原理 / 定义] 给出准确的定义、公式或规则（适合当前画像）
4. [例子] 最少给 1 个具体可操作的例子
5. [收尾] 邀请学习者反馈：「你觉得这个类比贴切吗？要不要我们再试别的例子？」

要求：
- 中文输出
- 分段清晰，2-6 段，不要超长
- 如果用户问题里提到了具体的困惑点（例如「a 变负的时候我不明白」），先直接回应那个困惑点再走结构
"""

    user_prompt = (
        user_question.strip() if user_question else f"请你详细讲解一下「{kp_name or subject}」"
    )
    return [
        ChatMessage(role="system", content=system_prompt),
        ChatMessage(role="user", content=user_prompt),
    ]


__all__ = ["ExplainEngine", "ExplainEngineState", "EXPLAIN_MODES"]

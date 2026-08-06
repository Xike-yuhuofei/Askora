"""
LearningFlowOrchestrator —— 跨教学引擎编排器（Askora TEI v1 最核心调度层）

职责：
1. 持有 per-session 的 SharedContext + 各引擎私有状态快照（session_id 为 key）
2. 每轮学习交互调用「当前引擎」的 step()
3. 读取引擎返回的 TransitionSuggestion，执行切换策略（adopt / sanitize / override）
4. 应用引擎建议的副作用到 SharedContext，并记录 engine_trace 以便审计
5. 对外暴露一个简单的 run_turn() 接口：输入 (session_id, learner_turn) → 输出 (reply, debug)

本文件是 TEI 架构的「调度大脑」，所有引擎切换决策、SharedContext 写入权限
（写权限 Orchestrator 独有，引擎只能通过 EngineSideEffect 提出建议）都在这里完成。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional

from app.core.logging import get_logger
from app.engines._registry import ENGINE_REGISTRY
from app.engines.base import (
    EngineSideEffect,
    EngineStepResult,
    FlowStage,
    LearnerTurn,
    SharedContext,
    TeachingEngine,
    TransitionRecord,
    TransitionSuggestion,
    TransitionType,
)
from app.engines.repository import OrchestratorRepository, get_orchestrator_repository

logger = get_logger(__name__)


@dataclass
class OrchestratorTurnResult:
    """Orchestrator 对外的单轮返回结构（比 EngineStepResult 多了引擎切换元信息）"""

    reply_text: str
    engine_id: str
    flow_stage: FlowStage
    shared_ctx_snapshot: dict[str, Any]
    switched_to: Optional[str] = None  # 如果本轮切换了引擎，记录目标
    decision_trace: list[str] = field(default_factory=list)
    engine_debug: dict[str, Any] = field(default_factory=dict)


class LearningFlowOrchestrator:
    """
    教学引擎编排器。

    设计原则：
    - 无状态服务：所有会话数据存放在 self._sessions 里（当前简化为内存实现）
      → 未来替换为 Redis / DB 持久化（只需改 _load_session / _save_session 两处）
    - 写权限单点：只有 Orchestrator 能改 SharedContext（引擎只能提出 side_effects 建议）
    - 策略可插拔：切换策略默认「采纳引擎建议 + 健康性校验」，未来可替换为 LLM-Based 策略

    最简化实现（MVP）：
    - 支持 STAY / SWITCH_TO / SWITCH_AND_RETURN / END_FLOW 四种切换
    - 切换栈（SWITCH_AND_RETURN 的 return 语义）用一个简单栈存 shared_ctx.extras["return_stack"]
    - 没有 LLM 策略，只用规则校验引擎建议是否合法
    """

    def __init__(self) -> None:
        # session_id -> (shared_ctx, engine_states)
        # 内存缓存（热路径快速访问）+ Redis 持久化（容错/重启恢复）
        self._sessions: dict[str, tuple[SharedContext, dict[str, dict[str, Any]]]] = {}
        # engine_id -> 已实例化的引擎单例（因为引擎实例无状态，复用即可）
        self._engine_instances: dict[str, TeachingEngine] = {}
        # Redis 持久化仓库（通过 get_orchestrator_repository() 延迟初始化）
        self._repository: Optional[OrchestratorRepository] = None

    def _get_repository(self) -> OrchestratorRepository:
        if self._repository is None:
            self._repository = get_orchestrator_repository()
        return self._repository

    # ================================================================
    # public API
    # ================================================================
    async def create_session(
        self,
        session_id: str,
        *,
        subject: str = "general",
        knowledge_point_id: Optional[str] = None,
        initial_stage: FlowStage = FlowStage.LEARN,
        learner_persona: str = "",
        learner_preferences: Optional[dict[str, str]] = None,
        initial_engine_id: Optional[str] = None,
        extras: Optional[dict[str, Any]] = None,
    ) -> SharedContext:
        """
        创建一个新的会话（编排器视角的 session）。

        如果不指定 initial_engine_id，则会根据 flow_stage + persona 评分选出最优初始引擎。
        创建成功后，会话状态会同步写入 Redis 持久化仓库。
        """
        shared = SharedContext(
            subject=subject,
            knowledge_point_id=knowledge_point_id,
            current_flow_stage=initial_stage,
            learner_persona=learner_persona,
            learner_preferences=learner_preferences or {},
            extras={
                "session_id": session_id,
                "created_at": time.time(),
                **(extras or {}),
            },
        )
        engine_states: dict[str, dict[str, Any]] = {}

        if initial_engine_id is None:
            initial_engine_id = await self._pick_best_engine(shared)

        shared.current_engine_id = initial_engine_id
        shared.turn_count_in_current_engine = 0

        # 初始化「起始引擎」的私有状态，并且调用 on_enter
        engine = self._get_engine_instance(initial_engine_id)
        if engine is None:
            raise ValueError(
                f"初始引擎 {initial_engine_id} 未注册（已注册: {sorted(ENGINE_REGISTRY.keys())}）"
            )
        init_state_obj = engine.build_initial_state(shared)
        engine_states[initial_engine_id] = _engine_state_to_dict(init_state_obj)
        await engine.on_enter(shared)

        self._sessions[session_id] = (shared, engine_states)

        # 异步写入 Redis 持久化（不阻塞主流程，失败静默降级到内存）
        await self._persist_session_async(session_id, shared, engine_states)

        logger.info(
            "orchestrator_session_created",
            session_id=session_id,
            initial_engine=initial_engine_id,
            flow_stage=initial_stage.value,
            persona=learner_persona or "neutral",
        )
        return shared

    async def run_turn(
        self,
        session_id: str,
        learner_turn: LearnerTurn,
        *,
        forced_stage: Optional[FlowStage] = None,
        forced_engine: Optional[str] = None,
    ) -> OrchestratorTurnResult:
        """执行一轮学习交互。这是编排器对外的核心入口。"""
        shared, engine_states = await self._load_session(session_id)
        decisions: list[str] = []
        switched_to: Optional[str] = None

        # 可选：外部强制切换引擎（例如用户点了按钮 / 前端控制 / 后端 debug）
        if forced_engine and forced_engine != shared.current_engine_id:
            decisions.append(f"forced_switch:{forced_engine}")
            shared, engine_states = await self._do_switch(
                session_id=session_id,
                shared=shared,
                engine_states=engine_states,
                from_engine=shared.current_engine_id,
                to_engine=forced_engine,
                decided_by="manual_override",
                reason="forced_engine_override",
                return_semantics=False,
            )
            switched_to = forced_engine
            shared.turn_count_in_current_engine = 0

        if forced_stage is not None:
            if forced_stage != shared.current_flow_stage:
                decisions.append(f"forced_stage:{forced_stage.value}")
            shared.current_flow_stage = forced_stage

        # 1. 取当前引擎实例
        current_engine_id = shared.current_engine_id or "socratic"
        engine = self._get_engine_instance(current_engine_id)
        if engine is None:
            # 防御：未知引擎 → 回到 socratic
            decisions.append(f"unknown_engine_fallback_to_socratic:{current_engine_id}")
            current_engine_id = "socratic"
            engine = self._get_engine_instance(current_engine_id)
            if engine is None:
                raise RuntimeError("socratic engine must be registered")
            shared.current_engine_id = current_engine_id

        # 2. 恢复引擎私有状态
        engine_state_obj = _dict_to_engine_state(
            cls=type(engine.build_initial_state(shared)),
            data=engine_states.get(current_engine_id, {}),
            fallback=engine.build_initial_state(shared),
        )

        # 3. 调用引擎 step()
        step_result: EngineStepResult = await engine.step(
            learner_input=learner_turn,
            flow_stage=shared.current_flow_stage,
            shared_ctx=shared,
            engine_state=engine_state_obj,
        )

        # 4. 应用副作用到 SharedContext（Orchestrator 是唯一写入方）
        self._apply_side_effects(shared, step_result.side_effects, decisions)

        # 5. 保存引擎返回的私有状态更新
        engine_states[current_engine_id] = step_result.engine_state_update

        # 6. 执行切换策略：处理 transition_suggestion
        transition: TransitionSuggestion = step_result.transition
        shared.turn_count_in_current_engine += 1

        next_engine_id = current_engine_id
        if transition.type == TransitionType.END_FLOW:
            decisions.append("engine_suggested_end_flow")
            # 目前 MVP 不做真正的结束，只是留痕；未来这里可以返回 END_FLOW token
        elif transition.type == TransitionType.STAY:
            decisions.append("stay_in_current_engine")
            if transition.reset_hint_level is not None:
                shared.last_hint_level_used = transition.reset_hint_level
        elif transition.type in (TransitionType.SWITCH_TO, TransitionType.SWITCH_AND_RETURN):
            target = transition.target_engine_id
            if target and target in ENGINE_REGISTRY and target != current_engine_id:
                return_semantics = transition.type == TransitionType.SWITCH_AND_RETURN
                decisions.append(f"adopt_suggestion:{transition.type.value}->{target}")
                # 将引擎额外上下文（mode / item_count 等）透传到 shared.extras["pending_engine_args"]
                if transition.extra_context:
                    shared.extras["pending_engine_args"] = dict(transition.extra_context)
                shared, engine_states = await self._do_switch(
                    session_id=session_id,
                    shared=shared,
                    engine_states=engine_states,
                    from_engine=current_engine_id,
                    to_engine=target,
                    decided_by="engine_suggestion",
                    reason=transition.reason,
                    return_semantics=return_semantics,
                )
                next_engine_id = target
                switched_to = target
                shared.turn_count_in_current_engine = 0
            else:
                decisions.append(f"ignore_invalid_transition:{transition.type.value}->{target}")
        else:  # 未知枚举
            decisions.append(f"unknown_transition_type:{transition.type.value}")

        # 7. 判断是否需要从 SWITCH_AND_RETURN 返回
        if self._should_return_to_previous(
            step_result=step_result,
            current_engine_id=current_engine_id,
            shared=shared,
        ):
            prev_engine = shared.extras.get("prev_engine_before_switch")
            if prev_engine and prev_engine in ENGINE_REGISTRY and prev_engine != current_engine_id:
                decisions.append(f"auto_return_from_switch_and_return:{prev_engine}")
                shared, engine_states = await self._do_switch(
                    session_id=session_id,
                    shared=shared,
                    engine_states=engine_states,
                    from_engine=current_engine_id,
                    to_engine=prev_engine,
                    decided_by="orchestrator_policy",
                    reason="switch_and_return_completed",
                    return_semantics=False,
                )
                next_engine_id = prev_engine
                switched_to = prev_engine
                shared.turn_count_in_current_engine = 0
                # 消费一次 prev（把它 pop 出来）
                stack = shared.extras.get("return_stack") or []
                if stack:
                    shared.extras["prev_engine_before_switch"] = stack[-1]
                    shared.extras["return_stack"] = stack[:-1]
                else:
                    shared.extras.pop("prev_engine_before_switch", None)

        shared.current_engine_id = next_engine_id

        # 8. 保存到内存 + Redis 持久化
        self._sessions[session_id] = (shared, engine_states)
        await self._persist_session_async(session_id, shared, engine_states)

        return OrchestratorTurnResult(
            reply_text=step_result.reply_text,
            engine_id=next_engine_id,
            flow_stage=shared.current_flow_stage,
            shared_ctx_snapshot=shared_ctx_to_jsonable(shared),
            switched_to=switched_to,
            decision_trace=decisions,
            engine_debug={
                **(step_result.engine_debug_info or {}),
                "input_tokens": step_result.input_tokens,
                "output_tokens": step_result.output_tokens,
                "generation_ms": step_result.generation_ms,
                "ttft_ms": step_result.ttft_ms,
            },
        )

    # ================================================================
    # internals
    # ================================================================
    async def _load_session(
        self, session_id: str
    ) -> tuple[SharedContext, dict[str, dict[str, Any]]]:
        # 1. 先查内存（热路径）
        if session_id in self._sessions:
            return self._sessions[session_id]

        # 2. 内存没有 → 尝试从 Redis 恢复（服务重启后恢复会话的关键路径）
        repo = self._get_repository()
        stored = await repo.load_session(session_id)
        if stored is not None:
            shared_dict, engine_states = stored
            shared = _dict_to_shared_context(shared_dict)
            self._sessions[session_id] = (shared, engine_states)
            logger.info("orchestrator_session_restored_from_redis", session_id=session_id)
            return shared, engine_states

        raise KeyError(f"orchestrator session {session_id} not found — call create_session() first")

    async def _persist_session_async(
        self,
        session_id: str,
        shared: SharedContext,
        engine_states: dict[str, dict[str, Any]],
    ) -> None:
        """将会话状态写入 Redis 持久化（失败不影响主流程）"""
        try:
            repo = self._get_repository()
            shared_dict = shared_ctx_to_jsonable(shared)
            # engine_states 已经是 dict[str, dict]，直接序列化
            await repo.save_session(session_id, shared_dict, engine_states)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "orchestrator_redis_persist_failed_fallback_to_memory",
                session_id=session_id,
                error=str(exc),
            )

    def _get_engine_instance(self, engine_id: str) -> Optional[TeachingEngine]:
        if engine_id not in ENGINE_REGISTRY:
            return None
        if engine_id not in self._engine_instances:
            self._engine_instances[engine_id] = ENGINE_REGISTRY[engine_id]()
        return self._engine_instances[engine_id]

    async def _pick_best_engine(self, shared: SharedContext) -> str:
        """当没有指定初始引擎时，调用所有已注册引擎的 can_handle()，取评分最高者"""
        if not ENGINE_REGISTRY:
            raise RuntimeError(
                "ENGINE_REGISTRY is empty — engines must be registered via @register_engine"
            )
        best_id: Optional[str] = None
        best_score: float = -1.0
        for eid in ENGINE_REGISTRY:
            engine = self._get_engine_instance(eid)
            if engine is None:
                continue
            score = await engine.can_handle(shared.current_flow_stage, shared)
            if score > best_score:
                best_score = score
                best_id = eid
        return best_id or sorted(ENGINE_REGISTRY.keys())[0]

    async def _do_switch(
        self,
        *,
        session_id: str,
        shared: SharedContext,
        engine_states: dict[str, dict[str, Any]],
        from_engine: Optional[str],
        to_engine: str,
        decided_by: str,
        reason: str,
        return_semantics: bool,
    ) -> tuple[SharedContext, dict[str, dict[str, Any]]]:
        """
        执行实际的引擎切换：
        1. on_exit(from_engine)
        2. 记录切换历史
        3. 如果目标引擎从未初始化 → build_initial_state
        4. on_enter(to_engine)
        """
        if from_engine:
            from_inst = self._get_engine_instance(from_engine)
            if from_inst is not None:
                try:
                    await from_inst.on_exit(shared)
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "orchestrator_on_exit_failed",
                        from_engine=from_engine,
                        error=str(exc),
                    )

        # Always update current_engine_id
        shared.current_engine_id = to_engine

        if return_semantics and from_engine:
            # 压栈，便于解释引擎完成后返回
            stack = shared.extras.setdefault("return_stack", [])
            if shared.extras.get("prev_engine_before_switch"):
                stack.append(shared.extras["prev_engine_before_switch"])
            shared.extras["prev_engine_before_switch"] = from_engine

        shared.engine_trace.append(
            TransitionRecord(
                from_engine=from_engine or "",
                to_engine=to_engine,
                reason=reason,
                decided_by=decided_by,
                timestamp=time.time(),
            )
        )
        # 保留前 50 条（避免无限增长）
        if len(shared.engine_trace) > 50:
            shared.engine_trace = shared.engine_trace[-50:]

        if to_engine not in engine_states:
            to_inst = self._get_engine_instance(to_engine)
            if to_inst is not None:
                init = to_inst.build_initial_state(shared)
                engine_states[to_engine] = _engine_state_to_dict(init)
                # 如果有透传参数（例如 explain_mode），合并进去
                pending = shared.extras.pop("pending_engine_args", None)
                if pending and isinstance(pending, dict):
                    engine_states[to_engine] = {**engine_states[to_engine], **pending}

        to_inst = self._get_engine_instance(to_engine)
        if to_inst is not None:
            try:
                await to_inst.on_enter(shared)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "orchestrator_on_enter_failed",
                    to_engine=to_engine,
                    error=str(exc),
                )

        logger.info(
            "orchestrator_engine_switch",
            session_id=session_id,
            from_engine=from_engine,
            to_engine=to_engine,
            decided_by=decided_by,
            reason=reason,
            return_semantics=return_semantics,
        )
        return shared, engine_states

    @staticmethod
    def _apply_side_effects(
        shared: SharedContext,
        effects: EngineSideEffect,
        decisions: list[str],
    ) -> None:
        """把引擎建议的副作用应用到 SharedContext（Orchestrator 独有写入权限）"""
        # 1. 掌握度更新
        for kp_id, delta in (effects.mastery_updates or {}).items():
            prev = shared.mastery_vector.get(kp_id, 0.0)
            new_val = max(0.0, min(1.0, prev + delta))
            shared.mastery_vector[kp_id] = new_val
            # 置信度随着更新次数增加（简化）
            prev_conf = shared.mastery_confidence.get(kp_id, 0.1)
            shared.mastery_confidence[kp_id] = min(0.95, prev_conf + 0.05)
            decisions.append(f"mastery_update:{kp_id} {prev:+.2f}→{new_val:+.2f}")

        # 2. 新增断层
        for gap in effects.add_gaps or []:
            existing = shared.has_gap_of(gap.name)
            if existing is None:
                shared.identified_gaps.append(gap)
                decisions.append(f"add_gap:{gap.name}")
            else:
                # 更新已有断层的严重度
                existing.severity = max(existing.severity, gap.severity)
                existing.last_updated_at = gap.last_updated_at or time.time()

        # 3. 已解释概念
        if effects.explained_ids:
            shared.explained_concept_ids |= set(effects.explained_ids)
            decisions.append(f"mark_explained:{sorted(effects.explained_ids)}")

        # 4. 产出作品
        if effects.produced_assets:
            shared.produced_assets.extend(effects.produced_assets)

        # 5. 错误连击（夹逼在 0..10）
        if effects.wrong_streak_delta:
            shared.recent_wrong_streak = max(
                0, min(10, shared.recent_wrong_streak + effects.wrong_streak_delta)
            )
            decisions.append(
                f"wrong_streak_delta:{effects.wrong_streak_delta}→{shared.recent_wrong_streak}"
            )
            if shared.recent_wrong_streak == 0 and effects.wrong_streak_delta < 0:
                decisions.append("wrong_streak_cleared")

        # 6. 提示级别 & 策略覆盖
        if effects.hint_level_override is not None:
            shared.last_hint_level_used = effects.hint_level_override
        if effects.strategy_override is not None:
            shared.last_strategy_used = effects.strategy_override

        # 7. 阶段建议（引擎能建议但 Orchestrator 保留最终决策权，这里 MVP 直接采纳）
        if (
            effects.stage_suggestion is not None
            and effects.stage_suggestion != shared.current_flow_stage
        ):
            decisions.append(
                f"stage_progress:{shared.current_flow_stage.value}→{effects.stage_suggestion.value}"
            )
            shared.current_flow_stage = effects.stage_suggestion

        # 8. 扩展字段（引擎自定义数据，Orchestrator 不解释直接合并）
        if effects.extra:
            orc_bucket = shared.extras.setdefault("engine_side_effects_extra", {})
            orc_bucket.update(effects.extra)

    @staticmethod
    def _should_return_to_previous(
        *,
        step_result: EngineStepResult,
        current_engine_id: str,
        shared: SharedContext,
    ) -> bool:
        """
        SWITCH_AND_RETURN 完成后自动返回。
        启发式：如果当前引擎（通常是 Explain）给的 transition 是 SWITCH_TO prev，
        或者 step 已标记完成，就返回。
        """
        # 显式引擎建议 SWITCH_TO 就是 prev_engine（Explain adapter 的逻辑）—— 已在上层处理，这里不重复
        if shared.extras.get("prev_engine_before_switch") is None:
            return False
        # 隐式：如果 Explain 标记了 explained_ids 非空 + 用户没有追问更多解释（由 Explain adapter 内部 _user_still_asks_for_more_explain 控制）
        # 这里让 Explain 自己发 SWITCH_TO，避免越俎代庖；MVP 不做隐式返回
        return False


# ======================================================================
# 序列化 / 反序列化辅助（MVP 仅内存，不过把接口定义好便于后续持久化）
# ======================================================================


def _engine_state_to_dict(state_obj: Any) -> dict[str, Any]:
    """把 dataclass 引擎状态转成 dict（MVP 用 dataclasses.asdict，未来可以换成 pydantic）"""
    import dataclasses as _dc

    if _dc.is_dataclass(state_obj):
        data = _dc.asdict(state_obj)  # type: ignore[arg-type]
        # set → list 以便 JSON
        for k, v in list(data.items()):
            if isinstance(v, set):
                data[k] = list(v)
        return data
    if isinstance(state_obj, dict):
        return {k: (list(v) if isinstance(v, set) else v) for k, v in state_obj.items()}
    return {"raw": state_obj}


def _dict_to_engine_state(cls: type, data: dict, fallback: Any) -> Any:
    """MVP：如果 dataclass，把 dict 注入；否则返回 fallback"""
    import dataclasses as _dc
    import typing as _t

    if not data:
        return fallback
    if _dc.is_dataclass(fallback):
        try:
            resolved_hints = _t.get_type_hints(cls)
            kwargs: dict[str, Any] = {}
            for k, v in data.items():
                if k in resolved_hints and _is_set_type(resolved_hints[k]) and isinstance(v, list):
                    kwargs[k] = set(v)
                else:
                    kwargs[k] = v
            return cls(**kwargs)
        except Exception as exc:  # noqa: BLE001
            logger.warning("orchestrator_deser_engine_state_failed", error_type=type(exc).__name__)
            return fallback
    return fallback


def _is_set_type(t: Any) -> bool:
    """检查字段类型是否是 set[...]（支持 PEP585 / typing.Set）"""
    import typing as _t

    origin = getattr(t, "__origin__", None)
    if origin is set:
        return True
    try:
        return t is _t.Set or getattr(t, "__origin__", None) is _t.Set
    except Exception:  # noqa: BLE001
        return False


def shared_ctx_to_jsonable(shared: SharedContext) -> dict[str, Any]:
    """把 SharedContext 变成可返回给客户端的 dict（无类实例）"""
    import dataclasses as _dc

    data = _dc.asdict(shared)
    # enum → value
    data["current_flow_stage"] = shared.current_flow_stage.value
    data["identified_gaps"] = [_dc.asdict(g) for g in shared.identified_gaps]
    data["produced_assets"] = [_dc.asdict(a) for a in shared.produced_assets]
    data["engine_trace"] = [_dc.asdict(r) for r in shared.engine_trace]
    data["explained_concept_ids"] = list(shared.explained_concept_ids)
    return data


def _dict_to_shared_context(data: dict[str, Any]) -> SharedContext:
    """
    从 Redis 反序列化的 dict 还原 SharedContext。
    处理 enum / set / list / dataclass 的类型还原。
    """
    from app.engines.base import (
        FlowStage,
        KnowledgeGap,
        ProducedAsset,
        TransitionRecord,
    )

    # 基础字段
    current_flow_stage = FlowStage(data.get("current_flow_stage", FlowStage.LEARN.value))

    identified_gaps = []
    for g_data in data.get("identified_gaps", []):
        identified_gaps.append(
            KnowledgeGap(
                kp_id=g_data.get("kp_id", ""),
                name=g_data.get("name", ""),
                severity=g_data.get("severity", 0.5),
                evidence_turn_ids=g_data.get("evidence_turn_ids", []),
                last_updated_at=g_data.get("last_updated_at"),
            )
        )

    produced_assets = []
    for a_data in data.get("produced_assets", []):
        produced_assets.append(
            ProducedAsset(
                asset_id=a_data.get("asset_id", ""),
                asset_type=a_data.get("asset_type", ""),
                title=a_data.get("title", ""),
                summary=a_data.get("summary", ""),
                url_or_content=a_data.get("url_or_content", ""),
            )
        )

    engine_trace = []
    for t_data in data.get("engine_trace", []):
        engine_trace.append(
            TransitionRecord(
                from_engine=t_data.get("from_engine", ""),
                to_engine=t_data.get("to_engine", ""),
                reason=t_data.get("reason", ""),
                decided_by=t_data.get("decided_by", ""),
                timestamp=t_data.get("timestamp", 0.0),
            )
        )

    explained = set(data.get("explained_concept_ids", []) or [])

    return SharedContext(
        subject=data.get("subject", "general"),
        knowledge_point_id=data.get("knowledge_point_id"),
        mastery_vector=data.get("mastery_vector", {}) or {},
        mastery_confidence=data.get("mastery_confidence", {}) or {},
        identified_gaps=identified_gaps,
        recent_wrong_streak=data.get("recent_wrong_streak", 0),
        last_hint_level_used=data.get("last_hint_level_used", 2),
        last_strategy_used=data.get("last_strategy_used"),
        explained_concept_ids=explained,
        produced_assets=produced_assets,
        current_flow_stage=current_flow_stage,
        engine_trace=engine_trace,
        current_engine_id=data.get("current_engine_id"),
        turn_count_in_current_engine=data.get("turn_count_in_current_engine", 0),
        learner_persona=data.get("learner_persona", ""),
        learner_preferences=data.get("learner_preferences", {}) or {},
        extras=data.get("extras", {}) or {},
    )


# ======================================================================
# 单例入口
# ======================================================================


_ORCHESTRATOR_SINGLETON: Optional[LearningFlowOrchestrator] = None


def get_orchestrator() -> LearningFlowOrchestrator:
    """获取编排器单例（服务启动后第一次调用时实例化）"""
    global _ORCHESTRATOR_SINGLETON
    if _ORCHESTRATOR_SINGLETON is None:
        _ORCHESTRATOR_SINGLETON = LearningFlowOrchestrator()
    return _ORCHESTRATOR_SINGLETON


__all__ = [
    "LearningFlowOrchestrator",
    "OrchestratorTurnResult",
    "get_orchestrator",
    "shared_ctx_to_jsonable",
]

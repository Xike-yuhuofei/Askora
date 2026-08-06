"""
StateGraph —— Askora 教学流程状态图引擎

实现多智能体编排的状态机，支持：
- 条件转移（基于掌握度、错误连击、置信度）
- 反馈循环（VALIDATE → LEARN 回退）
- 并行分支（DRILL + INQUIRE 并发执行）
- 子图嵌套（复杂学习场景的模块化组织）
- 可配置阈值的转移决策

核心设计：
1. StateGraph 定义状态（FlowStage）和转移规则
2. StateGraphEngine 执行状态图遍历，产出 TransitionDecision
3. 与 LearningFlowOrchestrator 协同，作为其「下一步决策大脑」

典型用法：
    engine = StateGraphEngine()
    decision = engine.get_next_stage(shared_ctx)
    if decision.confidence >= 0.6:
        shared_ctx.current_flow_stage = decision.next_stage
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from app.core.logging import get_logger
from app.engines.base import FlowStage, SharedContext

logger = get_logger(__name__)


# ======================================================================
# 数据结构
# ======================================================================


@dataclass
class TransitionDecision:
    """
    状态转移决策结果。

    由 StateGraphEngine.get_next_stage() 返回，
    Orchestrator 可根据此决策更新 FlowStage 和引擎选择。

    Attributes:
        next_stage: 推荐的下一学习阶段
        confidence: 转移置信度（0.0 ~ 1.0）
        reason: 人类可读的转移原因（如 "mastery_low_feedback_loop"）
        recommended_engine: 推荐使用的引擎 ID（可选）
    """

    next_stage: FlowStage
    confidence: float
    reason: str
    recommended_engine: Optional[str] = None


@dataclass
class StateNode:
    """
    状态图中的节点，封装一个 FlowStage 及其关联的处理器。

    Attributes:
        stage: 对应的 FlowStage
        handlers: 进入该状态时执行的回调函数列表
        subgraph: 嵌套子图（用于复杂场景的模块化）
    """

    stage: FlowStage
    handlers: list[Callable[[SharedContext], None]] = field(default_factory=list)
    subgraph: Optional["StateGraph"] = None


@dataclass
class Transition:
    """
    状态转移规则。

    定义从 from_stage 到 to_stage 的条件转移，
    支持通过 priority 控制多条规则的评估顺序。

    Attributes:
        from_stage: 源状态
        to_stage: 目标状态
        condition: 判断是否触发转移的条件函数
        priority: 优先级（数值越大越先评估）
        name: 转移名称（用于日志和审计）
    """

    from_stage: FlowStage
    to_stage: FlowStage
    condition: Callable[[SharedContext], bool]
    priority: int = 0
    name: str = ""


# ======================================================================
# StateGraph —— 状态图定义
# ======================================================================


class StateGraph:
    """
    教学流程状态图。

    以 FlowStage 为节点，以条件函数为边，
    定义学习流程的状态流转规则。

    支持的高级特性：
    - 条件转移：每条边绑定一个 condition(ctx) -> bool
    - 反馈循环：VALIDATE 掌握度低 → LEARN 重新学习
    - 并行分支：DRILL 与 INQUIRE 可并发运行
    - 子图嵌套：复杂场景可拆分为嵌套子图

    用法：
        graph = StateGraph("custom_flow")
        graph.add_state(FlowStage.LEARN)
        graph.add_state(FlowStage.VALIDATE)
        graph.add_transition(
            FlowStage.VALIDATE, FlowStage.LEARN,
            condition=lambda ctx: ctx.mastery_vector.get(kp_id, 0) < 0.3,
            name="feedback_loop",
        )
    """

    def __init__(self, name: str = "default") -> None:
        self.name: str = name
        self._nodes: dict[FlowStage, StateNode] = {}
        self._transitions: list[Transition] = []
        self._parallel_groups: list[frozenset[FlowStage]] = []
        self._subgraphs: dict[str, StateGraph] = {}

    # ------------------------------------------------------------------
    # 节点管理
    # ------------------------------------------------------------------

    def add_state(
        self,
        stage: FlowStage,
        handlers: Optional[list[Callable[[SharedContext], None]]] = None,
        subgraph: Optional[StateGraph] = None,
    ) -> StateNode:
        """
        添加一个状态节点到图中。

        Args:
            stage: 对应的 FlowStage
            handlers: 进入该状态时执行的回调列表
            subgraph: 嵌套子图（可选）

        Returns:
            创建的 StateNode 实例
        """
        node = StateNode(stage=stage, handlers=handlers or [], subgraph=subgraph)
        self._nodes[stage] = node
        return node

    def get_node(self, stage: FlowStage) -> Optional[StateNode]:
        """获取指定阶段的节点，不存在则返回 None"""
        return self._nodes.get(stage)

    # ------------------------------------------------------------------
    # 转移管理
    # ------------------------------------------------------------------

    def add_transition(
        self,
        from_stage: FlowStage,
        to_stage: FlowStage,
        condition: Callable[[SharedContext], bool],
        priority: int = 0,
        name: str = "",
    ) -> None:
        """
        添加一条转移规则。

        如果 from_stage 或 to_stage 尚未作为节点存在，
        会自动创建对应的空节点。

        Args:
            from_stage: 源状态
            to_stage: 目标状态
            condition: 条件函数，接收 SharedContext，返回 bool
            priority: 优先级，数值越大越先评估（默认 0）
            name: 转移名称，用于日志和审计
        """
        if from_stage not in self._nodes:
            self.add_state(from_stage)
        if to_stage not in self._nodes:
            self.add_state(to_stage)

        self._transitions.append(
            Transition(
                from_stage=from_stage,
                to_stage=to_stage,
                condition=condition,
                priority=priority,
                name=name,
            )
        )

    def get_transitions_from(self, stage: FlowStage) -> list[Transition]:
        """
        获取从指定状态出发的所有转移规则。

        Args:
            stage: 源状态

        Returns:
            该状态的转移规则列表（按优先级降序排列）
        """
        return sorted(
            [t for t in self._transitions if t.from_stage == stage],
            key=lambda t: t.priority,
            reverse=True,
        )

    def get_transitions_to(self, stage: FlowStage) -> list[Transition]:
        """获取指向指定状态的所有转移规则"""
        return [t for t in self._transitions if t.to_stage == stage]

    # ------------------------------------------------------------------
    # 并行分支
    # ------------------------------------------------------------------

    def add_parallel_group(self, stages: set[FlowStage]) -> None:
        """
        添加并行分支组。

        组内的状态被视为可以并发执行。
        例如 DRILL 和 INQUIRE 可以同时进行：
        学生一边做练习题（DRILL），一边向系统提问（INQUIRE）。

        Args:
            stages: 属于同一并行组的状态集合
        """
        frozenset_key = frozenset(stages)
        for stage in stages:
            if stage not in self._nodes:
                self.add_state(stage)
        if frozenset_key not in self._parallel_groups:
            self._parallel_groups.append(frozenset_key)

    def is_parallel(self, stage: FlowStage) -> bool:
        """检查指定状态是否属于某个并行分支组"""
        return any(stage in group for group in self._parallel_groups)

    def get_parallel_group(self, stage: FlowStage) -> Optional[frozenset[FlowStage]]:
        """获取指定状态所属的并行分支组（不存在返回 None）"""
        for group in self._parallel_groups:
            if stage in group:
                return group
        return None

    # ------------------------------------------------------------------
    # 子图管理
    # ------------------------------------------------------------------

    def add_subgraph(self, key: str, subgraph: StateGraph) -> None:
        """
        注册一个命名子图。

        子图可被 StateNode.subgraph 引用，
        实现复杂学习场景的模块化组织。

        Args:
            key: 子图的唯一标识
            subgraph: 嵌套的 StateGraph 实例
        """
        self._subgraphs[key] = subgraph

    def get_subgraph(self, key: str) -> Optional[StateGraph]:
        """按名称获取子图"""
        return self._subgraphs.get(key)

    # ------------------------------------------------------------------
    # 属性导出
    # ------------------------------------------------------------------

    @property
    def nodes(self) -> dict[FlowStage, StateNode]:
        """所有节点的只读副本"""
        return dict(self._nodes)

    @property
    def transitions(self) -> list[Transition]:
        """所有转移规则的只读副本"""
        return list(self._transitions)

    @property
    def parallel_groups(self) -> list[frozenset[FlowStage]]:
        """所有并行分支组的只读副本"""
        return list(self._parallel_groups)

    @property
    def subgraphs(self) -> dict[str, StateGraph]:
        """所有子图的只读副本"""
        return dict(self._subgraphs)


# ======================================================================
# StateGraphEngine —— 状态图引擎
# ======================================================================


class StateGraphEngine:
    """
    状态图引擎 —— 多智能体编排的决策核心。

    负责根据 SharedContext 遍历 StateGraph，
    产出下一步的 TransitionDecision，供 Orchestrator 采用。

    与 Orchestrator 的协作方式：
    1. Orchestrator 在初始化时创建 StateGraphEngine 实例
    2. 每轮交互后，Orchestrator 调用 get_next_stage()
       获取基于当前 SharedContext 的阶段转移建议
    3. Orchestrator 根据 should_transition() 的结果
       决定是否采纳转移建议（可覆盖）

    阈值可配置：
        engine = StateGraphEngine()
        engine.set_thresholds(mastery_low=0.4, mastery_high=0.75)
    """

    # 默认引擎映射：每个 FlowStage 对应的推荐引擎列表
    _STAGE_ENGINE_MAP: dict[FlowStage, list[str]] = {
        FlowStage.DIAGNOSE: ["quiz", "diagnostic"],
        FlowStage.LEARN: ["explain", "socratic"],
        FlowStage.INQUIRE: ["socratic", "inquiry"],
        FlowStage.VALIDATE: ["quiz"],
        FlowStage.DRILL: ["drill"],
        FlowStage.PRODUCE: ["produce", "project"],
    }

    def __init__(self, graph: Optional[StateGraph] = None) -> None:
        """
        初始化状态图引擎。

        Args:
            graph: 自定义状态图，为 None 时使用内置默认图
        """
        self._default_thresholds: dict[str, float] = {
            "mastery_low": 0.3,
            "mastery_high": 0.7,
            "mastery_medium_low": 0.3,
            "mastery_medium_high": 0.7,
            "error_streak_limit": 3.0,
            "confidence_low": 0.2,
            "transition_confidence_threshold": 0.5,
        }
        self._visit_depth_limit: int = 10
        self._graph: StateGraph = graph or self._build_default_graph()

    # ------------------------------------------------------------------
    # 属性
    # ------------------------------------------------------------------

    @property
    def graph(self) -> StateGraph:
        """当前使用的状态图"""
        return self._graph

    def get_threshold(self, key: str) -> float:
        """获取指定阈值的当前值"""
        return self._default_thresholds.get(key, 0.5)

    def set_thresholds(self, **kwargs: float) -> None:
        """
        批量更新阈值。

        仅接受 _default_thresholds 中已定义的 key，
        未知 key 会被静默忽略。

        Args:
            **kwargs: 阈值名称 → 新值 的映射
        """
        for key, value in kwargs.items():
            if key in self._default_thresholds:
                self._default_thresholds[key] = value

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------

    def get_next_stage(self, shared_ctx: SharedContext) -> TransitionDecision:
        """
        根据共享上下文确定下一阶段。

        执行流程：
        1. 检查当前节点是否关联子图（子图优先评估）
        2. 获取当前状态的所有转移规则
        3. 按优先级逐一评估条件函数
        4. 返回首个满足条件的转移决策
        5. 无匹配则返回「保持当前阶段」的决策

        Args:
            shared_ctx: 当前会话的共享上下文

        Returns:
            TransitionDecision 实例
        """
        return self._resolve_next_stage(shared_ctx, _visited=set(), _depth=0)

    def should_transition(
        self,
        shared_ctx: SharedContext,
        threshold: Optional[float] = None,
    ) -> bool:
        """
        判断是否应该发生状态转移。

        计算 get_next_stage() 的结果，并检查：
        1. 下一阶段是否与当前阶段不同
        2. 转移置信度是否 >= 阈值

        Args:
            shared_ctx: 共享上下文
            threshold: 置信度阈值，None 时使用默认阈值

        Returns:
            是否建议转移
        """
        decision = self.get_next_stage(shared_ctx)
        effective_threshold = (
            threshold
            if threshold is not None
            else self._default_thresholds["transition_confidence_threshold"]
        )
        return (
            decision.next_stage != shared_ctx.current_flow_stage
            and decision.confidence >= effective_threshold
        )

    # ------------------------------------------------------------------
    # 内部实现
    # ------------------------------------------------------------------

    def _resolve_next_stage(
        self,
        shared_ctx: SharedContext,
        _visited: set[int],
        _depth: int,
    ) -> TransitionDecision:
        """
        递归解析下一阶段。

        支持子图嵌套，通过 _visited 和 _depth 防止无限递归。

        Args:
            shared_ctx: 共享上下文
            _visited: 已访问的 id 集合（防循环）
            _depth: 当前递归深度（防过深）

        Returns:
            转移决策
        """
        if _depth > self._visit_depth_limit:
            logger.warning(
                "stategraph_max_depth_reached",
                depth=_depth,
                current_stage=shared_ctx.current_flow_stage.value,
            )
            return self._stay_decision(shared_ctx, "max_depth_reached_fallback")

        current_stage = shared_ctx.current_flow_stage
        node = self._graph.get_node(current_stage)

        # ---- 子图优先 ----
        if node and node.subgraph is not None:
            node_id = id(node.subgraph)
            if node_id not in _visited:
                _visited.add(node_id)
                sub_engine = StateGraphEngine(node.subgraph)
                sub_ctx = self._make_subgraph_context(shared_ctx, current_stage)
                return sub_engine._resolve_next_stage(sub_ctx, _visited, _depth + 1)

        # ---- 评估转移条件 ----
        transitions = self._graph.get_transitions_from(current_stage)

        for transition in transitions:
            try:
                if transition.condition(shared_ctx):
                    confidence = self._compute_confidence(shared_ctx, transition)
                    reason = transition.name or getattr(
                        transition.condition, "__name__", "unnamed_condition"
                    )
                    recommended = self._infer_engine_for_stage(transition.to_stage)

                    logger.info(
                        "stategraph_transition_fired",
                        from_stage=current_stage.value,
                        to_stage=transition.to_stage.value,
                        reason=reason,
                        confidence=confidence,
                        priority=transition.priority,
                    )

                    return TransitionDecision(
                        next_stage=transition.to_stage,
                        confidence=confidence,
                        reason=reason,
                        recommended_engine=recommended,
                    )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "stategraph_transition_condition_error",
                    from_stage=current_stage.value,
                    to_stage=transition.to_stage.value,
                    error=str(exc),
                )
                continue

        # ---- 无匹配转移：保持当前 ----
        return self._stay_decision(shared_ctx, "no_transition_condition_met")

    @staticmethod
    def _stay_decision(
        shared_ctx: SharedContext,
        reason: str,
    ) -> TransitionDecision:
        """构建「保持当前阶段」的决策"""
        return TransitionDecision(
            next_stage=shared_ctx.current_flow_stage,
            confidence=0.5,
            reason=reason,
            recommended_engine=shared_ctx.current_engine_id,
        )

    @staticmethod
    def _make_subgraph_context(
        shared_ctx: SharedContext,
        stage: FlowStage,
    ) -> SharedContext:
        """为子图创建共享上下文的副本，将 current_flow_stage 重置为子图入口"""
        import dataclasses as _dc

        ctx_copy = _dc.replace(shared_ctx)
        ctx_copy.current_flow_stage = stage
        return ctx_copy

    def _compute_confidence(
        self,
        shared_ctx: SharedContext,
        transition: Transition,
    ) -> float:
        """
        计算转移的置信度。

        综合考虑以下因素：
        1. 目标知识点的掌握度（mastery 越高，转移确定性越高）
        2. 错误连击数（连击越多，反馈回退的信心越高）
        3. 掌握度置信度（confidence 越高，判断越可靠）

        Args:
            shared_ctx: 共享上下文
            transition: 当前正在评估的转移规则

        Returns:
            0.0 ~ 0.95 的置信度值
        """
        confidence = 0.5

        kp_id = shared_ctx.knowledge_point_id
        if kp_id and kp_id in shared_ctx.mastery_vector:
            mastery = shared_ctx.mastery_vector[kp_id]
            # 掌握度与置信度正相关：掌握度越高，转移判断越确定
            confidence = min(0.95, max(0.1, 0.3 + mastery * 0.65))

        error_limit = self._default_thresholds["error_streak_limit"]
        if shared_ctx.recent_wrong_streak >= error_limit:
            confidence = min(0.95, confidence + 0.2)

        if kp_id and kp_id in shared_ctx.mastery_confidence:
            conf_val = shared_ctx.mastery_confidence[kp_id]
            low_conf = self._default_thresholds["confidence_low"]
            if conf_val > low_conf:
                confidence = min(0.95, confidence + 0.1)

        return round(confidence, 3)

    def _infer_engine_for_stage(self, stage: FlowStage) -> Optional[str]:
        """
        根据 FlowStage 推断推荐的引擎 ID。

        基于内置的阶段-引擎映射表，取第一个候选。

        Args:
            stage: 目标学习阶段

        Returns:
            推荐引擎 ID，或 None
        """
        candidates = self._STAGE_ENGINE_MAP.get(stage, [])
        return candidates[0] if candidates else None

    # ------------------------------------------------------------------
    # 默认图构建
    # ------------------------------------------------------------------

    def _build_default_graph(self) -> StateGraph:
        """
        构建 Askora 内置的默认学习流程状态图。

        流程概述：
            DIAGNOSE → LEARN → INQUIRE → VALIDATE → DRILL → PRODUCE
                         ↑                    ↓         ↓
                         └──── 反馈循环 ←──────  ←────────┘

        核心转移规则：
        - DIAGNOSE → LEARN:  诊断完成（置信度 >= 0.6 或已识别断层）
        - LEARN → INQUIRE:   掌握度中等（0.3~0.7）
        - LEARN → DRILL:     错误连击过高（>= 3）
        - LEARN → PRODUCE:   掌握度高（>= 0.7）
        - LEARN → VALIDATE:  掌握度低（< 0.3）
        - INQUIRE → LEARN:   探究中发现新断层
        - INQUIRE → VALIDATE: 无断层，可进入验证
        - VALIDATE → LEARN:  验证掌握度低 → 反馈回学习（核心反馈循环）
        - VALIDATE → DRILL:  验证掌握度中等 → 进入练习
        - VALIDATE → PRODUCE: 验证掌握度高 → 进入产出
        - DRILL → VALIDATE:  练习完成，重新验证
        - DRILL → INQUIRE:   练习中错误连击 → 需要引导
        - PRODUCE → DIAGNOSE: 完成学习单元，诊断新知识点
        """
        graph = StateGraph(name="askora_default_flow")

        thresholds = self._default_thresholds

        # ---- 条件函数工厂 ----
        def _diagnose_complete(ctx: SharedContext) -> bool:
            kp_id = ctx.knowledge_point_id
            if kp_id and kp_id in ctx.mastery_confidence:
                return ctx.mastery_confidence[kp_id] >= 0.6
            return len(ctx.identified_gaps) > 0

        def _mastery_high(ctx: SharedContext) -> bool:
            kp_id = ctx.knowledge_point_id
            if kp_id and kp_id in ctx.mastery_vector:
                return ctx.mastery_vector[kp_id] >= thresholds["mastery_high"]
            return False

        def _mastery_low(ctx: SharedContext) -> bool:
            kp_id = ctx.knowledge_point_id
            if kp_id and kp_id in ctx.mastery_vector:
                return ctx.mastery_vector[kp_id] < thresholds["mastery_low"]
            return True

        def _mastery_medium(ctx: SharedContext) -> bool:
            kp_id = ctx.knowledge_point_id
            if kp_id and kp_id in ctx.mastery_vector:
                m = ctx.mastery_vector[kp_id]
                return thresholds["mastery_low"] <= m < thresholds["mastery_high"]
            return False

        def _error_streak_high(ctx: SharedContext) -> bool:
            return ctx.recent_wrong_streak >= thresholds["error_streak_limit"]

        def _has_gaps(ctx: SharedContext) -> bool:
            return len(ctx.identified_gaps) > 0

        def _no_gaps(ctx: SharedContext) -> bool:
            return len(ctx.identified_gaps) == 0

        # ---- 注册所有状态 ----
        for stage in FlowStage:
            graph.add_state(stage)

        # ---- 转移规则（优先级从高到低）----

        # DIAGNOSE → LEARN：诊断完成，进入学习
        graph.add_transition(
            from_stage=FlowStage.DIAGNOSE,
            to_stage=FlowStage.LEARN,
            condition=_diagnose_complete,
            priority=10,
            name="diagnose_to_learn",
        )

        # LEARN → DRILL：学习中错误连击过多，需要大量练习（高优先级）
        graph.add_transition(
            from_stage=FlowStage.LEARN,
            to_stage=FlowStage.DRILL,
            condition=_error_streak_high,
            priority=8,
            name="learn_to_drill_error_streak",
        )

        # LEARN → PRODUCE：学习后掌握度高，可跳过中间环节进入产出
        graph.add_transition(
            from_stage=FlowStage.LEARN,
            to_stage=FlowStage.PRODUCE,
            condition=_mastery_high,
            priority=6,
            name="learn_to_produce_advanced",
        )

        # LEARN → INQUIRE：学习后掌握度中等，需要进一步探究
        graph.add_transition(
            from_stage=FlowStage.LEARN,
            to_stage=FlowStage.INQUIRE,
            condition=_mastery_medium,
            priority=5,
            name="learn_to_inquire",
        )

        # LEARN → VALIDATE：学习后掌握度低，先做一次小测试确认
        graph.add_transition(
            from_stage=FlowStage.LEARN,
            to_stage=FlowStage.VALIDATE,
            condition=_mastery_low,
            priority=4,
            name="learn_to_validate",
        )

        # INQUIRE → LEARN：探究中发现新的知识断层，回到学习补充
        graph.add_transition(
            from_stage=FlowStage.INQUIRE,
            to_stage=FlowStage.LEARN,
            condition=_has_gaps,
            priority=8,
            name="inquire_to_learn_gaps_found",
        )

        # INQUIRE → VALIDATE：探究完成且无断层，进入验证
        graph.add_transition(
            from_stage=FlowStage.INQUIRE,
            to_stage=FlowStage.VALIDATE,
            condition=_no_gaps,
            priority=5,
            name="inquire_to_validate",
        )

        # VALIDATE → LEARN：验证失败，掌握度低 —— 核心反馈循环
        graph.add_transition(
            from_stage=FlowStage.VALIDATE,
            to_stage=FlowStage.LEARN,
            condition=_mastery_low,
            priority=10,
            name="validate_to_learn_feedback_loop",
        )

        # VALIDATE → PRODUCE：验证通过，掌握度高，进入产出
        graph.add_transition(
            from_stage=FlowStage.VALIDATE,
            to_stage=FlowStage.PRODUCE,
            condition=_mastery_high,
            priority=8,
            name="validate_to_produce_advance",
        )

        # VALIDATE → DRILL：验证掌握度中等，需要变式练习巩固
        graph.add_transition(
            from_stage=FlowStage.VALIDATE,
            to_stage=FlowStage.DRILL,
            condition=_mastery_medium,
            priority=5,
            name="validate_to_drill",
        )

        # DRILL → INQUIRE：练习中错误连击过多，需要引导式帮助
        graph.add_transition(
            from_stage=FlowStage.DRILL,
            to_stage=FlowStage.INQUIRE,
            condition=_error_streak_high,
            priority=8,
            name="drill_to_inquire_scaffold",
        )

        # DRILL → VALIDATE：练习完成且无断层，重新验证
        graph.add_transition(
            from_stage=FlowStage.DRILL,
            to_stage=FlowStage.VALIDATE,
            condition=_no_gaps,
            priority=5,
            name="drill_to_validate",
        )

        # PRODUCE → DIAGNOSE：完成一个学习单元，开始诊断新知识点
        graph.add_transition(
            from_stage=FlowStage.PRODUCE,
            to_stage=FlowStage.DIAGNOSE,
            condition=_no_gaps,
            priority=5,
            name="produce_to_diagnose_new_topic",
        )

        # ---- 并行分支定义 ----
        # DRILL 和 INQUIRE 可以并发执行：
        # 学生一边做题（DRILL），一边向系统提问（INQUIRE）
        graph.add_parallel_group({FlowStage.DRILL, FlowStage.INQUIRE})

        return graph


# ======================================================================
# 便捷入口
# ======================================================================


def create_state_graph_engine(
    graph: Optional[StateGraph] = None,
    **thresholds: float,
) -> StateGraphEngine:
    """
    创建 StateGraphEngine 实例的便捷工厂函数。

    Args:
        graph: 自定义状态图（为 None 时使用默认图）
        **thresholds: 覆盖默认阈值，例如 mastery_low=0.4

    Returns:
        配置好的 StateGraphEngine 实例
    """
    engine = StateGraphEngine(graph=graph)
    if thresholds:
        engine.set_thresholds(**thresholds)
    return engine


__all__ = [
    # 数据结构
    "TransitionDecision",
    "StateNode",
    "Transition",
    # 核心类
    "StateGraph",
    "StateGraphEngine",
    # 工厂函数
    "create_state_graph_engine",
]

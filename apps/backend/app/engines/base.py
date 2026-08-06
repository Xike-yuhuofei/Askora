"""
Teaching Engine Interface (TEI v1) — Askora 教学引擎统一抽象接口

所有教学引擎（Socratic / Explain / Quiz / Drill / Inquiry / Coach / Project / Produce）
必须实现本文件定义的 TeachingEngine ABC 类，才能被 LearningFlowOrchestrator 调度。

核心设计决策：
1. 引擎是无状态的纯函数管道，内部状态通过 build_initial_state / engine_state 外置
2. 引擎输出不仅有回复，还要产出「对 SharedContext 的副作用建议」和「下一步切换引擎建议」
   （即 transition_suggestion，Orchestrator 可采纳也可覆盖）
3. 不做 if/else 人群分支，人群特征通过 can_handle() 评分权重 + shared_ctx.learner_persona 读取
4. 向后兼容：现有 SocraticEngine 不会被改动，通过适配器包装成 TEI 实现
"""

from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generic, Optional, TypeVar

# ========== 认知维度枚举（对应上方 4×4 引擎矩阵的轴）==========


class CognitiveLevel(str, enum.Enum):
    """认知参与深度（布鲁姆分类法简化版）"""

    RECEIVE = "L1_receive"  # 接受式：讲解 / 综述 / 案例 / 叙事
    GUIDE = "L2_guide"  # 引导式：苏格拉底 / 探究 / 教练
    PRACTICE = "L3_practice"  # 练习式：测验 / 变式 / 错题 / 模拟
    CREATE = "L4_create"  # 创造式：求解 / 建造 / 项目 / 产出


class TaskOpenness(str, enum.Enum):
    """任务开放度（是否有唯一标准答案）"""

    CLOSED = "closed"  # 结构化：有标准答案
    SEMI_STRUCTURED = "semi"  # 半结构化：多步推理
    OPEN = "open"  # 开放式：多元答案真实情境
    GENERATIVE = "generative"  # 创生式：端到端个性化产出


class FlowStage(str, enum.Enum):
    """学习流程阶段（Orchestrator 的调度阶段，引擎根据阶段给出适配评分）"""

    DIAGNOSE = "diagnose"  # P1 诊断：前置掌握度 / 断层识别
    LEARN = "learn"  # P2 学习：讲解 / 概念建立
    INQUIRE = "inquire"  # P3 探究：引导 / 思维建模
    VALIDATE = "validate"  # P4 验证：小测试确认掌握
    DRILL = "drill"  # P5 练习：变式巩固
    PRODUCE = "produce"  # P6 产出：项目 / 作品 / 复盘


class TransitionType(str, enum.Enum):
    """引擎间切换建议的类型"""

    STAY = "stay"  # 继续当前引擎（可带参数微调）
    SWITCH_TO = "switch_to"  # 切换到指定引擎（一次）
    SWITCH_AND_RETURN = "switch_and_return"  # 切换到指定引擎，完成后自动返回当前引擎
    END_FLOW = "end_flow"  # 本学习单元结束


EngineStateT = TypeVar("EngineStateT")


# ========== 共享上下文（跨引擎无缝传递） ==========


@dataclass
class KnowledgeGap:
    """已识别的知识断层（Quiz / Error 引擎产出，Explain / Socratic 会消费）"""

    kp_id: str  # 知识点 ID
    name: str  # 人类可读名称
    severity: float = 0.5  # 0~1 严重程度
    evidence_turn_ids: list[str] = field(default_factory=list)  # 在哪几轮对话中暴露出来
    last_updated_at: Optional[float] = None  # unix ts


@dataclass
class ProducedAsset:
    """引擎产出的作品（Project / Produce 引擎生成）"""

    asset_id: str
    asset_type: str  # "note" / "code" / "chart" / "course_outline" / "reflection"
    title: str
    summary: str
    url_or_content: str = ""


@dataclass
class TransitionRecord:
    """引擎切换历史（可审计，用于复盘为什么切了引擎）"""

    from_engine: str
    to_engine: str
    reason: str  # "stuck_wrong_streak" / "mastery_threshold" / "flow_stage_progress"
    decided_by: str  # "engine_suggestion" / "orchestrator_policy" / "manual_override"
    timestamp: float


@dataclass
class SharedContext:
    """
    跨引擎共享状态仓库。

    注意：这里不存用户 PII（姓名 / 手机号 / 邮箱），只保留 pseudonym_id 关联。
    PII 留在 User 模型中，符合 Askora 现有「PII 域 / 学习数据域 双轨隔离」设计。
    """

    # ==== 学习本体（引擎间最常读写的部分）====
    subject: str = "general"
    knowledge_point_id: Optional[str] = None
    mastery_vector: dict[str, float] = field(default_factory=dict)  # kp_id -> [0,1]
    mastery_confidence: dict[str, float] = field(default_factory=dict)  # kp_id -> [0,1]
    identified_gaps: list[KnowledgeGap] = field(default_factory=list)

    # ==== 交互元数据（所有引擎写入，帮助下一个引擎建立上下文感知）====
    recent_wrong_streak: int = 0
    last_hint_level_used: int = 2
    last_strategy_used: Optional[str] = None
    explained_concept_ids: set[str] = field(default_factory=set)  # 已经讲解过，不再从零引导
    produced_assets: list[ProducedAsset] = field(default_factory=list)

    # ==== 调度 & 审计 ====
    current_flow_stage: FlowStage = FlowStage.LEARN
    engine_trace: list[TransitionRecord] = field(default_factory=list)
    current_engine_id: Optional[str] = None
    turn_count_in_current_engine: int = 0

    # ==== 人群特征（不做架构分支，只改引擎内部参数权重）====
    # value 示例: "k12_primary" / "k12_high" / "higher_ed" / "professional" / "adult_general" / "senior"
    # 默认为空字符串表示「无偏好」，所有引擎用中性权重评分
    learner_persona: str = ""
    # 更细粒度的偏好（可选）：{ "difficulty_pref": "moderate", "case_domain_pref": "sports", "explain_style": "analogy_first" }
    learner_preferences: dict[str, str] = field(default_factory=dict)

    # ==== 扩展字段（业务自定义，Orchestrator 不解释，原样透传）====
    extras: dict[str, Any] = field(default_factory=dict)

    def has_gap_of(self, kp_name_fragment: str) -> Optional[KnowledgeGap]:
        """便捷查询：看是否已经有某个名字相关的断层"""
        kp_name_fragment = kp_name_fragment.strip().lower()
        if not kp_name_fragment:
            return None
        for g in self.identified_gaps:
            if kp_name_fragment in g.name.lower():
                return g
        return None


# ========== 引擎统一输入 / 输出 ==========


@dataclass
class LearnerTurn:
    """学习者本轮输入（口语化内容 / 选择答案 / 上传文件链接等）"""

    text: str
    turn_id: str = ""
    attachments: list[dict[str, str]] = field(default_factory=list)  # {"type":"image","url":"..."}


@dataclass
class TransitionSuggestion:
    """
    引擎给 Orchestrator 的反向建议：「下一步我建议怎么办」。

    Orchestrator 有权采纳 / 覆盖 / 忽略，但会把决策写入 engine_trace 留痕。
    """

    type: TransitionType = TransitionType.STAY
    target_engine_id: Optional[str] = None  # SWITCH_TO 时使用
    reset_hint_level: Optional[int] = None  # STAY 时可带
    extra_context: dict[str, Any] = field(default_factory=dict)  # 透传给目标引擎
    reason: str = "engine_suggested_stay"


@dataclass
class EngineSideEffect:
    """
    引擎建议对 SharedContext 的修改（不能直接改，Orchestrator 会根据策略应用或拒绝）。

    采用建议模式而不是引擎直接修改，保证 Orchestrator 是唯一状态写入方（便于审计 / 回滚）。
    """

    mastery_updates: dict[str, float] = field(default_factory=dict)  # kp_id -> mastery_delta
    add_gaps: list[KnowledgeGap] = field(default_factory=list)
    explained_ids: set[str] = field(default_factory=set)
    produced_assets: list[ProducedAsset] = field(default_factory=list)
    wrong_streak_delta: int = 0
    hint_level_override: Optional[int] = None
    strategy_override: Optional[str] = None
    stage_suggestion: Optional[FlowStage] = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class EngineStepResult:
    """所有教学引擎 step() 的统一返回结构"""

    reply_text: str  # 本轮要呈现给学习者的内容
    engine_state_update: dict[str, Any]  # 写入当前引擎私有状态（Orchestrator 原样保存）
    side_effects: EngineSideEffect = field(default_factory=EngineSideEffect)
    transition: TransitionSuggestion = field(default_factory=TransitionSuggestion)

    # 元数据：性能 / 审计
    input_tokens: int = 0
    output_tokens: int = 0
    generation_ms: int = 0
    ttft_ms: Optional[int] = None
    engine_debug_info: dict[str, Any] = field(default_factory=dict)  # 不返回给客户端，仅用于日志


# ========== TEI 抽象接口（所有引擎必须实现）==========


class TeachingEngine(ABC, Generic[EngineStateT]):
    """
    Teaching Engine Interface (TEI v1) —— 所有教学引擎的统一抽象。

    请在具体子类上使用 @register_engine 装饰器将其注册到全局注册表，
    这样 LearningFlowOrchestrator 才能按 engine_id 动态调度。
    """

    # ==== 元信息（子类必须覆盖）====
    engine_id: str = ""  # 唯一 ID，例如 "socratic" / "explain"
    engine_name: str = ""  # 中文展示名，例如 "苏格拉底引导引擎"
    supported_cognitive_levels: list[CognitiveLevel] = []
    supported_openness: list[TaskOpenness] = []

    # ==== 生命周期钩子（可选覆盖，默认实现为 noop）====

    async def on_enter(self, shared_ctx: SharedContext) -> None:
        """
        Orchestrator 切换进本引擎时调用（可用于预热 / 加载专用题库 / 初始化资源）。
        默认空实现。
        """
        return None

    async def on_exit(self, shared_ctx: SharedContext) -> None:
        """Orchestrator 切换出本引擎时调用（可选，用于写总结报告 / 关闭资源）。"""
        return None

    # ==== 核心：适配评分 + 单步执行 + 初始化状态 ====

    @abstractmethod
    async def can_handle(
        self,
        flow_stage: FlowStage,
        shared_ctx: SharedContext,
    ) -> float:
        """
        返回 0~1，表示本引擎适配当前阶段 / 上下文的程度。

        Orchestrator 在需要自动选引擎时，会调用所有已注册引擎的 can_handle()，
        取加权评分最高的一个。默认推荐：
        - 完全匹配当前 flow_stage + 人群适配度好 → 0.8~1.0
        - 能用但不是最优 → 0.4~0.7
        - 不适合（例如 Drills 在 DIAGNOSE 阶段）→ 0~0.3
        """

    @abstractmethod
    def build_initial_state(self, shared_ctx: SharedContext) -> EngineStateT:
        """
        引擎内部状态的初始值（引擎实例无状态，状态外置在 Orchestrator 的会话记录中）。
        首次进入本引擎时调用；切换回来时会使用之前保存的状态，不再调用。
        """

    @abstractmethod
    async def step(
        self,
        learner_input: LearnerTurn,
        flow_stage: FlowStage,
        shared_ctx: SharedContext,
        engine_state: EngineStateT,
    ) -> EngineStepResult:
        """
        执行一个交互轮次：读取学习者输入 + 当前上下文 + 引擎私有状态，
        产出「回复 + 副作用建议 + 下一步切换建议」。

        要求：
        - 内部可以自由调用 LLM / RAG / 工具，但不得直接修改 shared_ctx（应通过 side_effects 建议）
        - 不得直接写 DB / Redis（Orchestrator 会在应用 side_effects 后统一持久化）
        """


__all__ = [
    # enums
    "CognitiveLevel",
    "TaskOpenness",
    "FlowStage",
    "TransitionType",
    # dataclasses
    "KnowledgeGap",
    "ProducedAsset",
    "TransitionRecord",
    "SharedContext",
    "LearnerTurn",
    "TransitionSuggestion",
    "EngineSideEffect",
    "EngineStepResult",
    # ABC + Generic
    "TeachingEngine",
    # TypeVar
    "EngineStateT",
]

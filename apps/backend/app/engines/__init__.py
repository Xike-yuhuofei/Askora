"""
Askora 教学引擎运行时 (Teaching Engine Runtime)
统一管理 TEI 接口实现的所有教学引擎，暴露注册表与 Orchestrator

设计目标：
- 所有教学引擎（Socratic / Explain / Quiz / Drill ...）统一实现 TeachingEngine ABC
- 通过 ENGINE_REGISTRY 按 engine_id 动态发现与实例化
- LearningFlowOrchestrator 是运行时入口：负责跨引擎调度 + SharedContext 传递

注意：ENGINE_REGISTRY 和 register_engine / list_registered_engines 实现在 `_registry.py`
（独立叶子模块，不依赖 base / orchestrator，避免 __init__ → orchestrator → registry 循环 import）。
注册顺序刻意安排：base → _registry → 各引擎（触发 @register_engine 副作用）→ orchestrator → 对外重导出。
这样保证 orchestrator 首次被引用时 ENGINE_REGISTRY 已填充完整。
"""

from __future__ import annotations

from app.engines import drill_engine as _drill_engine_module  # noqa: E402,F401
from app.engines import explain_engine as _explain_engine_module  # noqa: E402,F401
from app.engines import inquiry_engine as _inquiry_engine_module  # noqa: E402,F401
from app.engines import quiz_engine as _quiz_engine_module  # noqa: E402,F401

# 3. 触发全部具体引擎的 @register_engine 装饰器（import side effect 刻意保留）
#    必须在 orchestrator 之前完成，确保注册表完整。
from app.engines import socratic_adapter as _socratic_adapter_module  # noqa: E402,F401

# 1. 先暴露注册表（叶子模块，只依赖 stdlib）
from app.engines._registry import (  # noqa: E402
    ENGINE_REGISTRY,
    list_registered_engines,
    register_engine,
)

# 2. 再导入 TEI 基类与共享数据结构
from app.engines.base import (  # noqa: E402
    CognitiveLevel,
    EngineSideEffect,
    EngineStepResult,
    FlowStage,
    KnowledgeGap,
    LearnerTurn,
    ProducedAsset,
    SharedContext,
    TaskOpenness,
    TeachingEngine,
    TransitionRecord,
    TransitionSuggestion,
    TransitionType,
)

# 4. 编排器（依赖已就绪的注册表）
from app.engines.orchestrator import (  # noqa: E402
    LearningFlowOrchestrator,
    OrchestratorTurnResult,
    get_orchestrator,
)

# 5. 状态图引擎（可选，独立于编排器）
from app.engines.state_graph import (  # noqa: E402
    StateGraph,
    StateGraphEngine,
    StateNode,
    Transition,
    TransitionDecision,
    create_state_graph_engine,
)

__all__ = [
    # TEI 接口基类 & 枚举
    "TeachingEngine",
    "SharedContext",
    "EngineStepResult",
    "EngineSideEffect",
    "TransitionSuggestion",
    "TransitionType",
    "FlowStage",
    "CognitiveLevel",
    "TaskOpenness",
    # 共享上下文数据结构
    "LearnerTurn",
    "KnowledgeGap",
    "ProducedAsset",
    "TransitionRecord",
    # Orchestrator
    "LearningFlowOrchestrator",
    "OrchestratorTurnResult",
    "get_orchestrator",
    # 注册表
    "ENGINE_REGISTRY",
    "register_engine",
    "list_registered_engines",
    # StateGraph 状态机
    "StateGraph",
    "StateGraphEngine",
    "StateNode",
    "Transition",
    "TransitionDecision",
    "create_state_graph_engine",
]

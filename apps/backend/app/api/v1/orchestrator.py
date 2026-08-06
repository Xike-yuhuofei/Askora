"""
Orchestrator 调试端点（仅在非生产环境启用）。

提供用于跑通 TEI v1 编排链路的最小 API：
1. POST /api/v1/orchestrator/sessions —— 创建新会话（可指定 subject/kp/learner_persona/初始引擎）
2. POST /api/v1/orchestrator/sessions/{session_id}/turns —— 跑一轮学习交互（Socratic ↔ Explain 可互切）
3. GET  /api/v1/orchestrator/engines —— 列出已注册引擎元信息（方便验证注册行为）
4. GET  /api/v1/orchestrator/sessions/{session_id} —— 查看会话的 SharedContext 最新快照

注意：这是 debug/demo 端点，不经过 PEP 网关鉴权，仅在非生产环境可用。
生产环境应通过 dialog_service 内部重构接入 Orchestrator。
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logging import get_logger
from app.engines import (
    ENGINE_REGISTRY,
    FlowStage,
    get_orchestrator,
    list_registered_engines,
)
from app.engines.base import LearnerTurn
from app.engines.orchestrator import OrchestratorTurnResult, shared_ctx_to_jsonable

logger = get_logger(__name__)

router = APIRouter(
    prefix="/orchestrator",
    tags=["Orchestrator TEI v1 (调试)"],
)


# ================== Pydantic 请求 / 响应模型 ==================


class CreateSessionRequest(BaseModel):
    session_id: str = Field(..., description="会话唯一 ID（调用方自行生成，推荐 uuid4）")
    subject: str = Field(default="general", description="学科，例如 math/physics/chinese/python")
    knowledge_point_id: Optional[str] = Field(default=None, description="初始知识点 ID（可选）")
    initial_stage: Optional[str] = Field(
        default="learn",
        description="初始流程阶段，可选 diagnose/learn/inquire/validate/drill/produce",
    )
    learner_persona: Optional[str] = Field(
        default="",
        description="人群画像（不做架构分支，只改权重），例如 k12_primary / higher_ed / professional / senior",
    )
    learner_preferences: dict[str, str] = Field(default_factory=dict)
    initial_engine_id: Optional[str] = Field(
        default=None,
        description="可选：强制起始引擎（socratic/explain/...），留空则自动选最优",
    )
    extras: dict[str, Any] = Field(default_factory=dict, description="业务自定义扩展字段")


class CreateSessionResponse(BaseModel):
    ok: bool
    session_id: str
    initial_engine_id: str
    current_flow_stage: str
    registered_engines_count: int
    learner_persona: str
    shared_ctx_snapshot: dict[str, Any]


class RunTurnRequest(BaseModel):
    text: str = Field(..., description="学习者本轮输入文本")
    turn_id: Optional[str] = Field(default="", description="调用方可传入的回合 ID，原样返回")
    attachments: list[dict[str, str]] = Field(default_factory=list)
    forced_stage: Optional[str] = Field(default=None, description="可选：强制设定当前流程阶段")
    forced_engine: Optional[str] = Field(
        default=None, description="可选：强制切换到指定引擎（前端按钮/调试用）"
    )


class RunTurnResponse(BaseModel):
    ok: bool
    session_id: str
    reply_text: str
    engine_id: str
    switched_to: Optional[str]
    flow_stage: str
    decision_trace: list[str]
    shared_ctx_snapshot: dict[str, Any]
    engine_debug: dict[str, Any]


class ListEnginesResponse(BaseModel):
    ok: bool
    engines: list[dict[str, Any]]
    count: int


# ================== 路由实现 ==================


@router.get("/engines", response_model=ListEnginesResponse)
async def list_engines() -> ListEnginesResponse:
    """列出所有已注册到 ENGINE_REGISTRY 的教学引擎（便于验证注册链路是否正常）"""
    engines = list_registered_engines()
    return ListEnginesResponse(ok=True, engines=engines, count=len(engines))


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_orchestrator_session(
    req: CreateSessionRequest,
) -> CreateSessionResponse:
    """创建一个 Orchestrator 会话（自动选择最优初始引擎）"""
    try:
        stage = FlowStage(req.initial_stage) if req.initial_stage else FlowStage.LEARN
    except ValueError:
        raise HTTPException(  # noqa: B008
            status_code=400,
            detail={
                "code": "ORCH-0001",
                "message": f"invalid initial_stage={req.initial_stage!r}",
                "allowed": [s.value for s in FlowStage],
            },
        )

    if req.initial_engine_id and req.initial_engine_id not in ENGINE_REGISTRY:
        raise HTTPException(  # noqa: B008
            status_code=400,
            detail={
                "code": "ORCH-0002",
                "message": (
                    f"initial_engine_id {req.initial_engine_id!r} not registered. "
                    f"registered engines: {sorted(ENGINE_REGISTRY.keys())}"
                ),
            },
        )

    orch = get_orchestrator()
    try:
        shared = await orch.create_session(
            session_id=req.session_id,
            subject=req.subject,
            knowledge_point_id=req.knowledge_point_id,
            initial_stage=stage,
            learner_persona=req.learner_persona or "",
            learner_preferences=req.learner_preferences,
            initial_engine_id=req.initial_engine_id,
            extras={
                **req.extras,
                "endpoint_created_via": "orchestrator_debug_api",
            },
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail={"code": "ORCH-0003", "message": str(exc)}
        )  # noqa: B008

    return CreateSessionResponse(
        ok=True,
        session_id=req.session_id,
        initial_engine_id=shared.current_engine_id or "(none)",
        current_flow_stage=shared.current_flow_stage.value,
        registered_engines_count=len(ENGINE_REGISTRY),
        learner_persona=shared.learner_persona or "neutral",
        shared_ctx_snapshot=shared_ctx_to_jsonable(shared),
    )


@router.post("/sessions/{session_id}/turns", response_model=RunTurnResponse)
async def run_orchestrator_turn(
    session_id: str,
    req: RunTurnRequest,
) -> RunTurnResponse:
    """跑一轮学习交互：Orchestrator → 当前引擎.step() → 按引擎切换建议执行切换"""
    if not req.text.strip():
        raise HTTPException(  # noqa: B008
            status_code=400,
            detail={"code": "ORCH-0010", "message": "text must not be empty"},
        )

    orch = get_orchestrator()
    forced_stage: Optional[FlowStage] = None
    if req.forced_stage:
        try:
            forced_stage = FlowStage(req.forced_stage)
        except ValueError:
            raise HTTPException(  # noqa: B008
                status_code=400,
                detail={
                    "code": "ORCH-0011",
                    "message": f"invalid forced_stage={req.forced_stage!r}",
                    "allowed": [s.value for s in FlowStage],
                },
            )

    if req.forced_engine and req.forced_engine not in ENGINE_REGISTRY:
        raise HTTPException(  # noqa: B008
            status_code=400,
            detail={
                "code": "ORCH-0012",
                "message": (
                    f"forced_engine {req.forced_engine!r} not registered. "
                    f"registered engines: {sorted(ENGINE_REGISTRY.keys())}"
                ),
            },
        )

    learner_turn = LearnerTurn(
        text=req.text.strip(),
        turn_id=req.turn_id or "",
        attachments=req.attachments,
    )
    try:
        result: OrchestratorTurnResult = await orch.run_turn(
            session_id=session_id,
            learner_turn=learner_turn,
            forced_stage=forced_stage,
            forced_engine=req.forced_engine,
        )
    except KeyError as exc:
        raise HTTPException(  # noqa: B008
            status_code=404,
            detail={
                "code": "ORCH-0020",
                "message": str(exc),
                "hint": "Call POST /orchestrator/sessions before running turns.",
            },
        )

    return RunTurnResponse(
        ok=True,
        session_id=session_id,
        reply_text=result.reply_text,
        engine_id=result.engine_id,
        switched_to=result.switched_to,
        flow_stage=result.flow_stage.value,
        decision_trace=result.decision_trace,
        shared_ctx_snapshot=result.shared_ctx_snapshot,
        engine_debug=result.engine_debug,
    )


@router.get("/sessions/{session_id}")
async def get_orchestrator_session(
    session_id: str,
    include_trace: bool = Query(default=True, description="是否返回完整 engine_trace"),
):
    """查看 Orchestrator 会话最新快照（用于 debug 编排是否按预期工作）"""
    orch = get_orchestrator()
    # MVP 只能直接访问内部 _sessions（未来改为 Redis/DB 持久化后走 repository）
    sessions = getattr(orch, "_sessions", None)
    if sessions is None or session_id not in sessions:
        raise HTTPException(  # noqa: B008
            status_code=404,
            detail={
                "code": "ORCH-0030",
                "message": f"session_id {session_id!r} not found",
            },
        )
    shared, _engine_states = sessions[session_id]
    data = shared_ctx_to_jsonable(shared)
    if not include_trace:
        data["engine_trace"] = {"count": len(data.get("engine_trace", []))}
    return {
        "ok": True,
        "session_id": session_id,
        "shared_ctx": data,
        "engine_states_count": len(_engine_states),
        "engine_state_ids": sorted(_engine_states.keys()),
    }


# 仅在非生产环境挂到主路由（main.py 里会用 is_production 再次过滤）
# 这里先不直接暴露，交给 main.py include_router 时控制
if settings.is_production:
    # 生产环境：只保留 list_engines 的只读元信息端点，其他调试端点下线
    # 为了「尽量少改」，我们直接通过把 router.routes 清空并重新只保留 /engines 的方式
    # 但 FastAPI 的 include_router 调用发生在 main.py，所以这里只打日志提醒；
    # 真正的开关在 main.py 里 include_router 时判断 settings.is_production
    logger.info("orchestrator_debug_api_loaded_in_production_will_be_disabled_by_main")


__all__ = ["router"]

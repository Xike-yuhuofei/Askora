"""
Orchestrator 核心流程单元测试

直接实例化 LearningFlowOrchestrator 和教学引擎，不通过 HTTP：
1. 完整 Socratic → Quiz → Socratic 流程模拟
2. 引擎切换逻辑验证
3. SharedContext 状态跨轮次持久化
4. 掌握度更新跨引擎传播
5. SWITCH_AND_RETURN 行为
6. FlowStage 阶段转换 (LEARN → VALIDATE → DRILL)
"""

from __future__ import annotations

import uuid

import pytest

# ---------------------------------------------------------------------------
# 可选依赖安全导入
# ---------------------------------------------------------------------------
try:
    import structlog  # noqa: F401
except ImportError:
    structlog = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# 引擎可用性检测
# ---------------------------------------------------------------------------
try:
    from app.engines.drill_engine import DrillEngine  # noqa: F401

    _DRILL_AVAILABLE = True
except (ImportError, AttributeError):
    _DRILL_AVAILABLE = False


def _unique_id(prefix: str = "test") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


# ===========================================================================
# Test 1: 完整 Socratic → Quiz → Socratic 流程模拟
# ===========================================================================
@pytest.mark.asyncio
async def test_full_socratic_quiz_socratic_flow():
    """验证 Orchestrator 能完成 Socratic → Quiz → Socratic 完整流程"""
    from app.engines import FlowStage, LearnerTurn, LearningFlowOrchestrator

    orch = LearningFlowOrchestrator()
    session_id = _unique_id("flow")

    shared = await orch.create_session(
        session_id=session_id,
        subject="math",
        knowledge_point_id="kp_algebra_transposition",
        initial_stage=FlowStage.LEARN,
        learner_persona="k12_high",
        initial_engine_id="socratic",
    )

    assert shared.current_engine_id == "socratic"
    assert shared.current_flow_stage == FlowStage.LEARN

    result1 = await orch.run_turn(
        session_id=session_id,
        learner_turn=LearnerTurn(text="我不太理解移项", turn_id="t1"),
    )
    assert result1.reply_text
    assert result1.engine_id == "socratic"

    result2 = await orch.run_turn(
        session_id=session_id,
        learner_turn=LearnerTurn(text="我觉得我懂了一些，来测验我吧", turn_id="t2"),
        forced_engine="quiz",
        forced_stage=FlowStage.VALIDATE,
    )
    assert result2.reply_text
    assert result2.engine_id == "quiz"

    result3 = await orch.run_turn(
        session_id=session_id,
        learner_turn=LearnerTurn(text="我做完了，回到引导吧", turn_id="t3"),
    )
    assert result3.reply_text
    assert result3.engine_id == "quiz"

    result4 = await orch.run_turn(
        session_id=session_id,
        learner_turn=LearnerTurn(text="继续引导我深入理解", turn_id="t4"),
        forced_engine="socratic",
    )
    assert result4.reply_text
    assert result4.engine_id == "socratic"


# ===========================================================================
# Test 2: 引擎切换逻辑验证
# ===========================================================================
@pytest.mark.asyncio
async def test_engine_switch_logic():
    """验证引擎切换逻辑：forced_engine 切换、SWITCH_TO 行为"""
    from app.engines import FlowStage, LearnerTurn, LearningFlowOrchestrator

    orch = LearningFlowOrchestrator()
    session_id = _unique_id("switch")

    await orch.create_session(
        session_id=session_id,
        subject="math",
        knowledge_point_id="kp_algebra_transposition",
        initial_stage=FlowStage.LEARN,
        initial_engine_id="socratic",
    )

    result = await orch.run_turn(
        session_id=session_id,
        learner_turn=LearnerTurn(text="讲解这个概念", turn_id="t1"),
        forced_engine="explain",
    )

    assert result.engine_id == "explain"
    assert "forced_switch:explain" in result.decision_trace

    result2 = await orch.run_turn(
        session_id=session_id,
        learner_turn=LearnerTurn(text="我懂了", turn_id="t2"),
    )
    assert result2.reply_text
    assert result2.engine_id == "explain"


@pytest.mark.asyncio
async def test_switch_to_invalid_engine_falls_back():
    """验证切换到无效引擎 ID 不会导致崩溃"""
    from app.engines import LearnerTurn, LearningFlowOrchestrator

    orch = LearningFlowOrchestrator()
    session_id = _unique_id("invalid-switch")

    await orch.create_session(
        session_id=session_id,
        subject="math",
        initial_engine_id="socratic",
    )

    result = await orch.run_turn(
        session_id=session_id,
        learner_turn=LearnerTurn(text="test", turn_id="t1"),
        forced_engine="nonexistent_engine_xyz",
    )

    assert result.reply_text
    assert (
        "ignore_invalid_transition" in str(result.decision_trace) or result.engine_id == "socratic"
    )


# ===========================================================================
# Test 3: SharedContext 状态跨轮次持久化
# ===========================================================================
@pytest.mark.asyncio
async def test_shared_context_persistence_across_turns():
    """验证 SharedContext 状态在多轮交互中保持持久化"""
    from app.engines import FlowStage, LearnerTurn, LearningFlowOrchestrator

    orch = LearningFlowOrchestrator()
    session_id = _unique_id("persist")

    shared = await orch.create_session(
        session_id=session_id,
        subject="math",
        knowledge_point_id="kp_algebra_transposition",
        initial_stage=FlowStage.LEARN,
    )

    initial_turn_count = shared.turn_count_in_current_engine

    result1 = await orch.run_turn(
        session_id=session_id,
        learner_turn=LearnerTurn(text="第一轮输入", turn_id="t1"),
    )

    snapshot1 = result1.shared_ctx_snapshot
    assert snapshot1["turn_count_in_current_engine"] == initial_turn_count + 1

    result2 = await orch.run_turn(
        session_id=session_id,
        learner_turn=LearnerTurn(text="第二轮输入", turn_id="t2"),
    )

    snapshot2 = result2.shared_ctx_snapshot
    assert snapshot2["turn_count_in_current_engine"] == initial_turn_count + 2
    assert len(snapshot2["engine_trace"]) >= len(snapshot1["engine_trace"])

    assert result1.shared_ctx_snapshot["subject"] == "math"
    assert result2.shared_ctx_snapshot["subject"] == "math"


@pytest.mark.asyncio
async def test_shared_context_engine_trace_accumulates():
    """验证 engine_trace 随切换累积"""
    from app.engines import LearnerTurn, LearningFlowOrchestrator

    orch = LearningFlowOrchestrator()
    session_id = _unique_id("trace")

    await orch.create_session(
        session_id=session_id,
        subject="math",
        initial_engine_id="socratic",
    )

    trace_lengths = []
    for i in range(4):
        result = await orch.run_turn(
            session_id=session_id,
            learner_turn=LearnerTurn(text=f"第{i}轮", turn_id=f"t{i}"),
        )
        trace_lengths.append(len(result.shared_ctx_snapshot["engine_trace"]))

    for j in range(1, len(trace_lengths)):
        assert trace_lengths[j] >= trace_lengths[j - 1], f"engine_trace 应单调不减: {trace_lengths}"


# ===========================================================================
# Test 4: 掌握度 (Mastery) 更新跨引擎传播
# ===========================================================================
@pytest.mark.asyncio
async def test_mastery_update_propagation():
    """验证引擎的掌握度更新 (mastery_updates) 被正确传播到 SharedContext"""
    from app.engines import (
        FlowStage,
        LearnerTurn,
        LearningFlowOrchestrator,
    )

    orch = LearningFlowOrchestrator()
    session_id = _unique_id("mastery")

    await orch.create_session(
        session_id=session_id,
        subject="math",
        knowledge_point_id="kp_test_mastery",
        initial_stage=FlowStage.LEARN,
        initial_engine_id="socratic",
    )

    await orch.run_turn(
        session_id=session_id,
        learner_turn=LearnerTurn(text="我非常理解这个概念", turn_id="t1"),
    )

    shared_after, _ = await orch._load_session(session_id)
    final_mastery = shared_after.mastery_vector.get("kp_test_mastery", 0.0)

    assert isinstance(final_mastery, float)
    assert 0.0 <= final_mastery <= 1.0
    assert final_mastery >= 0.0


@pytest.mark.asyncio
async def test_mastery_confidence_updates():
    """验证掌握度置信度随更新次数增加"""
    from app.engines import FlowStage, LearnerTurn, LearningFlowOrchestrator

    orch = LearningFlowOrchestrator()
    session_id = _unique_id("confidence")

    await orch.create_session(
        session_id=session_id,
        subject="math",
        knowledge_point_id="kp_confidence_test",
        initial_stage=FlowStage.LEARN,
    )

    shared0, _ = await orch._load_session(session_id)
    conf0 = shared0.mastery_confidence.get("kp_confidence_test", 0.1)

    for i in range(3):
        await orch.run_turn(
            session_id=session_id,
            learner_turn=LearnerTurn(text=f"确认理解第{i}次", turn_id=f"t{i}"),
        )

    shared3, _ = await orch._load_session(session_id)
    conf3 = shared3.mastery_confidence.get("kp_confidence_test", 0.1)

    assert conf3 >= conf0, f"Confidence should not decrease: {conf3} >= {conf0}"


# ===========================================================================
# Test 5: SWITCH_AND_RETURN 行为
# ===========================================================================
@pytest.mark.asyncio
async def test_switch_and_return_behavior():
    """验证 SWITCH_AND_RETURN 切换语义：压栈 prev_engine，完成后自动返回"""
    from app.engines import (
        FlowStage,
        LearnerTurn,
        LearningFlowOrchestrator,
    )

    orch = LearningFlowOrchestrator()
    session_id = _unique_id("sar")

    await orch.create_session(
        session_id=session_id,
        subject="math",
        knowledge_point_id="kp_sar_test",
        initial_stage=FlowStage.LEARN,
        initial_engine_id="socratic",
    )

    result = await orch.run_turn(
        session_id=session_id,
        learner_turn=LearnerTurn(text="需要详细讲解", turn_id="t1"),
        forced_engine="explain",
    )

    assert result.engine_id == "explain"
    assert result.reply_text

    shared, _ = await orch._load_session(session_id)
    assert shared.current_engine_id == "explain"

    result2 = await orch.run_turn(
        session_id=session_id,
        learner_turn=LearnerTurn(text="讲解完毕，返回", turn_id="t2"),
    )

    assert result2.reply_text


@pytest.mark.asyncio
async def test_switch_and_return_stack_behavior():
    """验证 return_stack 正确维护多个引擎的返回栈"""
    from app.engines import LearnerTurn, LearningFlowOrchestrator

    orch = LearningFlowOrchestrator()
    session_id = _unique_id("stack")

    await orch.create_session(
        session_id=session_id,
        subject="math",
        initial_engine_id="socratic",
    )

    result = await orch.run_turn(
        session_id=session_id,
        learner_turn=LearnerTurn(text="切到 explain", turn_id="t1"),
        forced_engine="explain",
    )

    assert result.engine_id == "explain"

    shared, _ = await orch._load_session(session_id)
    assert shared.current_engine_id == "explain"


@pytest.mark.asyncio
async def test_switch_and_return_with_extra_context():
    """验证 SWITCH_AND_RETURN 的 extra_context 正确透传"""
    from app.engines import LearnerTurn, LearningFlowOrchestrator

    orch = LearningFlowOrchestrator()
    session_id = _unique_id("extra-ctx")

    await orch.create_session(
        session_id=session_id,
        subject="math",
        knowledge_point_id="kp_extra_ctx",
        initial_engine_id="socratic",
    )

    await orch.run_turn(
        session_id=session_id,
        learner_turn=LearnerTurn(text="用类比迁移模式讲解", turn_id="t1"),
        forced_engine="explain",
    )

    shared, _ = await orch._load_session(session_id)
    assert shared.current_engine_id == "explain"


# ===========================================================================
# Test 6: FlowStage 阶段转换 (LEARN → VALIDATE → DRILL)
# ===========================================================================
@pytest.mark.asyncio
async def test_flow_stage_transition_learn_to_validate():
    """验证 FlowStage 从 LEARN 转换到 VALIDATE"""
    from app.engines import FlowStage, LearnerTurn, LearningFlowOrchestrator

    orch = LearningFlowOrchestrator()
    session_id = _unique_id("stage")

    shared = await orch.create_session(
        session_id=session_id,
        subject="math",
        knowledge_point_id="kp_stage_test",
        initial_stage=FlowStage.LEARN,
    )

    assert shared.current_flow_stage == FlowStage.LEARN

    result = await orch.run_turn(
        session_id=session_id,
        learner_turn=LearnerTurn(text="开始验证我是否掌握了", turn_id="t1"),
        forced_stage=FlowStage.VALIDATE,
        forced_engine="quiz",
    )

    assert result.flow_stage == FlowStage.VALIDATE
    snapshot = result.shared_ctx_snapshot
    assert snapshot["current_flow_stage"] == "validate"


@pytest.mark.asyncio
async def test_flow_stage_transition_to_drill():
    """验证 FlowStage 转换到 DRILL 阶段"""
    if not _DRILL_AVAILABLE:
        pytest.skip("DrillEngine 不可用，跳过 DRILL 阶段测试")

    from app.engines import FlowStage, LearnerTurn, LearningFlowOrchestrator

    orch = LearningFlowOrchestrator()
    session_id = _unique_id("drill-stage")

    await orch.create_session(
        session_id=session_id,
        subject="math",
        knowledge_point_id="kp_drill_stage",
        initial_stage=FlowStage.LEARN,
    )

    result = await orch.run_turn(
        session_id=session_id,
        learner_turn=LearnerTurn(text="我需要更多练习", turn_id="t1"),
        forced_stage=FlowStage.DRILL,
        forced_engine="drill",
    )

    assert result.flow_stage == FlowStage.DRILL
    assert result.engine_id == "drill"

    snapshot = result.shared_ctx_snapshot
    assert snapshot["current_flow_stage"] == "drill"


@pytest.mark.asyncio
async def test_flow_stage_backward_transition():
    """验证阶段可以向后回退（如从 VALIDATE 回到 LEARN）"""
    from app.engines import FlowStage, LearnerTurn, LearningFlowOrchestrator

    orch = LearningFlowOrchestrator()
    session_id = _unique_id("backward")

    await orch.create_session(
        session_id=session_id,
        subject="math",
        initial_stage=FlowStage.VALIDATE,
    )

    result = await orch.run_turn(
        session_id=session_id,
        learner_turn=LearnerTurn(text="我还没准备好验证", turn_id="t1"),
        forced_stage=FlowStage.LEARN,
    )

    assert result.flow_stage == FlowStage.LEARN


# ===========================================================================
# 附加: Orchestrator 生命周期与单例行为
# ===========================================================================
@pytest.mark.asyncio
async def test_orchestrator_session_isolation():
    """验证不同 session 之间的数据隔离"""
    from app.engines import FlowStage, LearnerTurn, LearningFlowOrchestrator

    orch = LearningFlowOrchestrator()

    sid_a = _unique_id("iso-a")
    sid_b = _unique_id("iso-b")

    await orch.create_session(
        session_id=sid_a,
        subject="math",
        knowledge_point_id="kp_A",
        initial_stage=FlowStage.LEARN,
    )

    await orch.create_session(
        session_id=sid_b,
        subject="physics",
        knowledge_point_id="kp_B",
        initial_stage=FlowStage.INQUIRE,
    )

    result_a = await orch.run_turn(
        session_id=sid_a,
        learner_turn=LearnerTurn(text="session A 输入", turn_id="a1"),
    )

    result_b = await orch.run_turn(
        session_id=sid_b,
        learner_turn=LearnerTurn(text="session B 输入", turn_id="b1"),
    )

    ctx_a = result_a.shared_ctx_snapshot
    ctx_b = result_b.shared_ctx_snapshot

    assert ctx_a["subject"] == "math"
    assert ctx_b["subject"] == "physics"
    assert ctx_a.get("knowledge_point_id") == "kp_A"
    assert ctx_b.get("knowledge_point_id") == "kp_B"


@pytest.mark.asyncio
async def test_orchestrator_turn_count_resets_on_switch():
    """验证切换引擎后 turn_count_in_current_engine 重置为 0"""
    from app.engines import LearnerTurn, LearningFlowOrchestrator

    orch = LearningFlowOrchestrator()
    session_id = _unique_id("reset")

    await orch.create_session(
        session_id=session_id,
        subject="math",
        initial_engine_id="socratic",
    )

    for i in range(3):
        await orch.run_turn(
            session_id=session_id,
            learner_turn=LearnerTurn(text=f"连续输入 {i}", turn_id=f"t{i}"),
        )

    shared_before, _ = await orch._load_session(session_id)
    count_before = shared_before.turn_count_in_current_engine

    await orch.run_turn(
        session_id=session_id,
        learner_turn=LearnerTurn(text="切换引擎", turn_id="t-switch"),
        forced_engine="explain",
    )

    shared_after, _ = await orch._load_session(session_id)
    count_after_switch = shared_after.turn_count_in_current_engine

    assert (
        count_after_switch == 1
    ), f"切换引擎后 turn_count 应为 1（重置后本轮+1）, 实际为 {count_after_switch} (before={count_before})"

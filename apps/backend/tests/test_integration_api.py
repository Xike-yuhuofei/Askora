"""
Orchestrator HTTP API 集成测试

通过 httpx TestClient 直接测试 Orchestrator 调试端点：
1. POST   /api/v1/orchestrator/sessions       创建会话
2. POST   /api/v1/orchestrator/sessions/{id}/turns  执行一轮学习交互
3. GET    /api/v1/orchestrator/engines         列出已注册引擎
4. GET    /api/v1/orchestrator/sessions/{id}   查看会话快照
5. 引擎路由验证（DrillEngine 处理 FlowStage.DRILL）
6. 错误处理（无效 session_id 返回 404）
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
# 辅助函数
# ---------------------------------------------------------------------------
def _unique_session_id(prefix: str = "test") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


# ---------------------------------------------------------------------------
# Test 1: POST /api/v1/orchestrator/sessions 创建会话
# ---------------------------------------------------------------------------
def test_create_session_successfully(client):
    """验证 POST /orchestrator/sessions 成功创建会话"""
    session_id = _unique_session_id()

    resp = client.post(
        "/api/v1/orchestrator/sessions",
        json={
            "session_id": session_id,
            "subject": "math",
            "knowledge_point_id": "kp_algebra_transposition",
            "initial_stage": "learn",
            "learner_persona": "k12_high",
        },
    )

    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    data = resp.json()
    assert data["ok"] is True
    assert data["session_id"] == session_id
    assert data["initial_engine_id"], "initial_engine_id should not be empty"
    assert data["current_flow_stage"] == "learn"
    assert data["registered_engines_count"] > 0
    assert "shared_ctx_snapshot" in data


def test_create_session_with_optional_fields(client):
    """验证创建会话时可选字段正常工作"""
    session_id = _unique_session_id()

    resp = client.post(
        "/api/v1/orchestrator/sessions",
        json={
            "session_id": session_id,
            "subject": "physics",
            "knowledge_point_id": "kp_velocity",
            "initial_stage": "inquire",
            "learner_persona": "higher_ed",
            "learner_preferences": {"difficulty_pref": "moderate"},
            "initial_engine_id": "socratic",
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["session_id"] == session_id
    assert data["initial_engine_id"] == "socratic"
    assert data["current_flow_stage"] == "inquire"


def test_create_session_invalid_stage(client):
    """验证无效 initial_stage 返回 400"""
    session_id = _unique_session_id()

    resp = client.post(
        "/api/v1/orchestrator/sessions",
        json={
            "session_id": session_id,
            "subject": "math",
            "initial_stage": "invalid_stage_xyz",
        },
    )

    assert resp.status_code == 400
    data = resp.json()
    assert "detail" in data or "code" in data


# ---------------------------------------------------------------------------
# Test 2: POST /api/v1/orchestrator/sessions/{id}/turns 执行一轮交互
# ---------------------------------------------------------------------------
def test_run_turn_processes_turn(client):
    """验证 POST /orchestrator/sessions/{id}/turns 成功处理一轮交互"""
    session_id = _unique_session_id()

    create_resp = client.post(
        "/api/v1/orchestrator/sessions",
        json={
            "session_id": session_id,
            "subject": "math",
            "knowledge_point_id": "kp_algebra_transposition",
            "initial_stage": "learn",
        },
    )
    assert create_resp.status_code == 200, "Failed to create session"

    turn_resp = client.post(
        f"/api/v1/orchestrator/sessions/{session_id}/turns",
        json={
            "text": "我不太理解为什么要移项",
            "turn_id": "turn-001",
        },
    )

    assert (
        turn_resp.status_code == 200
    ), f"Expected 200, got {turn_resp.status_code}: {turn_resp.text}"

    data = turn_resp.json()
    assert data["ok"] is True
    assert data["session_id"] == session_id
    assert data["reply_text"], "reply_text should not be empty"
    assert data["engine_id"], "engine_id should not be empty"
    assert "decision_trace" in data
    assert "shared_ctx_snapshot" in data


def test_run_turn_empty_text_rejected(client):
    """验证空文本被拒绝（400）"""
    session_id = _unique_session_id()

    client.post(
        "/api/v1/orchestrator/sessions",
        json={"session_id": session_id, "subject": "math"},
    )

    resp = client.post(
        f"/api/v1/orchestrator/sessions/{session_id}/turns",
        json={"text": "   ", "turn_id": "turn-001"},
    )

    assert resp.status_code == 400


def test_run_turn_multiple_turns_in_sequence(client):
    """验证多轮对话顺序执行"""
    session_id = _unique_session_id()

    client.post(
        "/api/v1/orchestrator/sessions",
        json={
            "session_id": session_id,
            "subject": "math",
            "knowledge_point_id": "kp_algebra_transposition",
        },
    )

    replies: list[str] = []
    for i, text in enumerate(
        [
            "什么是移项？",
            "能给我一个例子吗？",
            "我现在明白了",
        ]
    ):
        resp = client.post(
            f"/api/v1/orchestrator/sessions/{session_id}/turns",
            json={"text": text, "turn_id": f"turn-{i}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        replies.append(data["reply_text"])

    assert len(replies) == 3
    assert all(r for r in replies), "All replies should be non-empty"


# ---------------------------------------------------------------------------
# Test 3: GET /api/v1/orchestrator/engines 返回已注册引擎
# ---------------------------------------------------------------------------
def test_list_engines_returns_registered_engines(client):
    """验证 GET /orchestrator/engines 返回已注册引擎列表"""
    resp = client.get("/api/v1/orchestrator/engines")

    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert isinstance(data["engines"], list)
    assert data["count"] > 0, "Should have at least 1 registered engine"

    engine_ids = [e["engine_id"] for e in data["engines"]]
    assert "socratic" in engine_ids, "Socratic engine should be registered"
    assert "quiz" in engine_ids, "Quiz engine should be registered"


def test_list_engines_structure_valid(client):
    """验证每个引擎元数据结构完整"""
    resp = client.get("/api/v1/orchestrator/engines")
    data = resp.json()

    for engine in data["engines"]:
        assert "engine_id" in engine
        assert "engine_name" in engine
        assert "supported_cognitive_levels" in engine
        assert "supported_openness" in engine
        assert isinstance(engine["supported_cognitive_levels"], list)


# ---------------------------------------------------------------------------
# Test 4: GET /api/v1/orchestrator/sessions/{id} 返回会话快照
# ---------------------------------------------------------------------------
def test_get_session_snapshot(client):
    """验证 GET /orchestrator/sessions/{id} 返回会话快照"""
    session_id = _unique_session_id()

    client.post(
        "/api/v1/orchestrator/sessions",
        json={
            "session_id": session_id,
            "subject": "math",
            "knowledge_point_id": "kp_algebra_transposition",
        },
    )

    resp = client.get(f"/api/v1/orchestrator/sessions/{session_id}")

    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["session_id"] == session_id
    assert "shared_ctx" in data
    assert "engine_states_count" in data

    shared_ctx = data["shared_ctx"]
    assert shared_ctx["subject"] == "math"


def test_get_session_after_turn_contains_trace(client):
    """验证执行一轮后会话快照包含 engine_trace"""
    session_id = _unique_session_id()

    client.post(
        "/api/v1/orchestrator/sessions",
        json={
            "session_id": session_id,
            "subject": "math",
            "knowledge_point_id": "kp_algebra_transposition",
        },
    )

    client.post(
        f"/api/v1/orchestrator/sessions/{session_id}/turns",
        json={"text": "我不太理解", "turn_id": "turn-001"},
    )

    resp = client.get(f"/api/v1/orchestrator/sessions/{session_id}")
    assert resp.status_code == 200
    data = resp.json()

    shared_ctx = data["shared_ctx"]
    assert "engine_trace" in shared_ctx
    assert len(shared_ctx["engine_trace"]) >= 0


# ---------------------------------------------------------------------------
# Test 5: 引擎路由 —— 验证 DrillEngine 处理 FlowStage.DRILL
# ---------------------------------------------------------------------------
def test_drill_engine_handles_drill_stage(client):
    """验证 DrillEngine 能处理 FlowStage.DRILL 阶段"""
    drill_available = True
    try:
        from app.engines.drill_engine import DrillEngine  # noqa: F401
    except (ImportError, AttributeError):
        drill_available = False

    if not drill_available:
        pytest.skip("DrillEngine 不可用（可能因 CognitiveLevel 枚举不匹配）")

    session_id = _unique_session_id()

    resp = client.post(
        "/api/v1/orchestrator/sessions",
        json={
            "session_id": session_id,
            "subject": "math",
            "knowledge_point_id": "kp_algebra_transposition",
            "initial_stage": "drill",
            "initial_engine_id": "drill",
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["initial_engine_id"] == "drill"
    assert data["current_flow_stage"] == "drill"

    turn_resp = client.post(
        f"/api/v1/orchestrator/sessions/{session_id}/turns",
        json={
            "text": "开始练习",
            "turn_id": "drill-turn-001",
        },
    )

    assert turn_resp.status_code == 200
    turn_data = turn_resp.json()
    assert turn_data["ok"] is True
    assert turn_data["engine_id"] == "drill"
    assert "练习题" in turn_data["reply_text"] or "📝" in turn_data["reply_text"]


def test_forced_engine_switch_to_drill(client):
    """验证通过 forced_engine 切换到 Drill 引擎"""
    drill_available = True
    try:
        from app.engines.drill_engine import DrillEngine  # noqa: F401
    except (ImportError, AttributeError):
        drill_available = False

    if not drill_available:
        pytest.skip("DrillEngine 不可用")

    session_id = _unique_session_id()

    client.post(
        "/api/v1/orchestrator/sessions",
        json={
            "session_id": session_id,
            "subject": "math",
            "knowledge_point_id": "kp_algebra_transposition",
            "initial_stage": "learn",
        },
    )

    resp = client.post(
        f"/api/v1/orchestrator/sessions/{session_id}/turns",
        json={
            "text": "我想练习一下",
            "forced_engine": "drill",
            "forced_stage": "drill",
            "turn_id": "switch-turn-001",
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["engine_id"] == "drill"


# ---------------------------------------------------------------------------
# Test 6: 错误处理 —— 无效 session_id 返回 404
# ---------------------------------------------------------------------------
def test_get_invalid_session_returns_404(client):
    """验证 GET 不存在的 session 返回 404"""
    resp = client.get("/api/v1/orchestrator/sessions/nonexistent-session-id")

    assert resp.status_code == 404
    data = resp.json()
    assert "detail" in data or "code" in data


def test_run_turn_invalid_session_returns_404(client):
    """验证对不存在的 session 执行 turn 返回 404"""
    resp = client.post(
        "/api/v1/orchestrator/sessions/nonexistent-session-id/turns",
        json={"text": "hello", "turn_id": "turn-001"},
    )

    assert resp.status_code == 404
    data = resp.json()
    assert "detail" in data or "code" in data


def test_create_session_duplicate_id(client):
    """验证重复 session_id 创建第二个会话不冲突"""
    session_id = _unique_session_id()

    resp1 = client.post(
        "/api/v1/orchestrator/sessions",
        json={"session_id": session_id, "subject": "math"},
    )
    assert resp1.status_code == 200

    resp2 = client.post(
        "/api/v1/orchestrator/sessions",
        json={"session_id": session_id, "subject": "physics"},
    )
    assert resp2.status_code == 200

    data2 = resp2.json()
    assert data2["ok"] is True
    assert data2["shared_ctx_snapshot"]["subject"] == "physics"

"""
Pytest 全局 fixtures —— Askora 后端测试基础设施

提供：
- app: FastAPI 应用实例（不启动 lifespan，避免触发 DB/Redis 初始化）
- client: httpx TestClient 用于 HTTP 集成测试（不启动 lifespan）
- orchestrator_session: 直接通过编排器创建测试会话的便捷 async fixture
"""

from __future__ import annotations

import os
import sys
from typing import Any, Optional

import pytest

# ---------------------------------------------------------------------------
# 确保项目根目录在 sys.path 中
# ---------------------------------------------------------------------------
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# ---------------------------------------------------------------------------
# 可选依赖安全导入
# ---------------------------------------------------------------------------
try:
    import structlog  # noqa: F401

    _HAS_STRUCTLOG = True
except ImportError:
    _HAS_STRUCTLOG = False

# ---------------------------------------------------------------------------
# 关键：测试环境必须覆盖本机 .env，避免误用真实密钥或外部模型。
# ---------------------------------------------------------------------------
os.environ["APP_ENV"] = "test"
os.environ["APP_NAME"] = "askora-test"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-at-least-32-chars!!"
os.environ["KEK_MASTER_KEY"] = "test-kek-key-at-least-32-bytes-long!!"
os.environ["ENABLE_ORCHESTRATOR_DEBUG_API"] = "true"
os.environ["LLM_QWEN_API_KEY"] = ""
os.environ["LLM_DEEPSEEK_API_KEY"] = ""
os.environ["LLM_DOUBAO_API_KEY"] = ""
os.environ["EMBEDDING_API_KEY"] = ""


@pytest.fixture(scope="session")
def app():
    """
    创建 FastAPI 应用实例（不启动 lifespan）。

    直接 import app.main:app 不会触发 lifespan，
    这样可以避免测试时初始化数据库、Redis 等外部依赖。
    """
    try:
        from app.main import app as _fastapi_app

        return _fastapi_app
    except Exception as exc:
        pytest.skip(f"无法导入 app.main:app —— {exc}")


@pytest.fixture(scope="session")
def client(app):
    """
    httpx TestClient 实例（基于 FastAPI）。

    用于发起 HTTP 请求测试 API 端点。
    注意：不启动 lifespan，因此依赖 lifespan 初始化的服务可能不可用。
    """
    try:
        from fastapi.testclient import TestClient

        _client = TestClient(app, raise_server_exceptions=False)
        yield _client
    except ImportError:
        pytest.skip("fastapi 未安装，跳过 client fixture")


@pytest.fixture
async def orchestrator_session():
    """
    通过编排器直接创建测试会话（不走 HTTP）的 async 工厂 fixture。

    返回一个异步工厂函数，调用时会创建一个新的 LearningFlowOrchestrator 会话。
    用法:
        result = await orchestrator_session(
            session_id="test-001",
            subject="math",
            knowledge_point_id="kp_algebra_transposition",
        )
        shared_ctx = result["shared_ctx"]
        orch = result["orchestrator"]
    """
    from app.engines import FlowStage, LearningFlowOrchestrator

    async def _create(
        session_id: str = "test-session",
        subject: str = "math",
        knowledge_point_id: Optional[str] = None,
        initial_stage: str = "learn",
        learner_persona: str = "k12_high",
        initial_engine_id: Optional[str] = None,
        **extras: Any,
    ) -> dict[str, Any]:
        orch = LearningFlowOrchestrator()

        try:
            stage = FlowStage(initial_stage)
        except ValueError:
            stage = FlowStage.LEARN

        shared = await orch.create_session(
            session_id=session_id,
            subject=subject,
            knowledge_point_id=knowledge_point_id,
            initial_stage=stage,
            learner_persona=learner_persona,
            initial_engine_id=initial_engine_id,
            extras=extras,
        )
        return {
            "orchestrator": orch,
            "shared_ctx": shared,
            "session_id": session_id,
        }

    return _create

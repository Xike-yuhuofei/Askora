"""
FastAPI 主应用入口
苏格拉底式教学 App 后端 - 个人版精简版

架构特点：
- 核心对话引擎（Socratic, Drill, Quiz, Inquiry, Explain）
- 本地知识库/RAG 支持
- 核心鉴权体系（简化版）
- 国产模型路由
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import (
    auth_router,
    dialog_router,
    documents_router,
    orchestrator_router,
    users_router,
    ws_router,
)
from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.exceptions import AppError
from app.core.logging import get_logger, setup_logging
from app.core.redis_client import close_redis, init_redis
from app.observability import setup_observability

# 初始化日志
setup_logging()
logger = get_logger(__name__)


def _check_runtime_config() -> None:
    """
    启动时检查关键系统运行配置
    """
    checks: list[str] = []

    # LLM API Key
    llm_keys = {
        "qwen": settings.llm_qwen_api_key,
        "deepseek": settings.llm_deepseek_api_key,
        "doubao": settings.llm_doubao_api_key,
    }
    if not any(llm_keys.values()):
        logger.warning(
            "config_llm_api_key_missing",
            detail="未配置任何 LLM API Key，对话回复将使用模拟响应",
        )
        checks.append("llm_api_key: MISSING")
    else:
        logger.info("config_llm_api_key_ok", providers=[k for k, v in llm_keys.items() if v])

    # 安全密钥
    if settings.jwt_secret_key == "change-me-in-production":
        logger.warning("config_jwt_secret_default", detail="JWT 密钥仍为默认值，请在生产环境替换")
        checks.append("jwt_secret: DEFAULT")

    if checks:
        logger.warning("runtime_config_warnings", issues=checks)
    else:
        logger.info("runtime_config_ok")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    logger.info(
        "app_starting",
        app_name=settings.app_name,
        version=settings.app_version,
        env=settings.app_env.value,
    )

    # 初始化数据库
    await init_db()
    logger.info("database_initialized")

    # 初始化 Redis
    try:
        await init_redis()
        logger.info("redis_initialized")
    except Exception as e:
        if settings.auto_create_tables:
            logger.info("redis_optional_unavailable", error_type=type(e).__name__)
        else:
            logger.error("redis_init_failed", error_type=type(e).__name__)
            raise

    # 初始化模型路由
    from app.services.llm.model_router import get_model_router

    get_model_router()
    logger.info("model_router_initialized")

    # 初始化文档服务组件
    try:
        from app.services.documents import get_tokenizer

        get_tokenizer()
        logger.info("document_services_initialized")
    except Exception as e:
        logger.warning("document_services_init_failed", error_type=type(e).__name__)

    # 系统运行配置健康检查
    _check_runtime_config()

    logger.info("app_started", app_name=settings.app_name)

    yield

    # 关闭
    logger.info("app_shutting_down")

    # 关闭 WebSocket 连接
    try:
        from app.services.websocket import get_ws_manager

        await get_ws_manager().close_all()
        logger.info("websocket_connections_closed")
    except Exception as e:
        logger.warning("websocket_close_failed", error_type=type(e).__name__)

    # 关闭数据库
    from app.api.v1.documents import drain_document_tasks

    await drain_document_tasks()
    logger.info("document_tasks_drained")

    # 关闭数据库
    await close_db()
    logger.info("database_closed")

    # 关闭 Redis
    await close_redis()
    logger.info("redis_closed")

    # 关闭模型路由
    from app.services.llm.model_router import get_model_router

    await get_model_router().close()
    logger.info("model_router_closed")

    logger.info("app_shutdown_complete")


# 创建 FastAPI 应用
app = FastAPI(
    title="苏格拉底式教学 App 后端 API",
    description="个人版 - 精简苏格拉底式对话学习引擎",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.auto_create_tables else None,
    redoc_url="/redoc" if settings.auto_create_tables else None,
    openapi_url="/openapi.json" if settings.auto_create_tables else None,
)

# ========== 中间件 ==========

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 可观测性
setup_observability(app)


# ========== 全局异常处理 ==========


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    """统一应用异常处理"""
    request_id = getattr(request.state, "request_id", "unknown")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "request_id": request_id,
                "details": (
                    exc.error_detail if hasattr(exc, "error_detail") and exc.error_detail else None
                ),
            }
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局未捕获异常处理"""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        "unhandled_exception",
        error_type=type(exc).__name__,
        request_id=request_id,
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "SYS-0001",
                "message": "服务器内部错误",
                "request_id": request_id,
            }
        },
    )


# ========== 健康检查 ==========


@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查端点"""
    return {
        "status": "alive",
        "app": settings.app_name,
        "version": settings.app_version,
        "env": settings.app_env.value,
    }


@app.get("/health/config", tags=["系统"])
async def config_health_check():
    """系统运行配置状态"""
    llm_configured = bool(
        settings.llm_qwen_api_key or settings.llm_deepseek_api_key or settings.llm_doubao_api_key
    )

    return {
        "status": "ok",
        "mode": "private" if settings.private_app else "service",
        "llm_ready": llm_configured,
    }


# ========== API 路由 ==========

# v1 API
app.include_router(auth_router, prefix="/api/v1")
app.include_router(dialog_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(ws_router, prefix="/api/v1")

# Orchestrator TEI v1 调试端点
if settings.enable_orchestrator_debug_api:
    logger.info("orchestrator_debug_api_enabled")
    app.include_router(orchestrator_router, prefix="/api/v1")
else:
    logger.info("orchestrator_debug_api_disabled")


# ========== 启动入口 ==========


def main():
    """命令行启动入口"""
    import uvicorn

    target = "app.main:app" if settings.is_development else app
    uvicorn.run(
        target,
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()

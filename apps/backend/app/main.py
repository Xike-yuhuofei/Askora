"""
FastAPI 主应用入口
苏格拉底式教学 App 后端 - 个人版精简版

EXEC-048: No-Auth & Loopback Cutover
架构特点：
- 无认证（LocalOwnerContext 单用户模式）
- 本地知识库/RAG 支持
- Loopback-only 网络边界
- 国产模型路由
"""

from __future__ import annotations

import ipaddress
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import (
    book_learning_router,
    data_control_router,
    dialog_router,
    documents_router,
    goals_router,
    onboarding_router,
    orchestrator_router,
    recovery_router,
    users_router,
    workspace_router,
    ws_router,
)
from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.exceptions import AppError
from app.core.logging import get_logger, setup_logging
from app.core.redis_client import close_redis, init_redis
from app.data_control.erasure import erasure_fail_closed
from app.observability import setup_observability

# 初始化日志
setup_logging()
logger = get_logger(__name__)
ERASURE_FAIL_CLOSED_MARKER = (
    Path(settings.local_storage_base_path).resolve().parent / "recovery" / "erasure-pending.json"
)

# EXEC-048: Loopback-only network boundary
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
LOOPBACK_ORIGINS = {
    "http://127.0.0.1",
    "http://localhost",
    "https://127.0.0.1",
    "https://localhost",
}


def _validate_loopback_host(host: str) -> None:
    """Validate that the host is loopback-only for production (EXEC-048).

    Production Local Web must not bind to LAN/public addresses.
    Only loopback addresses are permitted.
    """
    if host in LOOPBACK_HOSTS:
        return

    try:
        ip = ipaddress.ip_address(host)
    except ValueError as exc:
        raise ValueError(f"LOCAL_NETWORK_BOUNDARY_VIOLATION: Invalid host address: {host}") from exc

    if not ip.is_loopback:
        raise ValueError(
            f"LOCAL_NETWORK_BOUNDARY_VIOLATION: "
            f"Host {host} is not loopback-only. "
            f"Production mode only allows loopback addresses."
        )


def _is_loopback_origin(origin: str | None) -> bool:
    """Check if an HTTP origin is loopback-only (EXEC-048)."""
    if not origin:
        return True  # Same-origin / no-origin requests allowed (loopback default)
    return (
        origin in LOOPBACK_ORIGINS
        or origin.startswith("http://127.0.0.1:")
        or origin.startswith("http://localhost:")
    )


def _check_runtime_config() -> None:
    """
    启动时检查关键系统运行配置
    EXEC-048: 添加 loopback 网络边界验证
    """
    checks: list[str] = []

    # LLM API Key
    llm_keys = {
        "qwen": settings.llm_qwen_api_key,
        "deepseek": settings.llm_deepseek_api_key,
        "doubao": settings.llm_doubao_api_key,
        "zhipu": settings.llm_zhipu_api_key,
    }
    if not any(llm_keys.values()):
        logger.warning(
            "config_llm_api_key_missing",
            detail="未配置任何 LLM API Key，对话回复将使用模拟响应",
        )
        checks.append("llm_api_key: MISSING")
    else:
        logger.info("config_llm_api_key_ok", providers=[k for k, v in llm_keys.items() if v])

    # EXEC-048: Loopback-only network boundary validation
    try:
        _validate_loopback_host(settings.host)
        logger.info("loopback_host_boundary_ok", host=settings.host)
    except ValueError as e:
        logger.error("loopback_host_boundary_violation", error=str(e))
        if not settings.is_development:
            raise RuntimeError(str(e)) from e
        checks.append(f"host_boundary: VIOLATION ({settings.host})")

    # EXEC-048: JWT secret key is no longer required for production
    # Keep warning for development environments that may still use auth
    if settings.jwt_secret_key == "change-me-in-production" and settings.is_development:
        logger.info("jwt_secret_default_dev", detail="JWT 密钥仍为默认值（仅开发环境）")

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

    # 恢复屏障与到期删除必须先于 Redis、模型和文档后台处理。
    from app.core.database import get_session_factory
    from app.services.privacy.runtime import start_account_deletion_runtime

    recovered = await start_account_deletion_runtime(get_session_factory())
    logger.info("account_deletion_runtime_initialized", recovered_subjects=recovered)

    # 初始化 Redis
    try:
        await init_redis()
        logger.info("redis_initialized")
        from app.services.privacy.cache import reconcile_cache_barriers
        from app.services.privacy.restore_barrier import RestoreBarrierStore

        cache_deleted = await reconcile_cache_barriers(
            RestoreBarrierStore(Path(settings.privacy_restore_barrier_path))
        )
        logger.info("privacy_cache_reconciled", deleted_keys=cache_deleted)
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
        from app.services.documents.processing_worker import start_document_processing_runtime

        get_tokenizer()
        reconciled = await start_document_processing_runtime(get_session_factory())
        logger.info("document_services_initialized", reconciled_tasks=reconciled)
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

    # 关闭 durable document worker，再释放数据库连接。
    from app.services.documents.processing_worker import stop_document_processing_runtime

    await stop_document_processing_runtime()
    logger.info("document_tasks_drained")

    from app.services.privacy.runtime import stop_account_deletion_runtime

    await stop_account_deletion_runtime()
    logger.info("account_deletion_tasks_drained")

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

# EXEC-048: CORS restricted to loopback origins only
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 可观测性
setup_observability(app)


@app.middleware("http")
async def enforce_loopback_origin(request: Request, call_next):
    """EXEC-048: Enforce loopback-only origin for HTTP requests.

    Production Local Web must only accept requests from loopback origins.
    Non-loopback origins are rejected with 403.
    """
    if not settings.is_development:
        origin = request.headers.get("origin")
        referer = request.headers.get("referer")

        # Allow health check endpoints without origin validation
        if request.url.path.startswith("/health"):
            return await call_next(request)

        # Validate origin if present
        if origin and not _is_loopback_origin(origin):
            logger.warning("loopback_origin_rejected", origin=origin, path=request.url.path)
            return JSONResponse(
                status_code=403,
                content={
                    "error": {
                        "code": "LOCAL_NETWORK_BOUNDARY_VIOLATION",
                        "message": "仅允许本地回环地址访问",
                        "origin": origin,
                    }
                },
            )

        # Validate referer as fallback
        if not origin and referer:
            if not _is_loopback_origin(referer):
                logger.warning("loopback_referer_rejected", referer=referer, path=request.url.path)
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": {
                            "code": "LOCAL_NETWORK_BOUNDARY_VIOLATION",
                            "message": "仅允许本地回环地址访问",
                            "referer": referer,
                        }
                    },
                )

    return await call_next(request)


@app.middleware("http")
async def enforce_pending_erasure_fail_closed(request: Request, call_next):
    if erasure_fail_closed(ERASURE_FAIL_CLOSED_MARKER, request.url.path):
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "DATA_ERASURE_PARTIAL",
                    "message": "删除后恢复基线尚未完成，学习数据功能暂时关闭",
                    "request_id": getattr(request.state, "request_id", "unknown"),
                }
            },
        )
    return await call_next(request)


# ========== 全局异常处理 ==========


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    """统一应用异常处理"""
    request_id = getattr(request.state, "request_id", "unknown")
    correlation_id = exc.correlation_id or request_id

    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "request_id": request_id,
                "category": exc.category,
                "retryable": exc.retryable,
                "correlation_id": correlation_id,
                "details": (
                    exc.error_detail if hasattr(exc, "error_detail") and exc.error_detail else None
                ),
                "recovery": exc.recovery,
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
                "category": "internal",
                "retryable": False,
                "correlation_id": request_id,
                "details": None,
                "recovery": None,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(request: Request, exc: RequestValidationError):
    """Keep the destructive confirmation failure stable without echoing submitted secrets."""
    if request.url.path.endswith("/account/deletion/request") and any(
        error.get("loc", ())[-1:] == ("confirmation_phrase",) for error in exc.errors()
    ):
        from app.core.exceptions import AccountDeletionConfirmationInvalidError

        error = AccountDeletionConfirmationInvalidError()
        return await app_error_handler(request, error)
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


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
    provider = settings.llm_default_provider.value
    api_key = getattr(settings, f"llm_{provider}_api_key")
    return {
        "status": "ok",
        "mode": "private" if settings.private_app else "service",
        "model_configuration": {
            "provider": provider,
            "model": getattr(settings, f"llm_{provider}_model"),
            "runtime_ready": bool(api_key),
        },
    }


# ========== API 路由 ==========

# EXEC-048: Removed auth_router, account_router, dev_auth_router registrations
# Authentication is no longer required for single-user local instance.
# Legacy auth endpoints return 404 (handled by not registering the router).

# v1 API (no-auth loopback mode)
app.include_router(book_learning_router, prefix="/api/v1")
app.include_router(data_control_router, prefix="/api/v1")
app.include_router(dialog_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(goals_router, prefix="/api/v1")
app.include_router(ws_router, prefix="/api/v1")
app.include_router(workspace_router, prefix="/api/v1")
app.include_router(onboarding_router, prefix="/api/v1")
app.include_router(recovery_router, prefix="/api/v1")

# Orchestrator TEI v1 调试端点
if settings.enable_orchestrator_debug_api:
    logger.info("orchestrator_debug_api_enabled")
    app.include_router(orchestrator_router, prefix="/api/v1")
else:
    logger.info("orchestrator_debug_api_disabled")

# EXEC-048: dev auto-login remains disabled in no-auth mode.
if settings.dev_auto_login_enabled and settings.is_development:
    logger.warning(
        "dev_auto_login_enabled_deprecated", message="Dev auto-login is deprecated in no-auth mode."
    )


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

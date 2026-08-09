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

import base64
import hmac
import re
from collections import Counter
from contextlib import asynccontextmanager
from math import log2
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.api.v1 import (
    auth_router,
    book_learning_router,
    data_control_router,
    dialog_router,
    documents_router,
    onboarding_router,
    orchestrator_router,
    recovery_router,
    users_router,
    workspace_router,
    ws_router,
)
from app.api.v1.account import router as account_router
from app.contracts.model_configuration import (
    ModelConfigErrorCode,
    ModelConfigErrorV1,
)
from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.exceptions import AppError
from app.core.logging import get_logger, setup_logging
from app.core.redis_client import close_redis, init_redis
from app.core.startup_diagnostics import (
    classify_database_startup_error,
    emit_startup_diagnostic,
)
from app.data_control.erasure import erasure_fail_closed
from app.observability import setup_observability

# 初始化日志
setup_logging()
logger = get_logger(__name__)
ERASURE_FAIL_CLOSED_MARKER = (
    Path(settings.local_storage_base_path).resolve().parent / "recovery" / "erasure-pending.json"
)


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
    try:
        await init_db()
    except Exception as exc:
        code, retryable = classify_database_startup_error(exc)
        emit_startup_diagnostic(code, retryable=retryable)
        raise
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
    from app.orchestration.model_configuration import get_runtime_model_config_summary

    return {
        "status": "ok",
        "mode": "private" if settings.private_app else "service",
        "model_configuration": get_runtime_model_config_summary().model_dump(mode="json"),
    }


_DESKTOP_CONTROL_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_-]{64}")
_DESKTOP_CONTROL_TOKEN_BYTES = 48
_DESKTOP_CONTROL_TOKEN_MIN_UNIQUE_BYTES = 24
_DESKTOP_CONTROL_TOKEN_MIN_SHANNON_ENTROPY = 4.75


def _shannon_entropy(data: bytes) -> float:
    counts = Counter(data)
    total = len(data)
    return -sum((count / total) * log2(count / total) for count in counts.values())


def _has_repeated_block(data: bytes) -> bool:
    for block_size in range(1, len(data) // 2 + 1):
        if len(data) % block_size == 0 and data == data[:block_size] * (len(data) // block_size):
            return True
    return False


def _is_high_entropy_desktop_control_token(token: str) -> bool:
    """Validate Electron's 48-byte token against explicit statistical quality limits."""
    if not _DESKTOP_CONTROL_TOKEN_PATTERN.fullmatch(token):
        return False
    try:
        decoded = base64.urlsafe_b64decode(token + "==")
    except (ValueError, UnicodeEncodeError):
        return False
    return (
        len(decoded) == _DESKTOP_CONTROL_TOKEN_BYTES
        and len(set(decoded)) >= _DESKTOP_CONTROL_TOKEN_MIN_UNIQUE_BYTES
        and _shannon_entropy(decoded) >= _DESKTOP_CONTROL_TOKEN_MIN_SHANNON_ENTROPY
        and not _has_repeated_block(decoded)
    )


def _model_config_error_response(*, status_code: int, error: ModelConfigErrorV1) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": error.model_dump(mode="json")})


async def _desktop_model_probe(request: Request) -> JSONResponse:
    """Local-only credential probe; deliberately absent from public API/OpenAPI."""
    from app.contracts.model_configuration import ModelConfigCandidateV1
    from app.orchestration.model_configuration import (
        ModelConfigurationProbeError,
        probe_model_configuration,
    )

    correlation_id = getattr(request.state, "request_id", None)
    peer = request.client.host if request.client else ""
    supplied_token = request.headers.get("x-askora-desktop-control", "")
    if peer not in {"127.0.0.1", "::1"} or not hmac.compare_digest(
        supplied_token, settings.desktop_control_token
    ):
        return _model_config_error_response(
            status_code=404,
            error=ModelConfigErrorV1.for_code(
                code=ModelConfigErrorCode.MODEL_CONTROL_NOT_AVAILABLE,
                message="本地模型控制面不可用",
                correlation_id=correlation_id,
            ),
        )
    try:
        payload = await request.json()
        candidate = ModelConfigCandidateV1.model_validate(payload)
    except (ValidationError, ValueError, TypeError):
        return _model_config_error_response(
            status_code=422,
            error=ModelConfigErrorV1.for_code(
                code=ModelConfigErrorCode.MODEL_CONFIG_SCHEMA_UNSUPPORTED,
                message="模型配置格式或 provider/model 组合不受支持",
                correlation_id=correlation_id,
            ),
        )
    try:
        result = await probe_model_configuration(candidate, correlation_id=correlation_id)
        return JSONResponse(status_code=200, content=result.model_dump(mode="json"))
    except ModelConfigurationProbeError as exc:
        error = ModelConfigErrorV1.for_code(
            code=exc.code,
            message=exc.message,
            correlation_id=correlation_id,
        )
        status_code = 503 if error.retryable else 400
        if exc.code == ModelConfigErrorCode.MODEL_CREDENTIAL_REJECTED:
            status_code = 401
        elif exc.code == ModelConfigErrorCode.MODEL_RATE_LIMITED:
            status_code = 429
        return _model_config_error_response(
            status_code=status_code,
            error=error,
        )


if (
    settings.is_local
    and settings.private_app
    and settings.host in {"127.0.0.1", "::1", "localhost"}
    and _is_high_entropy_desktop_control_token(settings.desktop_control_token)
):
    app.add_api_route(
        "/_desktop/model-configuration/probe",
        _desktop_model_probe,
        methods=["POST"],
        include_in_schema=False,
    )


# ========== API 路由 ==========

# v1 API
app.include_router(auth_router, prefix="/api/v1")
app.include_router(book_learning_router, prefix="/api/v1")
app.include_router(data_control_router, prefix="/api/v1")
app.include_router(dialog_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(ws_router, prefix="/api/v1")
app.include_router(workspace_router, prefix="/api/v1")
app.include_router(onboarding_router, prefix="/api/v1")
app.include_router(recovery_router, prefix="/api/v1")

app.include_router(account_router, prefix="/api/v1")

# Orchestrator TEI v1 调试端点
if settings.enable_orchestrator_debug_api:
    logger.info("orchestrator_debug_api_enabled")
    app.include_router(orchestrator_router, prefix="/api/v1")
else:
    logger.info("orchestrator_debug_api_disabled")

# 开发自动登录（仅非生产环境，显式开启时注册）
if settings.dev_auto_login_enabled:
    from app.api.v1.dev_auth import router as dev_auth_router

    logger.info("dev_auto_login_enabled")
    app.include_router(dev_auth_router, prefix="/api/v1")


# ========== 启动入口 ==========


def main():
    """命令行启动入口"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "data-control":
        from app.data_control.cli import main as data_control_main

        raise SystemExit(data_control_main(sys.argv[2:]))

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

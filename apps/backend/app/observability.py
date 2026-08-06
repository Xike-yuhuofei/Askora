"""
可观测性配置模块

为 Askora 后端提供统一的可观测性配置入口，包括：
1. Prometheus 指标端点注册
2. OpenTelemetry 分布式追踪（可选，基础配置）
3. 请求级日志关联（Request-ID 注入）
4. 就绪性探针端点（/ready）
5. 健康检查增强（Redis / DB 实时状态）
6. 告警规则文档

使用方式：
    from app.observability import setup_observability
    setup_observability(app)

或按需单独调用：
    from app.observability import setup_metrics, setup_log_correlation
    setup_metrics(app)
    setup_log_correlation(app)
"""

from __future__ import annotations

import re
import time
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ======================================================================
# setup_metrics — Prometheus 指标端点注册
# ======================================================================


def setup_metrics(app: FastAPI) -> None:
    """
    注册 Prometheus /metrics 端点与指标采集中间件。

    详细指标定义见 app.metrics 模块。
    当 settings.prometheus_enabled 为 False 时跳过注册。

    :param app: FastAPI 应用实例
    """
    from app.metrics import init_metrics

    init_metrics(app)


# ======================================================================
# setup_tracing — OpenTelemetry 追踪基础配置
# ======================================================================


def setup_tracing(app: FastAPI) -> None:
    """
    配置 OpenTelemetry 分布式追踪（基础版）。

    当 opentelemetry 相关包未安装时静默跳过，不影响应用启动。
    生产环境可在此处接入 Jaeger / Zipkin / Tempo 等后端。

    :param app: FastAPI 应用实例
    """
    try:
        from opentelemetry import trace
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            BatchSpanProcessor,
            ConsoleSpanExporter,
        )

        provider = TracerProvider()
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        trace.set_tracer_provider(provider)

        FastAPIInstrumentor.instrument_app(app)

        trace.get_tracer("askora")
        logger.info("otel_tracing_initialized", tracer_name="askora")

    except ImportError:
        logger.info("otel_tracing_skipped_package_not_installed")
    except Exception as e:
        logger.warning("otel_tracing_setup_failed", error_type=type(e).__name__)


# ======================================================================
# setup_log_correlation — 请求级日志关联
# ======================================================================


class LogCorrelationMiddleware(BaseHTTPMiddleware):
    """
    请求级日志关联中间件。

    为每个请求分配唯一的 Request-ID（如果请求头中未提供），
    并将其注入 structlog 上下文变量，使所有日志条目自动携带
    request_id 字段，便于全链路追踪和日志关联。
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """请求分发 — 注入 Request-ID 到日志上下文"""
        from structlog.contextvars import bind_contextvars, unbind_contextvars

        supplied_id = request.headers.get("X-Request-ID", "")
        request_id = (
            supplied_id
            if re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", supplied_id)
            else str(uuid.uuid4())
        )
        request.state.request_id = request_id
        bind_contextvars(request_id=request_id)

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            unbind_contextvars("request_id")


def setup_log_correlation(app: FastAPI) -> None:
    """
    配置请求级日志关联中间件。

    每个进入的请求会被分配唯一的 Request-ID，
    该 ID 会出现在响应头和所有关联的日志条目中。

    :param app: FastAPI 应用实例
    """
    app.add_middleware(LogCorrelationMiddleware)
    logger.info("log_correlation_middleware_enabled")


# ======================================================================
# /ready 就绪性探针端点
# ======================================================================


async def _check_redis_ready() -> bool:
    """
    检查 Redis 连接状态。

    :return: 是否已就绪
    """
    try:
        from app.core.redis_client import get_redis_client, is_redis_available

        if is_redis_available() is False:
            return False
        client = get_redis_client()
        return await client.ping()
    except Exception:
        return False


async def _check_db_ready() -> bool:
    """
    检查数据库连接状态。

    :return: 是否已就绪
    """
    try:
        from app.core.database import get_engine

        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        return True
    except Exception:
        return False


async def readiness_probe() -> JSONResponse:
    """
    /ready 就绪性探针端点。

    检查 Redis 和 PostgreSQL 数据库的连接状态，
    供 Kubernetes / Docker 编排层进行 liveness / readiness 探测。

    返回 200 表示全部就绪，503 表示部分组件未就绪。
    """
    redis_ok = await _check_redis_ready()
    db_ok = await _check_db_ready()

    components = {
        "redis": redis_ok,
        "database": db_ok,
    }
    redis_required = not settings.auto_create_tables
    all_ready = db_ok and (redis_ok or not redis_required)

    status_code = 200 if all_ready else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if all_ready else "degraded",
            "components": components,
            "requirements": {
                "database": True,
                "redis": redis_required,
            },
            "degraded_features": (
                ["跨进程缓存、令牌撤销持久化和 KT 持久化"]
                if not redis_ok and not redis_required
                else []
            ),
            "timestamp": time.time(),
        },
        headers={"Cache-Control": "no-store"},
    )


# ======================================================================
# setup_observability — 一键配置所有可观测性组件
# ======================================================================


def setup_observability(app: FastAPI) -> None:
    """
    一键配置所有可观测性组件。

    按顺序执行：
    1. 日志关联中间件（最先执行，确保后续所有请求有 Request-ID）
    2. Prometheus 指标（注册 /metrics 端点与采集中间件）
    3. OpenTelemetry 追踪（可选，依赖 opentelemetry 包）
    4. 注册 /ready 就绪性探针端点

    :param app: FastAPI 应用实例
    """
    setup_log_correlation(app)
    setup_metrics(app)
    setup_tracing(app)

    from fastapi import FastAPI

    if isinstance(app, FastAPI):
        app.add_api_route(
            "/ready",
            readiness_probe,
            methods=["GET"],
            tags=["系统"],
            include_in_schema=True,
        )
    else:
        app.add_route(
            "/ready",
            readiness_probe,
            methods=["GET"],
        )
    logger.info("observability_setup_complete")


# ======================================================================
# 告警规则文档（Prometheus / Alertmanager 配置参考）
# ======================================================================

# ----------------------------------------------------------------------
# 以下告警规则为推荐配置，供运维团队在 Prometheus 中配置。
# 可直接复制到 Prometheus 的 alert_rules.yml 或 Alertmanager 中使用。
#
# ========== 规则 1：高错误率 ==========
#
# - 名称: AskoraHighErrorRate
# - 描述: 5 分钟内错误率超过 1%
# - 严重度: critical
# - 表达式:
#     sum(rate(askora_errors_total[5m]))
#     /
#     sum(rate(askora_engine_calls_total[5m]))
#     > 0.01
# - 标签:
#     severity: critical
#     team: askora-backend
#
# ========== 规则 2：延迟 SLO 违反 ==========
#
# - 名称: AskoraLatencySLOBreach
# - 描述: API P95 响应时间超过 SLO（8 秒）
# - 严重度: critical
# - 表达式:
#     histogram_quantile(
#       0.95,
#       sum(rate(askora_response_time_seconds_bucket[5m])) by (le, endpoint)
#     ) > 8
# - 标签:
#     severity: critical
#     team: askora-backend
#
# ========== 规则 3：Redis 连接断开 ==========
#
# - 名称: AskoraRedisDown
# - 描述: Redis 连接状态为 0
# - 严重度: critical
# - 表达式:
#     askora_redis_connected == 0
# - 标签:
#     severity: critical
#     team: askora-backend
#
# ========== 规则 4：数据库连接断开 ==========
#
# - 名称: AskoraDatabaseDown
# - 描述: 数据库连接状态为 0
# - 严重度: critical
# - 表达式:
#     askora_db_connected == 0
# - 标签:
#     severity: critical
#     team: askora-backend
#
# ========== 规则 5：LLM API 高失败率 ==========
#
# - 名称: AskoraLLMHighFailureRate
# - 描述: LLM API 调用 5 分钟失败率超过 10%
# - 严重度: warning
# - 表达式:
#     sum(rate(askora_llm_calls_total{success="false"}[5m]))
#     /
#     sum(rate(askora_llm_calls_total[5m]))
#     > 0.10
# - 标签:
#     severity: warning
#     team: askora-backend
#
# ========== 规则 6：活跃会话异常 ==========
#
# - 名称: AskoraSessionsAbnormal
# - 描述: 活跃会话数在短时间内大幅波动（可能的异常流量）
# - 严重度: warning
# - 表达式:
#     abs(
#       askora_active_sessions
#       - askora_active_sessions offset 5m
#     ) > 100
# - 标签:
#     severity: warning
#     team: askora-backend
#
# ========== 规则 7：引擎切换异常 ==========
#
# - 名称: AskoraExcessiveEngineSwitching
# - 描述: 5 分钟内引擎切换次数异常高（可能的循环切换）
# - 严重度: warning
# - 表达式:
#     rate(askora_engine_switches_total[5m]) > 0.5
# - 标签:
#     severity: warning
#     team: askora-backend
#
# ========== 规则 8：引擎调用延迟异常 ==========
#
# - 名称: AskoraEngineCallSlow
# - 描述: 引擎调用 P95 耗时超过 5 秒
# - 严重度: warning
# - 表达式:
#     histogram_quantile(
#       0.95,
#       sum(rate(askora_engine_call_duration_seconds_bucket[5m])) by (le, engine_id)
#     ) > 5
# - 标签:
#     severity: warning
#     team: askora-backend
#
# ======================================================================


__all__ = [
    "setup_metrics",
    "setup_tracing",
    "setup_log_correlation",
    "LogCorrelationMiddleware",
    "readiness_probe",
    "setup_observability",
]

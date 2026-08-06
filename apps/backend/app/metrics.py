"""
Prometheus 指标定义与辅助工具

为 Askora 后端提供全面的可观测性指标覆盖：
- 引擎调用计数与耗时
- 引擎切换追踪
- 学习轮次统计
- 掌握度更新计数
- 反思触发追踪
- LLM 调用统计
- 错误统计
- API 响应时间
- 活跃会话数
- 知识点与掌握度分布
- Redis / 数据库连接状态
"""

from __future__ import annotations

import time
from collections.abc import AsyncGenerator
from typing import Optional

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    REGISTRY,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ======================================================================
# Counter 指标
# ======================================================================

askora_engine_calls_total = Counter(
    "askora_engine_calls_total",
    "引擎调用总次数",
    ["engine_id", "flow_stage"],
)

askora_engine_switches_total = Counter(
    "askora_engine_switches_total",
    "引擎切换总次数",
    ["from_engine", "to_engine", "reason"],
)

askora_turn_total = Counter(
    "askora_turn_total",
    "学习轮次总数",
    ["subject", "engine_id"],
)

askora_mastery_updates_total = Counter(
    "askora_mastery_updates_total",
    "掌握度更新总次数",
    ["kp_id", "subject", "is_correct"],
)

askora_reflection_triggers_total = Counter(
    "askora_reflection_triggers_total",
    "反思触发总次数",
    ["reflection_type"],
)

askora_llm_calls_total = Counter(
    "askora_llm_calls_total",
    "LLM API 调用总次数",
    ["provider", "model", "success"],
)

askora_errors_total = Counter(
    "askora_errors_total",
    "错误总次数",
    ["error_type", "engine_id"],
)

# ======================================================================
# Histogram 指标
# ======================================================================

askora_engine_call_duration_seconds = Histogram(
    "askora_engine_call_duration_seconds",
    "引擎调用耗时（秒）",
    ["engine_id", "flow_stage"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

askora_llm_call_duration_seconds = Histogram(
    "askora_llm_call_duration_seconds",
    "LLM API 调用耗时（秒）",
    ["provider", "model"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)

askora_turn_duration_seconds = Histogram(
    "askora_turn_duration_seconds",
    "学习轮次总耗时（秒）",
    ["engine_id"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
)

askora_response_time_seconds = Histogram(
    "askora_response_time_seconds",
    "API 响应时间（秒）",
    ["endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# ======================================================================
# Gauge 指标
# ======================================================================

askora_active_sessions = Gauge(
    "askora_active_sessions",
    "当前活跃学习会话数",
)

askora_knowledge_points_total = Gauge(
    "askora_knowledge_points_total",
    "追踪的知识点总数",
    ["subject"],
)

askora_mastery_distribution = Gauge(
    "askora_mastery_distribution",
    "掌握度等级分布",
    ["subject", "level"],
)

askora_redis_connected = Gauge(
    "askora_redis_connected",
    "Redis 连接状态（1=已连接，0=已断开）",
)

askora_db_connected = Gauge(
    "askora_db_connected",
    "数据库连接状态（1=已连接，0=已断开）",
)

# ======================================================================
# 辅助函数
# ======================================================================


def track_engine_call(engine_id: str, stage: str, duration: float) -> None:
    """
    记录一次引擎调用。

    :param engine_id: 引擎标识（如 socratic / explain / quiz）
    :param stage: 流程阶段（diagnose / learn / inquire / validate / drill / produce）
    :param duration: 调用耗时（秒）
    """
    askora_engine_calls_total.labels(engine_id=engine_id, flow_stage=stage).inc()
    askora_engine_call_duration_seconds.labels(engine_id=engine_id, flow_stage=stage).observe(
        duration
    )


def track_engine_switch(from_engine: str, to_engine: str, reason: str) -> None:
    """
    记录一次引擎切换。

    :param from_engine: 源引擎 ID
    :param to_engine: 目标引擎 ID
    :param reason: 切换原因
    """
    askora_engine_switches_total.labels(
        from_engine=from_engine, to_engine=to_engine, reason=reason
    ).inc()


def track_turn(subject: str, engine_id: str, duration: float) -> None:
    """
    记录一次学习轮次。

    :param subject: 学科（如 math / chinese / physics）
    :param engine_id: 引擎 ID
    :param duration: 轮次总耗时（秒）
    """
    askora_turn_total.labels(subject=subject, engine_id=engine_id).inc()
    askora_turn_duration_seconds.labels(engine_id=engine_id).observe(duration)


def track_mastery_update(kp_id: str, subject: str, is_correct: bool) -> None:
    """
    记录一次掌握度更新。

    :param kp_id: 知识点 ID
    :param subject: 学科
    :param is_correct: 是否答对
    """
    askora_mastery_updates_total.labels(
        kp_id=kp_id, subject=subject, is_correct=str(is_correct).lower()
    ).inc()


def track_reflection(reflection_type: str) -> None:
    """
    记录一次反思触发。

    :param reflection_type: 反思类型
    """
    askora_reflection_triggers_total.labels(reflection_type=reflection_type).inc()


def track_llm_call(provider: str, model: str, duration: float, success: bool) -> None:
    """
    记录一次 LLM API 调用。

    :param provider: 供应商（qwen / deepseek / doubao）
    :param model: 模型名称
    :param duration: 调用耗时（秒）
    :param success: 是否成功
    """
    askora_llm_calls_total.labels(
        provider=provider, model=model, success=str(success).lower()
    ).inc()
    askora_llm_call_duration_seconds.labels(provider=provider, model=model).observe(duration)


def track_error(error_type: str, engine_id: str = "") -> None:
    """
    记录一次错误。

    :param error_type: 错误类型
    :param engine_id: 关联的引擎 ID（可选）
    """
    askora_errors_total.labels(error_type=error_type, engine_id=engine_id).inc()


def update_active_sessions(delta: int = 1) -> None:
    """
    更新活跃会话数。

    :param delta: 变化量（+1 新会话，-1 会话结束）
    """
    askora_active_sessions.inc(delta)


def set_active_sessions(value: int) -> None:
    """
    直接设置活跃会话数。

    :param value: 当前活跃会话数
    """
    askora_active_sessions.set(value)


def observe_response_time(endpoint: str, duration: float) -> None:
    """
    记录一次 API 响应时间。

    :param endpoint: 端点路径（模板化）
    :param duration: 响应耗时（秒）
    """
    askora_response_time_seconds.labels(endpoint=endpoint).observe(duration)


def set_knowledge_points_total(subject: str, count: int) -> None:
    """
    设置某学科的知识点总数。

    :param subject: 学科
    :param count: 知识点总数
    """
    askora_knowledge_points_total.labels(subject=subject).set(count)


def update_mastery_distribution(subject: str, level: str, count: int) -> None:
    """
    更新某学科某掌握度等级的知识点数量。

    :param subject: 学科
    :param level: 掌握度等级（low / medium / high）
    :param count: 该等级的知识点数量
    """
    askora_mastery_distribution.labels(subject=subject, level=level).set(count)


def set_redis_connected(connected: bool) -> None:
    """
    设置 Redis 连接状态。

    :param connected: 是否已连接
    """
    askora_redis_connected.set(1 if connected else 0)


def set_db_connected(connected: bool) -> None:
    """
    设置数据库连接状态。

    :param connected: 是否已连接
    """
    askora_db_connected.set(1 if connected else 0)


# ======================================================================
# FastAPI 中间件：自动采集 API 响应时间
# ======================================================================


class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    """
    Prometheus 指标采集中间件。

    自动为每个 API 请求记录响应时间 Histogram。
    支持模板化端点（将路径中的数字 ID 替换为 {id}）。
    """

    SENSITIVE_PATHS = {
        "/metrics",
        "/health",
        "/ready",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/static",
        "/favicon.ico",
    }

    async def dispatch(self, request: Request, call_next) -> Response:
        """请求分发 - 记录响应时间"""
        path = request.url.path

        if self._should_skip(path):
            return await call_next(request)

        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        endpoint = self._normalize_endpoint(path)
        observe_response_time(endpoint, duration)

        return response

    @classmethod
    def _should_skip(cls, path: str) -> bool:
        """检查是否跳过采集"""
        for skip_path in cls.SENSITIVE_PATHS:
            if path == skip_path or path.startswith(skip_path + "/"):
                return True
        return False

    @staticmethod
    def _normalize_endpoint(path: str) -> str:
        """
        将端点路径模板化，把数字 ID 替换为 {id}。
        例如 /api/v1/dialog/123 -> /api/v1/dialog/{id}
        """
        import re

        normalized = re.sub(r"/\d+", "/{id}", path)
        return normalized


# ======================================================================
# FastAPI 依赖：为特定端点记录响应时间
# ======================================================================


def get_metrics_dependency(endpoint_name: Optional[str] = None):
    """
    FastAPI 依赖，用于在路由级别精确记录响应时间。

    使用方式：
        @app.get("/api/v1/example")
        async def example(metrics=Depends(get_metrics_dependency("example"))):
            ...

    :param endpoint_name: 端点名称（默认使用当前路径）
    """
    import time as _time

    async def _dependency(request: Request) -> AsyncGenerator[dict, None]:
        start = _time.time()
        try:
            yield {}
        finally:
            duration = _time.time() - start
            name = endpoint_name or request.url.path
            observe_response_time(name, duration)

    return _dependency


# ======================================================================
# Prometheus 指标端点
# ======================================================================


def metrics_endpoint(request: Request) -> Response:
    """
    Prometheus /metrics 端点处理器。

    返回所有已注册指标的最新值，供 Prometheus Server 抓取。
    接受可选的 Request 参数以兼容 Starlette 路由协议。
    """
    from fastapi.responses import Response as FastAPIResponse

    return FastAPIResponse(
        content=generate_latest(REGISTRY),
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-store"},
    )


# ======================================================================
# 模块初始化
# ======================================================================

_initialized = False


def init_metrics(app: FastAPI) -> None:
    """
    初始化 Prometheus 指标系统。

    包括：
    1. 注册 /metrics 端点
    2. 添加 PrometheusMetricsMiddleware 中间件
    3. 注册应用启动/关闭事件来更新 Gauge

    :param app: FastAPI 应用实例
    """
    global _initialized
    if _initialized:
        logger.warning("prometheus_metrics_already_initialized")
        return

    if not settings.prometheus_enabled:
        logger.info("prometheus_metrics_disabled_by_config")
        return

    app.add_route("/metrics", metrics_endpoint, include_in_schema=False)
    app.add_middleware(PrometheusMetricsMiddleware)

    set_redis_connected(False)
    set_db_connected(False)
    set_active_sessions(0)

    _initialized = True
    logger.info("prometheus_metrics_initialized")


__all__ = [
    # Counter 指标
    "askora_engine_calls_total",
    "askora_engine_switches_total",
    "askora_turn_total",
    "askora_mastery_updates_total",
    "askora_reflection_triggers_total",
    "askora_llm_calls_total",
    "askora_errors_total",
    # Histogram 指标
    "askora_engine_call_duration_seconds",
    "askora_llm_call_duration_seconds",
    "askora_turn_duration_seconds",
    "askora_response_time_seconds",
    # Gauge 指标
    "askora_active_sessions",
    "askora_knowledge_points_total",
    "askora_mastery_distribution",
    "askora_redis_connected",
    "askora_db_connected",
    # 辅助函数
    "track_engine_call",
    "track_engine_switch",
    "track_turn",
    "track_mastery_update",
    "track_reflection",
    "track_llm_call",
    "track_error",
    "update_active_sessions",
    "set_active_sessions",
    "observe_response_time",
    "set_knowledge_points_total",
    "update_mastery_distribution",
    "set_redis_connected",
    "set_db_connected",
    # 中间件与依赖
    "PrometheusMetricsMiddleware",
    "get_metrics_dependency",
    # 端点与初始化
    "metrics_endpoint",
    "init_metrics",
]

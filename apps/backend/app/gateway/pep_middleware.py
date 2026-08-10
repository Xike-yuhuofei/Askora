"""
简化版 PEP 网关中间件
移除了内容审核、防沉迷、合规检查等功能
保留基础的请求追踪和速率限制
"""

from __future__ import annotations

import time
import uuid
from typing import Optional

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import AppError, RateLimitError
from app.core.logging import get_logger
from app.core.redis_client import RedisKeys, get_redis_client

logger = get_logger(__name__)

# 不需要检查的路径白名单
WHITELIST_PATHS = {
    "/health",
    "/metrics",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/static",
    "/favicon.ico",
}


class SimpleMiddleware(BaseHTTPMiddleware):
    """
    简化版中间件：仅保留基础速率限制和请求追踪
    """

    def __init__(self, app: FastAPI):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        """请求分发"""
        path = request.url.path
        # 请求 ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # 白名单路径直接放行
        if self._is_whitelisted(path):
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response

        start_time = time.time()

        try:
            # 速率限制
            await self._check_rate_limit(request)

            # 继续处理请求
            response = await call_next(request)

            # 添加追踪头
            latency_ms = int((time.time() - start_time) * 1000)
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = str(latency_ms)

            return response

        except AppError as e:
            logger.warning("request_blocked", path=path, error_code=e.error_code, message=e.message)
            return self._create_error_response(
                status_code=e.status_code,
                error_code=e.error_code,
                message=e.message,
                request_id=request_id,
                details=e.error_detail if hasattr(e, "error_detail") else None,
            )
        except Exception as e:
            logger.error("middleware_error", path=path, error=str(e))
            return self._create_error_response(
                status_code=500,
                error_code="SYS-0001",
                message="服务器内部错误",
                request_id=request_id,
            )

    def _is_whitelisted(self, path: str) -> bool:
        """检查是否为白名单路径"""
        for wp in WHITELIST_PATHS:
            if path == wp or path.startswith(wp + "/"):
                return True
        return False

    async def _check_rate_limit(self, request: Request) -> None:
        """速率限制检查（IP 级滑动窗口）"""
        client_ip = self._get_client_ip(request)

        try:
            redis = get_redis_client()
            if redis is None:
                # Redis 不可用时放宽限制
                logger.warning("rate_limit_redis_unavailable_skip_check")
                return

            window_key = RedisKeys.format(
                RedisKeys.RATE_LIMIT_IP,
                ip=client_ip,
                window=int(time.time() // 60),
            )

            current = await redis.incr(window_key)
            if current == 1:
                await redis.expire(window_key, RedisKeys.RATE_LIMIT_TTL)

            if current > settings.rate_limit_ip_per_minute:
                raise RateLimitError()
        except RateLimitError:
            raise
        except Exception as e:
            # Redis 故障时放宽限制
            logger.warning("rate_limit_redis_failed", error=str(e))

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端真实 IP"""
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()

        x_real_ip = request.headers.get("X-Real-IP")
        if x_real_ip:
            return x_real_ip

        client = request.client
        return client.host if client else "unknown"

    def _create_error_response(
        self,
        status_code: int,
        error_code: str,
        message: str,
        request_id: str,
        details: Optional[dict] = None,
    ) -> JSONResponse:
        """创建统一格式的错误响应"""
        content = {
            "error": {
                "code": error_code,
                "message": message,
                "request_id": request_id,
            }
        }
        if details:
            content["error"]["details"] = details

        return JSONResponse(status_code=status_code, content=content)


def setup_pep_middleware(app: FastAPI) -> None:
    """配置中间件"""
    app.add_middleware(SimpleMiddleware)
    logger.info("simple_middleware_enabled")

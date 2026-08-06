"""
结构化日志配置 - 合规审计日志与业务日志分离
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

from app.core.config import settings


def setup_logging() -> None:
    """初始化结构化日志系统"""

    # 共享的处理器配置
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso", utc=False),
        structlog.processors.EventRenamer("msg"),
    ]

    if settings.log_format == "json" or settings.is_production:
        # 生产环境: JSON 格式
        structlog.configure(
            processors=shared_processors
            + [
                structlog.processors.ExceptionRenderer(
                    structlog.tracebacks.ExceptionDictTransformer(show_locals=False)
                ),
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(
                logging.getLevelName(settings.log_level)
            ),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        # 开发环境: 人类可读格式
        structlog.configure(
            processors=shared_processors
            + [
                structlog.dev.ConsoleRenderer(colors=True),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(
                logging.getLevelName(settings.log_level)
            ),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )

    # 配置标准库 logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=settings.log_level,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """获取结构化日志记录器"""
    return structlog.get_logger(name)


# 合规审计日志专用 logger
def get_audit_logger() -> structlog.stdlib.BoundLogger:
    """
    获取合规审计日志记录器
    审计日志需满足: 不可篡改、完整留痕、PII 脱敏
    """
    return structlog.get_logger("audit").bind(audit_type="compliance")

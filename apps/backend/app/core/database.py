"""
数据库连接与会话管理
支持 PostgreSQL + 异步 SQLAlchemy + RLS 行级安全
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import event, make_url, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """ORM 基类"""

    pass


_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def _restrict_sqlite_permissions(database_path: str) -> None:
    Path(database_path).resolve().chmod(0o600)


def get_engine() -> AsyncEngine:
    """获取数据库引擎（单例）"""
    global _engine
    if _engine is None:
        engine_kwargs: dict[str, Any] = {
            # SQL 参数可能含 PII/令牌；必须用独立显式开关，不能随 DEBUG 自动开启。
            "echo": settings.database_echo,
            "future": True,
        }
        if not settings.database_url.startswith("sqlite"):
            engine_kwargs.update(
                pool_size=settings.database_pool_size,
                max_overflow=settings.database_max_overflow,
                pool_pre_ping=True,
                pool_recycle=3600,
            )
        _engine = create_async_engine(settings.database_url, **engine_kwargs)

        if settings.database_url.startswith("sqlite"):

            @event.listens_for(_engine.sync_engine, "connect")
            def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """获取会话工厂（单例）"""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话上下文管理器
    自动提交/回滚，自动关闭会话
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖注入用的数据库会话"""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """初始化数据库连接（应用启动时调用）"""
    # 触发引擎创建，建立连接池
    get_engine()
    get_session_factory()

    # 私人本地、开发和测试环境自动建表；失败时终止启动，避免假健康。
    if settings.auto_create_tables:
        from app import models  # noqa: F401  # 确保所有模型注册到 Base.metadata

        async with get_engine().begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        database_path = make_url(settings.database_url).database
        if database_path and database_path != ":memory:":
            await asyncio.to_thread(_restrict_sqlite_permissions, database_path)
    else:
        async with get_engine().connect() as conn:
            await conn.execute(text("SELECT 1"))


async def close_db() -> None:
    """关闭数据库连接（应用关闭时调用）"""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None

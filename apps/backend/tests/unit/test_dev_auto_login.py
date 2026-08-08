"""开发自动登录（免登录直接进入系统）的单元测试。"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.api.v1.dev_auth import DevAutoLoginRequest
from app.core.config import AppEnv, Settings
from app.services.auth.demo_user import (
    DEV_DEMO_PASSWORD,
    DEV_DEMO_USER_ID,
    ensure_demo_user,
)
from app.services.auth.token_service import verify_password


class _Result:
    def __init__(self, user):
        self._user = user

    def scalar_one_or_none(self):
        return self._user


class FakeDB:
    def __init__(self, existing_user=None):
        self.existing_user = existing_user
        self.added = []
        self.commit = AsyncMock()
        self.refresh = AsyncMock()

    async def execute(self, _stmt):
        return _Result(self.existing_user)

    def add(self, obj):
        self.added.append(obj)


def test_dev_auto_login_enabled_is_gating():
    # 显式开启 + 非生产 → 可用
    dev = Settings(enable_dev_auto_login=True, app_env=AppEnv.DEVELOPMENT)
    assert dev.dev_auto_login_enabled is True

    # 显式关闭 → 不可用
    off = Settings(enable_dev_auto_login=False, app_env=AppEnv.DEVELOPMENT)
    assert off.dev_auto_login_enabled is False

    # 生产环境即使开启也强制关闭
    prod = Settings(enable_dev_auto_login=True, app_env=AppEnv.PRODUCTION)
    assert prod.dev_auto_login_enabled is False


@pytest.mark.asyncio
async def test_ensure_demo_user_returns_existing_user():
    existing = SimpleNamespace(password_hash="hashed")
    user = await ensure_demo_user(FakeDB(existing_user=existing))
    assert user is existing


@pytest.mark.asyncio
async def test_ensure_demo_user_creates_missing_user():
    db = FakeDB(existing_user=None)
    user = await ensure_demo_user(db)

    assert user.id == DEV_DEMO_USER_ID
    assert user.password_hash is not None
    assert verify_password(DEV_DEMO_PASSWORD, user.password_hash) is True
    assert db.added == [user]
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once()


def test_dev_auto_login_request_accepts_optional_fingerprint():
    req = DevAutoLoginRequest(device_fingerprint="device-12345678")
    assert req.device_fingerprint == "device-12345678"
    assert DevAutoLoginRequest().device_fingerprint is None

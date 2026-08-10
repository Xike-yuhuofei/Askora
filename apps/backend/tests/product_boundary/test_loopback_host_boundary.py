"""Required Local Web network-boundary regressions."""

from __future__ import annotations

import pytest

from app.core.config import AppEnv, settings
from app.main import _check_runtime_config, _validate_loopback_host


@pytest.mark.required
def test_all_interface_host_is_not_loopback() -> None:
    with pytest.raises(ValueError, match="LOCAL_NETWORK_BOUNDARY_VIOLATION"):
        _validate_loopback_host("0.0.0.0")


@pytest.mark.required
def test_production_runtime_fails_closed_on_all_interface_host(monkeypatch) -> None:
    monkeypatch.setattr(settings, "host", "0.0.0.0")
    monkeypatch.setattr(settings, "app_env", AppEnv.PRODUCTION)

    with pytest.raises(RuntimeError, match="LOCAL_NETWORK_BOUNDARY_VIOLATION"):
        _check_runtime_config()

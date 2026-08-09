"""Traceability: MODEL-CONFIG-040/052/053 and SEC-AC-203/204."""

from __future__ import annotations

import json

import pytest
from starlette.requests import Request

from app import main
from app.core.config import settings
from app.main import _desktop_model_probe, app

CONTROL_TOKEN = "iBES5Q6GuksaCWeXzMV2aaybqxeTeM0OW8QVvJYddvzhhzzvqr15qIEPxKeMdfO9"


def _request(payload: dict, token: str, host: str = "127.0.0.1") -> Request:
    body = json.dumps(payload).encode()
    delivered = False

    async def receive():
        nonlocal delivered
        if delivered:
            return {"type": "http.disconnect"}
        delivered = True
        return {"type": "http.request", "body": body, "more_body": False}

    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/_desktop/model-configuration/probe",
        "raw_path": b"/_desktop/model-configuration/probe",
        "query_string": b"",
        "headers": [(b"x-askora-desktop-control", token.encode())],
        "client": (host, 3210),
        "server": ("127.0.0.1", 8765),
        "state": {"request_id": "security-probe"},
    }
    return Request(scope, receive)


@pytest.mark.asyncio
async def test_control_probe_rejects_bad_token_without_echo(monkeypatch) -> None:
    monkeypatch.setattr(settings, "desktop_control_token", CONTROL_TOKEN)
    secret = "candidate-secret-key"

    response = await _desktop_model_probe(
        _request(
            {
                "schema_version": "1.0",
                "provider": "zhipu",
                "model": "glm-4.7-flash",
                "api_key": secret,
            },
            "wrong-token",
        )
    )

    assert response.status_code == 404
    assert secret.encode() not in response.body
    assert b"wrong-token" not in response.body


@pytest.mark.asyncio
async def test_validation_error_never_echoes_candidate_secret(monkeypatch) -> None:
    token = CONTROL_TOKEN
    monkeypatch.setattr(settings, "desktop_control_token", token)
    secret = "candidate-secret-key"

    response = await _desktop_model_probe(
        _request(
            {
                "schema_version": "1.0",
                "provider": "zhipu",
                "model": "not-allowed",
                "api_key": secret,
                "unexpected": secret,
            },
            token,
        )
    )

    assert response.status_code == 422
    assert secret.encode() not in response.body
    assert b"not-allowed" not in response.body


def test_desktop_control_route_is_absent_from_openapi_and_test_mode() -> None:
    assert "/_desktop/model-configuration/probe" not in app.openapi()["paths"]
    assert all(
        getattr(route, "path", None) != "/_desktop/model-configuration/probe"
        for route in app.routes
    )


def test_desktop_control_token_rejects_low_entropy_and_accepts_electron_format() -> None:
    """MODEL-CONFIG-052: token must be a high-entropy Electron base64url value."""
    validator = getattr(main, "_is_high_entropy_desktop_control_token", lambda _token: False)

    assert validator("a" * 32) is False
    assert validator("a" * 64) is False
    assert validator(CONTROL_TOKEN) is True

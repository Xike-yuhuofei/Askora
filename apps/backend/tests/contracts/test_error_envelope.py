"""ERROR-002 is emitted for handled and unhandled HTTP failures."""

from __future__ import annotations

import json

import pytest
from starlette.requests import Request

from app.core.exceptions import BusinessError
from app.main import app_error_handler, global_exception_handler


def _request(request_id: str) -> Request:
    request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})
    request.state.request_id = request_id
    return request


@pytest.mark.asyncio
async def test_app_error_has_complete_machine_envelope() -> None:
    response = await app_error_handler(
        _request("corr-rate"),
        BusinessError(
            message="rate limited",
            error_code="AI_PROVIDER_RATE_LIMITED",
            status_code=429,
            category="transient",
            retryable=True,
            recovery={"issue_ref": "provider:a", "retry_after_seconds": 12, "actions": []},
        ),
    )
    error = json.loads(response.body)["error"]
    assert error == {
        "code": "AI_PROVIDER_RATE_LIMITED",
        "message": "rate limited",
        "request_id": "corr-rate",
        "category": "transient",
        "retryable": True,
        "correlation_id": "corr-rate",
        "details": None,
        "recovery": {
            "issue_ref": "provider:a",
            "retry_after_seconds": 12,
            "actions": [],
        },
    }


@pytest.mark.asyncio
async def test_unhandled_error_is_nonretryable_and_hides_exception() -> None:
    response = await global_exception_handler(_request("corr-internal"), RuntimeError("secret"))
    serialized = json.loads(response.body)
    assert serialized["error"]["category"] == "internal"
    assert serialized["error"]["retryable"] is False
    assert serialized["error"]["correlation_id"] == "corr-internal"
    assert "secret" not in response.body.decode()

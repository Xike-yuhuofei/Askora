"""Traceability: MODEL-CONFIG-050/051/053/080 and MODEL-CONFIG-AC-003/006/007."""

from __future__ import annotations

import httpx
import pytest

from app.contracts.model_configuration import ModelConfigCandidateV1
from app.orchestration import model_configuration
from app.services.llm.model_router import LLMResponse


class _FakeProvider:
    def __init__(self, response: LLMResponse | None = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.messages = []
        self.temperature = None
        self.max_tokens = None
        self.closed = False

    async def chat_completion(self, messages, temperature=None, max_tokens=None):
        self.messages = messages
        self.temperature = temperature
        self.max_tokens = max_tokens
        if self.error:
            raise self.error
        assert self.response is not None
        return self.response

    async def close(self) -> None:
        self.closed = True


def _candidate() -> ModelConfigCandidateV1:
    return ModelConfigCandidateV1.model_validate(
        {
            "schema_version": "1.0",
            "provider": "zhipu",
            "model": "glm-4.7-flash",
            "api_key": "candidate-secret-key",
        }
    )


@pytest.mark.asyncio
async def test_probe_uses_only_fixed_synthetic_prompt_and_no_fallback(monkeypatch) -> None:
    provider = _FakeProvider(
        LLMResponse(content="ASKORA_MODEL_PROBE_OK", provider="zhipu", model="glm-4.7-flash")
    )
    captured = {}

    def factory(provider_name, *, api_key, model, timeout):
        captured.update(provider=provider_name, api_key=api_key, model=model, timeout=timeout)
        return provider

    monkeypatch.setattr(model_configuration, "create_explicit_provider", factory)

    result = await model_configuration.probe_model_configuration(
        _candidate(), correlation_id="probe-1"
    )

    assert result.ok is True
    assert result.provider.value == "zhipu"
    assert captured["api_key"] == "candidate-secret-key"
    assert provider.messages[0].content == model_configuration.PROBE_PROMPT
    assert "candidate-secret-key" not in provider.messages[0].content
    assert provider.temperature == 0.0
    assert provider.max_tokens == 32
    assert provider.closed is True
    assert "candidate-secret-key" not in result.model_dump_json()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "expected_code", "retryable"),
    [
        (401, "MODEL_CREDENTIAL_REJECTED", False),
        (403, "MODEL_CREDENTIAL_REJECTED", False),
        (404, "MODEL_NOT_AVAILABLE", False),
        (429, "MODEL_RATE_LIMITED", True),
        (503, "MODEL_PROVIDER_UNAVAILABLE", True),
    ],
)
async def test_probe_maps_provider_status_without_raw_body(
    monkeypatch, status: int, expected_code: str, retryable: bool
) -> None:
    request = httpx.Request("POST", "https://provider.invalid/chat")
    response = httpx.Response(status, request=request, text="raw-secret-provider-body")
    error = httpx.HTTPStatusError("raw-secret-provider-body", request=request, response=response)
    provider = _FakeProvider(error=error)
    monkeypatch.setattr(model_configuration, "create_explicit_provider", lambda *a, **k: provider)

    with pytest.raises(model_configuration.ModelConfigurationProbeError) as exc_info:
        await model_configuration.probe_model_configuration(_candidate())

    assert exc_info.value.code == expected_code
    assert exc_info.value.retryable is retryable
    assert "raw-secret" not in exc_info.value.message
    assert provider.closed is True


@pytest.mark.asyncio
async def test_probe_timeout_has_sanitized_retryable_error(monkeypatch) -> None:
    secret = "candidate-secret-key"
    provider = _FakeProvider(error=httpx.TimeoutException("raw-secret-provider-body"))
    monkeypatch.setattr(model_configuration, "create_explicit_provider", lambda *a, **k: provider)

    with pytest.raises(model_configuration.ModelConfigurationProbeError) as exc_info:
        await model_configuration.probe_model_configuration(_candidate())

    assert exc_info.value.code == "MODEL_PROVIDER_TIMEOUT"
    assert exc_info.value.category == "transient"
    assert exc_info.value.retryable is True
    assert secret not in exc_info.value.message
    assert "raw-secret" not in exc_info.value.message
    assert provider.closed is True


@pytest.mark.asyncio
async def test_probe_rejects_empty_or_mock_response(monkeypatch) -> None:
    provider = _FakeProvider(LLMResponse(content="", provider="zhipu", model="glm-4.7-flash-mock"))
    monkeypatch.setattr(model_configuration, "create_explicit_provider", lambda *a, **k: provider)

    with pytest.raises(model_configuration.ModelConfigurationProbeError) as exc_info:
        await model_configuration.probe_model_configuration(_candidate())

    assert exc_info.value.code == "MODEL_PROVIDER_UNAVAILABLE"
    assert provider.closed is True

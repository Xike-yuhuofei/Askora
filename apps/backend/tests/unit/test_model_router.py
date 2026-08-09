from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.core.config import LLMProvider, settings
from app.services.llm.model_router import ChatMessage, ModelRouter, ZhipuProvider


class _JsonResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return {
            "choices": [{"message": {"content": "测试回答"}}],
            "usage": {
                "prompt_tokens": 3,
                "completion_tokens": 4,
                "total_tokens": 7,
            },
        }


@pytest.mark.asyncio
async def test_zhipu_chat_uses_configured_openai_compatible_endpoint(monkeypatch) -> None:
    class FakeClient:
        def __init__(self) -> None:
            self.url = ""
            self.payload: dict[str, object] = {}

        async def post(self, url: str, json: dict[str, object]) -> _JsonResponse:
            self.url = url
            self.payload = json
            return _JsonResponse()

    provider = ZhipuProvider()
    provider.api_key = "configured-test-key"
    provider.model = "glm-4.7-flash"
    provider.base_url = "https://open.bigmodel.cn/api/paas/v4"
    client = FakeClient()
    monkeypatch.setattr(provider, "_get_client", AsyncMock(return_value=client))

    response = await provider.chat_completion(
        [ChatMessage(role="user", content="你好")], temperature=0.0, max_tokens=32
    )

    assert client.url == "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    assert client.payload == {
        "model": "glm-4.7-flash",
        "messages": [{"role": "user", "content": "你好"}],
        "temperature": 0.0,
        "max_tokens": 32,
        "thinking": {"type": "disabled"},
        "stream": False,
    }
    assert response.provider == "zhipu"
    assert response.model == "glm-4.7-flash"
    assert response.content == "测试回答"
    assert response.total_tokens == 7


@pytest.mark.asyncio
async def test_zhipu_stream_parses_openai_compatible_sse(monkeypatch) -> None:
    class FakeResponse:
        async def __aenter__(self):
            return self

        async def __aexit__(self, _exc_type, _exc, _traceback) -> bool:
            return False

        def raise_for_status(self) -> None:
            return None

        async def aiter_lines(self):
            yield 'data: {"choices":[{"delta":{"content":"你"}}]}'
            yield 'data: {"choices":[{"delta":{"content":"好"}}]}'
            yield "data: [DONE]"

    class FakeClient:
        def __init__(self) -> None:
            self.url = ""
            self.payload: dict[str, object] = {}

        def stream(self, _method: str, url: str, json: dict[str, object]) -> FakeResponse:
            self.url = url
            self.payload = json
            return FakeResponse()

    provider = ZhipuProvider()
    provider.api_key = "configured-test-key"
    client = FakeClient()
    monkeypatch.setattr(provider, "_get_client", AsyncMock(return_value=client))

    chunks = [
        chunk
        async for chunk in provider.stream_chat_completion(
            [ChatMessage(role="user", content="你好")]
        )
    ]

    assert client.url.endswith("/chat/completions")
    assert client.payload["stream"] is True
    assert client.payload["thinking"] == {"type": "disabled"}
    assert client.payload["max_tokens"] == settings.llm_max_tokens
    assert "".join(chunk.content for chunk in chunks) == "你好"
    assert chunks[-1].is_final is True


def test_explicit_default_and_math_routes_select_zhipu(monkeypatch) -> None:
    monkeypatch.setattr(settings, "llm_default_provider", LLMProvider.ZHIPU)
    monkeypatch.setattr(settings, "llm_math_provider", LLMProvider.ZHIPU)
    monkeypatch.setattr(settings, "llm_zhipu_api_key", "configured-test-key")

    router = ModelRouter()

    assert isinstance(router.route_for_subject("science"), ZhipuProvider)
    assert isinstance(router.route_for_subject("数学"), ZhipuProvider)


def test_desktop_vault_route_never_silently_switches_provider(monkeypatch) -> None:
    monkeypatch.setattr(settings, "model_config_source", "DESKTOP_VAULT")
    monkeypatch.setattr(settings, "model_config_state", "ACTIVE")
    monkeypatch.setattr(settings, "llm_default_provider", LLMProvider.ZHIPU)
    monkeypatch.setattr(settings, "llm_math_provider", LLMProvider.DEEPSEEK)
    monkeypatch.setattr(settings, "llm_zhipu_api_key", "configured-test-key")
    monkeypatch.setattr(settings, "llm_deepseek_api_key", "other-key")

    router = ModelRouter()

    assert isinstance(router.get_provider("deepseek"), ZhipuProvider)
    assert isinstance(router.route_for_subject("数学"), ZhipuProvider)
    assert isinstance(router.route_for_cost("high"), ZhipuProvider)


@pytest.mark.asyncio
async def test_disabled_desktop_route_rejects_without_returning_a_mock(monkeypatch) -> None:
    """MODEL-CONFIG-070/071: disabled vault must not masquerade as a usable model."""
    monkeypatch.setattr(settings, "model_config_source", "DESKTOP_VAULT")
    monkeypatch.setattr(settings, "model_config_state", "DISABLED")
    monkeypatch.setattr(settings, "llm_default_provider", LLMProvider.ZHIPU)
    monkeypatch.setattr(settings, "llm_zhipu_api_key", "")

    router = ModelRouter()

    with pytest.raises(RuntimeError, match="MODEL_NOT_AVAILABLE"):
        await router.chat_completion_with_fallback([ChatMessage(role="user", content="测试")])


@pytest.mark.asyncio
async def test_zhipu_without_key_returns_explicit_mock_provenance() -> None:
    provider = ZhipuProvider()
    provider.api_key = ""

    response = await provider.chat_completion([ChatMessage(role="user", content="你好")])

    assert response.provider == "zhipu"
    assert response.model == "glm-4.7-flash-mock"

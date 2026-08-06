"""
模型路由层 - 多模型供应商统一接入
支持通义千问、DeepSeek、豆包等国产模型
根据学科、成本、质量自动路由
"""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator, Optional

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ChatMessage:
    """聊天消息"""

    role: str  # system | user | assistant
    content: str


@dataclass
class LLMResponse:
    """LLM 响应"""

    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0
    ttft_ms: Optional[int] = None  # 首 Token 延迟（流式）


@dataclass
class StreamChunk:
    """流式响应块"""

    content: str
    is_final: bool = False
    finish_reason: Optional[str] = None
    token_count: int = 0


class BaseLLMProvider(ABC):
    """LLM 供应商基类"""

    @abstractmethod
    async def chat_completion(
        self,
        messages: list[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """非流式对话补全"""
        pass

    @abstractmethod
    def stream_chat_completion(
        self,
        messages: list[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncGenerator[StreamChunk, None]:
        """流式对话补全"""
        raise NotImplementedError

    @abstractmethod
    async def embedding(self, text: str) -> list[float]:
        """文本嵌入"""
        pass


class QwenProvider(BaseLLMProvider):
    """通义千问（阿里云）- 主力模型"""

    def __init__(self):
        self.api_key = settings.llm_qwen_api_key
        self.model = settings.llm_qwen_model
        self.base_url = "https://dashscope.aliyuncs.com/api/v1"
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(settings.llm_timeout),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def chat_completion(
        self,
        messages: list[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        start_time = time.time()

        if not self.api_key:
            logger.warning("qwen_api_key_missing_using_mock", model=self.model)
            return self._mock_response(messages, "qwen")

        client = await self._get_client()

        payload = {
            "model": self.model,
            "input": {
                "messages": [{"role": m.role, "content": m.content} for m in messages],
            },
            "parameters": {
                "temperature": temperature or settings.llm_temperature,
                "max_tokens": max_tokens or settings.llm_max_tokens,
                "result_format": "message",
            },
        }

        try:
            response = await client.post(
                f"{self.base_url}/services/aigc/text-generation/generation",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            output = data.get("output", {})
            choices = output.get("choices", [])
            content = choices[0]["message"]["content"] if choices else ""

            usage = data.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)

            return LLMResponse(
                content=content,
                model=self.model,
                provider="qwen",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                latency_ms=int((time.time() - start_time) * 1000),
            )
        except Exception as e:
            logger.exception("qwen_chat_failed", error_type=type(e).__name__)
            raise

    async def stream_chat_completion(
        self,
        messages: list[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncGenerator[StreamChunk, None]:
        ttft_recorded = False

        if not self.api_key:
            # Mock 流式响应
            logger.warning("qwen_stream_api_key_missing_using_mock", model=self.model)
            mock_content = "这是通义千问的模拟响应。"
            for i, char in enumerate(mock_content):
                await asyncio.sleep(0.02)
                if not ttft_recorded:
                    ttft_recorded = True
                yield StreamChunk(
                    content=char,
                    is_final=(i == len(mock_content) - 1),
                    finish_reason="stop" if i == len(mock_content) - 1 else None,
                )
            return

        # 通义千问流式使用 SSE 格式。
        client = await self._get_client()
        payload = {
            "model": self.model,
            "input": {
                "messages": [{"role": m.role, "content": m.content} for m in messages],
            },
            "parameters": {
                "temperature": temperature or settings.llm_temperature,
                "max_tokens": max_tokens or settings.llm_max_tokens,
                "result_format": "message",
                "incremental_output": True,
            },
        }

        try:
            async with client.stream(
                "POST",
                f"{self.base_url}/services/aigc/text-generation/generation",
                json=payload,
                headers={"X-DashScope-SSE": "enable"},
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        data_str = line[5:].strip()
                        if data_str == "[DONE]":
                            yield StreamChunk(content="", is_final=True, finish_reason="stop")
                            return
                        try:
                            import json

                            data = json.loads(data_str)
                            output = data.get("output", {})
                            choices = output.get("choices", [])
                            if choices:
                                delta = choices[0].get("message", {}).get("content", "")
                                if delta:
                                    if not ttft_recorded:
                                        ttft_recorded = True
                                    yield StreamChunk(content=delta)
                        except (KeyError, IndexError, TypeError, ValueError) as exc:
                            logger.warning(
                                "qwen_stream_chunk_invalid",
                                error_type=type(exc).__name__,
                            )
                yield StreamChunk(content="", is_final=True, finish_reason="eof")
        except Exception as e:
            logger.exception("qwen_stream_failed", error_type=type(e).__name__)
            raise

    async def embedding(self, text: str) -> list[float]:
        if not self.api_key:
            return [0.0] * 1536  # Mock 向量

        # 该 provider 接口当前不参与 RAG；RAG 统一使用独立的 EmbeddingService。
        return [0.0] * 1536

    def _mock_response(self, messages: list[ChatMessage], model_name: str) -> LLMResponse:
        """模拟响应（未配置 API Key 时使用）"""
        last_user_msg = next((m for m in reversed(messages) if m.role == "user"), None)
        user_content = last_user_msg.content if last_user_msg else ""

        response_content = (
            f"[模拟响应 - {model_name}] 我理解你的问题是：{user_content[:50]}...\n\n"
            "这是一个很好的问题。让我们一起来思考一下。\n"
            "首先，你能告诉我你目前的理解是什么吗？"
        )

        return LLMResponse(
            content=response_content,
            model=f"{model_name}-mock",
            provider=model_name,
            input_tokens=len(user_content) // 2,
            output_tokens=len(response_content) // 2,
            total_tokens=len(user_content) // 2 + len(response_content) // 2,
            latency_ms=150,
        )


class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek - 数学专项模型"""

    def __init__(self):
        self.api_key = settings.llm_deepseek_api_key
        self.model = settings.llm_deepseek_model
        self.base_url = "https://api.deepseek.com"
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(settings.llm_timeout),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def chat_completion(
        self,
        messages: list[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        start_time = time.time()

        if not self.api_key:
            logger.warning("deepseek_api_key_missing_using_mock", model=self.model)
            return self._mock_response(messages)

        client = await self._get_client()
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature or settings.llm_temperature,
            "max_tokens": max_tokens or settings.llm_max_tokens,
            "stream": False,
        }

        try:
            response = await client.post(f"{self.base_url}/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

            choice = data["choices"][0]
            content = choice["message"]["content"]
            usage = data.get("usage", {})

            return LLMResponse(
                content=content,
                model=self.model,
                provider="deepseek",
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                latency_ms=int((time.time() - start_time) * 1000),
            )
        except Exception as e:
            logger.exception("deepseek_chat_failed", error_type=type(e).__name__)
            raise

    async def stream_chat_completion(
        self,
        messages: list[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncGenerator[StreamChunk, None]:
        if not self.api_key:
            logger.warning("deepseek_stream_api_key_missing_using_mock", model=self.model)
            mock_content = "[模拟响应 - DeepSeek] 这是数学专项模型的模拟回答。"
            for i, char in enumerate(mock_content):
                await asyncio.sleep(0.02)
                yield StreamChunk(
                    content=char,
                    is_final=(i == len(mock_content) - 1),
                    finish_reason="stop" if i == len(mock_content) - 1 else None,
                )
            return

        # DeepSeek 使用 OpenAI 兼容的 SSE 流。
        client = await self._get_client()
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature or settings.llm_temperature,
            "max_tokens": max_tokens or settings.llm_max_tokens,
            "stream": True,
        }

        try:
            async with client.stream(
                "POST", f"{self.base_url}/chat/completions", json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        data_str = line[5:].strip()
                        if data_str == "[DONE]":
                            yield StreamChunk(content="", is_final=True, finish_reason="stop")
                            return
                        try:
                            import json

                            data = json.loads(data_str)
                            delta = data["choices"][0].get("delta", {}).get("content", "")
                            if delta:
                                yield StreamChunk(content=delta)
                        except (KeyError, IndexError, TypeError, ValueError) as exc:
                            logger.warning(
                                "deepseek_stream_chunk_invalid",
                                error_type=type(exc).__name__,
                            )
                yield StreamChunk(content="", is_final=True, finish_reason="eof")
        except Exception as e:
            logger.exception("deepseek_stream_failed", error_type=type(e).__name__)
            raise

    async def embedding(self, text: str) -> list[float]:
        # DeepSeek 暂无 embedding API，使用 Mock
        return [0.0] * 1536

    def _mock_response(self, messages: list[ChatMessage]) -> LLMResponse:
        last_user_msg = next((m for m in reversed(messages) if m.role == "user"), None)
        user_content = last_user_msg.content if last_user_msg else ""
        response_content = (
            f"[模拟响应 - DeepSeek 数学专项] 关于你的数学问题：{user_content[:50]}...\n\n"
            "让我们用代数的方法来分析这个问题。首先，设未知数为 x..."
        )
        return LLMResponse(
            content=response_content,
            model="deepseek-chat-mock",
            provider="deepseek",
            input_tokens=len(user_content) // 2,
            output_tokens=len(response_content) // 2,
            total_tokens=len(user_content) // 2 + len(response_content) // 2,
            latency_ms=200,
        )


class DoubaoProvider(BaseLLMProvider):
    """豆包（字节跳动）- 低成本备选"""

    def __init__(self):
        self.api_key = settings.llm_doubao_api_key
        self.model = settings.llm_doubao_model
        self.base_url = "https://ark.cn-beijing.volces.com/api/v3"
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(settings.llm_timeout),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def chat_completion(
        self,
        messages: list[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        start_time = time.time()

        if not self.api_key:
            logger.warning("doubao_api_key_missing_using_mock", model=self.model)
            last_user_msg = next((m for m in reversed(messages) if m.role == "user"), None)
            user_content = last_user_msg.content if last_user_msg else ""
            response_content = (
                f"[模拟响应 - 豆包低成本备选] {user_content[:30]}... 让我们来看看这个问题。"
            )
            return LLMResponse(
                content=response_content,
                model="doubao-mock",
                provider="doubao",
                input_tokens=len(user_content) // 2,
                output_tokens=len(response_content) // 2,
                total_tokens=len(user_content) + len(response_content) // 2,
                latency_ms=180,
            )

        # 豆包 Ark 使用 OpenAI 兼容接口。
        client = await self._get_client()
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature or settings.llm_temperature,
            "max_tokens": max_tokens or settings.llm_max_tokens,
        }

        response = await client.post(f"{self.base_url}/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()

        choice = data["choices"][0]
        content = choice["message"]["content"]
        usage = data.get("usage", {})

        return LLMResponse(
            content=content,
            model=self.model,
            provider="doubao",
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            latency_ms=int((time.time() - start_time) * 1000),
        )

    async def stream_chat_completion(
        self,
        messages: list[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncGenerator[StreamChunk, None]:
        if not self.api_key:
            mock_content = "[模拟响应 - 豆包流式] 这是模拟的流式输出内容。"
            for i, char in enumerate(mock_content):
                await asyncio.sleep(0.02)
                yield StreamChunk(
                    content=char,
                    is_final=(i == len(mock_content) - 1),
                    finish_reason="stop" if i == len(mock_content) - 1 else None,
                )
            return

        client = await self._get_client()
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature or settings.llm_temperature,
            "max_tokens": max_tokens or settings.llm_max_tokens,
            "stream": True,
        }

        try:
            async with client.stream(
                "POST", f"{self.base_url}/chat/completions", json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    if data_str == "[DONE]":
                        yield StreamChunk(content="", is_final=True, finish_reason="stop")
                        return
                    try:
                        import json

                        data = json.loads(data_str)
                        delta = data["choices"][0].get("delta", {}).get("content", "")
                    except (KeyError, IndexError, TypeError, ValueError) as exc:
                        logger.warning(
                            "doubao_stream_chunk_invalid",
                            error_type=type(exc).__name__,
                        )
                        continue
                    if delta:
                        yield StreamChunk(content=delta)
                yield StreamChunk(content="", is_final=True, finish_reason="eof")
        except Exception as exc:
            logger.exception("doubao_stream_failed", error_type=type(exc).__name__)
            raise

    async def embedding(self, text: str) -> list[float]:
        return [0.0] * 1536


class ModelRouter:
    """
    模型路由器
    根据学科、成本、质量、可用性自动选择最优模型
    """

    def __init__(self):
        self._providers: dict[str, BaseLLMProvider] = {
            "qwen": QwenProvider(),
            "deepseek": DeepSeekProvider(),
            "doubao": DoubaoProvider(),
        }
        self._default_provider = settings.llm_default_provider.value

    def get_provider(self, provider_name: Optional[str] = None) -> BaseLLMProvider:
        """获取指定供应商，默认使用配置的默认模型"""
        name = provider_name or self._default_provider
        if name not in self._providers:
            logger.warning("unknown_provider_fallback", provider=name)
            name = self._default_provider
        return self._providers[name]

    def route_for_subject(self, subject: str) -> BaseLLMProvider:
        """
        根据学科路由模型
        - 数学 → DeepSeek（数学推理专项）
        - 其他 → 通义千问（主力模型）
        """
        if subject and subject.lower() in {"math", "mathematics", "数学", "shuxue"}:
            # 数学优先用 DeepSeek
            if settings.llm_deepseek_api_key:
                return self._providers["deepseek"]

        return self._providers[self._default_provider]

    def route_for_cost(self, cost_sensitivity: str = "normal") -> BaseLLMProvider:
        """
        根据成本敏感度路由
        - high: 豆包（低成本）
        - normal: 通义千问
        - low: DeepSeek（高质量）
        """
        if cost_sensitivity == "high":
            return self._providers["doubao"]
        elif cost_sensitivity == "low":
            return self._providers["deepseek"]
        return self._providers[self._default_provider]

    async def chat_completion_with_fallback(
        self,
        messages: list[ChatMessage],
        subject: Optional[str] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        带降级的对话补全
        主模型失败时自动切换到备选模型
        """
        providers_to_try = [self.route_for_subject(subject or "general")]

        # 添加备选
        for p in self._providers.values():
            if p not in providers_to_try:
                providers_to_try.append(p)

        last_error = None
        for provider in providers_to_try:
            try:
                response = await provider.chat_completion(messages, **kwargs)
                return response
            except Exception as e:
                last_error = e
                provider_name = type(provider).__name__
                logger.warning(
                    "model_provider_failed",
                    provider=provider_name,
                    error_type=type(e).__name__,
                )
                continue

        # 所有供应商都失败了
        error_type = type(last_error).__name__ if last_error else "unknown"
        raise RuntimeError(f"所有 LLM 供应商均不可用（{error_type}）")

    async def close(self) -> None:
        """关闭所有供应商的连接"""
        for provider in self._providers.values():
            if hasattr(provider, "_client") and provider._client and not provider._client.is_closed:
                await provider._client.aclose()


# 全局单例
_model_router: Optional[ModelRouter] = None


def get_model_router() -> ModelRouter:
    """获取模型路由器单例"""
    global _model_router
    if _model_router is None:
        _model_router = ModelRouter()
    return _model_router

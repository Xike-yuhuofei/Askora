"""Isolated real-provider probe and sanitized runtime projection for SYS08."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from time import monotonic

import httpx

from app.contracts.model_configuration import (
    ModelConfigCandidateV1,
    ModelConfigErrorCategory,
    ModelConfigErrorCode,
    ModelConfigProvider,
    ModelConfigSource,
    ModelConfigState,
    ModelProbeResultV1,
    ModelRouteProfileSummaryV1,
)
from app.core.config import settings
from app.services.llm.model_router import ChatMessage, create_explicit_provider

PROBE_PROMPT = "Reply with exactly: ASKORA_MODEL_PROBE_OK"
PROBE_TIMEOUT_SECONDS = 12.0
PROBE_MAX_TOKENS = 32


@dataclass(frozen=True)
class ModelConfigurationProbeError(Exception):
    code: ModelConfigErrorCode
    category: ModelConfigErrorCategory
    message: str
    retryable: bool


def _map_provider_error(exc: Exception) -> ModelConfigurationProbeError:
    if isinstance(exc, (httpx.TimeoutException, TimeoutError, asyncio.TimeoutError)):
        return ModelConfigurationProbeError(
            ModelConfigErrorCode.MODEL_PROVIDER_TIMEOUT,
            ModelConfigErrorCategory.TRANSIENT,
            "模型连接测试超时",
            True,
        )
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        if status in {401, 403}:
            return ModelConfigurationProbeError(
                ModelConfigErrorCode.MODEL_CREDENTIAL_REJECTED,
                ModelConfigErrorCategory.AUTHORIZATION,
                "API Key 未获 provider 接受",
                False,
            )
        if status == 404:
            return ModelConfigurationProbeError(
                ModelConfigErrorCode.MODEL_NOT_AVAILABLE,
                ModelConfigErrorCategory.DEPENDENCY,
                "所选模型不可用或账户无访问权限",
                False,
            )
        if status == 429:
            return ModelConfigurationProbeError(
                ModelConfigErrorCode.MODEL_RATE_LIMITED,
                ModelConfigErrorCategory.TRANSIENT,
                "Provider 暂时限制了请求频率",
                True,
            )
        if status >= 500:
            return ModelConfigurationProbeError(
                ModelConfigErrorCode.MODEL_PROVIDER_UNAVAILABLE,
                ModelConfigErrorCategory.DEPENDENCY,
                "Provider 服务暂时不可用",
                True,
            )
    if isinstance(exc, (httpx.NetworkError, OSError)):
        return ModelConfigurationProbeError(
            ModelConfigErrorCode.MODEL_PROVIDER_UNAVAILABLE,
            ModelConfigErrorCategory.DEPENDENCY,
            "无法连接到 provider",
            True,
        )
    return ModelConfigurationProbeError(
        ModelConfigErrorCode.MODEL_PROVIDER_UNAVAILABLE,
        ModelConfigErrorCategory.DEPENDENCY,
        "模型连接测试失败",
        True,
    )


async def probe_model_configuration(
    candidate: ModelConfigCandidateV1,
    *,
    correlation_id: str | None = None,
) -> ModelProbeResultV1:
    """MODEL-CONFIG-050/051: probe one explicit candidate with no fallback or persistence."""

    provider = create_explicit_provider(
        candidate.provider.value,
        api_key=candidate.api_key.get_secret_value(),
        model=candidate.model,
        timeout=PROBE_TIMEOUT_SECONDS,
    )
    started = monotonic()
    try:
        response = await asyncio.wait_for(
            provider.chat_completion(
                [ChatMessage(role="user", content=PROBE_PROMPT)],
                temperature=0.0,
                max_tokens=PROBE_MAX_TOKENS,
            ),
            timeout=PROBE_TIMEOUT_SECONDS,
        )
        if (
            not response.content.strip()
            or response.provider != candidate.provider.value
            or response.model != candidate.model
            or response.model.endswith("-mock")
        ):
            raise ModelConfigurationProbeError(
                ModelConfigErrorCode.MODEL_PROVIDER_UNAVAILABLE,
                ModelConfigErrorCategory.DEPENDENCY,
                "Provider 未返回可验证的真实模型响应",
                True,
            )
        return ModelProbeResultV1(
            provider=candidate.provider,
            model=candidate.model,
            latency_ms=int((monotonic() - started) * 1000),
            correlation_id=correlation_id,
        )
    except ModelConfigurationProbeError:
        raise
    except Exception as exc:
        raise _map_provider_error(exc) from None
    finally:
        await provider.close()


def get_runtime_model_config_summary() -> ModelRouteProfileSummaryV1:
    """Return only the active runtime projection; never expose credentials."""

    source_raw = settings.model_config_source.upper()
    if source_raw == ModelConfigSource.DESKTOP_VAULT.value:
        source = ModelConfigSource.DESKTOP_VAULT
    elif source_raw == ModelConfigSource.NONE.value:
        source = ModelConfigSource.NONE
    else:
        source = ModelConfigSource.EXTERNAL_ENVIRONMENT

    if settings.model_config_state.upper() == ModelConfigState.DISABLED.value:
        return ModelRouteProfileSummaryV1(
            revision=settings.model_config_revision,
            state=ModelConfigState.DISABLED,
            provider=None,
            model=None,
            source=ModelConfigSource.DESKTOP_VAULT,
            verified_at=_parse_verified_at(settings.model_config_verified_at),
            runtime_ready=False,
            runtime_revision=settings.model_config_revision,
            reason_codes=["MODEL_CONFIGURATION_DISABLED"],
        )

    provider = settings.llm_default_provider
    model = getattr(settings, f"llm_{provider.value}_model")
    api_key = getattr(settings, f"llm_{provider.value}_api_key")
    ready = bool(api_key)
    if source == ModelConfigSource.DESKTOP_VAULT:
        state = ModelConfigState.ACTIVE if ready else ModelConfigState.DEGRADED
    else:
        state = ModelConfigState.EXTERNAL_READ_ONLY if ready else ModelConfigState.UNCONFIGURED
    return ModelRouteProfileSummaryV1(
        revision=settings.model_config_revision,
        state=state,
        provider=ModelConfigProvider(provider.value) if ready else None,
        model=model if ready else None,
        source=source if ready or source == ModelConfigSource.DESKTOP_VAULT else ModelConfigSource.NONE,
        verified_at=_parse_verified_at(settings.model_config_verified_at),
        runtime_ready=ready,
        runtime_revision=settings.model_config_revision,
        reason_codes=[] if ready else ["MODEL_CREDENTIAL_MISSING"],
    )


def _parse_verified_at(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo is not None and parsed.utcoffset() is not None else None
    except ValueError:
        return None

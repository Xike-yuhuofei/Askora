"""Typed provider failure classification for ERROR/RECOVERY contracts."""

from __future__ import annotations

from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class ProviderFailure:
    code: str
    retryable: bool
    retry_after_seconds: int | None = None


def classify_provider_failure(exc: BaseException) -> ProviderFailure:
    """Classify by typed exception/status; never branch on provider message text."""
    if isinstance(exc, httpx.TimeoutException):
        return ProviderFailure("AI_PROVIDER_TIMEOUT", True)
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        if status in {401, 403}:
            return ProviderFailure("AI_PROVIDER_KEY_INVALID", False)
        if status == 429:
            retry_after = exc.response.headers.get("retry-after")
            seconds = int(retry_after) if retry_after and retry_after.isdigit() else None
            return ProviderFailure("AI_PROVIDER_RATE_LIMITED", True, seconds)
        if status == 404:
            return ProviderFailure("AI_MODEL_UNAVAILABLE", False)
        if status >= 500:
            return ProviderFailure("AI_MODEL_UNAVAILABLE", True)
    if isinstance(exc, httpx.RequestError):
        return ProviderFailure("AI_MODEL_UNAVAILABLE", True)
    return ProviderFailure("AI_MODEL_UNAVAILABLE", True)

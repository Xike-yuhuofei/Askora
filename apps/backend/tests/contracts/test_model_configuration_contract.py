"""Traceability: MODEL-CONFIG-010/011/020 and MODEL-CONFIG-AC-002/004/005."""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.contracts.model_configuration import (
    ModelConfigCandidateV1,
    ModelConfigErrorV1,
    ModelProbeResultV1,
)
from app.core.config import LLMProvider, settings
from app.orchestration.model_configuration import get_runtime_model_config_summary


def test_candidate_is_versioned_strict_and_secret_masked() -> None:
    candidate = ModelConfigCandidateV1.model_validate(
        {
            "schema_version": "1.0",
            "provider": "zhipu",
            "model": "glm-4.7-flash",
            "api_key": "secret-test-key",
        }
    )

    assert "secret-test-key" not in repr(candidate)
    assert "secret-test-key" not in candidate.model_dump_json()
    with pytest.raises(ValidationError):
        ModelConfigCandidateV1.model_validate(
            {
                "schema_version": "1.0",
                "provider": "zhipu",
                "model": "unapproved-model",
                "api_key": "secret-test-key",
            }
        )
    with pytest.raises(ValidationError):
        ModelConfigCandidateV1.model_validate(
            {
                "schema_version": "2.0",
                "provider": "zhipu",
                "model": "glm-4.7-flash",
                "api_key": "secret-test-key",
            }
        )


def test_public_model_configuration_contracts_are_immutable_and_timezone_aware() -> None:
    """MODEL-CONFIG-010: versioned public contracts cannot be mutated or carry naive time."""
    candidate = ModelConfigCandidateV1.model_validate(
        {
            "schema_version": "1.0",
            "provider": "zhipu",
            "model": "glm-4.7-flash",
            "api_key": "secret-test-key",
        }
    )

    with pytest.raises(ValidationError):
        candidate.model = "another-model"
    with pytest.raises(ValidationError):
        ModelProbeResultV1(
            provider="zhipu",
            model="glm-4.7-flash",
            latency_ms=1,
            tested_at=datetime(2026, 8, 9, 12, 0, 0),
        )


def test_model_configuration_error_uses_stable_code_and_category_enums() -> None:
    """MODEL-CONFIG-080: external error taxonomy cannot drift into arbitrary strings."""
    with pytest.raises(ValidationError):
        ModelConfigErrorV1(
            code="MODEL_SOMETHING_NEW",
            category="unexpected",
            message="not used",
            retryable=False,
        )


def test_runtime_summary_uses_exact_default_route_not_any_configured_key(monkeypatch) -> None:
    monkeypatch.setattr(settings, "model_config_source", "DESKTOP_VAULT")
    monkeypatch.setattr(settings, "model_config_state", "ACTIVE")
    monkeypatch.setattr(settings, "model_config_revision", 7)
    monkeypatch.setattr(settings, "model_config_verified_at", "2026-08-09T04:00:00Z")
    monkeypatch.setattr(settings, "llm_default_provider", LLMProvider.ZHIPU)
    monkeypatch.setattr(settings, "llm_zhipu_api_key", "")
    monkeypatch.setattr(settings, "llm_qwen_api_key", "some-other-key")

    summary = get_runtime_model_config_summary()

    assert summary.runtime_ready is False
    assert summary.state.value == "DEGRADED"
    assert summary.provider is None
    assert summary.runtime_revision == 7
    assert "some-other-key" not in summary.model_dump_json()


def test_active_runtime_summary_projects_exact_desktop_route(monkeypatch) -> None:
    """MODEL-CONFIG-010/002: health projection is the active exact runtime route."""
    monkeypatch.setattr(settings, "model_config_source", "DESKTOP_VAULT")
    monkeypatch.setattr(settings, "model_config_state", "ACTIVE")
    monkeypatch.setattr(settings, "model_config_revision", 9)
    monkeypatch.setattr(settings, "model_config_verified_at", "2026-08-09T04:00:00Z")
    monkeypatch.setattr(settings, "llm_default_provider", LLMProvider.ZHIPU)
    monkeypatch.setattr(settings, "llm_zhipu_model", "glm-4.7-flash")
    monkeypatch.setattr(settings, "llm_zhipu_api_key", "configured-test-key")

    summary = get_runtime_model_config_summary()

    assert summary.state.value == "ACTIVE"
    assert summary.source.value == "DESKTOP_VAULT"
    assert summary.provider.value == "zhipu"
    assert summary.model == "glm-4.7-flash"
    assert summary.revision == 9
    assert summary.runtime_revision == 9
    assert summary.runtime_ready is True


def test_disabled_tombstone_is_not_external_fallback(monkeypatch) -> None:
    monkeypatch.setattr(settings, "model_config_source", "DESKTOP_VAULT")
    monkeypatch.setattr(settings, "model_config_state", "DISABLED")
    monkeypatch.setattr(settings, "model_config_revision", 8)
    monkeypatch.setattr(settings, "llm_qwen_api_key", "inherited-env-key")

    summary = get_runtime_model_config_summary()

    assert summary.state.value == "DISABLED"
    assert summary.source.value == "DESKTOP_VAULT"
    assert summary.provider is None
    assert summary.runtime_ready is False
    assert summary.runtime_revision == 8

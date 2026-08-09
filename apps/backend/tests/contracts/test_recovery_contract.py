"""P1-07 strict recovery contract and stable provider catalog tests."""

from datetime import datetime, timezone

import httpx
import pytest
from pydantic import ValidationError

from app.contracts.recovery import (
    RECOVERY_CATALOG,
    RECOVERY_CATALOG_VERSION,
    BootstrapDiagnosticV1,
    RecoveryActionV1,
    RecoveryCategory,
    RecoveryCommandV1,
    RecoveryIssueViewV1,
)
from app.services.llm.provider_errors import classify_provider_failure

NOW = datetime(2026, 8, 9, 5, 0, tzinfo=timezone.utc)


def test_recovery_contract_is_strict_versioned_and_path_free() -> None:
    issue = RecoveryIssueViewV1(
        issue_ref="provider:activity-1",
        issue_version=1,
        code="AI_PROVIDER_TIMEOUT",
        category=RecoveryCategory.TRANSIENT,
        severity="blocking",
        status="waiting",
        title="模型响应超时",
        summary="本轮未被接纳。",
        data_safety="preserved",
        duplicate_risk="prevented_by_idempotency",
        source_system="SYS08",
        resource_ref="activity:activity-1",
        retry_budget=3,
        actions=(
            RecoveryActionV1(
                action_code="wait_until",
                label="等待后再试",
                kind="wait",
                enabled=True,
            ),
        ),
        opened_at=NOW,
        updated_at=NOW,
    )
    payload = issue.model_dump(mode="json")
    assert payload["schema_version"] == "1.0"
    assert not any("/Users/" in str(value) for value in payload.values())

    with pytest.raises(ValidationError):
        RecoveryCommandV1.model_validate(
            {
                "schema_version": "2.0",
                "issue_ref": issue.issue_ref,
                "expected_issue_version": 1,
                "action_code": "wait_until",
                "idempotency_key": "command-1",
            }
        )
    with pytest.raises(ValidationError):
        RecoveryIssueViewV1.model_validate({**payload, "unexpected": True})
    with pytest.raises(ValidationError):
        RecoveryIssueViewV1.model_validate(
            {**payload, "opened_at": "2026-08-09T05:00:00", "updated_at": NOW.isoformat()}
        )
    with pytest.raises(ValidationError):
        RecoveryIssueViewV1.model_validate({**payload, "category": "dependency"})


def test_stable_catalog_covers_every_p107_runtime_code() -> None:
    assert RECOVERY_CATALOG_VERSION == "1.0"
    assert set(RECOVERY_CATALOG) == {
        "AI_PROVIDER_TIMEOUT",
        "AI_PROVIDER_RATE_LIMITED",
        "AI_PROVIDER_KEY_INVALID",
        "AI_PROVIDER_KEY_MISSING",
        "AI_MODEL_UNAVAILABLE",
        "AI_OUTPUT_VALIDATION_FAILED",
        "CONTENT_PROCESSING_FAILED",
        "CONTENT_QUARANTINED",
        "CONTENT_FILE_MISSING",
        "CONTENT_OCR_REVIEW_REQUIRED",
        "DATABASE_UNAVAILABLE",
        "DATABASE_MIGRATION_REQUIRED",
        "DATABASE_INTEGRITY_FAILED",
        "OUTBOX_RETRY_WAITING",
        "OUTBOX_RETRY_EXHAUSTED",
        "OUTBOX_HANDLER_UNAVAILABLE",
    }
    assert all(entry.allowed_actions for entry in RECOVERY_CATALOG.values())


def test_bootstrap_contract_is_backend_independent_and_sanitized() -> None:
    diagnostic = BootstrapDiagnosticV1(
        status="failed",
        code="BOOTSTRAP_DATABASE_MIGRATION_REQUIRED",
        data_safety="preserved",
        retryable=True,
        attempt=2,
        started_at=NOW,
        updated_at=NOW,
        exit_code=78,
        actions=("retry_backend", "copy_diagnostics"),
    )
    assert set(diagnostic.model_dump()) == {
        "schema_version",
        "status",
        "code",
        "data_safety",
        "retryable",
        "attempt",
        "started_at",
        "updated_at",
        "exit_code",
        "actions",
    }


def test_provider_failures_use_typed_status_not_message_matching() -> None:
    request = httpx.Request("POST", "https://provider.invalid/chat")
    rate_response = httpx.Response(429, headers={"retry-after": "17"}, request=request)
    rate = classify_provider_failure(
        httpx.HTTPStatusError("any text", request=request, response=rate_response)
    )
    assert (rate.code, rate.retryable, rate.retry_after_seconds) == (
        "AI_PROVIDER_RATE_LIMITED",
        True,
        17,
    )

    auth_response = httpx.Response(401, request=request)
    auth = classify_provider_failure(
        httpx.HTTPStatusError("completely different text", request=request, response=auth_response)
    )
    assert (auth.code, auth.retryable) == ("AI_PROVIDER_KEY_INVALID", False)
    assert classify_provider_failure(httpx.ReadTimeout("slow", request=request)).code == (
        "AI_PROVIDER_TIMEOUT"
    )

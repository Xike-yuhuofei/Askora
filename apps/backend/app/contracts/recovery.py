"""P1-07 strict recovery query/control-plane contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Literal, Mapping

from pydantic import model_validator

from app.contracts.base import ContractModel


class RecoveryCategory(StrEnum):
    DEPENDENCY = "dependency"
    TRANSIENT = "transient"
    CONFLICT = "conflict"
    SECURITY = "security"
    DATA_INTEGRITY = "data_integrity"
    INTERNAL = "internal"


RecoveryActionCode = Literal[
    "retry_owner_command",
    "reinspect_document",
    "open_model_settings",
    "open_data_recovery",
    "open_activity",
    "reselect_file",
    "wait_until",
    "copy_diagnostics",
    "acknowledge",
]


@dataclass(frozen=True)
class RecoveryCatalogEntry:
    """Single server-owned policy entry for one stable recovery code."""

    category: RecoveryCategory
    data_safety: Literal["preserved", "preserved_but_unavailable", "at_risk", "unknown"]
    retry_policy: Literal["none", "automatic", "manual", "navigation"]
    allowed_actions: frozenset[RecoveryActionCode]


RECOVERY_CATALOG_VERSION = "1.0"
RECOVERY_CATALOG: Mapping[str, RecoveryCatalogEntry] = MappingProxyType(
    {
        "AI_PROVIDER_TIMEOUT": RecoveryCatalogEntry(
            RecoveryCategory.TRANSIENT,
            "preserved",
            "manual",
            frozenset({"wait_until", "copy_diagnostics", "open_activity"}),
        ),
        "AI_PROVIDER_RATE_LIMITED": RecoveryCatalogEntry(
            RecoveryCategory.TRANSIENT,
            "preserved",
            "automatic",
            frozenset({"wait_until", "copy_diagnostics", "open_activity"}),
        ),
        "AI_PROVIDER_KEY_INVALID": RecoveryCatalogEntry(
            RecoveryCategory.DEPENDENCY,
            "preserved",
            "navigation",
            frozenset({"open_model_settings", "open_activity"}),
        ),
        "AI_PROVIDER_KEY_MISSING": RecoveryCatalogEntry(
            RecoveryCategory.DEPENDENCY,
            "preserved",
            "navigation",
            frozenset({"open_model_settings", "open_activity"}),
        ),
        "AI_MODEL_UNAVAILABLE": RecoveryCatalogEntry(
            RecoveryCategory.DEPENDENCY,
            "preserved",
            "navigation",
            frozenset({"open_model_settings", "copy_diagnostics", "open_activity"}),
        ),
        "AI_OUTPUT_VALIDATION_FAILED": RecoveryCatalogEntry(
            RecoveryCategory.INTERNAL,
            "preserved",
            "none",
            frozenset({"copy_diagnostics", "open_activity"}),
        ),
        "CONTENT_PROCESSING_FAILED": RecoveryCatalogEntry(
            RecoveryCategory.TRANSIENT,
            "preserved",
            "manual",
            frozenset({"retry_owner_command", "copy_diagnostics"}),
        ),
        "CONTENT_QUARANTINED": RecoveryCatalogEntry(
            RecoveryCategory.SECURITY,
            "preserved_but_unavailable",
            "manual",
            frozenset({"reinspect_document", "wait_until", "copy_diagnostics"}),
        ),
        "CONTENT_FILE_MISSING": RecoveryCatalogEntry(
            RecoveryCategory.DATA_INTEGRITY,
            "preserved_but_unavailable",
            "navigation",
            frozenset({"open_data_recovery", "reselect_file"}),
        ),
        "CONTENT_OCR_REVIEW_REQUIRED": RecoveryCatalogEntry(
            RecoveryCategory.CONFLICT,
            "preserved_but_unavailable",
            "navigation",
            frozenset({"copy_diagnostics"}),
        ),
        "DATABASE_UNAVAILABLE": RecoveryCatalogEntry(
            RecoveryCategory.DEPENDENCY,
            "unknown",
            "none",
            frozenset({"copy_diagnostics"}),
        ),
        "DATABASE_MIGRATION_REQUIRED": RecoveryCatalogEntry(
            RecoveryCategory.CONFLICT,
            "preserved",
            "none",
            frozenset({"open_data_recovery", "copy_diagnostics"}),
        ),
        "DATABASE_INTEGRITY_FAILED": RecoveryCatalogEntry(
            RecoveryCategory.DATA_INTEGRITY,
            "unknown",
            "none",
            frozenset({"open_data_recovery", "copy_diagnostics"}),
        ),
        "OUTBOX_RETRY_WAITING": RecoveryCatalogEntry(
            RecoveryCategory.TRANSIENT,
            "preserved",
            "automatic",
            frozenset({"wait_until"}),
        ),
        "OUTBOX_RETRY_EXHAUSTED": RecoveryCatalogEntry(
            RecoveryCategory.TRANSIENT,
            "preserved",
            "manual",
            frozenset({"retry_owner_command", "copy_diagnostics"}),
        ),
        "OUTBOX_HANDLER_UNAVAILABLE": RecoveryCatalogEntry(
            RecoveryCategory.INTERNAL,
            "preserved",
            "none",
            frozenset({"copy_diagnostics"}),
        ),
    }
)


def recovery_catalog_entry(code: str) -> RecoveryCatalogEntry:
    try:
        return RECOVERY_CATALOG[code]
    except KeyError as exc:
        raise ValueError(f"unknown recovery code: {code}") from exc


class RecoveryActionV1(ContractModel):
    action_code: RecoveryActionCode
    label: str
    kind: Literal["command", "navigate", "wait", "client"]
    enabled: bool
    disabled_reason_code: str | None = None
    endpoint: str | None = None
    method: Literal["POST"] | None = None
    route: str | None = None
    requires_idempotency_key: bool = False
    requires_confirmation: bool = False


class RecoveryIssueViewV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    issue_ref: str
    issue_version: int
    code: str
    category: RecoveryCategory
    severity: Literal["info", "warning", "blocking"]
    status: Literal["active", "waiting", "action_running", "resolved"]
    title: str
    summary: str
    data_safety: Literal["preserved", "preserved_but_unavailable", "at_risk", "unknown"]
    duplicate_risk: Literal[
        "none", "prevented_by_idempotency", "requires_confirmation", "not_applicable"
    ]
    source_system: Literal["SYS01", "SYS08", "BOOTSTRAP", "DATA_CONTROL"]
    resource_ref: str | None = None
    correlation_id: str | None = None
    attempt_count: int = 0
    retry_budget: int | None = None
    next_eligible_at: datetime | None = None
    actions: tuple[RecoveryActionV1, ...] = ()
    opened_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def enforce_catalog_policy(self) -> RecoveryIssueViewV1:
        entry = recovery_catalog_entry(self.code)
        if self.category != entry.category:
            raise ValueError("recovery category does not match stable catalog")
        if self.data_safety != entry.data_safety:
            raise ValueError("recovery data safety does not match stable catalog")
        action_codes = {action.action_code for action in self.actions}
        if not action_codes.issubset(entry.allowed_actions):
            raise ValueError("recovery action is not allowed by stable catalog")
        return self


class RecoveryIssueListResponseV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    generated_at: datetime
    issues: tuple[RecoveryIssueViewV1, ...]
    active_count: int
    correlation_id: str


class RecoveryCommandV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    issue_ref: str
    expected_issue_version: int
    action_code: str
    idempotency_key: str


class RecoveryResultV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    result_ref: str
    issue_ref: str
    status: Literal["accepted", "already_applied", "waiting", "succeeded", "failed"]
    issue_version: int
    owner_command_ref: str | None = None
    replacement_task_ref: str | None = None
    message: str
    correlation_id: str
    completed_at: datetime


class BootstrapDiagnosticV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    status: Literal["starting", "ready", "failed"]
    code: str | None = None
    data_safety: Literal["preserved", "unknown"]
    retryable: bool
    attempt: int
    started_at: datetime | None = None
    updated_at: datetime
    exit_code: int | None = None
    actions: tuple[Literal["retry_backend", "copy_diagnostics"], ...] = ()

"""SYS08 desktop model configuration contracts (MODEL-CONFIG-010/011/080)."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator, model_validator


class ModelConfigProvider(str, Enum):
    QWEN = "qwen"
    DEEPSEEK = "deepseek"
    DOUBAO = "doubao"
    ZHIPU = "zhipu"


SUPPORTED_MODELS: dict[ModelConfigProvider, tuple[str, ...]] = {
    ModelConfigProvider.QWEN: ("qwen-turbo",),
    ModelConfigProvider.DEEPSEEK: ("deepseek-chat",),
    ModelConfigProvider.DOUBAO: ("doubao-pro-32k",),
    ModelConfigProvider.ZHIPU: ("glm-4.7-flash",),
}


class ModelConfigSource(str, Enum):
    DESKTOP_VAULT = "DESKTOP_VAULT"
    EXTERNAL_ENVIRONMENT = "EXTERNAL_ENVIRONMENT"
    NONE = "NONE"


class ModelConfigState(str, Enum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    EXTERNAL_READ_ONLY = "EXTERNAL_READ_ONLY"
    UNCONFIGURED = "UNCONFIGURED"
    DEGRADED = "DEGRADED"


class ModelConfigErrorCode(str, Enum):
    MODEL_CONTROL_NOT_AVAILABLE = "MODEL_CONTROL_NOT_AVAILABLE"
    MODEL_CONFIG_STORAGE_UNAVAILABLE = "MODEL_CONFIG_STORAGE_UNAVAILABLE"
    MODEL_CONFIG_SCHEMA_UNSUPPORTED = "MODEL_CONFIG_SCHEMA_UNSUPPORTED"
    MODEL_CONFIG_REVISION_CONFLICT = "MODEL_CONFIG_REVISION_CONFLICT"
    MODEL_CREDENTIAL_REJECTED = "MODEL_CREDENTIAL_REJECTED"
    MODEL_NOT_AVAILABLE = "MODEL_NOT_AVAILABLE"
    MODEL_RATE_LIMITED = "MODEL_RATE_LIMITED"
    MODEL_PROVIDER_TIMEOUT = "MODEL_PROVIDER_TIMEOUT"
    MODEL_PROVIDER_UNAVAILABLE = "MODEL_PROVIDER_UNAVAILABLE"
    MODEL_CONFIG_APPLY_FAILED = "MODEL_CONFIG_APPLY_FAILED"
    MODEL_CONFIG_ROLLBACK_FAILED = "MODEL_CONFIG_ROLLBACK_FAILED"


class ModelConfigErrorCategory(str, Enum):
    SECURITY = "security"
    VALIDATION = "validation"
    CONFLICT = "conflict"
    AUTHORIZATION = "authorization"
    DEPENDENCY = "dependency"
    TRANSIENT = "transient"
    INTERNAL = "internal"


MODEL_CONFIG_ERROR_SEMANTICS: dict[ModelConfigErrorCode, tuple[ModelConfigErrorCategory, bool]] = {
    ModelConfigErrorCode.MODEL_CONTROL_NOT_AVAILABLE: (ModelConfigErrorCategory.SECURITY, False),
    ModelConfigErrorCode.MODEL_CONFIG_STORAGE_UNAVAILABLE: (
        ModelConfigErrorCategory.DEPENDENCY,
        False,
    ),
    ModelConfigErrorCode.MODEL_CONFIG_SCHEMA_UNSUPPORTED: (
        ModelConfigErrorCategory.VALIDATION,
        False,
    ),
    ModelConfigErrorCode.MODEL_CONFIG_REVISION_CONFLICT: (ModelConfigErrorCategory.CONFLICT, False),
    ModelConfigErrorCode.MODEL_CREDENTIAL_REJECTED: (
        ModelConfigErrorCategory.AUTHORIZATION,
        False,
    ),
    ModelConfigErrorCode.MODEL_NOT_AVAILABLE: (ModelConfigErrorCategory.DEPENDENCY, False),
    ModelConfigErrorCode.MODEL_RATE_LIMITED: (ModelConfigErrorCategory.TRANSIENT, True),
    ModelConfigErrorCode.MODEL_PROVIDER_TIMEOUT: (ModelConfigErrorCategory.TRANSIENT, True),
    ModelConfigErrorCode.MODEL_PROVIDER_UNAVAILABLE: (ModelConfigErrorCategory.DEPENDENCY, True),
    ModelConfigErrorCode.MODEL_CONFIG_APPLY_FAILED: (ModelConfigErrorCategory.INTERNAL, True),
    ModelConfigErrorCode.MODEL_CONFIG_ROLLBACK_FAILED: (ModelConfigErrorCategory.INTERNAL, False),
}


def model_config_error_semantics(
    code: ModelConfigErrorCode,
) -> tuple[ModelConfigErrorCategory, bool]:
    """Return the one stable category/retryable tuple for a public error code."""
    return MODEL_CONFIG_ERROR_SEMANTICS[code]


class ModelConfigCandidateV1(BaseModel):
    """Transient candidate. Its secret must never appear in a response or log."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"]
    provider: ModelConfigProvider
    model: str = Field(min_length=1, max_length=128)
    api_key: SecretStr = Field(min_length=8, max_length=4096)

    @model_validator(mode="after")
    def validate_supported_route(self) -> "ModelConfigCandidateV1":
        if self.model not in SUPPORTED_MODELS[self.provider]:
            raise ValueError("unsupported provider/model combination")
        return self


class ModelProbeResultV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"] = "1.0"
    ok: Literal[True] = True
    provider: ModelConfigProvider
    model: str
    prompt_version: Literal["model-settings-probe-v1"] = "model-settings-probe-v1"
    latency_ms: int = Field(ge=0)
    tested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: str | None = None

    @field_validator("tested_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("tested_at must be timezone-aware")
        return value


class ModelConfigErrorV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: ModelConfigErrorCode
    category: ModelConfigErrorCategory
    message: str
    retryable: bool
    correlation_id: str | None = None

    @model_validator(mode="after")
    def validate_semantics(self) -> "ModelConfigErrorV1":
        category, retryable = model_config_error_semantics(self.code)
        if (self.category, self.retryable) != (category, retryable):
            raise ValueError("code/category/retryable combination is not supported")
        return self

    @classmethod
    def for_code(
        cls,
        *,
        code: ModelConfigErrorCode,
        message: str,
        correlation_id: str | None = None,
    ) -> "ModelConfigErrorV1":
        category, retryable = model_config_error_semantics(code)
        return cls(
            code=code,
            category=category,
            message=message,
            retryable=retryable,
            correlation_id=correlation_id,
        )


class ModelRouteProfileSummaryV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"] = "1.0"
    revision: int | None
    state: ModelConfigState
    provider: ModelConfigProvider | None
    model: str | None
    source: ModelConfigSource
    verified_at: datetime | None
    runtime_ready: bool
    runtime_revision: int | None
    reason_codes: list[str] = Field(default_factory=list)

    @field_validator("verified_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("verified_at must be timezone-aware")
        return value

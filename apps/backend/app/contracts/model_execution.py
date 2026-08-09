"""SYS08 model execution metadata shared by accepted responses and transcripts."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.contracts.base import ContractModel


class ModelExecutionV1(ContractModel):
    """Minimal, replay-safe metadata; raw prompts and model output are intentionally absent."""

    schema_version: Literal["1.0"] = "1.0"
    mode: Literal["real_model", "local_fallback"]
    provider: str | None = None
    model: str | None = None
    prompt_version: str = Field(min_length=1)
    inference_id: UUID
    latency_ms: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)

    @model_validator(mode="after")
    def real_model_must_be_identifiable(self) -> ModelExecutionV1:
        if self.mode == "real_model":
            if not self.provider or not self.model or "mock" in self.model.lower():
                raise ValueError("real_model execution requires a non-mock provider and model")
        return self

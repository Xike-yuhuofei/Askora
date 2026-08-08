"""RENDER-* versioned rich-response presentation contracts."""

from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.contracts.base import ContractModel


class MarkdownBlockV1(ContractModel):
    """RENDER-011 learner-visible CommonMark/GFM/math source."""

    id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    type: Literal["markdown"] = "markdown"
    source: str = Field(min_length=1, max_length=20_000)


class CardBlockV1(ContractModel):
    """RENDER-012 non-interactive typed presentation card."""

    id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    type: Literal["card"] = "card"
    variant: Literal["concept", "hint", "question", "feedback", "source"]
    title: str = Field(min_length=1, max_length=200)
    body_markdown: str = Field(min_length=1, max_length=10_000)


class CitationItemV1(ContractModel):
    """RENDER-013 stable citation label and SourceSpan reference."""

    label: str = Field(min_length=1, max_length=300)
    source_span_id: UUID


class CitationBlockV1(ContractModel):
    """RENDER-013 learner-visible citation collection."""

    id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    type: Literal["citations"] = "citations"
    items: tuple[CitationItemV1, ...] = Field(min_length=1, max_length=20)


RenderBlockV1 = Annotated[
    MarkdownBlockV1 | CardBlockV1 | CitationBlockV1,
    Field(discriminator="type"),
]


class RenderPayloadV1(ContractModel):
    """RENDER-010 accepted, ordered SYS08 presentation artifact."""

    schema_version: Literal["1.0"] = "1.0"
    blocks: tuple[RenderBlockV1, ...] = Field(min_length=1, max_length=32)

    @model_validator(mode="after")
    def require_unique_block_ids(self) -> RenderPayloadV1:
        block_ids = [block.id for block in self.blocks]
        if len(block_ids) != len(set(block_ids)):
            raise ValueError("render block ids must be unique within a response")
        return self


def markdown_render_payload(text: str) -> RenderPayloadV1 | None:
    """RENDER-031 deterministic baseline for existing canonical reply text."""

    if not text or len(text) > 20_000:
        return None
    return RenderPayloadV1(
        blocks=(
            MarkdownBlockV1(
                id="content",
                source=text,
            ),
        )
    )

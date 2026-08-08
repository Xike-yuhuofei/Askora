"""EXEC-014 / RENDER-* public rich-response contract tests."""

from __future__ import annotations

from uuid import UUID

import pytest
from pydantic import ValidationError

from app.contracts.rendering import (
    CardBlockV1,
    CitationBlockV1,
    CitationItemV1,
    MarkdownBlockV1,
    RenderPayloadV1,
    markdown_render_payload,
)


def test_render_ac_002_deterministic_markdown_baseline() -> None:
    """RENDER-031/RENDER-AC-002: existing reply text gets one stable block."""
    first = markdown_render_payload("公式：$x^2$")
    second = markdown_render_payload("公式：$x^2$")

    assert first == second
    assert first is not None
    assert first.model_dump(mode="json") == {
        "schema_version": "1.0",
        "blocks": [
            {
                "id": "content",
                "type": "markdown",
                "source": "公式：$x^2$",
            }
        ],
    }


def test_render_ac_003_supports_markdown_five_cards_and_citations() -> None:
    """RENDER-010..013/RENDER-AC-003: only the frozen typed block union is accepted."""
    payload = RenderPayloadV1(
        blocks=(
            MarkdownBlockV1(id="body", source="# 标题"),
            *(
                CardBlockV1(
                    id=f"card-{variant}",
                    variant=variant,
                    title=variant,
                    body_markdown="正文",
                )
                for variant in ("concept", "hint", "question", "feedback", "source")
            ),
            CitationBlockV1(
                id="citations",
                items=(
                    CitationItemV1(
                        label="教材第三章",
                        source_span_id=UUID("22222222-2222-4222-8222-222222222222"),
                    ),
                ),
            ),
        )
    )

    assert [block.type for block in payload.blocks] == [
        "markdown",
        "card",
        "card",
        "card",
        "card",
        "card",
        "citations",
    ]


@pytest.mark.parametrize(
    "payload",
    [
        {"schema_version": "2.0", "blocks": [{"id": "x", "type": "markdown", "source": "x"}]},
        {"schema_version": "1.0", "blocks": [{"id": "x", "type": "video"}]},
        {
            "schema_version": "1.0",
            "blocks": [{"id": "x", "type": "markdown", "source": "x", "html": "<b>x</b>"}],
        },
        {
            "schema_version": "1.0",
            "blocks": [
                {"id": "same", "type": "markdown", "source": "one"},
                {"id": "same", "type": "markdown", "source": "two"},
            ],
        },
    ],
)
def test_render_ac_004_005_rejects_unknown_or_ambiguous_schema(payload: dict) -> None:
    """SCHEMA-003/RENDER-AC-004/005: strict validation never guesses rich semantics."""
    with pytest.raises(ValidationError):
        RenderPayloadV1.model_validate(payload)


def test_render_031_empty_reply_has_no_structured_payload() -> None:
    """RENDER-032: an empty candidate degrades without manufacturing a block."""
    assert markdown_render_payload("") is None
    assert markdown_render_payload("x" * 20_001) is None

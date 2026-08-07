"""Deterministic SYS01 revision and SourceSpan construction."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from app.contracts.content import KnowledgeUnit, MaterialRevision, SourceSpan

CONTENT_RECORD_KEY = "content_knowledge_v1"
PARSER_VERSION = "askora-parser-v1"
SEGMENTATION_VERSION = "askora-segmentation-v1"
ANCHOR_VERSION = "source-span-v1"


def build_content_revision(
    *,
    document_id: UUID,
    original_filename: str,
    file_content: bytes,
    full_text: str,
    chunks: list[str],
    previous_record: dict[str, Any] | None,
    knowledge_point_id: str | None,
    created_at: datetime | None = None,
) -> dict[str, Any]:
    """Build an immutable revision record with stable anchors (SYS01-010/041)."""
    previous = previous_record or {}
    revisions = list(previous.get("revisions", []))
    checksum = hashlib.sha256(file_content).hexdigest()
    revision_id = uuid5(document_id, f"material:{checksum}")
    if any(item.get("revision_id") == str(revision_id) for item in revisions):
        return previous

    supersedes = UUID(revisions[-1]["revision_id"]) if revisions else None
    revision = MaterialRevision(
        revision_id=revision_id,
        document_id=document_id,
        checksum=checksum,
        source_uri=None,
        parser_version=PARSER_VERSION,
        extraction_version="minimal-binding-v1",
        created_at=created_at or datetime.now(UTC),
        supersedes_revision_id=supersedes,
    )
    spans = _build_spans(revision_id=revision_id, full_text=full_text, chunks=chunks)
    knowledge_unit_id = uuid5(
        NAMESPACE_URL,
        f"askora-knowledge-unit:{document_id}:{knowledge_point_id or original_filename.lower()}",
    )
    knowledge_unit = KnowledgeUnit(
        knowledge_unit_id=knowledge_unit_id,
        revision=len(revisions) + 1,
        kind="concept",
        canonical_name=knowledge_point_id or original_filename,
        description=_first_meaningful_line(full_text) or original_filename,
        concept_ids=[],
        evidence_span_ids=[span.span_id for span in spans],
        provenance_type="source_explicit",
        confidence=1.0,
        status="published",
    )
    new_revision = {
        **revision.model_dump(mode="json"),
        "source_spans": [span.model_dump(mode="json") for span in spans],
        "knowledge_units": [knowledge_unit.model_dump(mode="json")],
        "full_text_checksum": hashlib.sha256(full_text.encode("utf-8")).hexdigest(),
    }
    return {
        "document_id": str(document_id),
        "current_revision_id": str(revision_id),
        "revisions": [*revisions, new_revision],
    }


def _build_spans(*, revision_id: UUID, full_text: str, chunks: list[str]) -> list[SourceSpan]:
    spans: list[SourceSpan] = []
    cursor = 0
    for index, text in enumerate(chunks):
        start = full_text.find(text, cursor)
        if start < 0:
            start = full_text.find(text)
        if start < 0:
            start = cursor
        end = start + len(text)
        cursor = max(cursor, end)
        page_match = re.search(r"\[Page\s+(\d+)\]", text, re.IGNORECASE)
        chapter_match = re.search(r"^#{1,6}\s+(.+)$", text, re.MULTILINE)
        span_id = uuid5(
            revision_id,
            f"span:{index}:{start}:{end}:{hashlib.sha256(text.encode()).hexdigest()}",
        )
        spans.append(
            SourceSpan(
                span_id=span_id,
                revision_id=revision_id,
                page=int(page_match.group(1)) if page_match else None,
                chapter=chapter_match.group(1).strip() if chapter_match else None,
                start_offset=start,
                end_offset=end,
                text=text,
                anchor_version=ANCHOR_VERSION,
            )
        )
    return spans


def _first_meaningful_line(text: str) -> str:
    for line in text.splitlines():
        cleaned = line.lstrip("# ").strip()
        if cleaned:
            return cleaned[:500]
    return ""

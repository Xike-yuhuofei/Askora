"""Deterministic SYS01 revision and SourceSpan construction."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast
from uuid import NAMESPACE_URL, UUID, uuid5

from app.contracts.content import (
    DocumentIR,
    DocumentNode,
    KnowledgeUnit,
    MaterialRevision,
    SourceLocator,
    SourceSpan,
)

CONTENT_RECORD_KEY = "content_knowledge_v1"
PARSER_VERSION = "askora-parser-bundle-v2"
SEGMENTATION_VERSION = "askora-segmentation-v1"
ANCHOR_VERSION = "source-span-v1"
EXTRACTION_VERSION = "deterministic-structure-v2"


def build_content_revision(
    *,
    document_id: UUID,
    original_filename: str,
    file_content: bytes,
    full_text: str,
    chunks: list[str],
    previous_record: dict[str, Any] | None,
    knowledge_point_id: str | None,
    parser_version: str = "askora-parser-v1",
    document_format: str = "text",
    document_nodes: list[dict[str, Any]] | None = None,
    root_node_local_id: str | None = None,
    created_at: datetime | None = None,
) -> dict[str, Any]:
    """Build an immutable revision record with stable anchors (SYS01-010/041)."""
    previous = previous_record or {}
    revisions = list(previous.get("revisions", []))
    checksum = hashlib.sha256(file_content).hexdigest()
    revision_id = uuid5(
        document_id,
        f"material:{checksum}:{parser_version}:{EXTRACTION_VERSION}",
    )
    if any(item.get("revision_id") == str(revision_id) for item in revisions):
        return previous

    supersedes = UUID(revisions[-1]["revision_id"]) if revisions else None
    revision = MaterialRevision(
        revision_id=revision_id,
        document_id=document_id,
        checksum=checksum,
        source_uri=None,
        parser_version=parser_version,
        extraction_version=EXTRACTION_VERSION,
        created_at=created_at or datetime.now(UTC),
        supersedes_revision_id=supersedes,
    )
    persisted_nodes, document_ir, node_local_ids = _build_document_ir(
        document_id=document_id,
        revision_id=revision_id,
        parser_version=parser_version,
        document_format=document_format,
        full_text=full_text,
        document_nodes=document_nodes or [],
        root_node_local_id=root_node_local_id,
    )
    spans = _build_spans(
        revision_id=revision_id,
        full_text=full_text,
        chunks=chunks,
        structured_nodes=document_nodes or [],
        node_local_ids=node_local_ids,
    )
    knowledge_units = _build_knowledge_units(
        document_id=document_id,
        original_filename=original_filename,
        spans=spans,
        full_text=full_text,
        knowledge_point_id=knowledge_point_id,
        revision_number=len(revisions) + 1,
    )
    new_revision = {
        **revision.model_dump(mode="json"),
        "source_spans": [span.model_dump(mode="json") for span in spans],
        "knowledge_units": [item.model_dump(mode="json") for item in knowledge_units],
        "relations": [],
        "full_text_checksum": hashlib.sha256(full_text.encode("utf-8")).hexdigest(),
        "document_ir": document_ir.model_dump(mode="json") if document_ir else None,
        "document_nodes": [node.model_dump(mode="json") for node in persisted_nodes],
    }
    return {
        "document_id": str(document_id),
        "current_revision_id": str(revision_id),
        "revisions": [*revisions, new_revision],
    }


def _build_document_ir(
    *,
    document_id: UUID,
    revision_id: UUID,
    parser_version: str,
    document_format: str,
    full_text: str,
    document_nodes: list[dict[str, Any]],
    root_node_local_id: str | None,
) -> tuple[list[DocumentNode], DocumentIR | None, dict[str, UUID]]:
    if not document_nodes or root_node_local_id is None:
        return [], None, {}

    local_ids = {
        item["local_id"]: uuid5(
            revision_id,
            f"document-node:{item['local_id']}:{item['content_hash']}",
        )
        for item in document_nodes
    }
    persisted: list[DocumentNode] = []
    cursor = 0
    for item in document_nodes:
        canonical_text = item.get("canonical_text")
        start: int | None = None
        end: int | None = None
        if isinstance(canonical_text, str) and canonical_text:
            start = full_text.find(canonical_text, cursor)
            if start < 0:
                start = full_text.find(canonical_text)
            if start >= 0:
                end = start + len(canonical_text)
                cursor = end
            else:
                start = None
        parent_local_id = item.get("parent_local_id")
        persisted.append(
            DocumentNode(
                node_id=local_ids[item["local_id"]],
                revision_id=revision_id,
                parent_node_id=(
                    local_ids.get(parent_local_id) if isinstance(parent_local_id, str) else None
                ),
                node_type=item["node_type"],
                ordinal=item["ordinal"],
                heading=item.get("heading"),
                text=item.get("text"),
                source_locator=SourceLocator.model_validate(item["source_locator"]),
                content_hash=item["content_hash"],
                metadata={
                    **item.get("metadata", {}),
                    "canonical_text": canonical_text,
                    "canonical_start_offset": start,
                    "canonical_end_offset": end,
                },
            )
        )

    structure_payload = [
        {
            "local_id": item["local_id"],
            "parent_local_id": item.get("parent_local_id"),
            "node_type": item["node_type"],
            "ordinal": item["ordinal"],
            "heading": item.get("heading"),
            "content_hash": item["content_hash"],
            "source_locator": item["source_locator"],
        }
        for item in document_nodes
    ]
    format_value = cast(
        Literal["epub", "pdf", "docx", "markdown", "text"],
        document_format,
    )
    document_ir = DocumentIR(
        document_id=document_id,
        revision_id=revision_id,
        parser_version=parser_version,
        format=format_value,
        root_node_id=local_ids[root_node_local_id],
        node_ids=[node.node_id for node in persisted],
        canonical_text_hash=hashlib.sha256(full_text.encode("utf-8")).hexdigest(),
        structure_hash=hashlib.sha256(
            json.dumps(structure_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
    )
    return persisted, document_ir, local_ids


def _build_spans(
    *,
    revision_id: UUID,
    full_text: str,
    chunks: list[str],
    structured_nodes: list[dict[str, Any]],
    node_local_ids: dict[str, UUID],
) -> list[SourceSpan]:
    spans: list[SourceSpan] = []
    cursor = 0
    used_nodes: set[str] = set()
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
        structured = next(
            (
                item
                for item in structured_nodes
                if item.get("canonical_text") == text and item.get("local_id") not in used_nodes
            ),
            None,
        )
        local_id = structured.get("local_id") if structured else None
        if isinstance(local_id, str):
            used_nodes.add(local_id)
        spans.append(
            SourceSpan(
                span_id=span_id,
                revision_id=revision_id,
                node_id=node_local_ids.get(local_id) if isinstance(local_id, str) else None,
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


def _build_knowledge_units(
    *,
    document_id: UUID,
    original_filename: str,
    spans: list[SourceSpan],
    full_text: str,
    knowledge_point_id: str | None,
    revision_number: int,
) -> list[KnowledgeUnit]:
    """Build conservative structural candidates; publication requires an owner decision."""
    visible_spans = [span for span in spans if not _is_grader_only(span.text)]
    if not visible_spans:
        return []

    units: list[KnowledgeUnit] = []
    occurrences: dict[str, int] = {}
    for span in visible_spans:
        for heading, description in _headings_with_descriptions(span.text):
            normalized = _normalize_identity(heading)
            if not normalized:
                continue
            occurrence = occurrences.get(normalized, 0)
            occurrences[normalized] = occurrence + 1
            unit_id = uuid5(
                NAMESPACE_URL,
                f"askora-knowledge-unit:{document_id}:heading:{normalized}:{occurrence}",
            )
            units.append(
                KnowledgeUnit(
                    knowledge_unit_id=unit_id,
                    revision=revision_number,
                    kind="concept",
                    canonical_name=heading[:200],
                    description=description or heading[:500],
                    concept_ids=[],
                    evidence_span_ids=[span.span_id],
                    provenance_type="source_explicit",
                    confidence=None,
                    status="candidate",
                )
            )

    if units:
        return units

    fallback_name = knowledge_point_id or Path(original_filename).stem or original_filename
    unit_id = uuid5(
        NAMESPACE_URL,
        f"askora-knowledge-unit:{document_id}:document-root:{_normalize_identity(fallback_name)}",
    )
    return [
        KnowledgeUnit(
            knowledge_unit_id=unit_id,
            revision=revision_number,
            kind="concept",
            canonical_name=fallback_name[:200],
            description=_first_meaningful_line(full_text) or fallback_name[:500],
            concept_ids=[],
            evidence_span_ids=[span.span_id for span in visible_spans],
            provenance_type="human_curated" if knowledge_point_id else "source_explicit",
            confidence=None,
            status="candidate",
        )
    ]


def _normalize_identity(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip().casefold()
    return re.sub(r"\s+", " ", normalized)


def _headings_with_descriptions(text: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"^#{1,6}\s+(.+)$", text, re.MULTILINE))
    result: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        section_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        section = text[match.end() : section_end]
        result.append((match.group(1).strip(), _first_meaningful_line(section)))
    return result


def _is_grader_only(text: str) -> bool:
    lowered = text.casefold()
    return any(
        marker in lowered
        for marker in ("[grader-only]", "reference answer:", "参考答案：", "参考答案:")
    )

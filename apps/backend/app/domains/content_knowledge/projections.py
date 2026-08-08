"""Deterministic SYS01 multi-granularity working sets and projections (SPEC-D02)."""

from __future__ import annotations

import hashlib
import re
from typing import Any, Literal
from uuid import UUID, uuid5

from app.contracts.content import EvidenceSpanRef, HierarchyNode, SemanticUnit

SEMANTIC_SEGMENTATION_VERSION = "semantic-node-boundary-v1"
RETRIEVAL_SEGMENTATION_VERSION = "retrieval-span-window-v2"
HIERARCHY_PROJECTION_VERSION = "hierarchy-route-v1"
SEMANTIC_MAX_CHARACTERS = 1200
RETRIEVAL_MAX_CHARACTERS = 1400
RETRIEVAL_MAX_SOURCE_SPANS = 2
RETRIEVAL_MAX_SEMANTIC_UNITS = 2

SEMANTIC_SEGMENTATION_PROFILE = {
    "version": SEMANTIC_SEGMENTATION_VERSION,
    "max_characters": SEMANTIC_MAX_CHARACTERS,
}
RETRIEVAL_SEGMENTATION_PROFILE = {
    "version": RETRIEVAL_SEGMENTATION_VERSION,
    "max_characters": RETRIEVAL_MAX_CHARACTERS,
    "max_source_spans": RETRIEVAL_MAX_SOURCE_SPANS,
    "max_semantic_units": RETRIEVAL_MAX_SEMANTIC_UNITS,
}

SemanticRole = Literal[
    "definition", "argument", "procedure", "example", "exercise", "narrative", "other"
]
EvidenceRole = Literal["source_fact", "definition", "example", "procedure"]


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _is_grader_only(text: str) -> bool:
    lowered = text.casefold()
    return any(
        marker in lowered
        for marker in ("[grader-only]", "reference answer:", "参考答案：", "参考答案:")
    )


def _semantic_role(node_type: str | None, text: str) -> SemanticRole:
    lowered = text.casefold()
    if node_type in {"LIST", "CODE"} or "procedure" in lowered or "步骤" in text:
        return "procedure"
    if "example" in lowered or "例如" in text or "示例" in text:
        return "example"
    if "exercise" in lowered or "练习" in text:
        return "exercise"
    if "definition" in lowered or "定义" in text:
        return "definition"
    if node_type in {"CHAPTER", "SECTION"}:
        return "argument"
    if node_type == "PARAGRAPH":
        return "narrative"
    return "other"


def _pedagogical_role(text: str, semantic_roles: set[str]) -> str:
    if _is_grader_only(text):
        return "solution"
    if "definition" in semantic_roles:
        return "definition"
    if "example" in semantic_roles:
        return "example"
    if "procedure" in semantic_roles:
        return "context"
    return "context"


def _evidence_role(semantic_role: SemanticRole) -> EvidenceRole:
    if semantic_role == "definition":
        return "definition"
    if semantic_role == "example":
        return "example"
    if semantic_role == "procedure":
        return "procedure"
    return "source_fact"


def _split_semantic_text(text: str) -> list[str]:
    max_characters = SEMANTIC_MAX_CHARACTERS
    if len(text) <= max_characters:
        return [text]
    sentences = [
        item.strip() for item in re.split(r"(?<=[。！？.!?])\s+|\n{2,}", text) if item.strip()
    ]
    if not sentences:
        return [
            text[index : index + max_characters] for index in range(0, len(text), max_characters)
        ]
    chunks: list[str] = []
    current: list[str] = []
    current_size = 0
    for sentence in sentences:
        if current and current_size + len(sentence) + 1 > max_characters:
            chunks.append(" ".join(current))
            current = []
            current_size = 0
        if len(sentence) > max_characters:
            if current:
                chunks.append(" ".join(current))
                current = []
                current_size = 0
            chunks.extend(
                sentence[index : index + max_characters]
                for index in range(0, len(sentence), max_characters)
            )
            continue
        current.append(sentence)
        current_size += len(sentence) + 1
    if current:
        chunks.append(" ".join(current))
    return chunks


def _node_maps(
    document_nodes: list[dict[str, Any]],
) -> tuple[dict[str, dict], dict[str, str | None]]:
    by_id = {
        str(item["node_id"]): item
        for item in document_nodes
        if isinstance(item, dict) and item.get("node_id")
    }
    parents = {node_id: item.get("parent_node_id") for node_id, item in by_id.items()}
    return by_id, parents


def _hierarchy_scope(
    node_id: str | None,
    *,
    nodes: dict[str, dict],
    parents: dict[str, str | None],
) -> list[str]:
    scope: list[str] = []
    current = node_id
    visited: set[str] = set()
    while current and current not in visited:
        visited.add(current)
        node = nodes.get(current)
        if node is None:
            break
        if node.get("node_type") in {"BOOK", "PART", "CHAPTER", "SECTION"}:
            scope.append(current)
        parent = parents.get(current)
        current = str(parent) if parent else None
    return list(reversed(scope))


def build_multi_granularity_projections(
    *,
    revision_id: UUID,
    source_spans: list[dict[str, Any]],
    document_nodes: list[dict[str, Any]],
    knowledge_units: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build independent semantic, hierarchy and retrieval projections deterministically."""
    nodes, parents = _node_maps(document_nodes)
    span_by_id = {str(item["span_id"]): item for item in source_spans}
    knowledge_by_span: dict[str, list[str]] = {}
    for unit in knowledge_units:
        for span_id in unit.get("evidence_span_ids", []):
            knowledge_by_span.setdefault(str(span_id), []).append(str(unit["knowledge_unit_id"]))

    semantic_units: list[dict[str, Any]] = []
    for span in source_spans:
        span_id = str(span["span_id"])
        node_id = str(span["node_id"]) if span.get("node_id") else None
        node = nodes.get(node_id or "", {})
        scope = _hierarchy_scope(node_id, nodes=nodes, parents=parents)
        role = _semantic_role(node.get("node_type"), span["text"])
        for part_index, text in enumerate(_split_semantic_text(span["text"])):
            unit_id = uuid5(
                revision_id,
                f"{SEMANTIC_SEGMENTATION_VERSION}:{span_id}:{part_index}:{_digest(text)}",
            )
            evidence_ref = EvidenceSpanRef(
                source_span_ids=[UUID(span_id)],
                evidence_role=_evidence_role(role),
                evidence_hash=_digest(f"{span_id}:{text}"),
            )
            semantic_units.append(
                SemanticUnit(
                    semantic_unit_id=unit_id,
                    revision_id=revision_id,
                    segmentation_version=SEMANTIC_SEGMENTATION_VERSION,
                    source_span_ids=[UUID(span_id)],
                    parent_node_ids=[UUID(node_id)] if node_id else [],
                    text=text,
                    semantic_role=role,
                    context_refs=[UUID(item) for item in scope],
                    evidence_ref=evidence_ref,
                    ordinal=len(semantic_units),
                ).model_dump(mode="json")
            )

    hierarchy_nodes: list[dict[str, Any]] = []
    hierarchy_id_by_document_node: dict[str, str] = {}
    for node in sorted(
        document_nodes, key=lambda item: (int(item.get("ordinal", 0)), item["node_id"])
    ):
        if node.get("node_type") not in {"BOOK", "PART", "CHAPTER", "SECTION"}:
            continue
        document_node_id = str(node["node_id"])
        hierarchy_id = str(
            uuid5(
                revision_id,
                f"{HIERARCHY_PROJECTION_VERSION}:{document_node_id}",
            )
        )
        hierarchy_id_by_document_node[document_node_id] = hierarchy_id
        parent = node.get("parent_node_id")
        parent_hierarchy_id: str | None = None
        while parent:
            parent_key = str(parent)
            if parent_key in hierarchy_id_by_document_node:
                parent_hierarchy_id = hierarchy_id_by_document_node[parent_key]
                break
            parent = parents.get(parent_key)
        hierarchy_nodes.append(
            HierarchyNode(
                hierarchy_node_id=UUID(hierarchy_id),
                projection_version=HIERARCHY_PROJECTION_VERSION,
                revision_id=revision_id,
                document_node_id=UUID(document_node_id),
                parent_hierarchy_node_id=(
                    UUID(parent_hierarchy_id) if parent_hierarchy_id else None
                ),
                node_type=node["node_type"],
                heading=node.get("heading"),
                ordinal=node["ordinal"],
            ).model_dump(mode="json")
        )

    retrieval_chunks: list[dict[str, Any]] = []
    pending_span_ids: list[str] = []
    pending_semantic_unit_ids: list[str] = []
    pending_text: list[str] = []
    pending_visibility: str | None = None

    def flush() -> None:
        nonlocal pending_span_ids, pending_semantic_unit_ids, pending_text, pending_visibility
        if not pending_span_ids:
            return
        text = "\n\n".join(pending_text)
        semantic_roles = {
            item["semantic_role"]
            for item in semantic_units
            if set(item["source_span_ids"]).intersection(pending_span_ids)
        }
        hierarchy_scope_refs = sorted(
            {
                hierarchy_id_by_document_node[ref]
                for item in semantic_units
                if set(item["source_span_ids"]).intersection(pending_span_ids)
                for ref in item["context_refs"]
                if ref in hierarchy_id_by_document_node
            }
        )
        knowledge_unit_ids = sorted(
            {
                knowledge_id
                for span_id in pending_span_ids
                for knowledge_id in knowledge_by_span.get(span_id, [])
            }
        )
        answer_exposure = "COMPLETE" if pending_visibility == "grader_only" else "NONE"
        chunk_id = uuid5(
            revision_id,
            f"{RETRIEVAL_SEGMENTATION_VERSION}:{len(retrieval_chunks)}:"
            f"{':'.join(pending_span_ids)}:{_digest(text)}",
        )
        retrieval_chunks.append(
            {
                "chunk_id": str(chunk_id),
                "revision_id": str(revision_id),
                "segmentation_version": RETRIEVAL_SEGMENTATION_VERSION,
                "source_span_ids": list(pending_span_ids),
                "semantic_unit_ids": list(pending_semantic_unit_ids),
                "knowledge_unit_ids": knowledge_unit_ids,
                "text": text,
                "pedagogical_role": _pedagogical_role(text, semantic_roles),
                "answer_exposure": answer_exposure,
                "allowed_use": pending_visibility or "learner_visible",
                "hierarchy_scope_refs": hierarchy_scope_refs,
                "ordinal": len(retrieval_chunks),
            }
        )
        pending_span_ids = []
        pending_semantic_unit_ids = []
        pending_text = []
        pending_visibility = None

    max_characters = RETRIEVAL_MAX_CHARACTERS
    max_spans = RETRIEVAL_MAX_SOURCE_SPANS
    max_semantic_units = RETRIEVAL_MAX_SEMANTIC_UNITS
    for semantic in semantic_units:
        span_id = semantic["source_span_ids"][0]
        span = span_by_id[span_id]
        visibility = "grader_only" if _is_grader_only(span["text"]) else "learner_visible"
        proposed_size = sum(len(item) for item in pending_text) + len(semantic["text"])
        if pending_span_ids and (
            visibility != pending_visibility
            or len(pending_span_ids) >= max_spans
            or len(pending_semantic_unit_ids) >= max_semantic_units
            or proposed_size > max_characters
        ):
            flush()
        if span_id not in pending_span_ids:
            pending_span_ids.append(span_id)
        pending_semantic_unit_ids.append(semantic["semantic_unit_id"])
        pending_text.append(semantic["text"])
        pending_visibility = visibility
    flush()

    return {
        "semantic_segmentation_version": SEMANTIC_SEGMENTATION_VERSION,
        "semantic_segmentation_profile": dict(SEMANTIC_SEGMENTATION_PROFILE),
        "semantic_units": semantic_units,
        "hierarchy_projection_version": HIERARCHY_PROJECTION_VERSION,
        "hierarchy_nodes": hierarchy_nodes,
        "retrieval_segmentation_version": RETRIEVAL_SEGMENTATION_VERSION,
        "retrieval_segmentation_profile": dict(RETRIEVAL_SEGMENTATION_PROFILE),
        "retrieval_chunks": retrieval_chunks,
    }

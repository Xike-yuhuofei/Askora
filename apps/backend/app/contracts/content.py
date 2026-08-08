"""SYS01 public content/knowledge contracts for the v0.2 slice."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field

from app.contracts.base import ContractModel


class MaterialRevision(ContractModel):
    """DOMAIN-020 immutable source material revision."""

    revision_id: UUID
    document_id: UUID
    checksum: str
    source_uri: str | None = None
    parser_version: str
    extraction_version: str | None = None
    created_at: datetime
    supersedes_revision_id: UUID | None = None


class SourceSpan(ContractModel):
    """DOMAIN-021 stable learner-visible citation anchor."""

    span_id: UUID
    revision_id: UUID
    node_id: UUID | None = None
    page: int | None = Field(default=None, ge=1)
    chapter: str | None = None
    start_offset: int | None = Field(default=None, ge=0)
    end_offset: int | None = Field(default=None, ge=0)
    text: str
    anchor_version: str


class SourceChunk(ContractModel):
    """DOMAIN-022 rebuildable retrieval projection contract."""

    chunk_id: UUID
    revision_id: UUID
    segmentation_version: str
    source_span_ids: list[UUID]
    text: str
    metadata: dict[str, Any]


class SourceLocator(ContractModel):
    """D01-040 SYS01-owned locator value used by DocumentNode replay."""

    kind: Literal["epub", "pdf", "docx", "markdown", "text"]
    locator_version: str
    source_path: str | None = None
    node_path: str | None = None
    spine_index: int | None = Field(default=None, ge=0)
    spine_item_id: str | None = None
    href: str | None = None
    nav_path: list[str] = Field(default_factory=list)
    dom_path: str | None = None
    epub_cfi: str | None = None


class DocumentNode(ContractModel):
    """D01-030 internal, immutable structure fact inside one MaterialRevision."""

    node_id: UUID
    revision_id: UUID
    parent_node_id: UUID | None = None
    node_type: Literal[
        "BOOK",
        "PART",
        "CHAPTER",
        "SECTION",
        "PARAGRAPH",
        "LIST",
        "TABLE",
        "IMAGE",
        "FIGURE",
        "FORMULA",
        "CODE",
        "FOOTNOTE",
        "ENDNOTE",
        "OTHER",
    ]
    ordinal: int = Field(ge=0)
    heading: str | None = None
    text: str | None = None
    source_locator: SourceLocator
    content_hash: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentIR(ContractModel):
    """D01-020 rebuildable SYS01 parsing intermediate representation."""

    document_id: UUID
    revision_id: UUID
    parser_version: str
    format: Literal["epub", "pdf", "docx", "markdown", "text"]
    root_node_id: UUID
    node_ids: list[UUID]
    canonical_text_hash: str
    structure_hash: str


class SourceReplayResult(ContractModel):
    """D01-051 explicit source replay result; FAILED is never publishable evidence."""

    status: Literal["EXACT", "RECOVERED", "FAILED"]
    document_id: UUID
    revision_id: UUID
    span_id: UUID
    node_id: UUID | None
    resolved_node_path: str | None = None
    reason_codes: list[str] = Field(default_factory=list)


class KnowledgeUnit(ContractModel):
    """DOMAIN-030 minimal canonical teaching identity for the first slice."""

    knowledge_unit_id: UUID
    revision: int = Field(ge=1)
    kind: Literal["concept", "fact", "principle", "procedure", "method", "representation", "skill"]
    canonical_name: str
    description: str
    concept_ids: list[UUID]
    evidence_span_ids: list[UUID]
    provenance_type: Literal["source_explicit", "system_inferred", "human_curated"]
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    status: Literal["candidate", "verified", "published", "rejected", "superseded"]

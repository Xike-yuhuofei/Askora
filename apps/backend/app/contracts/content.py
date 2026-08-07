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

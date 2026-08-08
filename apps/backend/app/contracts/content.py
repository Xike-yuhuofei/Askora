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


class EvidenceSpanRef(ContractModel):
    """D02-020 typed evidence role over canonical SourceSpan references."""

    source_span_ids: list[UUID] = Field(min_length=1)
    evidence_role: Literal[
        "source_fact",
        "definition",
        "example",
        "counterexample",
        "procedure",
        "relation_evidence",
        "assessment_support",
    ]
    evidence_hash: str


class SemanticUnit(ContractModel):
    """D02-030 deterministic SYS01 extraction working record."""

    semantic_unit_id: UUID
    revision_id: UUID
    segmentation_version: str
    source_span_ids: list[UUID] = Field(min_length=1)
    parent_node_ids: list[UUID]
    text: str
    semantic_role: Literal[
        "definition",
        "argument",
        "procedure",
        "example",
        "exercise",
        "narrative",
        "other",
    ]
    context_refs: list[UUID]
    evidence_ref: EvidenceSpanRef
    ordinal: int = Field(ge=0)


class HierarchyNode(ContractModel):
    """D02-050 rebuildable scope-routing projection, never prerequisite truth."""

    hierarchy_node_id: UUID
    projection_version: str
    revision_id: UUID
    document_node_id: UUID
    parent_hierarchy_node_id: UUID | None = None
    node_type: Literal["BOOK", "PART", "CHAPTER", "SECTION"]
    heading: str | None = None
    ordinal: int = Field(ge=0)


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


class PrerequisiteRelation(ContractModel):
    """DOMAIN-040 canonical SYS01 prerequisite relation revision."""

    relation_id: UUID
    revision: int = Field(ge=1)
    prerequisite_id: UUID
    target_knowledge_unit_id: UUID
    strength: Literal["hard", "soft", "contextual"]
    evidence_span_ids: list[UUID]
    inference_method: Literal["explicit", "rule", "model", "human"]
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    status: Literal["candidate", "published", "rejected", "superseded"]


CandidateStatus = Literal[
    "candidate",
    "verified",
    "published",
    "rejected",
    "review_required",
    "superseded",
]
CandidateProvenance = Literal["deterministic", "source_explicit", "model_inferred", "human_curated"]


class KnowledgeCandidateBase(ContractModel):
    """D03 internal candidate envelope; never canonical truth by itself."""

    candidate_id: UUID
    revision_id: UUID
    source_span_ids: list[UUID]
    semantic_unit_ids: list[UUID]
    extraction_run_id: UUID
    proposed_payload: dict[str, Any]
    provenance_type: CandidateProvenance
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    status: CandidateStatus = "candidate"
    reason_codes: list[str] = Field(default_factory=list)


class ConceptCandidate(KnowledgeCandidateBase):
    candidate_type: Literal["concept"] = "concept"


class KnowledgeUnitCandidate(KnowledgeCandidateBase):
    candidate_type: Literal["knowledge_unit"] = "knowledge_unit"


class RelationCandidate(KnowledgeCandidateBase):
    candidate_type: Literal["relation"] = "relation"


class PedagogicalAssetCandidate(KnowledgeCandidateBase):
    candidate_type: Literal["pedagogical_asset"] = "pedagogical_asset"


class ExtractionRun(ContractModel):
    """D03-010 pinned extraction inputs and execution versions."""

    extraction_run_id: UUID
    input_revision_id: UUID
    parser_version: str
    semantic_segmentation_version: str
    extractor_version: str
    model_provider: str | None = None
    model_name: str | None = None
    model_snapshot: str | None = None
    prompt_version: str | None = None
    schema_version: str
    publication_policy_version: str
    created_at: datetime
    execution_mode: Literal["deterministic", "model_assisted"]
    reason_codes: list[str] = Field(default_factory=list)


class KnowledgePublicationPolicy(ContractModel):
    """D03 immutable policy snapshot; values are product rules, not science constants."""

    policy_version: str
    auto_publish_knowledge_provenance: tuple[
        Literal["deterministic", "source_explicit", "human_curated"], ...
    ]
    hard_prerequisite_inference_methods: tuple[Literal["explicit", "rule", "human"], ...]
    allowed_deterministic_rule_ids: tuple[str, ...]
    require_current_revision_evidence: bool
    require_reverse_relation_verification: bool
    model_confidence_is_calibrated: Literal[False] = False


class KnowledgePublicationResult(ContractModel):
    """Persisted SYS01 decision result used by replay without online inference."""

    decision_id: UUID
    extraction_run_id: UUID
    revision_id: UUID
    policy_version: str
    candidate_ids: list[UUID]
    published_knowledge_unit_refs: list[str]
    published_relation_refs: list[str]
    review_required_candidate_ids: list[UUID]
    rejected_candidate_ids: list[UUID]
    reason_codes: list[str]
    decided_at: datetime

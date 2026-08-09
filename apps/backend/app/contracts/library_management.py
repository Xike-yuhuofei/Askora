"""Strict SYS01 contracts for P1-04 library management and OCR review."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.contracts.base import ContractModel


class LibraryTagViewV1(ContractModel):
    tag_id: UUID
    name: str
    version: int


class LibraryCollectionViewV1(ContractModel):
    collection_id: UUID
    name: str
    version: int


class CreateLibraryLabelRequestV1(ContractModel):
    name: str = Field(min_length=1, max_length=120)
    idempotency_key: str = Field(min_length=8, max_length=200)


class UpdateDocumentMetadataRequestV1(ContractModel):
    expected_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=200)
    display_title: str | None = Field(default=None, min_length=1, max_length=255)
    subject: str | None = Field(default=None, max_length=100)
    author: str | None = Field(default=None, max_length=200)
    language: str | None = Field(default=None, max_length=35)


class DocumentMetadataResultV1(ContractModel):
    document_id: UUID
    metadata_version: int
    display_title: str
    subject: str | None
    author: str | None
    language: str | None


class BatchOrganizeDocumentsRequestV1(ContractModel):
    document_ids: tuple[UUID, ...] = Field(min_length=1, max_length=100)
    expected_versions: dict[str, int]
    idempotency_key: str = Field(min_length=8, max_length=200)
    subject: str | None = Field(default=None, max_length=100)
    add_tag_ids: tuple[UUID, ...] = ()
    remove_tag_ids: tuple[UUID, ...] = ()
    add_collection_ids: tuple[UUID, ...] = ()
    remove_collection_ids: tuple[UUID, ...] = ()
    archive: bool | None = None


class BatchDocumentResultV1(ContractModel):
    document_id: UUID
    status: Literal["updated", "archived", "restored"]
    metadata_version: int


class BatchOrganizeDocumentsResponseV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    operation_id: UUID
    results: tuple[BatchDocumentResultV1, ...]


class DuplicateSuggestionViewV1(ContractModel):
    suggestion_id: UUID
    primary_document_id: UUID
    candidate_document_id: UUID
    kind: Literal["EXACT_DUPLICATE", "CONTENT_SIMILAR", "REVISION_CANDIDATE"]
    fingerprint_version: str
    confidence: float | None
    evidence: dict
    status: Literal["pending", "kept", "dismissed", "archived", "attached_as_revision"]
    version: int
    created_at: datetime


class ResolveDuplicateSuggestionRequestV1(ContractModel):
    expected_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=200)
    action: Literal["KEEP_SEPARATE", "DISMISS", "ARCHIVE_CANDIDATE"]


class RequestOcrRunV1(ContractModel):
    idempotency_key: str = Field(min_length=8, max_length=200)
    languages: tuple[str, ...] = Field(default=("chi_sim", "eng"), min_length=1, max_length=4)


class OcrCandidateViewV1(ContractModel):
    candidate_id: UUID
    page_number: int
    block_index: int
    bbox: tuple[float, float, float, float]
    text: str
    confidence: float | None
    image_hash: str
    status: Literal["candidate", "accepted", "rejected"]
    corrected_text: str | None
    version: int


class OcrRunViewV1(ContractModel):
    run_id: UUID
    document_id: UUID
    input_revision_id: UUID | None
    engine: str
    engine_version: str
    languages: tuple[str, ...]
    policy_version: str
    status: Literal["pending", "processing", "review_required", "accepted", "rejected", "failed"]
    page_count: int
    candidate_count: int
    reason_codes: tuple[str, ...]
    error_code: str | None
    candidates: tuple[OcrCandidateViewV1, ...] = ()


class ReviewOcrCandidateV1(ContractModel):
    candidate_id: UUID
    expected_version: int = Field(ge=1)
    action: Literal["ACCEPT", "REJECT"]
    corrected_text: str | None = Field(default=None, max_length=20_000)


class ReviewOcrRunRequestV1(ContractModel):
    idempotency_key: str = Field(min_length=8, max_length=200)
    decisions: tuple[ReviewOcrCandidateV1, ...] = Field(min_length=1, max_length=1000)
    publish: bool = False

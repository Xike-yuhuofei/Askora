"""Canonical SYS01 published projection -> SYS02 EvidenceBundle adapter.

The legacy document RAG service remains a v0.2 read adapter.  This module is the
v0.3 path and delegates all ranking/selection to the existing hybrid SYS02 owner.
"""

from __future__ import annotations

from typing import Any, Literal, cast
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.adaptive import AnswerExposure, TeachingActionV03
from app.domains.content_knowledge import CONTENT_RECORD_KEY
from app.domains.retrieval import (
    AdaptiveEvidenceBuildResult,
    AdaptiveEvidenceRetriever,
    AdaptiveRetrievalCandidate,
)
from app.models.document import (
    DocumentChunk,
    ModerationStatus,
    ProcessingStatus,
    UserDocument,
)

_ALLOWED_USES = {"learner_visible", "grader_only", "internal_only"}
AllowedUseV03 = Literal["learner_visible", "grader_only", "internal_only"]


class PublishedKnowledgeRAGService:
    """Load validated current projections and ask SYS02 to build the bundle."""

    def __init__(
        self,
        db: AsyncSession,
        retriever: AdaptiveEvidenceRetriever | None = None,
    ) -> None:
        self.db = db
        self.retriever = retriever or AdaptiveEvidenceRetriever()

    async def build_evidence_bundle(
        self,
        *,
        pseudonym_id: str,
        query: str,
        teaching_action: TeachingActionV03,
        request_id: UUID | None = None,
        source_scope: dict[str, object] | None = None,
        max_chunks: int = 5,
    ) -> AdaptiveEvidenceBuildResult:
        documents = await self._available_documents(pseudonym_id)
        requested_scope = dict(source_scope or {})
        requested_scope["pseudonym_id"] = pseudonym_id
        raw_requested_ids = requested_scope.get("document_ids")
        if isinstance(raw_requested_ids, (list, tuple, set)):
            requested_ids = {str(item) for item in raw_requested_ids}
            documents = [item for item in documents if item.id in requested_ids]

        document_ids = [item.id for item in documents]
        requested_scope["document_ids"] = document_ids
        if not document_ids:
            return self.retriever.build(
                request_id=request_id or uuid4(),
                teaching_action=teaching_action,
                query=query,
                candidates=(),
                source_scope=requested_scope,
                index_versions={},
                max_items=max_chunks,
            )

        rows = (
            await self.db.execute(
                select(DocumentChunk, UserDocument)
                .join(UserDocument, DocumentChunk.document_id == UserDocument.id)
                .where(DocumentChunk.document_id.in_(document_ids))
            )
        ).all()
        candidates: list[AdaptiveRetrievalCandidate] = []
        index_versions: dict[str, str] = {}
        current_revision_ids: dict[str, str] = {}
        for chunk, document in rows:
            candidate, versions, current_revision_id = self._candidate_from_projection(
                chunk=chunk,
                document=document,
            )
            if current_revision_id:
                current_revision_ids[document.id] = current_revision_id
            if candidate is not None:
                candidates.append(candidate)
                index_versions.update(versions)

        if "revision_ids" not in requested_scope:
            requested_scope["revision_ids"] = current_revision_ids
        return self.retriever.build(
            request_id=request_id or uuid4(),
            teaching_action=teaching_action,
            query=query,
            candidates=tuple(candidates),
            source_scope=requested_scope,
            index_versions=index_versions,
            max_items=max_chunks,
        )

    async def _available_documents(self, pseudonym_id: str) -> list[UserDocument]:
        return list(
            (
                await self.db.scalars(
                    select(UserDocument).where(
                        UserDocument.pseudonym_id == pseudonym_id,
                        UserDocument.processing_status == ProcessingStatus.COMPLETED,
                        UserDocument.moderation_status == ModerationStatus.APPROVED,
                        UserDocument.is_deleted.is_(False),
                    )
                )
            ).all()
        )

    @classmethod
    def _candidate_from_projection(
        cls,
        *,
        chunk: DocumentChunk,
        document: UserDocument,
    ) -> tuple[AdaptiveRetrievalCandidate | None, dict[str, str], str | None]:
        metadata = chunk.chunk_metadata or {}
        record = (document.moderation_details or {}).get(CONTENT_RECORD_KEY, {})
        current_revision_id = record.get("current_revision_id")
        revision = next(
            (
                item
                for item in record.get("revisions", [])
                if item.get("revision_id") == current_revision_id
            ),
            None,
        )
        chunk_id = cls._uuid(chunk.id)
        document_id = cls._uuid(document.id)
        revision_id = cls._uuid(metadata.get("revision_id"))
        if chunk_id is None or document_id is None or revision_id is None:
            return None, {}, current_revision_id

        projection = next(
            (
                item
                for item in (revision or {}).get("retrieval_chunks", [])
                if item.get("chunk_id") == chunk.id
            ),
            None,
        )
        projection_versions = metadata.get("projection_versions", {})
        if not isinstance(projection_versions, dict):
            projection_versions = {}
        namespaced_versions = {
            f"document:{document.id}:{key}": str(value)
            for key, value in projection_versions.items()
        }

        span_ids = cls._uuids(metadata.get("source_span_ids", []))
        knowledge_unit_ids = cls._uuids(metadata.get("knowledge_unit_ids", []))
        knowledge_unit_refs = cls._strings(metadata.get("knowledge_unit_refs", []))
        relation_refs = cls._strings(metadata.get("relation_refs", []))
        canonical_units = {
            str(item.get("knowledge_unit_id")): item
            for item in (revision or {}).get("knowledge_units", [])
            if item.get("status") == "published"
        }
        published_unit_refs = {
            str(item.get("knowledge_unit_ref"))
            for item in (revision or {})
            .get("knowledge_publication_bindings", {})
            .get("knowledge_units", [])
        }
        published_relation_refs = {
            str(item.get("relation_ref"))
            for item in (revision or {})
            .get("knowledge_publication_bindings", {})
            .get("relations", [])
        }
        canonical_span_ids = {
            str(item.get("span_id")) for item in (revision or {}).get("source_spans", [])
        }
        expected_versions = cls._expected_versions(document.id, revision or {})
        metadata_matches_projection = bool(
            projection
            and projection.get("projection_fingerprint") == metadata.get("projection_fingerprint")
            and projection.get("source_span_ids") == metadata.get("source_span_ids")
            and projection.get("knowledge_unit_refs") == metadata.get("knowledge_unit_refs")
        )
        eligible = bool(
            revision
            and current_revision_id == str(revision_id)
            and projection
            and metadata.get("canonical_retrieval_eligible") is True
            and metadata_matches_projection
            and span_ids
            and {str(item) for item in span_ids}.issubset(canonical_span_ids)
            and knowledge_unit_ids
            and all(str(item) in canonical_units for item in knowledge_unit_ids)
            and knowledge_unit_refs
            and set(knowledge_unit_refs).issubset(published_unit_refs)
            and set(relation_refs).issubset(published_relation_refs)
            and namespaced_versions == expected_versions
        )
        exposure = cls._answer_exposure(metadata.get("answer_exposure"))
        raw_allowed_use = str(metadata.get("allowed_use", "internal_only"))
        allowed_use = cast(
            AllowedUseV03,
            raw_allowed_use if raw_allowed_use in _ALLOWED_USES else "internal_only",
        )
        return (
            AdaptiveRetrievalCandidate(
                chunk_id=chunk_id,
                document_id=document_id,
                revision_id=revision_id,
                source_span_ids=span_ids,
                knowledge_unit_ids=knowledge_unit_ids,
                content=chunk.content,
                pedagogical_role=str(metadata.get("pedagogical_role", "context")),
                answer_exposure=exposure,
                allowed_use=allowed_use,
                knowledge_unit_refs=knowledge_unit_refs,
                relation_refs=relation_refs,
                hierarchy_scope_refs=cls._strings(metadata.get("hierarchy_refs", [])),
                publication_status="published" if eligible else "ineligible",
                canonical_retrieval_eligible=eligible,
                projection_versions=namespaced_versions,
            ),
            expected_versions,
            current_revision_id,
        )

    @staticmethod
    def _expected_versions(document_id: str, revision: dict[str, Any]) -> dict[str, str]:
        result = revision.get("knowledge_publication_result", {})
        values = {
            "material_revision": revision.get("revision_id"),
            "semantic_segmentation": revision.get("semantic_segmentation_version"),
            "retrieval_segmentation": revision.get("retrieval_segmentation_version"),
            "hierarchy_projection": revision.get("hierarchy_projection_version"),
            "knowledge_extractor": revision.get("knowledge_extractor_version"),
            "knowledge_publication_policy": revision.get("knowledge_publication_policy_version"),
            "knowledge_publication_decision": result.get("decision_id"),
        }
        return {
            f"document:{document_id}:{key}": str(value)
            for key, value in values.items()
            if value is not None
        }

    @staticmethod
    def _answer_exposure(value: object) -> AnswerExposure | None:
        try:
            return AnswerExposure(str(value))
        except ValueError:
            return None

    @staticmethod
    def _uuid(value: object) -> UUID | None:
        try:
            return UUID(str(value))
        except (TypeError, ValueError, AttributeError):
            return None

    @classmethod
    def _uuids(cls, values: object) -> tuple[UUID, ...]:
        if not isinstance(values, list):
            return ()
        return tuple(item for value in values if (item := cls._uuid(value)) is not None)

    @staticmethod
    def _strings(values: object) -> tuple[str, ...]:
        if not isinstance(values, list):
            return ()
        return tuple(str(value) for value in values)

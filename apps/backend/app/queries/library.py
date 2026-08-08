"""Current-user read models for UI-02A library and scoped knowledge map."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Literal, cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts import AvailabilityStatus, KnowledgeUnit
from app.contracts.workspace import (
    KnowledgeMapDataV1,
    KnowledgeMapEdgeV1,
    KnowledgeMapNodeV1,
    KnowledgeMapResponseV1,
    KnowledgeMapScopeV1,
    LibraryDocumentViewV1,
    LibraryWorkspaceDataV1,
    LibraryWorkspaceResponseV1,
    SourceSpanViewV1,
    WorkspaceSourceStatusV1,
    WorkspaceSourceSystem,
)
from app.core.exceptions import ResourceNotFoundError, ValidationInputError
from app.domains.content_knowledge import CONTENT_RECORD_KEY, EXTRACTION_VERSION
from app.models.document import ModerationStatus, ProcessingStatus, UserDocument
from app.models.user import User

NODE_CAP = 100
EDGE_CAP = 200
SPAN_CAP = 300
EXCERPT_CAP = 2000

_MEDIA_TYPES = {
    "md": "text/markdown",
    "txt": "text/plain",
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "epub": "application/epub+zip",
}
_PROCESSING_STATUSES = {
    ProcessingStatus.PENDING,
    ProcessingStatus.PROCESSING,
    ProcessingStatus.COMPLETED,
    ProcessingStatus.FAILED,
    ProcessingStatus.REJECTED,
    ProcessingStatus.QUARANTINED,
}


class WorkspaceLibraryQueryService:
    """Compose UI read models without becoming a content or learner-state writer."""

    def __init__(
        self,
        db: AsyncSession,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._db = db
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    async def list_library(
        self,
        current_user: User,
        *,
        status: str | None,
        subject: str | None,
        page: int,
        page_size: int,
        correlation_id: str,
    ) -> LibraryWorkspaceResponseV1:
        if status is not None and status not in _PROCESSING_STATUSES:
            raise ValidationInputError("status 不是受支持的文档处理状态")
        query = select(UserDocument).where(
            UserDocument.pseudonym_id == current_user.pseudonym_id,
            UserDocument.is_deleted.is_(False),
        )
        if status:
            query = query.where(UserDocument.processing_status == status)
        if subject:
            query = query.where(UserDocument.subject == subject)
        total = await self._db.scalar(select(func.count()).select_from(query.subquery())) or 0
        documents = (
            await self._db.scalars(
                query.order_by(UserDocument.created_at.desc(), UserDocument.id)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).all()
        items = tuple(self._document_view(document) for document in documents)
        view_state: Literal["READY", "PARTIAL", "STALE", "EMPTY"]
        if not items:
            view_state = "EMPTY"
        elif any(
            item.knowledge_status == "LEGACY_COMPATIBILITY"
            or item.processing_status in {"failed", "quarantined"}
            for item in items
        ):
            view_state = "PARTIAL"
        else:
            view_state = "READY"
        return LibraryWorkspaceResponseV1(
            generated_at=self._clock(),
            correlation_id=correlation_id,
            data=LibraryWorkspaceDataV1(
                view_state=view_state,
                total=total,
                page=page,
                page_size=page_size,
                documents=items,
            ),
            source_status=(
                WorkspaceSourceStatusV1(
                    source_system=WorkspaceSourceSystem.SYS01,
                    availability=AvailabilityStatus.AVAILABLE,
                    reason_codes=("CURRENT_USER_DOCUMENTS",),
                ),
            ),
        )

    async def get_knowledge_map(
        self,
        current_user: User,
        *,
        document_id: UUID,
        correlation_id: str,
    ) -> KnowledgeMapResponseV1:
        document = await self._db.scalar(
            select(UserDocument).where(
                UserDocument.id == str(document_id),
                UserDocument.pseudonym_id == current_user.pseudonym_id,
                UserDocument.is_deleted.is_(False),
            )
        )
        if document is None:
            raise ResourceNotFoundError("文档")

        revision = self._current_revision(document)
        reason_codes: list[str] = []
        availability = AvailabilityStatus.AVAILABLE
        nodes: tuple[KnowledgeMapNodeV1, ...] = ()
        edges: tuple[KnowledgeMapEdgeV1, ...] = ()
        spans: tuple[SourceSpanViewV1, ...] = ()

        blocked = (
            document.processing_status
            in {
                ProcessingStatus.QUARANTINED,
                ProcessingStatus.REJECTED,
            }
            or document.moderation_status == ModerationStatus.REJECTED
        )
        if blocked:
            availability = AvailabilityStatus.MISSING
            reason_codes.append("CONTENT_QUARANTINED")
        elif document.processing_status in {ProcessingStatus.PENDING, ProcessingStatus.PROCESSING}:
            availability = AvailabilityStatus.MISSING
            reason_codes.append("DOCUMENT_PROCESSING_INCOMPLETE")
        elif revision is None:
            availability = AvailabilityStatus.MISSING
            reason_codes.append("CONTENT_REVISION_MISSING")
        elif revision.get("extraction_version") != EXTRACTION_VERSION:
            availability = AvailabilityStatus.STALE
            reason_codes.append("LEGACY_MINIMAL_BINDING_PENDING_REBUILD")
        else:
            nodes, edges, spans, build_reasons = self._build_map(document, revision)
            reason_codes.extend(build_reasons)

        graph_version = (
            f"material_revision:{revision['revision_id']}"
            if revision is not None
            else f"source_document:{document.id}:unmodeled"
        )
        return KnowledgeMapResponseV1(
            generated_at=self._clock(),
            correlation_id=correlation_id,
            data=KnowledgeMapDataV1(
                scope=KnowledgeMapScopeV1(
                    document_refs=(self._document_ref(document, revision),),
                    subject=document.subject,
                    graph_version=graph_version,
                ),
                nodes=nodes,
                edges=edges,
                source_spans=spans,
            ),
            source_status=(
                WorkspaceSourceStatusV1(
                    source_system=WorkspaceSourceSystem.SYS01,
                    availability=availability,
                    source_ref=graph_version,
                    reason_codes=tuple(reason_codes),
                ),
                WorkspaceSourceStatusV1(
                    source_system=WorkspaceSourceSystem.SYS03,
                    availability=AvailabilityStatus.NOT_APPLICABLE,
                    reason_codes=("EVIDENCE_PROFILE_DEFERRED_TO_UI_02B",),
                ),
            ),
        )

    def _document_view(self, document: UserDocument) -> LibraryDocumentViewV1:
        revision = self._current_revision(document)
        reasons: list[str] = []
        units: list[dict] = []
        relations: list[dict] = []
        knowledge_status: Literal[
            "NOT_MODELED", "CANDIDATES", "PUBLISHED", "LEGACY_COMPATIBILITY"
        ] = "NOT_MODELED"
        if revision is None:
            reasons.append("CONTENT_REVISION_MISSING")
        elif revision.get("extraction_version") != EXTRACTION_VERSION:
            knowledge_status = "LEGACY_COMPATIBILITY"
            reasons.append("LEGACY_MINIMAL_BINDING_PENDING_REBUILD")
        else:
            units = list(revision.get("knowledge_units", []))
            relations = list(revision.get("relations", []))
            if any(item.get("status") == "published" for item in units):
                knowledge_status = "PUBLISHED"
            elif units:
                knowledge_status = "CANDIDATES"
            else:
                reasons.append("NO_KNOWLEDGE_CANDIDATES")

        processing_status = cast(
            Literal["pending", "processing", "completed", "failed", "rejected", "quarantined"],
            document.processing_status,
        )
        if processing_status == "pending":
            reasons.append("DOCUMENT_PROCESSING_PENDING")
        elif processing_status == "processing":
            reasons.append("DOCUMENT_PROCESSING_ACTIVE")
        elif processing_status == "failed":
            reasons.append("DOCUMENT_PROCESSING_FAILED")
        elif processing_status == "quarantined":
            reasons.append("CONTENT_QUARANTINED")

        return LibraryDocumentViewV1(
            document_ref=self._document_ref(document, revision),
            document_id=UUID(document.id),
            title=document.original_filename,
            media_type=_MEDIA_TYPES.get(document.file_extension, "application/octet-stream"),
            file_size_bytes=document.file_size_bytes,
            subject=document.subject,
            processing_status=processing_status,
            moderation_status=cast(
                Literal["pending", "approved", "requires_review", "rejected"],
                document.moderation_status,
            ),
            current_revision_ref=(
                f"material_revision:{revision['revision_id']}" if revision is not None else None
            ),
            knowledge_status=knowledge_status,
            knowledge_unit_count=len(units),
            relation_count=len(relations),
            reason_codes=tuple(reasons),
            created_at=self._as_utc(document.created_at),
            updated_at=self._as_utc(document.updated_at),
        )

    def _build_map(
        self,
        document: UserDocument,
        revision: dict,
    ) -> tuple[
        tuple[KnowledgeMapNodeV1, ...],
        tuple[KnowledgeMapEdgeV1, ...],
        tuple[SourceSpanViewV1, ...],
        list[str],
    ]:
        reasons: list[str] = []
        revision_id = revision["revision_id"]
        visible_spans = {
            item["span_id"]: item
            for item in revision.get("source_spans", [])
            if isinstance(item, dict) and self._learner_visible(item.get("text", ""))
        }
        raw_units = list(revision.get("knowledge_units", []))
        if len(raw_units) > NODE_CAP:
            reasons.append("KNOWLEDGE_MAP_NODE_CAP_APPLIED")
        node_items: list[KnowledgeMapNodeV1] = []
        ref_by_id: dict[str, str] = {}
        referenced_span_ids: set[str] = set()
        for raw in raw_units[:NODE_CAP]:
            unit = KnowledgeUnit.model_validate(raw)
            evidence_ids = [str(item) for item in unit.evidence_span_ids]
            visible_ids = tuple(item for item in evidence_ids if item in visible_spans)
            if not visible_ids:
                continue
            unit_ref = f"knowledge_unit:{unit.knowledge_unit_id}:v{unit.revision}"
            ref_by_id[str(unit.knowledge_unit_id)] = unit_ref
            referenced_span_ids.update(visible_ids)
            node_items.append(
                KnowledgeMapNodeV1(
                    knowledge_unit_ref=unit_ref,
                    kind=unit.kind,
                    canonical_name=unit.canonical_name,
                    description=unit.description,
                    provenance_type=unit.provenance_type,
                    confidence=unit.confidence,
                    status=unit.status,
                    evidence_span_refs=tuple(
                        f"source_span:{span_id}:revision:{revision_id}" for span_id in visible_ids
                    ),
                )
            )
        nodes = tuple(
            sorted(
                node_items,
                key=lambda item: (item.canonical_name.casefold(), item.knowledge_unit_ref),
            )
        )

        raw_relations = list(revision.get("relations", []))
        if len(raw_relations) > EDGE_CAP:
            reasons.append("KNOWLEDGE_MAP_EDGE_CAP_APPLIED")
        edge_items: list[KnowledgeMapEdgeV1] = []
        for raw in raw_relations[:EDGE_CAP]:
            prerequisite_id = str(raw.get("prerequisite_id", ""))
            target_id = str(raw.get("target_knowledge_unit_id", ""))
            if prerequisite_id not in ref_by_id or target_id not in ref_by_id:
                continue
            relation_id = str(raw.get("relation_id", ""))
            revision_number = int(raw.get("revision", 1))
            relation_evidence_ids = tuple(
                str(item) for item in raw.get("evidence_span_ids", []) if str(item) in visible_spans
            )
            if not relation_id or not relation_evidence_ids:
                continue
            referenced_span_ids.update(relation_evidence_ids)
            edge_items.append(
                KnowledgeMapEdgeV1(
                    relation_ref=f"knowledge_relation:{relation_id}:v{revision_number}",
                    prerequisite_ref=ref_by_id[prerequisite_id],
                    target_ref=ref_by_id[target_id],
                    strength=raw["strength"],
                    confidence=raw.get("confidence"),
                    status=raw["status"],
                    evidence_span_refs=tuple(
                        f"source_span:{span_id}:revision:{revision_id}"
                        for span_id in relation_evidence_ids
                    ),
                )
            )
        edges = tuple(sorted(edge_items, key=lambda item: item.relation_ref))
        if not edges:
            reasons.append("NO_VERIFIED_RELATIONS")

        ordered_span_ids = sorted(
            referenced_span_ids,
            key=lambda span_id: (
                visible_spans[span_id].get("start_offset") or 0,
                span_id,
            ),
        )
        if len(ordered_span_ids) > SPAN_CAP:
            reasons.append("KNOWLEDGE_MAP_SPAN_CAP_APPLIED")
        spans = tuple(
            SourceSpanViewV1(
                source_span_ref=f"source_span:{span_id}:revision:{revision_id}",
                source_span_id=UUID(span_id),
                document_id=UUID(document.id),
                page=visible_spans[span_id].get("page"),
                chapter=visible_spans[span_id].get("chapter"),
                start_offset=visible_spans[span_id].get("start_offset"),
                end_offset=visible_spans[span_id].get("end_offset"),
                excerpt=visible_spans[span_id].get("text", "")[:EXCERPT_CAP],
            )
            for span_id in ordered_span_ids[:SPAN_CAP]
        )
        return nodes, edges, spans, reasons

    @staticmethod
    def _current_revision(document: UserDocument) -> dict | None:
        record = (document.moderation_details or {}).get(CONTENT_RECORD_KEY, {})
        current_id = record.get("current_revision_id")
        return next(
            (item for item in record.get("revisions", []) if item.get("revision_id") == current_id),
            None,
        )

    @staticmethod
    def _document_ref(document: UserDocument, revision: dict | None) -> str:
        suffix = revision["revision_id"] if revision is not None else "imported"
        return f"source_document:{document.id}:revision:{suffix}"

    @staticmethod
    def _learner_visible(text: str) -> bool:
        lowered = text.casefold()
        return not any(
            marker in lowered
            for marker in ("[grader-only]", "reference answer:", "参考答案：", "参考答案:")
        )

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

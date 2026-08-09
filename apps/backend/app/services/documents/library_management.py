"""SYS01 application service for P1-04 library management and deduplication."""

from __future__ import annotations

import hashlib
import json
import unicodedata
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any, Literal, cast

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.library_management import (
    BatchDocumentResultV1,
    BatchOrganizeDocumentsResponseV1,
    DocumentMetadataResultV1,
    DuplicateSuggestionViewV1,
    LibraryCollectionViewV1,
    LibraryTagViewV1,
)
from app.core.exceptions import (
    DuplicateSuggestionNotActionableError,
    LibraryBatchScopeInvalidError,
    LibraryIdempotencyConflictError,
    LibraryMetadataVersionConflictError,
    ResourceNotFoundError,
)
from app.domains.content_knowledge import CONTENT_RECORD_KEY
from app.models.document import (
    DocumentCollectionAssignment,
    DocumentTagAssignment,
    DuplicateSuggestion,
    LibraryCollection,
    LibraryCommandReceipt,
    LibrarySearchProjection,
    LibraryTag,
    ModerationStatus,
    ProcessingStatus,
    UserDocument,
)

SEARCH_INDEX_VERSION = "library-lexical-v1"
FINGERPRINT_VERSION = "normalized-content-v1"
SIMILARITY_THRESHOLD = 0.82


def normalize_library_text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def _payload_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _current_revision(document: UserDocument) -> dict[str, Any] | None:
    record = (document.moderation_details or {}).get(CONTENT_RECORD_KEY, {})
    current_id = record.get("current_revision_id")
    return next(
        (
            item
            for item in record.get("revisions", [])
            if isinstance(item, dict) and item.get("revision_id") == current_id
        ),
        None,
    )


def _learner_visible(text: str) -> bool:
    lowered = text.casefold()
    return not any(
        marker in lowered
        for marker in ("[grader-only]", "reference answer:", "参考答案：", "参考答案:")
    )


def _similarity(left: str, right: str) -> float:
    """Bounded deterministic similarity suitable for personal-library candidate generation."""
    if not left or not right:
        return 0.0
    if left == right:
        return 1.0
    left_sample = left[:50_000]
    right_sample = right[:50_000]
    return round(SequenceMatcher(None, left_sample, right_sample, autojunk=False).ratio(), 6)


class LibraryManagementService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_tag(
        self, *, pseudonym_id: str, name: str, idempotency_key: str
    ) -> LibraryTagViewV1:
        result = await self._create_label(
            pseudonym_id=pseudonym_id,
            name=name,
            idempotency_key=idempotency_key,
            kind="tag",
        )
        return LibraryTagViewV1.model_validate(result)

    async def create_collection(
        self, *, pseudonym_id: str, name: str, idempotency_key: str
    ) -> LibraryCollectionViewV1:
        result = await self._create_label(
            pseudonym_id=pseudonym_id,
            name=name,
            idempotency_key=idempotency_key,
            kind="collection",
        )
        return LibraryCollectionViewV1.model_validate(result)

    async def _create_label(
        self,
        *,
        pseudonym_id: str,
        name: str,
        idempotency_key: str,
        kind: Literal["tag", "collection"],
    ) -> dict[str, Any]:
        clean_name = " ".join(name.split()).strip()
        normalized = normalize_library_text(clean_name)
        command_type = f"create_{kind}"
        payload = {"name": clean_name}
        replay = await self._receipt_result(
            pseudonym_id, command_type, idempotency_key, payload
        )
        if replay is not None:
            return replay

        model: Any = LibraryTag if kind == "tag" else LibraryCollection
        existing = await self.db.scalar(
            select(model).where(
                model.pseudonym_id == pseudonym_id,
                model.normalized_name == normalized,
            )
        )
        if existing is None:
            existing = model(
                id=str(uuid.uuid4()),
                pseudonym_id=pseudonym_id,
                name=clean_name,
                normalized_name=normalized,
                version=1,
                is_archived=False,
            )
            self.db.add(existing)
            await self.db.flush()
        result = {
            f"{kind}_id": existing.id,
            "name": existing.name,
            "version": existing.version,
        }
        await self._store_receipt(
            pseudonym_id, command_type, idempotency_key, payload, result
        )
        await self.db.commit()
        return result

    async def update_metadata(
        self,
        *,
        document_id: str,
        pseudonym_id: str,
        expected_version: int,
        idempotency_key: str,
        changes: dict[str, Any],
    ) -> DocumentMetadataResultV1:
        payload = {
            "document_id": document_id,
            "expected_version": expected_version,
            "changes": changes,
        }
        replay = await self._receipt_result(
            pseudonym_id, "update_document_metadata", idempotency_key, payload
        )
        if replay is not None:
            return DocumentMetadataResultV1.model_validate(replay)
        document = await self._owned_document(document_id, pseudonym_id, include_archived=True)
        if document.metadata_version != expected_version:
            raise LibraryMetadataVersionConflictError()
        for field in ("display_title", "subject", "author", "language"):
            if field not in changes:
                continue
            value = changes[field]
            if isinstance(value, str):
                value = " ".join(value.split()).strip() or None
            if field == "display_title" and value is None:
                raise ValueError("display_title cannot be empty")
            setattr(document, field, value)
        document.metadata_version += 1
        await self.rebuild_search_projection(document)
        result = self._metadata_result(document).model_dump(mode="json")
        await self._store_receipt(
            pseudonym_id, "update_document_metadata", idempotency_key, payload, result
        )
        await self.db.commit()
        return DocumentMetadataResultV1.model_validate(result)

    async def batch_organize(
        self,
        *,
        pseudonym_id: str,
        document_ids: list[str],
        expected_versions: dict[str, int],
        idempotency_key: str,
        subject_supplied: bool,
        subject: str | None,
        add_tag_ids: list[str],
        remove_tag_ids: list[str],
        add_collection_ids: list[str],
        remove_collection_ids: list[str],
        archive: bool | None,
    ) -> BatchOrganizeDocumentsResponseV1:
        unique_document_ids = list(dict.fromkeys(document_ids))
        if not 1 <= len(unique_document_ids) <= 100 or len(unique_document_ids) != len(
            document_ids
        ):
            raise LibraryBatchScopeInvalidError()
        payload = {
            "document_ids": unique_document_ids,
            "expected_versions": expected_versions,
            "subject_supplied": subject_supplied,
            "subject": subject,
            "add_tag_ids": sorted(add_tag_ids),
            "remove_tag_ids": sorted(remove_tag_ids),
            "add_collection_ids": sorted(add_collection_ids),
            "remove_collection_ids": sorted(remove_collection_ids),
            "archive": archive,
        }
        replay = await self._receipt_result(
            pseudonym_id, "batch_organize_documents", idempotency_key, payload
        )
        if replay is not None:
            return BatchOrganizeDocumentsResponseV1.model_validate(replay)

        documents = (
            await self.db.scalars(
                select(UserDocument).where(
                    UserDocument.id.in_(unique_document_ids),
                    UserDocument.pseudonym_id == pseudonym_id,
                )
            )
        ).all()
        if len(documents) != len(unique_document_ids):
            raise ResourceNotFoundError("资料")
        by_id = {item.id: item for item in documents}
        for document_id in unique_document_ids:
            expected = expected_versions.get(document_id)
            if expected is None or by_id[document_id].metadata_version != expected:
                raise LibraryMetadataVersionConflictError()

        await self._validate_labels(pseudonym_id, add_tag_ids + remove_tag_ids, kind="tag")
        await self._validate_labels(
            pseudonym_id, add_collection_ids + remove_collection_ids, kind="collection"
        )
        now = datetime.now(timezone.utc)
        results: list[BatchDocumentResultV1] = []
        for document_id in unique_document_ids:
            document = by_id[document_id]
            if subject_supplied:
                document.subject = " ".join((subject or "").split()).strip() or None
            await self._update_assignments(
                document_id,
                add_tag_ids,
                remove_tag_ids,
                model=DocumentTagAssignment,
                foreign_key="tag_id",
            )
            await self._update_assignments(
                document_id,
                add_collection_ids,
                remove_collection_ids,
                model=DocumentCollectionAssignment,
                foreign_key="collection_id",
            )
            status: Literal["updated", "archived", "restored"] = "updated"
            if archive is True:
                document.is_deleted = True
                document.deleted_at = now
                status = "archived"
            elif archive is False:
                document.is_deleted = False
                document.deleted_at = None
                status = "restored"
            document.metadata_version += 1
            await self.rebuild_search_projection(document)
            results.append(
                BatchDocumentResultV1(
                    document_id=uuid.UUID(document.id),
                    status=status,
                    metadata_version=document.metadata_version,
                )
            )

        response = BatchOrganizeDocumentsResponseV1(
            operation_id=uuid.uuid4(), results=tuple(results)
        )
        dumped = response.model_dump(mode="json")
        await self._store_receipt(
            pseudonym_id, "batch_organize_documents", idempotency_key, payload, dumped
        )
        await self.db.commit()
        return response

    async def rebuild_search_projection(self, document: UserDocument) -> LibrarySearchProjection:
        revision = _current_revision(document)
        body_parts: list[str] = []
        span_refs: list[str] = []
        if (
            revision is not None
            and document.processing_status == ProcessingStatus.COMPLETED
            and document.moderation_status != ModerationStatus.REJECTED
        ):
            for span in revision.get("source_spans", []):
                text = span.get("text", "") if isinstance(span, dict) else ""
                if not text or not _learner_visible(text):
                    continue
                body_parts.append(text)
                span_refs.append(str(span["span_id"]))
        projection = await self.db.get(LibrarySearchProjection, document.id)
        if projection is None:
            projection = LibrarySearchProjection(
                document_id=document.id,
                pseudonym_id=document.pseudonym_id,
                revision_id=revision.get("revision_id") if revision else None,
                index_version=SEARCH_INDEX_VERSION,
                normalized_title=normalize_library_text(
                    document.display_title or document.original_filename
                ),
                normalized_body=normalize_library_text("\n".join(body_parts)),
                source_span_refs=span_refs,
                freshness="MISSING" if document.is_deleted else "AVAILABLE",
            )
            self.db.add(projection)
        else:
            projection.revision_id = revision.get("revision_id") if revision else None
            projection.index_version = SEARCH_INDEX_VERSION
            projection.normalized_title = normalize_library_text(
                document.display_title or document.original_filename
            )
            projection.normalized_body = normalize_library_text("\n".join(body_parts))
            projection.source_span_refs = span_refs
            projection.freshness = "MISSING" if document.is_deleted else "AVAILABLE"
        await self.db.flush()
        return projection

    async def refresh_duplicate_suggestions(
        self, document: UserDocument, *, normalized_body: str
    ) -> list[DuplicateSuggestion]:
        document.content_fingerprint = hashlib.sha256(normalized_body.encode("utf-8")).hexdigest()
        document.fingerprint_version = FINGERPRINT_VERSION
        projections = (
            await self.db.execute(
                select(UserDocument, LibrarySearchProjection)
                .join(
                    LibrarySearchProjection,
                    LibrarySearchProjection.document_id == UserDocument.id,
                )
                .where(
                    UserDocument.pseudonym_id == document.pseudonym_id,
                    UserDocument.id != document.id,
                    UserDocument.is_deleted.is_(False),
                )
            )
        ).all()
        created: list[DuplicateSuggestion] = []
        for other, projection in projections:
            kind: str | None = None
            confidence: float | None = None
            reasons: list[str] = []
            if (
                document.raw_asset_checksum
                and other.raw_asset_checksum == document.raw_asset_checksum
            ):
                kind = "EXACT_DUPLICATE"
                confidence = 1.0
                reasons.append("RAW_ASSET_CHECKSUM_MATCH")
            else:
                score = _similarity(normalized_body, projection.normalized_body)
                if score < SIMILARITY_THRESHOLD:
                    continue
                confidence = score
                same_title = normalize_library_text(
                    document.display_title or document.original_filename
                ) == normalize_library_text(other.display_title or other.original_filename)
                kind = "REVISION_CANDIDATE" if same_title else "CONTENT_SIMILAR"
                reasons.extend(("NORMALIZED_CONTENT_SIMILAR", f"SIMILARITY_{score:.3f}"))
                if same_title:
                    reasons.append("NORMALIZED_TITLE_MATCH")
            ordered = sorted(
                (document, other),
                key=lambda item: (item.created_at, item.id),
            )
            primary, candidate = ordered
            existing = await self.db.scalar(
                select(DuplicateSuggestion).where(
                    or_(
                        (
                            (DuplicateSuggestion.primary_document_id == primary.id)
                            & (DuplicateSuggestion.candidate_document_id == candidate.id)
                        ),
                        (
                            (DuplicateSuggestion.primary_document_id == candidate.id)
                            & (DuplicateSuggestion.candidate_document_id == primary.id)
                        ),
                    ),
                    DuplicateSuggestion.fingerprint_version == FINGERPRINT_VERSION,
                )
            )
            if existing is not None:
                continue
            suggestion = DuplicateSuggestion(
                id=str(uuid.uuid4()),
                pseudonym_id=document.pseudonym_id,
                primary_document_id=primary.id,
                candidate_document_id=candidate.id,
                kind=kind,
                fingerprint_version=FINGERPRINT_VERSION,
                confidence=confidence,
                evidence={"reason_codes": reasons},
                status="pending",
                version=1,
            )
            self.db.add(suggestion)
            created.append(suggestion)
        await self.db.flush()
        return created

    async def list_duplicate_suggestions(
        self, pseudonym_id: str, *, status: str = "pending"
    ) -> tuple[DuplicateSuggestionViewV1, ...]:
        suggestions = (
            await self.db.scalars(
                select(DuplicateSuggestion)
                .where(
                    DuplicateSuggestion.pseudonym_id == pseudonym_id,
                    DuplicateSuggestion.status == status,
                )
                .order_by(DuplicateSuggestion.created_at, DuplicateSuggestion.id)
            )
        ).all()
        return tuple(self._suggestion_view(item) for item in suggestions)

    async def resolve_duplicate(
        self,
        *,
        suggestion_id: str,
        pseudonym_id: str,
        expected_version: int,
        idempotency_key: str,
        action: str,
    ) -> DuplicateSuggestionViewV1:
        payload = {
            "suggestion_id": suggestion_id,
            "expected_version": expected_version,
            "action": action,
        }
        replay = await self._receipt_result(
            pseudonym_id, "resolve_duplicate", idempotency_key, payload
        )
        if replay is not None:
            return DuplicateSuggestionViewV1.model_validate(replay)
        suggestion = await self.db.scalar(
            select(DuplicateSuggestion).where(
                DuplicateSuggestion.id == suggestion_id,
                DuplicateSuggestion.pseudonym_id == pseudonym_id,
            )
        )
        if (
            suggestion is None
            or suggestion.status != "pending"
            or suggestion.version != expected_version
        ):
            raise DuplicateSuggestionNotActionableError()
        status_by_action = {
            "KEEP_SEPARATE": "kept",
            "DISMISS": "dismissed",
            "ARCHIVE_CANDIDATE": "archived",
        }
        suggestion.status = status_by_action[action]
        suggestion.resolution_reason = action
        suggestion.resolved_at = datetime.now(timezone.utc)
        suggestion.version += 1
        if action == "ARCHIVE_CANDIDATE":
            candidate = await self._owned_document(
                suggestion.candidate_document_id, pseudonym_id, include_archived=True
            )
            candidate.is_deleted = True
            candidate.deleted_at = datetime.now(timezone.utc)
            candidate.metadata_version += 1
            await self.rebuild_search_projection(candidate)
        result = self._suggestion_view(suggestion).model_dump(mode="json")
        await self._store_receipt(
            pseudonym_id, "resolve_duplicate", idempotency_key, payload, result
        )
        await self.db.commit()
        return DuplicateSuggestionViewV1.model_validate(result)

    async def assignment_views(
        self, document_ids: list[str]
    ) -> tuple[
        dict[str, tuple[LibraryTagViewV1, ...]],
        dict[str, tuple[LibraryCollectionViewV1, ...]],
    ]:
        tag_map: dict[str, list[LibraryTagViewV1]] = defaultdict(list)
        collection_map: dict[str, list[LibraryCollectionViewV1]] = defaultdict(list)
        if not document_ids:
            return {}, {}
        tag_rows = (
            await self.db.execute(
                select(DocumentTagAssignment.document_id, LibraryTag)
                .join(LibraryTag, LibraryTag.id == DocumentTagAssignment.tag_id)
                .where(
                    DocumentTagAssignment.document_id.in_(document_ids),
                    LibraryTag.is_archived.is_(False),
                )
            )
        ).all()
        for document_id, tag in tag_rows:
            tag_map[document_id].append(
                LibraryTagViewV1(tag_id=uuid.UUID(tag.id), name=tag.name, version=tag.version)
            )
        collection_rows = (
            await self.db.execute(
                select(DocumentCollectionAssignment.document_id, LibraryCollection)
                .join(
                    LibraryCollection,
                    LibraryCollection.id == DocumentCollectionAssignment.collection_id,
                )
                .where(
                    DocumentCollectionAssignment.document_id.in_(document_ids),
                    LibraryCollection.is_archived.is_(False),
                )
            )
        ).all()
        for document_id, collection in collection_rows:
            collection_map[document_id].append(
                LibraryCollectionViewV1(
                    collection_id=uuid.UUID(collection.id),
                    name=collection.name,
                    version=collection.version,
                )
            )
        return (
            {key: tuple(sorted(value, key=lambda item: item.name.casefold())) for key, value in tag_map.items()},
            {
                key: tuple(sorted(value, key=lambda item: item.name.casefold()))
                for key, value in collection_map.items()
            },
        )

    async def available_labels(
        self, pseudonym_id: str
    ) -> tuple[tuple[LibraryTagViewV1, ...], tuple[LibraryCollectionViewV1, ...]]:
        tags = (
            await self.db.scalars(
                select(LibraryTag)
                .where(LibraryTag.pseudonym_id == pseudonym_id, LibraryTag.is_archived.is_(False))
                .order_by(LibraryTag.normalized_name, LibraryTag.id)
            )
        ).all()
        collections = (
            await self.db.scalars(
                select(LibraryCollection)
                .where(
                    LibraryCollection.pseudonym_id == pseudonym_id,
                    LibraryCollection.is_archived.is_(False),
                )
                .order_by(LibraryCollection.normalized_name, LibraryCollection.id)
            )
        ).all()
        return (
            tuple(
                LibraryTagViewV1(tag_id=uuid.UUID(item.id), name=item.name, version=item.version)
                for item in tags
            ),
            tuple(
                LibraryCollectionViewV1(
                    collection_id=uuid.UUID(item.id), name=item.name, version=item.version
                )
                for item in collections
            ),
        )

    async def _owned_document(
        self, document_id: str, pseudonym_id: str, *, include_archived: bool
    ) -> UserDocument:
        clauses = [
            UserDocument.id == document_id,
            UserDocument.pseudonym_id == pseudonym_id,
        ]
        if not include_archived:
            clauses.append(UserDocument.is_deleted.is_(False))
        document = await self.db.scalar(select(UserDocument).where(*clauses))
        if document is None:
            raise ResourceNotFoundError("资料")
        return document

    async def _validate_labels(
        self, pseudonym_id: str, ids: list[str], *, kind: Literal["tag", "collection"]
    ) -> None:
        unique_ids = set(ids)
        if not unique_ids:
            return
        model = LibraryTag if kind == "tag" else LibraryCollection
        count = len(
            (
                await self.db.scalars(
                    select(model).where(
                        model.id.in_(unique_ids),
                        model.pseudonym_id == pseudonym_id,
                        model.is_archived.is_(False),
                    )
                )
            ).all()
        )
        if count != len(unique_ids):
            raise ResourceNotFoundError("资料分类")

    async def _update_assignments(
        self,
        document_id: str,
        add_ids: list[str],
        remove_ids: list[str],
        *,
        model: type[DocumentTagAssignment] | type[DocumentCollectionAssignment],
        foreign_key: str,
    ) -> None:
        if remove_ids:
            await self.db.execute(
                delete(model).where(
                    model.document_id == document_id,
                    getattr(model, foreign_key).in_(remove_ids),
                )
            )
        if not add_ids:
            return
        existing = set(
            await self.db.scalars(
                select(getattr(model, foreign_key)).where(model.document_id == document_id)
            )
        )
        for item_id in dict.fromkeys(add_ids):
            if item_id not in existing:
                self.db.add(model(document_id=document_id, **{foreign_key: item_id}))

    async def _receipt_result(
        self,
        pseudonym_id: str,
        command_type: str,
        idempotency_key: str,
        payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        existing = await self.db.scalar(
            select(LibraryCommandReceipt).where(
                LibraryCommandReceipt.pseudonym_id == pseudonym_id,
                LibraryCommandReceipt.command_type == command_type,
                LibraryCommandReceipt.idempotency_key == idempotency_key,
            )
        )
        if existing is None:
            return None
        if existing.payload_digest != _payload_digest(payload):
            raise LibraryIdempotencyConflictError()
        return existing.result_payload

    async def _store_receipt(
        self,
        pseudonym_id: str,
        command_type: str,
        idempotency_key: str,
        payload: dict[str, Any],
        result: dict[str, Any],
    ) -> None:
        self.db.add(
            LibraryCommandReceipt(
                id=str(uuid.uuid4()),
                pseudonym_id=pseudonym_id,
                command_type=command_type,
                idempotency_key=idempotency_key,
                payload_digest=_payload_digest(payload),
                result_payload=result,
            )
        )
        await self.db.flush()

    @staticmethod
    def _metadata_result(document: UserDocument) -> DocumentMetadataResultV1:
        return DocumentMetadataResultV1(
            document_id=uuid.UUID(document.id),
            metadata_version=document.metadata_version,
            display_title=document.display_title or document.original_filename,
            subject=document.subject,
            author=document.author,
            language=document.language,
        )

    @staticmethod
    def _suggestion_view(item: DuplicateSuggestion) -> DuplicateSuggestionViewV1:
        created_at = item.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        return DuplicateSuggestionViewV1(
            suggestion_id=uuid.UUID(item.id),
            primary_document_id=uuid.UUID(item.primary_document_id),
            candidate_document_id=uuid.UUID(item.candidate_document_id),
            kind=cast(
                Literal["EXACT_DUPLICATE", "CONTENT_SIMILAR", "REVISION_CANDIDATE"],
                item.kind,
            ),
            fingerprint_version=item.fingerprint_version,
            confidence=item.confidence,
            evidence=item.evidence,
            status=cast(
                Literal["pending", "kept", "dismissed", "archived", "attached_as_revision"],
                item.status,
            ),
            version=item.version,
            created_at=created_at,
        )

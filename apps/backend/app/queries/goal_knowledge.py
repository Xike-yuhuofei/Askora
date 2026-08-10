"""Read-only SYS01 view used by the SYS06 goal mapper."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.content_knowledge import CONTENT_RECORD_KEY
from app.models.document import MaterialLifecycle, ModerationStatus, ProcessingStatus, UserDocument
from app.models.user import User


@dataclass(frozen=True)
class PublishedKnowledgeUnitView:
    knowledge_unit_id: UUID
    knowledge_unit_ref: str
    source_document_id: UUID
    material_revision_id: UUID
    canonical_name: str
    description: str
    kind: str
    source_span_ids: tuple[UUID, ...]
    hierarchy_labels: tuple[str, ...]


@dataclass(frozen=True)
class PublishedKnowledgeRelationView:
    relation_id: UUID
    relation_ref: str
    source_document_id: UUID
    material_revision_id: UUID
    prerequisite_id: UUID
    target_knowledge_unit_id: UUID
    strength: str
    source_span_ids: tuple[UUID, ...]


@dataclass(frozen=True)
class PublishedGoalKnowledgeScope:
    requested_document_ids: tuple[UUID, ...]
    authorized_document_ids: tuple[UUID, ...]
    missing_document_ids: tuple[UUID, ...]
    knowledge_graph_versions: tuple[str, ...]
    units: tuple[PublishedKnowledgeUnitView, ...]
    relations: tuple[PublishedKnowledgeRelationView, ...]
    incomplete_candidate_terms: tuple[str, ...]


class GoalKnowledgeQueryService:
    """Expose published current-revision facts without granting SYS06 write access."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def load_scope(
        self,
        *,
        user: User,
        source_document_ids: tuple[UUID, ...],
    ) -> PublishedGoalKnowledgeScope:
        requested = tuple(sorted(set(source_document_ids), key=str))
        documents = (
            await self._db.scalars(
                select(UserDocument).where(
                    UserDocument.id.in_([str(item) for item in requested]),
                    UserDocument.pseudonym_id == user.pseudonym_id,
                    UserDocument.processing_status == ProcessingStatus.COMPLETED,
                    UserDocument.moderation_status == ModerationStatus.APPROVED,
                    UserDocument.lifecycle == MaterialLifecycle.ACTIVE,
                )
            )
        ).all()
        authorized = tuple(sorted((UUID(item.id) for item in documents), key=str))
        missing = tuple(item for item in requested if item not in set(authorized))
        versions: list[str] = []
        units: list[PublishedKnowledgeUnitView] = []
        relations: list[PublishedKnowledgeRelationView] = []
        incomplete_terms: set[str] = set()

        for document in sorted(documents, key=lambda item: item.id):
            record = (document.moderation_details or {}).get(CONTENT_RECORD_KEY, {})
            revision = next(
                (
                    item
                    for item in record.get("revisions", [])
                    if item.get("revision_id") == record.get("current_revision_id")
                ),
                None,
            )
            if revision is None:
                continue
            revision_id = UUID(revision["revision_id"])
            decision_id = revision.get("knowledge_publication_result", {}).get("decision_id")
            versions.append(
                f"document:{document.id}:revision:{revision_id}:publication:{decision_id}"
            )
            unit_refs = {
                str(item["knowledge_unit_ref"]).split(":")[1]: str(item["knowledge_unit_ref"])
                for item in revision.get("knowledge_publication_bindings", {}).get(
                    "knowledge_units", []
                )
            }
            relation_refs = {
                str(item["relation_ref"]).split(":")[1]: str(item["relation_ref"])
                for item in revision.get("knowledge_publication_bindings", {}).get("relations", [])
            }
            spans = {str(item["span_id"]): item for item in revision.get("source_spans", [])}
            nodes = {str(item["node_id"]): item for item in revision.get("document_nodes", [])}
            for item in revision.get("knowledge_units", []):
                if item.get("status") != "published":
                    continue
                unit_id = str(item["knowledge_unit_id"])
                evidence_ids = tuple(UUID(value) for value in item.get("evidence_span_ids", []))
                hierarchy_labels = tuple(
                    sorted(
                        {
                            str(node.get("heading"))
                            for span_id in evidence_ids
                            if (span := spans.get(str(span_id)))
                            and (node := nodes.get(str(span.get("node_id"))))
                            and node.get("heading")
                        }
                    )
                )
                units.append(
                    PublishedKnowledgeUnitView(
                        knowledge_unit_id=UUID(unit_id),
                        knowledge_unit_ref=unit_refs.get(
                            unit_id,
                            f"knowledge_unit:{unit_id}:v{item.get('revision', 1)}",
                        ),
                        source_document_id=UUID(document.id),
                        material_revision_id=revision_id,
                        canonical_name=str(item.get("canonical_name", "")),
                        description=str(item.get("description", "")),
                        kind=str(item.get("kind", "concept")),
                        source_span_ids=evidence_ids,
                        hierarchy_labels=hierarchy_labels,
                    )
                )
            for item in revision.get("relations", []):
                if item.get("status") != "published":
                    continue
                relation_id = str(item["relation_id"])
                relations.append(
                    PublishedKnowledgeRelationView(
                        relation_id=UUID(relation_id),
                        relation_ref=relation_refs.get(
                            relation_id,
                            f"knowledge_relation:{relation_id}:v{item.get('revision', 1)}",
                        ),
                        source_document_id=UUID(document.id),
                        material_revision_id=revision_id,
                        prerequisite_id=UUID(item["prerequisite_id"]),
                        target_knowledge_unit_id=UUID(item["target_knowledge_unit_id"]),
                        strength=str(item.get("strength", "contextual")),
                        source_span_ids=tuple(
                            UUID(value) for value in item.get("evidence_span_ids", [])
                        ),
                    )
                )
            for candidate in revision.get("knowledge_candidates", []):
                if candidate.get("status") not in {
                    "candidate",
                    "verified",
                    "review_required",
                }:
                    continue
                payload = candidate.get("proposed_payload", {})
                unit = payload.get("knowledge_unit", {}) if isinstance(payload, dict) else {}
                name = unit.get("canonical_name") if isinstance(unit, dict) else None
                if name:
                    incomplete_terms.add(str(name))
                description = unit.get("description") if isinstance(unit, dict) else None
                if description:
                    incomplete_terms.add(str(description))
                for span_id in candidate.get("source_span_ids", []):
                    span = spans.get(str(span_id))
                    if span and span.get("text"):
                        incomplete_terms.add(str(span["text"]))

        return PublishedGoalKnowledgeScope(
            requested_document_ids=requested,
            authorized_document_ids=authorized,
            missing_document_ids=missing,
            knowledge_graph_versions=tuple(sorted(versions)),
            units=tuple(sorted(units, key=lambda item: str(item.knowledge_unit_id))),
            relations=tuple(sorted(relations, key=lambda item: str(item.relation_id))),
            incomplete_candidate_terms=tuple(sorted(incomplete_terms)),
        )

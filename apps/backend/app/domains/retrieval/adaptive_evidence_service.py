"""SYS02 v0.3 canonical exposure retrieval with tightening-only semantics."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Literal, cast
from uuid import NAMESPACE_URL, UUID, uuid5

from app.contracts.adaptive import (
    AnswerExposure,
    EvidenceBundleV03,
    EvidenceItemV03,
    TeachingActionV03,
    VersionedRef,
)
from app.domains.retrieval.evidence_service import HybridEvidenceRetriever

_EXPOSURE_RANK = {
    AnswerExposure.NONE: 0,
    AnswerExposure.PARTIAL: 1,
    AnswerExposure.COMPLETE: 2,
}
_ROLES = {
    "definition",
    "example",
    "counterexample",
    "prerequisite",
    "hint",
    "rubric",
    "solution",
    "context",
}
PedagogicalRoleV03 = Literal[
    "definition",
    "example",
    "counterexample",
    "prerequisite",
    "hint",
    "rubric",
    "solution",
    "context",
]


@dataclass(frozen=True)
class AdaptiveRetrievalCandidate:
    chunk_id: UUID
    document_id: UUID
    revision_id: UUID
    source_span_ids: tuple[UUID, ...]
    knowledge_unit_ids: tuple[UUID, ...]
    content: str
    pedagogical_role: str = "context"
    answer_exposure: AnswerExposure | None = None
    allowed_use: Literal["learner_visible", "grader_only", "internal_only"] = "learner_visible"
    confidence: float | None = 1.0
    knowledge_unit_refs: tuple[str, ...] = ()
    relation_refs: tuple[str, ...] = ()
    hierarchy_scope_refs: tuple[str, ...] = ()
    publication_status: str = "published"
    canonical_retrieval_eligible: bool = True
    projection_versions: dict[str, str] = field(default_factory=dict)


@dataclass
class AdaptiveRetrievalTraceItem:
    chunk_id: str
    evidence_id: str | None = None
    revision_id: str = ""
    source_span_ids: tuple[str, ...] = ()
    knowledge_unit_refs: tuple[str, ...] = ()
    relation_refs: tuple[str, ...] = ()
    hierarchy_scope_refs: tuple[str, ...] = ()
    projection_versions: dict[str, str] = field(default_factory=dict)
    score: float = 0.0
    selected: bool = False
    reason_codes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AdaptiveRetrievalTrace:
    retrieval_trace_id: UUID
    request_id: UUID
    candidate_table: tuple[AdaptiveRetrievalTraceItem, ...]
    reason_codes: tuple[str, ...]
    cache_identity: str


@dataclass(frozen=True)
class AdaptiveEvidenceBuildResult:
    bundle: EvidenceBundleV03
    trace: AdaptiveRetrievalTrace


class AdaptiveEvidenceRetriever:
    """Canonical v0.3 adapter over the single HybridEvidenceRetriever baseline."""

    algorithm_version = "hybrid-rrf-tightening/2.0"

    def __init__(self, hybrid_retriever: HybridEvidenceRetriever | None = None) -> None:
        self._hybrid_retriever = hybrid_retriever or HybridEvidenceRetriever()

    def build(
        self,
        *,
        request_id: UUID,
        teaching_action: TeachingActionV03,
        query: str,
        candidates: tuple[AdaptiveRetrievalCandidate, ...],
        source_scope: dict[str, object],
        index_versions: dict[str, str],
        max_items: int = 5,
    ) -> AdaptiveEvidenceBuildResult:
        action_ref = VersionedRef(
            entity_type="teaching_action",
            entity_id=str(teaching_action.action_id),
            version=teaching_action.action_schema_version,
        )
        raw_document_ids = source_scope.get("document_ids")
        scope_restricted = raw_document_ids is not None
        allowed_document_ids: set[str] = set()
        if isinstance(raw_document_ids, (list, tuple, set)):
            allowed_document_ids = {str(value) for value in raw_document_ids}
        raw_revision_ids = source_scope.get("revision_ids")
        required_revision_ids = (
            {str(key): str(value) for key, value in raw_revision_ids.items()}
            if isinstance(raw_revision_ids, dict)
            else {}
        )

        trace_items = {
            candidate.chunk_id: AdaptiveRetrievalTraceItem(
                chunk_id=str(candidate.chunk_id),
                revision_id=str(candidate.revision_id),
                source_span_ids=tuple(str(item) for item in candidate.source_span_ids),
                knowledge_unit_refs=candidate.knowledge_unit_refs,
                relation_refs=candidate.relation_refs,
                hierarchy_scope_refs=candidate.hierarchy_scope_refs,
                projection_versions=dict(candidate.projection_versions),
            )
            for candidate in candidates
        }
        eligible: list[AdaptiveRetrievalCandidate] = []
        for candidate in candidates:
            reasons = trace_items[candidate.chunk_id].reason_codes
            if scope_restricted and str(candidate.document_id) not in allowed_document_ids:
                reasons.append("V03_RETRIEVAL_SOURCE_SCOPE_DENIED")
            required_revision = required_revision_ids.get(str(candidate.document_id))
            if required_revision and str(candidate.revision_id) != required_revision:
                reasons.append("V03_RETRIEVAL_REVISION_STALE")
            if not candidate.canonical_retrieval_eligible:
                reasons.append("V03_RETRIEVAL_CANONICAL_ELIGIBILITY_DENIED")
            if candidate.publication_status != "published" or not candidate.knowledge_unit_ids:
                reasons.append("V03_RETRIEVAL_UNPUBLISHED_KNOWLEDGE")
            if candidate.projection_versions and any(
                index_versions.get(key) != value
                for key, value in candidate.projection_versions.items()
            ):
                reasons.append("V03_RETRIEVAL_INDEX_STALE")
            if candidate.allowed_use != "learner_visible":
                reasons.append("V03_RETRIEVAL_VISIBILITY_DENIED")
            if not candidate.source_span_ids:
                reasons.append("V03_RETRIEVAL_CITATION_INVALID")
            if candidate.answer_exposure is None:
                reasons.append("V03_RETRIEVAL_EXPOSURE_UNCERTAIN_TIGHTENED")
            elif (
                _EXPOSURE_RANK[candidate.answer_exposure]
                > _EXPOSURE_RANK[teaching_action.answer_exposure]
            ):
                reasons.append("V03_RETRIEVAL_EXPOSURE_LIMIT")
            if not reasons:
                eligible.append(candidate)

        ranking = self._hybrid_retriever.rank_candidates(
            query=query,
            candidates=eligible,
            max_items=max_items,
        )
        selected = list(ranking.selected)
        for candidate in eligible:
            trace = trace_items[candidate.chunk_id]
            ranked_trace = ranking.trace_by_id[candidate.chunk_id]
            trace.score = min(1.0, ranked_trace.rrf_score * 30)
            trace.selected = ranked_trace.selected
            trace.reason_codes.extend(ranked_trace.reason_codes)
            if trace.selected:
                trace.evidence_id = str(
                    uuid5(
                        NAMESPACE_URL,
                        f"askora:v03:evidence:{request_id}:{candidate.chunk_id}",
                    )
                )

        required_roles = {role for role in teaching_action.evidence_requirements if role in _ROLES}
        selected_roles = {candidate.pedagogical_role for candidate in selected}
        missing_roles = tuple(sorted(required_roles - selected_roles))
        missing_reasons: list[str] = []
        if not selected:
            missing_reasons.append("V03_RETRIEVAL_NO_VERIFIED_EVIDENCE")
        if missing_roles:
            missing_reasons.append("V03_RETRIEVAL_REQUIRED_ROLE_MISSING")

        items = tuple(
            EvidenceItemV03(
                evidence_id=uuid5(
                    NAMESPACE_URL,
                    f"askora:v03:evidence:{request_id}:{candidate.chunk_id}",
                ),
                source_span_ids=candidate.source_span_ids,
                knowledge_unit_ids=candidate.knowledge_unit_ids,
                pedagogical_role=cast(
                    PedagogicalRoleV03,
                    (
                        candidate.pedagogical_role
                        if candidate.pedagogical_role in _ROLES
                        else "context"
                    ),
                ),
                content=candidate.content,
                relevance=trace_items[candidate.chunk_id].score,
                confidence=candidate.confidence,
                answer_exposure=candidate.answer_exposure or AnswerExposure.NONE,
                allowed_use=candidate.allowed_use,
            )
            for candidate in selected
        )
        trace_id = uuid5(
            NAMESPACE_URL,
            f"askora:v03:retrieval-trace:{request_id}:{teaching_action.action_id}:{self.algorithm_version}",
        )
        semantic_ids = ":".join(str(item.evidence_id) for item in items)
        bundle_id = uuid5(
            NAMESPACE_URL,
            f"askora:v03:evidence-bundle:{request_id}:{teaching_action.action_id}:{semantic_ids}",
        )
        bundle = EvidenceBundleV03(
            bundle_id=bundle_id,
            request_id=request_id,
            teaching_action_ref=action_ref,
            source_scope=source_scope,
            index_versions=index_versions,
            items=items,
            missing_roles=missing_roles,
            missing_reason_codes=tuple(missing_reasons),
            bundle_confidence=(
                sum(item.confidence or 0.0 for item in items) / len(items) if items else None
            ),
            retrieval_trace_id=trace_id,
        )
        return AdaptiveEvidenceBuildResult(
            bundle=bundle,
            trace=AdaptiveRetrievalTrace(
                retrieval_trace_id=trace_id,
                request_id=request_id,
                candidate_table=tuple(trace_items.values()),
                reason_codes=(self.algorithm_version, *ranking.degraded_reason_codes),
                cache_identity=self.cache_identity(
                    teaching_action=teaching_action,
                    query=query,
                    candidates=candidates,
                    source_scope=source_scope,
                    index_versions=index_versions,
                ),
            ),
        )

    def cache_identity(
        self,
        *,
        teaching_action: TeachingActionV03,
        query: str,
        candidates: tuple[AdaptiveRetrievalCandidate, ...],
        source_scope: dict[str, object],
        index_versions: dict[str, str],
    ) -> str:
        """Build the SYS02-031 identity; this does not make cache a truth source."""
        payload = {
            "algorithm_version": self.algorithm_version,
            "request_semantics": " ".join(query.casefold().split()),
            "answer_exposure": teaching_action.answer_exposure.value,
            "source_scope": source_scope,
            "revision_ids": sorted({str(item.revision_id) for item in candidates}),
            "projection_versions": sorted(
                {
                    (key, value)
                    for item in candidates
                    for key, value in item.projection_versions.items()
                }
            ),
            "index_versions": index_versions,
        }
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

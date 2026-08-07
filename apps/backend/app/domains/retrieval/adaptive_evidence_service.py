"""SYS02 v0.3 canonical exposure retrieval with tightening-only semantics."""

from __future__ import annotations

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
from app.domains.retrieval.evidence_service import _lexical_score

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


@dataclass
class AdaptiveRetrievalTraceItem:
    chunk_id: str
    score: float = 0.0
    selected: bool = False
    reason_codes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AdaptiveRetrievalTrace:
    retrieval_trace_id: UUID
    request_id: UUID
    candidate_table: tuple[AdaptiveRetrievalTraceItem, ...]
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class AdaptiveEvidenceBuildResult:
    bundle: EvidenceBundleV03
    trace: AdaptiveRetrievalTrace


class AdaptiveEvidenceRetriever:
    """Closed v0.3 writer; legacy integer exposure never enters this path."""

    algorithm_version = "adaptive-lexical-tightening/1.0"

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

        trace_items = {
            candidate.chunk_id: AdaptiveRetrievalTraceItem(chunk_id=str(candidate.chunk_id))
            for candidate in candidates
        }
        eligible: list[AdaptiveRetrievalCandidate] = []
        for candidate in candidates:
            reasons = trace_items[candidate.chunk_id].reason_codes
            if scope_restricted and str(candidate.document_id) not in allowed_document_ids:
                reasons.append("V03_RETRIEVAL_SOURCE_SCOPE_DENIED")
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

        ranked = sorted(
            eligible,
            key=lambda item: (-_lexical_score(query, item.content), str(item.chunk_id)),
        )
        selected = [item for item in ranked if _lexical_score(query, item.content) > 0][:max_items]
        for candidate in eligible:
            trace = trace_items[candidate.chunk_id]
            trace.score = _lexical_score(query, candidate.content)
            if candidate in selected:
                trace.selected = True
                trace.reason_codes.append("V03_RETRIEVAL_SELECTED")
            else:
                trace.reason_codes.append("V03_RETRIEVAL_NOT_SELECTED")

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
                reason_codes=(self.algorithm_version,),
            ),
        )

"""Deterministic hybrid retrieval and policy filtering for SYS02."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Callable, Literal, cast
from uuid import UUID, uuid4

from app.contracts.learning import EvidenceBundle, EvidenceItem, TeachingAction

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
PedagogicalRole = Literal[
    "definition",
    "example",
    "counterexample",
    "prerequisite",
    "hint",
    "rubric",
    "solution",
    "context",
]
ExposureLevel = Literal[0, 1, 2, 3, 4]
AllowedUse = Literal["learner_visible", "grader_only", "internal_only"]


@dataclass(frozen=True)
class RetrievalCandidate:
    chunk_id: UUID
    document_id: UUID
    revision_id: UUID
    source_span_ids: tuple[UUID, ...]
    knowledge_unit_ids: tuple[UUID, ...]
    content: str
    pedagogical_role: str = "context"
    exposure_level: int = 0
    allowed_use: str = "learner_visible"


@dataclass
class RetrievalTraceItem:
    chunk_id: str
    lexical_rank: int | None = None
    dense_rank: int | None = None
    rrf_score: float = 0.0
    selected: bool = False
    reason_codes: list[str] = field(default_factory=list)


@dataclass
class RetrievalTrace:
    retrieval_trace_id: UUID
    request_id: UUID
    index_versions: dict[str, str]
    candidates: list[RetrievalTraceItem]
    degraded_reason_codes: list[str]


@dataclass(frozen=True)
class EvidenceBundleBuildResult:
    bundle: EvidenceBundle
    trace: RetrievalTrace


class HybridEvidenceRetriever:
    """BM25-like lexical + local dense cosine + RRF with hard policy filters."""

    def __init__(
        self,
        *,
        dense_scorer: Callable[[str, str], float] | None = None,
        reranker: Callable[[str, list[RetrievalCandidate]], list[RetrievalCandidate]] | None = None,
        rrf_k: int = 60,
    ) -> None:
        self._dense_scorer = dense_scorer or _dense_cosine
        self._reranker = reranker
        self._rrf_k = rrf_k

    def build_evidence_bundle(
        self,
        *,
        request_id: UUID,
        teaching_action: TeachingAction,
        query: str,
        candidates: list[RetrievalCandidate],
        source_scope: dict[str, object],
        index_versions: dict[str, str],
        learner_visible: bool = True,
        max_items: int = 5,
    ) -> EvidenceBundleBuildResult:
        trace_id = uuid4()
        trace_by_id = {
            candidate.chunk_id: RetrievalTraceItem(chunk_id=str(candidate.chunk_id))
            for candidate in candidates
        }
        raw_document_ids = source_scope.get("document_ids", [])
        scope_restricted = "document_ids" in source_scope
        allowed_document_ids: set[UUID] = set()
        if isinstance(raw_document_ids, (list, tuple, set)):
            for value in raw_document_ids:
                try:
                    allowed_document_ids.add(UUID(str(value)))
                except (TypeError, ValueError, AttributeError):
                    continue
        eligible: list[RetrievalCandidate] = []
        for candidate in candidates:
            reasons = trace_by_id[candidate.chunk_id].reason_codes
            if scope_restricted and candidate.document_id not in allowed_document_ids:
                reasons.append("RETRIEVAL_SOURCE_SCOPE_DENIED")
            if candidate.exposure_level > teaching_action.answer_exposure_max:
                reasons.append("RETRIEVAL_EXPOSURE_LIMIT")
            if learner_visible and candidate.allowed_use != "learner_visible":
                reasons.append("RETRIEVAL_VISIBILITY_DENIED")
            if not candidate.source_span_ids:
                reasons.append("RETRIEVAL_CITATION_INVALID")
            if not reasons:
                eligible.append(candidate)

        deduplicated: list[RetrievalCandidate] = []
        seen_content: set[str] = set()
        for candidate in eligible:
            normalized = " ".join(candidate.content.lower().split())
            if normalized in seen_content:
                trace_by_id[candidate.chunk_id].reason_codes.append("RETRIEVAL_DUPLICATE")
                continue
            seen_content.add(normalized)
            deduplicated.append(candidate)
        eligible = deduplicated

        degraded: list[str] = []
        lexical = sorted(
            ((_lexical_score(query, item.content), item) for item in eligible),
            key=lambda pair: (-pair[0], str(pair[1].chunk_id)),
        )
        lexical = [pair for pair in lexical if pair[0] > 0]
        for rank, (_score, candidate) in enumerate(lexical, 1):
            trace_by_id[candidate.chunk_id].lexical_rank = rank

        try:
            dense = sorted(
                ((self._dense_scorer(query, item.content), item) for item in eligible),
                key=lambda pair: (-pair[0], str(pair[1].chunk_id)),
            )
            dense = [pair for pair in dense if pair[0] > 0]
        except Exception:
            dense = []
            degraded.append("RETRIEVAL_DENSE_UNAVAILABLE_LEXICAL_ONLY")
        for rank, (_score, candidate) in enumerate(dense, 1):
            trace_by_id[candidate.chunk_id].dense_rank = rank

        ranked_ids = {candidate.chunk_id for _score, candidate in lexical + dense}
        for candidate_id in ranked_ids:
            item = trace_by_id[candidate_id]
            if item.lexical_rank is not None:
                item.rrf_score += 1.0 / (self._rrf_k + item.lexical_rank)
            if item.dense_rank is not None:
                item.rrf_score += 1.0 / (self._rrf_k + item.dense_rank)
        ranked = sorted(
            (item for item in eligible if item.chunk_id in ranked_ids),
            key=lambda item: (-trace_by_id[item.chunk_id].rrf_score, str(item.chunk_id)),
        )
        if self._reranker and ranked:
            try:
                ranked = self._reranker(query, ranked)
            except Exception:
                degraded.append("RETRIEVAL_RERANKER_UNAVAILABLE_RRF_USED")

        selected = ranked[:max_items]
        for candidate in selected:
            trace_by_id[candidate.chunk_id].selected = True
            trace_by_id[candidate.chunk_id].reason_codes.append("RETRIEVAL_SELECTED_RRF")
        for candidate in eligible:
            trace_item = trace_by_id[candidate.chunk_id]
            if not trace_item.selected and not trace_item.reason_codes:
                trace_item.reason_codes.append("RETRIEVAL_NOT_SELECTED_BUDGET_OR_RELEVANCE")

        roles_present = {item.pedagogical_role for item in selected}
        required_roles = {role for role in teaching_action.evidence_requirements if role in _ROLES}
        missing_roles = sorted(required_roles - roles_present)
        items = [
            EvidenceItem(
                evidence_id=uuid4(),
                source_span_ids=list(item.source_span_ids),
                knowledge_unit_ids=list(item.knowledge_unit_ids),
                pedagogical_role=(
                    cast(
                        PedagogicalRole,
                        item.pedagogical_role if item.pedagogical_role in _ROLES else "context",
                    )
                ),
                content=item.content,
                relevance=min(1.0, trace_by_id[item.chunk_id].rrf_score * 30),
                confidence=1.0,
                exposure_level=cast(ExposureLevel, item.exposure_level),
                allowed_use=cast(AllowedUse, item.allowed_use),
            )
            for item in selected
        ]
        bundle = EvidenceBundle(
            bundle_id=uuid4(),
            request_id=request_id,
            teaching_action_id=teaching_action.action_id,
            assessment_context_id=None,
            source_scope=source_scope,
            index_versions=index_versions,
            items=items,
            conflicts=[],
            missing_roles=missing_roles,
            bundle_confidence=(sum(item.confidence or 0.0 for item in items) / len(items))
            if items
            else None,
            retrieval_trace_id=trace_id,
        )
        return EvidenceBundleBuildResult(
            bundle=bundle,
            trace=RetrievalTrace(
                retrieval_trace_id=trace_id,
                request_id=request_id,
                index_versions=index_versions,
                candidates=list(trace_by_id.values()),
                degraded_reason_codes=degraded,
            ),
        )


def _tokens(text: str) -> list[str]:
    lowered = text.lower()
    words = re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", lowered)
    compact_cn = "".join(re.findall(r"[\u4e00-\u9fff]", lowered))
    bigrams = [compact_cn[index : index + 2] for index in range(max(0, len(compact_cn) - 1))]
    return [*words, *bigrams]


def _lexical_score(query: str, content: str) -> float:
    query_counts = Counter(_tokens(query))
    content_counts = Counter(_tokens(content))
    if not query_counts or not content_counts:
        return 0.0
    length = sum(content_counts.values())
    return sum(
        (content_counts[token] * 2.2) / (content_counts[token] + 1.2 * (0.25 + 0.75 * length / 100))
        for token in query_counts
        if content_counts[token]
    )


def _dense_cosine(query: str, content: str) -> float:
    left = Counter(_tokens(query))
    right = Counter(_tokens(content))
    if not left or not right:
        return 0.0
    dot = sum(value * right[token] for token, value in left.items())
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0

"""Deterministic SYS01 candidate verification and publication pipeline (SPEC-D03)."""

from __future__ import annotations

import copy
import re
import unicodedata
from collections import Counter
from datetime import datetime
from typing import Any, Iterable
from uuid import UUID, uuid5

from app.contracts.content import (
    ConceptCandidate,
    ExtractionRun,
    KnowledgeCandidateBase,
    KnowledgePublicationPolicy,
    KnowledgePublicationResult,
    KnowledgeUnit,
    KnowledgeUnitCandidate,
    PedagogicalAssetCandidate,
    PrerequisiteRelation,
    RelationCandidate,
)
from app.contracts.decisions import (
    DecisionAlgorithm,
    DecisionExperiment,
    DecisionInput,
    DecisionTrace,
)
from app.contracts.events import (
    EventActor,
    EventContext,
    EventPrivacy,
    EventProvenance,
    EventTrace,
    LearningEventEnvelope,
)

KNOWLEDGE_EXTRACTOR_VERSION = "knowledge-candidate-deterministic-v1"
KNOWLEDGE_CANDIDATE_SCHEMA_VERSION = "knowledge-candidate-schema-v1"
KNOWLEDGE_PUBLICATION_POLICY_VERSION = "knowledge-publication-policy-v1"
EXPLICIT_PREREQUISITE_RULE_VERSION = "source-explicit-prerequisite-v1"

DEFAULT_KNOWLEDGE_PUBLICATION_POLICY = KnowledgePublicationPolicy(
    policy_version=KNOWLEDGE_PUBLICATION_POLICY_VERSION,
    auto_publish_knowledge_provenance=(
        "deterministic",
        "source_explicit",
        "human_curated",
    ),
    hard_prerequisite_inference_methods=("explicit", "rule", "human"),
    allowed_deterministic_rule_ids=(EXPLICIT_PREREQUISITE_RULE_VERSION,),
    require_current_revision_evidence=True,
    require_reverse_relation_verification=True,
    model_confidence_is_calibrated=False,
)

KnowledgeCandidate = (
    ConceptCandidate | KnowledgeUnitCandidate | RelationCandidate | PedagogicalAssetCandidate
)


def _normalized(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip().casefold()
    return re.sub(r"\s+", " ", normalized)


def _created_at(revision: dict[str, Any]) -> datetime:
    value = revision["created_at"]
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _candidate_model(payload: dict[str, Any] | KnowledgeCandidate) -> KnowledgeCandidate:
    if isinstance(payload, KnowledgeCandidateBase):
        return payload
    candidate_type = payload.get("candidate_type")
    if candidate_type == "concept":
        return ConceptCandidate.model_validate(payload)
    if candidate_type == "knowledge_unit":
        return KnowledgeUnitCandidate.model_validate(payload)
    if candidate_type == "relation":
        return RelationCandidate.model_validate(payload)
    if candidate_type == "pedagogical_asset":
        return PedagogicalAssetCandidate.model_validate(payload)
    raise ValueError(f"unsupported knowledge candidate type: {candidate_type}")


def _semantic_ids_for_spans(revision: dict[str, Any], span_ids: Iterable[str]) -> list[UUID]:
    wanted = set(span_ids)
    return [
        UUID(item["semantic_unit_id"])
        for item in revision.get("semantic_units", [])
        if wanted.intersection(item.get("source_span_ids", []))
    ]


def _has_explicit_heading(revision: dict[str, Any], unit: dict[str, Any]) -> bool:
    target = _normalized(unit["canonical_name"])
    evidence_ids = set(unit.get("evidence_span_ids", []))
    for semantic in revision.get("semantic_units", []):
        if not evidence_ids.intersection(semantic.get("source_span_ids", [])):
            continue
        for heading in re.findall(r"^#{1,6}\s+(.+)$", semantic.get("text", ""), re.MULTILINE):
            if _normalized(heading) == target:
                return True
    return False


def build_extraction_run(
    revision: dict[str, Any],
    *,
    policy: KnowledgePublicationPolicy = DEFAULT_KNOWLEDGE_PUBLICATION_POLICY,
) -> ExtractionRun:
    """Pin every deterministic extraction input and version to the exact revision."""
    revision_id = UUID(revision["revision_id"])
    run_id = uuid5(
        revision_id,
        ":".join(
            (
                KNOWLEDGE_EXTRACTOR_VERSION,
                revision["semantic_segmentation_version"],
                KNOWLEDGE_CANDIDATE_SCHEMA_VERSION,
                policy.policy_version,
            )
        ),
    )
    return ExtractionRun(
        extraction_run_id=run_id,
        input_revision_id=revision_id,
        parser_version=revision["parser_version"],
        semantic_segmentation_version=revision["semantic_segmentation_version"],
        extractor_version=KNOWLEDGE_EXTRACTOR_VERSION,
        model_provider=None,
        model_name=None,
        model_snapshot=None,
        prompt_version=None,
        schema_version=KNOWLEDGE_CANDIDATE_SCHEMA_VERSION,
        publication_policy_version=policy.policy_version,
        created_at=_created_at(revision),
        execution_mode="deterministic",
        reason_codes=["DETERMINISTIC_EXTRACTION_NO_MODEL_CALL"],
    )


def _explicit_relation_direction(
    text: str,
    prerequisite_name: str,
    target_name: str,
) -> bool:
    prerequisite = re.escape(_normalized(prerequisite_name))
    target = re.escape(_normalized(target_name))
    patterns = (
        rf"{prerequisite}.{{0,40}}(?:(?:is|are)\s+(?:an?\s+)?prerequisite\s+for|precedes).{{0,40}}{target}",
        rf"{target}.{{0,40}}(?:requires|depends\s+on).{{0,40}}{prerequisite}",
        rf"{target}.{{0,40}}(?:必须先|需要先|前置).{{0,40}}{prerequisite}",
        rf"{prerequisite}.{{0,40}}(?:是|作为).{{0,40}}{target}.{{0,40}}前置",
    )
    statements = [
        _normalized(item) for item in re.split(r"(?<=[.!?。！？])\s+|\n+", text) if item.strip()
    ]
    return any(re.search(pattern, statement) for statement in statements for pattern in patterns)


def build_deterministic_candidates(
    revision: dict[str, Any],
    *,
    extraction_run: ExtractionRun,
) -> list[KnowledgeCandidate]:
    """Adapt structural KUs and source roles into the unified D03 candidate envelope."""
    revision_id = UUID(revision["revision_id"])
    run_id = extraction_run.extraction_run_id
    candidates: list[KnowledgeCandidate] = []
    units = list(revision.get("knowledge_units", []))

    for unit in units:
        unit_id = unit["knowledge_unit_id"]
        span_ids = [str(item) for item in unit.get("evidence_span_ids", [])]
        semantic_ids = _semantic_ids_for_spans(revision, span_ids)
        structural_basis = (
            "explicit_heading" if _has_explicit_heading(revision, unit) else "document_root"
        )
        candidates.append(
            KnowledgeUnitCandidate(
                candidate_id=uuid5(run_id, f"knowledge-unit:{unit_id}:v{unit['revision']}"),
                revision_id=revision_id,
                source_span_ids=[UUID(item) for item in span_ids],
                semantic_unit_ids=semantic_ids,
                extraction_run_id=run_id,
                proposed_payload={
                    "knowledge_unit": unit,
                    "structural_basis": structural_basis,
                },
                provenance_type="deterministic",
                confidence=None,
            )
        )
        candidates.append(
            ConceptCandidate(
                candidate_id=uuid5(run_id, f"concept:{unit_id}:v{unit['revision']}"),
                revision_id=revision_id,
                source_span_ids=[UUID(item) for item in span_ids],
                semantic_unit_ids=semantic_ids,
                extraction_run_id=run_id,
                proposed_payload={
                    "canonical_name": unit["canonical_name"],
                    "definition": unit["description"],
                    "aliases": [],
                    "resolution_scope": "current_material_revision",
                },
                provenance_type="deterministic",
                confidence=None,
            )
        )

    for semantic in revision.get("semantic_units", []):
        role = semantic.get("semantic_role")
        text = semantic.get("text", "")
        protected = any(
            marker in text.casefold()
            for marker in ("[grader-only]", "reference answer:", "参考答案：", "参考答案:")
        )
        asset_type = "solution" if protected else role
        if asset_type not in {"definition", "example", "exercise", "solution"}:
            continue
        asset_span_ids = [UUID(item) for item in semantic.get("source_span_ids", [])]
        candidates.append(
            PedagogicalAssetCandidate(
                candidate_id=uuid5(
                    run_id,
                    f"pedagogical-asset:{semantic['semantic_unit_id']}:{asset_type}",
                ),
                revision_id=revision_id,
                source_span_ids=asset_span_ids,
                semantic_unit_ids=[UUID(semantic["semantic_unit_id"])],
                extraction_run_id=run_id,
                proposed_payload={
                    "asset_type": asset_type,
                    "source_span_ids": [str(item) for item in asset_span_ids],
                    "provenance": "source_derived",
                    "activation_status": "candidate_only",
                },
                provenance_type="source_explicit",
                confidence=None,
            )
        )

    for semantic in revision.get("semantic_units", []):
        text = semantic.get("text", "")
        for prerequisite in units:
            for target in units:
                if prerequisite["knowledge_unit_id"] == target["knowledge_unit_id"]:
                    continue
                if not _explicit_relation_direction(
                    text,
                    prerequisite["canonical_name"],
                    target["canonical_name"],
                ):
                    continue
                relation_id = uuid5(
                    revision_id,
                    f"hard-prerequisite:{prerequisite['knowledge_unit_id']}:"
                    f"{target['knowledge_unit_id']}",
                )
                candidate_id = uuid5(run_id, f"relation:{relation_id}:v1")
                relation_span_ids = [UUID(item) for item in semantic.get("source_span_ids", [])]
                candidates.append(
                    RelationCandidate(
                        candidate_id=candidate_id,
                        revision_id=revision_id,
                        source_span_ids=relation_span_ids,
                        semantic_unit_ids=[UUID(semantic["semantic_unit_id"])],
                        extraction_run_id=run_id,
                        proposed_payload={
                            "relation": {
                                "relation_id": str(relation_id),
                                "revision": 1,
                                "prerequisite_id": prerequisite["knowledge_unit_id"],
                                "target_knowledge_unit_id": target["knowledge_unit_id"],
                                "strength": "hard",
                                "evidence_span_ids": [str(item) for item in relation_span_ids],
                                "inference_method": "explicit",
                                "confidence": None,
                                "status": "candidate",
                            },
                            "reverse_verification": {
                                "method": "deterministic_explicit_text",
                                "rule_id": EXPLICIT_PREREQUISITE_RULE_VERSION,
                            },
                        },
                        provenance_type="source_explicit",
                        confidence=None,
                    )
                )
    return candidates


def _replace_candidate(
    candidate: KnowledgeCandidate,
    *,
    status: str,
    reason_codes: list[str],
) -> KnowledgeCandidate:
    return candidate.model_copy(update={"status": status, "reason_codes": reason_codes})


def _reference_errors(
    candidate: KnowledgeCandidate,
    *,
    revision_id: str,
    span_ids: set[str],
    semantic_ids: set[str],
    anchor_status_by_span: dict[str, str],
    extraction_run_id: UUID,
) -> list[str]:
    errors: list[str] = []
    if str(candidate.revision_id) != revision_id:
        errors.append("CANDIDATE_SUPERSEDED_REVISION_REF")
    if candidate.extraction_run_id != extraction_run_id:
        errors.append("CANDIDATE_EXTRACTION_RUN_MISMATCH")
    if not candidate.source_span_ids:
        errors.append("CANDIDATE_ORPHAN_EVIDENCE")
    for span_id in candidate.source_span_ids:
        key = str(span_id)
        if key not in span_ids:
            errors.append("CANDIDATE_INVALID_SOURCE_SPAN")
        elif anchor_status_by_span.get(key, "FAILED") == "FAILED":
            errors.append("CANDIDATE_SOURCE_ANCHOR_REPLAY_FAILED")
    if not candidate.semantic_unit_ids or any(
        str(item) not in semantic_ids for item in candidate.semantic_unit_ids
    ):
        errors.append("CANDIDATE_INVALID_SEMANTIC_UNIT_REF")
    return list(dict.fromkeys(errors))


def _path_exists(adjacency: dict[str, set[str]], start: str, target: str) -> bool:
    pending = [start]
    visited: set[str] = set()
    while pending:
        current = pending.pop()
        if current == target:
            return True
        if current in visited:
            continue
        visited.add(current)
        pending.extend(sorted(adjacency.get(current, set()) - visited))
    return False


def _relation_reverse_verified(
    candidate: RelationCandidate,
    relation: PrerequisiteRelation,
    *,
    spans: dict[str, dict[str, Any]],
    units: dict[str, KnowledgeUnit],
    policy: KnowledgePublicationPolicy,
) -> bool:
    verification = candidate.proposed_payload.get("reverse_verification", {})
    if relation.inference_method == "rule":
        return verification.get("rule_id") in policy.allowed_deterministic_rule_ids and bool(
            verification.get("applicability")
        )
    if relation.inference_method == "human":
        return bool(verification.get("review_decision_ref"))
    if relation.inference_method != "explicit":
        return False
    prerequisite = units.get(str(relation.prerequisite_id))
    target = units.get(str(relation.target_knowledge_unit_id))
    if prerequisite is None or target is None:
        return False
    return any(
        _explicit_relation_direction(
            spans[str(span_id)]["text"],
            prerequisite.canonical_name,
            target.canonical_name,
        )
        for span_id in relation.evidence_span_ids
        if str(span_id) in spans
    )


def publish_revision_knowledge(
    revision: dict[str, Any],
    *,
    anchor_status_by_span: dict[str, str],
    additional_candidates: Iterable[dict[str, Any] | KnowledgeCandidate] = (),
    policy: KnowledgePublicationPolicy = DEFAULT_KNOWLEDGE_PUBLICATION_POLICY,
) -> dict[str, Any]:
    """Run the pinned D03 pipeline and return one self-contained revision record."""
    if revision.get("extraction_version") == "minimal-binding-v1":
        raise ValueError("MINIMAL_BINDING_LEGACY_COMPATIBILITY_ONLY")
    supplied_candidates = tuple(additional_candidates)
    if (
        revision.get("knowledge_publication_result")
        and not supplied_candidates
        and revision.get("knowledge_publication_policy_version") == policy.policy_version
        and revision.get("knowledge_extractor_version") == KNOWLEDGE_EXTRACTOR_VERSION
    ):
        return copy.deepcopy(revision)

    updated = copy.deepcopy(revision)
    revision_id = str(updated["revision_id"])
    extraction_run = build_extraction_run(updated, policy=policy)
    candidates = build_deterministic_candidates(updated, extraction_run=extraction_run)
    candidates.extend(_candidate_model(item) for item in supplied_candidates)

    spans = {str(item["span_id"]): item for item in updated.get("source_spans", [])}
    semantic_ids = {str(item["semantic_unit_id"]) for item in updated.get("semantic_units", [])}
    candidate_name_counts = Counter(
        _normalized(item.proposed_payload.get("knowledge_unit", {}).get("canonical_name", ""))
        for item in candidates
        if isinstance(item, KnowledgeUnitCandidate)
    )

    evaluated: list[KnowledgeCandidate] = []
    published_units: dict[str, KnowledgeUnit] = {
        str(item["knowledge_unit_id"]): KnowledgeUnit.model_validate(item)
        for item in updated.get("knowledge_units", [])
        if item.get("status") == "published"
    }
    knowledge_bindings: list[dict[str, Any]] = []

    for candidate in candidates:
        if isinstance(candidate, RelationCandidate):
            continue
        ref_errors = _reference_errors(
            candidate,
            revision_id=revision_id,
            span_ids=set(spans),
            semantic_ids=semantic_ids,
            anchor_status_by_span=anchor_status_by_span,
            extraction_run_id=extraction_run.extraction_run_id,
        )
        if ref_errors:
            evaluated.append(
                _replace_candidate(candidate, status="rejected", reason_codes=ref_errors)
            )
            continue
        if isinstance(candidate, KnowledgeUnitCandidate):
            try:
                unit = KnowledgeUnit.model_validate(candidate.proposed_payload["knowledge_unit"])
            except (KeyError, ValueError):
                evaluated.append(
                    _replace_candidate(
                        candidate,
                        status="rejected",
                        reason_codes=["KNOWLEDGE_UNIT_SCHEMA_VALIDATION_FAILED"],
                    )
                )
                continue
            if {str(item) for item in unit.evidence_span_ids} != {
                str(item) for item in candidate.source_span_ids
            }:
                evaluated.append(
                    _replace_candidate(
                        candidate,
                        status="rejected",
                        reason_codes=["KNOWLEDGE_UNIT_EVIDENCE_BINDING_MISMATCH"],
                    )
                )
                continue
            name_key = _normalized(unit.canonical_name)
            if candidate_name_counts[name_key] > 1:
                evaluated.append(
                    _replace_candidate(
                        candidate,
                        status="review_required",
                        reason_codes=["ENTITY_RESOLUTION_BLOCKING_AMBIGUITY"],
                    )
                )
                continue
            if candidate.provenance_type == "model_inferred":
                evaluated.append(
                    _replace_candidate(
                        candidate,
                        status="review_required",
                        reason_codes=["MODEL_INFERENCE_REQUIRES_INDEPENDENT_VERIFICATION"],
                    )
                )
                continue
            if candidate.provenance_type not in policy.auto_publish_knowledge_provenance:
                evaluated.append(
                    _replace_candidate(
                        candidate,
                        status="review_required",
                        reason_codes=["PUBLICATION_PROVENANCE_REQUIRES_REVIEW"],
                    )
                )
                continue
            if candidate.proposed_payload.get("structural_basis") != "explicit_heading":
                evaluated.append(
                    _replace_candidate(
                        candidate,
                        status="review_required",
                        reason_codes=["STRUCTURAL_ROOT_REQUIRES_REVIEW"],
                    )
                )
                continue
            published = unit.model_copy(update={"status": "published"})
            published_units[str(published.knowledge_unit_id)] = published
            evaluated.append(
                _replace_candidate(
                    candidate,
                    status="published",
                    reason_codes=["SOURCE_EXPLICIT_KNOWLEDGE_PUBLISHED"],
                )
            )
            knowledge_bindings.append(
                {
                    "knowledge_unit_ref": (
                        f"knowledge_unit:{published.knowledge_unit_id}:v{published.revision}"
                    ),
                    "candidate_id": str(candidate.candidate_id),
                    "extraction_run_id": str(extraction_run.extraction_run_id),
                    "revision_id": revision_id,
                    "source_span_ids": [str(item) for item in candidate.source_span_ids],
                    "publication_policy_version": policy.policy_version,
                }
            )
        elif isinstance(candidate, ConceptCandidate):
            concept_name = _normalized(str(candidate.proposed_payload.get("canonical_name", "")))
            same_name = [
                item
                for item in candidates
                if isinstance(item, ConceptCandidate)
                and _normalized(str(item.proposed_payload.get("canonical_name", "")))
                == concept_name
            ]
            if not concept_name or len(same_name) > 1:
                status = "review_required"
                reasons = ["ENTITY_RESOLUTION_BLOCKING_AMBIGUITY"]
            else:
                status = "verified"
                reasons = ["CONCEPT_CANDIDATE_VERIFIED_NO_SILENT_MERGE"]
            evaluated.append(_replace_candidate(candidate, status=status, reason_codes=reasons))
        else:
            evaluated.append(
                _replace_candidate(
                    candidate,
                    status="verified",
                    reason_codes=["SOURCE_DERIVED_ASSET_CANDIDATE_ONLY"],
                )
            )

    published_relations: list[PrerequisiteRelation] = [
        PrerequisiteRelation.model_validate(item)
        for item in updated.get("relations", [])
        if item.get("status") == "published"
    ]
    adjacency: dict[str, set[str]] = {}
    edge_keys: set[tuple[str, str, str]] = set()
    for relation in published_relations:
        source = str(relation.prerequisite_id)
        target = str(relation.target_knowledge_unit_id)
        adjacency.setdefault(source, set()).add(target)
        edge_keys.add((source, target, relation.strength))
    relation_bindings: list[dict[str, Any]] = []

    for candidate in candidates:
        if not isinstance(candidate, RelationCandidate):
            continue
        ref_errors = _reference_errors(
            candidate,
            revision_id=revision_id,
            span_ids=set(spans),
            semantic_ids=semantic_ids,
            anchor_status_by_span=anchor_status_by_span,
            extraction_run_id=extraction_run.extraction_run_id,
        )
        if ref_errors:
            evaluated.append(
                _replace_candidate(candidate, status="rejected", reason_codes=ref_errors)
            )
            continue
        try:
            relation = PrerequisiteRelation.model_validate(candidate.proposed_payload["relation"])
        except (KeyError, ValueError):
            evaluated.append(
                _replace_candidate(
                    candidate,
                    status="rejected",
                    reason_codes=["RELATION_SCHEMA_VALIDATION_FAILED"],
                )
            )
            continue
        if {str(item) for item in relation.evidence_span_ids} != {
            str(item) for item in candidate.source_span_ids
        }:
            evaluated.append(
                _replace_candidate(
                    candidate,
                    status="rejected",
                    reason_codes=["RELATION_EVIDENCE_BINDING_MISMATCH"],
                )
            )
            continue
        source = str(relation.prerequisite_id)
        target = str(relation.target_knowledge_unit_id)
        if source == target:
            evaluated.append(
                _replace_candidate(
                    candidate,
                    status="rejected",
                    reason_codes=["RELATION_SELF_LOOP_BLOCKED"],
                )
            )
            continue
        if source not in published_units or target not in published_units:
            evaluated.append(
                _replace_candidate(
                    candidate,
                    status="review_required",
                    reason_codes=["RELATION_ENDPOINT_NOT_PUBLISHED"],
                )
            )
            continue
        if relation.strength == "hard" and relation.inference_method == "model":
            evaluated.append(
                _replace_candidate(
                    candidate,
                    status="review_required",
                    reason_codes=["MODEL_ONLY_HARD_PREREQUISITE_BLOCKED"],
                )
            )
            continue
        if relation.inference_method not in policy.hard_prerequisite_inference_methods:
            evaluated.append(
                _replace_candidate(
                    candidate,
                    status="review_required",
                    reason_codes=["RELATION_INFERENCE_METHOD_REQUIRES_REVIEW"],
                )
            )
            continue
        if policy.require_reverse_relation_verification and not _relation_reverse_verified(
            candidate,
            relation,
            spans=spans,
            units=published_units,
            policy=policy,
        ):
            evaluated.append(
                _replace_candidate(
                    candidate,
                    status="review_required",
                    reason_codes=["RELATION_REVERSE_VERIFICATION_FAILED"],
                )
            )
            continue
        edge_key = (source, target, relation.strength)
        if edge_key in edge_keys:
            evaluated.append(
                _replace_candidate(
                    candidate,
                    status="rejected",
                    reason_codes=["RELATION_DUPLICATE_IDENTITY"],
                )
            )
            continue
        if relation.strength == "hard" and _path_exists(adjacency, target, source):
            evaluated.append(
                _replace_candidate(
                    candidate,
                    status="rejected",
                    reason_codes=["HARD_PREREQUISITE_CYCLE_BLOCKED"],
                )
            )
            continue
        published_relation = relation.model_copy(update={"status": "published"})
        published_relations.append(published_relation)
        adjacency.setdefault(source, set()).add(target)
        edge_keys.add(edge_key)
        evaluated.append(
            _replace_candidate(
                candidate,
                status="published",
                reason_codes=["PREREQUISITE_RELATION_PUBLISHED"],
            )
        )
        relation_bindings.append(
            {
                "relation_ref": (
                    f"knowledge_relation:{published_relation.relation_id}:"
                    f"v{published_relation.revision}"
                ),
                "candidate_id": str(candidate.candidate_id),
                "extraction_run_id": str(extraction_run.extraction_run_id),
                "revision_id": revision_id,
                "source_span_ids": [str(item) for item in candidate.source_span_ids],
                "publication_policy_version": policy.policy_version,
            }
        )

    order = {str(candidate.candidate_id): index for index, candidate in enumerate(candidates)}
    evaluated.sort(key=lambda item: order[str(item.candidate_id)])
    review_ids = [item.candidate_id for item in evaluated if item.status == "review_required"]
    rejected_ids = [item.candidate_id for item in evaluated if item.status == "rejected"]
    published_unit_refs = [item["knowledge_unit_ref"] for item in knowledge_bindings]
    published_relation_refs = [item["relation_ref"] for item in relation_bindings]
    reason_codes = ["KNOWLEDGE_PUBLICATION_PIPELINE_COMPLETED"]
    if review_ids:
        reason_codes.append("KNOWLEDGE_REVIEW_REQUIRED")
    if rejected_ids:
        reason_codes.append("KNOWLEDGE_CANDIDATES_REJECTED")
    decision_id = uuid5(extraction_run.extraction_run_id, f"publication:{policy.policy_version}")
    result = KnowledgePublicationResult(
        decision_id=decision_id,
        extraction_run_id=extraction_run.extraction_run_id,
        revision_id=UUID(revision_id),
        policy_version=policy.policy_version,
        candidate_ids=[item.candidate_id for item in evaluated],
        published_knowledge_unit_refs=published_unit_refs,
        published_relation_refs=published_relation_refs,
        review_required_candidate_ids=review_ids,
        rejected_candidate_ids=rejected_ids,
        reason_codes=reason_codes,
        decided_at=extraction_run.created_at,
    )

    original_units = {
        str(item["knowledge_unit_id"]): item for item in updated.get("knowledge_units", [])
    }
    updated["knowledge_units"] = [
        published_units.get(unit_id, KnowledgeUnit.model_validate(item)).model_dump(mode="json")
        for unit_id, item in original_units.items()
    ]
    updated["relations"] = [item.model_dump(mode="json") for item in published_relations]
    updated["knowledge_extractor_version"] = KNOWLEDGE_EXTRACTOR_VERSION
    updated["knowledge_publication_policy_version"] = policy.policy_version
    updated["extraction_runs"] = [extraction_run.model_dump(mode="json")]
    updated["knowledge_candidates"] = [item.model_dump(mode="json") for item in evaluated]
    updated["knowledge_publication_policy"] = policy.model_dump(mode="json")
    updated["knowledge_publication_result"] = result.model_dump(mode="json")
    updated["knowledge_publication_bindings"] = {
        "knowledge_units": knowledge_bindings,
        "relations": relation_bindings,
    }
    return updated


def replay_persisted_knowledge_publication(revision: dict[str, Any]) -> dict[str, Any]:
    """Replay only persisted results; this function has no model/provider dependency."""
    result = KnowledgePublicationResult.model_validate(revision["knowledge_publication_result"])
    run = ExtractionRun.model_validate(revision["extraction_runs"][0])
    if result.extraction_run_id != run.extraction_run_id:
        raise ValueError("KNOWLEDGE_REPLAY_EXTRACTION_RUN_MISMATCH")
    candidate_ids = {
        str(_candidate_model(item).candidate_id) for item in revision["knowledge_candidates"]
    }
    if any(str(item) not in candidate_ids for item in result.candidate_ids):
        raise ValueError("KNOWLEDGE_REPLAY_CANDIDATE_MISSING")
    return {
        "knowledge_units": copy.deepcopy(
            [
                item
                for item in revision.get("knowledge_units", [])
                if item.get("status") == "published"
            ]
        ),
        "relations": copy.deepcopy(
            [item for item in revision.get("relations", []) if item.get("status") == "published"]
        ),
        "publication_result": result.model_dump(mode="json"),
    }


def build_publication_decision_trace(
    revision: dict[str, Any],
    *,
    correlation_id: UUID,
) -> DecisionTrace:
    result = KnowledgePublicationResult.model_validate(revision["knowledge_publication_result"])
    run = ExtractionRun.model_validate(revision["extraction_runs"][0])
    candidates = [_candidate_model(item) for item in revision["knowledge_candidates"]]
    return DecisionTrace(
        decision_id=result.decision_id,
        decision_type="knowledge_publication",
        owner_system="content_knowledge",
        inputs=[
            DecisionInput(entity_type="MaterialRevision", entity_id=result.revision_id, version=1),
            DecisionInput(
                entity_type="ExtractionRun",
                entity_id=result.extraction_run_id,
                version=run.extractor_version,
            ),
            DecisionInput(
                entity_type="KnowledgePublicationPolicy",
                entity_id=result.policy_version,
                version=result.policy_version,
            ),
        ],
        candidates=[
            {
                "candidate_id": str(item.candidate_id),
                "candidate_type": item.candidate_type,
                "status": item.status,
                "reason_codes": item.reason_codes,
            }
            for item in candidates
        ],
        selected={
            "knowledge_unit_refs": result.published_knowledge_unit_refs,
            "relation_refs": result.published_relation_refs,
        },
        constraints=[
            {"constraint": "current_revision_replayable_evidence", "required": True},
            {"constraint": "no_model_only_hard_prerequisite", "required": True},
            {"constraint": "no_self_loop_duplicate_or_hard_cycle", "required": True},
        ],
        reason_codes=result.reason_codes,
        confidence=None,
        algorithm=DecisionAlgorithm(
            algorithm_id="knowledge-publication-pipeline",
            algorithm_version=result.policy_version,
            model_inference_ids=[],
            prompt_versions=[],
        ),
        experiment=DecisionExperiment(),
        created_at=result.decided_at,
        correlation_id=correlation_id,
        trace_id=f"knowledge-publication:{result.decision_id}",
    )


def build_publication_events(
    revision: dict[str, Any],
    *,
    user_id: UUID,
    correlation_id: UUID,
) -> list[LearningEventEnvelope]:
    """Create minimal exact-ref publication events owned by SYS01."""
    result = KnowledgePublicationResult.model_validate(revision["knowledge_publication_result"])
    run = ExtractionRun.model_validate(revision["extraction_runs"][0])
    if not result.published_knowledge_unit_refs and not result.published_relation_refs:
        return []
    actor = EventActor(actor_type="system", actor_id="SYS01")
    context = EventContext(
        user_id=user_id,
        knowledge_unit_ids=[
            UUID(ref.split(":")[1]) for ref in result.published_knowledge_unit_refs
        ],
        content_revision_ids=[result.revision_id],
    )
    provenance = EventProvenance(
        source="domain",
        model_provider=run.model_provider,
        model_name=run.model_name,
        model_snapshot=run.model_snapshot,
        prompt_version=run.prompt_version,
        policy_version=result.policy_version,
        algorithm_version=run.extractor_version,
    )
    trace = EventTrace(trace_id=f"knowledge-publication:{result.decision_id}")
    privacy = EventPrivacy(
        classification="personal",
        external_processing=False,
        retention_class="core_learning",
    )
    events = [
        LearningEventEnvelope(
            event_id=uuid5(result.revision_id, f"ContentPublished:{result.decision_id}"),
            event_type="ContentPublished",
            aggregate_type="MaterialRevision",
            aggregate_id=result.revision_id,
            aggregate_version=1,
            sequence=1,
            occurred_at=result.decided_at,
            recorded_at=result.decided_at,
            idempotency_key=f"content-published:{result.revision_id}:{result.extraction_run_id}",
            correlation_id=correlation_id,
            actor=actor,
            context=context,
            payload={
                "revision_id": str(result.revision_id),
                "extraction_run_id": str(result.extraction_run_id),
                "publication_policy_version": result.policy_version,
                "candidate_ids": [str(item) for item in result.candidate_ids],
                "published_knowledge_unit_refs": result.published_knowledge_unit_refs,
                "reason_codes": result.reason_codes,
            },
            provenance=provenance,
            trace=trace,
            privacy=privacy,
        )
    ]
    relations = {
        f"knowledge_relation:{item['relation_id']}:v{item['revision']}": item
        for item in revision.get("relations", [])
        if item.get("status") == "published"
    }
    bindings = {
        item["relation_ref"]: item
        for item in revision.get("knowledge_publication_bindings", {}).get("relations", [])
    }
    for relation_ref in result.published_relation_refs:
        relation = relations[relation_ref]
        binding = bindings[relation_ref]
        relation_id = UUID(relation["relation_id"])
        events.append(
            LearningEventEnvelope(
                event_id=uuid5(relation_id, f"KnowledgeRelationPublished:{result.decision_id}"),
                event_type="KnowledgeRelationPublished",
                aggregate_type="KnowledgeRelation",
                aggregate_id=relation_id,
                aggregate_version=relation["revision"],
                sequence=relation["revision"],
                occurred_at=result.decided_at,
                recorded_at=result.decided_at,
                idempotency_key=f"knowledge-relation-published:{relation_id}:v{relation['revision']}",
                correlation_id=correlation_id,
                actor=actor,
                context=context,
                payload={
                    "relation_ref": relation_ref,
                    "candidate_id": binding["candidate_id"],
                    "revision_id": str(result.revision_id),
                    "source_span_ids": relation["evidence_span_ids"],
                    "extraction_run_id": str(result.extraction_run_id),
                    "publication_policy_version": result.policy_version,
                    "reason_codes": ["PREREQUISITE_RELATION_PUBLISHED"],
                },
                provenance=provenance,
                trace=trace,
                privacy=privacy,
            )
        )
    return events

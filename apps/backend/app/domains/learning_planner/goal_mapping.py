"""Deterministic SPEC-D04 goal formation, mapping and subgraph projection."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import NAMESPACE_URL, UUID, uuid5

from app.contracts.adaptive import VersionedRef
from app.contracts.planning import (
    ConfirmedLearningGoal,
    GoalKnowledgeMappingV1,
    GoalSpecificKnowledgeSubgraphV1,
    GoalTargetEvidenceV1,
    LearningGoalV1,
)
from app.queries.goal_knowledge import (
    PublishedGoalKnowledgeScope,
    PublishedKnowledgeRelationView,
    PublishedKnowledgeUnitView,
)

MAPPER_VERSION = "goal-knowledge-rrf-v1"
CLOSURE_POLICY_VERSION = "published-hard-prerequisite-closure-v1"
_BROAD_MARKERS = ("全书", "整本", "核心思想", "whole book", "core idea", "overview")
_UNMEASURABLE_MARKERS = ("了解", "熟悉", "看完", "understand", "familiar", "read")


@dataclass(frozen=True)
class GoalMappingDecision:
    mapping: GoalKnowledgeMappingV1
    subgraph: GoalSpecificKnowledgeSubgraphV1 | None
    planner_goal: ConfirmedLearningGoal | None


def measurable_success_criterion(topic: str, raw_intent: str) -> tuple[str, tuple[str, ...]]:
    """Convert vague intent to a bounded assessment-compatible candidate."""
    if any(marker in raw_intent.casefold() for marker in _UNMEASURABLE_MARKERS):
        return (
            f"能够不依赖原文解释 {topic} 的关键概念，并在新例子中正确应用",
            ("SUCCESS_CRITERIA_REWRITTEN_MEASURABLE",),
        )
    return (
        f"能够解释并应用 {topic}，且用来源材料证据支持结论",
        ("SUCCESS_CRITERIA_MEASURABLE_BASELINE",),
    )


class GoalKnowledgeMapper:
    """SYS06 mapper; consumes immutable SYS01 views and writes no knowledge facts."""

    mapper_version = MAPPER_VERSION
    max_broad_targets = 3

    def map(
        self,
        *,
        goal: LearningGoalV1,
        scope: PublishedGoalKnowledgeScope,
        mapping_version: int,
        created_at: datetime,
        persisted_semantic_scores: dict[UUID, float] | None = None,
        model_reason_codes: tuple[str, ...] = (),
    ) -> GoalMappingDecision:
        mapping_id = uuid5(goal.goal_id, "goal-knowledge-mapping")
        base_reasons = list(model_reason_codes)
        if not goal.source_document_ids or not scope.authorized_document_ids:
            mapping = self._blocked(
                mapping_id=mapping_id,
                goal=goal,
                scope=scope,
                mapping_version=mapping_version,
                created_at=created_at,
                reasons=(*base_reasons, "SOURCE_SCOPE_EMPTY"),
                question="请选择至少一份已完成处理且有权限访问的学习资料。",
            )
            return GoalMappingDecision(mapping=mapping, subgraph=None, planner_goal=None)
        if scope.missing_document_ids:
            mapping = self._blocked(
                mapping_id=mapping_id,
                goal=goal,
                scope=scope,
                mapping_version=mapping_version,
                created_at=created_at,
                reasons=(*base_reasons, "SOURCE_SCOPE_UNAUTHORIZED_OR_UNAVAILABLE"),
                question="目标包含不可用资料，请确认并重新选择学习资料范围。",
            )
            return GoalMappingDecision(mapping=mapping, subgraph=None, planner_goal=None)

        query = " ".join(
            (
                goal.title,
                goal.topic,
                *goal.target_capabilities,
                goal.application_context or "",
                *goal.success_criteria,
            )
        )
        broad = any(marker in query.casefold() for marker in _BROAD_MARKERS)
        evidence = self._rank(
            query=query,
            units=scope.units,
            broad=broad,
            semantic_scores=persisted_semantic_scores or {},
        )
        if not evidence:
            reasons = [*base_reasons, "NO_PUBLISHED_TARGET_MATCH"]
            if self._incomplete_match(query, scope.incomplete_candidate_terms):
                reasons.append("CONTENT_MODEL_INCOMPLETE")
            mapping = self._blocked(
                mapping_id=mapping_id,
                goal=goal,
                scope=scope,
                mapping_version=mapping_version,
                created_at=created_at,
                reasons=tuple(reasons),
                question="当前已发布知识中没有明确匹配项；请缩小主题或等待内容复核完成。",
            )
            return GoalMappingDecision(mapping=mapping, subgraph=None, planner_goal=None)

        if self._is_blocking_ambiguity(query, evidence, scope.units):
            mapping = GoalKnowledgeMappingV1(
                mapping_id=mapping_id,
                mapping_version=mapping_version,
                goal_id=goal.goal_id,
                goal_version=goal.version,
                source_document_ids=scope.authorized_document_ids,
                knowledge_graph_versions=scope.knowledge_graph_versions,
                candidate_target_ids=tuple(item.knowledge_unit_id for item in evidence),
                selected_target_ids=(),
                excluded_target_ids=tuple(item.knowledge_unit_id for item in evidence),
                target_evidence=evidence,
                confidence=None,
                reason_codes=(*base_reasons, "AMBIGUOUS_GOAL_MAPPING"),
                mapper_version=self.mapper_version,
                model_inference_refs=goal.model_inference_refs,
                status="blocked",
                clarification_question=self._ambiguity_question(evidence, scope.units),
                created_at=created_at,
            )
            return GoalMappingDecision(mapping=mapping, subgraph=None, planner_goal=None)

        if broad:
            target_count = min(self.max_broad_targets, len(evidence))
        else:
            unit_names = {
                item.knowledge_unit_id: item.canonical_name.casefold() for item in scope.units
            }
            explicit_count = sum(
                unit_names[item.knowledge_unit_id] in query.casefold() for item in evidence[:2]
            )
            target_count = min(len(evidence), max(1, explicit_count))
        normalized_names = {
            item.knowledge_unit_id: " ".join(item.canonical_name.casefold().split())
            for item in scope.units
        }
        selected_evidence: list[GoalTargetEvidenceV1] = []
        seen_names: set[str] = set()
        for item in evidence:
            normalized_name = normalized_names[item.knowledge_unit_id]
            if normalized_name in seen_names:
                continue
            selected_evidence.append(item)
            seen_names.add(normalized_name)
            if len(selected_evidence) >= target_count:
                break
        selected_ids = tuple(item.knowledge_unit_id for item in selected_evidence)
        reasons = [*base_reasons, "GOAL_TARGETS_DETERMINISTIC_RRF_SELECTED"]
        if broad:
            reasons.append("GOAL_BROAD_SCOPE_LIMITED_TARGET_SET")
        if len(selected_evidence) < min(target_count, len(evidence)):
            reasons.append("GOAL_REDUNDANCY_REPAIRED")
        status: Literal["candidate", "confirmed"] = (
            "confirmed" if goal.status in {"confirmed", "active"} else "candidate"
        )
        mapping = GoalKnowledgeMappingV1(
            mapping_id=mapping_id,
            mapping_version=mapping_version,
            goal_id=goal.goal_id,
            goal_version=goal.version,
            source_document_ids=scope.authorized_document_ids,
            knowledge_graph_versions=scope.knowledge_graph_versions,
            candidate_target_ids=tuple(item.knowledge_unit_id for item in evidence),
            selected_target_ids=selected_ids,
            excluded_target_ids=tuple(
                item.knowledge_unit_id
                for item in evidence
                if item.knowledge_unit_id not in set(selected_ids)
            ),
            target_evidence=evidence,
            confidence=self._confidence(evidence),
            reason_codes=tuple(reasons),
            mapper_version=self.mapper_version,
            model_inference_refs=goal.model_inference_refs,
            status=status,
            created_at=created_at,
        )
        if status != "confirmed":
            return GoalMappingDecision(mapping=mapping, subgraph=None, planner_goal=None)
        subgraph = self.build_subgraph(mapping=mapping, scope=scope, created_at=created_at)
        planner_goal = ConfirmedLearningGoal(
            goal_id=goal.goal_id,
            objective_id=uuid5(
                NAMESPACE_URL,
                f"askora:objective:{goal.goal_id}:v{goal.version}:mapping:{mapping_version}",
            ),
            target_knowledge_unit_ids=list(selected_ids),
            confirmed_at=goal.confirmed_at or goal.created_at,
        )
        return GoalMappingDecision(
            mapping=mapping,
            subgraph=subgraph,
            planner_goal=planner_goal,
        )

    def build_subgraph(
        self,
        *,
        mapping: GoalKnowledgeMappingV1,
        scope: PublishedGoalKnowledgeScope,
        created_at: datetime,
    ) -> GoalSpecificKnowledgeSubgraphV1:
        if mapping.status != "confirmed":
            raise ValueError("GOAL_MAPPING_NOT_CONFIRMED")
        in_scope_units = {item.knowledge_unit_id for item in scope.units}
        closure = set(mapping.selected_target_ids)
        included_prerequisites: set[UUID] = set()
        included_relations: list[PublishedKnowledgeRelationView] = []
        changed = True
        while changed:
            changed = False
            for relation in scope.relations:
                if relation.strength != "hard":
                    continue
                if relation.target_knowledge_unit_id not in closure:
                    continue
                if relation.prerequisite_id not in in_scope_units:
                    continue
                if relation.relation_id not in {item.relation_id for item in included_relations}:
                    included_relations.append(relation)
                if relation.prerequisite_id not in closure:
                    closure.add(relation.prerequisite_id)
                    included_prerequisites.add(relation.prerequisite_id)
                    changed = True
        relation_refs = tuple(
            self._versioned_relation_ref(item.relation_ref)
            for item in sorted(included_relations, key=lambda item: str(item.relation_id))
        )
        return GoalSpecificKnowledgeSubgraphV1(
            subgraph_id=uuid5(mapping.mapping_id, "goal-specific-knowledge-subgraph"),
            version=mapping.mapping_version,
            goal_mapping_ref=VersionedRef(
                entity_type="goal_knowledge_mapping",
                entity_id=str(mapping.mapping_id),
                version=str(mapping.mapping_version),
            ),
            target_knowledge_unit_ids=mapping.selected_target_ids,
            included_prerequisite_ids=tuple(sorted(included_prerequisites, key=str)),
            relation_refs=relation_refs,
            knowledge_graph_versions=mapping.knowledge_graph_versions,
            closure_policy_version=CLOSURE_POLICY_VERSION,
            reason_codes=("PUBLISHED_HARD_PREREQUISITE_CLOSURE_BUILT",),
            created_at=created_at,
        )

    def _rank(
        self,
        *,
        query: str,
        units: tuple[PublishedKnowledgeUnitView, ...],
        broad: bool,
        semantic_scores: dict[UUID, float],
    ) -> tuple[GoalTargetEvidenceV1, ...]:
        if broad:
            lexical_scores = {item.knowledge_unit_id: 1.0 for item in units}
        else:
            lexical_scores = {
                item.knowledge_unit_id: _overlap_score(
                    query,
                    " ".join((item.canonical_name, item.description)),
                )
                for item in units
            }
        hierarchy_scores = {
            item.knowledge_unit_id: _overlap_score(query, " ".join(item.hierarchy_labels))
            for item in units
        }
        capability_scores = {item.knowledge_unit_id: _capability_fit(query, item) for item in units}
        rankings = {
            "lexical": _positive_rank(lexical_scores),
            "semantic": _positive_rank(semantic_scores),
            "hierarchy": _positive_rank(hierarchy_scores),
            "capability": _positive_rank(capability_scores),
        }
        unit_by_id = {item.knowledge_unit_id: item for item in units}
        candidate_ids = set().union(*(set(value) for value in rankings.values()))
        ranked: list[GoalTargetEvidenceV1] = []
        for unit_id in candidate_ids:
            positions = {
                name: position
                for name, rank in rankings.items()
                if (position := rank.get(unit_id)) is not None
            }
            fusion_score = sum(1.0 / (60 + position) for position in positions.values())
            unit = unit_by_id[unit_id]
            reasons = ["GOAL_SCOPE_ALLOWED", "GOAL_RRF_CANDIDATE"]
            if "lexical" in positions:
                reasons.append("GOAL_LEXICAL_MATCH")
            if "semantic" in positions:
                reasons.append("GOAL_PERSISTED_SEMANTIC_MATCH")
            if "hierarchy" in positions:
                reasons.append("GOAL_HIERARCHY_MATCH")
            if "capability" in positions:
                reasons.append("GOAL_CAPABILITY_KIND_FIT")
            ranked.append(
                GoalTargetEvidenceV1(
                    knowledge_unit_id=unit_id,
                    knowledge_unit_ref=unit.knowledge_unit_ref,
                    source_document_id=unit.source_document_id,
                    material_revision_id=unit.material_revision_id,
                    source_span_ids=unit.source_span_ids,
                    rank_positions=positions,
                    fusion_score=fusion_score,
                    reason_codes=tuple(reasons),
                )
            )
        return tuple(
            sorted(
                ranked,
                key=lambda item: (-item.fusion_score, str(item.knowledge_unit_id)),
            )
        )

    @staticmethod
    def _is_blocking_ambiguity(
        query: str,
        evidence: tuple[GoalTargetEvidenceV1, ...],
        units: tuple[PublishedKnowledgeUnitView, ...],
    ) -> bool:
        if any(marker in query.casefold() for marker in _BROAD_MARKERS):
            return False
        if len(evidence) < 2 or abs(evidence[0].fusion_score - evidence[1].fusion_score) > 0.001:
            return False
        names = {item.knowledge_unit_id: item.canonical_name.casefold() for item in units}
        normalized_query = query.casefold()
        explicit = [names[item.knowledge_unit_id] in normalized_query for item in evidence[:2]]
        return not all(explicit)

    @staticmethod
    def _ambiguity_question(
        evidence: tuple[GoalTargetEvidenceV1, ...],
        units: tuple[PublishedKnowledgeUnitView, ...],
    ) -> str:
        names = {item.knowledge_unit_id: item.canonical_name for item in units}
        choices = "、".join(names[item.knowledge_unit_id] for item in evidence[:2])
        return f"目标可能对应 {choices}；请明确希望优先掌握哪一个。"

    @staticmethod
    def _confidence(evidence: tuple[GoalTargetEvidenceV1, ...]) -> float:
        if len(evidence) == 1:
            return 1.0
        top, second = evidence[0].fusion_score, evidence[1].fusion_score
        return max(0.0, min(1.0, (top - second) / top if top else 0.0))

    @staticmethod
    def _incomplete_match(query: str, terms: tuple[str, ...]) -> bool:
        return any(_overlap_score(query, item) > 0 for item in terms)

    def _blocked(
        self,
        *,
        mapping_id: UUID,
        goal: LearningGoalV1,
        scope: PublishedGoalKnowledgeScope,
        mapping_version: int,
        created_at: datetime,
        reasons: tuple[str, ...],
        question: str,
    ) -> GoalKnowledgeMappingV1:
        return GoalKnowledgeMappingV1(
            mapping_id=mapping_id,
            mapping_version=mapping_version,
            goal_id=goal.goal_id,
            goal_version=goal.version,
            source_document_ids=scope.authorized_document_ids,
            knowledge_graph_versions=scope.knowledge_graph_versions,
            candidate_target_ids=(),
            selected_target_ids=(),
            excluded_target_ids=(),
            target_evidence=(),
            confidence=None,
            reason_codes=reasons,
            mapper_version=self.mapper_version,
            model_inference_refs=goal.model_inference_refs,
            status="blocked",
            clarification_question=question,
            created_at=created_at,
        )

    @staticmethod
    def _versioned_relation_ref(value: str) -> VersionedRef:
        parts = value.split(":")
        if len(parts) != 3:
            raise ValueError("GOAL_SUBGRAPH_RELATION_REF_INVALID")
        return VersionedRef(
            entity_type="knowledge_relation",
            entity_id=parts[1],
            version=parts[2].removeprefix("v"),
        )


def _tokens(value: str) -> Counter[str]:
    lowered = value.casefold()
    words = re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", lowered)
    compact_cn = "".join(re.findall(r"[\u4e00-\u9fff]", lowered))
    bigrams = [compact_cn[index : index + 2] for index in range(max(0, len(compact_cn) - 1))]
    return Counter((*words, *bigrams))


def _overlap_score(left: str, right: str) -> float:
    left_tokens = _tokens(left)
    right_tokens = _tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    overlap = sum(min(count, right_tokens[token]) for token, count in left_tokens.items())
    return overlap / sum(left_tokens.values())


def _positive_rank(scores: dict[UUID, float]) -> dict[UUID, int]:
    return {
        unit_id: index
        for index, (unit_id, score) in enumerate(
            sorted(scores.items(), key=lambda item: (-item[1], str(item[0]))),
            1,
        )
        if score > 0
    }


def _capability_fit(query: str, unit: PublishedKnowledgeUnitView) -> float:
    lowered = query.casefold()
    description = unit.description.casefold()
    score = 0.0
    if any(marker in lowered for marker in ("解释", "explain", "理解", "understand")):
        if unit.kind == "concept" or any(
            marker in description for marker in ("definition", "定义")
        ):
            score += 1.0
    if any(marker in lowered for marker in ("应用", "apply", "解决", "solve")):
        if any(marker in description for marker in ("procedure", "example", "步骤", "例")):
            score += 1.0
        else:
            score += 0.25
    return score

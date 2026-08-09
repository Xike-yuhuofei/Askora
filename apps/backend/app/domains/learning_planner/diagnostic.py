"""Deterministic SPEC-D05 graph-adaptive prerequisite diagnostic decisions."""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime
from uuid import NAMESPACE_URL, UUID, uuid5

from app.contracts.adaptive import VersionedRef
from app.contracts.learning import MasteryEstimate
from app.contracts.planning import (
    DiagnosticNeedV1,
    DiagnosticPrerequisiteEdgeV1,
)


class PrerequisiteDiagnosticPlanner:
    """SYS06 selection only; grading and learner projection remain external owners."""

    PLANNER_VERSION = "graph-adaptive-diagnostic-v1"
    BUDGET_POLICY_VERSION = "diagnostic-budget-v1"
    CURRENT_EVIDENCE_PROFILE_VERSION = "diagnostic-current-evidence-v1"
    MIN_CURRENT_CONFIDENCE = 0.25
    READY_COMPETENCE = 0.70

    def build_need(
        self,
        *,
        user_id: UUID,
        goal_mapping_ref: VersionedRef,
        goal_subgraph_ref: VersionedRef,
        target_knowledge_unit_id: UUID,
        prerequisite_ids: tuple[UUID, ...],
        edges: tuple[DiagnosticPrerequisiteEdgeV1, ...],
        mastery: dict[UUID, MasteryEstimate | None],
        learner_state_version: int,
        knowledge_graph_versions: tuple[str, ...],
        learning_planner_version: str,
        max_attempts: int,
        attempts_used: int,
        version: int,
        created_at: datetime,
        assessment_result_refs: tuple[VersionedRef, ...] = (),
        supersedes_version: int | None = None,
    ) -> DiagnosticNeedV1:
        need_id = uuid5(
            NAMESPACE_URL,
            f"askora:diagnostic-need:{user_id}:{goal_mapping_ref.entity_id}:"
            f"{goal_mapping_ref.version}:{target_knowledge_unit_id}",
        )
        unknown, unmet, sufficient = self._classify(prerequisite_ids, mastery)
        children = self._children(edges)
        candidates: set[UUID] = set()
        remediation_required = False
        direct_ids = children.get(target_knowledge_unit_id, ())
        for direct_id in direct_ids:
            if direct_id in unknown:
                candidates.add(direct_id)
            elif direct_id in unmet:
                deeper = self._first_unresolved_descendants(
                    direct_id,
                    children=children,
                    unknown=unknown,
                    unmet=unmet,
                    sufficient=sufficient,
                )
                if deeper:
                    candidates.update(deeper)
                else:
                    remediation_required = True

        current: UUID | None = None
        status = "active"
        stop_reason = None
        reasons = [
            self.PLANNER_VERSION,
            self.BUDGET_POLICY_VERSION,
            self.CURRENT_EVIDENCE_PROFILE_VERSION,
            "DIAGNOSTIC_DECISION_RELEVANT_ONLY",
        ]
        if not prerequisite_ids:
            status = "resolved"
            stop_reason = "TARGET_READY"
            reasons.append("DIAGNOSTIC_TARGET_HAS_NO_HARD_PREREQUISITE")
        elif not candidates:
            if remediation_required or any(item in unmet for item in direct_ids):
                status = "stopped"
                stop_reason = "REMEDIATION_REQUIRED"
                reasons.append("DIAGNOSTIC_DIRECT_PREREQUISITE_UNMET")
            else:
                status = "resolved"
                stop_reason = "ALL_DECISION_RELEVANT_PREREQUISITES_RESOLVED"
                reasons.append("DIAGNOSTIC_DIRECT_PREREQUISITES_HAVE_CURRENT_EVIDENCE")
        elif attempts_used >= max_attempts:
            status = "stopped"
            stop_reason = "DIAGNOSTIC_BUDGET_EXHAUSTED"
            reasons.append("DIAGNOSTIC_UNKNOWN_PRESERVED_AT_BUDGET_STOP")
        else:
            current = self._select(candidates, edges)
            reasons.extend(
                (
                    "DIAGNOSTIC_HIGH_VALUE_PREREQUISITE_SELECTED",
                    "DIAGNOSTIC_ITEM_REQUIRED",
                )
            )

        return DiagnosticNeedV1(
            need_id=need_id,
            version=version,
            user_id=user_id,
            goal_mapping_ref=goal_mapping_ref,
            goal_subgraph_ref=goal_subgraph_ref,
            target_knowledge_unit_id=target_knowledge_unit_id,
            prerequisite_knowledge_unit_ids=tuple(sorted(set(prerequisite_ids), key=str)),
            prerequisite_edges=tuple(
                sorted(edges, key=lambda item: str(item.relation_ref.entity_id))
            ),
            unknown_ids=tuple(sorted(unknown, key=str)),
            unmet_ids=tuple(sorted(unmet, key=str)),
            sufficient_current_evidence_ids=tuple(sorted(sufficient, key=str)),
            reason_codes=tuple(reasons),
            planner_version=learning_planner_version,
            diagnostic_planner_version=self.PLANNER_VERSION,
            budget_policy_version=self.BUDGET_POLICY_VERSION,
            max_attempts=max_attempts,
            attempts_used=attempts_used,
            created_from_learner_state_version=learner_state_version,
            knowledge_graph_versions=knowledge_graph_versions,
            current_knowledge_unit_id=current,
            assessment_result_refs=assessment_result_refs,
            status=status,  # type: ignore[arg-type]
            stop_reason=stop_reason,  # type: ignore[arg-type]
            created_at=created_at,
            supersedes_version=supersedes_version,
        )

    def _classify(
        self,
        prerequisite_ids: tuple[UUID, ...],
        mastery: dict[UUID, MasteryEstimate | None],
    ) -> tuple[set[UUID], set[UUID], set[UUID]]:
        unknown: set[UUID] = set()
        unmet: set[UUID] = set()
        sufficient: set[UUID] = set()
        for knowledge_unit_id in prerequisite_ids:
            estimate = mastery.get(knowledge_unit_id)
            if (
                estimate is None
                or estimate.competence_probability is None
                or estimate.confidence < self.MIN_CURRENT_CONFIDENCE
                or estimate.evidence_count == 0
            ):
                unknown.add(knowledge_unit_id)
            elif (
                estimate.competence_probability >= self.READY_COMPETENCE
                and estimate.independent_success_count > 0
            ):
                sufficient.add(knowledge_unit_id)
            else:
                unmet.add(knowledge_unit_id)
        return unknown, unmet, sufficient

    @staticmethod
    def _children(
        edges: tuple[DiagnosticPrerequisiteEdgeV1, ...],
    ) -> dict[UUID, tuple[UUID, ...]]:
        mutable: dict[UUID, set[UUID]] = defaultdict(set)
        for edge in edges:
            mutable[edge.target_knowledge_unit_id].add(edge.prerequisite_id)
        return {
            target: tuple(sorted(prerequisites, key=str))
            for target, prerequisites in mutable.items()
        }

    @staticmethod
    def _first_unresolved_descendants(
        root: UUID,
        *,
        children: dict[UUID, tuple[UUID, ...]],
        unknown: set[UUID],
        unmet: set[UUID],
        sufficient: set[UUID],
    ) -> tuple[UUID, ...]:
        del sufficient
        immediate = children.get(root, ())
        direct_unknown = tuple(item for item in immediate if item in unknown)
        if direct_unknown:
            return direct_unknown
        queue = deque(item for item in immediate if item in unmet)
        visited: set[UUID] = set()
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            next_items = children.get(current, ())
            found = tuple(item for item in next_items if item in unknown)
            if found:
                return found
            queue.extend(item for item in next_items if item in unmet)
        return ()

    @staticmethod
    def _select(
        candidates: set[UUID],
        edges: tuple[DiagnosticPrerequisiteEdgeV1, ...],
    ) -> UUID:
        downstream_value: dict[UUID, int] = defaultdict(int)
        for edge in edges:
            downstream_value[edge.prerequisite_id] += 1
        return min(candidates, key=lambda item: (-downstream_value[item], str(item)))

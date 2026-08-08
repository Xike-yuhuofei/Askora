"""SPEC-D05 application orchestration across existing SYS04/SYS03/SYS06 owners."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.adaptive import VersionedRef
from app.contracts.assessment import AssistanceSnapshot
from app.contracts.events import (
    EventActor,
    EventContext,
    EventPrivacy,
    EventProvenance,
    EventTrace,
    LearningEventEnvelope,
)
from app.contracts.learning import AssessmentResult, LearnerStateV1, LearningActivity, LearningPlan
from app.contracts.planning import (
    ConfirmedLearningGoal,
    DiagnosticNeedV1,
    DiagnosticPrerequisiteEdgeV1,
    GoalKnowledgeMappingV1,
    GoalSpecificKnowledgeSubgraphV1,
    LearningGoalV1,
)
from app.domains.assessment import ScoringUnavailableError
from app.domains.learner_model.diagnostic_state import (
    CanonicalMasteryProjectionPort,
    DiagnosticLearnerStateService,
)
from app.domains.learning_planner import LearningPlanner, PrerequisiteDiagnosticPlanner
from app.infrastructure.ledger import LearningEventRepository
from app.infrastructure.planning_records import (
    DiagnosticNeedRepository,
    GoalPlanningRepository,
    LearningPlanRepository,
)
from app.models.user import User
from app.queries.diagnostic_assessment import DiagnosticAssessmentItemQuery
from app.queries.goal_knowledge import GoalKnowledgeQueryService, PublishedGoalKnowledgeScope
from app.services.assessment.canonical_service import (
    CanonicalAssessmentService,
    ScoredAssessmentRecord,
)


@dataclass(frozen=True)
class DiagnosticBootstrapResult:
    need: DiagnosticNeedV1
    learner_state: LearnerStateV1
    plan: LearningPlan | None
    activities: tuple[LearningActivity, ...]
    assessment_result: AssessmentResult | None = None


class DiagnosticAssessmentPort(Protocol):
    async def score_submission_with_attempt(
        self,
        *,
        item: Any,
        user_id: UUID,
        response: Any,
        assistance: AssistanceSnapshot,
        idempotency_key: str,
        correlation_id: str,
    ) -> ScoredAssessmentRecord: ...


class PrerequisiteDiagnosticService:
    """Coordinates owner commands without owning grading, mastery, or plans."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        assessment_service: DiagnosticAssessmentPort | None = None,
        learner_projector: CanonicalMasteryProjectionPort,
        diagnostic_planner: PrerequisiteDiagnosticPlanner | None = None,
        learning_planner: LearningPlanner | None = None,
    ) -> None:
        self._session = session
        self._goal_repo = GoalPlanningRepository(session)
        self._need_repo = DiagnosticNeedRepository(session)
        self._plan_repo = LearningPlanRepository(session)
        self._knowledge = GoalKnowledgeQueryService(session)
        self._items = DiagnosticAssessmentItemQuery(session)
        self._assessment = assessment_service or CanonicalAssessmentService(session)
        self._learner = DiagnosticLearnerStateService(session, mastery_projector=learner_projector)
        self._diagnostic_planner = diagnostic_planner or PrerequisiteDiagnosticPlanner()
        self._learning_planner = learning_planner or LearningPlanner()

    async def create_need(
        self,
        *,
        user: User,
        mapping_id: UUID,
        mapping_version: int,
        subgraph_id: UUID,
        subgraph_version: int,
        target_knowledge_unit_id: UUID,
        max_attempts: int,
        idempotency_key: str,
        correlation_id: UUID,
        created_at: datetime,
    ) -> DiagnosticBootstrapResult:
        existing = await self._need_repo.find_by_idempotency(idempotency_key)
        if existing is not None:
            return await self._existing_result(existing, plan_key=f"{idempotency_key}:plan")

        goal, mapping, subgraph, scope, edges = await self._load_inputs(
            user=user,
            mapping_id=mapping_id,
            mapping_version=mapping_version,
            subgraph_id=subgraph_id,
            subgraph_version=subgraph_version,
            target_knowledge_unit_id=target_knowledge_unit_id,
        )
        knowledge_ids = self._knowledge_ids(subgraph)
        state, estimates = await self._learner.current_state(
            user_id=UUID(user.id),
            knowledge_unit_ids=knowledge_ids,
            created_at=created_at,
        )
        mastery = {item.knowledge_unit_id: item for item in estimates}
        need = self._diagnostic_planner.build_need(
            user_id=UUID(user.id),
            goal_mapping_ref=VersionedRef(
                entity_type="goal_knowledge_mapping",
                entity_id=str(mapping.mapping_id),
                version=mapping.mapping_version,
            ),
            goal_subgraph_ref=VersionedRef(
                entity_type="goal_specific_knowledge_subgraph",
                entity_id=str(subgraph.subgraph_id),
                version=subgraph.version,
            ),
            target_knowledge_unit_id=target_knowledge_unit_id,
            prerequisite_ids=subgraph.included_prerequisite_ids,
            edges=edges,
            mastery={item: mastery.get(item) for item in subgraph.included_prerequisite_ids},
            learner_state_version=state.version,
            knowledge_graph_versions=subgraph.knowledge_graph_versions,
            learning_planner_version=self._learning_planner.PLANNER_VERSION,
            max_attempts=max_attempts,
            attempts_used=0,
            version=1,
            created_at=created_at,
        )
        prior_need = await self._need_repo.latest(need_id=need.need_id, user_id=UUID(user.id))
        if prior_need is not None:
            need = self._diagnostic_planner.build_need(
                user_id=UUID(user.id),
                goal_mapping_ref=need.goal_mapping_ref,
                goal_subgraph_ref=need.goal_subgraph_ref,
                target_knowledge_unit_id=target_knowledge_unit_id,
                prerequisite_ids=subgraph.included_prerequisite_ids,
                edges=edges,
                mastery={item: mastery.get(item) for item in subgraph.included_prerequisite_ids},
                learner_state_version=state.version,
                knowledge_graph_versions=subgraph.knowledge_graph_versions,
                learning_planner_version=self._learning_planner.PLANNER_VERSION,
                max_attempts=max_attempts,
                attempts_used=0,
                version=await self._need_repo.next_version(need.need_id),
                created_at=created_at,
                supersedes_version=prior_need.version,
            )
        need = await self._attach_item_or_stop(need)
        need = await self._need_repo.save(need, idempotency_key=idempotency_key)
        plan, activities = await self._generate_plan(
            goal=goal,
            mapping=mapping,
            edges=edges,
            mastery=mastery,
            learner_state_version=state.version,
            created_at=created_at,
            idempotency_key=f"{idempotency_key}:plan",
            reason_codes=["PLAN_INITIAL_DIAGNOSTIC_BOOTSTRAP"],
        )
        await self._append_diagnostic_event(
            need=need,
            event_type="DiagnosticStarted",
            correlation_id=correlation_id,
            idempotency_key=f"diagnostic-started:{idempotency_key}",
        )
        return DiagnosticBootstrapResult(
            need=need,
            learner_state=state,
            plan=plan,
            activities=activities,
        )

    async def submit_response(
        self,
        *,
        user: User,
        need_id: UUID,
        expected_need_version: int,
        response: Any,
        assistance: AssistanceSnapshot,
        idempotency_key: str,
        correlation_id: UUID,
        submitted_at: datetime,
    ) -> DiagnosticBootstrapResult:
        prior = await self._need_repo.latest(need_id=need_id, user_id=UUID(user.id))
        if prior is None:
            raise ValueError("DIAGNOSTIC_NEED_NOT_FOUND")
        existing = await self._need_repo.find_by_idempotency(f"response:{idempotency_key}")
        if existing is not None:
            return await self._existing_result(
                existing,
                plan_key=f"diagnostic-replan:{idempotency_key}",
            )
        if prior.version != expected_need_version:
            raise ValueError("DIAGNOSTIC_NEED_VERSION_CONFLICT")
        if prior.status != "active" or prior.assessment_item_ref is None:
            raise ValueError("DIAGNOSTIC_NEED_NOT_ACTIVE")
        await self._reload_need_inputs(user=user, need=prior)
        item = await self._items.get_exact(
            item_id=UUID(prior.assessment_item_ref.entity_id),
            version=str(prior.assessment_item_ref.version),
        )
        if item is None:
            return await self._stop_without_learner_evidence(
                prior=prior,
                user_id=UUID(user.id),
                reason="NO_VALID_ASSESSMENT_ITEM",
                reason_code="DIAGNOSTIC_ITEM_INVALID",
                idempotency_key=f"response:{idempotency_key}",
                correlation_id=correlation_id,
                created_at=submitted_at,
            )

        _before_state, before_estimates = await self._learner.current_state(
            user_id=UUID(user.id),
            knowledge_unit_ids=tuple(
                sorted(
                    set(prior.prerequisite_knowledge_unit_ids) | {prior.target_knowledge_unit_id},
                    key=str,
                )
            ),
            created_at=submitted_at,
        )
        try:
            scored = await self._assessment.score_submission_with_attempt(
                item=item,
                user_id=UUID(user.id),
                response=response,
                assistance=assistance,
                idempotency_key=idempotency_key,
                correlation_id=str(correlation_id),
            )
        except ScoringUnavailableError:
            return await self._stop_without_learner_evidence(
                prior=prior,
                user_id=UUID(user.id),
                reason="SYSTEM_BLOCKED",
                reason_code="ASSESSMENT_SYSTEM_FAILURE",
                idempotency_key=f"response:{idempotency_key}",
                correlation_id=correlation_id,
                created_at=submitted_at,
            )
        except ValueError:
            return await self._stop_without_learner_evidence(
                prior=prior,
                user_id=UUID(user.id),
                reason="NO_VALID_ASSESSMENT_ITEM",
                reason_code="DIAGNOSTIC_ITEM_INVALID",
                idempotency_key=f"response:{idempotency_key}",
                correlation_id=correlation_id,
                created_at=submitted_at,
            )

        result_event = await self._append_assessment_event(
            need=prior,
            result=scored.result,
            correlation_id=correlation_id,
            idempotency_key=f"diagnostic-assessment-result:{idempotency_key}",
            occurred_at=submitted_at,
        )
        knowledge_ids = tuple(
            sorted(
                set(prior.prerequisite_knowledge_unit_ids) | {prior.target_knowledge_unit_id},
                key=str,
            )
        )
        estimate, state, after_estimates = await self._learner.project_assessment(
            result=scored.result,
            attempt=scored.attempt,
            knowledge_unit_id=item.knowledge_unit_id,
            source_event_id=result_event.event_id,
            item_difficulty=item.difficulty,
            correlation_id=correlation_id,
            knowledge_unit_ids=knowledge_ids,
            created_at=submitted_at,
        )
        result_refs = (
            *prior.assessment_result_refs,
            VersionedRef(
                entity_type="AssessmentResult",
                entity_id=str(scored.result.result_id),
                version=scored.result.result_version,
            ),
        )
        next_version = await self._need_repo.next_version(prior.need_id)
        if estimate is None or scored.result.independence != "independent":
            next_need = prior.model_copy(
                update={
                    "version": next_version,
                    "attempts_used": prior.attempts_used + 1,
                    "assessment_result_refs": result_refs,
                    "status": "stopped",
                    "stop_reason": "LOW_CONFIDENCE_REQUIRES_REVIEW",
                    "reason_codes": (
                        *prior.reason_codes,
                        "DIAGNOSTIC_ASSISTANCE_NOT_INDEPENDENT",
                        "DIAGNOSTIC_UNKNOWN_PRESERVED",
                    ),
                    "created_from_learner_state_version": state.version,
                    "created_at": submitted_at,
                    "supersedes_version": prior.version,
                }
            )
        else:
            mapping, subgraph, goal, edges = await self._reload_need_inputs(user=user, need=prior)
            del mapping, goal
            mastery = {item.knowledge_unit_id: item for item in after_estimates}
            next_need = self._diagnostic_planner.build_need(
                user_id=UUID(user.id),
                goal_mapping_ref=prior.goal_mapping_ref,
                goal_subgraph_ref=prior.goal_subgraph_ref,
                target_knowledge_unit_id=prior.target_knowledge_unit_id,
                prerequisite_ids=subgraph.included_prerequisite_ids,
                edges=edges,
                mastery={item: mastery.get(item) for item in subgraph.included_prerequisite_ids},
                learner_state_version=state.version,
                knowledge_graph_versions=prior.knowledge_graph_versions,
                learning_planner_version=self._learning_planner.PLANNER_VERSION,
                max_attempts=prior.max_attempts,
                attempts_used=prior.attempts_used + 1,
                version=next_version,
                created_at=submitted_at,
                assessment_result_refs=result_refs,
                supersedes_version=prior.version,
            )
            next_need = await self._attach_item_or_stop(
                next_need,
                excluded_item_ids=(item.item_id,),
            )
        next_need = await self._need_repo.save(
            next_need, idempotency_key=f"response:{idempotency_key}"
        )

        before = {item.knowledge_unit_id: item.competence_probability for item in before_estimates}
        after = {item.knowledge_unit_id: item.competence_probability for item in after_estimates}
        plan: LearningPlan | None = None
        activities: tuple[LearningActivity, ...] = ()
        if self._learning_planner.is_material_change(prior_mastery=before, new_mastery=after):
            mapping, subgraph, goal, edges = await self._reload_need_inputs(
                user=user, need=next_need
            )
            mastery = {item.knowledge_unit_id: item for item in after_estimates}
            plan, activities = await self._generate_plan(
                goal=goal,
                mapping=mapping,
                edges=edges,
                mastery=mastery,
                learner_state_version=state.version,
                created_at=submitted_at,
                idempotency_key=f"diagnostic-replan:{idempotency_key}",
                reason_codes=["PLAN_REPLAN_DIAGNOSTIC_MATERIAL_STATE_CHANGE"],
            )
        await self._append_diagnostic_event(
            need=next_need,
            event_type=(
                "DiagnosticContinued" if next_need.status == "active" else "DiagnosticCompleted"
            ),
            correlation_id=correlation_id,
            idempotency_key=f"diagnostic-state:{idempotency_key}",
        )
        return DiagnosticBootstrapResult(
            need=next_need,
            learner_state=state,
            plan=plan,
            activities=activities,
            assessment_result=scored.result,
        )

    async def replay_need(self, *, user: User, need_id: UUID, version: int) -> DiagnosticNeedV1:
        """Load exact immutable diagnostic input/output; never invokes a model."""
        need = await self._need_repo.get(
            need_id=need_id,
            version=version,
            user_id=UUID(user.id),
        )
        if need is None:
            raise ValueError("DIAGNOSTIC_NEED_NOT_FOUND")
        state = await self._learner.get_state(
            user_id=UUID(user.id),
            version=need.created_from_learner_state_version,
        )
        if state is None:
            raise ValueError("LEARNER_STATE_STALE")
        return need

    async def generate_plan(
        self,
        *,
        user: User,
        need_id: UUID,
        idempotency_key: str,
        created_at: datetime,
    ) -> DiagnosticBootstrapResult:
        """Ask the existing SYS06 planner to materialize or replay the current plan."""
        need = await self._need_repo.latest(need_id=need_id, user_id=UUID(user.id))
        if need is None:
            raise ValueError("DIAGNOSTIC_NEED_NOT_FOUND")
        if need.status not in {"resolved", "stopped"} or need.stop_reason not in {
            "ALL_DECISION_RELEVANT_PREREQUISITES_RESOLVED",
            "TARGET_READY",
            "REMEDIATION_REQUIRED",
            "DIAGNOSTIC_BUDGET_EXHAUSTED",
        }:
            raise ValueError("DIAGNOSTIC_NEED_NOT_PLAN_ELIGIBLE")
        mapping, subgraph, goal, edges = await self._reload_need_inputs(user=user, need=need)
        knowledge_ids = self._knowledge_ids(subgraph)
        state, estimates = await self._learner.current_state(
            user_id=UUID(user.id),
            knowledge_unit_ids=knowledge_ids,
            created_at=created_at,
        )
        mastery = {item.knowledge_unit_id: item for item in estimates}
        active_plans = [
            item
            for item in await self._plan_repo.list_versions(goal.goal_id)
            if item.status == "active"
        ]
        current = active_plans[-1] if active_plans else None
        expected_graph_version = ",".join(mapping.knowledge_graph_versions)
        if (
            current is not None
            and current.created_from_learner_state_version == state.version
            and current.knowledge_graph_version == expected_graph_version
        ):
            activities = tuple(
                await self._plan_repo.activities(
                    plan_id=current.plan_id, plan_version=current.version
                )
            )
            return DiagnosticBootstrapResult(
                need=need,
                learner_state=state,
                plan=current,
                activities=activities,
            )
        plan, activities = await self._generate_plan(
            goal=goal,
            mapping=mapping,
            edges=edges,
            mastery=mastery,
            learner_state_version=state.version,
            created_at=created_at,
            idempotency_key=idempotency_key,
            reason_codes=["PLAN_GENERATED_FROM_TERMINAL_DIAGNOSTIC_STATE"],
        )
        return DiagnosticBootstrapResult(
            need=need,
            learner_state=state,
            plan=plan,
            activities=activities,
        )

    async def _load_inputs(
        self,
        *,
        user: User,
        mapping_id: UUID,
        mapping_version: int,
        subgraph_id: UUID,
        subgraph_version: int,
        target_knowledge_unit_id: UUID,
    ) -> tuple[
        LearningGoalV1,
        GoalKnowledgeMappingV1,
        GoalSpecificKnowledgeSubgraphV1,
        PublishedGoalKnowledgeScope,
        tuple[DiagnosticPrerequisiteEdgeV1, ...],
    ]:
        mapping = await self._goal_repo.get_mapping_version(
            mapping_id=mapping_id, version=mapping_version
        )
        if mapping is None or mapping.status != "confirmed":
            raise ValueError("GOAL_MAPPING_NOT_CONFIRMED")
        goal = await self._goal_repo.get_goal_version(
            goal_id=mapping.goal_id,
            version=mapping.goal_version,
            user_id=UUID(user.id),
        )
        if goal is None:
            raise ValueError("LEARNING_GOAL_NOT_FOUND")
        subgraph = await self._goal_repo.get_subgraph(
            subgraph_id=subgraph_id, version=subgraph_version
        )
        if (
            subgraph is None
            or subgraph.goal_mapping_ref.entity_id != str(mapping.mapping_id)
            or str(subgraph.goal_mapping_ref.version) != str(mapping.mapping_version)
        ):
            raise ValueError("PREREQUISITE_GRAPH_STALE")
        if target_knowledge_unit_id not in subgraph.target_knowledge_unit_ids:
            raise ValueError("DIAGNOSTIC_TARGET_OUTSIDE_GOAL_MAPPING")
        scope = await self._knowledge.load_scope(
            user=user, source_document_ids=goal.source_document_ids
        )
        if scope.missing_document_ids:
            raise ValueError("DIAGNOSTIC_SOURCE_SCOPE_UNAVAILABLE")
        edges = self._exact_edges(subgraph=subgraph, scope=scope)
        return goal, mapping, subgraph, scope, edges

    async def _reload_need_inputs(
        self, *, user: User, need: DiagnosticNeedV1
    ) -> tuple[
        GoalKnowledgeMappingV1,
        GoalSpecificKnowledgeSubgraphV1,
        LearningGoalV1,
        tuple[DiagnosticPrerequisiteEdgeV1, ...],
    ]:
        mapping = await self._goal_repo.get_mapping_version(
            mapping_id=UUID(need.goal_mapping_ref.entity_id),
            version=int(need.goal_mapping_ref.version),
        )
        subgraph = await self._goal_repo.get_subgraph(
            subgraph_id=UUID(need.goal_subgraph_ref.entity_id),
            version=int(need.goal_subgraph_ref.version),
        )
        if mapping is None or subgraph is None:
            raise ValueError("PREREQUISITE_GRAPH_STALE")
        goal = await self._goal_repo.get_goal_version(
            goal_id=mapping.goal_id,
            version=mapping.goal_version,
            user_id=UUID(user.id),
        )
        if goal is None:
            raise ValueError("LEARNING_GOAL_NOT_FOUND")
        scope = await self._knowledge.load_scope(
            user=user, source_document_ids=goal.source_document_ids
        )
        exact_edges = self._exact_edges(subgraph=subgraph, scope=scope)
        if exact_edges != need.prerequisite_edges:
            raise ValueError("PREREQUISITE_GRAPH_STALE")
        return mapping, subgraph, goal, exact_edges

    @staticmethod
    def _exact_edges(
        *,
        subgraph: GoalSpecificKnowledgeSubgraphV1,
        scope: PublishedGoalKnowledgeScope,
    ) -> tuple[DiagnosticPrerequisiteEdgeV1, ...]:
        views = {str(item.relation_id): item for item in scope.relations if item.strength == "hard"}
        edges: list[DiagnosticPrerequisiteEdgeV1] = []
        for relation_ref in subgraph.relation_refs:
            relation = views.get(relation_ref.entity_id)
            if relation is None:
                raise ValueError("PREREQUISITE_GRAPH_STALE")
            parts = relation.relation_ref.split(":")
            if len(parts) != 3 or parts[2].removeprefix("v") != str(relation_ref.version):
                raise ValueError("PREREQUISITE_GRAPH_STALE")
            edges.append(
                DiagnosticPrerequisiteEdgeV1(
                    prerequisite_id=relation.prerequisite_id,
                    target_knowledge_unit_id=relation.target_knowledge_unit_id,
                    relation_ref=relation_ref,
                )
            )
        return tuple(sorted(edges, key=lambda item: item.relation_ref.entity_id))

    async def _attach_item_or_stop(
        self,
        need: DiagnosticNeedV1,
        *,
        excluded_item_ids: tuple[UUID, ...] = (),
    ) -> DiagnosticNeedV1:
        if need.status != "active" or need.current_knowledge_unit_id is None:
            return need
        item = await self._items.select_active(
            knowledge_unit_id=need.current_knowledge_unit_id,
            excluded_item_ids=excluded_item_ids,
        )
        if item is None:
            return need.model_copy(
                update={
                    "status": "blocked",
                    "stop_reason": "NO_VALID_ASSESSMENT_ITEM",
                    "reason_codes": (*need.reason_codes, "DIAGNOSTIC_ITEM_UNAVAILABLE"),
                }
            )
        return need.model_copy(
            update={
                "assessment_item_ref": VersionedRef(
                    entity_type="AssessmentItem",
                    entity_id=str(item.item_id),
                    version=item.version,
                ),
                "reason_codes": (*need.reason_codes, "DIAGNOSTIC_ACTIVE_ITEM_EXACT_VERSION"),
            }
        )

    async def _generate_plan(
        self,
        *,
        goal: LearningGoalV1,
        mapping: GoalKnowledgeMappingV1,
        edges: tuple[DiagnosticPrerequisiteEdgeV1, ...],
        mastery: dict,
        learner_state_version: int,
        created_at: datetime,
        idempotency_key: str,
        reason_codes: list[str],
    ) -> tuple[LearningPlan, tuple[LearningActivity, ...]]:
        existing = await self._plan_repo.find_by_idempotency(idempotency_key)
        if existing is not None:
            return existing, tuple(
                await self._plan_repo.activities(
                    plan_id=existing.plan_id, plan_version=existing.version
                )
            )
        prerequisites: dict[UUID, list[UUID]] = {}
        for edge in edges:
            prerequisites.setdefault(edge.target_knowledge_unit_id, []).append(edge.prerequisite_id)
        planner_goal = ConfirmedLearningGoal(
            goal_id=goal.goal_id,
            objective_id=uuid5(
                NAMESPACE_URL,
                f"askora:objective:{goal.goal_id}:v{goal.version}:mapping:{mapping.mapping_version}",
            ),
            target_knowledge_unit_ids=list(mapping.selected_target_ids),
            confirmed_at=goal.confirmed_at or goal.created_at,
        )
        version = await self._plan_repo.next_version(goal.goal_id)
        decision = self._learning_planner.generate(
            goal=planner_goal,
            prerequisites=prerequisites,
            mastery={item: value.competence_probability for item, value in mastery.items()},
            due_candidates=[],
            time_budget_minutes=max(5, min(60, goal.weekly_time_budget_minutes or 30)),
            learner_state_version=learner_state_version,
            knowledge_graph_version=",".join(mapping.knowledge_graph_versions),
            version=version,
            created_at=created_at,
            reason_codes=reason_codes,
        )
        plan = await self._plan_repo.save(decision, idempotency_key=idempotency_key)
        return plan, decision.activities

    async def _existing_result(
        self, need: DiagnosticNeedV1, *, plan_key: str
    ) -> DiagnosticBootstrapResult:
        state = await self._learner.get_state(
            user_id=need.user_id,
            version=need.created_from_learner_state_version,
        )
        if state is None:
            raise ValueError("LEARNER_STATE_STALE")
        plan = await self._plan_repo.find_by_idempotency(plan_key)
        activities = (
            tuple(await self._plan_repo.activities(plan_id=plan.plan_id, plan_version=plan.version))
            if plan is not None
            else ()
        )
        return DiagnosticBootstrapResult(
            need=need,
            learner_state=state,
            plan=plan,
            activities=activities,
        )

    async def _stop_without_learner_evidence(
        self,
        *,
        prior: DiagnosticNeedV1,
        user_id: UUID,
        reason: str,
        reason_code: str,
        idempotency_key: str,
        correlation_id: UUID,
        created_at: datetime,
    ) -> DiagnosticBootstrapResult:
        state = await self._learner.get_state(
            user_id=user_id,
            version=prior.created_from_learner_state_version,
        )
        if state is None:
            raise ValueError("LEARNER_STATE_STALE")
        need = prior.model_copy(
            update={
                "version": await self._need_repo.next_version(prior.need_id),
                "status": "blocked",
                "stop_reason": reason,
                "reason_codes": (*prior.reason_codes, reason_code, "DIAGNOSTIC_UNKNOWN_PRESERVED"),
                "created_at": created_at,
                "supersedes_version": prior.version,
            }
        )
        need = await self._need_repo.save(need, idempotency_key=idempotency_key)
        await self._append_diagnostic_event(
            need=need,
            event_type="DiagnosticBlocked",
            correlation_id=correlation_id,
            idempotency_key=f"diagnostic-blocked:{idempotency_key}",
        )
        return DiagnosticBootstrapResult(
            need=need,
            learner_state=state,
            plan=None,
            activities=(),
        )

    async def _append_assessment_event(
        self,
        *,
        need: DiagnosticNeedV1,
        result: AssessmentResult,
        correlation_id: UUID,
        idempotency_key: str,
        occurred_at: datetime,
    ) -> LearningEventEnvelope:
        event = LearningEventEnvelope(
            event_id=uuid5(result.result_id, "AssessmentResultRecorded"),
            event_type="AssessmentResultRecorded",
            aggregate_type="AssessmentAttempt",
            aggregate_id=result.attempt_id,
            aggregate_version=result.result_version,
            sequence=result.result_version,
            occurred_at=occurred_at,
            recorded_at=occurred_at,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
            actor=EventActor(actor_type="learner", actor_id=str(need.user_id)),
            context=EventContext(
                user_id=need.user_id,
                goal_id=None,
                knowledge_unit_ids=[need.current_knowledge_unit_id]
                if need.current_knowledge_unit_id
                else [],
                assessment_attempt_id=result.attempt_id,
                content_revision_ids=[],
            ),
            payload={
                "result_ref": f"assessment_result:{result.result_id}:v{result.result_version}",
                "diagnostic_need_ref": f"diagnostic_need:{need.need_id}:v{need.version}",
                "correctness": result.correctness,
                "independence": result.independence,
                "assessment_confidence": result.assessment_confidence,
                "reason_codes": result.reason_codes,
            },
            provenance=EventProvenance(
                source="domain",
                algorithm_version=",".join(result.evaluator_versions),
            ),
            trace=EventTrace(trace_id=f"diagnostic-assessment:{result.result_id}"),
            privacy=EventPrivacy(
                classification="personal",
                external_processing=False,
                retention_class="diagnostic",
            ),
        )
        return await LearningEventRepository(self._session).append(event)

    async def _append_diagnostic_event(
        self,
        *,
        need: DiagnosticNeedV1,
        event_type: str,
        correlation_id: UUID,
        idempotency_key: str,
    ) -> None:
        event = LearningEventEnvelope(
            event_id=uuid5(need.need_id, f"{event_type}:v{need.version}"),
            event_type=event_type,
            aggregate_type="DiagnosticNeed",
            aggregate_id=need.need_id,
            aggregate_version=need.version,
            sequence=need.version,
            occurred_at=need.created_at,
            recorded_at=need.created_at,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
            actor=EventActor(actor_type="system", actor_id="SYS06"),
            context=EventContext(
                user_id=need.user_id,
                knowledge_unit_ids=[need.target_knowledge_unit_id],
                content_revision_ids=[],
            ),
            payload={
                "diagnostic_need_ref": f"diagnostic_need:{need.need_id}:v{need.version}",
                "learner_state_version": need.created_from_learner_state_version,
                "attempts_used": need.attempts_used,
                "max_attempts": need.max_attempts,
                "status": need.status,
                "stop_reason": need.stop_reason,
                "reason_codes": list(need.reason_codes),
            },
            provenance=EventProvenance(
                source="domain",
                algorithm_version=need.diagnostic_planner_version,
            ),
            trace=EventTrace(trace_id=f"diagnostic:{need.need_id}:v{need.version}"),
            privacy=EventPrivacy(
                classification="personal",
                external_processing=False,
                retention_class="diagnostic",
            ),
        )
        await LearningEventRepository(self._session).append(event)

    @staticmethod
    def _knowledge_ids(subgraph: GoalSpecificKnowledgeSubgraphV1) -> tuple[UUID, ...]:
        return tuple(
            sorted(
                set(subgraph.target_knowledge_unit_ids) | set(subgraph.included_prerequisite_ids),
                key=str,
            )
        )

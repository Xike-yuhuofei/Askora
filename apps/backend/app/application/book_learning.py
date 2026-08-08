"""SPEC-D06 Book-to-Learning application composition over canonical owners."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Literal, Protocol
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.adaptive import (
    AvailabilityStatus,
    TeachingActionV03,
    TeachingContextV03,
    ValueWithAvailability,
    VersionedRef,
)
from app.contracts.assessment import AssistanceSnapshot
from app.contracts.book_learning import (
    BookLearningOperationResponseV1,
    BookLearningOwnerRefV1,
    BookLearningReadinessV1,
    BookLearningTeachingResponseV1,
    LearnerVisibleDiagnosticItemV1,
)
from app.contracts.events import (
    ActualAssistanceRecordedPayloadV03,
    EventActor,
    EventContext,
    EventPrivacy,
    EventProvenance,
    EventProvenanceV03,
    EventTrace,
    LearningEventEnvelope,
    LearningEventEnvelopeV03,
)
from app.contracts.learning import LearningActivity, LearningPlan, MasteryEstimate
from app.contracts.planning import LearningGoalV1
from app.infrastructure.adaptive_records import (
    AdaptiveContractRepository,
    DecisionTraceV03Repository,
    LearningEventV03Repository,
)
from app.infrastructure.learning_records import LearnerModelRepository
from app.infrastructure.ledger import LearningEventRepository
from app.infrastructure.planning_records import (
    DiagnosticNeedRepository,
    GoalPlanningRepository,
    LearningPlanRepository,
)
from app.models.adaptive import TeachingContextRecord
from app.models.ledger import LearningEventRecord
from app.models.user import User
from app.orchestration.learning_facade import CanonicalTurnRequest, LearningOrchestrationFacade
from app.queries.book_learning import BookLearningReadinessQuery
from app.queries.diagnostic_assessment import DiagnosticAssessmentItemQuery
from app.services.assessment.diagnostic_bootstrap import (
    DiagnosticBootstrapResult,
    PrerequisiteDiagnosticService,
)
from app.services.auth.canonical_identity import canonical_user_id
from app.services.kt.canonical_projector import CanonicalLearnerProjectorService
from app.services.learning_goals import LearningGoalService
from app.services.policy_runtime import (
    ActivePolicyRuntimeResolver,
    PolicyRuntimeResolutionError,
    PolicyRuntimeSelection,
)
from app.services.rag_service import PublishedKnowledgeRAGService


class BookLearningApplicationError(ValueError):
    """Fail-closed application error mapped by the transport layer."""


BookLearningPolicyRuntime = PolicyRuntimeSelection


class BookLearningPolicyRuntimeResolver(Protocol):
    async def resolve(self) -> BookLearningPolicyRuntime: ...


class BookLearningApplication:
    """Coordinates owner commands; it owns no domain algorithm or second truth."""

    def __init__(
        self,
        db: AsyncSession,
        *,
        teaching_facade: LearningOrchestrationFacade | None = None,
        policy_runtime_resolver: BookLearningPolicyRuntimeResolver | None = None,
    ) -> None:
        self._db = db
        self._goals = LearningGoalService(db)
        self._diagnostics = PrerequisiteDiagnosticService(
            db,
            learner_projector=CanonicalLearnerProjectorService(db),
        )
        self._goal_repo = GoalPlanningRepository(db)
        self._need_repo = DiagnosticNeedRepository(db)
        self._plan_repo = LearningPlanRepository(db)
        self._learner_repo = LearnerModelRepository(db)
        self._readiness = BookLearningReadinessQuery(db)
        self._diagnostic_items = DiagnosticAssessmentItemQuery(db)
        self._retrieval = PublishedKnowledgeRAGService(db)
        self._teaching = teaching_facade or LearningOrchestrationFacade()
        self._policy_runtime = policy_runtime_resolver or ActivePolicyRuntimeResolver(db)

    async def readiness(
        self, *, user: User, document_id: UUID, correlation_id: str
    ) -> BookLearningReadinessV1:
        return await self._readiness.get(
            user=user,
            document_id=document_id,
            correlation_id=correlation_id,
        )

    async def get_goal(
        self, *, user: User, goal_id: UUID, correlation_id: UUID
    ) -> BookLearningOperationResponseV1:
        goal = await self._require_goal(user, goal_id)
        return self._operation("GetLearningGoal", correlation_id, goal=goal)

    async def get_mapping(
        self, *, user: User, goal_id: UUID, correlation_id: UUID
    ) -> BookLearningOperationResponseV1:
        goal = await self._require_goal(user, goal_id)
        mapping = await self._goal_repo.latest_mapping(goal.goal_id)
        if mapping is None:
            raise BookLearningApplicationError("GOAL_KNOWLEDGE_MAPPING_NOT_FOUND")
        subgraph = await self._goal_repo.latest_subgraph_for_mapping(mapping.mapping_id)
        values: dict[str, Any] = {"mapping": mapping}
        if subgraph is not None:
            values["subgraph"] = subgraph
        return self._operation("GetGoalKnowledgeMapping", correlation_id, **values)

    async def get_diagnostic(
        self, *, user: User, goal_id: UUID, correlation_id: UUID
    ) -> BookLearningOperationResponseV1:
        goal = await self._require_goal(user, goal_id)
        mapping = await self._goal_repo.latest_mapping(goal.goal_id)
        if mapping is None:
            raise BookLearningApplicationError("GOAL_KNOWLEDGE_MAPPING_NOT_FOUND")
        need = await self._need_repo.latest_for_mapping(
            mapping_id=mapping.mapping_id, user_id=canonical_user_id(user.id)
        )
        if need is None:
            raise BookLearningApplicationError("DIAGNOSTIC_NEED_NOT_FOUND")
        values: dict[str, Any] = {"need": need}
        if need.status == "active":
            if need.assessment_item_ref is None:
                raise BookLearningApplicationError("DIAGNOSTIC_ITEM_UNAVAILABLE")
            learner_item = await self._diagnostic_items.get_learner_visible(
                item_id=UUID(need.assessment_item_ref.entity_id),
                version=str(need.assessment_item_ref.version),
                need_id=need.need_id,
                need_version=need.version,
            )
            if learner_item is None:
                raise BookLearningApplicationError("DIAGNOSTIC_ITEM_UNAVAILABLE")
            values["learner_item"] = learner_item
        return self._operation("GetCurrentDiagnosticState", correlation_id, **values)

    async def get_plan(
        self, *, user: User, goal_id: UUID, correlation_id: UUID
    ) -> BookLearningOperationResponseV1:
        goal = await self._require_goal(user, goal_id)
        plans = await self._plan_repo.list_versions(goal.goal_id)
        plan = next((item for item in reversed(plans) if item.status == "active"), None)
        if plan is None:
            raise BookLearningApplicationError("LEARNING_PLAN_NOT_FOUND")
        activities = tuple(
            await self._plan_repo.activities(plan_id=plan.plan_id, plan_version=plan.version)
        )
        return self._operation(
            "GetCurrentLearningPlan", correlation_id, plan=plan, activities=activities
        )

    async def create_goal_candidate(
        self,
        *,
        user: User,
        document_id: UUID,
        intent: str,
        idempotency_key: str,
        correlation_id: UUID,
        application_context: str | None = None,
        deadline_at: datetime | None = None,
        weekly_time_budget_minutes: int | None = None,
        now: datetime | None = None,
    ) -> BookLearningOperationResponseV1:
        existing = await self._goal_repo.find_goal_by_idempotency(idempotency_key)
        if existing is not None:
            if existing.user_id != canonical_user_id(user.id) or existing.source_document_ids != (
                document_id,
            ):
                raise BookLearningApplicationError("GOAL_IDEMPOTENCY_SCOPE_CONFLICT")
            return self._operation("CreateGoalCandidate", correlation_id, goal=existing)
        readiness = await self.readiness(
            user=user, document_id=document_id, correlation_id=str(correlation_id)
        )
        if readiness.state != "READY_FOR_GOAL":
            raise BookLearningApplicationError(f"BOOK_NOT_READY_FOR_GOAL:{readiness.state}")
        goal = await self._goals.create_candidate(
            user=user,
            intent=intent,
            source_document_ids=(document_id,),
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
            created_at=now or datetime.now(timezone.utc),
            application_context=application_context,
            deadline_at=deadline_at,
            weekly_time_budget_minutes=weekly_time_budget_minutes,
        )
        return self._operation("CreateGoalCandidate", correlation_id, goal=goal)

    async def confirm_goal(
        self,
        *,
        user: User,
        goal_id: UUID,
        confirmed_by_user: bool,
        idempotency_key: str,
        correlation_id: UUID,
        now: datetime | None = None,
    ) -> BookLearningOperationResponseV1:
        goal = await self._goals.confirm_goal(
            user=user,
            goal_id=goal_id,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
            confirmed_at=now or datetime.now(timezone.utc),
            confirmed_by_user=confirmed_by_user,
        )
        return self._operation("ConfirmGoal", correlation_id, goal=goal)

    async def map_goal(
        self,
        *,
        user: User,
        goal_id: UUID,
        idempotency_key: str,
        correlation_id: UUID,
        now: datetime | None = None,
    ) -> BookLearningOperationResponseV1:
        decision = await self._goals.map_goal(
            user=user,
            goal_id=goal_id,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
            created_at=now or datetime.now(timezone.utc),
        )
        values: dict[str, Any] = {"mapping": decision.mapping}
        if decision.subgraph is not None:
            values["subgraph"] = decision.subgraph
        return self._operation("MapGoalAndBuildSubgraph", correlation_id, **values)

    async def start_diagnostic(
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
        now: datetime | None = None,
    ) -> BookLearningOperationResponseV1:
        result = await self._diagnostics.create_need(
            user=user,
            mapping_id=mapping_id,
            mapping_version=mapping_version,
            subgraph_id=subgraph_id,
            subgraph_version=subgraph_version,
            target_knowledge_unit_id=target_knowledge_unit_id,
            max_attempts=max_attempts,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
            created_at=now or datetime.now(timezone.utc),
        )
        return self._diagnostic_operation("GenerateDiagnosisAndPlan", correlation_id, result)

    async def submit_diagnostic_response(
        self,
        *,
        user: User,
        need_id: UUID,
        expected_need_version: int,
        response: Any,
        assistance: AssistanceSnapshot,
        idempotency_key: str,
        correlation_id: UUID,
        now: datetime | None = None,
    ) -> BookLearningOperationResponseV1:
        result = await self._diagnostics.submit_response(
            user=user,
            need_id=need_id,
            expected_need_version=expected_need_version,
            response=response,
            assistance=assistance,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
            submitted_at=now or datetime.now(timezone.utc),
        )
        return self._diagnostic_operation("ContinueDiagnosisAndReplan", correlation_id, result)

    async def generate_plan(
        self,
        *,
        user: User,
        need_id: UUID,
        idempotency_key: str,
        correlation_id: UUID,
        now: datetime | None = None,
    ) -> BookLearningOperationResponseV1:
        result = await self._diagnostics.generate_plan(
            user=user,
            need_id=need_id,
            idempotency_key=idempotency_key,
            created_at=now or datetime.now(timezone.utc),
        )
        return self._diagnostic_operation("GenerateLearningPlan", correlation_id, result)

    async def select_next_activity(
        self,
        *,
        user: User,
        goal_id: UUID,
        idempotency_key: str,
        correlation_id: UUID,
        now: datetime | None = None,
    ) -> BookLearningOperationResponseV1:
        goal = await self._require_goal(user, goal_id)
        plans = await self._plan_repo.list_versions(goal.goal_id)
        plan = next((item for item in reversed(plans) if item.status == "active"), None)
        if plan is None:
            raise BookLearningApplicationError("LEARNING_PLAN_NOT_READY")
        activities = await self._plan_repo.activities(
            plan_id=plan.plan_id, plan_version=plan.version
        )
        activity = next(
            (item for item in activities if item.status in {"available", "planned", "active"}),
            None,
        )
        if activity is None:
            raise BookLearningApplicationError("LEARNING_ACTIVITY_NOT_AVAILABLE")
        event_repo = LearningEventRepository(self._db)
        existing = await event_repo.get_by_idempotency_key(
            f"book-activity-selected:{idempotency_key}"
        )
        if existing is not None:
            expected_plan_ref = f"learning_plan:{plan.plan_id}:v{plan.version}"
            if (
                existing.context.user_id != canonical_user_id(user.id)
                or existing.context.goal_id != goal.goal_id
                or existing.aggregate_id != str(activity.activity_id)
                or existing.payload.get("plan_ref") != expected_plan_ref
            ):
                raise BookLearningApplicationError("ACTIVITY_SELECTION_IDEMPOTENCY_CONFLICT")
            return self._operation(
                "SelectNextActivity", correlation_id, goal=goal, plan=plan, activity=activity
            )
        await self._require_book_state(user=user, goal=goal, expected="PLAN_READY")
        selected_at = now or datetime.now(timezone.utc)
        event = self._activity_selected_event(
            user=user,
            goal=goal,
            plan=plan,
            activity=activity,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
            selected_at=selected_at,
        )
        await event_repo.append(event)
        return self._operation(
            "SelectNextActivity", correlation_id, goal=goal, plan=plan, activity=activity
        )

    async def start_teaching_round(
        self,
        *,
        user: User,
        goal_id: UUID,
        plan_id: UUID,
        plan_version: int,
        activity_id: UUID,
        session_id: UUID,
        turn_id: str,
        learner_text: str,
        idempotency_key: str,
        correlation_id: UUID,
        now: datetime | None = None,
    ) -> BookLearningTeachingResponseV1:
        goal, plan, activity = await self._require_selected_activity(
            user=user,
            goal_id=goal_id,
            plan_id=plan_id,
            plan_version=plan_version,
            activity_id=activity_id,
        )
        await self._require_book_state(user=user, goal=goal, expected="READY_TO_LEARN")
        try:
            runtime = await self._policy_runtime.resolve()
        except PolicyRuntimeResolutionError as exc:
            raise BookLearningApplicationError(str(exc)) from exc
        runtime.profile.assert_matches(runtime.bundle)
        context = await self._teaching_context(
            user=user,
            goal=goal,
            plan=plan,
            activity=activity,
            idempotency_key=idempotency_key,
            decision_time=now or datetime.now(timezone.utc),
        )
        inputs = await self._retrieval.load_adaptive_input(
            pseudonym_id=user.pseudonym_id,
            source_scope={"document_ids": [str(item) for item in goal.source_document_ids]},
        )
        records = AdaptiveContractRepository(self._db)
        await records.publish_policy_bundle(runtime.bundle)
        await records.save_context(context)
        result = await self._teaching.run_turn(
            CanonicalTurnRequest(
                session_id=str(session_id),
                user_id=user.id,
                text=learner_text,
                turn_id=turn_id,
                subject=goal.topic,
                knowledge_point_id=(
                    str(activity.knowledge_unit_ids[0]) if activity.knowledge_unit_ids else None
                ),
                correlation_id=str(correlation_id),
                teaching_context_v03=context,
                policy_bundle_v03=runtime.bundle,
                policy_profile_v03=runtime.profile,
                adaptive_retrieval_candidates=inputs.candidates,
                adaptive_source_scope=inputs.source_scope,
                adaptive_index_versions=inputs.index_versions,
            )
        )
        if (
            result.teaching_action_v03 is None
            or result.decision_trace_v03 is None
            or result.evidence_bundle_v03 is None
            or result.actual_assistance_event_v03 is None
            or result.adaptive_execution_v03 is None
        ):
            raise BookLearningApplicationError("CANONICAL_TEACHING_HANDOFF_INCOMPLETE")
        await records.save_action(result.teaching_action_v03)
        await DecisionTraceV03Repository(self._db).append(result.decision_trace_v03)
        assistance_event = self._actual_assistance_event(
            user=user,
            goal=goal,
            activity=activity,
            teaching_action=result.teaching_action_v03,
            event_payload=result.actual_assistance_event_v03,
            response_id=result.adaptive_execution_v03.response_id,
            policy_version=runtime.bundle.policy_version,
            session_id=session_id,
            correlation_id=correlation_id,
            occurred_at=context.decision_time,
        )
        event_records = LearningEventV03Repository(self._db)
        existing_assistance_event = await event_records.get(assistance_event.event_id)
        if existing_assistance_event is not None:
            if (
                existing_assistance_event.aggregate_id != assistance_event.aggregate_id
                or existing_assistance_event.payload != assistance_event.payload
                or existing_assistance_event.context.user_id != assistance_event.context.user_id
            ):
                raise BookLearningApplicationError("ACTUAL_ASSISTANCE_IDEMPOTENCY_CONFLICT")
            assistance_event = existing_assistance_event
        else:
            await event_records.append(assistance_event)
        refs = (
            self._owner_ref("SYS06", "LearningGoal", goal.goal_id, goal.version, goal.status),
            self._owner_ref("SYS06", "LearningPlan", plan.plan_id, plan.version, plan.status),
            self._owner_ref(
                "SYS06",
                "LearningActivity",
                activity.activity_id,
                activity.plan_version,
                activity.status,
            ),
            self._owner_ref(
                "SYS05",
                "TeachingAction",
                result.teaching_action_v03.action_id,
                result.teaching_action_v03.action_schema_version,
                "decided",
            ),
            self._owner_ref(
                "SYS02",
                "EvidenceBundle",
                result.evidence_bundle_v03.bundle_id,
                result.evidence_bundle_v03.bundle_schema_version,
                "selected",
            ),
            self._owner_ref(
                "SYS08",
                "ActualAssistanceRecorded",
                assistance_event.event_id,
                assistance_event.schema_version,
                "recorded",
            ),
        )
        return BookLearningTeachingResponseV1(
            reply_text=result.reply_text,
            teaching_action=result.teaching_action_v03,
            evidence_bundle=result.evidence_bundle_v03,
            owner_refs=refs,
            correlation_id=str(correlation_id),
        )

    @staticmethod
    def _actual_assistance_event(
        *,
        user: User,
        goal: LearningGoalV1,
        activity: LearningActivity,
        teaching_action: TeachingActionV03,
        event_payload: ActualAssistanceRecordedPayloadV03,
        response_id: UUID,
        policy_version: str,
        session_id: UUID,
        correlation_id: UUID,
        occurred_at: datetime,
    ) -> LearningEventEnvelopeV03:
        event_id = uuid5(
            NAMESPACE_URL,
            f"askora:actual-assistance:{teaching_action.action_id}:{response_id}",
        )
        return LearningEventEnvelopeV03(
            event_id=event_id,
            event_type="ActualAssistanceRecorded",
            aggregate_type="TeachingAction",
            aggregate_id=teaching_action.action_id,
            aggregate_version=1,
            sequence=1,
            occurred_at=occurred_at,
            recorded_at=occurred_at,
            idempotency_key=f"book-actual-assistance:{teaching_action.action_id}:{response_id}",
            correlation_id=correlation_id,
            causation_id=teaching_action.decision_id,
            actor=EventActor(actor_type="system", actor_id="SYS08"),
            context=EventContext(
                user_id=canonical_user_id(user.id),
                session_id=session_id,
                goal_id=goal.goal_id,
                knowledge_unit_ids=list(activity.knowledge_unit_ids),
                content_revision_ids=[],
            ),
            producer_system="SYS08",
            payload=event_payload.model_dump(mode="json"),
            provenance=EventProvenanceV03(
                source="orchestrator",
                policy_version=policy_version,
                policy_bundle_ref=teaching_action.policy_bundle_ref,
            ),
            trace=EventTrace(trace_id=f"book-assistance:{event_id}"),
            privacy=EventPrivacy(
                classification="personal",
                external_processing=False,
                retention_class="core_learning",
            ),
        )

    async def _require_goal(self, user: User, goal_id: UUID) -> LearningGoalV1:
        goal = await self._goal_repo.latest_goal(
            goal_id=goal_id, user_id=canonical_user_id(user.id)
        )
        if goal is None:
            raise BookLearningApplicationError("LEARNING_GOAL_NOT_FOUND")
        return goal

    async def _require_book_state(self, *, user: User, goal: LearningGoalV1, expected: str) -> None:
        if not goal.source_document_ids:
            raise BookLearningApplicationError("LEARNING_GOAL_SOURCE_SCOPE_EMPTY")
        state = await self.readiness(
            user=user,
            document_id=goal.source_document_ids[0],
            correlation_id="book-learning-owner-command",
        )
        if state.state != expected:
            raise BookLearningApplicationError(
                f"BOOK_LEARNING_STATE_CONFLICT:{state.state}:EXPECTED_{expected}"
            )

    async def _require_selected_activity(
        self,
        *,
        user: User,
        goal_id: UUID,
        plan_id: UUID,
        plan_version: int,
        activity_id: UUID,
    ) -> tuple[LearningGoalV1, LearningPlan, LearningActivity]:
        goal = await self._require_goal(user, goal_id)
        plans = await self._plan_repo.list_versions(goal_id)
        plan = next(
            (
                item
                for item in plans
                if item.plan_id == plan_id
                and item.version == plan_version
                and item.status == "active"
            ),
            None,
        )
        if plan is None:
            raise BookLearningApplicationError("LEARNING_PLAN_STALE_OR_UNAUTHORIZED")
        activities = await self._plan_repo.activities(plan_id=plan_id, plan_version=plan_version)
        activity = next((item for item in activities if item.activity_id == activity_id), None)
        if activity is None:
            raise BookLearningApplicationError("LEARNING_ACTIVITY_STALE_OR_UNAUTHORIZED")
        selected = await self._db.scalar(
            select(LearningEventRecord.event_id).where(
                LearningEventRecord.event_type == "ActivitySelected",
                LearningEventRecord.aggregate_id == str(activity_id),
            )
        )
        if selected is None:
            raise BookLearningApplicationError("LEARNING_ACTIVITY_NOT_SELECTED")
        return goal, plan, activity

    async def _teaching_context(
        self,
        *,
        user: User,
        goal: LearningGoalV1,
        plan: LearningPlan,
        activity: LearningActivity,
        idempotency_key: str,
        decision_time: datetime,
    ) -> TeachingContextV03:
        context_id = uuid5(
            NAMESPACE_URL, f"askora:book-teaching-context:{user.id}:{idempotency_key}"
        )
        existing = await self._db.get(TeachingContextRecord, str(context_id))
        if existing is not None:
            return TeachingContextV03.model_validate(existing.payload)
        estimates = await self._learner_repo.list_latest_mastery(
            user_id=canonical_user_id(user.id),
            knowledge_unit_ids=tuple(activity.knowledge_unit_ids),
        )
        state = await self._learner_repo.latest_learner_state(canonical_user_id(user.id))
        refs = [
            VersionedRef(
                entity_type="LearningGoal", entity_id=str(goal.goal_id), version=goal.version
            ),
            VersionedRef(
                entity_type="LearningPlan", entity_id=str(plan.plan_id), version=plan.version
            ),
            VersionedRef(
                entity_type="LearningActivity",
                entity_id=str(activity.activity_id),
                version=activity.plan_version,
            ),
            VersionedRef(
                entity_type="LearningObjective",
                entity_id=str(activity.objective_id),
                version=plan.version,
            ),
        ]
        if state is not None:
            refs.append(
                VersionedRef(
                    entity_type="LearnerState",
                    entity_id=str(state.learner_state_id),
                    version=state.version,
                )
            )
        mastery_refs = tuple(self._mastery_ref(item) for item in estimates)
        refs.extend(mastery_refs)
        source_refs = tuple(refs)
        missing = ValueWithAvailability(availability=AvailabilityStatus.MISSING)
        activity_value = ValueWithAvailability(
            value=activity.type,
            availability=AvailabilityStatus.AVAILABLE,
            confidence=1.0,
            source_refs=(source_refs[2],),
        )
        target_value = ValueWithAvailability(
            value=goal.target_capabilities[0],
            availability=AvailabilityStatus.AVAILABLE,
            confidence=1.0,
            source_refs=(source_refs[0],),
        )
        mastery_value = self._mastery_value(estimates, mastery_refs)
        payload: dict[str, Any] = {
            "context_id": str(context_id),
            "decision_time": decision_time,
            "learning_objective_ref": source_refs[3],
            "learning_activity_ref": source_refs[2],
            "activity_type": activity_value,
            "target_capability": target_value,
            "mastery_estimate_ref": mastery_refs[0] if len(mastery_refs) == 1 else None,
            "mastery_confidence": mastery_value,
            "prerequisite_state_refs": mastery_refs,
            "prerequisite_confidence": mastery_value,
            "evidence_sufficiency": missing,
            "correctness_score": missing,
            "assessment_confidence": missing,
            "error_type": missing,
            "diagnostic_confidence": missing,
            "needs_probe": missing,
            "worked_example_exposure": missing,
            "delayed_independent_evidence": missing,
            "review_context": missing,
            "transfer_evidence": missing,
            "transfer_distance_novelty": missing,
            "time_budget": ValueWithAvailability(
                value=max(60, activity.estimated_duration_minutes * 60),
                availability=AvailabilityStatus.AVAILABLE,
                confidence=1.0,
                source_refs=(source_refs[2],),
            ),
            "source_refs": source_refs,
        }
        fingerprint_payload = {
            key: value
            for key, value in TeachingContextV03.model_validate(
                {**payload, "context_fingerprint": "pending"}
            )
            .model_dump(mode="json")
            .items()
            if key not in {"context_fingerprint"}
        }
        payload["context_fingerprint"] = (
            "sha256:"
            + hashlib.sha256(
                json.dumps(fingerprint_payload, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
        )
        return TeachingContextV03.model_validate(payload)

    @staticmethod
    def _mastery_value(
        estimates: list[MasteryEstimate], refs: tuple[VersionedRef, ...]
    ) -> ValueWithAvailability:
        values = [
            item.competence_probability
            for item in estimates
            if item.competence_probability is not None
        ]
        if not values:
            return ValueWithAvailability(availability=AvailabilityStatus.MISSING)
        return ValueWithAvailability(
            value=sum(values) / len(values),
            availability=AvailabilityStatus.AVAILABLE,
            confidence=min(item.confidence for item in estimates),
            source_refs=refs,
        )

    @staticmethod
    def _mastery_ref(estimate: MasteryEstimate) -> VersionedRef:
        return VersionedRef(
            entity_type="MasteryEstimate",
            entity_id=str(estimate.estimate_id),
            version=estimate.version,
        )

    @classmethod
    def _diagnostic_operation(
        cls, operation: str, correlation_id: UUID, result: DiagnosticBootstrapResult
    ) -> BookLearningOperationResponseV1:
        values: dict[str, Any] = {
            "need": result.need,
            "learner_state": result.learner_state,
            "activities": result.activities,
        }
        if result.plan is not None:
            values["plan"] = result.plan
        if result.assessment_result is not None:
            values["assessment_result"] = result.assessment_result
        return cls._operation(operation, correlation_id, **values)

    @classmethod
    def _operation(
        cls, operation: str, correlation_id: UUID, **values: Any
    ) -> BookLearningOperationResponseV1:
        refs: list[BookLearningOwnerRefV1] = []

        def append_value(value: Any) -> None:
            if isinstance(value, (tuple, list)):
                for item in value:
                    append_value(item)
                return
            if isinstance(value, LearnerVisibleDiagnosticItemV1):
                refs.append(
                    cls._owner_ref(
                        "SYS04",
                        "AssessmentItem",
                        UUID(value.item_ref.entity_id),
                        value.item_ref.version,
                        "learner_visible",
                    )
                )
            elif isinstance(value, LearningGoalV1):
                refs.append(
                    cls._owner_ref(
                        "SYS06", "LearningGoal", value.goal_id, value.version, value.status
                    )
                )
            elif isinstance(value, LearningPlan):
                refs.append(
                    cls._owner_ref(
                        "SYS06", "LearningPlan", value.plan_id, value.version, value.status
                    )
                )
            elif isinstance(value, LearningActivity):
                refs.append(
                    cls._owner_ref(
                        "SYS06",
                        "LearningActivity",
                        value.activity_id,
                        value.plan_version,
                        value.status,
                    )
                )
            elif hasattr(value, "need_id"):
                refs.append(
                    cls._owner_ref(
                        "SYS06", "DiagnosticNeed", value.need_id, value.version, value.status
                    )
                )
            elif hasattr(value, "mapping_id"):
                refs.append(
                    cls._owner_ref(
                        "SYS06",
                        "GoalKnowledgeMapping",
                        value.mapping_id,
                        value.mapping_version,
                        value.status,
                    )
                )
            elif hasattr(value, "subgraph_id"):
                refs.append(
                    cls._owner_ref(
                        "SYS06",
                        "GoalSpecificKnowledgeSubgraph",
                        value.subgraph_id,
                        value.version,
                        "ready",
                    )
                )
            elif hasattr(value, "learner_state_id"):
                refs.append(
                    cls._owner_ref(
                        "SYS03", "LearnerState", value.learner_state_id, value.version, "current"
                    )
                )
            elif hasattr(value, "result_id"):
                refs.append(
                    cls._owner_ref(
                        "SYS04",
                        "AssessmentResult",
                        value.result_id,
                        value.result_version,
                        "recorded",
                    )
                )

        for value in values.values():
            append_value(value)
        return BookLearningOperationResponseV1(
            operation=operation,
            owner_refs=tuple(refs),
            payload={key: cls._json_value(value) for key, value in values.items()},
            correlation_id=str(correlation_id),
        )

    @staticmethod
    def _json_value(value: Any) -> Any:
        if hasattr(value, "model_dump"):
            return value.model_dump(mode="json")
        if isinstance(value, tuple):
            return [BookLearningApplication._json_value(item) for item in value]
        return value

    @staticmethod
    def _owner_ref(
        owner: Literal["SYS01", "SYS02", "SYS03", "SYS04", "SYS05", "SYS06", "SYS08"],
        entity_type: str,
        entity_id: UUID,
        version: str | int,
        status: str,
    ) -> BookLearningOwnerRefV1:
        return BookLearningOwnerRefV1(
            owner_system=owner,
            ref=VersionedRef(entity_type=entity_type, entity_id=str(entity_id), version=version),
            status=status,
        )

    @staticmethod
    def _activity_selected_event(
        *,
        user: User,
        goal: LearningGoalV1,
        plan: LearningPlan,
        activity: LearningActivity,
        idempotency_key: str,
        correlation_id: UUID,
        selected_at: datetime,
    ) -> LearningEventEnvelope:
        return LearningEventEnvelope(
            event_id=uuid5(NAMESPACE_URL, f"askora:activity-selected:{user.id}:{idempotency_key}"),
            event_type="ActivitySelected",
            aggregate_type="LearningActivity",
            aggregate_id=activity.activity_id,
            aggregate_version=activity.plan_version,
            sequence=activity.plan_version,
            occurred_at=selected_at,
            recorded_at=selected_at,
            idempotency_key=f"book-activity-selected:{idempotency_key}",
            correlation_id=correlation_id,
            actor=EventActor(actor_type="learner", actor_id=user.id),
            context=EventContext(
                user_id=canonical_user_id(user.id),
                goal_id=goal.goal_id,
                knowledge_unit_ids=activity.knowledge_unit_ids,
                content_revision_ids=[],
            ),
            payload={
                "goal_ref": f"learning_goal:{goal.goal_id}:v{goal.version}",
                "plan_ref": f"learning_plan:{plan.plan_id}:v{plan.version}",
                "activity_ref": f"learning_activity:{activity.activity_id}:v{activity.plan_version}",
            },
            provenance=EventProvenance(source="api", algorithm_version="sys06-select-v1"),
            trace=EventTrace(trace_id=f"book-learning:{correlation_id}"),
            privacy=EventPrivacy(
                classification="personal",
                external_processing=False,
                retention_class="core_learning",
            ),
        )

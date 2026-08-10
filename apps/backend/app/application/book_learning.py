"""SPEC-D06 Book-to-Learning application composition over canonical owners."""

from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Literal, Protocol
from uuid import NAMESPACE_URL, UUID, uuid5
from weakref import WeakValueDictionary

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.activity_lifecycle import StartLearningActivityV1
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
    BookLearningTranscriptEvidenceV1,
    BookLearningTranscriptTurnV1,
    BookLearningTranscriptV1,
    LearnerVisibleDiagnosticItemV1,
)
from app.contracts.decisions import DecisionTraceV03
from app.contracts.events import (
    ActualAssistanceRecordedPayloadV03,
    EventActor,
    EventContext,
    EventPrivacy,
    EventProvenanceV03,
    EventTrace,
    LearningEventEnvelopeV03,
)
from app.contracts.learning import LearningActivity, LearningPlan, MasteryEstimate
from app.contracts.model_execution import ModelExecutionV1
from app.contracts.planning import LearningGoalV1
from app.infrastructure.activity_lifecycle import ActivityLifecycleRepository
from app.infrastructure.adaptive_records import (
    AdaptiveContractRepository,
    DecisionTraceV03Repository,
    LearningEventV03Repository,
)
from app.infrastructure.book_learning_transcript import BookLearningTranscriptRepository
from app.infrastructure.learning_records import LearnerModelRepository
from app.infrastructure.planning_records import (
    DiagnosticNeedRepository,
    GoalPlanningRepository,
    LearningPlanRepository,
)
from app.models.adaptive import TeachingContextRecord
from app.models.book_learning import BookLearningAdvanceRecord, BookLearningTranscriptTurnRecord
from app.models.planning import LearningActivityRecord, LearningPlanRecord
from app.models.user import User
from app.orchestration.learning_facade import CanonicalTurnRequest, LearningOrchestrationFacade
from app.orchestration.model_rendering import ModelRenderingError
from app.queries.book_learning import BookLearningReadinessQuery
from app.queries.diagnostic_assessment import DiagnosticAssessmentItemQuery
from app.services.activity_lifecycle import ActivityLifecycleService
from app.services.assessment.diagnostic_bootstrap import (
    DiagnosticBootstrapResult,
    PrerequisiteDiagnosticService,
)
from app.services.kt.canonical_projector import CanonicalLearnerProjectorService
from app.services.learning_goals import LearningGoalService
from app.services.owner.canonical_identity import canonical_user_id
from app.services.policy_runtime import (
    ActivePolicyRuntimeResolver,
    PolicyRuntimeResolutionError,
    PolicyRuntimeSelection,
)
from app.services.rag_service import PublishedKnowledgeRAGService

_BOOK_TURN_LOCKS: WeakValueDictionary[tuple[int, str], asyncio.Lock] = WeakValueDictionary()


def _book_turn_lock(key: str) -> asyncio.Lock:
    loop = asyncio.get_running_loop()
    scoped_key = (id(loop), key)
    lock = _BOOK_TURN_LOCKS.get(scoped_key)
    if lock is None:
        lock = asyncio.Lock()
        _BOOK_TURN_LOCKS[scoped_key] = lock
    return lock


class BookLearningApplicationError(ValueError):
    """Fail-closed application error mapped by the transport layer."""

    def __init__(
        self,
        code: str,
        *,
        category: str = "business",
        retryable: bool = False,
        retry_after_seconds: int | None = None,
    ) -> None:
        self.code = code
        self.category = category
        self.retryable = retryable
        self.retry_after_seconds = retry_after_seconds
        super().__init__(code)


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
        self._transcript_repo = BookLearningTranscriptRepository(db)
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

    async def advance(
        self,
        *,
        user: User,
        document_id: UUID,
        idempotency_key: str,
        correlation_id: UUID,
        now: datetime | None = None,
    ) -> BookLearningOperationResponseV1:
        """Execute exactly one readiness-authorized, non-user-input owner command."""

        user_id = str(canonical_user_id(user.id))
        existing_advance = await self._transcript_repo.get_advance_by_idempotency(
            user_id=user_id, idempotency_key=idempotency_key
        )
        if existing_advance is not None:
            if existing_advance.document_id != str(document_id):
                raise BookLearningApplicationError("BOOK_ADVANCE_IDEMPOTENCY_SCOPE_CONFLICT")
            return BookLearningOperationResponseV1.model_validate(existing_advance.response_payload)
        readiness = await self.readiness(
            user=user,
            document_id=document_id,
            correlation_id=str(correlation_id),
        )
        allowed = {
            "MapGoalToKnowledge",
            "BuildGoalKnowledgeSubgraph",
            "GeneratePrerequisiteDiagnosis",
            "GenerateLearningPlan",
            "SelectNextLearningActivity",
        }
        commands = tuple(command for command in readiness.next_commands if command in allowed)
        if len(commands) != 1:
            raise BookLearningApplicationError("BOOK_LEARNING_USER_INPUT_REQUIRED")
        command = commands[0]
        command_key = (
            f"book-advance:{command}:{hashlib.sha256(idempotency_key.encode('utf-8')).hexdigest()}"
        )
        goal_id = self._readiness_ref_id(readiness, "LearningGoal")
        if goal_id is None:
            raise BookLearningApplicationError("BOOK_LEARNING_GOAL_REF_MISSING")

        if command in {"MapGoalToKnowledge", "BuildGoalKnowledgeSubgraph"}:
            await self.map_goal(
                user=user,
                goal_id=goal_id,
                idempotency_key=command_key,
                correlation_id=correlation_id,
                now=now,
            )
        elif command == "GeneratePrerequisiteDiagnosis":
            mapping = await self._goal_repo.latest_mapping(goal_id)
            if mapping is None or not mapping.selected_target_ids:
                raise BookLearningApplicationError("PRIMARY_DIAGNOSTIC_TARGET_MISSING")
            subgraph = await self._goal_repo.latest_subgraph_for_mapping(mapping.mapping_id)
            if subgraph is None:
                raise BookLearningApplicationError("GOAL_SUBGRAPH_REQUIRED")
            await self.start_diagnostic(
                user=user,
                mapping_id=mapping.mapping_id,
                mapping_version=mapping.mapping_version,
                subgraph_id=subgraph.subgraph_id,
                subgraph_version=subgraph.version,
                target_knowledge_unit_id=mapping.selected_target_ids[0],
                max_attempts=3,
                idempotency_key=command_key,
                correlation_id=correlation_id,
                now=now,
            )
        elif command == "GenerateLearningPlan":
            mapping = await self._goal_repo.latest_mapping(goal_id)
            if mapping is None:
                raise BookLearningApplicationError("GOAL_KNOWLEDGE_MAPPING_NOT_FOUND")
            need = await self._need_repo.latest_for_mapping(
                mapping_id=mapping.mapping_id,
                user_id=canonical_user_id(user.id),
            )
            if need is None:
                raise BookLearningApplicationError("DIAGNOSTIC_NEED_NOT_FOUND")
            await self.generate_plan(
                user=user,
                need_id=need.need_id,
                idempotency_key=command_key,
                correlation_id=correlation_id,
                now=now,
            )
        else:
            await self.select_next_activity(
                user=user,
                goal_id=goal_id,
                idempotency_key=command_key,
                correlation_id=correlation_id,
                now=now,
            )

        next_readiness = await self.readiness(
            user=user,
            document_id=document_id,
            correlation_id=str(correlation_id),
        )
        response = BookLearningOperationResponseV1(
            operation="AdvanceBookLearning",
            owner_refs=next_readiness.owner_refs,
            payload={
                "applied_command": command,
                "readiness": next_readiness.model_dump(mode="json"),
            },
            correlation_id=str(correlation_id),
        )
        await self._transcript_repo.append_advance(
            BookLearningAdvanceRecord(
                advance_record_id=str(
                    uuid5(
                        NAMESPACE_URL,
                        f"askora:book-advance:{user_id}:{idempotency_key}",
                    )
                ),
                schema_version="1.0",
                user_id=user_id,
                document_id=str(document_id),
                idempotency_key=idempotency_key,
                applied_command=command,
                response_payload=response.model_dump(mode="json"),
                created_at=now or datetime.now(timezone.utc),
            )
        )
        return response

    async def get_transcript(
        self,
        *,
        user: User,
        activity_id: UUID,
        correlation_id: UUID,
    ) -> BookLearningTranscriptV1:
        _goal, _plan, activity = await self._require_activity_for_user(
            user=user, activity_id=activity_id
        )
        user_id = str(canonical_user_id(user.id))
        records = await self._transcript_repo.list_for_activity(
            user_id=user_id, activity_id=str(activity.activity_id)
        )
        session_id = self._transcript_session_id(user=user, activity=activity)
        if records:
            session_ids = {record.session_id for record in records}
            if len(session_ids) != 1 or session_ids != {str(session_id)}:
                raise BookLearningApplicationError("BOOK_TRANSCRIPT_SESSION_CONFLICT")
        turns = tuple(self._transcript_turn(record) for record in records)
        return BookLearningTranscriptV1(
            session_id=session_id,
            activity_ref=VersionedRef(
                entity_type="LearningActivity",
                entity_id=str(activity.activity_id),
                version=activity.plan_version,
            ),
            turns=turns,
            next_turn_number=(turns[-1].turn_number + 1 if turns else 1),
            correlation_id=str(correlation_id),
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
        lifecycle_service = ActivityLifecycleService(self._db)
        lifecycle = await lifecycle_service.replay_select_next(
            user=user,
            goal_id=goal.goal_id,
            idempotency_key=idempotency_key,
        )
        if lifecycle is None:
            await self._require_book_state(user=user, goal=goal, expected="PLAN_READY")
            lifecycle = await lifecycle_service.select_next(
                user=user,
                goal_id=goal.goal_id,
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                now=now,
            )
        selected_id = lifecycle.data.state.activity_id
        activity = next(
            (item for item in activities if item.activity_id == selected_id),
            None,
        )
        if activity is None:
            raise BookLearningApplicationError("LEARNING_ACTIVITY_NOT_AVAILABLE")
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
        session_id: UUID | None,
        turn_id: str,
        learner_text: str | None,
        idempotency_key: str,
        correlation_id: UUID,
        turn_kind: Literal["learner", "system_start"] = "learner",
        now: datetime | None = None,
    ) -> BookLearningTeachingResponseV1:
        lock_key = f"{canonical_user_id(user.id)}:{idempotency_key}"
        async with _book_turn_lock(lock_key):
            return await self._start_teaching_round_locked(
                user=user,
                goal_id=goal_id,
                plan_id=plan_id,
                plan_version=plan_version,
                activity_id=activity_id,
                session_id=session_id,
                turn_id=turn_id,
                turn_kind=turn_kind,
                learner_text=learner_text,
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                now=now,
            )

    async def _start_teaching_round_locked(
        self,
        *,
        user: User,
        goal_id: UUID,
        plan_id: UUID,
        plan_version: int,
        activity_id: UUID,
        session_id: UUID | None,
        turn_id: str,
        turn_kind: Literal["learner", "system_start"],
        learner_text: str | None,
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
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
            now=now,
        )
        user_id = str(canonical_user_id(user.id))
        transcript_session_id = self._transcript_session_id(user=user, activity=activity)
        existing_turn = await self._transcript_repo.get_by_idempotency(
            user_id=user_id, idempotency_key=idempotency_key
        )
        if existing_turn is not None:
            expected_learner_text = learner_text.strip() if learner_text else None
            if (
                existing_turn.goal_id != str(goal.goal_id)
                or existing_turn.plan_id != str(plan.plan_id)
                or existing_turn.plan_version != plan.version
                or existing_turn.activity_id != str(activity.activity_id)
                or existing_turn.session_id != str(transcript_session_id)
                or existing_turn.turn_id != turn_id
                or existing_turn.turn_kind != turn_kind
                or existing_turn.learner_text != expected_learner_text
            ):
                raise BookLearningApplicationError("BOOK_TRANSCRIPT_IDEMPOTENCY_CONFLICT")
            return BookLearningTeachingResponseV1.model_validate(existing_turn.response_payload)

        await self._require_book_state(user=user, goal=goal, expected="READY_TO_LEARN")
        existing_activity_turns = await self._transcript_repo.list_for_activity(
            user_id=user_id, activity_id=str(activity.activity_id)
        )
        if turn_kind == "system_start" and existing_activity_turns:
            raise BookLearningApplicationError("BOOK_SYSTEM_START_ALREADY_ACCEPTED")
        if turn_kind == "system_start":
            resolved_text = (
                f"请开始本次学习活动。学习主题：{goal.topic}；"
                f"目标能力：{goal.target_capabilities[0]}。"
                "依据资料先提出一个聚焦的引导问题，"
                "不要假设学习者已经掌握，也不要把这个系统指令当作学习者回答。"
            )
            stored_learner_text = None
        else:
            resolved_text = (learner_text or "").strip()
            if not resolved_text:
                raise BookLearningApplicationError("BOOK_LEARNER_TEXT_REQUIRED")
            stored_learner_text = resolved_text
        accepted_at = now or datetime.now(timezone.utc)
        turn_number = await self._transcript_repo.next_turn_number(
            session_id=str(transcript_session_id)
        )
        try:
            runtime = await self._policy_runtime.resolve()
        except PolicyRuntimeResolutionError as exc:
            raise BookLearningApplicationError(str(exc)) from exc
        runtime.profile.assert_matches(runtime.bundle)
        previous_action: TeachingActionV03 | None = None
        previous_trace: DecisionTraceV03 | None = None
        if existing_activity_turns:
            last_turn = existing_activity_turns[-1]
            last_payload = BookLearningTeachingResponseV1.model_validate(last_turn.response_payload)
            prior = last_payload.teaching_action
            # P0-1: a canonical previous TeachingAction already exists; the exact
            # DecisionTrace is REQUIRED for a sequential decision. Any missing /
            # mismatched / out-of-scope prior evidence must fail closed, never
            # silently downgrade to a first-turn bootstrap kernel.
            if prior.learning_activity_ref.entity_id != str(activity.activity_id):
                raise BookLearningApplicationError(
                    "SEQUENTIAL_PREVIOUS_ACTION_SCOPE_MISMATCH",
                    category="integrity",
                )
            prior_trace = await DecisionTraceV03Repository(self._db).get(prior.decision_id)
            if prior_trace is None:
                raise BookLearningApplicationError(
                    "SEQUENTIAL_PREVIOUS_DECISION_TRACE_MISSING",
                    category="integrity",
                )
            selected = prior_trace.selected_teaching_action_ref
            if (
                selected is None
                or selected.entity_id != str(prior.action_id)
                or str(selected.version) != prior.action_schema_version
            ):
                raise BookLearningApplicationError(
                    "SEQUENTIAL_PREVIOUS_TRACE_ACTION_MISMATCH",
                    category="integrity",
                )
            previous_action = prior
            previous_trace = prior_trace
        context = await self._teaching_context(
            user=user,
            goal=goal,
            plan=plan,
            activity=activity,
            idempotency_key=idempotency_key,
            decision_time=accepted_at,
            previous_action=previous_action,
            previous_trace=previous_trace,
        )
        inputs = await self._retrieval.load_adaptive_input(
            pseudonym_id=user.pseudonym_id,
            source_scope={"document_ids": [str(item) for item in goal.source_document_ids]},
        )
        records = AdaptiveContractRepository(self._db)
        await records.publish_policy_bundle(runtime.bundle)
        context_payload = context.model_copy()
        if previous_action is not None:
            context_payload = context_payload.model_copy(
                update={
                    "previous_teaching_action_ref": VersionedRef(
                        entity_type="teaching_action",
                        entity_id=str(previous_action.action_id),
                        version=previous_action.action_schema_version,
                    )
                }
            )
            context = context_payload
        await records.save_context(context)
        inference_id = uuid5(
            NAMESPACE_URL,
            f"askora:book-model-inference:{user_id}:{idempotency_key}",
        )
        try:
            result = await self._teaching.run_turn(
                CanonicalTurnRequest(
                    session_id=str(transcript_session_id),
                    user_id=user.id,
                    text=resolved_text,
                    turn_id=turn_id,
                    subject=goal.topic,
                    knowledge_point_id=(
                        str(activity.knowledge_unit_ids[0]) if activity.knowledge_unit_ids else None
                    ),
                    correlation_id=str(correlation_id),
                    model_inference_id=str(inference_id),
                    teaching_context_v03=context,
                    policy_bundle_v03=runtime.bundle,
                    policy_profile_v03=runtime.profile,
                    adaptive_retrieval_candidates=inputs.candidates,
                    adaptive_source_scope=inputs.source_scope,
                    adaptive_index_versions=inputs.index_versions,
                    previous_teaching_action_v03=previous_action,
                    previous_decision_trace_v03=previous_trace,
                )
            )
        except ModelRenderingError as exc:
            raise BookLearningApplicationError(
                exc.code,
                category=("transient" if exc.retryable else "dependency"),
                retryable=exc.retryable,
                retry_after_seconds=exc.retry_after_seconds,
            ) from exc
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
        model_execution = result.adaptive_execution_v03.model_execution
        event_records = LearningEventV03Repository(self._db)
        model_event: LearningEventEnvelopeV03 | None = None
        if model_execution is not None and model_execution.mode == "real_model":
            model_event = self._model_inference_event(
                user=user,
                goal=goal,
                activity=activity,
                teaching_action=result.teaching_action_v03,
                evidence_bundle_id=result.evidence_bundle_v03.bundle_id,
                evidence_bundle_version=result.evidence_bundle_v03.bundle_schema_version,
                model_execution=model_execution,
                response_length=len(result.reply_text),
                session_id=transcript_session_id,
                correlation_id=correlation_id,
                occurred_at=context.decision_time,
            )
            existing_model_event = await event_records.get(model_event.event_id)
            if existing_model_event is not None:
                if (
                    existing_model_event.aggregate_id != model_event.aggregate_id
                    or existing_model_event.payload != model_event.payload
                    or existing_model_event.context.user_id != model_event.context.user_id
                ):
                    raise BookLearningApplicationError("MODEL_INFERENCE_IDEMPOTENCY_CONFLICT")
                model_event = existing_model_event
            else:
                await event_records.append(model_event)
        assistance_event = self._actual_assistance_event(
            user=user,
            goal=goal,
            activity=activity,
            teaching_action=result.teaching_action_v03,
            event_payload=result.actual_assistance_event_v03,
            response_id=result.adaptive_execution_v03.response_id,
            policy_version=runtime.bundle.policy_version,
            session_id=transcript_session_id,
            correlation_id=correlation_id,
            occurred_at=context.decision_time,
        )
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
        refs = [
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
        ]
        if model_event is not None and model_execution is not None:
            refs.append(
                self._owner_ref(
                    "SYS08",
                    "ModelInference",
                    model_execution.inference_id,
                    model_execution.schema_version,
                    "completed",
                )
            )
        response = BookLearningTeachingResponseV1(
            reply_text=result.reply_text,
            teaching_action=result.teaching_action_v03,
            evidence_bundle=result.evidence_bundle_v03,
            decision_trace_v03=result.decision_trace_v03,
            owner_refs=tuple(refs),
            session_id=transcript_session_id,
            turn_id=turn_id,
            turn_number=turn_number,
            turn_kind=turn_kind,
            accepted_at=accepted_at,
            correlation_id=str(correlation_id),
            model_execution=model_execution,
        )
        await self._transcript_repo.append(
            BookLearningTranscriptTurnRecord(
                turn_record_id=str(
                    uuid5(
                        NAMESPACE_URL,
                        f"askora:book-transcript-turn:{transcript_session_id}:{turn_number}",
                    )
                ),
                schema_version="1.0",
                user_id=user_id,
                goal_id=str(goal.goal_id),
                plan_id=str(plan.plan_id),
                plan_version=plan.version,
                activity_id=str(activity.activity_id),
                session_id=str(transcript_session_id),
                turn_id=turn_id,
                turn_number=turn_number,
                turn_kind=turn_kind,
                idempotency_key=idempotency_key,
                learner_text=stored_learner_text,
                response_payload=response.model_dump(mode="json"),
                created_at=accepted_at,
            )
        )
        return response

    @staticmethod
    def _model_inference_event(
        *,
        user: User,
        goal: LearningGoalV1,
        activity: LearningActivity,
        teaching_action: TeachingActionV03,
        evidence_bundle_id: UUID,
        evidence_bundle_version: str,
        model_execution: ModelExecutionV1,
        response_length: int,
        session_id: UUID,
        correlation_id: UUID,
        occurred_at: datetime,
    ) -> LearningEventEnvelopeV03:
        event_id = uuid5(
            NAMESPACE_URL,
            f"askora:model-inference-completed:{model_execution.inference_id}",
        )
        return LearningEventEnvelopeV03(
            event_id=event_id,
            event_type="ModelInferenceCompleted",
            aggregate_type="ModelInference",
            aggregate_id=model_execution.inference_id,
            aggregate_version=1,
            sequence=1,
            occurred_at=occurred_at,
            recorded_at=occurred_at,
            idempotency_key=f"book-model-inference:{model_execution.inference_id}",
            correlation_id=correlation_id,
            causation_id=teaching_action.action_id,
            actor=EventActor(
                actor_type="model",
                actor_id=f"{model_execution.provider}:{model_execution.model}",
            ),
            context=EventContext(
                user_id=canonical_user_id(user.id),
                session_id=session_id,
                goal_id=goal.goal_id,
                knowledge_unit_ids=list(activity.knowledge_unit_ids),
                content_revision_ids=[],
            ),
            producer_system="SYS08",
            payload={
                "task_type": "policy_bound_language_realization",
                "workflow_version": "book-learning-teaching/1.0",
                "teaching_action_ref": {
                    "entity_type": "TeachingAction",
                    "entity_id": str(teaching_action.action_id),
                    "version": teaching_action.action_schema_version,
                },
                "evidence_bundle_ref": {
                    "entity_type": "EvidenceBundle",
                    "entity_id": str(evidence_bundle_id),
                    "version": evidence_bundle_version,
                },
                "response_length": response_length,
                "latency_ms": model_execution.latency_ms,
                "token_usage": {
                    "input": model_execution.input_tokens,
                    "output": model_execution.output_tokens,
                    "total": model_execution.total_tokens,
                },
            },
            provenance=EventProvenanceV03(
                source="orchestrator",
                model_provider=model_execution.provider,
                model_name=model_execution.model,
                prompt_id="policy-bound-real-render",
                prompt_version=model_execution.prompt_version,
                policy_bundle_ref=teaching_action.policy_bundle_ref,
            ),
            trace=EventTrace(trace_id=f"book-model-inference:{model_execution.inference_id}"),
            privacy=EventPrivacy(
                classification="personal",
                external_processing=True,
                retention_class="core_learning",
            ),
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

    @staticmethod
    def _readiness_ref_id(readiness: BookLearningReadinessV1, entity_type: str) -> UUID | None:
        ref = next(
            (item.ref for item in readiness.owner_refs if item.ref.entity_type == entity_type),
            None,
        )
        if ref is None:
            return None
        try:
            return UUID(ref.entity_id)
        except ValueError as exc:
            raise BookLearningApplicationError(
                f"BOOK_LEARNING_{entity_type.upper()}_REF_INVALID"
            ) from exc

    @staticmethod
    def _transcript_session_id(*, user: User, activity: LearningActivity) -> UUID:
        return uuid5(
            NAMESPACE_URL,
            f"askora:book-transcript:{canonical_user_id(user.id)}:{activity.activity_id}",
        )

    @staticmethod
    def _transcript_turn(
        record: BookLearningTranscriptTurnRecord,
    ) -> BookLearningTranscriptTurnV1:
        response = BookLearningTeachingResponseV1.model_validate(record.response_payload)
        if any(item.allowed_use != "learner_visible" for item in response.evidence_bundle.items):
            raise BookLearningApplicationError("BOOK_TRANSCRIPT_EVIDENCE_VISIBILITY_DENIED")
        evidence = tuple(
            BookLearningTranscriptEvidenceV1(
                evidence_id=item.evidence_id,
                source_span_ids=item.source_span_ids,
                pedagogical_role=item.pedagogical_role,
                excerpt=item.content.strip()[:2000],
            )
            for item in response.evidence_bundle.items
            if item.content.strip()
        )
        return BookLearningTranscriptTurnV1(
            turn_id=response.turn_id,
            turn_number=response.turn_number,
            turn_kind=response.turn_kind,
            learner_text=record.learner_text,
            reply_text=response.reply_text,
            teaching_action_ref=VersionedRef(
                entity_type="TeachingAction",
                entity_id=str(response.teaching_action.action_id),
                version=response.teaching_action.action_schema_version,
            ),
            evidence_bundle_ref=VersionedRef(
                entity_type="EvidenceBundle",
                entity_id=str(response.evidence_bundle.bundle_id),
                version=response.evidence_bundle.bundle_schema_version,
            ),
            evidence=evidence,
            accepted_at=response.accepted_at,
            model_execution=response.model_execution,
        )

    async def _require_activity_for_user(
        self, *, user: User, activity_id: UUID
    ) -> tuple[LearningGoalV1, LearningPlan, LearningActivity]:
        activity_record = await self._db.get(LearningActivityRecord, str(activity_id))
        if activity_record is None:
            raise BookLearningApplicationError("LEARNING_ACTIVITY_NOT_FOUND")
        activity = LearningActivity.model_validate(activity_record.payload)
        plan_record = await self._db.scalar(
            select(LearningPlanRecord).where(
                LearningPlanRecord.plan_id == activity_record.plan_id,
                LearningPlanRecord.version == activity_record.plan_version,
            )
        )
        if plan_record is None:
            raise BookLearningApplicationError("LEARNING_PLAN_NOT_FOUND")
        plan = LearningPlan.model_validate(plan_record.payload).model_copy(
            update={"status": plan_record.status}
        )
        goal = await self._require_goal(user, plan.learning_goal_id)
        state = await ActivityLifecycleRepository(self._db).latest(activity.activity_id)
        if state is None or state.status not in {"available", "active", "completed"}:
            raise BookLearningApplicationError("LEARNING_ACTIVITY_NOT_SELECTED")
        return goal, plan, activity

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
        idempotency_key: str,
        correlation_id: UUID,
        now: datetime | None,
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
        state = await ActivityLifecycleRepository(self._db).latest(activity_id)
        if state is not None and state.status == "available":
            await ActivityLifecycleService(self._db).start(
                user=user,
                command=StartLearningActivityV1(
                    activity_id=activity_id,
                    expected_state_version=state.version,
                    idempotency_key=str(
                        uuid5(
                            NAMESPACE_URL,
                            f"askora:book-compat-start:{user.id}:{idempotency_key}",
                        )
                    ),
                ),
                correlation_id=correlation_id,
                now=now,
            )
            state = await ActivityLifecycleRepository(self._db).latest(activity_id)
        if state is None or state.status != "active":
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
        previous_action: TeachingActionV03 | None = None,
        previous_trace: DecisionTraceV03 | None = None,
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
        recent_evidence = await self._learner_repo.latest_evidence_across_units(
            user_id=canonical_user_id(user.id),
            knowledge_unit_ids=tuple(activity.knowledge_unit_ids),
        )
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
        recent_assessment_result_ref: VersionedRef | None = None
        recent_assessment_value: ValueWithAvailability | None = None
        if recent_evidence is not None and recent_evidence.result_id is not None:
            recent_assessment_result_ref = VersionedRef(
                entity_type="AssessmentResult",
                entity_id=str(recent_evidence.result_id),
                version=1,
            )
            recent_assessment_value = ValueWithAvailability(
                value=recent_evidence.score,
                availability=AvailabilityStatus.AVAILABLE,
                confidence=recent_evidence.confidence,
                source_refs=(recent_assessment_result_ref,),
            )
            refs.append(recent_assessment_result_ref)
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
        previous_action_outcome_refs: tuple[VersionedRef, ...] = ()
        independent_success_history: tuple[VersionedRef, ...] = ()
        assisted_success_history: tuple[VersionedRef, ...] = ()
        worked_example_refs: list[VersionedRef] = []
        if previous_trace is not None:
            previous_action_outcome_refs = tuple(previous_trace.material_evidence_refs)
        if state is not None:
            progress = state.learner_progress_summary or {}
            independent_ids = progress.get("independent_success_result_ids")
            assisted_ids = progress.get("assisted_success_result_ids")
            if not isinstance(independent_ids, (list, tuple)):
                independent_ids = []
            if not isinstance(assisted_ids, (list, tuple)):
                assisted_ids = []
            independent_success_history = tuple(
                VersionedRef(
                    entity_type="AssessmentResult",
                    entity_id=str(item),
                    version="1",
                )
                for item in independent_ids
            )
            assisted_success_history = tuple(
                VersionedRef(
                    entity_type="AssessmentResult",
                    entity_id=str(item),
                    version="1",
                )
                for item in assisted_ids
            )
            worked_example_count = progress.get("worked_example_exposure_count")
            if (
                previous_action is not None
                and isinstance(worked_example_count, int)
                and worked_example_count > 0
            ):
                worked_example_refs = [
                    VersionedRef(
                        entity_type="TeachingAction",
                        entity_id=str(previous_action.action_id),
                        version=previous_action.action_schema_version,
                    )
                ]
        consecutive_failures = 0
        if state is not None:
            uncertainty = state.uncertainty_summary or {}
            cf = uncertainty.get("consecutive_failures")
            if isinstance(cf, int):
                consecutive_failures = cf
        assistance_history_summary: dict[str, Any] = {
            "consecutive_failures": consecutive_failures,
        }
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
            "correctness_score": (
                recent_assessment_value if recent_assessment_value is not None else missing
            ),
            "assessment_confidence": (
                recent_assessment_value if recent_assessment_value is not None else missing
            ),
            "recent_assessment_result_ref": recent_assessment_result_ref,
            "error_type": missing,
            "diagnostic_confidence": missing,
            "needs_probe": missing,
            "worked_example_exposure": (
                ValueWithAvailability(
                    value=True,
                    availability=AvailabilityStatus.AVAILABLE,
                    confidence=1.0,
                    source_refs=tuple(worked_example_refs),
                )
                if worked_example_refs
                else missing
            ),
            "assistance_history_summary": assistance_history_summary,
            "independent_success_history": independent_success_history,
            "assisted_success_history": assisted_success_history,
            "previous_action_outcome_refs": previous_action_outcome_refs,
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
        if previous_action is not None:
            prev_ref = VersionedRef(
                entity_type="teaching_action",
                entity_id=str(previous_action.action_id),
                version=previous_action.action_schema_version,
            )
            payload["previous_teaching_action_ref"] = prev_ref
            payload["source_refs"] = tuple(list(source_refs) + [prev_ref])
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

"""SYS06 application service for SPEC-D04 goal formation and mapping."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy.ext.asyncio import AsyncSession

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
from app.contracts.planning import GoalFormationInferenceV1, LearningGoalV1
from app.domains.learning_planner import (
    GoalKnowledgeMapper,
    GoalMappingDecision,
    measurable_success_criterion,
)
from app.infrastructure.ledger import DecisionTraceRepository, LearningEventRepository
from app.infrastructure.planning_records import GoalPlanningRepository
from app.models.user import User
from app.queries.goal_knowledge import GoalKnowledgeQueryService
from app.services.auth.canonical_identity import canonical_user_id

GOAL_FORMATION_PROMPT_VERSION = "goal-formation-bounded-v1"
GOAL_FORMATION_OUTPUT_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class GoalFormationModelResult:
    provider: str
    model_name: str
    model_snapshot: str | None
    structured_result: dict[str, object]


class GoalFormationModelPort(Protocol):
    async def form_goal_candidate(
        self,
        *,
        intent: str,
        source_document_ids: tuple[UUID, ...],
        prompt_version: str,
        output_schema_version: str,
    ) -> GoalFormationModelResult: ...


class LearningGoalService:
    """One SYS06 writer path; callers commit the surrounding local transaction."""

    def __init__(
        self,
        db: AsyncSession,
        *,
        model_port: GoalFormationModelPort | None = None,
        mapper: GoalKnowledgeMapper | None = None,
    ) -> None:
        self._db = db
        self._repo = GoalPlanningRepository(db)
        self._knowledge = GoalKnowledgeQueryService(db)
        self._model_port = model_port
        self._mapper = mapper or GoalKnowledgeMapper()

    async def create_candidate(
        self,
        *,
        user: User,
        intent: str,
        source_document_ids: tuple[UUID, ...],
        idempotency_key: str,
        correlation_id: UUID,
        created_at: datetime,
        application_context: str | None = None,
        deadline_at: datetime | None = None,
        weekly_time_budget_minutes: int | None = None,
    ) -> LearningGoalV1:
        existing = await self._repo.find_goal_by_idempotency(idempotency_key)
        if existing is not None:
            return existing
        goal_id = uuid5(
            NAMESPACE_URL,
            f"askora:learning-goal:{user.id}:{idempotency_key}",
        )
        goal = await self._form_candidate(
            goal_id=goal_id,
            version=1,
            user=user,
            intent=intent,
            source_document_ids=source_document_ids,
            created_at=created_at,
            application_context=application_context,
            deadline_at=deadline_at,
            weekly_time_budget_minutes=weekly_time_budget_minutes,
        )
        saved = await self._repo.save_goal(goal, idempotency_key=idempotency_key)
        await self._append_goal_event(
            goal=saved,
            event_type="GoalCreated",
            correlation_id=correlation_id,
            idempotency_key=f"goal-created:{idempotency_key}",
        )
        return saved

    async def revise_candidate(
        self,
        *,
        user: User,
        goal_id: UUID,
        intent: str,
        source_document_ids: tuple[UUID, ...],
        idempotency_key: str,
        correlation_id: UUID,
        created_at: datetime,
        application_context: str | None = None,
        deadline_at: datetime | None = None,
        weekly_time_budget_minutes: int | None = None,
    ) -> LearningGoalV1:
        existing = await self._repo.find_goal_by_idempotency(idempotency_key)
        if existing is not None:
            return existing
        prior = await self._repo.latest_goal(goal_id=goal_id, user_id=canonical_user_id(user.id))
        if prior is None:
            raise ValueError("LEARNING_GOAL_NOT_FOUND")
        version = await self._repo.next_goal_version(goal_id)
        goal = await self._form_candidate(
            goal_id=goal_id,
            version=version,
            user=user,
            intent=intent,
            source_document_ids=source_document_ids,
            created_at=created_at,
            application_context=application_context,
            deadline_at=deadline_at,
            weekly_time_budget_minutes=weekly_time_budget_minutes,
            supersedes_version=prior.version,
        )
        saved = await self._repo.save_goal(goal, idempotency_key=idempotency_key)
        await self._append_goal_event(
            goal=saved,
            event_type="GoalCreated",
            correlation_id=correlation_id,
            idempotency_key=f"goal-revised:{idempotency_key}",
        )
        return saved

    async def confirm_goal(
        self,
        *,
        user: User,
        goal_id: UUID,
        idempotency_key: str,
        correlation_id: UUID,
        confirmed_at: datetime,
        confirmed_by_user: bool,
    ) -> LearningGoalV1:
        if not confirmed_by_user:
            raise ValueError("LEARNING_GOAL_USER_CONFIRMATION_REQUIRED")
        existing = await self._repo.find_goal_by_idempotency(idempotency_key)
        if existing is not None:
            return existing
        candidate = await self._repo.latest_goal(
            goal_id=goal_id, user_id=canonical_user_id(user.id)
        )
        if candidate is None:
            raise ValueError("LEARNING_GOAL_NOT_FOUND")
        if candidate.status != "candidate":
            raise ValueError("LEARNING_GOAL_NOT_CONFIRMABLE")
        confirmed = candidate.model_copy(
            update={
                "version": await self._repo.next_goal_version(goal_id),
                "status": "confirmed",
                "confirmed_by_user": True,
                "confirmed_at": confirmed_at,
                "created_at": confirmed_at,
                "supersedes_version": candidate.version,
                "reason_codes": (*candidate.reason_codes, "GOAL_EXPLICITLY_CONFIRMED_BY_USER"),
            }
        )
        saved = await self._repo.save_goal(confirmed, idempotency_key=idempotency_key)
        await self._append_goal_event(
            goal=saved,
            event_type="GoalConfirmed",
            correlation_id=correlation_id,
            idempotency_key=f"goal-confirmed:{idempotency_key}",
        )
        return saved

    async def map_goal(
        self,
        *,
        user: User,
        goal_id: UUID,
        idempotency_key: str,
        correlation_id: UUID,
        created_at: datetime,
    ) -> GoalMappingDecision:
        existing = await self._repo.find_mapping_by_idempotency(idempotency_key)
        goal = (
            await self._repo.get_goal_version(
                goal_id=goal_id,
                version=existing.goal_version,
                user_id=canonical_user_id(user.id),
            )
            if existing is not None
            else await self._repo.latest_goal(goal_id=goal_id, user_id=canonical_user_id(user.id))
        )
        if goal is None:
            raise ValueError("LEARNING_GOAL_NOT_FOUND")
        if existing is not None:
            scope = await self._knowledge.load_scope(
                user=user,
                source_document_ids=goal.source_document_ids,
            )
            replayed = self._mapper.map(
                goal=goal,
                scope=scope,
                mapping_version=existing.mapping_version,
                created_at=existing.created_at,
                persisted_semantic_scores=await self._semantic_scores(goal, scope),
                model_reason_codes=await self._model_mapping_reasons(goal),
            )
            if replayed.mapping != existing:
                raise ValueError("GOAL_MAPPING_REPLAY_MISMATCH")
            return replayed

        scope = await self._knowledge.load_scope(
            user=user,
            source_document_ids=goal.source_document_ids,
        )
        mapping_version = await self._repo.next_mapping_version(goal.goal_id)
        decision = self._mapper.map(
            goal=goal,
            scope=scope,
            mapping_version=mapping_version,
            created_at=created_at,
            persisted_semantic_scores=await self._semantic_scores(goal, scope),
            model_reason_codes=await self._model_mapping_reasons(goal),
        )
        await self._repo.save_mapping(decision.mapping, idempotency_key=idempotency_key)
        if decision.subgraph is not None:
            await self._repo.save_subgraph(decision.subgraph)
        await DecisionTraceRepository(self._db).append(
            self._mapping_trace(decision=decision, correlation_id=correlation_id)
        )
        return decision

    async def _form_candidate(
        self,
        *,
        goal_id: UUID,
        version: int,
        user: User,
        intent: str,
        source_document_ids: tuple[UUID, ...],
        created_at: datetime,
        application_context: str | None,
        deadline_at: datetime | None,
        weekly_time_budget_minutes: int | None,
        supersedes_version: int | None = None,
    ) -> LearningGoalV1:
        normalized_intent = " ".join(intent.split())
        if not normalized_intent:
            raise ValueError("LEARNING_GOAL_INTENT_EMPTY")
        proposal: dict[str, object] = {}
        inference_refs: tuple[UUID, ...] = ()
        reasons = ["GOAL_FORMATION_DETERMINISTIC_FALLBACK"]
        if self._model_port is not None:
            inference = await self._run_model_candidate(
                goal_id=goal_id,
                intent=normalized_intent,
                source_document_ids=source_document_ids,
                created_at=created_at,
            )
            inference = await self._repo.save_inference(inference)
            inference_refs = (inference.inference_id,)
            reasons.extend(inference.reason_codes)
            if inference.status == "succeeded" and inference.structured_result:
                proposal = inference.structured_result
                reasons.append("GOAL_MODEL_CANDIDATE_BOUNDED_AND_PERSISTED")

        topic = self._bounded_text(
            proposal.get("topic"),
            fallback=self._topic_from_intent(normalized_intent),
            limit=200,
        )
        title = self._bounded_text(proposal.get("title"), fallback=f"学习：{topic}", limit=200)
        capabilities = self._bounded_strings(proposal.get("target_capabilities"), limit=5)
        if not capabilities:
            capabilities = (f"解释并应用 {topic}",)
        success_criteria = self._bounded_strings(proposal.get("success_criteria"), limit=5)
        if not success_criteria or all(
            any(marker in item.casefold() for marker in ("了解", "熟悉", "看完", "understand"))
            for item in success_criteria
        ):
            criterion, criterion_reasons = measurable_success_criterion(topic, normalized_intent)
            success_criteria = (criterion,)
            reasons.extend(criterion_reasons)
        if proposal.get("source_document_ids") is not None:
            reasons.append("GOAL_MODEL_SOURCE_SCOPE_IGNORED")
        return LearningGoalV1(
            goal_id=goal_id,
            version=version,
            user_id=canonical_user_id(user.id),
            title=title,
            topic=topic,
            target_capabilities=capabilities,
            application_context=application_context,
            success_criteria=success_criteria,
            source_document_ids=tuple(sorted(set(source_document_ids), key=str)),
            deadline_at=deadline_at,
            weekly_time_budget_minutes=weekly_time_budget_minutes,
            status="candidate",
            confirmed_by_user=False,
            created_at=created_at,
            supersedes_version=supersedes_version,
            model_inference_refs=inference_refs,
            reason_codes=tuple(dict.fromkeys(reasons)),
        )

    async def _run_model_candidate(
        self,
        *,
        goal_id: UUID,
        intent: str,
        source_document_ids: tuple[UUID, ...],
        created_at: datetime,
    ) -> GoalFormationInferenceV1:
        digest = hashlib.sha256(
            json.dumps(
                {
                    "intent": intent,
                    "source_document_ids": sorted(str(item) for item in source_document_ids),
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        inference_id = uuid5(
            goal_id,
            f"goal-formation:{digest}:{GOAL_FORMATION_PROMPT_VERSION}",
        )
        assert self._model_port is not None
        try:
            result = await self._model_port.form_goal_candidate(
                intent=intent,
                source_document_ids=source_document_ids,
                prompt_version=GOAL_FORMATION_PROMPT_VERSION,
                output_schema_version=GOAL_FORMATION_OUTPUT_SCHEMA_VERSION,
            )
        except Exception:
            return GoalFormationInferenceV1(
                inference_id=inference_id,
                goal_id=goal_id,
                input_digest=digest,
                prompt_version=GOAL_FORMATION_PROMPT_VERSION,
                output_schema_version=GOAL_FORMATION_OUTPUT_SCHEMA_VERSION,
                status="unavailable",
                reason_codes=("MAPPING_MODEL_UNAVAILABLE",),
                created_at=created_at,
            )
        if not isinstance(result.structured_result, dict):
            return GoalFormationInferenceV1(
                inference_id=inference_id,
                goal_id=goal_id,
                input_digest=digest,
                provider=result.provider,
                model_name=result.model_name,
                model_snapshot=result.model_snapshot,
                prompt_version=GOAL_FORMATION_PROMPT_VERSION,
                output_schema_version=GOAL_FORMATION_OUTPUT_SCHEMA_VERSION,
                status="invalid",
                reason_codes=("GOAL_MODEL_OUTPUT_INVALID",),
                created_at=created_at,
            )
        return GoalFormationInferenceV1(
            inference_id=inference_id,
            goal_id=goal_id,
            input_digest=digest,
            provider=result.provider,
            model_name=result.model_name,
            model_snapshot=result.model_snapshot,
            prompt_version=GOAL_FORMATION_PROMPT_VERSION,
            output_schema_version=GOAL_FORMATION_OUTPUT_SCHEMA_VERSION,
            structured_result=result.structured_result,
            status="succeeded",
            reason_codes=("GOAL_MODEL_OUTPUT_SCHEMA_ACCEPTED_AS_CANDIDATE",),
            created_at=created_at,
        )

    async def _semantic_scores(self, goal: LearningGoalV1, scope) -> dict[UUID, float]:
        allowed = {item.knowledge_unit_id for item in scope.units}
        scores: dict[UUID, float] = {}
        for inference_id in goal.model_inference_refs:
            inference = await self._repo.get_inference(inference_id)
            if inference is None or not inference.structured_result:
                continue
            raw_scores = inference.structured_result.get("semantic_scores")
            if not isinstance(raw_scores, dict):
                continue
            for raw_id, raw_score in raw_scores.items():
                try:
                    unit_id = UUID(str(raw_id))
                    score = float(raw_score)
                except (TypeError, ValueError):
                    continue
                if unit_id in allowed and 0.0 <= score <= 1.0:
                    scores[unit_id] = score
        return scores

    async def _model_mapping_reasons(self, goal: LearningGoalV1) -> tuple[str, ...]:
        reasons: list[str] = []
        for inference_id in goal.model_inference_refs:
            inference = await self._repo.get_inference(inference_id)
            if inference is not None and inference.status != "succeeded":
                reasons.extend(inference.reason_codes)
        return tuple(dict.fromkeys(reasons))

    async def _append_goal_event(
        self,
        *,
        goal: LearningGoalV1,
        event_type: str,
        correlation_id: UUID,
        idempotency_key: str,
    ) -> None:
        event = LearningEventEnvelope(
            event_id=uuid5(goal.goal_id, f"{event_type}:v{goal.version}"),
            event_type=event_type,
            aggregate_type="LearningGoal",
            aggregate_id=goal.goal_id,
            aggregate_version=goal.version,
            sequence=goal.version,
            occurred_at=goal.confirmed_at or goal.created_at,
            recorded_at=goal.confirmed_at or goal.created_at,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
            actor=EventActor(actor_type="learner", actor_id=str(goal.user_id)),
            context=EventContext(
                user_id=goal.user_id,
                goal_id=goal.goal_id,
                knowledge_unit_ids=[],
                content_revision_ids=[],
            ),
            payload={
                "goal_ref": f"learning_goal:{goal.goal_id}:v{goal.version}",
                "status": goal.status,
                "confirmed_by_user": goal.confirmed_by_user,
                "source_document_ids": [str(item) for item in goal.source_document_ids],
                "reason_codes": list(goal.reason_codes),
            },
            provenance=EventProvenance(
                source="domain",
                algorithm_version="goal-formation-v1",
            ),
            trace=EventTrace(trace_id=f"learning-goal:{goal.goal_id}:v{goal.version}"),
            privacy=EventPrivacy(
                classification="personal",
                external_processing=bool(goal.model_inference_refs),
                retention_class="core_learning",
            ),
        )
        await LearningEventRepository(self._db).append(event)

    def _mapping_trace(
        self,
        *,
        decision: GoalMappingDecision,
        correlation_id: UUID,
    ) -> DecisionTrace:
        mapping = decision.mapping
        return DecisionTrace(
            decision_id=uuid5(
                mapping.mapping_id,
                f"goal-mapping-decision:v{mapping.mapping_version}",
            ),
            decision_type="goal_knowledge_mapping",
            owner_system="learning_planner",
            inputs=[
                DecisionInput(
                    entity_type="LearningGoal",
                    entity_id=mapping.goal_id,
                    version=mapping.goal_version,
                ),
                *[
                    self._knowledge_graph_snapshot_input(value)
                    for value in mapping.knowledge_graph_versions
                ],
            ],
            candidates=[item.model_dump(mode="json") for item in mapping.target_evidence],
            selected={
                "mapping_ref": f"goal_knowledge_mapping:{mapping.mapping_id}:v{mapping.mapping_version}",
                "target_ids": [str(item) for item in mapping.selected_target_ids],
                "status": mapping.status,
            },
            constraints=[
                {
                    "constraint": "hard_source_scope",
                    "passed": not any(
                        code in mapping.reason_codes
                        for code in (
                            "SOURCE_SCOPE_EMPTY",
                            "SOURCE_SCOPE_UNAUTHORIZED_OR_UNAVAILABLE",
                        )
                    ),
                },
                {
                    "constraint": "published_knowledge_only",
                    "passed": "CONTENT_MODEL_INCOMPLETE" not in mapping.reason_codes,
                },
            ],
            reason_codes=list(mapping.reason_codes),
            confidence=mapping.confidence,
            algorithm=DecisionAlgorithm(
                algorithm_id="goal_knowledge_mapper",
                algorithm_version=mapping.mapper_version,
                model_inference_ids=list(mapping.model_inference_refs),
                prompt_versions=(
                    [GOAL_FORMATION_PROMPT_VERSION] if mapping.model_inference_refs else []
                ),
            ),
            experiment=DecisionExperiment(),
            created_at=mapping.created_at,
            correlation_id=correlation_id,
            trace_id=f"goal-mapping:{mapping.mapping_id}:v{mapping.mapping_version}",
        )

    @staticmethod
    def _knowledge_graph_snapshot_input(value: str) -> DecisionInput:
        parts = value.split(":")
        if len(parts) != 6 or parts[0::2] != ["document", "revision", "publication"]:
            raise ValueError("GOAL_MAPPING_KNOWLEDGE_GRAPH_VERSION_INVALID")
        try:
            document_id, revision_id, publication_id = (
                UUID(parts[1]),
                UUID(parts[3]),
                UUID(parts[5]),
            )
        except ValueError as exc:
            raise ValueError("GOAL_MAPPING_KNOWLEDGE_GRAPH_VERSION_INVALID") from exc
        return DecisionInput(
            entity_type="KnowledgeGraphSnapshot",
            entity_id=document_id,
            version=f"revision:{revision_id}:publication:{publication_id}",
        )

    @staticmethod
    def _bounded_text(value: object, *, fallback: str, limit: int) -> str:
        if isinstance(value, str) and value.strip():
            return " ".join(value.split())[:limit]
        return fallback[:limit]

    @staticmethod
    def _bounded_strings(value: object, *, limit: int) -> tuple[str, ...]:
        if not isinstance(value, (list, tuple)):
            return ()
        return tuple(
            text
            for item in value[:limit]
            if isinstance(item, str) and (text := " ".join(item.split())[:500])
        )

    @staticmethod
    def _topic_from_intent(intent: str) -> str:
        latin_topics = list(dict.fromkeys(re.findall(r"[A-Za-z][A-Za-z0-9_-]*", intent)))
        if latin_topics:
            return " ".join(latin_topics)[:200]
        topic = intent
        for marker in ("我想", "希望", "了解", "熟悉", "看完", "能够", "能", "学习", "掌握"):
            topic = topic.replace(marker, " ")
        topic = " ".join(topic.split()).strip("，。；、 ")
        return (topic or intent)[:200]

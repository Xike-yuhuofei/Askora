"""Derived, current-user-scoped BookLearningReadiness read model."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.adaptive import VersionedRef
from app.contracts.book_learning import (
    BookLearningOwnerRefV1,
    BookLearningReadinessV1,
)
from app.contracts.learning import LearningActivity, LearningPlan
from app.contracts.planning import (
    DiagnosticNeedV1,
    GoalKnowledgeMappingV1,
    GoalSpecificKnowledgeSubgraphV1,
    LearningGoalV1,
)
from app.domains.content_knowledge import CONTENT_RECORD_KEY
from app.models.assessment import LearnerStateRecord
from app.models.document import ModerationStatus, ProcessingStatus, UserDocument
from app.models.ledger import LearningEventRecord
from app.models.planning import (
    DiagnosticNeedRecord,
    GoalKnowledgeMappingRecord,
    GoalKnowledgeSubgraphRecord,
    LearningActivityRecord,
    LearningGoalRecord,
    LearningPlanRecord,
)
from app.models.user import User
from app.queries.goal_knowledge import GoalKnowledgeQueryService


class BookLearningReadinessQuery:
    """Composes exact owner refs; it persists no bootstrap session state."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(
        self,
        *,
        user: User,
        document_id: UUID,
        correlation_id: str,
        generated_at: datetime | None = None,
    ) -> BookLearningReadinessV1:
        now = generated_at or datetime.now(timezone.utc)
        document = await self._session.scalar(
            select(UserDocument).where(
                UserDocument.id == str(document_id),
                UserDocument.pseudonym_id == user.pseudonym_id,
                UserDocument.is_deleted.is_(False),
            )
        )
        if document is None:
            return self._result(
                document_id=document_id,
                state="BLOCKED",
                refs=(),
                reasons=("BOOK_SOURCE_NOT_FOUND_OR_UNAUTHORIZED",),
                commands=(),
                now=now,
                correlation_id=correlation_id,
            )

        document_ref = BookLearningOwnerRefV1(
            owner_system="SYS01",
            ref=VersionedRef(
                entity_type="SourceDocument",
                entity_id=document.id,
                version=str(document.updated_at.isoformat()),
            ),
            status=document.processing_status,
        )
        if document.processing_status in {
            ProcessingStatus.PENDING,
            ProcessingStatus.PROCESSING,
        }:
            return self._result(
                document_id=document_id,
                state="PROCESSING",
                refs=(document_ref,),
                reasons=("CONTENT_PROCESSING_IN_PROGRESS",),
                commands=(),
                now=now,
                correlation_id=correlation_id,
            )
        if (
            document.processing_status
            in {
                ProcessingStatus.FAILED,
                ProcessingStatus.REJECTED,
                ProcessingStatus.QUARANTINED,
            }
            or document.moderation_status != ModerationStatus.APPROVED
        ):
            return self._result(
                document_id=document_id,
                state="BLOCKED",
                refs=(document_ref,),
                reasons=("CONTENT_NOT_APPROVED_FOR_LEARNING",),
                commands=(),
                now=now,
                correlation_id=correlation_id,
            )

        revision, content_refs, content_reasons = self._content_readiness(document)
        refs = (document_ref, *content_refs)
        if revision is None or content_reasons:
            return self._result(
                document_id=document_id,
                state="CONTENT_PARTIAL",
                refs=refs,
                reasons=content_reasons or ("CONTENT_MODEL_PARTIAL",),
                commands=(),
                now=now,
                correlation_id=correlation_id,
            )

        goal = await self._latest_goal_for_document(user_id=UUID(user.id), document_id=document_id)
        if goal is None:
            return self._result(
                document_id=document_id,
                state="READY_FOR_GOAL",
                refs=refs,
                reasons=("PUBLISHED_CONTENT_READY_FOR_GOAL",),
                commands=("CreateLearningGoalCandidate",),
                now=now,
                correlation_id=correlation_id,
            )
        goal_ref = self._owner_ref(
            "SYS06", "LearningGoal", goal.goal_id, goal.version, goal.status, goal.reason_codes
        )
        refs = (*refs, goal_ref)
        if goal.status == "candidate":
            return self._result(
                document_id=document_id,
                state="GOAL_CONFIRMATION_REQUIRED",
                refs=refs,
                reasons=("LEARNING_GOAL_USER_CONFIRMATION_REQUIRED",),
                commands=("ConfirmLearningGoal",),
                now=now,
                correlation_id=correlation_id,
            )

        mapping = await self._latest_mapping(goal.goal_id)
        if mapping is None:
            return self._result(
                document_id=document_id,
                state="DIAGNOSIS_REQUIRED",
                refs=refs,
                reasons=("GOAL_KNOWLEDGE_MAPPING_REQUIRED",),
                commands=("MapGoalToKnowledge",),
                now=now,
                correlation_id=correlation_id,
            )
        mapping_ref = self._owner_ref(
            "SYS06",
            "GoalKnowledgeMapping",
            mapping.mapping_id,
            mapping.mapping_version,
            mapping.status,
            mapping.reason_codes,
        )
        refs = (*refs, mapping_ref)
        if mapping.status == "blocked":
            return self._result(
                document_id=document_id,
                state="BLOCKED",
                refs=refs,
                reasons=mapping.reason_codes,
                commands=("ReviseLearningGoalCandidate",),
                now=now,
                correlation_id=correlation_id,
            )
        current_scope = await GoalKnowledgeQueryService(self._session).load_scope(
            user=user,
            source_document_ids=goal.source_document_ids,
        )
        if (
            current_scope.missing_document_ids
            or current_scope.knowledge_graph_versions != mapping.knowledge_graph_versions
        ):
            return self._result(
                document_id=document_id,
                state="DIAGNOSIS_REQUIRED",
                refs=refs,
                reasons=("GOAL_KNOWLEDGE_MAPPING_STALE",),
                commands=("MapGoalToKnowledge",),
                now=now,
                correlation_id=correlation_id,
            )
        subgraph = await self._latest_subgraph(mapping.mapping_id)
        if subgraph is None:
            return self._result(
                document_id=document_id,
                state="DIAGNOSIS_REQUIRED",
                refs=refs,
                reasons=("GOAL_SUBGRAPH_REQUIRED",),
                commands=("BuildGoalKnowledgeSubgraph",),
                now=now,
                correlation_id=correlation_id,
            )
        refs = (
            *refs,
            self._owner_ref(
                "SYS06",
                "GoalSpecificKnowledgeSubgraph",
                subgraph.subgraph_id,
                subgraph.version,
                "ready",
                subgraph.reason_codes,
            ),
        )
        diagnostic = await self._latest_diagnostic(mapping.mapping_id, UUID(user.id))
        if diagnostic is None:
            return self._result(
                document_id=document_id,
                state="DIAGNOSIS_REQUIRED",
                refs=refs,
                reasons=("PREREQUISITE_DIAGNOSTIC_REQUIRED",),
                commands=("GeneratePrerequisiteDiagnosis",),
                now=now,
                correlation_id=correlation_id,
            )
        refs = (
            *refs,
            self._owner_ref(
                "SYS06",
                "DiagnosticNeed",
                diagnostic.need_id,
                diagnostic.version,
                diagnostic.status,
                diagnostic.reason_codes,
            ),
            BookLearningOwnerRefV1(
                owner_system="SYS03",
                ref=VersionedRef(
                    entity_type="LearnerState",
                    entity_id=str(uuid5(NAMESPACE_URL, f"askora:learner-state:{user.id}")),
                    version=diagnostic.created_from_learner_state_version,
                ),
                status="exact_input",
            ),
        )
        if diagnostic.status == "active":
            return self._result(
                document_id=document_id,
                state="DIAGNOSING",
                refs=refs,
                reasons=("DIAGNOSTIC_ACTIVITY_ACTIVE",),
                commands=("ContinuePrerequisiteDiagnosis",),
                now=now,
                correlation_id=correlation_id,
            )
        if diagnostic.status == "blocked" or diagnostic.stop_reason in {
            "NO_VALID_ASSESSMENT_ITEM",
            "LOW_CONFIDENCE_REQUIRES_REVIEW",
            "SYSTEM_BLOCKED",
            "USER_STOPPED",
        }:
            return self._result(
                document_id=document_id,
                state="BLOCKED",
                refs=refs,
                reasons=(diagnostic.stop_reason or "DIAGNOSTIC_BLOCKED",),
                commands=(),
                now=now,
                correlation_id=correlation_id,
            )

        plan = await self._latest_plan(goal.goal_id)
        if plan is None:
            return self._result(
                document_id=document_id,
                state="PLAN_READY",
                refs=refs,
                reasons=("DIAGNOSTIC_COMPLETE_PLAN_GENERATION_REQUIRED",),
                commands=("GenerateLearningPlan",),
                now=now,
                correlation_id=correlation_id,
            )
        activities = await self._activities(plan)
        refs = (
            *refs,
            self._owner_ref(
                "SYS06", "LearningPlan", plan.plan_id, plan.version, plan.status, plan.reason_codes
            ),
            *(
                self._owner_ref(
                    "SYS06",
                    "LearningActivity",
                    activity.activity_id,
                    activity.plan_version,
                    activity.status,
                    tuple(activity.reason_codes),
                )
                for activity in activities
            ),
        )
        if not activities:
            return self._result(
                document_id=document_id,
                state="BLOCKED",
                refs=refs,
                reasons=("PLAN_NO_FEASIBLE_ACTIVITY",),
                commands=(),
                now=now,
                correlation_id=correlation_id,
            )
        latest_learner_state_version = await self._session.scalar(
            select(LearnerStateRecord.version)
            .where(LearnerStateRecord.user_id == user.id)
            .order_by(LearnerStateRecord.version.desc())
            .limit(1)
        )
        if plan.knowledge_graph_version != ",".join(mapping.knowledge_graph_versions) or (
            latest_learner_state_version is not None
            and plan.created_from_learner_state_version != latest_learner_state_version
        ):
            return self._result(
                document_id=document_id,
                state="PLAN_READY",
                refs=refs,
                reasons=("LEARNING_PLAN_STALE",),
                commands=("GenerateLearningPlan",),
                now=now,
                correlation_id=correlation_id,
            )
        selected = await self._activity_selected(plan, UUID(user.id))
        return self._result(
            document_id=document_id,
            state="READY_TO_LEARN" if selected else "PLAN_READY",
            refs=refs,
            reasons=("LEARNING_ACTIVITY_SELECTED" if selected else "LEARNING_PLAN_READY",),
            commands=("StartCanonicalTeachingRound",)
            if selected
            else ("SelectNextLearningActivity",),
            now=now,
            correlation_id=correlation_id,
        )

    @staticmethod
    def _content_readiness(
        document: UserDocument,
    ) -> tuple[dict | None, tuple[BookLearningOwnerRefV1, ...], tuple[str, ...]]:
        record = (document.moderation_details or {}).get(CONTENT_RECORD_KEY, {})
        revision_id = record.get("current_revision_id")
        revision = next(
            (
                item
                for item in record.get("revisions", [])
                if item.get("revision_id") == revision_id
            ),
            None,
        )
        if revision is None:
            return None, (), ("MATERIAL_REVISION_MISSING",)
        revision_ref = BookLearningOwnerRefV1(
            owner_system="SYS01",
            ref=VersionedRef(
                entity_type="MaterialRevision",
                entity_id=str(revision_id),
                version=str(revision.get("parser_version", "unknown")),
            ),
            status="current",
        )
        published = [
            item
            for item in revision.get("knowledge_units", [])
            if item.get("status") == "published"
        ]
        eligible_chunks = [
            item
            for item in revision.get("retrieval_chunks", [])
            if item.get("canonical_retrieval_eligible") is True
        ]
        reasons: list[str] = []
        if not published:
            reasons.append("KNOWLEDGE_PUBLICATION_BLOCKED")
        if not eligible_chunks:
            reasons.append("RETRIEVAL_PROJECTION_MISSING")
        publication = revision.get("knowledge_publication_result", {})
        exact_refs: list[BookLearningOwnerRefV1] = [revision_ref]
        if publication.get("decision_id"):
            exact_refs.append(
                BookLearningOwnerRefV1(
                    owner_system="SYS01",
                    ref=VersionedRef(
                        entity_type="KnowledgePublicationResult",
                        entity_id=str(publication["decision_id"]),
                        version=str(publication.get("policy_version", "unknown")),
                    ),
                    status=str(publication.get("status", "recorded")),
                    reason_codes=tuple(publication.get("reason_codes", ())),
                )
            )
        exact_refs.extend(
            BookLearningOwnerRefV1(
                owner_system="SYS01",
                ref=VersionedRef(
                    entity_type="KnowledgeUnit",
                    entity_id=str(item["knowledge_unit_id"]),
                    version=int(item.get("revision", 1)),
                ),
                status="published",
            )
            for item in published
        )
        exact_refs.extend(
            BookLearningOwnerRefV1(
                owner_system="SYS02",
                ref=VersionedRef(
                    entity_type="RetrievalProjection",
                    entity_id=str(item["chunk_id"]),
                    version=str(item.get("projection_fingerprint", "unknown")),
                ),
                status="eligible",
            )
            for item in eligible_chunks
        )
        return revision, tuple(exact_refs), tuple(reasons)

    async def _latest_goal_for_document(
        self, *, user_id: UUID, document_id: UUID
    ) -> LearningGoalV1 | None:
        records = (
            await self._session.scalars(
                select(LearningGoalRecord)
                .where(LearningGoalRecord.user_id == str(user_id))
                .order_by(LearningGoalRecord.created_at.desc(), LearningGoalRecord.version.desc())
            )
        ).all()
        latest: dict[str, LearningGoalRecord] = {}
        for record in records:
            latest.setdefault(record.goal_id, record)
        goals = [LearningGoalV1.model_validate(item.payload) for item in latest.values()]
        return next(
            (item for item in goals if document_id in item.source_document_ids),
            None,
        )

    async def _latest_mapping(self, goal_id: UUID) -> GoalKnowledgeMappingV1 | None:
        record = await self._session.scalar(
            select(GoalKnowledgeMappingRecord)
            .where(GoalKnowledgeMappingRecord.goal_id == str(goal_id))
            .order_by(GoalKnowledgeMappingRecord.mapping_version.desc())
            .limit(1)
        )
        return GoalKnowledgeMappingV1.model_validate(record.payload) if record else None

    async def _latest_subgraph(self, mapping_id: UUID) -> GoalSpecificKnowledgeSubgraphV1 | None:
        record = await self._session.scalar(
            select(GoalKnowledgeSubgraphRecord)
            .where(GoalKnowledgeSubgraphRecord.mapping_id == str(mapping_id))
            .order_by(GoalKnowledgeSubgraphRecord.version.desc())
            .limit(1)
        )
        return GoalSpecificKnowledgeSubgraphV1.model_validate(record.payload) if record else None

    async def _latest_diagnostic(self, mapping_id: UUID, user_id: UUID) -> DiagnosticNeedV1 | None:
        record = await self._session.scalar(
            select(DiagnosticNeedRecord)
            .where(
                DiagnosticNeedRecord.goal_mapping_id == str(mapping_id),
                DiagnosticNeedRecord.user_id == str(user_id),
            )
            .order_by(DiagnosticNeedRecord.version.desc())
            .limit(1)
        )
        return DiagnosticNeedV1.model_validate(record.payload) if record else None

    async def _latest_plan(self, goal_id: UUID) -> LearningPlan | None:
        record = await self._session.scalar(
            select(LearningPlanRecord)
            .where(
                LearningPlanRecord.learning_goal_id == str(goal_id),
                LearningPlanRecord.status == "active",
            )
            .order_by(LearningPlanRecord.version.desc())
            .limit(1)
        )
        return LearningPlan.model_validate(record.payload) if record else None

    async def _activities(self, plan: LearningPlan) -> tuple[LearningActivity, ...]:
        records = (
            await self._session.scalars(
                select(LearningActivityRecord)
                .where(
                    LearningActivityRecord.plan_id == str(plan.plan_id),
                    LearningActivityRecord.plan_version == plan.version,
                )
                .order_by(LearningActivityRecord.priority.desc(), LearningActivityRecord.id)
            )
        ).all()
        return tuple(LearningActivity.model_validate(item.payload) for item in records)

    async def _activity_selected(self, plan: LearningPlan, user_id: UUID) -> bool:
        records = (
            await self._session.scalars(
                select(LearningEventRecord)
                .where(LearningEventRecord.event_type == "ActivitySelected")
                .order_by(LearningEventRecord.recorded_at.desc())
            )
        ).all()
        plan_ref = f"learning_plan:{plan.plan_id}:v{plan.version}"
        return any(
            str(item.context.get("user_id")) == str(user_id)
            and item.payload.get("plan_ref") == plan_ref
            for item in records
        )

    @staticmethod
    def _owner_ref(
        owner: Literal["SYS01", "SYS02", "SYS03", "SYS04", "SYS05", "SYS06", "SYS08"],
        entity_type: str,
        entity_id: UUID,
        version: str | int,
        status: str,
        reasons: tuple[str, ...] | list[str] = (),
    ) -> BookLearningOwnerRefV1:
        return BookLearningOwnerRefV1(
            owner_system=owner,
            ref=VersionedRef(entity_type=entity_type, entity_id=str(entity_id), version=version),
            status=status,
            reason_codes=tuple(reasons),
        )

    @staticmethod
    def _result(
        *,
        document_id: UUID,
        state: Literal[
            "PROCESSING",
            "CONTENT_PARTIAL",
            "READY_FOR_GOAL",
            "GOAL_CONFIRMATION_REQUIRED",
            "DIAGNOSIS_REQUIRED",
            "DIAGNOSING",
            "PLAN_READY",
            "READY_TO_LEARN",
            "BLOCKED",
        ],
        refs: tuple[BookLearningOwnerRefV1, ...],
        reasons: tuple[str, ...],
        commands: tuple[str, ...],
        now: datetime,
        correlation_id: str,
    ) -> BookLearningReadinessV1:
        return BookLearningReadinessV1(
            document_id=document_id,
            state=state,
            owner_refs=refs,
            reason_codes=tuple(reasons),
            next_commands=tuple(commands),
            generated_at=now,
            correlation_id=correlation_id,
        )

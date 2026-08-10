from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.contracts import (
    DecisionAlgorithm,
    DecisionExperiment,
    DecisionInput,
    DecisionTrace,
    EventActor,
    EventContext,
    EventPrivacy,
    EventProvenance,
    EventTrace,
    LearningEventEnvelope,
)
from app.contracts.assessment import AssessmentAttempt, AssessmentItemV1, AssistanceSnapshot
from app.contracts.learning import TeachingAction
from app.contracts.planning import ConfirmedLearningGoal
from app.core.database import Base
from app.domains.content_knowledge import CONTENT_RECORD_KEY
from app.domains.learner_model import WeightedBKTProjector
from app.domains.review_scheduler import observation_from_evidence
from app.engines import LearningFlowOrchestrator
from app.infrastructure.learning_records import LearnerModelRepository
from app.infrastructure.ledger import DecisionTraceRepository, LearningEventRepository
from app.infrastructure.outbox import OutboxProducer
from app.infrastructure.planning_records import LearningPlanRepository, ReviewScheduleRepository
from app.models.assessment import CanonicalAssessmentAttemptRecord, LearnerEvidenceRecord
from app.models.user import User
from app.orchestration.learning_facade import (
    CanonicalTurnRequest,
    LearningOrchestrationFacade,
)
from app.orchestration.review_planning import ReviewPlanningApplication
from app.services.assessment.canonical_service import CanonicalAssessmentService
from app.services.documents.document_service import DocumentService
from app.services.documents.rag_service import RAGService
from app.services.kt.canonical_projector import CanonicalLearnerProjectorService
from app.services.storage.local_storage import LocalFileStorage

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _teaching_action(activity_id: UUID) -> TeachingAction:
    return TeachingAction(
        action_id=uuid4(),
        learning_objective_id=uuid4(),
        learning_activity_id=activity_id,
        strategy_id="source-grounded-explain",
        strategy_version="1.0",
        action_type="explain",
        scaffold_level=1,
        hint_level=1,
        answer_exposure_max=1,
        evidence_requirements=["context"],
        expected_evidence_type="recall",
        success_condition={"deterministic_item_score": 1.0},
        failure_condition={"model_error": True},
        max_attempts=3,
        time_budget_seconds=600,
        reason_codes=["TEACH_SOURCE_GROUNDED_EXPLAIN"],
        policy_version="1.0",
        decision_id=uuid4(),
    )


def _event(
    *,
    event_type: str,
    aggregate_type: str,
    aggregate_id: UUID,
    user_id: UUID,
    knowledge_unit_id: UUID,
    correlation_id: UUID,
    trace_id: str,
    content_revision_id: UUID,
    payload: dict,
    attempt_id: UUID | None = None,
    provenance: EventProvenance | None = None,
) -> LearningEventEnvelope:
    now = datetime.now(timezone.utc)
    return LearningEventEnvelope(
        event_id=uuid4(),
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        aggregate_version=1,
        sequence=1,
        occurred_at=now,
        recorded_at=now,
        idempotency_key=f"e2e:{event_type}:{aggregate_id}",
        correlation_id=correlation_id,
        actor=EventActor(actor_type="learner", actor_id=str(user_id)),
        context=EventContext(
            user_id=user_id,
            knowledge_unit_ids=[knowledge_unit_id],
            assessment_attempt_id=attempt_id,
            content_revision_ids=[content_revision_id],
        ),
        payload=payload,
        provenance=provenance or EventProvenance(source="domain"),
        trace=EventTrace(trace_id=trace_id),
        privacy=EventPrivacy(
            classification="personal",
            external_processing=False,
            retention_class="core_learning",
        ),
    )


def _decision_trace(
    *,
    decision_id: UUID,
    owner_system: str,
    decision_type: str,
    input_id: UUID,
    correlation_id: UUID,
    trace_id: str,
    algorithm_id: str,
) -> DecisionTrace:
    return DecisionTrace(
        decision_id=decision_id,
        decision_type=decision_type,
        owner_system=owner_system,
        inputs=[DecisionInput(entity_type="LearningActivity", entity_id=input_id, version=1)],
        candidates=[{"candidate": "v0.2"}],
        selected={"selected": "v0.2"},
        constraints=[{"kind": "hard", "source_grounded": True}],
        reason_codes=["E2E_CANONICAL_DECISION"],
        algorithm=DecisionAlgorithm(
            algorithm_id=algorithm_id,
            algorithm_version="1.0",
            model_inference_ids=[],
            prompt_versions=[],
        ),
        experiment=DecisionExperiment(),
        created_at=datetime.now(timezone.utc),
        correlation_id=correlation_id,
        trace_id=trace_id,
    )


@pytest.mark.asyncio
async def test_v02_canonical_learning_loop_restart_replay_and_trace(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'v02-e2e.db'}"
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    correlation_id, user_id = uuid4(), uuid4()
    trace_id, workflow_run_id, model_inference_id = (
        f"trace-{uuid4()}",
        str(uuid4()),
        str(uuid4()),
    )

    async with factory() as session:
        user = User(id=str(user_id), pseudonym_id="v02-e2e-user")
        session.add(user)
        await session.commit()
        documents = DocumentService(session)
        documents.storage = LocalFileStorage(str(tmp_path / "documents"))
        document = await documents.upload_document(
            user.pseudonym_id,
            "water-loop.md",
            (FIXTURES / "malicious_document.md").read_bytes(),
            subject="science",
            knowledge_point_id="water-boiling-point",
        )
        await documents.process_document(document.id)
        await session.refresh(document)
        revision = document.moderation_details[CONTENT_RECORD_KEY]["revisions"][0]
        revision_id = UUID(revision["revision_id"])
        knowledge_unit_id = UUID(revision["knowledge_units"][0]["knowledge_unit_id"])
        span_id = UUID(revision["source_spans"][0]["span_id"])
        assert await documents.get_source_span(document.id, str(span_id)) is not None

        planning = ReviewPlanningApplication(
            ReviewScheduleRepository(session),
            LearningPlanRepository(session),
            OutboxProducer(session),
        )
        goal = ConfirmedLearningGoal(
            goal_id=uuid4(),
            objective_id=uuid4(),
            target_knowledge_unit_ids=[knowledge_unit_id],
            confirmed_at=datetime.now(timezone.utc),
        )
        initial_plan = await planning.generate_plan(
            goal=goal,
            user_id=user_id,
            prerequisites={},
            mastery={knowledge_unit_id: None},
            time_budget_minutes=30,
            learner_state_version=0,
            knowledge_graph_version="content-revision/1.0",
            at=datetime.now(timezone.utc),
            idempotency_key="e2e-initial-plan",
            correlation_id=str(correlation_id),
        )
        initial_activities = await LearningPlanRepository(session).activities(
            plan_id=initial_plan.plan_id, plan_version=initial_plan.version
        )
        action = _teaching_action(initial_activities[0].activity_id)
        action_before = action.model_dump()
        bundle_result = await RAGService(session).build_evidence_bundle(
            workspace_id=document.workspace_id,
            pseudonym_id=user.pseudonym_id,
            query="标准大气压下水的沸点",
            teaching_action=action,
            source_scope={"document_ids": [document.id]},
        )
        bundle = bundle_result.bundle
        assert bundle.items
        assert all(item.allowed_use == "learner_visible" for item in bundle.items)
        assert all("[grader-only]" not in item.content for item in bundle.items)
        assert action.model_dump() == action_before

        decisions = DecisionTraceRepository(session)
        await decisions.append(
            _decision_trace(
                decision_id=action.decision_id,
                owner_system="teaching_policy",
                decision_type="TeachingActionSelected",
                input_id=initial_activities[0].activity_id,
                correlation_id=correlation_id,
                trace_id=trace_id,
                algorithm_id="teaching-policy",
            )
        )
        await decisions.append(
            _decision_trace(
                decision_id=bundle.retrieval_trace_id,
                owner_system="retrieval",
                decision_type="EvidenceBundleSelected",
                input_id=action.action_id,
                correlation_id=correlation_id,
                trace_id=trace_id,
                algorithm_id="hybrid-rrf",
            )
        )

        teaching = await LearningOrchestrationFacade(LearningFlowOrchestrator()).run_turn(
            CanonicalTurnRequest(
                session_id=str(uuid4()),
                user_id=str(user_id),
                text="请根据我的资料讲解水的沸点。",
                turn_id=str(uuid4()),
                subject="science",
                knowledge_point_id="water-boiling-point",
                correlation_id=str(correlation_id),
                workflow_run_id=workflow_run_id,
                model_inference_id=model_inference_id,
                teaching_action=action,
                evidence_bundle=bundle,
            )
        )
        assert teaching.reply_text
        assert teaching.engine_id == "explain"
        assert teaching.engine_debug["prompt_version"] == "explain-evidence/1.0"
        model_event = _event(
            event_type="ModelInferenceCompleted",
            aggregate_type="ModelInference",
            aggregate_id=UUID(model_inference_id),
            user_id=user_id,
            knowledge_unit_id=knowledge_unit_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            content_revision_id=revision_id,
            payload={
                "workflow_run_id": workflow_run_id,
                "teaching_action_id": str(action.action_id),
                "evidence_bundle_id": str(bundle.bundle_id),
                "response_length": len(teaching.reply_text),
            },
            provenance=EventProvenance(
                source="orchestrator",
                model_provider=teaching.engine_debug["provider"],
                model_name=teaching.engine_debug["model"],
                prompt_id="explain-evidence",
                prompt_version=teaching.engine_debug["prompt_version"],
            ),
        )
        await LearningEventRepository(session).append(model_event)

        item = AssessmentItemV1(
            item_id=uuid4(),
            version="1.0",
            knowledge_unit_id=knowledge_unit_id,
            item_type="exact",
            prompt="标准大气压下纯水的沸点（摄氏度）？",
            answer_key="100",
            difficulty=0.2,
        )
        variants = [
            (
                "independent",
                AssistanceSnapshot(
                    hint_level=0,
                    assistance_class="none",
                    source_visible=False,
                    answer_visible=False,
                    response_revision=1,
                    response_time_ms=900,
                ),
            ),
            (
                "assisted",
                AssistanceSnapshot(
                    hint_level=2,
                    assistance_class="hint",
                    source_visible=True,
                    answer_visible=False,
                    response_revision=1,
                    response_time_ms=1100,
                ),
            ),
            (
                "answer_exposed",
                AssistanceSnapshot(
                    hint_level=4,
                    assistance_class="full_solution",
                    source_visible=True,
                    answer_visible=True,
                    response_revision=1,
                    response_time_ms=500,
                ),
            ),
        ]
        projected = []
        assessment_service = CanonicalAssessmentService(session)
        learner_service = CanonicalLearnerProjectorService(session)
        for index, (expected_independence, assistance) in enumerate(variants, start=1):
            key = f"e2e-attempt-{index}"
            result = await assessment_service.score_submission(
                item=item,
                user_id=user_id,
                response="100",
                assistance=assistance,
                idempotency_key=key,
                correlation_id=str(correlation_id),
            )
            duplicate = await assessment_service.score_submission(
                item=item,
                user_id=user_id,
                response="100",
                assistance=assistance,
                idempotency_key=key,
                correlation_id=str(correlation_id),
            )
            assert duplicate.result_id == result.result_id
            assert result.independence == expected_independence
            task_event = _event(
                event_type="AttemptScored",
                aggregate_type="Attempt",
                aggregate_id=result.attempt_id,
                user_id=user_id,
                knowledge_unit_id=knowledge_unit_id,
                correlation_id=correlation_id,
                trace_id=trace_id,
                content_revision_id=revision_id,
                attempt_id=result.attempt_id,
                payload={"result_id": str(result.result_id), "independence": result.independence},
            )
            await LearningEventRepository(session).append(task_event)
            attempt_record = await session.get(
                CanonicalAssessmentAttemptRecord, str(result.attempt_id)
            )
            assert attempt_record is not None
            estimate = await learner_service.project_assessment(
                result=result,
                attempt=AssessmentAttempt.model_validate(attempt_record.payload),
                knowledge_unit_id=knowledge_unit_id,
                source_event_ids=[task_event.event_id],
                correlation_id=str(correlation_id),
            )
            projected.append(estimate)

        attempts = await session.scalar(
            select(func.count()).select_from(CanonicalAssessmentAttemptRecord)
        )
        evidence_rows = (
            await session.scalars(
                select(LearnerEvidenceRecord).order_by(LearnerEvidenceRecord.created_at)
            )
        ).all()
        assert attempts == 3
        weights = [row.payload["evidence_weight"] for row in evidence_rows]
        assert weights[0] > weights[1] > weights[2]
        assert weights[2] == 0.0
        assert all(estimate is not None for estimate in projected)

        independent_evidence = await LearnerModelRepository(session).list_evidence(
            user_id=user_id, knowledge_unit_id=knowledge_unit_id
        )
        review_schedule = await planning.apply_review_observation(
            observation_from_evidence(independent_evidence[0]),
            correlation_id=str(correlation_id),
        )
        future_plan = await planning.generate_plan(
            goal=goal,
            user_id=user_id,
            prerequisites={},
            mastery={knowledge_unit_id: projected[-1].competence_probability},
            time_budget_minutes=30,
            learner_state_version=projected[-1].version,
            knowledge_graph_version="content-revision/1.0",
            at=review_schedule.next_due_at + timedelta(days=2),
            idempotency_key="e2e-future-plan",
            reason_codes=["PLAN_REVIEW_DUE"],
            correlation_id=str(correlation_id),
        )
        future_activities = await LearningPlanRepository(session).activities(
            plan_id=future_plan.plan_id, plan_version=future_plan.version
        )
        assert "delayed_review" in [activity.type for activity in future_activities]
        await session.commit()

    await engine.dispose()
    restarted = create_async_engine(database_url)
    restarted_factory = async_sessionmaker(restarted, expire_on_commit=False)
    async with restarted_factory() as session:
        learner_records = LearnerModelRepository(session)
        evidence = await learner_records.list_evidence(
            user_id=user_id, knowledge_unit_id=knowledge_unit_id
        )
        latest = await learner_records.latest_mastery(
            user_id=user_id, knowledge_unit_id=knowledge_unit_id
        )
        assert latest is not None
        replayed = WeightedBKTProjector().project(
            user_id=user_id,
            knowledge_unit_id=knowledge_unit_id,
            evidence=evidence,
            version=latest.version,
        )
        assert replayed == latest
        assert (
            await ReviewScheduleRepository(session).latest(
                user_id=user_id, knowledge_unit_id=knowledge_unit_id
            )
            == review_schedule
        )
        assert len(await LearningPlanRepository(session).list_versions(goal.goal_id)) == 2
        assert len(await LearningEventRepository(session).query(correlation_id=correlation_id)) == 4
        assert len(await DecisionTraceRepository(session).query(correlation_id=correlation_id)) == 2
    await restarted.dispose()

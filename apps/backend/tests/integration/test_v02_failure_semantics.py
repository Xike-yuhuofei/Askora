from __future__ import annotations

from uuid import uuid4

import pytest

from app.contracts.learning import EvidenceBundle, TeachingAction
from app.engines import FlowStage, LearnerTurn, LearningFlowOrchestrator, SharedContext
from app.engines.explain_engine import ExplainEngine
from app.engines.quiz_engine import QuizEngine
from app.orchestration.learning_facade import CanonicalTurnRequest, LearningOrchestrationFacade
from app.services.llm.model_router import LLMResponse


def _action() -> TeachingAction:
    return TeachingAction(
        action_id=uuid4(),
        learning_objective_id=uuid4(),
        learning_activity_id=uuid4(),
        strategy_id="source-required",
        strategy_version="1.0",
        action_type="explain",
        scaffold_level=1,
        hint_level=1,
        answer_exposure_max=0,
        evidence_requirements=["definition"],
        expected_evidence_type="recall",
        success_condition={"grounded": True},
        failure_condition={"missing": True},
        max_attempts=1,
        time_budget_seconds=120,
        reason_codes=["SOURCE_REQUIRED"],
        policy_version="1.0",
        decision_id=uuid4(),
    )


class _NeverCalledProvider:
    async def chat_completion(self, _messages):
        raise AssertionError("model must not be called when required evidence is missing")


class _Router:
    def route_for_subject(self, _subject):
        return _NeverCalledProvider()


@pytest.mark.asyncio
async def test_retrieval_missing_returns_bounded_error_without_model_fabrication() -> None:
    action = _action()
    missing = EvidenceBundle(
        bundle_id=uuid4(),
        request_id=uuid4(),
        teaching_action_id=action.action_id,
        source_scope={"document_ids": []},
        index_versions={"content": "none"},
        items=[],
        conflicts=[],
        missing_roles=["definition"],
        retrieval_trace_id=uuid4(),
    )
    orchestrator = LearningFlowOrchestrator()
    explain = ExplainEngine()
    explain._model_router = _Router()
    orchestrator._engine_instances["explain"] = explain
    result = await LearningOrchestrationFacade(orchestrator).run_turn(
        CanonicalTurnRequest(
            session_id=str(uuid4()),
            user_id=str(uuid4()),
            text="请按资料解释",
            turn_id=str(uuid4()),
            subject="science",
            knowledge_point_id="missing",
            teaching_action=action,
            evidence_bundle=missing,
        )
    )
    assert result.engine_debug["error_code"] == "RETRIEVAL_EVIDENCE_MISSING"
    assert "不会补造" in result.reply_text


class _TimeoutProvider:
    async def chat_completion(self, _messages):
        raise TimeoutError("provider timeout")


class _TimeoutRouter:
    def route_for_subject(self, _subject):
        return _TimeoutProvider()


@pytest.mark.asyncio
async def test_model_timeout_returns_explicit_fallback_not_learner_failure() -> None:
    orchestrator = LearningFlowOrchestrator()
    explain = ExplainEngine()
    explain._model_router = _TimeoutRouter()
    orchestrator._engine_instances["explain"] = explain
    result = await LearningOrchestrationFacade(orchestrator).run_turn(
        CanonicalTurnRequest(
            session_id=str(uuid4()),
            user_id=str(uuid4()),
            text="请解释",
            turn_id=str(uuid4()),
            subject="science",
        )
    )
    assert result.engine_debug["fallback_reason"] == "TimeoutError"
    assert "mastery" not in result.engine_debug


class _InvalidStructuredProvider:
    async def chat_completion(self, _messages):
        return LLMResponse(
            content="not valid structured JSON",
            model="invalid-structured-model",
            provider="test-provider",
        )


class _InvalidStructuredRouter:
    def route_for_subject(self, _subject):
        return _InvalidStructuredProvider()


@pytest.mark.asyncio
async def test_invalid_structured_model_output_has_explicit_quiz_fallback() -> None:
    engine = QuizEngine()
    engine._model_router = _InvalidStructuredRouter()
    shared = SharedContext(subject="science", knowledge_point_id="water")
    result = await engine.step(
        LearnerTurn(text="开始测验", turn_id=str(uuid4())),
        FlowStage.VALIDATE,
        shared,
        engine.build_initial_state(shared),
    )
    assert result.engine_debug_info["fallback"] is True
    assert result.side_effects.extra["quiz_question_generation_failed"] is True
    assert result.side_effects.mastery_updates == {}

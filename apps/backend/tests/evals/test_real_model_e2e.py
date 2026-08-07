from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.contracts.learning import EvidenceBundle, EvidenceItem, TeachingAction
from app.core.config import LLMProvider, Settings, settings
from app.engines import LearningFlowOrchestrator
from app.orchestration.learning_facade import CanonicalTurnRequest, LearningOrchestrationFacade
from app.services.llm import model_router as router_module


def _configured_model() -> tuple[Settings, LLMProvider, str, str]:
    configured = Settings(_env_file=".env", _env_ignore_empty=True)
    if configured.llm_qwen_api_key:
        return configured, LLMProvider.QWEN, configured.llm_qwen_model, "science"
    if configured.llm_deepseek_api_key:
        return configured, LLMProvider.DEEPSEEK, configured.llm_deepseek_model, "math"
    if configured.llm_doubao_api_key:
        return configured, LLMProvider.DOUBAO, configured.llm_doubao_model, "science"
    pytest.fail("ASKORA_RUN_REAL_MODEL=1 but no configured real model credential was found")


@pytest.mark.asyncio
async def test_real_configured_model_through_canonical_orchestrator() -> None:
    if os.getenv("ASKORA_RUN_REAL_MODEL") != "1":
        pytest.skip("real model gate runs separately with ASKORA_RUN_REAL_MODEL=1")
    configured, provider_name, model_name, subject = _configured_model()
    original = settings.model_dump()
    settings.llm_default_provider = provider_name
    settings.llm_qwen_api_key = configured.llm_qwen_api_key
    settings.llm_deepseek_api_key = configured.llm_deepseek_api_key
    settings.llm_doubao_api_key = configured.llm_doubao_api_key
    settings.llm_qwen_model = configured.llm_qwen_model
    settings.llm_deepseek_model = configured.llm_deepseek_model
    settings.llm_doubao_model = configured.llm_doubao_model
    settings.llm_timeout = max(configured.llm_timeout, 60)
    router_module._model_router = None

    action = TeachingAction(
        action_id=uuid4(),
        learning_objective_id=uuid4(),
        learning_activity_id=uuid4(),
        strategy_id="real-model-source-explain",
        strategy_version="1.0",
        action_type="explain",
        scaffold_level=1,
        hint_level=1,
        answer_exposure_max=1,
        evidence_requirements=["context"],
        expected_evidence_type="explanation",
        success_condition={"response": "nonempty"},
        failure_condition={"provider": "unavailable"},
        max_attempts=1,
        time_budget_seconds=180,
        reason_codes=["REAL_MODEL_GATE"],
        policy_version="1.0",
        decision_id=uuid4(),
    )
    bundle = EvidenceBundle(
        bundle_id=uuid4(),
        request_id=uuid4(),
        teaching_action_id=action.action_id,
        source_scope={"fixture": "real-model-gate"},
        index_versions={"content": "1.0"},
        items=[
            EvidenceItem(
                evidence_id=uuid4(),
                source_span_ids=[uuid4()],
                knowledge_unit_ids=[uuid4()],
                pedagogical_role="context",
                content="纯水在标准大气压下的沸点是 100 摄氏度。",
                exposure_level=1,
                allowed_use="learner_visible",
            )
        ],
        conflicts=[],
        missing_roles=[],
        retrieval_trace_id=uuid4(),
    )
    try:
        result = await LearningOrchestrationFacade(LearningFlowOrchestrator()).run_turn(
            CanonicalTurnRequest(
                session_id=str(uuid4()),
                user_id=str(uuid4()),
                text="请用一个生活类比解释这条资料事实。",
                turn_id=str(uuid4()),
                subject=subject,
                knowledge_point_id="water-boiling-point",
                correlation_id=str(uuid4()),
                workflow_run_id=str(uuid4()),
                model_inference_id=str(uuid4()),
                teaching_action=action,
                evidence_bundle=bundle,
            )
        )
        assert result.reply_text.strip()
        assert result.engine_debug["provider"] == provider_name.value
        assert result.engine_debug["model"] == model_name
        assert "mock" not in result.engine_debug["model"].lower()
        assert result.engine_debug["prompt_version"] == "explain-evidence/1.0"
        summary = {
            "provider": result.engine_debug["provider"],
            "model": result.engine_debug["model"],
            "prompt_version": result.engine_debug["prompt_version"],
            "result": "success",
            "response_length": len(result.reply_text),
            "latency_ms": result.engine_debug["generation_ms"],
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        print("REAL_MODEL_RESULT " + json.dumps(summary, ensure_ascii=False))
    finally:
        active_router = router_module._model_router
        if active_router is not None:
            await active_router.close()
        for key, value in original.items():
            setattr(settings, key, value)
        router_module._model_router = None

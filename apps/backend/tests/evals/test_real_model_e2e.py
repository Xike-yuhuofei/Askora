from __future__ import annotations

import json
import os
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import NAMESPACE_URL, uuid5

import pytest

from app.contracts.adaptive import (
    AnswerExposure,
    AssistanceState,
    HintSpecificity,
    ScaffoldControl,
    ValidationObligation,
    VersionedRef,
)
from app.core.config import LLMProvider, Settings, settings
from app.domains.assessment import AdaptiveAssessmentService
from app.domains.learner_model import (
    AdaptiveEvidenceEligibility,
    AdaptiveEvidenceEligibilityProfile,
)
from app.domains.teaching_policy.kernel import TeachingPolicyKernel
from app.orchestration.adaptive_execution import AdaptiveRenderRequest, RenderProposal
from app.orchestration.learning_facade import LearningOrchestrationFacade
from app.services.llm import model_router as router_module
from app.services.llm.model_router import BaseLLMProvider, ChatMessage
from tests.fixtures.v03_execution_factory import adaptive_request, make_candidate
from tests.fixtures.v03_policy_factory import (
    NOW,
    fixed_uuid,
    load_profile,
    make_bundle,
    make_context,
    ref,
    with_previous_action,
)

PROMPT_VERSION = "v03-policy-bound-render/1.0"


def _configured_model() -> tuple[Settings, LLMProvider, str, str]:
    configured = Settings(_env_file=".env", _env_ignore_empty=True)  # type: ignore[call-arg]
    if configured.llm_qwen_api_key:
        return configured, LLMProvider.QWEN, configured.llm_qwen_model, "science"
    if configured.llm_deepseek_api_key:
        return configured, LLMProvider.DEEPSEEK, configured.llm_deepseek_model, "math"
    if configured.llm_doubao_api_key:
        return configured, LLMProvider.DOUBAO, configured.llm_doubao_model, "science"
    pytest.fail("ASKORA_RUN_REAL_MODEL=1 but no configured real model credential was found")


class _ConfiguredAdaptiveRenderer:
    """Test-only real provider adapter; SYS08 remains the output-policy authority."""

    def __init__(self, provider: BaseLLMProvider) -> None:
        self._provider = provider
        self.provider = ""
        self.model = ""
        self.latency_ms = 0

    async def render(self, request: AdaptiveRenderRequest) -> RenderProposal:
        evidence = "\n".join(item.content for item in request.evidence_bundle.items)
        response = await self._provider.chat_completion(
            [
                ChatMessage(
                    role="system",
                    content=(
                        "你只负责执行已确定的教学动作，不得选择或改变教学策略。"
                        "只能依据给定资料做简短解释，不调用工具，不直接给出任何测验答案。"
                    ),
                ),
                ChatMessage(
                    role="user",
                    content=(
                        f"教学策略：{request.teaching_action.strategy_family.value}\n"
                        f"允许动作：{','.join(move.value for move in request.teaching_action.interaction_moves)}\n"
                        f"资料：{evidence}\n"
                        f"学习者请求：{request.user_text}"
                    ),
                ),
            ],
            temperature=0.1,
            max_tokens=256,
        )
        self.provider = response.provider
        self.model = response.model
        self.latency_ms = response.latency_ms
        used_ids = tuple(item.evidence_id for item in request.evidence_bundle.items)
        return RenderProposal(
            response_id=uuid5(
                NAMESPACE_URL,
                f"askora:v03:real-render:{request.teaching_action.action_id}:{response.model}",
            ),
            response_version=PROMPT_VERSION,
            text=response.content.strip(),
            strategy_family=request.teaching_action.strategy_family,
            interaction_moves=request.teaching_action.interaction_moves,
            action_modifiers=request.teaching_action.action_modifiers,
            actual_scaffold_control=ScaffoldControl.LOW,
            actual_hint_specificity=HintSpecificity.CONCEPTUAL_STRATEGIC,
            actual_answer_exposure=AnswerExposure.NONE,
            declared_assistance_state=AssistanceState.ASSISTED,
            used_evidence_ids=used_ids,
        )


@pytest.mark.asyncio
async def test_real_configured_model_through_v03_canonical_adaptive_path() -> None:
    """VSLICE-364/EXEC013-AC-005: one real call under a fixed v0.3 envelope."""

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

    profile = load_profile()
    bundle = make_bundle(profile)
    context = make_context({"case_id": "real-model-v03", "mastery": 0.2})
    request = replace(
        adaptive_request(),
        text="请用生活中的例子解释分数为什么表示整体的一部分。",
        subject=subject,
        teaching_context_v03=context,
        policy_bundle_v03=bundle,
        policy_profile_v03=profile,
        adaptive_retrieval_candidates=(
            make_candidate(
                "real-model-v03",
                exposure=AnswerExposure.NONE,
                content="分数表示把一个整体平均分成若干份后取其中若干份。",
            ),
        ),
    )
    router = router_module.get_model_router()
    renderer = _ConfiguredAdaptiveRenderer(router.route_for_subject(subject))
    try:
        turn = await LearningOrchestrationFacade(adaptive_renderer=renderer).run_turn(request)
        assert turn.reply_text.strip()
        assert turn.teaching_action_v03 is not None
        assert turn.decision_trace_v03 is not None
        assert turn.evidence_bundle_v03 is not None
        assert turn.adaptive_execution_v03 is not None
        assert turn.decision_trace_v03.action_propensity is None
        assert not turn.adaptive_execution_v03.fallback_used
        assert (
            turn.adaptive_execution_v03.actual_assistance.assistance_state
            is AssistanceState.ASSISTED
        )
        assert "mock" not in renderer.model.lower()
        assert renderer.provider == provider_name.value
        assert renderer.model == model_name

        action = turn.teaching_action_v03
        execution = turn.adaptive_execution_v03
        assessment = AdaptiveAssessmentService().assess_exact(
            user_id=fixed_uuid("real-model-user"),
            session_id=fixed_uuid("real-model-session"),
            item_id=fixed_uuid("real-model-item"),
            item_version="1",
            assessment_type="formative",
            response="4",
            expected_answer="4",
            teaching_action=action,
            actual_assistance=execution.actual_assistance,
            teaching_action_ref=execution.teaching_action_ref,
            rendered_response_ref=VersionedRef(
                entity_type="rendered_response",
                entity_id=str(execution.response_id),
                version=execution.response_version,
            ),
            started_at=NOW,
            submitted_at=NOW + timedelta(seconds=30),
            idempotency_key="v03-real-model-assessment",
            assessment_confidence=0.95,
            diagnostic_confidence=0.2,
        )
        evidence = AdaptiveEvidenceEligibility().decide(
            result=assessment.result,
            attempt=assessment.attempt,
            actual_assistance=execution.actual_assistance,
            profile=AdaptiveEvidenceEligibilityProfile(
                profile_version="real-model-eligibility/1.0",
                minimum_assessment_confidence=0.5,
                independence_weights={
                    AssistanceState.INDEPENDENT: 1.0,
                    AssistanceState.ASSISTED: 0.35,
                    AssistanceState.ANSWER_EXPOSED: 0.0,
                },
                novelty_weights={"repeated": 0.5, "near_variant": 0.8, "far_variant": 1.0},
            ),
            knowledge_unit_id=fixed_uuid("knowledge-unit"),
            dimension="routine_application",
            novelty="near_variant",
            delay_seconds=0,
            source_event_refs=(ref("learning_event", "real-model-actual-assistance"),),
        )
        assert assessment.result.passed
        assert evidence.accepted
        assert evidence.evidence is not None
        assert evidence.evidence.assistance_state is AssistanceState.ASSISTED

        next_context = with_previous_action(
            make_context(
                {
                    "case_id": "real-model-next",
                    "mastery": 0.4,
                    "assisted_success": True,
                }
            ),
            action,
        )
        next_decision = TeachingPolicyKernel().decide(
            context=next_context,
            bundle=bundle,
            profile=profile,
        )
        assert (
            next_decision.action.validation_obligation
            is ValidationObligation.INDEPENDENT_VALIDATION_REQUIRED
        )

        summary = {
            "provider": renderer.provider,
            "model": renderer.model,
            "prompt_version": PROMPT_VERSION,
            "policy_bundle_version": bundle.policy_version,
            "result": "success",
            "response_length": len(turn.reply_text),
            "latency_ms": renderer.latency_ms,
            "teaching_action_id": str(action.action_id),
            "decision_id": str(action.decision_id),
            "actual_assistance": execution.actual_assistance.assistance_state.value,
            "assessment_result_id": str(assessment.result.result_id),
            "next_strategy_family": next_decision.action.strategy_family.value,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        print("REAL_MODEL_RESULT " + json.dumps(summary, ensure_ascii=False))
    finally:
        await router.close()
        for key, value in original.items():
            setattr(settings, key, value)
        router_module._model_router = None

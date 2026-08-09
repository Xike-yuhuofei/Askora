"""Opt-in P1-01B real configured-model open-response scoring gate."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid4, uuid5

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.contracts.goal_management import GoalAchievementPolicyV1
from app.core.config import LLMProvider, Settings, settings
from app.core.database import Base
from app.services.assessment.goal_achievement import GoalAchievementAssessmentService
from app.services.llm import model_router as router_module


def _configured_model() -> tuple[Settings, LLMProvider, str]:
    configured = Settings(_env_file=".env", _env_ignore_empty=True)  # type: ignore[call-arg]
    candidates = {
        LLMProvider.QWEN: (configured.llm_qwen_api_key, configured.llm_qwen_model),
        LLMProvider.DEEPSEEK: (configured.llm_deepseek_api_key, configured.llm_deepseek_model),
        LLMProvider.DOUBAO: (configured.llm_doubao_api_key, configured.llm_doubao_model),
        LLMProvider.ZHIPU: (configured.llm_zhipu_api_key, configured.llm_zhipu_model),
    }
    preferred = (
        LLMProvider.DEEPSEEK,
        configured.llm_default_provider,
        LLMProvider.ZHIPU,
        LLMProvider.QWEN,
        LLMProvider.DOUBAO,
    )
    for provider in dict.fromkeys(preferred):
        candidate_key, candidate_model = candidates[provider]
        if candidate_key:
            return configured, provider, candidate_model
    pytest.fail("ASKORA_RUN_REAL_MODEL=1 but no configured real model credential was found")


@pytest.mark.asyncio
async def test_real_configured_model_double_grades_goal_open_response(tmp_path) -> None:
    if os.getenv("ASKORA_RUN_REAL_MODEL") != "1":
        pytest.skip("real model goal grader gate runs separately with ASKORA_RUN_REAL_MODEL=1")
    configured, provider_name, model_name = _configured_model()
    original = settings.model_dump()
    for name in (
        "llm_qwen_api_key",
        "llm_deepseek_api_key",
        "llm_doubao_api_key",
        "llm_zhipu_api_key",
        "llm_qwen_model",
        "llm_deepseek_model",
        "llm_doubao_model",
        "llm_zhipu_model",
        "llm_zhipu_base_url",
        "llm_zhipu_thinking_enabled",
    ):
        setattr(settings, name, getattr(configured, name))
    settings.llm_default_provider = provider_name
    settings.llm_timeout = max(configured.llm_timeout, 60)
    router_module._model_router = None
    router = router_module.get_model_router()
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'real-goal-grader.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(timezone.utc)
    policy = GoalAchievementPolicyV1(
        policy_id=uuid5(NAMESPACE_URL, "askora:goal-achievement-policy:real-e2e"),
        policy_version=1,
        name="real model E2E policy",
        delay_seconds={
            process: 0 for process in ("recall", "understand", "explain", "apply", "transfer")
        },
        minimum_score=0.75,
        minimum_assessment_confidence=0.7,
        maximum_grader_disagreement=0.2,
        novelty_policy={"apply": "new_context_required"},
        rubric_version="goal-rubric/real-e2e",
        grader_schema_version="goal-open-grade/1.0",
        reviewer_required=True,
        created_at=now,
    )
    try:
        async with factory() as session:
            outcome = await GoalAchievementAssessmentService(session, router=router).score(
                user_id=uuid4(),
                activity_id=uuid4(),
                item_version="goal-real-e2e/1",
                response="孤立系统的熵不会减少；热机在冷热源温差更大时理论效率上限更高。",
                scoring_method="open_response",
                grader_payload={
                    "topic": "science",
                    "rubric": {
                        "criterion": "独立解释热力学第二定律并应用到一个新的热机场景",
                        "accuracy": "解释熵增方向并建立与热机效率的合理联系",
                    },
                    "source_evidence": "孤立系统中的熵不会减少。热机效率受冷热源温度约束。",
                },
                policy=policy,
                idempotency_key="goal-real-open-grade-e2e",
                now=now,
            )
            assert outcome.status in {"accepted", "needs_review", "scoring_failed"}
            if outcome.status == "scoring_failed":
                assert outcome.result is None
                assert outcome.reason_codes == ("GOAL_OPEN_GRADER_UNAVAILABLE",)
            else:
                assert outcome.result is not None
                assert len(outcome.result.evaluator_versions) == 2
            if outcome.status == "needs_review" and outcome.result is not None:
                assert outcome.result.reviewer_result == "needs_review"
                assert outcome.result.correctness == "unscorable"
            elif outcome.status == "accepted" and outcome.result is not None:
                assert outcome.result.reviewer_result == "accepted"
            print(
                "GOAL_REAL_MODEL_RESULT "
                + json.dumps(
                    {
                        "provider": provider_name.value,
                        "model": model_name,
                        "evaluator_versions": (
                            outcome.result.evaluator_versions if outcome.result else []
                        ),
                        "assessment_confidence": (
                            outcome.result.assessment_confidence if outcome.result else None
                        ),
                        "result": outcome.status,
                    },
                    ensure_ascii=False,
                )
            )
    finally:
        await router.close()
        await engine.dispose()
        for name, value in original.items():
            setattr(settings, name, value)
        router_module._model_router = None

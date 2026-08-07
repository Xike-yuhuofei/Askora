from __future__ import annotations

from datetime import timedelta

import pytest

from app.contracts.adaptive import AssistanceState, VersionedRef
from app.domains.assessment import AdaptiveAssessmentService
from app.domains.learner_model import (
    AdaptiveEvidenceEligibility,
    AdaptiveEvidenceEligibilityProfile,
)
from app.orchestration.learning_facade import LearningOrchestrationFacade
from tests.fixtures.v03_execution_factory import TightRenderer, adaptive_request
from tests.fixtures.v03_policy_factory import NOW, fixed_uuid, ref


@pytest.mark.asyncio
async def test_policy_to_actual_assistance_to_learner_evidence_e2e() -> None:
    turn = await LearningOrchestrationFacade(adaptive_renderer=TightRenderer()).run_turn(
        adaptive_request()
    )
    assert turn.teaching_action_v03 is not None
    assert turn.adaptive_execution_v03 is not None
    action = turn.teaching_action_v03
    execution = turn.adaptive_execution_v03

    assessment = AdaptiveAssessmentService().assess_exact(
        user_id=fixed_uuid("e2e-user"),
        session_id=fixed_uuid("e2e-session"),
        item_id=fixed_uuid("e2e-item"),
        item_version="1",
        assessment_type="formative",
        response="correct",
        expected_answer="correct",
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
        idempotency_key="v03-e2e-attempt",
        assessment_confidence=0.95,
        diagnostic_confidence=0.2,
    )
    evidence = AdaptiveEvidenceEligibility().decide(
        result=assessment.result,
        attempt=assessment.attempt,
        actual_assistance=execution.actual_assistance,
        profile=AdaptiveEvidenceEligibilityProfile(
            profile_version="e2e-eligibility-1",
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
        novelty="far_variant",
        delay_seconds=0,
        source_event_refs=(ref("learning_event", "e2e-actual-assistance"),),
    )
    assert evidence.accepted
    assert evidence.evidence is not None
    assert evidence.evidence.assistance_state is execution.actual_assistance.assistance_state
    assert turn.engine_debug == {
        **turn.engine_debug,
        "final_action_owner": "SYS05",
        "retrieval_owner": "SYS02",
        "execution_owner": "SYS08",
    }

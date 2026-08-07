from __future__ import annotations

from datetime import timedelta

import pytest
from pydantic import ValidationError

from app.contracts.adaptive import (
    AnswerExposure,
    AssistanceState,
    HintSpecificity,
    ScaffoldControl,
    VersionedRef,
)
from app.domains.assessment import AdaptiveAssessmentService
from app.domains.learner_model import (
    AdaptiveEvidenceEligibility,
    AdaptiveEvidenceEligibilityProfile,
)
from app.domains.retrieval import AdaptiveEvidenceRetriever
from app.orchestration.adaptive_execution import AdaptiveExecutionService
from tests.fixtures.v03_execution_factory import TightRenderer, make_action, make_candidate
from tests.fixtures.v03_policy_factory import NOW, fixed_uuid, ref

PROFILE = AdaptiveEvidenceEligibilityProfile(
    profile_version="eligibility-1",
    minimum_assessment_confidence=0.5,
    independence_weights={
        AssistanceState.INDEPENDENT: 1.0,
        AssistanceState.ASSISTED: 0.35,
        AssistanceState.ANSWER_EXPOSED: 0.0,
    },
    novelty_weights={"repeated": 0.5, "near_variant": 0.8, "far_variant": 1.0},
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("case", "renderer", "expected_state", "expected_weight"),
    [
        (
            {"case_id": "independent", "mastery": 0.9},
            TightRenderer(),
            AssistanceState.INDEPENDENT,
            0.95,
        ),
        (
            {"case_id": "assisted", "mastery": 0.2},
            TightRenderer(
                scaffold=ScaffoldControl.MEDIUM,
                hint=HintSpecificity.ORIENTATION,
                exposure=AnswerExposure.PARTIAL,
            ),
            AssistanceState.ASSISTED,
            0.3325,
        ),
        (
            {"case_id": "answer", "mastery": 0.2, "direct_answer_request": True},
            TightRenderer(
                scaffold=ScaffoldControl.HIGH,
                hint=HintSpecificity.BOTTOM_OUT,
                exposure=AnswerExposure.COMPLETE,
            ),
            AssistanceState.ANSWER_EXPOSED,
            0.0,
        ),
    ],
)
async def test_actual_assistance_controls_evidence_semantics(
    case: dict[str, object],
    renderer: TightRenderer,
    expected_state: AssistanceState,
    expected_weight: float,
) -> None:
    action = make_action(case)
    candidate = make_candidate(f"eligibility-{expected_state.value}", exposure=renderer.exposure)
    bundle = (
        AdaptiveEvidenceRetriever()
        .build(
            request_id=fixed_uuid(f"eligibility-{expected_state.value}"),
            teaching_action=action,
            query="fractions",
            candidates=(candidate,),
            source_scope={},
            index_versions={"lexical": "1"},
        )
        .bundle
    )
    execution = await AdaptiveExecutionService().execute(
        user_text="fractions",
        teaching_action=action,
        evidence_bundle=bundle,
        renderer=renderer,
    )
    record = AdaptiveAssessmentService().assess_exact(
        user_id=fixed_uuid("user"),
        session_id=fixed_uuid("session"),
        item_id=fixed_uuid(f"item-{expected_state.value}"),
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
        idempotency_key=f"eligibility-{expected_state.value}",
        assessment_confidence=0.95,
        diagnostic_confidence=0.2,
    )
    decision = AdaptiveEvidenceEligibility().decide(
        result=record.result,
        attempt=record.attempt,
        actual_assistance=execution.actual_assistance,
        profile=PROFILE,
        knowledge_unit_id=fixed_uuid("knowledge-unit"),
        dimension="recall",
        novelty="far_variant",
        delay_seconds=0,
        source_event_refs=(ref("learning_event", f"event-{expected_state.value}"),),
    )
    assert decision.accepted
    assert decision.evidence is not None
    assert decision.evidence.assistance_state is expected_state
    assert decision.evidence.evidence_weight == pytest.approx(expected_weight)
    if expected_state is AssistanceState.ANSWER_EXPOSED:
        assert "V03_ANSWER_EXPOSED_ZERO_INDEPENDENT_WEIGHT" in decision.reason_codes


@pytest.mark.asyncio
async def test_unknown_assistance_is_conservatively_rejected() -> None:
    action = make_action({"case_id": "unknown-assistance", "mastery": 0.9})
    bundle = (
        AdaptiveEvidenceRetriever()
        .build(
            request_id=fixed_uuid("unknown-assistance"),
            teaching_action=action,
            query="fractions",
            candidates=(make_candidate("unknown-assistance", exposure=AnswerExposure.NONE),),
            source_scope={},
            index_versions={"lexical": "1"},
        )
        .bundle
    )
    execution = await AdaptiveExecutionService().execute(
        user_text="fractions",
        teaching_action=action,
        evidence_bundle=bundle,
        renderer=TightRenderer(),
    )
    record = AdaptiveAssessmentService().assess_exact(
        user_id=fixed_uuid("user"),
        session_id=fixed_uuid("session"),
        item_id=fixed_uuid("item-unknown-assistance"),
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
        idempotency_key="unknown-assistance",
        assessment_confidence=0.95,
        diagnostic_confidence=0.2,
    )
    decision = AdaptiveEvidenceEligibility().decide(
        result=record.result,
        attempt=record.attempt,
        actual_assistance=None,
        profile=PROFILE,
        knowledge_unit_id=fixed_uuid("knowledge-unit"),
        dimension="recall",
        novelty="far_variant",
        delay_seconds=0,
        source_event_refs=(ref("learning_event", "unknown-assistance"),),
    )
    assert not decision.accepted
    assert decision.evidence is None
    assert decision.reason_codes == ("V03_ASSISTANCE_UNKNOWN_CONSERVATIVE_REJECT",)


def test_eligibility_profile_cannot_give_answer_exposed_mastery_weight() -> None:
    with pytest.raises(ValidationError):
        AdaptiveEvidenceEligibilityProfile(
            profile_version="unsafe",
            minimum_assessment_confidence=0.5,
            independence_weights={
                AssistanceState.INDEPENDENT: 1.0,
                AssistanceState.ASSISTED: 0.35,
                AssistanceState.ANSWER_EXPOSED: 0.1,
            },
            novelty_weights={"repeated": 0.5, "near_variant": 0.8, "far_variant": 1.0},
        )

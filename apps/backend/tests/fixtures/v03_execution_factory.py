"""Deterministic SYS02/SYS08 fixtures for EXEC-011."""

from __future__ import annotations

from uuid import UUID

from app.contracts.adaptive import (
    AnswerExposure,
    AssistanceState,
    HintSpecificity,
    ScaffoldControl,
    TeachingActionV03,
)
from app.domains.retrieval.adaptive_evidence_service import AdaptiveRetrievalCandidate
from app.domains.teaching_policy.kernel import TeachingPolicyKernel
from app.orchestration.adaptive_execution import AdaptiveRenderRequest, RenderProposal
from app.orchestration.learning_facade import CanonicalTurnRequest
from tests.fixtures.v03_policy_factory import fixed_uuid, load_profile, make_bundle, make_context


def make_action(case: dict[str, object] | None = None) -> TeachingActionV03:
    profile = load_profile()
    return (
        TeachingPolicyKernel()
        .decide(
            context=make_context(case),
            bundle=make_bundle(profile),
            profile=profile,
        )
        .action
    )


def make_candidate(
    name: str,
    *,
    exposure: AnswerExposure | None,
    role: str = "definition",
    content: str | None = None,
    allowed_use: str = "learner_visible",
    source_spans: tuple[UUID, ...] | None = None,
) -> AdaptiveRetrievalCandidate:
    return AdaptiveRetrievalCandidate(
        chunk_id=fixed_uuid(f"chunk-{name}"),
        document_id=fixed_uuid("document"),
        revision_id=fixed_uuid("revision"),
        source_span_ids=(fixed_uuid(f"span-{name}"),) if source_spans is None else source_spans,
        knowledge_unit_ids=(fixed_uuid("knowledge-unit"),),
        content=content or f"fractions verified evidence {name}",
        pedagogical_role=role,
        answer_exposure=exposure,
        allowed_use=allowed_use,  # type: ignore[arg-type]
    )


def exposure_candidates() -> tuple[AdaptiveRetrievalCandidate, ...]:
    return (
        make_candidate("none", exposure=AnswerExposure.NONE),
        make_candidate("partial", exposure=AnswerExposure.PARTIAL, role="hint"),
        make_candidate("complete", exposure=AnswerExposure.COMPLETE, role="solution"),
        make_candidate("unknown", exposure=None),
        make_candidate("grader", exposure=AnswerExposure.COMPLETE, allowed_use="grader_only"),
    )


class TightRenderer:
    def __init__(
        self,
        *,
        scaffold: ScaffoldControl = ScaffoldControl.NONE,
        hint: HintSpecificity = HintSpecificity.NONE,
        exposure: AnswerExposure = AnswerExposure.NONE,
    ) -> None:
        self.scaffold = scaffold
        self.hint = hint
        self.exposure = exposure

    async def render(self, request: AdaptiveRenderRequest) -> RenderProposal:
        if self.exposure is AnswerExposure.COMPLETE:
            state = AssistanceState.ANSWER_EXPOSED
        elif (
            self.scaffold is not ScaffoldControl.NONE
            or self.hint is not HintSpecificity.NONE
            or self.exposure is not AnswerExposure.NONE
        ):
            state = AssistanceState.ASSISTED
        else:
            state = AssistanceState.INDEPENDENT
        used = (
            (request.evidence_bundle.items[0].evidence_id,)
            if request.evidence_bundle.items
            and request.evidence_bundle.items[0].answer_exposure is self.exposure
            else ()
        )
        return RenderProposal(
            response_id=fixed_uuid(f"response-{request.teaching_action.action_id}-{state.value}"),
            response_version="tight-renderer/1",
            text=f"bounded response {state.value}",
            strategy_family=request.teaching_action.strategy_family,
            interaction_moves=request.teaching_action.interaction_moves,
            action_modifiers=request.teaching_action.action_modifiers,
            actual_scaffold_control=self.scaffold,
            actual_hint_specificity=self.hint,
            actual_answer_exposure=self.exposure,
            declared_assistance_state=state,
            used_evidence_ids=used,
        )


def adaptive_request() -> CanonicalTurnRequest:
    profile = load_profile()
    return CanonicalTurnRequest(
        session_id="v03-session",
        user_id=str(fixed_uuid("user")),
        text="fractions",
        turn_id="v03-turn",
        correlation_id="v03-correlation",
        teaching_context_v03=make_context({"case_id": "facade", "mastery": 0.2}),
        policy_bundle_v03=make_bundle(profile),
        policy_profile_v03=profile,
        adaptive_retrieval_candidates=exposure_candidates(),
        adaptive_source_scope={"document_ids": [str(fixed_uuid("document"))]},
        adaptive_index_versions={"lexical": "fixture-1"},
    )

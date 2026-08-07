"""SYS08 policy-bound rendering and tightening-only output validation."""

from __future__ import annotations

from typing import Protocol
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import Field

from app.contracts.adaptive import (
    ActionModifier,
    AnswerExposure,
    AssistanceSnapshotV03,
    AssistanceState,
    EvidenceBundleV03,
    HintSpecificity,
    InteractionMove,
    ScaffoldControl,
    StrategyFamily,
    TeachingActionV03,
    VersionedRef,
)
from app.contracts.base import ContractModel
from app.contracts.events import ActualAssistanceRecordedPayloadV03

_SCAFFOLD_RANK = {
    ScaffoldControl.NONE: 0,
    ScaffoldControl.LOW: 1,
    ScaffoldControl.MEDIUM: 2,
    ScaffoldControl.HIGH: 3,
}
_HINT_RANK = {
    HintSpecificity.NONE: 0,
    HintSpecificity.ORIENTATION: 1,
    HintSpecificity.CONCEPTUAL_STRATEGIC: 2,
    HintSpecificity.SUBGOAL: 3,
    HintSpecificity.PARTIAL_STEP: 4,
    HintSpecificity.BOTTOM_OUT: 5,
}
_EXPOSURE_RANK = {
    AnswerExposure.NONE: 0,
    AnswerExposure.PARTIAL: 1,
    AnswerExposure.COMPLETE: 2,
}


class RenderProposal(ContractModel):
    response_id: UUID
    response_version: str = Field(min_length=1)
    text: str
    strategy_family: StrategyFamily
    interaction_moves: tuple[InteractionMove, ...]
    action_modifiers: ActionModifier
    actual_scaffold_control: ScaffoldControl
    actual_hint_specificity: HintSpecificity
    actual_answer_exposure: AnswerExposure
    declared_assistance_state: AssistanceState
    used_evidence_ids: tuple[UUID, ...] = ()
    requested_tools: tuple[str, ...] = ()
    attempted_action_override: bool = False


class AdaptiveRenderRequest(ContractModel):
    user_text: str
    teaching_action: TeachingActionV03
    evidence_bundle: EvidenceBundleV03


class AdaptiveRenderer(Protocol):
    async def render(self, request: AdaptiveRenderRequest) -> RenderProposal: ...


class AdaptiveExecutionResult(ContractModel):
    response_id: UUID
    response_version: str
    text: str
    teaching_action_ref: VersionedRef
    actual_assistance: AssistanceSnapshotV03
    assistance_event: ActualAssistanceRecordedPayloadV03
    used_evidence_ids: tuple[UUID, ...]
    integrity_reason_codes: tuple[str, ...]
    fallback_used: bool


def _state_for_axes(
    scaffold: ScaffoldControl,
    hint: HintSpecificity,
    exposure: AnswerExposure,
) -> AssistanceState:
    if exposure is AnswerExposure.COMPLETE:
        return AssistanceState.ANSWER_EXPOSED
    if (
        scaffold is not ScaffoldControl.NONE
        or hint is not HintSpecificity.NONE
        or exposure is not AnswerExposure.NONE
    ):
        return AssistanceState.ASSISTED
    return AssistanceState.INDEPENDENT


class PolicyBoundTemplateRenderer:
    """Safe local fallback/default renderer; it never creates source facts."""

    async def render(self, request: AdaptiveRenderRequest) -> RenderProposal:
        action = request.teaching_action
        bundle = request.evidence_bundle
        response_id = uuid5(
            NAMESPACE_URL,
            f"askora:v03:render:{action.action_id}:{bundle.bundle_id}:{request.user_text}",
        )
        if bundle.missing_reason_codes:
            text = "当前资料不足，无法在既定教学动作下给出有依据的内容；请补充资料或重新决策。"
            exposure = AnswerExposure.NONE
            used_ids: tuple[UUID, ...] = ()
            scaffold = ScaffoldControl.NONE
        elif bundle.items:
            first = bundle.items[0]
            text = first.content
            exposure = first.answer_exposure
            used_ids = (first.evidence_id,)
            scaffold = (
                ScaffoldControl.LOW
                if _SCAFFOLD_RANK[action.scaffold_control] >= _SCAFFOLD_RANK[ScaffoldControl.LOW]
                else ScaffoldControl.NONE
            )
        else:
            text = "请先尝试说明你的思路；我会依据你的回答继续。"
            exposure = AnswerExposure.NONE
            used_ids = ()
            scaffold = ScaffoldControl.NONE
        hint = HintSpecificity.NONE
        state = _state_for_axes(scaffold, hint, exposure)
        return RenderProposal(
            response_id=response_id,
            response_version="template-renderer/1.0",
            text=text,
            strategy_family=action.strategy_family,
            interaction_moves=action.interaction_moves,
            action_modifiers=action.action_modifiers,
            actual_scaffold_control=scaffold,
            actual_hint_specificity=hint,
            actual_answer_exposure=exposure,
            declared_assistance_state=state,
            used_evidence_ids=used_ids,
        )


class AdaptiveExecutionService:
    """Validate an untrusted model/tool proposal against immutable SYS05/SYS02 facts."""

    fallback_version = "policy-tightening-fallback/1.0"

    def __init__(self, allowed_tools: frozenset[str] = frozenset()) -> None:
        self._allowed_tools = allowed_tools

    async def execute(
        self,
        *,
        user_text: str,
        teaching_action: TeachingActionV03,
        evidence_bundle: EvidenceBundleV03,
        renderer: AdaptiveRenderer,
    ) -> AdaptiveExecutionResult:
        if evidence_bundle.teaching_action_ref.entity_id != str(teaching_action.action_id):
            raise ValueError("SYS08_EVIDENCE_ACTION_REF_MISMATCH")
        request = AdaptiveRenderRequest(
            user_text=user_text,
            teaching_action=teaching_action,
            evidence_bundle=evidence_bundle,
        )
        proposal = await renderer.render(request)
        reasons: list[str] = []
        if proposal.attempted_action_override:
            reasons.append("SYS08_ACTION_OVERRIDE_DENIED")
        if proposal.strategy_family is not teaching_action.strategy_family:
            reasons.append("SYS08_STRATEGY_OVERRIDE_DENIED")
        if any(
            move not in teaching_action.interaction_moves for move in proposal.interaction_moves
        ):
            reasons.append("SYS08_INTERACTION_MOVE_EXPANSION_DENIED")
        if proposal.action_modifiers != teaching_action.action_modifiers:
            reasons.append("SYS08_ACTION_MODIFIER_OVERRIDE_DENIED")
        if (
            _SCAFFOLD_RANK[proposal.actual_scaffold_control]
            > _SCAFFOLD_RANK[teaching_action.scaffold_control]
        ):
            reasons.append("SYS08_SCAFFOLD_EXPANSION_DENIED")
        if (
            _HINT_RANK[proposal.actual_hint_specificity]
            > _HINT_RANK[teaching_action.hint_specificity]
        ):
            reasons.append("SYS08_HINT_EXPANSION_DENIED")
        if (
            _EXPOSURE_RANK[proposal.actual_answer_exposure]
            > _EXPOSURE_RANK[teaching_action.answer_exposure]
        ):
            reasons.append("SYS08_ANSWER_EXPOSURE_EXPANSION_DENIED")
        if any(tool not in self._allowed_tools for tool in proposal.requested_tools):
            reasons.append("SYS08_UNAUTHORIZED_TOOL_DENIED")

        by_id = {item.evidence_id: item for item in evidence_bundle.items}
        if any(evidence_id not in by_id for evidence_id in proposal.used_evidence_ids):
            reasons.append("SYS08_UNVERIFIED_EVIDENCE_DENIED")
        used_exposure_rank = max(
            (
                _EXPOSURE_RANK[by_id[item].answer_exposure]
                for item in proposal.used_evidence_ids
                if item in by_id
            ),
            default=0,
        )
        if used_exposure_rank > _EXPOSURE_RANK[proposal.actual_answer_exposure]:
            reasons.append("SYS08_ACTUAL_EXPOSURE_UNDERREPORTED")
        computed_state = _state_for_axes(
            proposal.actual_scaffold_control,
            proposal.actual_hint_specificity,
            proposal.actual_answer_exposure,
        )
        if computed_state is not proposal.declared_assistance_state:
            reasons.append("SYS08_ASSISTANCE_STATE_MISMATCH")

        fallback_used = bool(reasons)
        if fallback_used:
            response_id = uuid5(
                NAMESPACE_URL,
                f"askora:v03:safe-fallback:{teaching_action.action_id}:{':'.join(sorted(reasons))}",
            )
            response_version = self.fallback_version
            text = "当前输出未通过教学边界校验。请先说明你的思路，我会在允许范围内继续。"
            scaffold = ScaffoldControl.NONE
            hint = HintSpecificity.NONE
            exposure = AnswerExposure.NONE
            state = AssistanceState.INDEPENDENT
            used_ids: tuple[UUID, ...] = ()
            reasons.append("SYS08_TIGHTENING_FALLBACK_APPLIED")
        else:
            response_id = proposal.response_id
            response_version = proposal.response_version
            text = proposal.text
            scaffold = proposal.actual_scaffold_control
            hint = proposal.actual_hint_specificity
            exposure = proposal.actual_answer_exposure
            state = computed_state
            used_ids = proposal.used_evidence_ids
            reasons.append("SYS08_POLICY_ENVELOPE_VALIDATED")

        snapshot = AssistanceSnapshotV03(
            scaffold_control=scaffold,
            hint_specificity=hint,
            answer_exposure=exposure,
            assistance_state=state,
            support_reason=tuple(reasons),
            delivery_mode="adaptive_renderer",
        )
        action_ref = VersionedRef(
            entity_type="teaching_action",
            entity_id=str(teaching_action.action_id),
            version=teaching_action.action_schema_version,
        )
        response_ref = VersionedRef(
            entity_type="rendered_response",
            entity_id=str(response_id),
            version=response_version,
        )
        event = ActualAssistanceRecordedPayloadV03(
            teaching_action_ref=action_ref,
            rendered_response_ref=response_ref,
            actual_assistance=snapshot,
            integrity_reason_codes=tuple(reasons),
        )
        return AdaptiveExecutionResult(
            response_id=response_id,
            response_version=response_version,
            text=text,
            teaching_action_ref=action_ref,
            actual_assistance=snapshot,
            assistance_event=event,
            used_evidence_ids=used_ids,
            integrity_reason_codes=tuple(reasons),
            fallback_used=fallback_used,
        )

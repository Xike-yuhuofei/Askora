"""Canonical teaching application facade shared by normal and streaming transports.

Spec coverage: API-010/011, SYS08-002, VSLICE-010/011.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.adaptive import (
    EvidenceBundleV03,
    ExperimentAssignmentV03,
    PolicyBundleV03,
    TeachingActionV03,
    TeachingContextV03,
)
from app.contracts.decisions import DecisionTraceV03
from app.contracts.events import ActualAssistanceRecordedPayloadV03
from app.contracts.learning import EvidenceBundle, MasteryEstimate, TeachingAction
from app.contracts.rendering import RenderPayloadV1, markdown_render_payload
from app.core.config import settings
from app.domains.retrieval.adaptive_evidence_service import (
    AdaptiveEvidenceRetriever,
    AdaptiveRetrievalCandidate,
)
from app.domains.teaching_policy import PolicyRuntimeProfile, TeachingPolicyKernel
from app.domains.teaching_policy.evidence import EvidenceSignal, EvidenceSignalKind
from app.domains.teaching_policy.models import SequentialPolicyState
from app.domains.teaching_policy.sequential import SequentialTeachingPolicy
from app.domains.teaching_policy.time_source import TimeSource
from app.engines import FlowStage, LearnerTurn, LearningFlowOrchestrator, get_orchestrator
from app.infrastructure.adaptive_records import AdaptiveContractRepository
from app.orchestration.adaptive_execution import (
    AdaptiveExecutionResult,
    AdaptiveExecutionService,
    AdaptiveRenderer,
    PolicyBoundTemplateRenderer,
)
from app.orchestration.model_rendering import PolicyBoundModelRenderer


@dataclass(frozen=True)
class CanonicalTurnRequest:
    session_id: str
    user_id: str
    text: str
    turn_id: str
    subject: str = "general"
    knowledge_point_id: str | None = None
    learner_persona: str = "k12_high"
    correlation_id: str = ""
    workflow_run_id: str = ""
    model_inference_id: str = ""
    teaching_action: TeachingAction | None = None
    evidence_bundle: EvidenceBundle | None = None
    mastery_estimate: MasteryEstimate | None = None
    teaching_context_v03: TeachingContextV03 | None = None
    policy_bundle_v03: PolicyBundleV03 | None = None
    policy_profile_v03: PolicyRuntimeProfile | None = None
    experiment_assignment_v03: ExperimentAssignmentV03 | None = None
    adaptive_retrieval_candidates: tuple[AdaptiveRetrievalCandidate, ...] | None = None
    adaptive_source_scope: dict[str, object] = field(default_factory=dict)
    adaptive_index_versions: dict[str, str] = field(default_factory=dict)
    previous_teaching_action_v03: TeachingActionV03 | None = None
    previous_decision_trace_v03: DecisionTraceV03 | None = None
    sequential_policy_state_v03: SequentialPolicyState | None = None


@dataclass(frozen=True)
class CanonicalTurnResult:
    reply_text: str
    engine_id: str
    flow_stage: str
    switched_to: str | None
    decision_trace: tuple[str, ...]
    engine_debug: dict[str, Any]
    execution_snapshot: dict[str, Any]
    correlation_id: str
    render_payload: RenderPayloadV1 | None = None
    teaching_action_v03: TeachingActionV03 | None = None
    decision_trace_v03: DecisionTraceV03 | None = None
    evidence_bundle_v03: EvidenceBundleV03 | None = None
    actual_assistance_event_v03: ActualAssistanceRecordedPayloadV03 | None = None
    adaptive_execution_v03: AdaptiveExecutionResult | None = None
    sequential_policy_state_v03: SequentialPolicyState | None = None
    sequential_transition_reason_v03: str | None = None


@dataclass(frozen=True)
class CanonicalStreamEvent:
    type: str
    content: str = ""
    result: CanonicalTurnResult | None = None


class LearningOrchestrationFacade:
    """Production application entry; transport adapters never select engines directly."""

    def __init__(
        self,
        orchestrator: LearningFlowOrchestrator | None = None,
        *,
        policy_kernel: TeachingPolicyKernel | None = None,
        sequential_policy: SequentialTeachingPolicy | None = None,
        adaptive_retriever: AdaptiveEvidenceRetriever | None = None,
        adaptive_executor: AdaptiveExecutionService | None = None,
        adaptive_renderer: AdaptiveRenderer | None = None,
        adaptive_repository: AdaptiveContractRepository | None = None,
    ) -> None:
        self._orchestrator = orchestrator or get_orchestrator()
        self._policy_kernel = policy_kernel or TeachingPolicyKernel()
        self._sequential_policy = sequential_policy or SequentialTeachingPolicy(
            _SystemTimeSource()
        )
        self._adaptive_retriever = adaptive_retriever or AdaptiveEvidenceRetriever()
        self._adaptive_executor = adaptive_executor or AdaptiveExecutionService()
        self._adaptive_renderer = adaptive_renderer or (
            PolicyBoundTemplateRenderer() if settings.is_test else PolicyBoundModelRenderer()
        )
        self._adaptive_repository = adaptive_repository

    async def run_turn(self, request: CanonicalTurnRequest) -> CanonicalTurnResult:
        """Execute one canonical teaching turn for a non-streaming transport."""
        return await self._execute_turn(request)

    async def stream_turn(
        self, request: CanonicalTurnRequest
    ) -> AsyncIterator[CanonicalStreamEvent]:
        """Execute the same canonical turn and adapt its result to a stream transport."""
        result = await self._execute_turn(request)
        if result.reply_text:
            yield CanonicalStreamEvent(type="content", content=result.reply_text)
        yield CanonicalStreamEvent(type="final", result=result)

    async def _execute_turn(self, request: CanonicalTurnRequest) -> CanonicalTurnResult:
        adaptive_fields = (
            request.teaching_context_v03,
            request.policy_bundle_v03,
            request.policy_profile_v03,
            request.adaptive_retrieval_candidates,
        )
        if any(value is not None for value in adaptive_fields):
            if any(value is None for value in adaptive_fields):
                raise ValueError("ADAPTIVE_CANONICAL_INPUT_INCOMPLETE")
            return await self._execute_adaptive_turn(request)
        return await self._execute_legacy_turn(request)

    async def _execute_adaptive_turn(self, request: CanonicalTurnRequest) -> CanonicalTurnResult:
        context = request.teaching_context_v03
        bundle = request.policy_bundle_v03
        profile = request.policy_profile_v03
        candidates = request.adaptive_retrieval_candidates
        if context is None or bundle is None or profile is None or candidates is None:
            raise ValueError("ADAPTIVE_CANONICAL_INPUT_INCOMPLETE")
        decision: Any
        sequential_state: SequentialPolicyState | None = None
        transition_reason: str | None = None
        if (
            request.sequential_policy_state_v03 is not None
            or request.previous_teaching_action_v03 is not None
        ):
            state = request.sequential_policy_state_v03
            if state is None:
                prev_action = request.previous_teaching_action_v03
                prev_trace = request.previous_decision_trace_v03
                if prev_action is None or prev_trace is None:
                    raise ValueError(
                        "Sequential decision requires previous TeachingAction and DecisionTrace"
                    )
                state = SequentialPolicyState(
                    previous_action=prev_action,
                    previous_trace=prev_trace,
                    evidence_opportunities_since_transition=0,
                )
            signals = _build_evidence_signals(context, profile)
            seq_result = self._sequential_policy.decide(
                context=context,
                bundle=bundle,
                profile=profile,
                state=state,
                signals=signals,
                assignment=request.experiment_assignment_v03,
            )
            decision = seq_result.decision
            sequential_state = seq_result.next_state
            transition_reason = seq_result.transition_reason_code
        else:
            decision = self._policy_kernel.decide(
                context=context,
                bundle=bundle,
                profile=profile,
                assignment=request.experiment_assignment_v03,
            )
        request_id = uuid5(
            NAMESPACE_URL,
            f"askora:v03:turn:{request.session_id}:{request.turn_id}:{context.context_fingerprint}",
        )
        evidence = self._adaptive_retriever.build(
            request_id=request_id,
            teaching_action=decision.action,
            query=request.text,
            candidates=candidates,
            source_scope=request.adaptive_source_scope,
            index_versions=request.adaptive_index_versions,
        )
        execution = await self._adaptive_executor.execute(
            user_text=request.text,
            teaching_action=decision.action,
            evidence_bundle=evidence.bundle,
            renderer=self._adaptive_renderer,
            subject=request.subject,
            target_capability=(
                str(context.target_capability.value)
                if context.target_capability.value is not None
                else None
            ),
            inference_id=(UUID(request.model_inference_id) if request.model_inference_id else None),
        )
        trace_table = [
            {
                "chunk_id": item.chunk_id,
                "score": item.score,
                "selected": item.selected,
                "reason_codes": list(item.reason_codes),
            }
            for item in evidence.trace.candidate_table
        ]
        reason_codes = [*decision.trace.reason_codes, *execution.integrity_reason_codes]
        if transition_reason is not None:
            reason_codes.append(transition_reason)
        return CanonicalTurnResult(
            reply_text=execution.text,
            engine_id="sys08_policy_bound_execution",
            flow_stage=decision.action.teaching_stage.value,
            switched_to=None,
            decision_trace=tuple(reason_codes),
            engine_debug={
                "final_action_owner": "SYS05",
                "retrieval_owner": "SYS02",
                "execution_owner": "SYS08",
                "retrieval_trace": trace_table,
            },
            execution_snapshot={
                "teaching_context": context.model_dump(mode="json"),
                "teaching_action": decision.action.model_dump(mode="json"),
                "decision_trace": decision.trace.model_dump(mode="json"),
                "evidence_bundle": evidence.bundle.model_dump(mode="json"),
                "actual_assistance": execution.actual_assistance.model_dump(mode="json"),
            },
            correlation_id=request.correlation_id,
            render_payload=markdown_render_payload(execution.text),
            teaching_action_v03=decision.action,
            decision_trace_v03=decision.trace,
            evidence_bundle_v03=evidence.bundle,
            actual_assistance_event_v03=execution.assistance_event,
            adaptive_execution_v03=execution,
            sequential_policy_state_v03=sequential_state,
            sequential_transition_reason_v03=transition_reason,
        )

    async def _execute_legacy_turn(self, request: CanonicalTurnRequest) -> CanonicalTurnResult:
        """v0.2 compatibility path; it cannot produce canonical v0.3 actions."""
        await self._orchestrator.ensure_session(
            session_id=request.session_id,
            subject=request.subject,
            knowledge_point_id=request.knowledge_point_id,
            initial_stage=FlowStage.LEARN,
            learner_persona=request.learner_persona,
            extras={
                "user_id": request.user_id,
                "source": "canonical_learning_facade",
                "correlation_id": request.correlation_id,
                "workflow_run_id": request.workflow_run_id,
                "model_inference_id": request.model_inference_id,
                "canonical_execution": {
                    "teaching_action": (
                        request.teaching_action.model_dump(mode="json")
                        if request.teaching_action
                        else None
                    ),
                    "evidence_bundle": (
                        request.evidence_bundle.model_dump(mode="json")
                        if request.evidence_bundle
                        else None
                    ),
                },
                "canonical_mastery_snapshot": (
                    request.mastery_estimate.model_dump(mode="json")
                    if request.mastery_estimate
                    else None
                ),
            },
        )
        result = await self._orchestrator.run_turn(
            session_id=request.session_id,
            learner_turn=LearnerTurn(
                text=request.text.strip(),
                turn_id=request.turn_id,
                attachments=[],
            ),
        )
        return CanonicalTurnResult(
            reply_text=result.reply_text,
            engine_id=result.engine_id,
            flow_stage=result.flow_stage.value,
            switched_to=result.switched_to,
            decision_trace=tuple(result.decision_trace),
            engine_debug=dict(result.engine_debug),
            execution_snapshot=dict(result.shared_ctx_snapshot),
            correlation_id=request.correlation_id,
            render_payload=markdown_render_payload(result.reply_text),
        )


_FACADE: LearningOrchestrationFacade | None = None


def get_learning_orchestration_facade() -> LearningOrchestrationFacade:
    global _FACADE
    if _FACADE is None:
        _FACADE = LearningOrchestrationFacade()
    return _FACADE


class _SystemTimeSource:
    def now(self) -> datetime:
        return datetime.now(tz=timezone.utc)


def _build_evidence_signals(
    context: TeachingContextV03, profile: PolicyRuntimeProfile
) -> tuple[EvidenceSignal, ...]:
    signals: list[EvidenceSignal] = []
    now = datetime.now(tz=timezone.utc)

    fingerprint = context.context_fingerprint
    base_ref = context.learning_objective_ref

    if context.recent_assessment_result_ref is not None:
        signals.append(
            EvidenceSignal(
                signal_id=f"assessment:{fingerprint}",
                kind=EvidenceSignalKind.ASSESSMENT_RESULT,
                evidence_ref=context.recent_assessment_result_ref,
                occurred_at=context.decision_time,
                attributes={"source": "teaching_context_v03"},
            )
        )

    for ref in context.assisted_success_history:
        signals.append(
            EvidenceSignal(
                signal_id=f"assisted:{fingerprint}:{ref.entity_id}",
                kind=EvidenceSignalKind.ASSISTANCE_EVENT,
                evidence_ref=ref,
                occurred_at=context.decision_time,
                attributes={"source": "teaching_context_v03"},
            )
        )

    for ref in context.independent_success_history:
        signals.append(
            EvidenceSignal(
                signal_id=f"independent:{fingerprint}:{ref.entity_id}",
                kind=EvidenceSignalKind.INDEPENDENT_ATTEMPT,
                evidence_ref=ref,
                occurred_at=context.decision_time,
                attributes={"source": "teaching_context_v03"},
            )
        )

    if context.direct_answer_request:
        signals.append(
            EvidenceSignal(
                signal_id=f"user-request:{fingerprint}",
                kind=EvidenceSignalKind.EXPLICIT_USER_REQUEST,
                evidence_ref=base_ref,
                occurred_at=context.decision_time,
                attributes={"source": "teaching_context_v03"},
            )
        )

    error_value = context.error_type.value
    if isinstance(error_value, str) and error_value == "UNKNOWN":
        signals.append(
            EvidenceSignal(
                signal_id=f"probe:{fingerprint}",
                kind=EvidenceSignalKind.DIAGNOSTIC_PROBE,
                evidence_ref=base_ref,
                occurred_at=context.decision_time,
                attributes={"source": "teaching_context_v03"},
            )
        )

    if context.review_context.value is not None and context.review_context.value:
        elapsed_attrs = context.delayed_independent_evidence.attributes or {}
        elapsed = float(elapsed_attrs.get("delay_seconds", 0))
        if elapsed >= profile.meaningful_delay_seconds:
            signals.append(
                EvidenceSignal(
                    signal_id=f"review-delay:{fingerprint}",
                    kind=EvidenceSignalKind.REVIEW_DELAY_TRANSITION,
                    evidence_ref=base_ref,
                    occurred_at=context.decision_time,
                    attributes={
                        "source": "teaching_context_v03",
                        "delay_started_at": (
                            context.decision_time.timestamp() - elapsed
                        ),
                    },
                )
            )

    if not signals:
        signals.append(
            EvidenceSignal(
                signal_id=f"chat:{fingerprint}",
                kind=EvidenceSignalKind.CHAT_TURN,
                evidence_ref=base_ref,
                occurred_at=now,
                attributes={"source": "default"},
            )
        )

    return tuple(signals)

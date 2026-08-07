"""Canonical teaching application facade shared by normal and streaming transports.

Spec coverage: API-010/011, SYS08-002, VSLICE-010/011.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from app.engines import FlowStage, LearnerTurn, LearningFlowOrchestrator, get_orchestrator


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


@dataclass(frozen=True)
class CanonicalStreamEvent:
    type: str
    content: str = ""
    result: CanonicalTurnResult | None = None


class LearningOrchestrationFacade:
    """Production application entry; transport adapters never select engines directly."""

    def __init__(self, orchestrator: LearningFlowOrchestrator | None = None) -> None:
        self._orchestrator = orchestrator or get_orchestrator()

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
        )


_FACADE: LearningOrchestrationFacade | None = None


def get_learning_orchestration_facade() -> LearningOrchestrationFacade:
    global _FACADE
    if _FACADE is None:
        _FACADE = LearningOrchestrationFacade()
    return _FACADE

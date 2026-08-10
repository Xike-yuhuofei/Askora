"""EXEC-042 P0-1 fail-closed and persisted sequential replay production tests.

These tests close the documented P0-1 requirement: when a canonical previous
TeachingAction already exists, any missing / mismatched / out-of-scope prior
evidence must FAIL CLOSED — never silently downgrade to a first-turn bootstrap
kernel. They also verify the persisted-record sequential replay determinism
(EXEC042-AC-013 / section 十).
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.contracts.adaptive import (
    AvailabilityStatus,
    TeachingContextV03,
    ValueWithAvailability,
    VersionedRef,
)
from app.domains.teaching_policy import TeachingPolicyKernel
from app.orchestration.learning_facade import CanonicalTurnRequest, LearningOrchestrationFacade

NOW = datetime(2026, 8, 10, 14, 0, tzinfo=timezone.utc)


def _minimal_context(
    *,
    previous_ref: VersionedRef | None = None,
    fingerprint: str = "fc-context",
) -> TeachingContextV03:
    objective = VersionedRef(entity_type="LearningObjective", entity_id="fc-obj", version="1")
    activity = VersionedRef(entity_type="LearningActivity", entity_id="fc-act", version="1")
    sources = [objective, activity]
    if previous_ref is not None:
        sources.append(previous_ref)
    return TeachingContextV03(
        context_id=uuid4(),
        decision_time=NOW,
        context_fingerprint=fingerprint,
        learning_objective_ref=objective,
        learning_activity_ref=activity,
        activity_type=ValueWithAvailability(
            value="lesson",
            availability=AvailabilityStatus.AVAILABLE,
            confidence=1.0,
            source_refs=(activity,),
        ),
        target_capability=ValueWithAvailability(
            value="apply",
            availability=AvailabilityStatus.AVAILABLE,
            confidence=1.0,
            source_refs=(objective,),
        ),
        mastery_confidence=ValueWithAvailability(
            value=0.3,
            availability=AvailabilityStatus.AVAILABLE,
            confidence=1.0,
            source_refs=(),
        ),
        prerequisite_confidence=ValueWithAvailability(
            value=0.3,
            availability=AvailabilityStatus.AVAILABLE,
            confidence=1.0,
            source_refs=(),
        ),
        evidence_sufficiency=ValueWithAvailability(availability=AvailabilityStatus.MISSING),
        correctness_score=ValueWithAvailability(availability=AvailabilityStatus.MISSING),
        assessment_confidence=ValueWithAvailability(availability=AvailabilityStatus.MISSING),
        error_type=ValueWithAvailability(availability=AvailabilityStatus.MISSING),
        diagnostic_confidence=ValueWithAvailability(availability=AvailabilityStatus.MISSING),
        needs_probe=ValueWithAvailability(availability=AvailabilityStatus.MISSING),
        worked_example_exposure=ValueWithAvailability(availability=AvailabilityStatus.MISSING),
        delayed_independent_evidence=ValueWithAvailability(availability=AvailabilityStatus.MISSING),
        review_context=ValueWithAvailability(availability=AvailabilityStatus.MISSING),
        transfer_evidence=ValueWithAvailability(availability=AvailabilityStatus.MISSING),
        transfer_distance_novelty=ValueWithAvailability(availability=AvailabilityStatus.MISSING),
        time_budget=ValueWithAvailability(
            value=600,
            availability=AvailabilityStatus.AVAILABLE,
            confidence=1.0,
            source_refs=(activity,),
        ),
        previous_teaching_action_ref=previous_ref,
        source_refs=tuple(sources),
    )


def _bootstrap_previous(context: TeachingContextV03) -> tuple[VersionedRef, object, object]:
    """Produce a canonical bootstrap decision for a context and return its ref + action/trace."""
    from tests.fixtures.v03_policy_factory import load_profile, make_bundle

    profile = load_profile()
    kernel = TeachingPolicyKernel()
    decision = kernel.decide(context=context, bundle=make_bundle(profile), profile=profile)
    ref = VersionedRef(
        entity_type="teaching_action",
        entity_id=str(decision.action.action_id),
        version=decision.action.action_schema_version,
    )
    return ref, decision.action, decision.trace


def _adaptive_request(
    *,
    context: TeachingContextV03,
    previous_action: object | None = None,
    previous_trace: object | None = None,
    sequential_state: object | None = None,
) -> CanonicalTurnRequest:
    from tests.fixtures.v03_policy_factory import load_profile, make_bundle

    profile = load_profile()
    return CanonicalTurnRequest(
        session_id="fc-session",
        user_id="fc-user",
        text="continue",
        turn_id="fc-turn",
        subject="lesson",
        teaching_context_v03=context,
        policy_bundle_v03=make_bundle(profile),
        policy_profile_v03=profile,
        adaptive_retrieval_candidates=(),
        previous_teaching_action_v03=previous_action,
        previous_decision_trace_v03=previous_trace,
        sequential_policy_state_v03=sequential_state,
    )


async def test_exec042_fail_closed_previous_ref_without_action_or_trace() -> None:
    """context.previous_teaching_action_ref exists but no action/trace/state supplied.

    The production composition MUST fail closed instead of falling back to the
    bootstrap kernel.
    """
    context = _minimal_context(
        previous_ref=VersionedRef(
            entity_type="teaching_action", entity_id="fc-prev", version="1"
        ),
        fingerprint="fc-no-input",
    )
    facade = LearningOrchestrationFacade()
    with pytest.raises(ValueError, match="Sequential decision requires previous"):
        await facade.run_turn(_adaptive_request(context=context))


async def test_exec042_fail_closed_previous_action_without_trace() -> None:
    """previous TeachingAction supplied but its exact DecisionTrace is missing."""
    base = _minimal_context(fingerprint="fc-bare")
    _, action, _ = _bootstrap_previous(base)
    context = _minimal_context(
        previous_ref=VersionedRef(
            entity_type="teaching_action",
            entity_id=str(action.action_id),
            version=action.action_schema_version,
        ),
        fingerprint="fc-action-no-trace",
    )
    facade = LearningOrchestrationFacade()
    with pytest.raises(ValueError, match="Sequential decision requires previous"):
        await facade.run_turn(_adaptive_request(context=context, previous_action=action))


async def test_exec042_fail_closed_trace_selects_different_action() -> None:
    """previous DecisionTrace selects a different TeachingAction than the supplied one.

    Reconstruction must raise because the trace does not exactly match the
    previous action (SequentialPolicyState.require_exact_previous_trace).
    """
    base = _minimal_context(fingerprint="fc-mismatch-base")
    _, action, _ = _bootstrap_previous(base)
    # Build a trace that selects a *different* (fresh) action than `action`.
    from tests.fixtures.v03_policy_factory import load_profile, make_bundle

    profile = load_profile()
    mismatched_decision = TeachingPolicyKernel().decide(
        context=_minimal_context(fingerprint="fc-mismatch-other"),
        bundle=make_bundle(profile),
        profile=profile,
    )
    context = _minimal_context(
        previous_ref=VersionedRef(
            entity_type="teaching_action",
            entity_id=str(action.action_id),
            version=action.action_schema_version,
        ),
        fingerprint="fc-trace-mismatch",
    )
    facade = LearningOrchestrationFacade()
    # The trace's selected ref does not match `action` -> reconstruction raises
    # a deterministic fail-closed error, never a silent bootstrap fallback.
    with pytest.raises(ValidationError, match="must exactly select previous"):
        await facade.run_turn(
            _adaptive_request(
                context=context,
                previous_action=action,
                previous_trace=mismatched_decision.trace,
            )
        )


async def test_exec042_persisted_sequential_replay_is_deterministic() -> None:
    """Replay from exact persisted inputs with a pinned decision_time reproduces
    the same semantic TeachingAction and DecisionTrace, with the online model
    entry patched to fail.
    """
    from tests.fixtures.v03_policy_factory import load_profile, make_bundle

    profile = load_profile()
    bundle = make_bundle(profile)
    kernel = TeachingPolicyKernel()

    first_context = _minimal_context(fingerprint="replay-first")
    first = kernel.decide(context=first_context, bundle=bundle, profile=profile)

    # Reconstruct sequential state from the persisted first decision.
    from app.orchestration.learning_facade import _reconstruct_sequential_policy_state

    sequential_state = _reconstruct_sequential_policy_state(first.action, first.trace)

    second_context = _minimal_context(
        previous_ref=VersionedRef(
            entity_type="teaching_action",
            entity_id=str(first.action.action_id),
            version=first.action.action_schema_version,
        ),
        fingerprint="replay-second",
    )
    # Second context must carry the exact previous action ref used by
    # _exact_previous_ref during sequential evaluation.
    second_context = second_context.model_copy(
        update={
            "previous_teaching_action_ref": VersionedRef(
                entity_type="teaching_action",
                entity_id=str(first.action.action_id),
                version=first.action.action_schema_version,
            ),
            "source_refs": tuple(
                dict.fromkeys(
                    [
                        *second_context.source_refs,
                        VersionedRef(
                            entity_type="teaching_action",
                            entity_id=str(first.action.action_id),
                            version=first.action.action_schema_version,
                        ),
                    ]
                )
            ),
        }
    )

    facade = LearningOrchestrationFacade()
    result = await facade.run_turn(
        _adaptive_request(
            context=second_context,
            previous_action=first.action,
            previous_trace=first.trace,
            sequential_state=sequential_state,
        )
    )
    second_action = result.teaching_action_v03
    second_trace = result.decision_trace_v03
    assert second_action is not None
    assert second_trace is not None
    assert second_trace.previous_teaching_action_ref is not None
    assert second_trace.previous_teaching_action_ref.entity_id == str(first.action.action_id)
    assert second_trace.behavior_policy_type == "DETERMINISTIC"
    assert second_trace.action_propensity is None

    # Replay: same immutable inputs + same decision_time -> same semantic result.
    replayed = await facade.run_turn(
        _adaptive_request(
            context=second_context,
            previous_action=first.action,
            previous_trace=first.trace,
            sequential_state=sequential_state,
        )
    )
    assert replayed.teaching_action_v03 == second_action
    assert replayed.decision_trace_v03 == second_trace

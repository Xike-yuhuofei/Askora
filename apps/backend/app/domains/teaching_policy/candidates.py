"""Versioned typed candidate table for the six canonical strategy families."""

from __future__ import annotations

from app.contracts.adaptive import (
    ActionModifier,
    AnswerExposure,
    HintSpecificity,
    InteractionMove,
    ScaffoldControl,
    StrategyFamily,
    TeachingStage,
)
from app.domains.teaching_policy.models import TeachingCandidate


def candidate_table() -> tuple[TeachingCandidate, ...]:
    """Return the closed v0.3 candidate vocabulary in stable action-key order."""

    return (
        TeachingCandidate(
            action_key="explicit_instruction.core",
            strategy_family=StrategyFamily.EXPLICIT_INSTRUCTION,
            allowed_stages=(TeachingStage.EXPLICIT_INSTRUCTION,),
            interaction_moves=(
                InteractionMove.DIRECT_INSTRUCTION,
                InteractionMove.WORKED_EXAMPLE,
            ),
            action_modifiers=ActionModifier(self_explanation=True),
            scaffold_control=ScaffoldControl.HIGH,
            hint_specificity=HintSpecificity.CONCEPTUAL_STRATEGIC,
            answer_exposure=AnswerExposure.PARTIAL,
            evidence_requirements=("guided_attempt",),
            expected_evidence_type="assisted_attempt",
            success_condition={"kind": "guided_attempt_completed"},
            failure_condition={"kind": "cannot_apply_explanation"},
            max_attempts=2,
        ),
        TeachingCandidate(
            action_key="guided_practice.core",
            strategy_family=StrategyFamily.GUIDED_PRACTICE,
            allowed_stages=(TeachingStage.DIAGNOSE, TeachingStage.GUIDED_PRACTICE),
            interaction_moves=(
                InteractionMove.SOCRATIC_PROBE,
                InteractionMove.ORIENTATION_HINT,
            ),
            action_modifiers=ActionModifier(self_explanation=True),
            scaffold_control=ScaffoldControl.MEDIUM,
            hint_specificity=HintSpecificity.ORIENTATION,
            answer_exposure=AnswerExposure.NONE,
            evidence_requirements=("learner_response",),
            expected_evidence_type="diagnostic_or_guided_attempt",
            success_condition={"kind": "learner_advances_with_bounded_support"},
            failure_condition={"kind": "no_progress_after_bounded_support"},
            max_attempts=2,
        ),
        TeachingCandidate(
            action_key="fading_practice.core",
            strategy_family=StrategyFamily.FADING_PRACTICE,
            allowed_stages=(TeachingStage.FADING_PRACTICE,),
            interaction_moves=(
                InteractionMove.COMPLETION_PROBLEM,
                InteractionMove.FADING_STEP,
            ),
            action_modifiers=ActionModifier(transition_intent="fade_support"),
            scaffold_control=ScaffoldControl.LOW,
            hint_specificity=HintSpecificity.ORIENTATION,
            answer_exposure=AnswerExposure.NONE,
            evidence_requirements=("independent_completion",),
            expected_evidence_type="reduced_support_attempt",
            success_condition={"kind": "reduced_support_success"},
            failure_condition={"kind": "support_needed_again"},
            max_attempts=2,
        ),
        TeachingCandidate(
            action_key="retrieval_practice.core",
            strategy_family=StrategyFamily.RETRIEVAL_PRACTICE,
            allowed_stages=(TeachingStage.RETRIEVAL_PRACTICE, TeachingStage.DELAYED_RETRIEVAL),
            interaction_moves=(InteractionMove.RETRIEVAL_REQUEST,),
            action_modifiers=ActionModifier(),
            scaffold_control=ScaffoldControl.NONE,
            hint_specificity=HintSpecificity.NONE,
            answer_exposure=AnswerExposure.NONE,
            evidence_requirements=("independent_retrieval",),
            expected_evidence_type="independent_attempt",
            success_condition={"kind": "independent_retrieval_success"},
            failure_condition={"kind": "retrieval_failure"},
            max_attempts=1,
        ),
        TeachingCandidate(
            action_key="error_remediation.core",
            strategy_family=StrategyFamily.ERROR_REMEDIATION,
            allowed_stages=(TeachingStage.ERROR_REMEDIATION,),
            interaction_moves=(
                InteractionMove.SOCRATIC_PROBE,
                InteractionMove.CONCEPTUAL_HINT,
                InteractionMove.PROCESS_FEEDBACK,
            ),
            action_modifiers=ActionModifier(support_reason=("diagnosed_error",)),
            scaffold_control=ScaffoldControl.HIGH,
            hint_specificity=HintSpecificity.CONCEPTUAL_STRATEGIC,
            answer_exposure=AnswerExposure.NONE,
            evidence_requirements=("remediation_probe",),
            expected_evidence_type="diagnostic_attempt",
            success_condition={"kind": "error_hypothesis_resolved"},
            failure_condition={"kind": "error_persists_or_unknown"},
            max_attempts=2,
        ),
        TeachingCandidate(
            action_key="transfer_challenge.core",
            strategy_family=StrategyFamily.TRANSFER_CHALLENGE,
            allowed_stages=(TeachingStage.TRANSFER_CHALLENGE,),
            interaction_moves=(
                InteractionMove.TRANSFER_TASK,
                InteractionMove.SELF_EXPLANATION_PROMPT,
            ),
            action_modifiers=ActionModifier(self_explanation=True),
            scaffold_control=ScaffoldControl.NONE,
            hint_specificity=HintSpecificity.NONE,
            answer_exposure=AnswerExposure.NONE,
            evidence_requirements=("novel_transfer_attempt",),
            expected_evidence_type="independent_transfer_attempt",
            success_condition={"kind": "novel_transfer_success"},
            failure_condition={"kind": "transfer_failure"},
            max_attempts=1,
        ),
        TeachingCandidate(
            action_key="direct_answer.bounded",
            strategy_family=StrategyFamily.EXPLICIT_INSTRUCTION,
            allowed_stages=(
                TeachingStage.DIAGNOSE,
                TeachingStage.EXPLICIT_INSTRUCTION,
                TeachingStage.GUIDED_PRACTICE,
                TeachingStage.ERROR_REMEDIATION,
            ),
            interaction_moves=(InteractionMove.DIRECT_ANSWER_OVERRIDE,),
            action_modifiers=ActionModifier(
                transition_intent="explicit_user_request",
                support_reason=("user_direct_answer_request",),
            ),
            scaffold_control=ScaffoldControl.HIGH,
            hint_specificity=HintSpecificity.BOTTOM_OUT,
            answer_exposure=AnswerExposure.COMPLETE,
            evidence_requirements=("fresh_independent_validation",),
            expected_evidence_type="answer_exposed_attempt",
            success_condition={"kind": "answer_delivered_then_validation_pending"},
            failure_condition={"kind": "unsafe_or_assessment_integrity_conflict"},
            max_attempts=1,
        ),
    )


def generate_candidates(
    stage: TeachingStage,
    forbidden_action_keys: frozenset[str],
    direct_answer_request: bool,
) -> tuple[TeachingCandidate, ...]:
    """Generate legal candidates without ever reintroducing a hard-filtered key."""

    generated: list[TeachingCandidate] = []
    for candidate in candidate_table():
        if candidate.action_key in forbidden_action_keys:
            continue
        if stage not in candidate.allowed_stages:
            continue
        if candidate.action_key == "direct_answer.bounded" and not direct_answer_request:
            continue
        generated.append(candidate)
    return tuple(generated)

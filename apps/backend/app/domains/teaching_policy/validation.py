"""Exact-snapshot validation for the SYS05 decision entry."""

from __future__ import annotations

from app.contracts.adaptive import (
    ExperimentAssignmentV03,
    PolicyBundleV03,
    TeachingContextV03,
    VersionedRef,
)
from app.domains.teaching_policy.models import (
    PolicyDecisionError,
    PolicyFailureCode,
    PolicyRuntimeProfile,
    ValidatedPolicyInput,
)


def validate_policy_input(
    context: TeachingContextV03,
    bundle: PolicyBundleV03,
    profile: PolicyRuntimeProfile,
    assignment: ExperimentAssignmentV03 | None,
) -> ValidatedPolicyInput:
    """Validate exact immutable inputs without reading any mutable owner state."""

    profile.assert_matches(bundle)
    source_keys = {
        (ref.entity_type, ref.entity_id, str(ref.version)) for ref in context.source_refs
    }
    required_refs = [context.learning_objective_ref, context.learning_activity_ref]
    optional_refs = (
        context.current_task_ref,
        context.mastery_estimate_ref,
        context.recent_assessment_result_ref,
        context.previous_teaching_action_ref,
        context.experiment_assignment_ref,
    )
    required_refs.extend(ref for ref in optional_refs if ref is not None)
    required_refs.extend(context.task_structure_refs)
    required_refs.extend(context.prerequisite_state_refs)
    required_refs.extend(context.misconception_evidence_refs)
    required_refs.extend(context.independent_success_history)
    required_refs.extend(context.assisted_success_history)
    required_refs.extend(context.previous_action_outcome_refs)
    value_fields = (
        context.activity_type,
        context.target_capability,
        context.mastery_confidence,
        context.prerequisite_confidence,
        context.evidence_sufficiency,
        context.correctness_score,
        context.assessment_confidence,
        context.error_type,
        context.diagnostic_confidence,
        context.needs_probe,
        context.worked_example_exposure,
        context.delayed_independent_evidence,
        context.review_context,
        context.transfer_evidence,
        context.transfer_distance_novelty,
        context.time_budget,
    )
    required_refs.extend(ref for value in value_fields for ref in value.source_refs)
    missing_refs = [
        ref
        for ref in required_refs
        if (ref.entity_type, ref.entity_id, str(ref.version)) not in source_keys
    ]
    if missing_refs:
        missing = ",".join(
            f"{ref.entity_type}:{ref.entity_id}@{ref.version}" for ref in missing_refs
        )
        raise PolicyDecisionError(
            PolicyFailureCode.INVALID_CONTEXT,
            f"context source_refs do not pin required exact refs: {missing}",
        )

    assignment_ref = context.experiment_assignment_ref
    if (assignment_ref is None) != (assignment is None):
        raise PolicyDecisionError(
            PolicyFailureCode.EXPERIMENT_ASSIGNMENT_MISMATCH,
            "context assignment ref and exact assignment must be provided together",
        )
    if assignment_ref is not None and assignment is not None:
        if (
            assignment_ref.entity_type != "experiment_assignment"
            or assignment_ref.entity_id != str(assignment.assignment_id)
            or str(assignment_ref.version) != assignment.assignment_schema_version
        ):
            raise PolicyDecisionError(
                PolicyFailureCode.EXPERIMENT_ASSIGNMENT_MISMATCH,
                "assignment identity/version does not match TeachingContext exact ref",
            )

    return ValidatedPolicyInput(
        context_ref=VersionedRef(
            entity_type="teaching_context",
            entity_id=str(context.context_id),
            version=context.context_schema_version,
        ),
        bundle_ref=VersionedRef(
            entity_type="policy_bundle",
            entity_id=bundle.bundle_id,
            version=bundle.policy_version,
        ),
    )

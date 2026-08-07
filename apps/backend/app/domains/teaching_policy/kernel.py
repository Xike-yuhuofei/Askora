"""B3 deterministic single-decision Teaching Policy kernel (EXEC-009)."""

from __future__ import annotations

import json
from uuid import NAMESPACE_URL, UUID, uuid5

from app.contracts.adaptive import (
    AnswerExposure,
    ExperimentAssignmentV03,
    HintSpecificity,
    PolicyBundleV03,
    ScaffoldControl,
    TeachingActionV03,
    TeachingContextV03,
    ValidationObligation,
    VersionedRef,
)
from app.contracts.decisions import (
    BehaviorPolicyType,
    DecisionAlgorithm,
    DecisionFeatureV03,
    DecisionTraceV03,
    ReplayabilityStatus,
)
from app.domains.teaching_policy.candidates import candidate_table, generate_candidates
from app.domains.teaching_policy.constraints import evaluate_hard_constraints
from app.domains.teaching_policy.features import build_candidate_features
from app.domains.teaching_policy.models import (
    PolicyDecision,
    PolicyDecisionError,
    PolicyFailureCode,
    PolicyRuntimeProfile,
)
from app.domains.teaching_policy.scoring import score_candidate, select_stably
from app.domains.teaching_policy.stages import derive_teaching_stage
from app.domains.teaching_policy.validation import validate_policy_input


def _stable_uuid(kind: str, semantic_payload: dict[str, object]) -> UUID:
    canonical = json.dumps(semantic_payload, sort_keys=True, separators=(",", ":"))
    return uuid5(NAMESPACE_URL, f"askora:v0.3:{kind}:{canonical}")


class TeachingPolicyKernel:
    """Pure evaluator: no mutable reads, random choice, LLM call, or persistence."""

    algorithm_id = "askora.teaching_policy.b3"
    algorithm_version = "exec009.1"

    def decide(
        self,
        *,
        context: TeachingContextV03,
        bundle: PolicyBundleV03,
        profile: PolicyRuntimeProfile,
        assignment: ExperimentAssignmentV03 | None = None,
    ) -> PolicyDecision:
        validated = validate_policy_input(context, bundle, profile, assignment)
        table = candidate_table()
        hard = evaluate_hard_constraints(context, profile, table)
        if all(
            not result.passed
            for result in hard.results
            if result.rule_id == "SYS05-HC-HARD-RULE-CONFLICT"
        ):
            raise PolicyDecisionError(
                PolicyFailureCode.HARD_RULE_CONFLICT,
                "candidate priority/configuration conflicts with the closed candidate table",
            )

        stage = derive_teaching_stage(context, profile)
        candidates = generate_candidates(
            stage,
            hard.forbidden_action_keys,
            context.direct_answer_request,
        )
        if not candidates:
            raise PolicyDecisionError(
                PolicyFailureCode.NO_LEGAL_CANDIDATE,
                f"no candidate survives hard constraints for stage {stage.value}",
            )

        feature_sets = tuple(
            build_candidate_features(context, stage, candidate, profile) for candidate in candidates
        )
        scores = tuple(score_candidate(feature_set, profile) for feature_set in feature_sets)
        selected_score, tie_break_reason = select_stably(scores, profile)
        selected = next(
            candidate
            for candidate in candidates
            if candidate.action_key == selected_score.action_key
        )

        semantic_key: dict[str, object] = {
            "context_id": str(context.context_id),
            "context_fingerprint": context.context_fingerprint,
            "bundle_id": bundle.bundle_id,
            "bundle_version": bundle.policy_version,
            "bundle_digest": bundle.content_digest,
            "assignment_id": str(assignment.assignment_id) if assignment else None,
            "selected": selected.action_key,
        }
        decision_id = _stable_uuid("decision", semantic_key)
        action_id = _stable_uuid("action", {**semantic_key, "decision_id": str(decision_id)})
        assisted_envelope = (
            selected.scaffold_control is not ScaffoldControl.NONE
            or selected.hint_specificity is not HintSpecificity.NONE
            or selected.answer_exposure is not AnswerExposure.NONE
        )
        validation_obligation = (
            ValidationObligation.INDEPENDENT_VALIDATION_REQUIRED
            if assisted_envelope
            else ValidationObligation.NONE
        )
        reason_codes = (
            "B3_DETERMINISTIC_SELECTION",
            f"STAGE_{stage.value}",
            f"CANDIDATE_{selected.action_key.upper().replace('.', '_')}",
        )
        action = TeachingActionV03(
            action_id=action_id,
            learning_objective_ref=context.learning_objective_ref,
            learning_activity_ref=context.learning_activity_ref,
            strategy_family=selected.strategy_family,
            strategy_version=bundle.candidate_table_version,
            teaching_stage=stage,
            interaction_moves=selected.interaction_moves,
            action_modifiers=selected.action_modifiers,
            scaffold_control=selected.scaffold_control,
            hint_specificity=selected.hint_specificity,
            answer_exposure=selected.answer_exposure,
            evidence_requirements=selected.evidence_requirements,
            expected_evidence_type=selected.expected_evidence_type,
            success_condition=selected.success_condition,
            failure_condition=selected.failure_condition,
            max_attempts=selected.max_attempts,
            validation_obligation=validation_obligation,
            reason_codes=reason_codes,
            policy_bundle_ref=validated.bundle_ref,
            teaching_context_ref=validated.context_ref,
            decision_id=decision_id,
            created_at=context.decision_time,
        )

        flat_features = tuple(
            DecisionFeatureV03(
                feature_name=f"{feature_set.action_key}:{feature.feature_name}",
                value=feature.value,
                availability=feature.availability,
                confidence=feature.confidence,
                feature_version=feature.feature_version,
                source_refs=feature.source_refs,
            )
            for feature_set in feature_sets
            for feature in feature_set.features
        )
        assignment_ref = context.experiment_assignment_ref
        action_ref = VersionedRef(
            entity_type="teaching_action",
            entity_id=str(action.action_id),
            version=action.action_schema_version,
        )
        trace = DecisionTraceV03(
            decision_id=decision_id,
            decision_type="teaching_action_selection",
            owner_system="teaching_policy",
            decision_time=context.decision_time,
            teaching_context_ref=validated.context_ref,
            teaching_context_schema_version=context.context_schema_version,
            context_fingerprint=context.context_fingerprint,
            context_source_refs=context.source_refs,
            policy_bundle_ref=validated.bundle_ref,
            policy_bundle_hash=bundle.content_digest,
            policy_version=bundle.policy_version,
            strategy_family=selected.strategy_family,
            strategy_version=bundle.candidate_table_version,
            derived_teaching_stage=stage,
            stage_mapper_version=bundle.stage_mapper_version,
            available_actions=tuple(candidate.model_dump(mode="json") for candidate in candidates),
            hard_constraint_results=hard.results,
            hard_filtered_actions=hard.filtered,
            features=flat_features,
            candidate_scores=tuple(
                {
                    **score.model_dump(mode="json"),
                    "features": feature_set.model_dump(mode="json")["features"],
                    "normalization_version": bundle.normalization_version,
                    "weight_profile_version": bundle.weight_profile_version,
                }
                for score, feature_set in zip(scores, feature_sets, strict=True)
            ),
            selected_teaching_action_ref=action_ref,
            previous_teaching_action_ref=context.previous_teaching_action_ref,
            transition_reason_codes=("EXEC009_SINGLE_DECISION_KERNEL",),
            material_evidence_refs=context.previous_action_outcome_refs,
            anti_oscillation_decision=None,
            tie_break_reason=tie_break_reason,
            experiment_assignment_ref=assignment_ref,
            experiment_assignment_probability=(
                assignment.assignment_probability if assignment is not None else None
            ),
            behavior_policy_type=BehaviorPolicyType.DETERMINISTIC,
            action_propensity=None,
            algorithm=DecisionAlgorithm(
                algorithm_id=self.algorithm_id,
                algorithm_version=self.algorithm_version,
                model_inference_ids=[],
                prompt_versions=[],
            ),
            reason_codes=reason_codes,
            replayability_status=ReplayabilityStatus.FULL,
            replayability_reason_codes=("EXACT_CONTEXT_AND_POLICY_PROFILE",),
            correlation_id=context.context_id,
            trace_id=f"policy:{decision_id}",
            created_at=context.decision_time,
        )
        return PolicyDecision(action=action, trace=trace)

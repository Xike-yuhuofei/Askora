"""Sequential transition and anti-oscillation layer for EXEC-010."""

from __future__ import annotations

import json
from uuid import NAMESPACE_URL, UUID, uuid5

from app.contracts.adaptive import (
    ExperimentAssignmentV03,
    PolicyBundleV03,
    TeachingActionV03,
    TeachingContextV03,
    ValidationObligation,
    VersionedRef,
)
from app.contracts.decisions import DecisionFeatureV03, DecisionTraceV03
from app.domains.teaching_policy.candidates import candidate_key_for_action, candidate_table
from app.domains.teaching_policy.evidence import (
    ClassifiedEvidence,
    EvidenceSignal,
    EvidenceSignalKind,
    classify_material_evidence,
)
from app.domains.teaching_policy.features import build_candidate_features
from app.domains.teaching_policy.kernel import TeachingPolicyKernel
from app.domains.teaching_policy.models import (
    PolicyDecision,
    PolicyDecisionError,
    PolicyFailureCode,
    PolicyRuntimeProfile,
    SequentialPolicyDecision,
    SequentialPolicyState,
    ValidationObligationStatus,
)
from app.domains.teaching_policy.scoring import score_candidate
from app.domains.teaching_policy.time_source import TimeSource

SIGNAL_PRIORITY_NAME = {
    EvidenceSignalKind.ASSESSMENT_RESULT: "ASSESSMENT_RESULT",
    EvidenceSignalKind.INDEPENDENT_ATTEMPT: "INDEPENDENT_ATTEMPT",
    EvidenceSignalKind.DIAGNOSTIC_PROBE: "DIAGNOSTIC_PROBE",
    EvidenceSignalKind.LEARNER_STATE_UPDATE: "LEARNER_STATE_UPDATE",
    EvidenceSignalKind.EXPLICIT_USER_REQUEST: "EXPLICIT_USER_REQUEST",
    EvidenceSignalKind.PREREQUISITE_EVIDENCE: "PREREQUISITE_EVIDENCE",
    EvidenceSignalKind.ASSISTANCE_EVENT: "ASSISTANCE_EVENT",
    EvidenceSignalKind.REVIEW_DELAY_TRANSITION: "MEANINGFUL_REVIEW_DELAY",
}


def _stable_uuid(kind: str, payload: dict[str, object]) -> UUID:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return uuid5(NAMESPACE_URL, f"askora:v0.3:sequential:{kind}:{canonical}")


def _priority_reason(
    classified: tuple[ClassifiedEvidence, ...], profile: PolicyRuntimeProfile
) -> str:
    present = {
        SIGNAL_PRIORITY_NAME[item.kind]
        for item in classified
        if item.material and item.kind in SIGNAL_PRIORITY_NAME
    }
    for name in profile.transition_priority:
        if name in present:
            return f"TRANSITION_{name}"
    return "TRANSITION_MATERIAL_EVIDENCE"


def _exact_previous_ref(context: TeachingContextV03, previous: TeachingActionV03) -> None:
    ref = context.previous_teaching_action_ref
    if (
        ref is None
        or ref.entity_type != "teaching_action"
        or ref.entity_id != str(previous.action_id)
        or str(ref.version) != previous.action_schema_version
    ):
        raise PolicyDecisionError(
            PolicyFailureCode.INVALID_CONTEXT,
            "sequential decision requires exact previous TeachingAction ref",
        )


def _held_decision(
    *,
    proposed: PolicyDecision,
    context: TeachingContextV03,
    bundle: PolicyBundleV03,
    profile: PolicyRuntimeProfile,
    state: SequentialPolicyState,
    previous_key: str,
    anti: dict[str, object],
    transition_reason: str,
) -> PolicyDecision:
    previous = state.previous_action
    semantic: dict[str, object] = {
        "context": str(context.context_id),
        "fingerprint": context.context_fingerprint,
        "bundle": bundle.bundle_id,
        "version": bundle.policy_version,
        "held": previous_key,
        "reason": transition_reason,
    }
    decision_id = _stable_uuid("decision", semantic)
    action_id = _stable_uuid("action", {**semantic, "decision": str(decision_id)})
    obligation_required = (
        state.validation_obligation is not None
        and state.validation_obligation.status is ValidationObligationStatus.REQUIRED
    )
    action_payload = previous.model_dump()
    action_payload.update(
        {
            "action_id": action_id,
            "learning_objective_ref": context.learning_objective_ref,
            "learning_activity_ref": context.learning_activity_ref,
            "strategy_version": bundle.candidate_table_version,
            "teaching_stage": proposed.trace.derived_teaching_stage,
            "validation_obligation": (
                ValidationObligation.INDEPENDENT_VALIDATION_REQUIRED
                if obligation_required
                else previous.validation_obligation
            ),
            "reason_codes": (*previous.reason_codes, transition_reason),
            "policy_bundle_ref": proposed.action.policy_bundle_ref,
            "teaching_context_ref": proposed.action.teaching_context_ref,
            "decision_id": decision_id,
            "created_at": context.decision_time,
        }
    )
    action = TeachingActionV03.model_validate(action_payload)

    stage = proposed.trace.derived_teaching_stage
    if stage is None:
        raise PolicyDecisionError(
            PolicyFailureCode.UNSUPPORTED_CONFIGURATION,
            "proposed policy trace is missing derived TeachingStage",
        )

    table_entry = next(
        candidate for candidate in candidate_table() if candidate.action_key == previous_key
    )
    feature_set = build_candidate_features(
        context,
        stage,
        table_entry,
        profile,
    )
    previous_score = score_candidate(feature_set, profile)
    available = list(proposed.trace.available_actions)
    if not any(item.get("action_key") == previous_key for item in available):
        available.append(table_entry.model_dump(mode="json"))
    scores = list(proposed.trace.candidate_scores)
    if not any(item.get("action_key") == previous_key for item in scores):
        scores.append(
            {
                **previous_score.model_dump(mode="json"),
                "features": feature_set.model_dump(mode="json")["features"],
                "normalization_version": bundle.normalization_version,
                "weight_profile_version": bundle.weight_profile_version,
            }
        )
    features = list(proposed.trace.features)
    if not any(feature.feature_name.startswith(f"{previous_key}:") for feature in features):
        features.extend(
            DecisionFeatureV03(
                feature_name=f"{previous_key}:{feature.feature_name}",
                value=feature.value,
                availability=feature.availability,
                confidence=feature.confidence,
                feature_version=feature.feature_version,
                source_refs=feature.source_refs,
            )
            for feature in feature_set.features
        )
    trace_payload = proposed.trace.model_dump()
    trace_payload.update(
        {
            "decision_id": decision_id,
            "strategy_family": action.strategy_family,
            "available_actions": tuple(available),
            "features": tuple(features),
            "candidate_scores": tuple(scores),
            "selected_teaching_action_ref": VersionedRef(
                entity_type="teaching_action",
                entity_id=str(action.action_id),
                version=action.action_schema_version,
            ),
            "transition_reason_codes": (transition_reason,),
            "anti_oscillation_decision": anti,
            "tie_break_reason": f"{profile.tie_break_version}:anti_oscillation_hold_previous_legal",
            "reason_codes": (*proposed.trace.reason_codes, transition_reason),
            "trace_id": f"policy:{decision_id}",
        }
    )
    return PolicyDecision(action=action, trace=DecisionTraceV03.model_validate(trace_payload))


class SequentialTeachingPolicy:
    def __init__(self, time_source: TimeSource, kernel: TeachingPolicyKernel | None = None) -> None:
        self._time_source = time_source
        self._kernel = kernel or TeachingPolicyKernel()

    def decide(
        self,
        *,
        context: TeachingContextV03,
        bundle: PolicyBundleV03,
        profile: PolicyRuntimeProfile,
        state: SequentialPolicyState,
        signals: tuple[EvidenceSignal, ...] = (),
        assignment: ExperimentAssignmentV03 | None = None,
        time_source: TimeSource | None = None,
    ) -> SequentialPolicyDecision:
        _exact_previous_ref(context, state.previous_action)
        proposed = self._kernel.decide(
            context=context,
            bundle=bundle,
            profile=profile,
            assignment=assignment,
        )
        previous_key = candidate_key_for_action(state.previous_action)
        proposed_key = candidate_key_for_action(proposed.action)
        if previous_key is None or proposed_key is None:
            raise PolicyDecisionError(
                PolicyFailureCode.UNSUPPORTED_CONFIGURATION,
                "previous/proposed action is outside the closed candidate table",
            )
        stage = proposed.trace.derived_teaching_stage
        if stage is None:
            raise PolicyDecisionError(
                PolicyFailureCode.UNSUPPORTED_CONFIGURATION,
                "proposed policy trace is missing derived TeachingStage",
            )

        active_time_source = time_source or self._time_source
        now = active_time_source.now()
        classified = classify_material_evidence(signals, profile, now)
        material_keys = {
            ":".join(
                (
                    item.kind.value,
                    item.evidence_ref.entity_type,
                    item.evidence_ref.entity_id,
                    str(item.evidence_ref.version),
                )
            )
            for item in classified
            if item.material and item.evidence_ref is not None
        }
        new_material_keys = material_keys - set(state.observed_material_evidence_keys)
        new_opportunities = len(new_material_keys)
        total_opportunities = state.evidence_opportunities_since_transition + new_opportunities
        filtered = {
            item.action_ref: item.filter_reason_codes
            for item in proposed.trace.hard_filtered_actions
        }
        previous_hard_forbidden = previous_key in filtered
        repeated_failure = (
            isinstance(context.assistance_history_summary.get("consecutive_failures"), int)
            and context.assistance_history_summary.get("consecutive_failures", 0)
            >= profile.failure_ceiling
        )
        explicit_request = any(
            item.material and item.kind is EvidenceSignalKind.EXPLICIT_USER_REQUEST
            for item in classified
        )

        previous_candidate = next(
            candidate for candidate in candidate_table() if candidate.action_key == previous_key
        )
        previous_features = build_candidate_features(
            context,
            stage,
            previous_candidate,
            profile,
        )
        previous_score = score_candidate(previous_features, profile).total_score
        proposed_score = next(
            float(item["total_score"])
            for item in proposed.trace.candidate_scores
            if item["action_key"] == proposed_key
        )
        score_delta = round(proposed_score - previous_score, 12)

        if previous_hard_forbidden:
            should_switch = True
            transition_reason = (
                "TRANSITION_HARD_CONSTRAINT_REPEATED_FAILURE_OVERRIDE"
                if repeated_failure
                else "TRANSITION_HARD_CONSTRAINT_PRECEDENCE"
            )
        elif repeated_failure:
            should_switch = proposed_key != previous_key
            transition_reason = "TRANSITION_REPEATED_FAILURE_OVERRIDE"
        elif not any(item.material for item in classified):
            should_switch = False
            transition_reason = "HOLD_NO_MATERIAL_EVIDENCE"
        elif explicit_request:
            should_switch = proposed_key != previous_key
            transition_reason = "TRANSITION_EXPLICIT_USER_REQUEST"
        elif total_opportunities < profile.minimum_dwell_opportunities:
            should_switch = False
            transition_reason = "HOLD_MINIMUM_DWELL_EVIDENCE_OPPORTUNITY"
        elif proposed_key == previous_key:
            should_switch = False
            transition_reason = "HOLD_SAME_LEGAL_CANDIDATE"
        elif score_delta < profile.switch_margin:
            should_switch = False
            transition_reason = "HOLD_HYSTERESIS_SWITCH_MARGIN"
        else:
            should_switch = True
            transition_reason = _priority_reason(classified, profile)

        material_refs = tuple(
            item.evidence_ref
            for item in classified
            if item.material and item.evidence_ref is not None
        )
        anti: dict[str, object] = {
            "profile_version": bundle.anti_oscillation_profile_version,
            "decision": "SWITCH" if should_switch else "HOLD",
            "reason_code": transition_reason,
            "previous_action_key": previous_key,
            "proposed_action_key": proposed_key,
            "material_evidence": [item.model_dump(mode="json") for item in classified],
            "evidence_opportunities_since_transition": total_opportunities,
            "minimum_dwell_opportunities": profile.minimum_dwell_opportunities,
            "score_delta": score_delta,
            "switch_margin": profile.switch_margin,
            "fixed_decision_time": now.isoformat(),
        }
        if should_switch:
            trace_payload = proposed.trace.model_dump()
            trace_payload.update(
                {
                    "transition_reason_codes": (transition_reason,),
                    "material_evidence_refs": material_refs,
                    "anti_oscillation_decision": anti,
                    "reason_codes": (*proposed.trace.reason_codes, transition_reason),
                }
            )
            decision = PolicyDecision(
                action=proposed.action,
                trace=DecisionTraceV03.model_validate(trace_payload),
            )
        else:
            decision = _held_decision(
                proposed=proposed,
                context=context,
                bundle=bundle,
                profile=profile,
                state=state,
                previous_key=previous_key,
                anti=anti,
                transition_reason=transition_reason,
            )
            trace_payload = decision.trace.model_dump()
            trace_payload["material_evidence_refs"] = material_refs
            decision = PolicyDecision(
                action=decision.action,
                trace=DecisionTraceV03.model_validate(trace_payload),
            )

        next_state = SequentialPolicyState(
            previous_action=decision.action,
            previous_trace=decision.trace,
            evidence_opportunities_since_transition=0 if should_switch else total_opportunities,
            observed_material_evidence_keys=(
                ()
                if should_switch
                else tuple(sorted(set(state.observed_material_evidence_keys) | material_keys))
            ),
            validation_obligation=state.validation_obligation,
        )
        return SequentialPolicyDecision(
            decision=decision,
            next_state=next_state,
            transition_reason_code=transition_reason,
        )

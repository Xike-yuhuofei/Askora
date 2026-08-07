"""Additive outcome attribution and metric hierarchy; no ninth truth owner."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from app.contracts.adaptive import (
    AttributionScope,
    ExperimentAssignmentV03,
    LearningTrajectoryV03,
    OutcomeObservationV03,
    TeachingEpisodeV03,
    VersionedRef,
)
from app.contracts.base import ContractModel


class OutcomeMetricTier(StrEnum):
    PRIMARY_LEARNING = "PRIMARY_LEARNING"
    PROCESS_EXPERIENCE = "PROCESS_EXPERIENCE"


PRIMARY_LEARNING_OUTCOMES = frozenset(
    {
        "NO_HINT_INDEPENDENT_SUCCESS",
        "DELAYED_INDEPENDENT_PERFORMANCE",
        "INDEPENDENT_TRANSFER",
        "UNIT_TIME_CAPABILITY_GAIN",
    }
)
PROCESS_EXPERIENCE_METRICS = frozenset(
    {
        "ENGAGEMENT",
        "CONVERSATION_TURNS",
        "LIKES",
        "HINT_COUNT",
        "TOKENS",
        "SESSION_DURATION",
    }
)


def metric_tier(metric_name: str) -> OutcomeMetricTier:
    if metric_name in PRIMARY_LEARNING_OUTCOMES:
        return OutcomeMetricTier.PRIMARY_LEARNING
    if metric_name in PROCESS_EXPERIENCE_METRICS:
        return OutcomeMetricTier.PROCESS_EXPERIENCE
    raise ValueError(f"UNKNOWN_OUTCOME_METRIC:{metric_name}")


class ExperimentAnalysisEligibility(ContractModel):
    assignment_ref: VersionedRef
    analysis_plan_ref: VersionedRef
    assignment_integrity_verified: bool
    analysis_unit_eligible: bool
    outcome_definition_pre_registered: bool
    reason_codes: tuple[str, ...] = Field(min_length=1)


class OutcomeAttributionProfile(ContractModel):
    profile_version: str = Field(min_length=1)
    meaningful_delay_seconds: int = Field(ge=0)


class ValidatedOutcomeObservation(ContractModel):
    outcome: OutcomeObservationV03
    attribution_validation_version: str
    reason_codes: tuple[str, ...] = Field(min_length=1)


class OutcomeAttributionValidator:
    """Fail closed on last-touch and unsupported causal attribution."""

    def validate(
        self,
        *,
        outcome: OutcomeObservationV03,
        profile: OutcomeAttributionProfile,
        episode: TeachingEpisodeV03 | None = None,
        trajectory: LearningTrajectoryV03 | None = None,
        assignment: ExperimentAssignmentV03 | None = None,
        experiment_eligibility: ExperimentAnalysisEligibility | None = None,
    ) -> ValidatedOutcomeObservation:
        scope = outcome.attribution_scope
        reasons = [profile.profile_version]
        if episode is not None and outcome.teaching_episode_ref is not None:
            if (
                outcome.teaching_episode_ref.entity_id != str(episode.episode_id)
                or str(outcome.teaching_episode_ref.version) != episode.episode_schema_version
            ):
                raise ValueError("OUTCOME_EPISODE_REF_MISMATCH")
        if trajectory is not None and outcome.learning_trajectory_ref is not None:
            if (
                outcome.learning_trajectory_ref.entity_id != str(trajectory.trajectory_id)
                or str(outcome.learning_trajectory_ref.version)
                != trajectory.trajectory_schema_version
            ):
                raise ValueError("OUTCOME_TRAJECTORY_REF_MISMATCH")
        if scope is AttributionScope.ACTION_DIRECT:
            if episode is None or outcome.teaching_episode_ref is None:
                raise ValueError("ACTION_DIRECT_REQUIRES_EPISODE")
            if len(episode.teaching_action_refs) != 1:
                raise ValueError("ACTION_DIRECT_REQUIRES_SINGLE_ACTION_EPISODE")
            if (
                outcome.actual_delay_seconds is not None
                and outcome.actual_delay_seconds >= profile.meaningful_delay_seconds
            ):
                raise ValueError("DELAYED_OUTCOME_CANNOT_DEFAULT_LAST_TOUCH")
            reasons.append("ACTION_DIRECT_SINGLE_ACTION_BOUNDARY")
        elif scope is AttributionScope.EPISODE_ASSOCIATED:
            if episode is None or outcome.teaching_episode_ref is None:
                raise ValueError("EPISODE_ASSOCIATION_REQUIRES_EXACT_EPISODE")
            reasons.append("EPISODE_ASSOCIATION_ONLY_NOT_CAUSAL")
        elif scope is AttributionScope.TRAJECTORY_ASSOCIATED:
            if trajectory is None or outcome.learning_trajectory_ref is None:
                raise ValueError("TRAJECTORY_ASSOCIATION_REQUIRES_EXACT_TRAJECTORY")
            reasons.append("TRAJECTORY_ASSOCIATION_ONLY_NOT_CAUSAL")
        elif scope is AttributionScope.EXPERIMENTALLY_CAUSAL:
            if assignment is None or experiment_eligibility is None:
                raise ValueError("CAUSAL_ATTRIBUTION_REQUIRES_EXPERIMENT_ELIGIBILITY")
            association = outcome.experiment_association
            if (
                association is None
                or association.entity_id != str(assignment.assignment_id)
                or experiment_eligibility.assignment_ref != association
            ):
                raise ValueError("CAUSAL_ATTRIBUTION_ASSIGNMENT_MISMATCH")
            if not (
                experiment_eligibility.assignment_integrity_verified
                and experiment_eligibility.analysis_unit_eligible
                and experiment_eligibility.outcome_definition_pre_registered
            ):
                raise ValueError("CAUSAL_ATTRIBUTION_IDENTIFICATION_NOT_MET")
            reasons.append("EXPERIMENT_IDENTIFICATION_EVIDENCE_VERIFIED")
        else:
            reasons.append("OUTCOME_UNATTRIBUTABLE")

        supplied_assistance = (
            outcome.assistance_state,
            outcome.scaffold_control,
            outcome.hint_specificity,
            outcome.answer_exposure,
        )
        if any(value is not None for value in supplied_assistance) and any(
            value is None for value in supplied_assistance
        ):
            raise ValueError("OUTCOME_ACTUAL_ASSISTANCE_AXES_INCOMPLETE")
        return ValidatedOutcomeObservation(
            outcome=outcome,
            attribution_validation_version=profile.profile_version,
            reason_codes=tuple(reasons),
        )

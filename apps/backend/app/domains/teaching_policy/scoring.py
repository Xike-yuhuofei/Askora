"""Normalized weighted soft scoring and stable deterministic tie-break."""

from __future__ import annotations

from app.domains.teaching_policy.features import normalize_feature
from app.domains.teaching_policy.models import (
    CandidateFeatureSet,
    CandidateScore,
    PolicyDecisionError,
    PolicyFailureCode,
    PolicyRuntimeProfile,
)


def score_candidate(
    feature_set: CandidateFeatureSet, profile: PolicyRuntimeProfile
) -> CandidateScore:
    normalized: dict[str, float | None] = {}
    components: dict[str, float] = {}
    for feature in feature_set.features:
        value = normalize_feature(feature, profile)
        normalized[feature.feature_name] = value
        weight = profile.feature_weights.get(feature.feature_name)
        if weight is None:
            raise PolicyDecisionError(
                PolicyFailureCode.NORMALIZATION_FAILURE,
                f"missing exact weight for {feature.feature_name}",
            )
        components[feature.feature_name] = round((value or 0.0) * weight, 12)
    return CandidateScore(
        action_key=feature_set.action_key,
        normalized_features=normalized,
        weighted_components=components,
        total_score=round(sum(components.values()), 12),
    )


def select_stably(
    scores: tuple[CandidateScore, ...], profile: PolicyRuntimeProfile
) -> tuple[CandidateScore, str]:
    if not scores:
        raise PolicyDecisionError(
            PolicyFailureCode.NO_LEGAL_CANDIDATE,
            "hard constraints and candidate table produced no legal candidate",
        )
    priority = {key: index for index, key in enumerate(profile.candidate_priority)}
    missing = sorted(score.action_key for score in scores if score.action_key not in priority)
    if missing:
        raise PolicyDecisionError(
            PolicyFailureCode.TIE_BREAK_CONFIGURATION_FAILURE,
            f"candidate priority missing action keys: {','.join(missing)}",
        )
    selected = sorted(
        scores, key=lambda score: (-score.total_score, priority[score.action_key], score.action_key)
    )[0]
    tied = [score for score in scores if score.total_score == selected.total_score]
    reason = (
        f"{profile.tie_break_version}:score_then_candidate_priority_then_action_key"
        if len(tied) > 1
        else f"{profile.tie_break_version}:unique_max_score"
    )
    return selected, reason

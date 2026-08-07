"""EXEC-008 nine migration-candidate executable fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.contracts import (
    BehaviorPolicyType,
    MigrationCandidate,
    ReplayabilityStatus,
    upcast_v03_compatibility,
)

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "v03_migration"
FIXTURES = tuple(sorted(FIXTURE_DIR.glob("*.json")))


@pytest.mark.parametrize("fixture_path", FIXTURES, ids=lambda path: path.stem)
def test_all_nine_migration_candidates_are_explicit_and_idempotent(
    fixture_path: Path,
) -> None:
    """EXEC008-AC-008/010/011, TEST-290/291."""
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    first = upcast_v03_compatibility(fixture["candidate"], fixture["payload"])
    second = upcast_v03_compatibility(fixture["candidate"], fixture["payload"])

    assert first.model_dump(mode="json") == second.model_dump(mode="json")
    assert first.canonical_target == fixture["expected_target"]
    assert first.replayability_status.value == fixture["expected_replayability"]
    assert first.ambiguous is fixture["expected_ambiguous"]
    assert fixture["expected_reason"] in first.reason_codes
    assert first.compatibility_behavior
    assert first.retirement_condition
    assert first.raw_legacy_payload == fixture["payload"]


def test_fixture_register_contains_exactly_the_nine_frozen_candidates() -> None:
    """EXEC008-AC-008: no migration candidate is silently omitted."""
    fixtures = {json.loads(path.read_text(encoding="utf-8"))["candidate"] for path in FIXTURES}
    assert fixtures == {candidate.value for candidate in MigrationCandidate}
    assert len(FIXTURES) == 9


def test_ambiguous_integer_axes_never_guess_canonical_support_values() -> None:
    """DOMAIN-121/TEST-290: unspecified integer mappings remain unavailable."""
    for candidate, payload in (
        (MigrationCandidate.OLD_SCAFFOLD_LEVEL, {"scaffold_level": 2}),
        (MigrationCandidate.OLD_HINT_LEVEL, {"hint_level": 4}),
        (MigrationCandidate.OLD_ANSWER_EXPOSURE, {"answer_exposure_max": 3}),
    ):
        projection = upcast_v03_compatibility(candidate, payload)
        assert projection.canonical_payload is not None
        assert projection.canonical_payload["value"] is None
        assert projection.canonical_payload["availability"] == "MISSING"
        assert projection.replayability_status is ReplayabilityStatus.PARTIAL


def test_ambiguous_legacy_propensity_is_null_unknown_and_partial() -> None:
    """EXEC008-AC-007/008, DECISION-212/TEST-291."""
    projection = upcast_v03_compatibility(
        MigrationCandidate.OLD_DECISION_PROPENSITY, {"propensity": 0.5}
    )
    assert projection.canonical_payload is not None
    assert projection.canonical_payload["assignment_probability"] is None
    assert projection.canonical_payload["action_propensity"] is None
    assert projection.canonical_payload["behavior_policy_type"] == BehaviorPolicyType.UNKNOWN.value
    assert projection.replayability_status is ReplayabilityStatus.PARTIAL
    assert "AMBIGUOUS_LEGACY_PROPENSITY" in projection.reason_codes


def test_historical_replay_never_uses_current_mutable_refs() -> None:
    """EXEC008-AC-011, DECISION-220/221."""
    projection = upcast_v03_compatibility(
        MigrationCandidate.HISTORICAL_REPLAY,
        {"decision_id": "legacy", "teaching_context_ref": None},
    )
    assert projection.replayability_status is ReplayabilityStatus.NON_REPLAYABLE
    assert projection.canonical_payload == {
        "missing_exact_refs": [
            "context_source_refs",
            "policy_bundle_ref",
            "teaching_context_ref",
            "tie_break_version",
        ],
        "online_llm_allowed": False,
    }

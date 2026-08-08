"""ADR-0003 production policy artifact and packaging contract."""

from __future__ import annotations

import json
from pathlib import Path

from app.services.policy_runtime import (
    DEFAULT_POLICY_PROFILE_PATH,
    canonical_policy_profile_digest,
    default_policy_bundle,
    load_policy_runtime_profile,
)

BACKEND_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = BACKEND_ROOT / "tests" / "fixtures" / "v03_policy" / "profile.json"


def test_adr0003_production_profile_has_exact_digest_and_approved_behavior() -> None:
    production_payload = json.loads(DEFAULT_POLICY_PROFILE_PATH.read_text(encoding="utf-8"))
    fixture_payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert production_payload["content_digest"] == canonical_policy_profile_digest(
        production_payload
    )
    for identity_field in ("profile_id", "content_digest"):
        production_payload.pop(identity_field)
        fixture_payload.pop(identity_field)
    assert production_payload == fixture_payload

    profile = load_policy_runtime_profile()
    bundle = default_policy_bundle()
    profile.assert_matches(bundle)
    assert profile.profile_id == "askora-v03-default-1"
    assert bundle.bundle_id == "askora-v03-default-bundle-1"


def test_production_backend_bundle_includes_policy_artifact() -> None:
    spec = (BACKEND_ROOT / "backend.spec").read_text(encoding="utf-8")
    assert "('app/config', 'app/config')" in spec

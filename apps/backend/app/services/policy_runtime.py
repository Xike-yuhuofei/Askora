"""SYS05 production PolicyRuntimeProfile artifacts and active resolution."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.adaptive import PolicyBundleActivationV03, PolicyBundleV03, VersionedRef
from app.domains.teaching_policy import PolicyRuntimeProfile
from app.models.adaptive import PolicyBundleActivationRecord, PolicyBundleRecord

DEFAULT_POLICY_BUNDLE_ID = "askora-v03-default-bundle-1"
DEFAULT_POLICY_ACTIVATION_ID = "130bf2ea-ccc4-5ef1-9dd4-e41449870d0d"
DEFAULT_POLICY_PUBLISHED_AT = datetime(2026, 8, 8, tzinfo=timezone.utc)
DEFAULT_POLICY_PROFILE_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "policy_profiles" / "v03-default.json"
)


class PolicyRuntimeResolutionError(RuntimeError):
    """Typed unsupported-configuration failure; callers must fail closed."""


@dataclass(frozen=True)
class PolicyRuntimeSelection:
    bundle: PolicyBundleV03
    profile: PolicyRuntimeProfile


def canonical_policy_profile_digest(payload: dict[str, Any]) -> str:
    """ADR-0003 canonical digest, excluding the self-referential digest field."""

    canonical_payload = dict(payload)
    canonical_payload.pop("content_digest", None)
    canonical = json.dumps(
        canonical_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def load_policy_runtime_profile(path: Path = DEFAULT_POLICY_PROFILE_PATH) -> PolicyRuntimeProfile:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PolicyRuntimeResolutionError("POLICY_RUNTIME_PROFILE_UNAVAILABLE") from exc
    if not isinstance(payload, dict):
        raise PolicyRuntimeResolutionError("POLICY_RUNTIME_PROFILE_INVALID")
    claimed_digest = payload.get("content_digest")
    if claimed_digest != canonical_policy_profile_digest(payload):
        raise PolicyRuntimeResolutionError("POLICY_RUNTIME_PROFILE_DIGEST_MISMATCH")
    try:
        return PolicyRuntimeProfile.model_validate(payload)
    except ValueError as exc:
        raise PolicyRuntimeResolutionError("POLICY_RUNTIME_PROFILE_INVALID") from exc


def default_policy_bundle() -> PolicyBundleV03:
    profile = load_policy_runtime_profile()
    return PolicyBundleV03(
        bundle_id=DEFAULT_POLICY_BUNDLE_ID,
        policy_version=profile.policy_version,
        hard_rule_set_version=profile.hard_rule_set_version,
        stage_mapper_version=profile.stage_mapper_version,
        candidate_table_version=profile.candidate_table_version,
        feature_schema_version=profile.feature_schema_version,
        normalization_version=profile.normalization_version,
        weight_profile_version=profile.weight_profile_version,
        anti_oscillation_profile_version="anti-1",
        tie_break_version=profile.tie_break_version,
        fallback_profile_version=profile.fallback_profile_version,
        subject_profile_version=None,
        content_digest=profile.content_digest,
        published_at=DEFAULT_POLICY_PUBLISHED_AT,
    )


def default_policy_activation() -> PolicyBundleActivationV03:
    bundle = default_policy_bundle()
    return PolicyBundleActivationV03(
        activation_id=UUID(DEFAULT_POLICY_ACTIVATION_ID),
        bundle_ref=VersionedRef(
            entity_type="PolicyBundle",
            entity_id=bundle.bundle_id,
            version=bundle.policy_version,
        ),
        activated_at=DEFAULT_POLICY_PUBLISHED_AT,
        reason_codes=("ADR_0003_DEFAULT_BOOTSTRAP",),
    )


class ActivePolicyRuntimeResolver:
    """Resolve the stable latest activation to one exact immutable runtime."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def resolve(self) -> PolicyRuntimeSelection:
        activation = await self._db.scalar(
            select(PolicyBundleActivationRecord).order_by(
                PolicyBundleActivationRecord.activated_at.desc(),
                PolicyBundleActivationRecord.activation_id.desc(),
            )
        )
        if activation is None:
            raise PolicyRuntimeResolutionError("POLICY_RUNTIME_PROFILE_UNAVAILABLE")
        bundle_record = await self._db.get(PolicyBundleRecord, activation.bundle_id)
        if bundle_record is None:
            raise PolicyRuntimeResolutionError("POLICY_RUNTIME_BUNDLE_MISSING")
        try:
            bundle = PolicyBundleV03.model_validate(bundle_record.payload)
        except ValueError as exc:
            raise PolicyRuntimeResolutionError("POLICY_RUNTIME_BUNDLE_INVALID") from exc
        if (
            bundle.bundle_id != bundle_record.bundle_id
            or bundle.policy_version != bundle_record.policy_version
            or bundle.content_digest != bundle_record.content_digest
        ):
            raise PolicyRuntimeResolutionError("POLICY_RUNTIME_BUNDLE_RECORD_MISMATCH")
        profile = load_policy_runtime_profile()
        try:
            profile.assert_matches(bundle)
        except ValueError as exc:
            raise PolicyRuntimeResolutionError("POLICY_RUNTIME_PROFILE_BUNDLE_MISMATCH") from exc
        return PolicyRuntimeSelection(bundle=bundle, profile=profile)

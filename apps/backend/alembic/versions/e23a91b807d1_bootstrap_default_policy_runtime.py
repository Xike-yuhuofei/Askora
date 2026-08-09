"""bootstrap the first production PolicyBundle and atomic activation

Revision ID: e23a91b807d1
Revises: c22d05a8e101
Create Date: 2026-08-08 23:00:00.000000

Forward strategy: insert one deterministic immutable PolicyBundle and activation
whose digest is pinned to the ADR-0003 repository artifact. Existing rows are
accepted only when their immutable content is exactly identical.

Rollback strategy: remove only the deterministic seed rows on an unused
database. If a TeachingAction or later activation depends on the seed, fail
closed and require a forward-fix so historical policy provenance is retained.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import sqlalchemy as sa

from alembic import op

revision = "e23a91b807d1"
down_revision = "c22d05a8e101"
branch_labels = None
depends_on = None

BUNDLE_ID = "askora-v03-default-bundle-1"
ACTIVATION_ID = "130bf2ea-ccc4-5ef1-9dd4-e41449870d0d"
CONTENT_DIGEST = "sha256:a8ca56385d9c6f13ff7e10c4738f93baf034bf705f5ab537f2bcd2be2061898b"
PUBLISHED_AT = datetime(2026, 8, 8, tzinfo=timezone.utc)

BUNDLE_PAYLOAD: dict[str, Any] = {
    "bundle_id": BUNDLE_ID,
    "schema_version": "3.0",
    "policy_version": "policy-1",
    "hard_rule_set_version": "hard-1",
    "stage_mapper_version": "stage-1",
    "candidate_table_version": "candidates-1",
    "feature_schema_version": "features-1",
    "normalization_version": "fixed-bounds-1",
    "weight_profile_version": "weights-1",
    "anti_oscillation_profile_version": "anti-1",
    "tie_break_version": "tie-1",
    "fallback_profile_version": "fallback-1",
    "subject_profile_version": None,
    "content_digest": CONTENT_DIGEST,
    "published_at": "2026-08-08T00:00:00Z",
}


def _tables() -> tuple[sa.TableClause, sa.TableClause, sa.TableClause]:
    bundles = sa.table(
        "policy_bundles",
        sa.column("bundle_id", sa.String),
        sa.column("schema_version", sa.String),
        sa.column("policy_version", sa.String),
        sa.column("content_digest", sa.String),
        sa.column("payload", sa.JSON),
        sa.column("published_at", sa.DateTime(timezone=True)),
    )
    activations = sa.table(
        "policy_bundle_activations",
        sa.column("activation_id", sa.String),
        sa.column("bundle_id", sa.String),
        sa.column("activated_at", sa.DateTime(timezone=True)),
        sa.column("supersedes_activation_id", sa.String),
        sa.column("reason_codes", sa.JSON),
    )
    actions = sa.table(
        "teaching_action_versions",
        sa.column("action_id", sa.String),
        sa.column("policy_bundle_id", sa.String),
    )
    return bundles, activations, actions


def upgrade() -> None:
    bind = op.get_bind()
    bundles, activations, _actions = _tables()
    existing_bundle = bind.execute(
        sa.select(bundles).where(
            sa.or_(
                bundles.c.bundle_id == BUNDLE_ID,
                bundles.c.policy_version == BUNDLE_PAYLOAD["policy_version"],
                bundles.c.content_digest == CONTENT_DIGEST,
            )
        )
    ).mappings().first()
    if existing_bundle is None:
        bind.execute(
            bundles.insert().values(
                bundle_id=BUNDLE_ID,
                schema_version="3.0",
                policy_version="policy-1",
                content_digest=CONTENT_DIGEST,
                payload=BUNDLE_PAYLOAD,
                published_at=PUBLISHED_AT,
            )
        )
    elif not (
        existing_bundle["bundle_id"] == BUNDLE_ID
        and existing_bundle["schema_version"] == "3.0"
        and existing_bundle["policy_version"] == "policy-1"
        and existing_bundle["content_digest"] == CONTENT_DIGEST
        and existing_bundle["payload"] == BUNDLE_PAYLOAD
    ):
        raise RuntimeError("DEFAULT_POLICY_BUNDLE_IMMUTABLE_CONFLICT")

    existing_activation = bind.execute(
        sa.select(activations).where(activations.c.activation_id == ACTIVATION_ID)
    ).mappings().first()
    if existing_activation is None:
        bind.execute(
            activations.insert().values(
                activation_id=ACTIVATION_ID,
                bundle_id=BUNDLE_ID,
                activated_at=PUBLISHED_AT,
                supersedes_activation_id=None,
                reason_codes=["ADR_0003_DEFAULT_BOOTSTRAP"],
            )
        )
    elif not (
        existing_activation["bundle_id"] == BUNDLE_ID
        and existing_activation["supersedes_activation_id"] is None
        and existing_activation["reason_codes"] == ["ADR_0003_DEFAULT_BOOTSTRAP"]
    ):
        raise RuntimeError("DEFAULT_POLICY_ACTIVATION_IMMUTABLE_CONFLICT")


def downgrade() -> None:
    bind = op.get_bind()
    bundles, activations, actions = _tables()
    action_count = bind.scalar(
        sa.select(sa.func.count()).select_from(actions).where(
            actions.c.policy_bundle_id == BUNDLE_ID
        )
    )
    dependent_activation_count = bind.scalar(
        sa.select(sa.func.count()).select_from(activations).where(
            sa.or_(
                activations.c.supersedes_activation_id == ACTIVATION_ID,
                sa.and_(
                    activations.c.bundle_id == BUNDLE_ID,
                    activations.c.activation_id != ACTIVATION_ID,
                ),
            )
        )
    )
    if action_count or dependent_activation_count:
        raise RuntimeError("DEFAULT_POLICY_RUNTIME_IN_USE_FORWARD_FIX_REQUIRED")
    bind.execute(activations.delete().where(activations.c.activation_id == ACTIVATION_ID))
    bind.execute(bundles.delete().where(bundles.c.bundle_id == BUNDLE_ID))

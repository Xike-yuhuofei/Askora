"""add P1-01A goal definition, state, draft, preview and focus

Revision ID: d2f1010a37a1
Revises: f1061a0b9c01
Create Date: 2026-08-09 14:05:00.000000
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict

import sqlalchemy as sa
from alembic import op

revision = "d2f1010a37a1"
down_revision = "f1061a0b9c01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # App startup may have called Base.metadata.create_all before Alembic. The
    # matching-table path is safe because autogenerate parity is enforced below.
    existing_tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "learning_goal_definition_versions" in existing_tables:
        _backfill_legacy()
        return
    op.create_table(
        "learning_goal_definition_versions",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("goal_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("definition_version", sa.Integer(), nullable=False),
        sa.Column("semantic_fingerprint", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("goal_id", "definition_version", name="uq_goal_definition_version"),
    )
    op.create_index(
        "ix_learning_goal_definition_versions_goal_id",
        "learning_goal_definition_versions",
        ["goal_id"],
    )
    op.create_index(
        "ix_learning_goal_definition_versions_user_id",
        "learning_goal_definition_versions",
        ["user_id"],
    )
    op.create_index(
        "ix_learning_goal_definition_versions_semantic_fingerprint",
        "learning_goal_definition_versions",
        ["semantic_fingerprint"],
    )
    op.create_table(
        "learning_goal_state_versions",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("goal_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("state_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("definition_version", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("goal_id", "state_version", name="uq_goal_state_version"),
    )
    op.create_index(
        "ix_learning_goal_state_versions_goal_id", "learning_goal_state_versions", ["goal_id"]
    )
    op.create_index(
        "ix_learning_goal_state_versions_user_id", "learning_goal_state_versions", ["user_id"]
    )
    op.create_index(
        "ix_learning_goal_state_versions_status", "learning_goal_state_versions", ["status"]
    )
    op.create_table(
        "learning_plan_state_versions",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("plan_id", sa.String(36), nullable=False),
        sa.Column("plan_version", sa.Integer(), nullable=False),
        sa.Column("state_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "plan_id", "plan_version", "state_version", name="uq_goal_plan_state_version"
        ),
    )
    op.create_index(
        "ix_learning_plan_state_versions_plan_id", "learning_plan_state_versions", ["plan_id"]
    )
    op.create_index(
        "ix_learning_plan_state_versions_status", "learning_plan_state_versions", ["status"]
    )
    op.create_table(
        "learning_goal_draft_versions",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("draft_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("goal_id", sa.String(36), nullable=False),
        sa.Column("draft_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("draft_id", "draft_version", name="uq_goal_draft_version"),
    )
    op.create_index(
        "ix_learning_goal_draft_versions_draft_id", "learning_goal_draft_versions", ["draft_id"]
    )
    op.create_index(
        "ix_learning_goal_draft_versions_user_id", "learning_goal_draft_versions", ["user_id"]
    )
    op.create_index(
        "ix_learning_goal_draft_versions_goal_id", "learning_goal_draft_versions", ["goal_id"]
    )
    op.create_index(
        "ix_learning_goal_draft_versions_status", "learning_goal_draft_versions", ["status"]
    )
    op.create_table(
        "goal_change_preview_versions",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("preview_id", sa.String(36), nullable=False),
        sa.Column("preview_version", sa.Integer(), nullable=False),
        sa.Column("draft_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("preview_id", "preview_version", name="uq_goal_preview_version"),
    )
    op.create_index(
        "ix_goal_change_preview_versions_preview_id", "goal_change_preview_versions", ["preview_id"]
    )
    op.create_index(
        "ix_goal_change_preview_versions_draft_id", "goal_change_preview_versions", ["draft_id"]
    )
    op.create_index(
        "ix_goal_change_preview_versions_user_id", "goal_change_preview_versions", ["user_id"]
    )
    op.create_table(
        "focused_learning_goal_state_versions",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("focus_version", sa.Integer(), nullable=False),
        sa.Column("goal_id", sa.String(36), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("user_id", "focus_version", name="uq_goal_focus_version"),
    )
    op.create_index(
        "ix_focused_learning_goal_state_versions_user_id",
        "focused_learning_goal_state_versions",
        ["user_id"],
    )
    op.create_table(
        "goal_management_command_receipts",
        sa.Column("receipt_id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("command_type", sa.String(60), nullable=False),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("payload_digest", sa.String(64), nullable=False),
        sa.Column("response_type", sa.String(80), nullable=False),
        sa.Column("response_payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("user_id", "idempotency_key", name="uq_goal_management_user_key"),
    )
    op.create_index(
        "ix_goal_management_receipt_command",
        "goal_management_command_receipts",
        ["user_id", "command_type"],
    )
    _backfill_legacy()


def _backfill_legacy() -> None:
    bind = op.get_bind()
    metadata = sa.MetaData()
    goals = sa.Table("learning_goal_versions", metadata, autoload_with=bind)
    plans = sa.Table("learning_plan_versions", metadata, autoload_with=bind)
    definitions = sa.Table("learning_goal_definition_versions", metadata, autoload_with=bind)
    states = sa.Table("learning_goal_state_versions", metadata, autoload_with=bind)
    drafts = sa.Table("learning_goal_draft_versions", metadata, autoload_with=bind)
    plan_states = sa.Table("learning_plan_state_versions", metadata, autoload_with=bind)
    by_goal: dict[str, list[dict]] = defaultdict(list)
    for row in bind.execute(sa.select(goals).order_by(goals.c.goal_id, goals.c.version)).mappings():
        payload = row["payload"] if isinstance(row["payload"], dict) else json.loads(row["payload"])
        by_goal[row["goal_id"]].append({**row, "payload": payload})
    for goal_id, rows in by_goal.items():
        fingerprints: dict[str, int] = {}
        legacy_to_definition: dict[int, int] = {}
        for row in rows:
            payload = row["payload"]
            semantic = {
                key: payload.get(key)
                for key in (
                    "title",
                    "topic",
                    "target_capabilities",
                    "application_context",
                    "success_criteria",
                    "source_document_ids",
                    "deadline_at",
                    "weekly_time_budget_minutes",
                )
            }
            fingerprint = hashlib.sha256(
                json.dumps(semantic, sort_keys=True, separators=(",", ":"), default=str).encode()
            ).hexdigest()
            existing_definition_version = fingerprints.get(fingerprint)
            definition_version = fingerprints.setdefault(fingerprint, len(fingerprints) + 1)
            legacy_to_definition[int(row["version"])] = definition_version
            if existing_definition_version is not None:
                continue
            criteria = [
                {
                    "criterion_id": hashlib.md5(  # noqa: S324 - deterministic migration identity
                        f"{goal_id}:{definition_version}:{index}".encode()
                    ).hexdigest(),
                    "cognitive_process": "explain",
                    "statement": value,
                    "target_refs": [],
                    "evidence_requirements": ["independent_explanation"],
                }
                for index, value in enumerate(payload.get("success_criteria", []))
            ]
            definition_payload = {
                "goal_id": goal_id,
                "definition_schema_version": "2.0",
                "definition_version": definition_version,
                "user_id": row["user_id"],
                **semantic,
                "success_criteria": criteria,
                "semantic_fingerprint": fingerprint,
                "created_at": payload.get("created_at"),
                "supersedes_definition_version": (
                    definition_version - 1 if definition_version > 1 else None
                ),
                "reason_codes": ["LEGACY_GOAL_DEFINITION_BACKFILL"],
            }
            bind.execute(
                definitions.insert().values(
                    id=f"{goal_id}:{definition_version}",
                    goal_id=goal_id,
                    user_id=row["user_id"],
                    definition_version=definition_version,
                    semantic_fingerprint=fingerprint,
                    payload=definition_payload,
                )
            )
        latest = rows[-1]
        payload = latest["payload"]
        definition_version = legacy_to_definition[int(latest["version"])]
        if payload.get("status") == "candidate":
            draft_id = hashlib.md5(f"legacy-draft:{goal_id}".encode()).hexdigest()  # noqa: S324
            bind.execute(
                drafts.insert().values(
                    id=f"{draft_id}:1",
                    draft_id=draft_id,
                    user_id=latest["user_id"],
                    goal_id=goal_id,
                    draft_version=1,
                    status="draft",
                    payload={
                        "draft_id": draft_id,
                        "draft_schema_version": "1.0",
                        "draft_version": 1,
                        "user_id": latest["user_id"],
                        "goal_id": goal_id,
                        "base_definition_version": definition_version,
                        "status": "draft",
                        "title": payload["title"],
                        "topic": payload["topic"],
                        "target_capabilities": payload["target_capabilities"],
                        "application_context": payload.get("application_context"),
                        "deadline_at": payload.get("deadline_at"),
                        "weekly_time_budget_minutes": payload.get("weekly_time_budget_minutes"),
                        "success_criteria": [
                            {
                                "criterion_id": hashlib.md5(  # noqa: S324
                                    f"{goal_id}:draft:{index}".encode()
                                ).hexdigest(),
                                "cognitive_process": "explain",
                                "statement": value,
                                "evidence_requirements": ["independent_explanation"],
                            }
                            for index, value in enumerate(payload["success_criteria"])
                        ],
                        "source_document_ids": payload["source_document_ids"],
                        "selected_target_ids": [],
                        "targets_confirmed": False,
                        "pending_preview_id": None,
                        "block_reason_codes": ["LEGACY_CANDIDATE_BACKFILL"],
                        "created_at": payload["created_at"],
                    },
                )
            )
        else:
            state_payload = {
                "goal_id": goal_id,
                "state_schema_version": "1.0",
                "state_version": 1,
                "status": payload["status"],
                "definition_version": definition_version,
                "mapping_ref": None,
                "plan_ref": None,
                "previous_status": None,
                "reason_codes": ["LEGACY_GOAL_STATE_BACKFILL"],
                "correlation_id": goal_id,
                "created_at": payload["created_at"],
            }
            bind.execute(
                states.insert().values(
                    id=f"{goal_id}:1",
                    goal_id=goal_id,
                    user_id=latest["user_id"],
                    state_version=1,
                    status=payload["status"],
                    definition_version=definition_version,
                    payload=state_payload,
                )
            )
    for row in bind.execute(sa.select(plans)).mappings():
        payload = row["payload"] if isinstance(row["payload"], dict) else json.loads(row["payload"])
        bind.execute(
            plan_states.insert().values(
                id=f"{row['plan_id']}:{row['version']}:1",
                plan_id=row["plan_id"],
                plan_version=row["version"],
                state_version=1,
                status=row["status"],
                payload={
                    "plan_id": row["plan_id"],
                    "plan_version": row["version"],
                    "state_version": 1,
                    "status": row["status"],
                    "previous_status": None,
                    "reason_codes": ["LEGACY_PLAN_STATE_BACKFILL"],
                    "correlation_id": row["plan_id"],
                    "created_at": payload.get("created_at") or row["created_at"],
                },
            )
        )


def downgrade() -> None:
    op.drop_table("goal_management_command_receipts")
    op.drop_table("focused_learning_goal_state_versions")
    op.drop_table("goal_change_preview_versions")
    op.drop_table("learning_goal_draft_versions")
    op.drop_table("learning_plan_state_versions")
    op.drop_table("learning_goal_state_versions")
    op.drop_table("learning_goal_definition_versions")

"""add SYS06 canonical activity lifecycle

Revision ID: e30c06a1b2c3
Revises: a80d4f9c2b61
Create Date: 2026-08-09
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa

from alembic import op

revision: str = "e30c06a1b2c3"
down_revision: str | None = "a80d4f9c2b61"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_STATUSES = {"planned", "available", "active", "completed", "skipped", "superseded"}


def _payload(value: object) -> dict:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        loaded = json.loads(value)
        return loaded if isinstance(loaded, dict) else {}
    return {}


def _utc(value: object) -> datetime:
    if isinstance(value, datetime):
        return value.replace(tzinfo=value.tzinfo or timezone.utc)
    return datetime.now(timezone.utc)


def _backfill() -> None:
    bind = op.get_bind()
    metadata = sa.MetaData()
    activities = sa.Table("learning_activities", metadata, autoload_with=bind)
    plans = sa.Table("learning_plan_versions", metadata, autoload_with=bind)
    goals = sa.Table("learning_goal_versions", metadata, autoload_with=bind)
    events = sa.Table("learning_events", metadata, autoload_with=bind)
    transcripts = sa.Table("book_learning_transcript_turns", metadata, autoload_with=bind)
    states = sa.Table("learning_activity_state_versions", metadata, autoload_with=bind)

    goal_owner: dict[str, str] = {}
    goal_versions: dict[str, int] = {}
    for row in bind.execute(sa.select(goals)).mappings():
        if row["version"] >= goal_versions.get(row["goal_id"], 0):
            goal_versions[row["goal_id"]] = row["version"]
            goal_owner[row["goal_id"]] = row["user_id"]
    plan_goal = {
        (row["plan_id"], row["version"]): row["learning_goal_id"]
        for row in bind.execute(sa.select(plans)).mappings()
    }
    event_rows = list(bind.execute(sa.select(events)).mappings())
    transcript_rows = list(bind.execute(sa.select(transcripts)).mappings())
    existing = {
        row[0]
        for row in bind.execute(sa.select(states.c.activity_id).distinct()).all()
    }

    for row in bind.execute(sa.select(activities)).mappings():
        activity_id = row["id"]
        if activity_id in existing:
            continue
        goal_id = plan_goal.get((row["plan_id"], row["plan_version"]))
        owner_id = goal_owner.get(goal_id or "")
        plan_ref = f"learning_plan:{row['plan_id']}:v{row['plan_version']}"
        completed_event = next(
            (
                item
                for item in event_rows
                if item["event_type"] == "ActivityCompleted"
                and item["aggregate_id"] == activity_id
                and owner_id
                and str(_payload(item["context"]).get("user_id")) == owner_id
                and _payload(item["payload"]).get("plan_ref") == plan_ref
            ),
            None,
        )
        accepted_turn = next(
            (
                item
                for item in reversed(transcript_rows)
                if item["activity_id"] == activity_id and item["user_id"] == owner_id
            ),
            None,
        )
        selected_event = next(
            (
                item
                for item in event_rows
                if item["event_type"] == "ActivitySelected"
                and item["aggregate_id"] == activity_id
                and owner_id
                and str(_payload(item["context"]).get("user_id")) == owner_id
                and _payload(item["payload"]).get("plan_ref") == plan_ref
            ),
            None,
        )
        initial = str(_payload(row["payload"]).get("status", "planned"))
        if completed_event is not None:
            status = "completed"
            reason = "BACKFILL_OWNER_VALID_COMPLETION_EVENT"
            correlation = completed_event["correlation_id"]
            created_at = _utc(completed_event["recorded_at"])
        elif accepted_turn is not None:
            status = "active"
            reason = "BACKFILL_ACCEPTED_CURRENT_USER_TRANSCRIPT"
            correlation = str(
                uuid5(NAMESPACE_URL, f"askora:activity-backfill:{activity_id}:transcript")
            )
            created_at = _utc(accepted_turn["created_at"])
        elif selected_event is not None:
            status = "available"
            reason = "BACKFILL_OWNER_VALID_ACTIVITY_SELECTED"
            correlation = selected_event["correlation_id"]
            created_at = _utc(selected_event["recorded_at"])
        else:
            status = initial if initial in _STATUSES and initial != "completed" else "planned"
            reason = "BACKFILL_IMMUTABLE_INITIAL_STATUS"
            correlation = str(uuid5(NAMESPACE_URL, f"askora:activity-backfill:{activity_id}"))
            created_at = _utc(row["created_at"])
        bind.execute(
            states.insert().values(
                id=f"{activity_id}:1",
                activity_id=activity_id,
                version=1,
                plan_id=row["plan_id"],
                plan_version=row["plan_version"],
                status=status,
                previous_status=None,
                transition_reason=reason,
                source_refs=[],
                actor_type="system",
                started_at=created_at if status == "active" else None,
                completed_at=created_at if status == "completed" else None,
                correlation_id=correlation,
                created_at=created_at,
            )
        )


def _reconcile() -> None:
    """Fail the migration when exact activity/plan coverage is not preserved."""
    bind = op.get_bind()
    metadata = sa.MetaData()
    activities = sa.Table("learning_activities", metadata, autoload_with=bind)
    states = sa.Table("learning_activity_state_versions", metadata, autoload_with=bind)
    activity_refs = {
        row["id"]: (row["plan_id"], row["plan_version"])
        for row in bind.execute(sa.select(activities)).mappings()
    }
    state_refs: dict[str, tuple[str, int]] = {}
    for row in bind.execute(sa.select(states)).mappings():
        expected = activity_refs.get(row["activity_id"])
        actual = (row["plan_id"], row["plan_version"])
        if expected is None or expected != actual:
            raise RuntimeError(
                "activity lifecycle reconciliation failed for "
                f"{row['activity_id']}: expected={expected!r}, actual={actual!r}"
            )
        state_refs[row["activity_id"]] = actual
    missing = sorted(set(activity_refs) - set(state_refs))
    if missing:
        raise RuntimeError(
            "activity lifecycle reconciliation missing states for "
            f"{missing[:10]}"
        )


def upgrade() -> None:
    existing_tables = set(sa.inspect(op.get_bind()).get_table_names())
    lifecycle_tables = {
        "learning_activity_state_versions",
        "activity_lifecycle_command_receipts",
    }
    precreated = lifecycle_tables & existing_tables
    if precreated:
        if precreated != lifecycle_tables:
            raise RuntimeError(
                f"partial activity lifecycle schema before {revision}: {sorted(precreated)}"
            )
        state_columns = {
            item["name"]
            for item in sa.inspect(op.get_bind()).get_columns(
                "learning_activity_state_versions"
            )
        }
        receipt_columns = {
            item["name"]
            for item in sa.inspect(op.get_bind()).get_columns(
                "activity_lifecycle_command_receipts"
            )
        }
        if not {
            "activity_id",
            "version",
            "plan_id",
            "status",
            "source_refs",
            "correlation_id",
        }.issubset(state_columns) or not {
            "user_id",
            "activity_id",
            "idempotency_key",
            "command_digest",
            "response_payload",
        }.issubset(receipt_columns):
            raise RuntimeError(f"incompatible precreated activity lifecycle schema for {revision}")
        _backfill()
        _reconcile()
        return
    op.create_table(
        "learning_activity_state_versions",
        sa.Column("id", sa.String(length=80), nullable=False),
        sa.Column("activity_id", sa.String(length=36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.String(length=36), nullable=False),
        sa.Column("plan_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("previous_status", sa.String(length=20), nullable=True),
        sa.Column("transition_reason", sa.String(length=200), nullable=False),
        sa.Column("source_refs", sa.JSON(), nullable=False),
        sa.Column("actor_type", sa.String(length=20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("correlation_id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("activity_id", "version", name="uq_activity_state_version"),
    )
    op.create_index("ix_activity_state_latest", "learning_activity_state_versions", ["activity_id", "version"])
    op.create_index("ix_activity_state_plan", "learning_activity_state_versions", ["plan_id", "plan_version", "status"])
    for column in ("activity_id", "correlation_id", "plan_id", "status"):
        op.create_index(
            f"ix_learning_activity_state_versions_{column}",
            "learning_activity_state_versions",
            [column],
        )

    op.create_table(
        "activity_lifecycle_command_receipts",
        sa.Column("receipt_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("activity_id", sa.String(length=36), nullable=False),
        sa.Column("command_type", sa.String(length=40), nullable=False),
        sa.Column("idempotency_key", sa.String(length=200), nullable=False),
        sa.Column("command_digest", sa.String(length=64), nullable=False),
        sa.Column("response_payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("receipt_id"),
        sa.UniqueConstraint(
            "user_id", "idempotency_key", name="uq_activity_lifecycle_user_idempotency"
        ),
    )
    op.create_index(
        "ix_activity_lifecycle_receipt_activity",
        "activity_lifecycle_command_receipts",
        ["user_id", "activity_id"],
    )
    for column in ("activity_id", "user_id"):
        op.create_index(
            f"ix_activity_lifecycle_command_receipts_{column}",
            "activity_lifecycle_command_receipts",
            [column],
        )
    _backfill()
    _reconcile()


def downgrade() -> None:
    for column in ("user_id", "activity_id"):
        op.drop_index(
            f"ix_activity_lifecycle_command_receipts_{column}",
            table_name="activity_lifecycle_command_receipts",
        )
    op.drop_index(
        "ix_activity_lifecycle_receipt_activity",
        table_name="activity_lifecycle_command_receipts",
    )
    op.drop_table("activity_lifecycle_command_receipts")
    for column in ("status", "plan_id", "correlation_id", "activity_id"):
        op.drop_index(
            f"ix_learning_activity_state_versions_{column}",
            table_name="learning_activity_state_versions",
        )
    op.drop_index("ix_activity_state_plan", table_name="learning_activity_state_versions")
    op.drop_index("ix_activity_state_latest", table_name="learning_activity_state_versions")
    op.drop_table("learning_activity_state_versions")

"""Durable v0.3 adaptive-contract records.

The tables host immutable SYS05 contracts and additive outcome/experiment
ledgers.  Storage hosting does not transfer payload ownership from SYS01-SYS08.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Index, String, event, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.ledger import ImmutableLedgerError


class TeachingContextRecord(Base):
    __tablename__ = "teaching_contexts"

    context_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    context_fingerprint: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    decision_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (Index("ix_teaching_context_decision_time", "decision_time"),)


class PolicyBundleRecord(Base):
    __tablename__ = "policy_bundles"

    bundle_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    content_digest: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PolicyBundleActivationRecord(Base):
    __tablename__ = "policy_bundle_activations"

    activation_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    bundle_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("policy_bundles.bundle_id"), nullable=False, index=True
    )
    activated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    supersedes_activation_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("policy_bundle_activations.activation_id"), nullable=True
    )
    reason_codes: Mapped[list[str]] = mapped_column(JSON, nullable=False)

    __table_args__ = (Index("ix_policy_activation_time", "activated_at", "activation_id"),)


class TeachingActionV03Record(Base):
    __tablename__ = "teaching_action_versions"

    action_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    decision_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    context_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("teaching_contexts.context_id"), nullable=False, index=True
    )
    policy_bundle_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("policy_bundles.bundle_id"), nullable=False, index=True
    )
    strategy_family: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ExperimentAssignmentRecord(Base):
    __tablename__ = "experiment_assignments"

    assignment_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    experiment_id: Mapped[str] = mapped_column(String(100), nullable=False)
    experiment_version: Mapped[str] = mapped_column(String(100), nullable=False)
    unit_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    variant_id: Mapped[str] = mapped_column(String(100), nullable=False)
    assignment_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    opt_out: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    __table_args__ = (
        Index(
            "ix_experiment_assignment_lookup",
            "experiment_id",
            "experiment_version",
            "unit_ref",
        ),
    )


class TeachingEpisodeRecord(Base):
    __tablename__ = "teaching_episodes"

    episode_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class LearningTrajectoryRecord(Base):
    __tablename__ = "learning_trajectories"

    trajectory_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class OutcomeObservationRecord(Base):
    __tablename__ = "outcome_observations"

    outcome_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    outcome_type: Mapped[str] = mapped_column(String(100), nullable=False)
    measurement_entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    measurement_entity_id: Mapped[str] = mapped_column(String(255), nullable=False)
    measurement_version: Mapped[str] = mapped_column(String(100), nullable=False)
    attribution_scope: Mapped[str] = mapped_column(String(50), nullable=False)
    teaching_episode_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("teaching_episodes.episode_id"), nullable=True
    )
    learning_trajectory_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("learning_trajectories.trajectory_id"), nullable=True
    )
    experiment_assignment_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("experiment_assignments.assignment_id"), nullable=True
    )
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    __table_args__ = (
        Index(
            "ix_outcome_measurement",
            "measurement_entity_type",
            "measurement_entity_id",
            "measurement_version",
        ),
        Index("ix_outcome_observed_at", "observed_at"),
    )


def _reject_adaptive_record_mutation(_mapper: Any, _connection: Any, target: Any) -> None:
    raise ImmutableLedgerError(
        f"{type(target).__name__} is immutable; append a new version/correction instead"
    )


for _immutable_model in (
    TeachingContextRecord,
    PolicyBundleRecord,
    PolicyBundleActivationRecord,
    TeachingActionV03Record,
    ExperimentAssignmentRecord,
    TeachingEpisodeRecord,
    LearningTrajectoryRecord,
    OutcomeObservationRecord,
):
    event.listen(_immutable_model, "before_update", _reject_adaptive_record_mutation)
    event.listen(_immutable_model, "before_delete", _reject_adaptive_record_mutation)

"""SQLite/PostgreSQL-compatible persistence for v0.3 canonical contracts."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.adaptive import (
    AssessmentAttemptV03,
    AssessmentResultV03,
    AttributionScope,
    ExperimentAssignmentV03,
    LearningTrajectoryV03,
    OutcomeObservationV03,
    PolicyBundleActivationV03,
    PolicyBundleV03,
    TeachingActionV03,
    TeachingContextV03,
    TeachingEpisodeV03,
)
from app.contracts.decisions import DecisionTraceV03
from app.contracts.events import LearningEventEnvelopeV03
from app.models.adaptive import (
    ExperimentAssignmentRecord,
    LearningTrajectoryRecord,
    OutcomeObservationRecord,
    PolicyBundleActivationRecord,
    PolicyBundleRecord,
    TeachingActionV03Record,
    TeachingContextRecord,
    TeachingEpisodeRecord,
)
from app.models.assessment import (
    CanonicalAssessmentAttemptRecord,
    CanonicalAssessmentResultRecord,
)
from app.models.ledger import (
    DecisionTraceInputRecord,
    DecisionTraceRecord,
    LearningEventRecord,
)


class ImmutableContractConflict(RuntimeError):
    """An immutable identifier was reused with different semantic content."""


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _same_payload(record_payload: dict, contract: object) -> bool:
    return record_payload == contract.model_dump(mode="json")  # type: ignore[attr-defined]


class AdaptiveContractRepository:
    """SYS05 contract writer plus additive analytics-ledger hosting.

    Callers own the surrounding transaction.  All save methods are idempotent
    for the same immutable id and reject semantic overwrite.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_action(self, action: TeachingActionV03) -> TeachingActionV03:
        context = await self._session.get(
            TeachingContextRecord, action.teaching_context_ref.entity_id
        )
        if context is None:
            raise KeyError(f"teaching context not found: {action.teaching_context_ref.entity_id}")
        bundle = await self._session.get(PolicyBundleRecord, action.policy_bundle_ref.entity_id)
        if bundle is None:
            raise KeyError(f"policy bundle not found: {action.policy_bundle_ref.entity_id}")
        if str(action.teaching_context_ref.version) != context.schema_version:
            raise ValueError("TEACHING_CONTEXT_EXACT_VERSION_MISMATCH")
        if str(action.policy_bundle_ref.version) != bundle.policy_version:
            raise ValueError("POLICY_BUNDLE_EXACT_VERSION_MISMATCH")
        existing = await self._session.get(TeachingActionV03Record, str(action.action_id))
        if existing is not None:
            if not _same_payload(existing.payload, action):
                raise ImmutableContractConflict("teaching action semantic overwrite")
            return TeachingActionV03.model_validate(existing.payload)
        self._session.add(
            TeachingActionV03Record(
                action_id=str(action.action_id),
                schema_version=action.action_schema_version,
                decision_id=str(action.decision_id),
                context_id=action.teaching_context_ref.entity_id,
                policy_bundle_id=action.policy_bundle_ref.entity_id,
                strategy_family=action.strategy_family.value,
                payload=action.model_dump(mode="json"),
                created_at=action.created_at,
            )
        )
        await self._session.flush()
        return action

    async def get_action(self, action_id: UUID | str) -> TeachingActionV03 | None:
        record = await self._session.get(TeachingActionV03Record, str(action_id))
        if record is None:
            return None
        return TeachingActionV03.model_validate(record.payload)

    async def save_context(self, context: TeachingContextV03) -> TeachingContextV03:
        existing = await self._session.get(TeachingContextRecord, str(context.context_id))
        if existing is not None:
            if not _same_payload(existing.payload, context):
                raise ImmutableContractConflict("teaching context semantic overwrite")
            return TeachingContextV03.model_validate(existing.payload)
        self._session.add(
            TeachingContextRecord(
                context_id=str(context.context_id),
                schema_version=context.context_schema_version,
                context_fingerprint=context.context_fingerprint,
                decision_time=context.decision_time,
                payload=context.model_dump(mode="json"),
            )
        )
        await self._session.flush()
        return context

    async def publish_policy_bundle(self, bundle: PolicyBundleV03) -> PolicyBundleV03:
        existing = await self._session.get(PolicyBundleRecord, bundle.bundle_id)
        if existing is not None:
            if not _same_payload(existing.payload, bundle):
                raise ImmutableContractConflict("policy bundle semantic overwrite")
            return PolicyBundleV03.model_validate(existing.payload)
        self._session.add(
            PolicyBundleRecord(
                bundle_id=bundle.bundle_id,
                schema_version=bundle.schema_version,
                policy_version=bundle.policy_version,
                content_digest=bundle.content_digest,
                payload=bundle.model_dump(mode="json"),
                published_at=bundle.published_at,
            )
        )
        await self._session.flush()
        return bundle

    async def activate_policy_bundle(
        self, activation: PolicyBundleActivationV03
    ) -> PolicyBundleActivationV03:
        bundle = await self._session.get(PolicyBundleRecord, activation.bundle_ref.entity_id)
        if bundle is None:
            raise KeyError(f"policy bundle not found: {activation.bundle_ref.entity_id}")
        if str(activation.bundle_ref.version) != bundle.policy_version:
            raise ValueError("POLICY_BUNDLE_EXACT_VERSION_MISMATCH")
        existing = await self._session.get(
            PolicyBundleActivationRecord, str(activation.activation_id)
        )
        data = activation.model_dump(mode="json")
        if existing is not None:
            existing_payload = {
                "activation_id": existing.activation_id,
                "bundle_ref": {
                    "entity_type": "PolicyBundle",
                    "entity_id": existing.bundle_id,
                    "version": bundle.policy_version,
                },
                "activated_at": _aware(existing.activated_at),
                "supersedes_activation_id": existing.supersedes_activation_id,
                "reason_codes": existing.reason_codes,
            }
            return PolicyBundleActivationV03.model_validate(existing_payload)
        self._session.add(
            PolicyBundleActivationRecord(
                activation_id=str(activation.activation_id),
                bundle_id=activation.bundle_ref.entity_id,
                activated_at=activation.activated_at,
                supersedes_activation_id=(
                    str(activation.supersedes_activation_id)
                    if activation.supersedes_activation_id
                    else None
                ),
                reason_codes=list(data["reason_codes"]),
            )
        )
        await self._session.flush()
        return activation

    async def save_experiment_assignment(
        self, assignment: ExperimentAssignmentV03
    ) -> ExperimentAssignmentV03:
        existing = await self._session.get(
            ExperimentAssignmentRecord, str(assignment.assignment_id)
        )
        if existing is not None:
            if not _same_payload(existing.payload, assignment):
                raise ImmutableContractConflict("experiment assignment semantic overwrite")
            return ExperimentAssignmentV03.model_validate(existing.payload)
        self._session.add(
            ExperimentAssignmentRecord(
                assignment_id=str(assignment.assignment_id),
                schema_version=assignment.assignment_schema_version,
                experiment_id=assignment.experiment_id,
                experiment_version=assignment.experiment_version,
                unit_ref=assignment.unit_ref,
                variant_id=assignment.variant_id,
                assignment_probability=assignment.assignment_probability,
                opt_out=assignment.opt_out,
                assigned_at=assignment.assigned_at,
                payload=assignment.model_dump(mode="json"),
            )
        )
        await self._session.flush()
        return assignment

    async def save_episode(self, episode: TeachingEpisodeV03) -> TeachingEpisodeV03:
        for action_ref in episode.teaching_action_refs:
            action = await self._session.get(TeachingActionV03Record, action_ref.entity_id)
            if action is None or str(action_ref.version) != action.schema_version:
                raise ValueError("TEACHING_EPISODE_ACTION_EXACT_REF_INVALID")
        for bundle_ref in episode.policy_bundle_refs:
            bundle = await self._session.get(PolicyBundleRecord, bundle_ref.entity_id)
            if bundle is None or str(bundle_ref.version) != bundle.policy_version:
                raise ValueError("TEACHING_EPISODE_POLICY_EXACT_REF_INVALID")
        existing = await self._session.get(TeachingEpisodeRecord, str(episode.episode_id))
        if existing is not None:
            if not _same_payload(existing.payload, episode):
                raise ImmutableContractConflict("teaching episode semantic overwrite")
            return TeachingEpisodeV03.model_validate(existing.payload)
        self._session.add(
            TeachingEpisodeRecord(
                episode_id=str(episode.episode_id),
                schema_version=episode.episode_schema_version,
                user_id=str(episode.user_id),
                started_at=episode.started_at,
                ended_at=episode.ended_at,
                payload=episode.model_dump(mode="json"),
            )
        )
        await self._session.flush()
        return episode

    async def save_trajectory(self, trajectory: LearningTrajectoryV03) -> LearningTrajectoryV03:
        for episode_ref in trajectory.episode_refs:
            episode = await self._session.get(TeachingEpisodeRecord, episode_ref.entity_id)
            if episode is None or str(episode_ref.version) != episode.schema_version:
                raise ValueError("LEARNING_TRAJECTORY_EPISODE_EXACT_REF_INVALID")
        existing = await self._session.get(LearningTrajectoryRecord, str(trajectory.trajectory_id))
        if existing is not None:
            if not _same_payload(existing.payload, trajectory):
                raise ImmutableContractConflict("learning trajectory semantic overwrite")
            return LearningTrajectoryV03.model_validate(existing.payload)
        self._session.add(
            LearningTrajectoryRecord(
                trajectory_id=str(trajectory.trajectory_id),
                schema_version=trajectory.trajectory_schema_version,
                user_id=str(trajectory.user_id),
                started_at=trajectory.started_at,
                ended_at=trajectory.ended_at,
                payload=trajectory.model_dump(mode="json"),
            )
        )
        await self._session.flush()
        return trajectory

    async def save_outcome(self, outcome: OutcomeObservationV03) -> OutcomeObservationV03:
        episode_record = None
        if outcome.teaching_episode_ref is not None:
            episode_record = await self._session.get(
                TeachingEpisodeRecord, outcome.teaching_episode_ref.entity_id
            )
            if (
                episode_record is None
                or str(outcome.teaching_episode_ref.version) != episode_record.schema_version
            ):
                raise ValueError("OUTCOME_EPISODE_EXACT_REF_INVALID")
        if outcome.learning_trajectory_ref is not None:
            trajectory = await self._session.get(
                LearningTrajectoryRecord, outcome.learning_trajectory_ref.entity_id
            )
            if (
                trajectory is None
                or str(outcome.learning_trajectory_ref.version) != trajectory.schema_version
            ):
                raise ValueError("OUTCOME_TRAJECTORY_EXACT_REF_INVALID")
        if outcome.experiment_association is not None:
            assignment = await self._session.get(
                ExperimentAssignmentRecord, outcome.experiment_association.entity_id
            )
            if (
                assignment is None
                or str(outcome.experiment_association.version) != assignment.schema_version
            ):
                raise ValueError("OUTCOME_EXPERIMENT_EXACT_REF_INVALID")
        if outcome.attribution_scope is AttributionScope.ACTION_DIRECT:
            if episode_record is None or len(episode_record.payload["teaching_action_refs"]) != 1:
                raise ValueError("ACTION_DIRECT_REQUIRES_SINGLE_ACTION_EPISODE")
        existing = await self._session.get(OutcomeObservationRecord, str(outcome.outcome_id))
        if existing is not None:
            if not _same_payload(existing.payload, outcome):
                raise ImmutableContractConflict("outcome observation semantic overwrite")
            return OutcomeObservationV03.model_validate(existing.payload)
        self._session.add(
            OutcomeObservationRecord(
                outcome_id=str(outcome.outcome_id),
                schema_version=outcome.outcome_schema_version,
                outcome_type=outcome.outcome_type,
                measurement_entity_type=outcome.measurement_reference.entity_type,
                measurement_entity_id=outcome.measurement_reference.entity_id,
                measurement_version=str(outcome.measurement_reference.version),
                attribution_scope=outcome.attribution_scope.value,
                teaching_episode_id=(
                    outcome.teaching_episode_ref.entity_id
                    if outcome.teaching_episode_ref is not None
                    else None
                ),
                learning_trajectory_id=(
                    outcome.learning_trajectory_ref.entity_id
                    if outcome.learning_trajectory_ref is not None
                    else None
                ),
                experiment_assignment_id=(
                    outcome.experiment_association.entity_id
                    if outcome.experiment_association is not None
                    else None
                ),
                observed_at=outcome.observed_at,
                payload=outcome.model_dump(mode="json"),
            )
        )
        await self._session.flush()
        return outcome

    async def get_outcome(self, outcome_id: UUID | str) -> OutcomeObservationV03 | None:
        record = await self._session.get(OutcomeObservationRecord, str(outcome_id))
        if record is None:
            return None
        return OutcomeObservationV03.model_validate(record.payload)


class AssessmentRecordV03Repository:
    """SYS04 writer for v0.3 Attempt/AssessmentResult JSON payload versions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_attempt(self, attempt: AssessmentAttemptV03) -> AssessmentAttemptV03:
        existing = await self._session.scalar(
            select(CanonicalAssessmentAttemptRecord).where(
                CanonicalAssessmentAttemptRecord.idempotency_key == attempt.idempotency_key
            )
        )
        if existing is not None:
            if not _same_payload(existing.payload, attempt):
                raise ImmutableContractConflict("assessment attempt idempotency conflict")
            return AssessmentAttemptV03.model_validate(existing.payload)
        self._session.add(
            CanonicalAssessmentAttemptRecord(
                id=str(attempt.attempt_id),
                idempotency_key=attempt.idempotency_key,
                user_id=str(attempt.user_id),
                item_id=str(attempt.item_id),
                item_version=attempt.item_version,
                payload=attempt.model_dump(mode="json"),
            )
        )
        await self._session.flush()
        return attempt

    async def save_result(self, result: AssessmentResultV03) -> AssessmentResultV03:
        existing = await self._session.get(CanonicalAssessmentResultRecord, str(result.result_id))
        if existing is not None:
            if not _same_payload(existing.payload, result):
                raise ImmutableContractConflict("assessment result semantic overwrite")
            return AssessmentResultV03.model_validate(existing.payload)
        self._session.add(
            CanonicalAssessmentResultRecord(
                id=str(result.result_id),
                attempt_id=str(result.attempt_id),
                result_version=result.result_version,
                supersedes_result_id=(
                    str(result.supersedes_result_id) if result.supersedes_result_id else None
                ),
                payload=result.model_dump(mode="json"),
            )
        )
        await self._session.flush()
        return result


class LearningEventV03Repository:
    """Append-only event writer that preserves the complete v0.3 envelope."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(self, event: LearningEventEnvelopeV03) -> LearningEventEnvelopeV03:
        existing = await self._session.scalar(
            select(LearningEventRecord).where(
                LearningEventRecord.idempotency_key == event.idempotency_key
            )
        )
        if existing is not None:
            if existing.schema_version != event.schema_version or existing.v03_payload is None:
                raise ImmutableContractConflict(
                    "event idempotency key belongs to another schema/semantic record"
                )
            if not _same_payload(existing.v03_payload, event):
                raise ImmutableContractConflict("learning event semantic overwrite")
            return LearningEventEnvelopeV03.model_validate(existing.v03_payload)

        data = event.model_dump(mode="json")
        self._session.add(
            LearningEventRecord(
                event_id=str(event.event_id),
                event_type=event.event_type,
                schema_version=event.schema_version,
                aggregate_type=event.aggregate_type,
                aggregate_id=str(event.aggregate_id),
                aggregate_version=event.aggregate_version,
                sequence=event.sequence,
                occurred_at=event.occurred_at,
                recorded_at=event.recorded_at,
                idempotency_key=event.idempotency_key,
                correlation_id=str(event.correlation_id),
                causation_id=str(event.causation_id) if event.causation_id else None,
                actor=data["actor"],
                context=data["context"],
                payload=data["payload"],
                provenance=data["provenance"],
                trace=data["trace"],
                privacy=data["privacy"],
                producer_system=event.producer_system,
                v03_payload=data,
            )
        )
        await self._session.flush()
        return event

    async def get(self, event_id: UUID | str) -> LearningEventEnvelopeV03 | None:
        record = await self._session.get(LearningEventRecord, str(event_id))
        if record is None or record.v03_payload is None:
            return None
        return LearningEventEnvelopeV03.model_validate(record.v03_payload)


class DecisionTraceV03Repository:
    """Append-only v0.3 decision writer on the shared SYS08 ledger table."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, decision_id: UUID | str) -> DecisionTraceV03 | None:
        record = await self._session.get(DecisionTraceRecord, str(decision_id))
        if record is None or record.v03_payload is None:
            return None
        return DecisionTraceV03.model_validate(record.v03_payload)

    async def append(self, trace: DecisionTraceV03) -> DecisionTraceV03:
        existing = await self._session.get(DecisionTraceRecord, str(trace.decision_id))
        if existing is not None:
            if (
                existing.schema_version != trace.decision_schema_version
                or existing.v03_payload is None
            ):
                raise ImmutableContractConflict(
                    "decision id belongs to another schema/semantic record"
                )
            if not _same_payload(existing.v03_payload, trace):
                raise ImmutableContractConflict("decision trace semantic overwrite")
            return DecisionTraceV03.model_validate(existing.v03_payload)

        data = trace.model_dump(mode="json")
        context_id = (
            trace.teaching_context_ref.entity_id if trace.teaching_context_ref is not None else None
        )
        policy_bundle_id = (
            trace.policy_bundle_ref.entity_id if trace.policy_bundle_ref is not None else None
        )
        experiment_id = (
            trace.experiment_assignment_ref.entity_id
            if trace.experiment_assignment_ref is not None
            else None
        )
        selected = (
            trace.selected_teaching_action_ref.model_dump(mode="json")
            if trace.selected_teaching_action_ref is not None
            else {}
        )
        record = DecisionTraceRecord(
            decision_id=str(trace.decision_id),
            decision_type=trace.decision_type,
            schema_version=trace.decision_schema_version,
            owner_system=trace.owner_system,
            inputs=[
                {
                    "entity_type": ref.entity_type,
                    "entity_id": ref.entity_id,
                    "version": ref.version,
                }
                for ref in trace.context_source_refs
            ],
            candidates=list(data["available_actions"]),
            selected=selected,
            constraints=list(data["hard_constraint_results"]),
            reason_codes=list(trace.reason_codes),
            confidence=None,
            algorithm=data["algorithm"],
            algorithm_id=trace.algorithm.algorithm_id,
            algorithm_version=trace.algorithm.algorithm_version,
            experiment={
                "assignment_ref": data["experiment_assignment_ref"],
                "assignment_probability": trace.experiment_assignment_probability,
                "action_propensity": trace.action_propensity,
            },
            experiment_id=experiment_id,
            decision_time=trace.decision_time,
            v03_payload=data,
            teaching_context_id=context_id,
            policy_bundle_id=policy_bundle_id,
            behavior_policy_type=trace.behavior_policy_type.value,
            action_propensity=trace.action_propensity,
            experiment_assignment_probability=trace.experiment_assignment_probability,
            replayability_status=trace.replayability_status.value,
            created_at=trace.created_at,
            correlation_id=str(trace.correlation_id),
            trace_id=trace.trace_id,
            indexed_inputs=[
                DecisionTraceInputRecord(
                    entity_type=ref.entity_type,
                    entity_id=ref.entity_id,
                    entity_version=str(ref.version),
                )
                for ref in trace.context_source_refs
            ],
        )
        self._session.add(record)
        await self._session.flush()
        return trace

    async def query_by_context(self, context_id: UUID | str) -> list[DecisionTraceV03]:
        records = (
            await self._session.scalars(
                select(DecisionTraceRecord)
                .where(
                    DecisionTraceRecord.teaching_context_id == str(context_id),
                    DecisionTraceRecord.schema_version.like("3.%"),
                )
                .order_by(DecisionTraceRecord.created_at, DecisionTraceRecord.decision_id)
            )
        ).all()
        return [
            DecisionTraceV03.model_validate(record.v03_payload)
            for record in records
            if record.v03_payload is not None
        ]

"""Durable current-user erasure coordinator with explicit owner adapters.

The coordinator plans exact primary-key deletions and asks each registered
owner adapter to execute only its own rows. SQLAlchemy Core deletes are the
documented privacy-erasure exception to immutable/version-stream listeners;
ordinary product code must continue to append corrections instead.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import tempfile
import threading
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Callable, NoReturn, cast
from uuid import UUID, uuid4

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.schema import Table

from app.contracts.data_control import (
    DataControlErrorCode,
    ErasureOwnerImpactV1,
    ErasureOwnerResultV1,
    ErasurePreviewV1,
    ErasureReceiptV1,
    ErasureReportV1,
    ErasureScope,
    ErasureWorkflowStatus,
)
from app.core.database import Base
from app.data_control.recovery import RecoveryError
from app.infrastructure.privacy import FrozenSubjectManifest
from app.models.adaptive import (
    ExperimentAssignmentRecord,
    LearningTrajectoryRecord,
    OutcomeObservationRecord,
    TeachingActionV03Record,
    TeachingContextRecord,
    TeachingEpisodeRecord,
)
from app.models.assessment import (
    AssessmentResult,
    CanonicalAssessmentAttemptRecord,
    CanonicalAssessmentResultRecord,
    LearnerEvidenceRecord,
    LearnerStateRecord,
    MasteryEstimateRecord,
)
from app.models.data_control import (
    DataErasureCheckpointRecord,
    DataErasureReceiptRecord,
    DataErasureStepRecord,
    DataErasureWorkflowRecord,
)
from app.models.dialog import DialogMessage, DialogSession
from app.models.document import DocumentChunk, UserDocument
from app.models.ledger import (
    DecisionTraceInputRecord,
    DecisionTraceRecord,
    LearningEventRecord,
    OutboxTaskRecord,
)
from app.models.planning import (
    DiagnosticNeedRecord,
    GoalFormationInferenceRecord,
    GoalKnowledgeMappingRecord,
    GoalKnowledgeSubgraphRecord,
    LearningActivityRecord,
    LearningGoalRecord,
    LearningPlanRecord,
    ReviewObservationRecord,
    ReviewScheduleRecord,
)
from app.models.user import User

PREVIEW_TTL = timedelta(minutes=10)


@dataclass(frozen=True)
class SubjectBinding:
    table_name: str
    owner_system: str
    subject_binding: str
    export_disposition: str
    erasure_scopes: tuple[ErasureScope, ...]


def _binding(
    table_name: str,
    owner: str,
    subject_binding: str,
    export_disposition: str,
    *scopes: ErasureScope,
) -> SubjectBinding:
    return SubjectBinding(table_name, owner, subject_binding, export_disposition, scopes)


_LEARNING = (ErasureScope.LEARNING_RECORDS, ErasureScope.ALL_PERSONAL_DATA)
_MODEL = (ErasureScope.MODEL_EXECUTION, ErasureScope.ALL_PERSONAL_DATA)
SUBJECT_BINDINGS: tuple[SubjectBinding, ...] = (
    _binding("users", "IDENTITY", "id", "PROFILE_ALLOWLIST_V1", ErasureScope.ALL_PERSONAL_DATA),
    _binding(
        "user_profiles",
        "IDENTITY",
        "pseudonym_id",
        "PROFILE_ALLOWLIST_V1",
        ErasureScope.ALL_PERSONAL_DATA,
    ),
    _binding(
        "child_profiles",
        "IDENTITY",
        "child_pseudonym_id",
        "EXCLUDED_LEGACY_PROFILE_RELATIONSHIP_V1",
        ErasureScope.ALL_PERSONAL_DATA,
    ),
    _binding(
        "parent_child_relations",
        "IDENTITY",
        "parent_id|child_id",
        "EXCLUDED_LEGACY_PROFILE_RELATIONSHIP_V1",
        ErasureScope.ALL_PERSONAL_DATA,
    ),
    _binding(
        "consent_records",
        "IDENTITY",
        "user_id|guardian_user_id",
        "EXCLUDED_LEGACY_CONSENT_AUDIT_V1",
        ErasureScope.ALL_PERSONAL_DATA,
    ),
    _binding(
        "user_documents",
        "SYS01",
        "pseudonym_id",
        "DOCUMENTS_ALLOWLIST_V1",
        ErasureScope.DOCUMENT,
        ErasureScope.ALL_PERSONAL_DATA,
    ),
    _binding(
        "document_chunks",
        "SYS01",
        "document_id->user_documents",
        "DOCUMENTS_METADATA_ONLY",
        ErasureScope.DOCUMENT,
        ErasureScope.ALL_PERSONAL_DATA,
    ),
    _binding(
        "dialog_sessions",
        "LEGACY_DIALOG",
        "user_id",
        "LEARNING_AND_MODEL_ALLOWLIST_V1",
        *_LEARNING,
        ErasureScope.MODEL_EXECUTION,
    ),
    _binding(
        "dialog_messages",
        "LEGACY_DIALOG",
        "user_id",
        "LEARNING_AND_MODEL_ALLOWLIST_V1",
        *_LEARNING,
        ErasureScope.MODEL_EXECUTION,
    ),
    _binding("assessment_results", "SYS04", "user_id", "LEARNING_RECORDS_ALLOWLIST_V1", *_LEARNING),
    _binding(
        "canonical_assessment_attempts",
        "SYS04",
        "user_id",
        "LEARNING_RECORDS_ALLOWLIST_V1",
        *_LEARNING,
    ),
    _binding(
        "canonical_assessment_result_versions",
        "SYS04",
        "attempt_id->attempt",
        "LEARNING_RECORDS_ALLOWLIST_V1",
        *_LEARNING,
    ),
    _binding(
        "learner_evidence",
        "SYS03",
        "user_id",
        "LEARNING_RECORDS_ALLOWLIST_V1",
        ErasureScope.DOCUMENT,
        *_LEARNING,
    ),
    _binding(
        "canonical_mastery_estimate_versions",
        "SYS03",
        "user_id",
        "LEARNING_RECORDS_ALLOWLIST_V1",
        ErasureScope.DOCUMENT,
        *_LEARNING,
    ),
    _binding(
        "learner_state_versions",
        "SYS03",
        "user_id",
        "LEARNING_RECORDS_ALLOWLIST_V1",
        ErasureScope.DOCUMENT,
        *_LEARNING,
    ),
    _binding(
        "review_observations", "SYS07", "user_id", "LEARNING_RECORDS_ALLOWLIST_V1", *_LEARNING
    ),
    _binding(
        "review_schedule_versions", "SYS07", "user_id", "LEARNING_RECORDS_ALLOWLIST_V1", *_LEARNING
    ),
    _binding(
        "learning_goal_versions",
        "SYS06",
        "user_id",
        "LEARNING_RECORDS_ALLOWLIST_V1",
        ErasureScope.DOCUMENT,
        *_LEARNING,
    ),
    _binding(
        "learning_plan_versions",
        "SYS06",
        "learning_goal_id->goal",
        "LEARNING_RECORDS_ALLOWLIST_V1",
        ErasureScope.DOCUMENT,
        *_LEARNING,
    ),
    _binding(
        "learning_activities",
        "SYS06",
        "plan_id->plan",
        "LEARNING_RECORDS_ALLOWLIST_V1",
        ErasureScope.DOCUMENT,
        *_LEARNING,
    ),
    _binding(
        "goal_knowledge_mapping_versions",
        "SYS06",
        "goal_id->goal",
        "LEARNING_RECORDS_ALLOWLIST_V1",
        ErasureScope.DOCUMENT,
        *_LEARNING,
    ),
    _binding(
        "goal_knowledge_subgraph_versions",
        "SYS06",
        "mapping_id->mapping",
        "LEARNING_RECORDS_ALLOWLIST_V1",
        ErasureScope.DOCUMENT,
        *_LEARNING,
    ),
    _binding(
        "goal_formation_inferences",
        "SYS06",
        "goal_id->goal",
        "MODEL_EXECUTION_ALLOWLIST_V1",
        ErasureScope.DOCUMENT,
        *_LEARNING,
        *_MODEL,
    ),
    _binding(
        "diagnostic_need_versions", "SYS06", "user_id", "LEARNING_RECORDS_ALLOWLIST_V1", *_LEARNING
    ),
    _binding(
        "learning_events",
        "SYS08",
        "actor.actor_id|registered refs",
        "EXCLUDED_INTERNAL_AUDIT_PAYLOAD",
        ErasureScope.DOCUMENT,
        *_LEARNING,
        *_MODEL,
    ),
    _binding(
        "decision_traces",
        "SYS08",
        "decision_trace_inputs->registered refs",
        "EXCLUDED_INTERNAL_DECISION_PAYLOAD",
        *_LEARNING,
        *_MODEL,
    ),
    _binding(
        "decision_trace_inputs",
        "SYS08",
        "entity_id->registered refs",
        "EXCLUDED_INTERNAL_QUERY_INDEX",
        *_LEARNING,
        *_MODEL,
    ),
    _binding(
        "outbox_tasks",
        "SYS08",
        "payload registered refs",
        "EXCLUDED_INTERNAL_TASK_PAYLOAD",
        *_LEARNING,
        *_MODEL,
    ),
    _binding(
        "recovery_events",
        "SYS08",
        "pseudonym_id",
        "EXCLUDED_INTERNAL_RECOVERY_AUDIT",
        ErasureScope.ALL_PERSONAL_DATA,
    ),
    _binding(
        "teaching_contexts",
        "SYS05",
        "decision->context_id",
        "MODEL_EXECUTION_METADATA_V1",
        *_LEARNING,
        *_MODEL,
    ),
    _binding(
        "teaching_action_versions",
        "SYS05",
        "decision_id",
        "MODEL_EXECUTION_METADATA_V1",
        *_LEARNING,
        *_MODEL,
    ),
    _binding(
        "experiment_assignments",
        "SYS05",
        "unit_ref|payload",
        "MODEL_EXECUTION_METADATA_V1",
        *_LEARNING,
        *_MODEL,
    ),
    _binding(
        "teaching_episodes",
        "SYS05",
        "user_id",
        "LEARNING_RECORDS_ALLOWLIST_V1",
        *_LEARNING,
        *_MODEL,
    ),
    _binding(
        "learning_trajectories",
        "SYS05",
        "user_id",
        "LEARNING_RECORDS_ALLOWLIST_V1",
        *_LEARNING,
        *_MODEL,
    ),
    _binding(
        "outcome_observations",
        "SYS05",
        "episode|trajectory",
        "LEARNING_RECORDS_ALLOWLIST_V1",
        *_LEARNING,
        *_MODEL,
    ),
)

ERASURE_CONTROL_PATH_PREFIXES = (
    "/api/v1/data-control",
    "/api/v1/users",
    "/health",
    "/ready",
)


def erasure_fail_closed(marker: Path, request_path: str) -> bool:
    """Block product-data surfaces while a durable erasure marker is pending."""

    if not marker.is_file():
        return False
    return not any(
        request_path == prefix or request_path.startswith(f"{prefix}/")
        for prefix in ERASURE_CONTROL_PATH_PREFIXES
    )


@dataclass(frozen=True)
class DeletionOperation:
    owner_system: str
    table: Table
    primary_key: Any
    record_ids: tuple[Any, ...]
    exact_predicates: tuple[Any, ...] = ()


@dataclass(frozen=True)
class DeletionPlan:
    operations: tuple[DeletionOperation, ...]
    files: tuple[Path, ...] = ()

    def digest(self) -> str:
        payload = [
            {
                "owner": item.owner_system,
                "table": item.table.name,
                "ids": sorted(str(value) for value in item.record_ids),
            }
            for item in self.operations
        ]
        payload.append({"files": sorted(path.name for path in self.files)})
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


@dataclass(frozen=True)
class PreviewEntry:
    preview: ErasurePreviewV1
    user_id: str
    token_hash: str
    plan_digest: str


class ErasurePreviewRegistry:
    """Process-local short-lived proof; durable state begins only on confirm."""

    def __init__(self) -> None:
        self._entries: dict[UUID, PreviewEntry] = {}
        self._lock = threading.Lock()

    def register(self, entry: PreviewEntry) -> None:
        with self._lock:
            self._cleanup(datetime.now(UTC))
            self._entries[entry.preview.preview_id] = entry

    def get(self, preview_id: UUID, user_id: str, token: str) -> PreviewEntry:
        now = datetime.now(UTC)
        supplied = hashlib.sha256(token.encode()).hexdigest()
        with self._lock:
            self._cleanup(now)
            entry = self._entries.get(preview_id)
            if (
                entry is None
                or entry.user_id != user_id
                or entry.preview.expires_at <= now
                or not hmac.compare_digest(entry.token_hash, supplied)
            ):
                raise RecoveryError(
                    DataControlErrorCode.ERASURE_PREVIEW_EXPIRED,
                    "删除预览不存在、已过期或不属于当前用户",
                )
            return entry

    def _cleanup(self, now: datetime) -> None:
        for preview_id in [
            key for key, value in self._entries.items() if value.preview.expires_at <= now
        ]:
            self._entries.pop(preview_id, None)


preview_registry = ErasurePreviewRegistry()


class ErasureCoordinator:
    def __init__(
        self,
        session: AsyncSession,
        *,
        registry: ErasurePreviewRegistry | None = None,
        documents_dir: Path,
        fail_closed_marker: Path,
        owner_failure_injector: Callable[[str], None] | None = None,
        account_manifest: FrozenSubjectManifest | None = None,
    ) -> None:
        self.session = session
        self.registry = registry or preview_registry
        self.documents_dir = documents_dir.resolve()
        self.fail_closed_marker = fail_closed_marker.resolve()
        self.owner_failure_injector = owner_failure_injector
        self.account_manifest = account_manifest

    async def preview(
        self,
        *,
        user: User,
        scope: ErasureScope,
        target_ref: str | None = None,
    ) -> ErasurePreviewV1:
        if scope == ErasureScope.ALL_PERSONAL_DATA:
            raise RecoveryError(
                DataControlErrorCode.ERASURE_CONFIRMATION_INVALID,
                "全部个人数据删除必须通过账号删除流程确认",
            )
        return await self._create_preview(user=user, scope=scope, target_ref=target_ref)

    async def execute_authorized_account_deletion(
        self,
        *,
        user: User,
        account_request_id: UUID,
    ) -> ErasureReportV1:
        """Execute P1-05's accepted account authorization in the canonical workflow."""

        preview = await self._create_preview(
            user=user,
            scope=ErasureScope.ALL_PERSONAL_DATA,
            target_ref=None,
        )
        return await self.confirm(
            user=user,
            preview_id=preview.preview_id,
            token=preview.confirmation_token,
            confirmation_phrase=preview.confirmation_phrase,
            idempotency_key=f"account-deletion:{account_request_id}",
        )

    async def _create_preview(
        self,
        *,
        user: User,
        scope: ErasureScope,
        target_ref: str | None,
    ) -> ErasurePreviewV1:
        self._validate_target(scope, target_ref)
        plan = await self._build_plan(user, scope, target_ref)
        token = secrets.token_urlsafe(48)
        preview = ErasurePreviewV1(
            preview_id=uuid4(),
            user_ref=self._user_ref(user.id),
            scope=scope,
            target_ref=target_ref,
            impacts=self._impacts(plan),
            backup_impact=(
                "早于新删除检查点的受管理恢复点将失效并清理；"
                "桌面维护随后创建并验证 POST_ERASURE 基线。"
            ),
            confirmation_phrase=self._confirmation_phrase(scope, target_ref),
            expires_at=datetime.now(UTC) + PREVIEW_TTL,
            confirmation_token=token,
        )
        self.registry.register(
            PreviewEntry(
                preview=preview,
                user_id=user.id,
                token_hash=hashlib.sha256(token.encode()).hexdigest(),
                plan_digest=plan.digest(),
            )
        )
        return preview

    async def confirm(
        self,
        *,
        user: User,
        preview_id: UUID,
        token: str,
        confirmation_phrase: str,
        idempotency_key: str,
    ) -> ErasureReportV1:
        entry = self.registry.get(preview_id, user.id, token)
        preview = entry.preview
        if not idempotency_key or confirmation_phrase != preview.confirmation_phrase:
            self._confirmation_invalid()
        request_digest = self._request_digest(entry.plan_digest, preview, confirmation_phrase)
        existing = await self._existing_workflow(preview.user_ref, idempotency_key)
        if existing is not None:
            if not hmac.compare_digest(existing.request_digest, request_digest):
                self._confirmation_invalid()
            existing_report = ErasureReportV1.model_validate(existing.report)
            if existing_report.status == ErasureWorkflowStatus.PARTIAL:
                return await self.resume_committed_workflow(UUID(existing.workflow_id))
            if existing_report.status not in {
                ErasureWorkflowStatus.FAILED_RETRYABLE,
            }:
                return existing_report
            current_plan = await self._build_plan(user, preview.scope, preview.target_ref)
            if not hmac.compare_digest(current_plan.digest(), entry.plan_digest):
                self._confirmation_invalid()
            pending_report = existing_report.model_copy(
                update={
                    "status": ErasureWorkflowStatus.RUNNING,
                    "reason_codes": ("DATA_ERASURE_RETRY_STARTED",),
                }
            )
            existing.status = pending_report.status.value
            existing.report = pending_report.model_dump(mode="json")
            await self.session.commit()
            return await self._run_workflow(existing, preview, current_plan, pending_report)

        current_plan = await self._build_plan(user, preview.scope, preview.target_ref)
        if not hmac.compare_digest(current_plan.digest(), entry.plan_digest):
            self._confirmation_invalid()

        workflow_id = uuid4()
        started_at = datetime.now(UTC)
        target_hash = self._target_hash(preview.scope, preview.target_ref)
        pending_report = ErasureReportV1(
            workflow_id=workflow_id,
            scope=preview.scope,
            target_ref_hash=target_hash,
            status=ErasureWorkflowStatus.RUNNING,
            owner_results=(),
            started_at=started_at,
            reason_codes=("DATA_ERASURE_STARTED",),
        )
        self._write_marker(workflow_id, None, ErasureWorkflowStatus.RUNNING)
        workflow = DataErasureWorkflowRecord(
            workflow_id=str(workflow_id),
            user_id=user.id,
            user_ref=preview.user_ref,
            scope=preview.scope.value,
            target_ref=preview.target_ref,
            target_ref_hash=target_hash,
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            status=ErasureWorkflowStatus.RUNNING.value,
            report=pending_report.model_dump(mode="json"),
        )
        self.session.add(workflow)
        # SQLAlchemy cannot infer the insert dependency here because the ORM
        # records intentionally do not expose a relationship.  Persist the
        # workflow first so PostgreSQL never sees child steps before their
        # foreign-key parent during an autoflush triggered below.
        await self.session.flush()
        for ordinal, impact in enumerate(self._impacts(current_plan), start=1):
            self.session.add(
                DataErasureStepRecord(
                    workflow_id=str(workflow_id),
                    owner_system=impact.owner_system,
                    ordinal=ordinal,
                    status=ErasureWorkflowStatus.PENDING.value,
                    affected_records=0,
                    reason_codes=[],
                )
            )
        await self._ensure_checkpoint()
        await self.session.commit()

        return await self._run_workflow(workflow, preview, current_plan, pending_report)

    async def resume_committed_workflow(self, workflow_id: UUID) -> ErasureReportV1:
        """Finish file cleanup after the database receipt already committed."""

        workflow = await self.session.get(DataErasureWorkflowRecord, str(workflow_id))
        if workflow is None:
            raise RecoveryError(DataControlErrorCode.ERASURE_PARTIAL, "删除工作流不存在")
        report = ErasureReportV1.model_validate(workflow.report)
        if report.status != ErasureWorkflowStatus.PARTIAL:
            return report
        try:
            self._purge_file_journal(workflow_id)
        except OSError:
            return report
        awaiting = report.model_copy(
            update={
                "status": ErasureWorkflowStatus.AWAITING_RECOVERY_BASELINE,
                "reason_codes": (
                    *report.reason_codes,
                    "DATA_ERASURE_FILE_CLEANUP_COMPLETED",
                ),
            }
        )
        workflow.status = awaiting.status.value
        workflow.report = awaiting.model_dump(mode="json")
        await self.session.commit()
        self._write_marker(awaiting.workflow_id, awaiting.checkpoint, awaiting.status)
        return awaiting

    async def complete_operational_no_resurrection(
        self,
        *,
        workflow_id: UUID,
        checkpoint: int,
        barrier_digest: str,
    ) -> ErasureReportV1:
        """Complete non-desktop workflows from a verified operational barrier adapter."""

        bind = self.session.get_bind()
        if bind.dialect.name == "sqlite":
            raise RecoveryError(
                DataControlErrorCode.MODE_UNSUPPORTED,
                "SQLite 必须创建 VERIFIED POST_ERASURE 恢复基线",
            )
        workflow = await self.session.get(DataErasureWorkflowRecord, str(workflow_id))
        receipt = await self.session.scalar(
            select(DataErasureReceiptRecord).where(
                DataErasureReceiptRecord.workflow_id == str(workflow_id)
            )
        )
        current_checkpoint = await self.session.get(DataErasureCheckpointRecord, 1)
        if (
            workflow is None
            or receipt is None
            or current_checkpoint is None
            or workflow.checkpoint != checkpoint
            or receipt.checkpoint != checkpoint
            or current_checkpoint.checkpoint != checkpoint
            or not barrier_digest.startswith("sha256:")
        ):
            raise RecoveryError(
                DataControlErrorCode.ERASURE_PARTIAL,
                "删除检查点与运维防复活屏障不一致",
            )
        report = ErasureReportV1.model_validate(workflow.report)
        if report.status == ErasureWorkflowStatus.COMPLETED:
            return report
        if report.status != ErasureWorkflowStatus.AWAITING_RECOVERY_BASELINE:
            raise RecoveryError(DataControlErrorCode.ERASURE_PARTIAL, "删除工作流尚不可完成")
        completed = report.model_copy(
            update={
                "status": ErasureWorkflowStatus.COMPLETED,
                "completed_at": datetime.now(UTC),
                "reason_codes": (
                    *report.reason_codes,
                    "DATA_OPERATIONAL_NO_RESURRECTION_BARRIER_VERIFIED",
                ),
            }
        )
        workflow.status = completed.status.value
        workflow.report = completed.model_dump(mode="json")
        await self.session.commit()
        self._remove_matching_marker(workflow_id, checkpoint)
        return completed

    async def _run_workflow(
        self,
        workflow: DataErasureWorkflowRecord,
        preview: ErasurePreviewV1,
        current_plan: DeletionPlan,
        pending_report: ErasureReportV1,
    ) -> ErasureReportV1:
        workflow_id = UUID(workflow.workflow_id)
        started_at = pending_report.started_at
        target_hash = workflow.target_ref_hash
        self._prepare_file_journal(workflow_id, current_plan.files)
        database_committed = False
        report: ErasureReportV1 | None = None

        try:
            owner_results = await self._execute_plan(workflow_id, current_plan)
            checkpoint_record = await self.session.get(DataErasureCheckpointRecord, 1)
            if checkpoint_record is None:
                raise RuntimeError("erasure checkpoint missing")
            checkpoint = checkpoint_record.checkpoint + 1
            receipt_id = uuid4()
            result_digest = hashlib.sha256(
                json.dumps(
                    [item.model_dump(mode="json") for item in owner_results],
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode()
            ).hexdigest()
            completed_at = datetime.now(UTC)
            receipt = ErasureReceiptV1(
                receipt_id=receipt_id,
                workflow_id=workflow_id,
                user_ref=preview.user_ref,
                scope=preview.scope,
                target_ref_hash=target_hash,
                checkpoint=checkpoint,
                result_digest=result_digest,
                completed_at=completed_at,
            )
            self.session.add(
                DataErasureReceiptRecord(
                    receipt_id=str(receipt.receipt_id),
                    workflow_id=str(receipt.workflow_id),
                    user_ref=receipt.user_ref,
                    scope=receipt.scope.value,
                    target_ref_hash=receipt.target_ref_hash,
                    checkpoint=receipt.checkpoint,
                    result_digest=receipt.result_digest,
                    completed_at=receipt.completed_at,
                )
            )
            checkpoint_record.checkpoint = checkpoint
            checkpoint_record.receipt_id = str(receipt_id)
            report = ErasureReportV1(
                workflow_id=workflow_id,
                scope=preview.scope,
                target_ref_hash=target_hash,
                status=ErasureWorkflowStatus.AWAITING_RECOVERY_BASELINE,
                checkpoint=checkpoint,
                owner_results=owner_results,
                started_at=started_at,
                receipt_id=receipt_id,
                reason_codes=(
                    "DATA_ERASURE_DATABASE_COMMITTED",
                    "DATA_POST_ERASURE_BASELINE_REQUIRED",
                ),
            )
            workflow.status = report.status.value
            workflow.checkpoint = checkpoint
            workflow.report = report.model_dump(mode="json")
            workflow.target_ref = None
            if preview.scope == ErasureScope.ALL_PERSONAL_DATA:
                workflow.user_id = preview.user_ref
            await self.session.commit()
            database_committed = True
            self._purge_file_journal(workflow_id)
            self._write_marker(workflow_id, checkpoint, report.status)
            return report
        except Exception:
            if database_committed and report is not None:
                partial = report.model_copy(
                    update={
                        "status": ErasureWorkflowStatus.PARTIAL,
                        "reason_codes": (
                            *report.reason_codes,
                            "DATA_ERASURE_FILE_CLEANUP_PENDING",
                        ),
                    }
                )
                persisted = await self.session.get(
                    DataErasureWorkflowRecord,
                    str(workflow_id),
                )
                if persisted is not None:
                    persisted.status = partial.status.value
                    persisted.report = partial.model_dump(mode="json")
                    await self.session.commit()
                self._write_marker(workflow_id, partial.checkpoint, partial.status)
                return partial
            await self.session.rollback()
            self._discard_file_journal(workflow_id)
            persisted_workflow = await self.session.get(DataErasureWorkflowRecord, str(workflow_id))
            if persisted_workflow is not None:
                failed = pending_report.model_copy(
                    update={
                        "status": ErasureWorkflowStatus.FAILED_RETRYABLE,
                        "reason_codes": ("DATA_ERASURE_OWNER_STEP_FAILED",),
                    }
                )
                persisted_workflow.status = failed.status.value
                persisted_workflow.report = failed.model_dump(mode="json")
                await self.session.commit()
                self._write_marker(workflow_id, None, failed.status)
                return failed
            raise

    async def _build_plan(
        self,
        user: User,
        scope: ErasureScope,
        target_ref: str | None,
    ) -> DeletionPlan:
        if scope == ErasureScope.LEARNING_RECORDS:
            return await self._learning_plan(user)
        if scope == ErasureScope.DOCUMENT:
            assert target_ref is not None
            return await self._document_plan(user, target_ref)
        if scope == ErasureScope.MODEL_EXECUTION:
            return await self._model_execution_plan(user)
        if scope == ErasureScope.ALL_PERSONAL_DATA:
            return await self._all_personal_data_plan(user)
        raise RecoveryError(
            DataControlErrorCode.ERASURE_CONFIRMATION_INVALID,
            "删除范围尚未注册",
        )

    async def _learning_plan(self, user: User) -> DeletionPlan:
        session_ids = await self._ids(
            select(DialogSession.id).where(DialogSession.user_id == user.id)
        )
        attempt_ids = await self._ids(
            select(CanonicalAssessmentAttemptRecord.id).where(
                CanonicalAssessmentAttemptRecord.user_id == user.id
            )
        )
        result_ids = await self._ids(
            select(CanonicalAssessmentResultRecord.id).where(
                CanonicalAssessmentResultRecord.attempt_id.in_(attempt_ids)
            )
        )
        goal_ids = await self._ids(
            select(LearningGoalRecord.goal_id).where(LearningGoalRecord.user_id == user.id)
        )
        goal_record_ids = await self._ids(
            select(LearningGoalRecord.id).where(LearningGoalRecord.user_id == user.id)
        )
        plan_ids = await self._ids(
            select(LearningPlanRecord.plan_id).where(
                LearningPlanRecord.learning_goal_id.in_(goal_ids)
            )
        )
        plan_record_ids = await self._ids(
            select(LearningPlanRecord.id).where(LearningPlanRecord.learning_goal_id.in_(goal_ids))
        )
        mapping_ids = await self._ids(
            select(GoalKnowledgeMappingRecord.mapping_id).where(
                GoalKnowledgeMappingRecord.goal_id.in_(goal_ids)
            )
        )
        episode_ids = await self._ids(
            select(TeachingEpisodeRecord.episode_id).where(TeachingEpisodeRecord.user_id == user.id)
        )
        trajectory_ids = await self._ids(
            select(LearningTrajectoryRecord.trajectory_id).where(
                LearningTrajectoryRecord.user_id == user.id
            )
        )
        decision_plan = await self._decision_plan_for_refs(
            {
                user.id,
                *session_ids,
                *attempt_ids,
                *result_ids,
                *goal_ids,
                *plan_ids,
                *mapping_ids,
                *episode_ids,
                *trajectory_ids,
            }
        )
        operations = (
            await self._op(
                "SYS08",
                OutboxTaskRecord,
                OutboxTaskRecord.id,
                await self._json_owned_ids(OutboxTaskRecord, OutboxTaskRecord.id, user.id),
            ),
            await self._op(
                "SYS08",
                LearningEventRecord,
                LearningEventRecord.event_id,
                await self._event_ids(user.id),
            ),
            await self._op(
                "SYS05",
                OutcomeObservationRecord,
                OutcomeObservationRecord.outcome_id,
                await self._ids(
                    select(OutcomeObservationRecord.outcome_id).where(
                        or_(
                            OutcomeObservationRecord.teaching_episode_id.in_(episode_ids),
                            OutcomeObservationRecord.learning_trajectory_id.in_(trajectory_ids),
                        )
                    )
                ),
            ),
            await self._op(
                "SYS05",
                TeachingEpisodeRecord,
                TeachingEpisodeRecord.episode_id,
                episode_ids,
            ),
            await self._op(
                "SYS05",
                LearningTrajectoryRecord,
                LearningTrajectoryRecord.trajectory_id,
                trajectory_ids,
            ),
            await self._op(
                "SYS05",
                ExperimentAssignmentRecord,
                ExperimentAssignmentRecord.assignment_id,
                await self._experiment_assignment_ids(user.id),
            ),
            await self._op(
                "SYS07",
                ReviewObservationRecord,
                ReviewObservationRecord.id,
                await self._ids(
                    select(ReviewObservationRecord.id).where(
                        ReviewObservationRecord.user_id == user.id
                    )
                ),
            ),
            await self._op(
                "SYS07",
                ReviewScheduleRecord,
                ReviewScheduleRecord.id,
                await self._ids(
                    select(ReviewScheduleRecord.id).where(ReviewScheduleRecord.user_id == user.id)
                ),
            ),
            await self._op(
                "SYS06",
                LearningActivityRecord,
                LearningActivityRecord.id,
                await self._ids(
                    select(LearningActivityRecord.id).where(
                        LearningActivityRecord.plan_id.in_(plan_ids)
                    )
                ),
            ),
            await self._op(
                "SYS06",
                LearningPlanRecord,
                LearningPlanRecord.id,
                plan_record_ids,
            ),
            await self._op(
                "SYS06",
                DiagnosticNeedRecord,
                DiagnosticNeedRecord.id,
                await self._ids(
                    select(DiagnosticNeedRecord.id).where(DiagnosticNeedRecord.user_id == user.id)
                ),
            ),
            await self._op(
                "SYS06",
                GoalKnowledgeSubgraphRecord,
                GoalKnowledgeSubgraphRecord.id,
                await self._ids(
                    select(GoalKnowledgeSubgraphRecord.id).where(
                        GoalKnowledgeSubgraphRecord.mapping_id.in_(mapping_ids)
                    )
                ),
            ),
            await self._op(
                "SYS06",
                GoalKnowledgeMappingRecord,
                GoalKnowledgeMappingRecord.id,
                await self._ids(
                    select(GoalKnowledgeMappingRecord.id).where(
                        GoalKnowledgeMappingRecord.goal_id.in_(goal_ids)
                    )
                ),
            ),
            await self._op(
                "SYS06",
                GoalFormationInferenceRecord,
                GoalFormationInferenceRecord.inference_id,
                await self._ids(
                    select(GoalFormationInferenceRecord.inference_id).where(
                        GoalFormationInferenceRecord.goal_id.in_(goal_ids)
                    )
                ),
            ),
            await self._op(
                "SYS06",
                LearningGoalRecord,
                LearningGoalRecord.id,
                goal_record_ids,
            ),
            await self._op(
                "SYS03",
                LearnerStateRecord,
                LearnerStateRecord.id,
                await self._ids(
                    select(LearnerStateRecord.id).where(LearnerStateRecord.user_id == user.id)
                ),
            ),
            await self._op(
                "SYS03",
                MasteryEstimateRecord,
                MasteryEstimateRecord.id,
                await self._ids(
                    select(MasteryEstimateRecord.id).where(MasteryEstimateRecord.user_id == user.id)
                ),
            ),
            await self._op(
                "SYS03",
                LearnerEvidenceRecord,
                LearnerEvidenceRecord.id,
                await self._ids(
                    select(LearnerEvidenceRecord.id).where(LearnerEvidenceRecord.user_id == user.id)
                ),
            ),
            await self._op(
                "SYS04",
                CanonicalAssessmentResultRecord,
                CanonicalAssessmentResultRecord.id,
                result_ids,
            ),
            await self._op(
                "SYS04",
                CanonicalAssessmentAttemptRecord,
                CanonicalAssessmentAttemptRecord.id,
                attempt_ids,
            ),
            await self._op(
                "SYS04",
                AssessmentResult,
                AssessmentResult.id,
                await self._ids(
                    select(AssessmentResult.id).where(AssessmentResult.user_id == user.id)
                ),
            ),
            await self._op(
                "LEGACY_DIALOG",
                DialogMessage,
                DialogMessage.id,
                await self._ids(select(DialogMessage.id).where(DialogMessage.user_id == user.id)),
            ),
            await self._op(
                "LEGACY_DIALOG",
                DialogSession,
                DialogSession.id,
                session_ids,
            ),
        )
        return self._merge_plans(
            decision_plan,
            DeletionPlan(operations=tuple(item for item in operations if item.record_ids)),
        )

    async def _document_plan(self, user: User, document_id: str) -> DeletionPlan:
        document_row = (
            await self.session.execute(
                select(UserDocument.id, UserDocument.storage_path).where(
                    UserDocument.id == document_id,
                    UserDocument.pseudonym_id == user.pseudonym_id,
                )
            )
        ).one_or_none()
        if document_row is None:
            self._confirmation_invalid()
        raw_path = self._resolve_document(str(document_row[1]))
        chunk_ids = await self._ids(
            select(DocumentChunk.id).where(DocumentChunk.document_id == document_id)
        )

        goal_rows = (
            await self.session.execute(
                select(
                    LearningGoalRecord.id,
                    LearningGoalRecord.goal_id,
                    LearningGoalRecord.payload,
                ).where(LearningGoalRecord.user_id == user.id)
            )
        ).all()
        affected_goal_records = tuple(
            row[0] for row in goal_rows if self._contains_ref(row[2], document_id)
        )
        affected_goal_ids = tuple(
            row[1] for row in goal_rows if self._contains_ref(row[2], document_id)
        )
        plan_ids = await self._ids(
            select(LearningPlanRecord.plan_id).where(
                LearningPlanRecord.learning_goal_id.in_(affected_goal_ids)
            )
        )
        mapping_ids = await self._ids(
            select(GoalKnowledgeMappingRecord.mapping_id).where(
                GoalKnowledgeMappingRecord.goal_id.in_(affected_goal_ids)
            )
        )
        evidence_rows = (
            await self.session.execute(
                select(LearnerEvidenceRecord.id, LearnerEvidenceRecord.payload).where(
                    LearnerEvidenceRecord.user_id == user.id
                )
            )
        ).all()
        affected_evidence = tuple(
            row[0] for row in evidence_rows if self._contains_ref(row[1], document_id)
        )
        projection_reset = bool(affected_evidence)
        decision_plan = await self._decision_plan_for_refs(
            {
                document_id,
                *affected_goal_ids,
                *plan_ids,
                *mapping_ids,
                *affected_evidence,
            }
        )
        operations = (
            await self._op(
                "SYS08",
                LearningEventRecord,
                LearningEventRecord.event_id,
                await self._event_ids_containing(user.id, document_id),
            ),
            await self._op(
                "SYS06",
                LearningActivityRecord,
                LearningActivityRecord.id,
                await self._ids(
                    select(LearningActivityRecord.id).where(
                        LearningActivityRecord.plan_id.in_(plan_ids)
                    )
                ),
            ),
            await self._op(
                "SYS06",
                LearningPlanRecord,
                LearningPlanRecord.id,
                await self._ids(
                    select(LearningPlanRecord.id).where(
                        LearningPlanRecord.learning_goal_id.in_(affected_goal_ids)
                    )
                ),
            ),
            await self._op(
                "SYS06",
                GoalKnowledgeSubgraphRecord,
                GoalKnowledgeSubgraphRecord.id,
                await self._ids(
                    select(GoalKnowledgeSubgraphRecord.id).where(
                        GoalKnowledgeSubgraphRecord.mapping_id.in_(mapping_ids)
                    )
                ),
            ),
            await self._op(
                "SYS06",
                GoalKnowledgeMappingRecord,
                GoalKnowledgeMappingRecord.id,
                await self._ids(
                    select(GoalKnowledgeMappingRecord.id).where(
                        GoalKnowledgeMappingRecord.goal_id.in_(affected_goal_ids)
                    )
                ),
            ),
            await self._op(
                "SYS06",
                GoalFormationInferenceRecord,
                GoalFormationInferenceRecord.inference_id,
                await self._ids(
                    select(GoalFormationInferenceRecord.inference_id).where(
                        GoalFormationInferenceRecord.goal_id.in_(affected_goal_ids)
                    )
                ),
            ),
            await self._op(
                "SYS06",
                LearningGoalRecord,
                LearningGoalRecord.id,
                affected_goal_records,
            ),
            await self._op(
                "SYS03",
                LearnerStateRecord,
                LearnerStateRecord.id,
                (
                    await self._ids(
                        select(LearnerStateRecord.id).where(LearnerStateRecord.user_id == user.id)
                    )
                    if projection_reset
                    else ()
                ),
            ),
            await self._op(
                "SYS03",
                MasteryEstimateRecord,
                MasteryEstimateRecord.id,
                (
                    await self._ids(
                        select(MasteryEstimateRecord.id).where(
                            MasteryEstimateRecord.user_id == user.id
                        )
                    )
                    if projection_reset
                    else ()
                ),
            ),
            await self._op(
                "SYS03",
                LearnerEvidenceRecord,
                LearnerEvidenceRecord.id,
                affected_evidence,
            ),
            await self._op(
                "SYS01",
                DocumentChunk,
                DocumentChunk.id,
                chunk_ids,
            ),
            await self._op(
                "SYS01",
                UserDocument,
                UserDocument.id,
                (document_id,),
            ),
        )
        return self._merge_plans(
            decision_plan,
            DeletionPlan(
                operations=tuple(item for item in operations if item.record_ids),
                files=(raw_path,),
            ),
        )

    async def _model_execution_plan(self, user: User) -> DeletionPlan:
        session_ids = await self._ids(
            select(DialogSession.id).where(DialogSession.user_id == user.id)
        )
        goal_ids = await self._ids(
            select(LearningGoalRecord.goal_id).where(LearningGoalRecord.user_id == user.id)
        )
        inference_ids = await self._ids(
            select(GoalFormationInferenceRecord.inference_id).where(
                GoalFormationInferenceRecord.goal_id.in_(goal_ids)
            )
        )
        episode_ids = await self._ids(
            select(TeachingEpisodeRecord.episode_id).where(TeachingEpisodeRecord.user_id == user.id)
        )
        trajectory_ids = await self._ids(
            select(LearningTrajectoryRecord.trajectory_id).where(
                LearningTrajectoryRecord.user_id == user.id
            )
        )
        owned_refs = {user.id, *session_ids, *goal_ids, *episode_ids, *trajectory_ids}
        execution_refs = {*session_ids, *inference_ids, *episode_ids, *trajectory_ids}
        decision_ids = await self._decision_ids_for_refs(owned_refs)
        action_rows = (
            await self.session.execute(
                select(
                    TeachingActionV03Record.action_id,
                    TeachingActionV03Record.context_id,
                ).where(TeachingActionV03Record.decision_id.in_(decision_ids))
            )
        ).all()
        action_ids = tuple(row[0] for row in action_rows)
        context_ids = tuple(row[1] for row in action_rows)
        operations = (
            await self._op(
                "SYS08",
                OutboxTaskRecord,
                OutboxTaskRecord.id,
                await self._json_owned_ids(OutboxTaskRecord, OutboxTaskRecord.id, user.id),
            ),
            await self._op(
                "SYS08",
                LearningEventRecord,
                LearningEventRecord.event_id,
                await self._event_ids_for_refs(user.id, execution_refs),
            ),
            await self._op(
                "SYS08",
                DecisionTraceInputRecord,
                DecisionTraceInputRecord.id,
                await self._ids(
                    select(DecisionTraceInputRecord.id).where(
                        DecisionTraceInputRecord.decision_id.in_(decision_ids)
                    )
                ),
            ),
            await self._op(
                "SYS08",
                DecisionTraceRecord,
                DecisionTraceRecord.decision_id,
                decision_ids,
            ),
            await self._op(
                "SYS05",
                OutcomeObservationRecord,
                OutcomeObservationRecord.outcome_id,
                await self._ids(
                    select(OutcomeObservationRecord.outcome_id).where(
                        or_(
                            OutcomeObservationRecord.teaching_episode_id.in_(episode_ids),
                            OutcomeObservationRecord.learning_trajectory_id.in_(trajectory_ids),
                        )
                    )
                ),
            ),
            await self._op(
                "SYS05",
                TeachingActionV03Record,
                TeachingActionV03Record.action_id,
                action_ids,
            ),
            await self._op(
                "SYS05",
                TeachingContextRecord,
                TeachingContextRecord.context_id,
                context_ids,
            ),
            await self._op(
                "SYS05",
                TeachingEpisodeRecord,
                TeachingEpisodeRecord.episode_id,
                episode_ids,
            ),
            await self._op(
                "SYS05",
                LearningTrajectoryRecord,
                LearningTrajectoryRecord.trajectory_id,
                trajectory_ids,
            ),
            await self._op(
                "SYS05",
                ExperimentAssignmentRecord,
                ExperimentAssignmentRecord.assignment_id,
                await self._experiment_assignment_ids(user.id),
            ),
            await self._op(
                "SYS06",
                GoalFormationInferenceRecord,
                GoalFormationInferenceRecord.inference_id,
                inference_ids,
            ),
            await self._op(
                "LEGACY_DIALOG",
                DialogMessage,
                DialogMessage.id,
                await self._ids(select(DialogMessage.id).where(DialogMessage.user_id == user.id)),
            ),
            await self._op(
                "LEGACY_DIALOG",
                DialogSession,
                DialogSession.id,
                session_ids,
            ),
        )
        return DeletionPlan(operations=tuple(item for item in operations if item.record_ids))

    async def _all_personal_data_plan(self, user: User) -> DeletionPlan:
        manifest = self.account_manifest
        if (
            manifest is None
            or manifest.user_id != user.id
            or manifest.pseudonym_id != user.pseudonym_id
            or manifest.policy_version != "account-deletion-v1"
        ):
            raise RecoveryError(
                DataControlErrorCode.ERASURE_CONFIRMATION_INVALID,
                "账号删除缺少冻结的全部个人数据清单",
            )
        if manifest.blocking_issues:
            raise RecoveryError(
                DataControlErrorCode.ERASURE_PARTIAL,
                "全部个人数据范围存在无法安全归属的记录",
            )

        grouped: dict[tuple[str, str, str], list[Any]] = {}
        composite_operations: list[DeletionOperation] = []
        files: set[Path] = set()
        for entry in manifest.entries:
            if entry.file_path is not None:
                files.add(self._resolve_document(entry.file_path))
            if entry.table_name == "__local_files__":
                continue
            table = cast(Table, Base.metadata.tables[entry.table_name])
            if len(entry.primary_key) != 1:
                composite_operations.append(
                    DeletionOperation(
                        owner_system=entry.owner,
                        table=table,
                        primary_key=next(iter(table.primary_key.columns)),
                        record_ids=(entry.record_id,),
                        exact_predicates=(
                            and_(
                                *(table.c[column] == value for column, value in entry.primary_key)
                            ),
                        ),
                    )
                )
                continue
            column_name, value = entry.primary_key[0]
            grouped.setdefault((entry.owner, entry.table_name, column_name), []).append(value)

        operations = [
            DeletionOperation(
                owner_system=owner,
                table=cast(Table, Base.metadata.tables[table_name]),
                primary_key=Base.metadata.tables[table_name].c[column_name],
                record_ids=tuple(record_ids),
            )
            for (owner, table_name, column_name), record_ids in grouped.items()
        ]
        operations.extend(composite_operations)
        operations.append(
            DeletionOperation(
                owner_system="IDENTITY_FINALIZE",
                table=cast(Table, User.__table__),
                primary_key=User.id,
                record_ids=(user.id,),
            )
        )
        return DeletionPlan(operations=tuple(operations), files=tuple(sorted(files)))

    async def _execute_plan(
        self,
        workflow_id: UUID,
        plan: DeletionPlan,
    ) -> tuple[ErasureOwnerResultV1, ...]:
        grouped: dict[str, int] = {}
        injected: set[str] = set()
        for operation in plan.operations:
            if self.owner_failure_injector is not None and operation.owner_system not in injected:
                injected.add(operation.owner_system)
                self.owner_failure_injector(operation.owner_system)
            predicate = (
                or_(*operation.exact_predicates)
                if operation.exact_predicates
                else operation.primary_key.in_(operation.record_ids)
            )
            result = cast(
                CursorResult[Any],
                await self.session.execute(delete(operation.table).where(predicate)),
            )
            grouped[operation.owner_system] = grouped.get(operation.owner_system, 0) + int(
                result.rowcount or 0
            )
        owner_results = tuple(
            ErasureOwnerResultV1(
                owner_system=owner,
                status="COMPLETED",
                affected_records=count,
                reason_codes=("DATA_OWNER_ERASURE_COMPLETED",),
            )
            for owner, count in grouped.items()
        )
        for owner in grouped:
            step = await self.session.scalar(
                select(DataErasureStepRecord).where(
                    DataErasureStepRecord.workflow_id == str(workflow_id),
                    DataErasureStepRecord.owner_system == owner,
                )
            )
            if step is not None:
                step.status = ErasureWorkflowStatus.COMPLETED.value
                step.affected_records = grouped[owner]
                step.reason_codes = ["DATA_OWNER_ERASURE_COMPLETED"]
        return owner_results

    async def _event_ids(self, user_id: str) -> tuple[str, ...]:
        rows = (
            await self.session.execute(
                select(LearningEventRecord.event_id, LearningEventRecord.actor)
            )
        ).all()
        return tuple(
            row[0] for row in rows if isinstance(row[1], dict) and row[1].get("actor_id") == user_id
        )

    async def _event_ids_containing(self, user_id: str, target: str) -> tuple[str, ...]:
        return await self._event_ids_for_refs(user_id, {target})

    async def _event_ids_for_refs(self, user_id: str, refs: set[str]) -> tuple[str, ...]:
        if not refs:
            return ()
        rows = (
            await self.session.execute(
                select(
                    LearningEventRecord.event_id,
                    LearningEventRecord.actor,
                    LearningEventRecord.context,
                    LearningEventRecord.payload,
                    LearningEventRecord.provenance,
                    LearningEventRecord.v03_payload,
                )
            )
        ).all()
        return tuple(
            row[0]
            for row in rows
            if isinstance(row[1], dict)
            and row[1].get("actor_id") == user_id
            and any(self._contains_ref(value, target) for value in row[2:] for target in refs)
        )

    async def _decision_ids_for_refs(self, refs: set[str]) -> tuple[str, ...]:
        if not refs:
            return ()
        return await self._ids(
            select(DecisionTraceInputRecord.decision_id)
            .where(DecisionTraceInputRecord.entity_id.in_(refs))
            .distinct()
        )

    async def _decision_plan_for_refs(self, refs: set[str]) -> DeletionPlan:
        decision_ids = await self._decision_ids_for_refs(refs)
        if not decision_ids:
            return DeletionPlan(operations=())
        action_rows = (
            await self.session.execute(
                select(
                    TeachingActionV03Record.action_id,
                    TeachingActionV03Record.context_id,
                ).where(TeachingActionV03Record.decision_id.in_(decision_ids))
            )
        ).all()
        action_ids = tuple(row[0] for row in action_rows)
        context_ids = tuple(row[1] for row in action_rows)
        operations = (
            await self._op(
                "SYS08",
                DecisionTraceInputRecord,
                DecisionTraceInputRecord.id,
                await self._ids(
                    select(DecisionTraceInputRecord.id).where(
                        DecisionTraceInputRecord.decision_id.in_(decision_ids)
                    )
                ),
            ),
            await self._op(
                "SYS08",
                DecisionTraceRecord,
                DecisionTraceRecord.decision_id,
                decision_ids,
            ),
            await self._op(
                "SYS05",
                TeachingActionV03Record,
                TeachingActionV03Record.action_id,
                action_ids,
            ),
            await self._op(
                "SYS05",
                TeachingContextRecord,
                TeachingContextRecord.context_id,
                context_ids,
            ),
        )
        return DeletionPlan(operations=tuple(item for item in operations if item.record_ids))

    async def _experiment_assignment_ids(self, user_id: str) -> tuple[str, ...]:
        rows = (
            await self.session.execute(
                select(
                    ExperimentAssignmentRecord.assignment_id,
                    ExperimentAssignmentRecord.unit_ref,
                    ExperimentAssignmentRecord.payload,
                )
            )
        ).all()
        return tuple(
            row[0] for row in rows if row[1] == user_id or self._contains_ref(row[2], user_id)
        )

    async def _json_owned_ids(self, model: Any, key: Any, user_id: str) -> tuple[Any, ...]:
        payload_column = model.payload
        rows = (await self.session.execute(select(key, payload_column))).all()
        return tuple(row[0] for row in rows if self._contains_ref(row[1], user_id))

    async def _ids(self, statement: Any) -> tuple[Any, ...]:
        return tuple((await self.session.scalars(statement)).all())

    @staticmethod
    async def _op(
        owner: str,
        model: Any,
        key: Any,
        record_ids: tuple[Any, ...],
    ) -> DeletionOperation:
        return DeletionOperation(owner, model.__table__, key, record_ids)

    async def _existing_workflow(
        self, user_ref: str, idempotency_key: str
    ) -> DataErasureWorkflowRecord | None:
        return await self.session.scalar(
            select(DataErasureWorkflowRecord).where(
                DataErasureWorkflowRecord.user_ref == user_ref,
                DataErasureWorkflowRecord.idempotency_key == idempotency_key,
            )
        )

    async def _ensure_checkpoint(self) -> None:
        if await self.session.get(DataErasureCheckpointRecord, 1) is None:
            self.session.add(DataErasureCheckpointRecord(id=1, checkpoint=0))

    @staticmethod
    def _impacts(plan: DeletionPlan) -> tuple[ErasureOwnerImpactV1, ...]:
        grouped: dict[str, int] = {}
        for operation in plan.operations:
            grouped[operation.owner_system] = grouped.get(operation.owner_system, 0) + len(
                operation.record_ids
            )
        if plan.files:
            grouped["FILE_STORAGE"] = len(plan.files)
        if not grouped:
            grouped["DATA_CONTROL"] = 0
        return tuple(
            ErasureOwnerImpactV1(
                owner_system=owner,
                estimated_records=count,
                actions=("ERASE_REGISTERED_SUBJECT_DATA",),
            )
            for owner, count in grouped.items()
        )

    @staticmethod
    def _contains_ref(value: Any, target: str) -> bool:
        if isinstance(value, dict):
            return any(ErasureCoordinator._contains_ref(item, target) for item in value.values())
        if isinstance(value, (list, tuple)):
            return any(ErasureCoordinator._contains_ref(item, target) for item in value)
        return value == target

    @staticmethod
    def _validate_target(scope: ErasureScope, target_ref: str | None) -> None:
        if (scope == ErasureScope.DOCUMENT) != (target_ref is not None):
            raise RecoveryError(
                DataControlErrorCode.ERASURE_CONFIRMATION_INVALID,
                "删除目标与范围不匹配",
            )

    @staticmethod
    def _confirmation_phrase(scope: ErasureScope, target_ref: str | None) -> str:
        return f"永久删除 {target_ref or scope.value}"

    @staticmethod
    def _request_digest(
        plan_digest: str,
        preview: ErasurePreviewV1,
        phrase: str,
    ) -> str:
        return hashlib.sha256(
            json.dumps(
                {
                    "plan": plan_digest,
                    "user": preview.user_ref,
                    "scope": preview.scope.value,
                    "target": preview.target_ref,
                    "phrase": phrase,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()

    @staticmethod
    def _target_hash(scope: ErasureScope, target_ref: str | None) -> str:
        return hashlib.sha256(f"{scope.value}:{target_ref or '*'}".encode()).hexdigest()

    @staticmethod
    def _user_ref(user_id: str) -> str:
        return hashlib.sha256(f"askora-user-export:{user_id}".encode()).hexdigest()[:24]

    def _write_marker(
        self,
        workflow_id: UUID,
        checkpoint: int | None,
        status: ErasureWorkflowStatus,
    ) -> None:
        self.fail_closed_marker.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        descriptor, raw_path = tempfile.mkstemp(
            prefix=".erasure-pending-",
            suffix=".tmp",
            dir=self.fail_closed_marker.parent,
        )
        temporary = Path(raw_path)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as writer:
                json.dump(
                    {
                        "schema_version": "1.0",
                        "workflow_id": str(workflow_id),
                        "checkpoint": checkpoint,
                        "status": status.value,
                    },
                    writer,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                writer.flush()
                os.fsync(writer.fileno())
            temporary.chmod(0o600)
            os.replace(temporary, self.fail_closed_marker)
        finally:
            temporary.unlink(missing_ok=True)

    def _remove_matching_marker(self, workflow_id: UUID, checkpoint: int) -> None:
        if not self.fail_closed_marker.is_file():
            return
        try:
            payload = json.loads(self.fail_closed_marker.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if (
            payload.get("workflow_id") == str(workflow_id)
            and payload.get("checkpoint") == checkpoint
        ):
            self.fail_closed_marker.unlink(missing_ok=True)

    def _resolve_document(self, storage_path: str) -> Path:
        candidate = Path(storage_path)
        if candidate.is_absolute() or ".." in candidate.parts:
            self._confirmation_invalid()
        target = (self.documents_dir / candidate).resolve()
        if self.documents_dir not in target.parents or target.is_symlink():
            self._confirmation_invalid()
        return target

    @staticmethod
    def _merge_plans(*plans: DeletionPlan) -> DeletionPlan:
        merged: dict[tuple[str, str], DeletionOperation] = {}
        files: set[Path] = set()
        for plan in plans:
            files.update(plan.files)
            for operation in plan.operations:
                key = (operation.owner_system, operation.table.name)
                existing = merged.get(key)
                ids = set(operation.record_ids)
                if existing is not None:
                    ids.update(existing.record_ids)
                merged[key] = DeletionOperation(
                    owner_system=operation.owner_system,
                    table=operation.table,
                    primary_key=operation.primary_key,
                    record_ids=tuple(ids),
                    exact_predicates=(
                        *(existing.exact_predicates if existing is not None else ()),
                        *operation.exact_predicates,
                    ),
                )
        return DeletionPlan(tuple(merged.values()), tuple(sorted(files)))

    def _prepare_file_journal(self, workflow_id: UUID, files: tuple[Path, ...]) -> None:
        if not files:
            return
        relative_paths: list[str] = []
        for path in files:
            resolved = path.resolve()
            if self.documents_dir not in resolved.parents:
                self._confirmation_invalid()
            relative_paths.append(resolved.relative_to(self.documents_dir).as_posix())
        journal_dir = self.fail_closed_marker.parent / "erasure-files" / str(workflow_id)
        journal_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        journal = journal_dir / "journal.json"
        descriptor, raw_path = tempfile.mkstemp(
            prefix=".journal-",
            suffix=".tmp",
            dir=journal_dir,
        )
        temporary = Path(raw_path)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as writer:
                json.dump(
                    {"schema_version": "1.0", "relative_paths": relative_paths},
                    writer,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                writer.flush()
                os.fsync(writer.fileno())
            temporary.chmod(0o600)
            os.replace(temporary, journal)
        finally:
            temporary.unlink(missing_ok=True)

    def _purge_file_journal(self, workflow_id: UUID) -> None:
        journal_dir = self.fail_closed_marker.parent / "erasure-files" / str(workflow_id)
        journal = journal_dir / "journal.json"
        if not journal.is_file():
            return
        payload = json.loads(journal.read_text(encoding="utf-8"))
        if payload.get("schema_version") != "1.0" or not isinstance(
            payload.get("relative_paths"), list
        ):
            raise OSError("invalid erasure file journal")
        for raw_relative in payload["relative_paths"]:
            if not isinstance(raw_relative, str):
                raise OSError("invalid erasure file journal path")
            target = self._resolve_document(raw_relative)
            target.unlink(missing_ok=True)
        journal.unlink()
        journal_dir.rmdir()

    def _discard_file_journal(self, workflow_id: UUID) -> None:
        journal_dir = self.fail_closed_marker.parent / "erasure-files" / str(workflow_id)
        (journal_dir / "journal.json").unlink(missing_ok=True)
        try:
            journal_dir.rmdir()
        except FileNotFoundError:
            pass

    @staticmethod
    def _confirmation_invalid() -> NoReturn:
        raise RecoveryError(
            DataControlErrorCode.ERASURE_CONFIRMATION_INVALID,
            "删除确认无效或预览已过时",
        )

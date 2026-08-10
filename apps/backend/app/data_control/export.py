"""Current-user, explicit-allowlist portability export."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import threading
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.data_control import (
    DataControlErrorCode,
    ExportScope,
    UserExportManifestFileV1,
    UserExportManifestV1,
    UserExportReadyV1,
)
from app.core.config import settings
from app.data_control.recovery import RecoveryError
from app.models.assessment import (
    AssessmentResult,
    CanonicalAssessmentAttemptRecord,
    CanonicalAssessmentResultRecord,
    LearnerEvidenceRecord,
    LearnerStateRecord,
    MasteryEstimateRecord,
)
from app.models.dialog import DialogMessage, DialogSession, MessageRole
from app.models.document import UserDocument
from app.models.planning import (
    GoalFormationInferenceRecord,
    LearningActivityRecord,
    LearningGoalRecord,
    LearningPlanRecord,
    ReviewObservationRecord,
    ReviewScheduleRecord,
)
from app.models.profile import UserProfile
from app.models.user import User

EXPORT_TTL = timedelta(minutes=15)
FORBIDDEN_NESTED_KEY_PARTS = (
    "password",
    "secret",
    "token",
    "system_prompt",
    "instruction",
    "answer_key",
    "correct_answer",
    "rubric",
    "grader",
)

ATTEMPT_PAYLOAD_FIELDS = {
    "attempt_id",
    "item_id",
    "item_version",
    "raw_response",
    "normalized_response",
    "response_revisions",
    "assistance",
    "status",
    "submitted_at",
}
RESULT_PAYLOAD_FIELDS = {
    "result_id",
    "result_version",
    "attempt_id",
    "item_id",
    "item_version",
    "score",
    "passed",
    "correctness",
    "error_type",
    "misconception_evidence",
    "independence",
    "assessment_confidence",
    "reason_codes",
    "reviewer_result",
    "created_at",
}
EVIDENCE_PAYLOAD_FIELDS = {
    "evidence_id",
    "knowledge_unit_id",
    "attempt_id",
    "result_id",
    "accepted_at",
    "dimension",
    "outcome",
    "score",
    "confidence",
    "independence",
    "delay_seconds",
    "novelty",
    "evidence_weight",
    "item_difficulty",
    "source_event_ids",
    "eligibility_reason_codes",
}
MASTERY_PAYLOAD_FIELDS = {
    "estimate_id",
    "version",
    "knowledge_unit_id",
    "competence_probability",
    "confidence",
    "independent_success_count",
    "hint_dependency_score",
    "last_independent_success_at",
    "delayed_recall_evidence_count",
    "transfer_evidence_count",
    "active_misconception_ids",
    "evidence_count",
    "effective_evidence_weight",
    "algorithm_id",
    "algorithm_version",
    "source_evidence_ids",
    "created_at",
}
LEARNER_STATE_PAYLOAD_FIELDS = {
    "learner_state_id",
    "learner_state_schema_version",
    "version",
    "mastery_estimate_ids",
    "mastery_estimate_refs",
    "active_misconception_hypotheses",
    "learner_progress_summary",
    "uncertainty_summary",
    "created_from_event_sequence",
    "algorithm_bundle_version",
    "created_at",
}
GOAL_PAYLOAD_FIELDS = {
    "goal_id",
    "goal_schema_version",
    "version",
    "title",
    "topic",
    "target_capabilities",
    "application_context",
    "success_criteria",
    "source_document_ids",
    "deadline_at",
    "weekly_time_budget_minutes",
    "status",
    "confirmed_by_user",
    "created_at",
    "confirmed_at",
    "supersedes_version",
    "reason_codes",
}
REVIEW_PAYLOAD_FIELDS = {
    "schedule_id",
    "version",
    "knowledge_unit_id",
    "memory_model",
    "model_version",
    "difficulty",
    "stability",
    "retrievability",
    "desired_retention",
    "last_valid_retrieval_at",
    "next_due_at",
    "review_priority",
    "evidence_quality",
    "source_event_ids",
    "created_at",
}
PLAN_PAYLOAD_FIELDS = {
    "plan_id",
    "version",
    "learning_goal_id",
    "planning_horizon",
    "objective_ids",
    "activity_ids",
    "constraints",
    "assumptions",
    "created_from_learner_state_version",
    "knowledge_graph_version",
    "review_schedule_version",
    "reason_codes",
    "status",
}
ACTIVITY_PAYLOAD_FIELDS = {
    "activity_id",
    "plan_id",
    "plan_version",
    "objective_id",
    "type",
    "knowledge_unit_ids",
    "estimated_duration_minutes",
    "priority",
    "reason_codes",
    "status",
}
REVIEW_OBSERVATION_PAYLOAD_FIELDS = {
    "observation_id",
    "knowledge_unit_id",
    "observed_at",
    "actual_reviewed_at",
    "retrieval_required",
    "independence",
    "hint_level",
    "answer_seen_before_attempt",
    "assessment_confidence",
    "outcome",
    "delay_seconds",
    "source_evidence_id",
    "source_event_ids",
}


@dataclass(frozen=True)
class ExportArtifact:
    export_id: UUID
    user_id: str
    path: Path
    token_hash: str
    expires_at: datetime
    consumed: bool = False


class ExportRegistry:
    def __init__(self) -> None:
        self._artifacts: dict[UUID, ExportArtifact] = {}
        self._lock = threading.Lock()

    def register(self, artifact: ExportArtifact) -> None:
        with self._lock:
            self._cleanup_expired_locked(datetime.now(UTC))
            self._artifacts[artifact.export_id] = artifact

    def consume(self, export_id: UUID, user_id: str, token: str) -> Path:
        now = datetime.now(UTC)
        with self._lock:
            self._cleanup_expired_locked(now)
            artifact = self._artifacts.get(export_id)
            supplied_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
            if (
                artifact is None
                or artifact.consumed
                or artifact.user_id != user_id
                or artifact.expires_at <= now
                or not hmac.compare_digest(artifact.token_hash, supplied_hash)
            ):
                raise RecoveryError(
                    DataControlErrorCode.EXPORT_EXPIRED,
                    "导出不存在、已使用或已过期",
                )
            consumed = ExportArtifact(
                export_id=artifact.export_id,
                user_id=artifact.user_id,
                path=artifact.path,
                token_hash=artifact.token_hash,
                expires_at=artifact.expires_at,
                consumed=True,
            )
            self._artifacts[export_id] = consumed
            return artifact.path

    def delete(self, export_id: UUID, path: Path) -> None:
        with self._lock:
            artifact = self._artifacts.pop(export_id, None)
        target = artifact.path if artifact is not None else path
        target.unlink(missing_ok=True)

    def _cleanup_expired_locked(self, now: datetime) -> None:
        expired = [
            export_id
            for export_id, artifact in self._artifacts.items()
            if artifact.expires_at <= now
        ]
        for export_id in expired:
            artifact = self._artifacts.pop(export_id)
            artifact.path.unlink(missing_ok=True)


export_registry = ExportRegistry()


class UserDataExporter:
    def __init__(
        self,
        session: AsyncSession,
        *,
        artifact_dir: Path | None = None,
        documents_dir: Path | None = None,
    ) -> None:
        self.session = session
        storage = Path(settings.local_storage_base_path).resolve()
        self.artifact_dir = (artifact_dir or storage.parent / "exports").resolve()
        self.documents_dir = (documents_dir or storage).resolve()

    async def create(
        self,
        *,
        user: User,
        scopes: tuple[ExportScope, ...],
        include_document_originals: bool,
    ) -> UserExportReadyV1:
        normalized_scopes = tuple(dict.fromkeys(scopes))
        if not normalized_scopes or (
            include_document_originals and ExportScope.DOCUMENTS not in normalized_scopes
        ):
            raise RecoveryError(
                DataControlErrorCode.EXPORT_SCOPE_INVALID,
                "导出范围无效",
            )
        export_id = uuid4()
        created_at = datetime.now(UTC)
        expires_at = created_at + EXPORT_TTL
        token = secrets.token_urlsafe(48)
        self.artifact_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        final_path = self.artifact_dir / f"{export_id}.zip"
        temporary_path = self.artifact_dir / f".{export_id}.partial"
        files: list[tuple[str, str, bytes | Path]] = []
        documents: list[dict[str, Any]] = []

        try:
            if ExportScope.PROFILE in normalized_scopes:
                profile = await self._profile(user)
                files.append(self._json_file("profile.json", profile))
            if ExportScope.DOCUMENTS in normalized_scopes:
                documents, originals = await self._documents(
                    user,
                    include_originals=include_document_originals,
                )
                files.append(self._json_file("documents.json", {"documents": documents}))
                files.extend(originals)
            if ExportScope.LEARNING_RECORDS in normalized_scopes:
                learning_records = await self._learning_records(user)
                files.append(self._json_file("learning-records.json", learning_records))
            if ExportScope.MODEL_EXECUTION in normalized_scopes:
                model_execution = await self._model_execution(user)
                files.append(self._json_file("model-execution.json", model_execution))

            manifest_files = tuple(self._manifest_entry(item) for item in files)
            manifest = UserExportManifestV1(
                export_id=export_id,
                created_at=created_at,
                user_ref=self._user_ref(user.id),
                scopes=normalized_scopes,
                includes_document_originals=include_document_originals,
                files=manifest_files,
            )
            with zipfile.ZipFile(
                temporary_path,
                "x",
                compression=zipfile.ZIP_DEFLATED,
                allowZip64=True,
            ) as package:
                for archive_path, _media_type, content in files:
                    self._validate_archive_path(archive_path)
                    if isinstance(content, Path):
                        package.write(content, archive_path)
                    else:
                        package.writestr(archive_path, content)
                package.writestr("manifest.json", manifest.model_dump_json(indent=2))
            temporary_path.chmod(0o600)
            os.replace(temporary_path, final_path)
            final_path.chmod(0o600)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            final_path.unlink(missing_ok=True)
            raise

        ready = UserExportReadyV1(
            export_id=export_id,
            created_at=created_at,
            expires_at=expires_at,
            download_token=token,
            file_count=len(files),
            size_bytes=final_path.stat().st_size,
        )
        export_registry.register(
            ExportArtifact(
                export_id=export_id,
                user_id=user.id,
                path=final_path,
                token_hash=hashlib.sha256(token.encode("utf-8")).hexdigest(),
                expires_at=expires_at,
            )
        )
        return ready

    async def _profile(self, user: User) -> dict[str, Any]:
        profile_rows = (
            await self.session.execute(
                select(
                    UserProfile.favorite_subjects,
                    UserProfile.total_sessions,
                    UserProfile.total_learning_minutes,
                    UserProfile.streak_days,
                    UserProfile.skills_mastered,
                    UserProfile.mastery_summary,
                    UserProfile.metacognition,
                    UserProfile.affective,
                    UserProfile.grade_level,
                    UserProfile.created_at,
                    UserProfile.updated_at,
                ).where(UserProfile.pseudonym_id == user.pseudonym_id)
            )
        ).all()
        return {
            "schema_version": "1.0",
            "source": "PROFILE_OWNER_ALLOWLIST_V1",
            "account": {
                "user_ref": self._user_ref(user.id),
                "role": self._enum_value(user.role),
                "status": self._enum_value(user.status),
                "nickname": user.nickname,
                "created_at": self._json_value(user.created_at),
                "updated_at": self._json_value(user.updated_at),
            },
            "learning_profiles": [
                {
                    "favorite_subjects": row[0],
                    "total_sessions": row[1],
                    "total_learning_minutes": row[2],
                    "streak_days": row[3],
                    "skills_mastered": row[4],
                    "mastery_summary": self._sanitize(row[5]),
                    "metacognition": self._sanitize(row[6]),
                    "affective": self._sanitize(row[7]),
                    "grade_level": row[8],
                    "created_at": self._json_value(row[9]),
                    "updated_at": self._json_value(row[10]),
                }
                for row in profile_rows
            ],
        }

    async def _documents(
        self,
        user: User,
        *,
        include_originals: bool,
    ) -> tuple[list[dict[str, Any]], list[tuple[str, str, bytes | Path]]]:
        rows = (
            await self.session.execute(
                select(
                    UserDocument.id,
                    UserDocument.original_filename,
                    UserDocument.file_extension,
                    UserDocument.file_size_bytes,
                    UserDocument.storage_path,
                    UserDocument.processing_status,
                    UserDocument.moderation_status,
                    UserDocument.subject,
                    UserDocument.knowledge_point_id,
                    UserDocument.chunk_count,
                    UserDocument.total_tokens,
                    UserDocument.is_deleted,
                    UserDocument.created_at,
                    UserDocument.updated_at,
                    UserDocument.deleted_at,
                ).where(UserDocument.pseudonym_id == user.pseudonym_id)
            )
        ).all()
        documents: list[dict[str, Any]] = []
        originals: list[tuple[str, str, bytes | Path]] = []
        for row in rows:
            document = {
                "document_id": row[0],
                "original_filename": row[1],
                "file_extension": row[2],
                "file_size_bytes": row[3],
                "processing_status": row[5],
                "moderation_status": row[6],
                "subject": row[7],
                "knowledge_point_id": row[8],
                "chunk_count": row[9],
                "total_tokens": row[10],
                "is_deleted": row[11],
                "created_at": self._json_value(row[12]),
                "updated_at": self._json_value(row[13]),
                "deleted_at": self._json_value(row[14]),
                "source": "SYS01_DOCUMENT_METADATA_V1",
            }
            documents.append(document)
            if include_originals and not row[11]:
                source = self._resolve_document(str(row[4]))
                if not source.is_file() or source.is_symlink():
                    raise RecoveryError(
                        DataControlErrorCode.BACKUP_INTEGRITY_FAILED,
                        "导出所需资料原件不存在",
                    )
                suffix = str(row[2]).lstrip(".").lower()
                archive_path = f"documents/originals/{row[0]}.{suffix}"
                originals.append((archive_path, "application/octet-stream", source))
        return documents, originals

    async def _learning_records(self, user: User) -> dict[str, Any]:
        session_rows = (
            await self.session.execute(
                select(
                    DialogSession.id,
                    DialogSession.title,
                    DialogSession.subject,
                    DialogSession.topic,
                    DialogSession.knowledge_point_id,
                    DialogSession.status,
                    DialogSession.turn_count,
                    DialogSession.duration_seconds,
                    DialogSession.created_at,
                    DialogSession.ended_at,
                    DialogSession.deleted_at,
                ).where(DialogSession.user_id == user.id)
            )
        ).all()
        message_rows = (
            await self.session.execute(
                select(
                    DialogMessage.id,
                    DialogMessage.session_id,
                    DialogMessage.role,
                    DialogMessage.content,
                    DialogMessage.turn_number,
                    DialogMessage.created_at,
                ).where(
                    DialogMessage.user_id == user.id,
                    DialogMessage.role.in_([MessageRole.USER, MessageRole.ASSISTANT]),
                )
            )
        ).all()
        assessment_rows = (
            await self.session.execute(
                select(
                    AssessmentResult.id,
                    AssessmentResult.assessment_type,
                    AssessmentResult.subject,
                    AssessmentResult.knowledge_point_ids,
                    AssessmentResult.total_items,
                    AssessmentResult.correct_count,
                    AssessmentResult.score,
                    AssessmentResult.time_spent_seconds,
                    AssessmentResult.detected_misconceptions,
                    AssessmentResult.started_at,
                    AssessmentResult.completed_at,
                ).where(AssessmentResult.user_id == user.id)
            )
        ).all()
        attempts = await self._payload_records(
            select(
                CanonicalAssessmentAttemptRecord.id,
                CanonicalAssessmentAttemptRecord.item_id,
                CanonicalAssessmentAttemptRecord.item_version,
                CanonicalAssessmentAttemptRecord.payload,
                CanonicalAssessmentAttemptRecord.created_at,
            ).where(CanonicalAssessmentAttemptRecord.user_id == user.id),
            ATTEMPT_PAYLOAD_FIELDS,
            "SYS04_ASSESSMENT_ATTEMPT_V1",
        )
        results = await self._canonical_results(user.id)
        evidence = await self._learner_evidence(user.id)
        mastery = await self._payload_records(
            select(
                MasteryEstimateRecord.id,
                MasteryEstimateRecord.knowledge_unit_id,
                MasteryEstimateRecord.version,
                MasteryEstimateRecord.payload,
                MasteryEstimateRecord.created_at,
            ).where(MasteryEstimateRecord.user_id == user.id),
            MASTERY_PAYLOAD_FIELDS,
            "SYS03_MASTERY_ESTIMATE_V1",
        )
        learner_states = await self._payload_records(
            select(
                LearnerStateRecord.id,
                LearnerStateRecord.learner_state_id,
                LearnerStateRecord.version,
                LearnerStateRecord.payload,
                LearnerStateRecord.created_at,
            ).where(LearnerStateRecord.user_id == user.id),
            LEARNER_STATE_PAYLOAD_FIELDS,
            "SYS03_LEARNER_STATE_V1",
        )
        goals = await self._payload_records(
            select(
                LearningGoalRecord.id,
                LearningGoalRecord.goal_id,
                LearningGoalRecord.version,
                LearningGoalRecord.payload,
                LearningGoalRecord.created_at,
            ).where(LearningGoalRecord.user_id == user.id),
            GOAL_PAYLOAD_FIELDS,
            "SYS06_LEARNING_GOAL_V1",
        )
        plans = await self._payload_records(
            select(
                LearningPlanRecord.id,
                LearningPlanRecord.plan_id,
                LearningPlanRecord.version,
                LearningPlanRecord.payload,
                LearningPlanRecord.created_at,
            )
            .join(
                LearningGoalRecord,
                LearningGoalRecord.goal_id == LearningPlanRecord.learning_goal_id,
            )
            .where(LearningGoalRecord.user_id == user.id)
            .distinct(),
            PLAN_PAYLOAD_FIELDS,
            "SYS06_LEARNING_PLAN_V1",
        )
        activities = await self._payload_records(
            select(
                LearningActivityRecord.id,
                LearningActivityRecord.plan_id,
                LearningActivityRecord.plan_version,
                LearningActivityRecord.payload,
                LearningActivityRecord.created_at,
            )
            .join(
                LearningPlanRecord,
                LearningPlanRecord.plan_id == LearningActivityRecord.plan_id,
            )
            .join(
                LearningGoalRecord,
                LearningGoalRecord.goal_id == LearningPlanRecord.learning_goal_id,
            )
            .where(LearningGoalRecord.user_id == user.id)
            .distinct(),
            ACTIVITY_PAYLOAD_FIELDS,
            "SYS06_LEARNING_ACTIVITY_V1",
        )
        review_observations = await self._review_observations(user.id)
        reviews = await self._payload_records(
            select(
                ReviewScheduleRecord.id,
                ReviewScheduleRecord.schedule_id,
                ReviewScheduleRecord.version,
                ReviewScheduleRecord.payload,
                ReviewScheduleRecord.created_at,
            ).where(ReviewScheduleRecord.user_id == user.id),
            REVIEW_PAYLOAD_FIELDS,
            "SYS07_REVIEW_SCHEDULE_V1",
        )
        return {
            "schema_version": "1.0",
            "dialog_sessions": [
                {
                    "session_id": row[0],
                    "title": row[1],
                    "subject": row[2],
                    "topic": row[3],
                    "knowledge_point_id": row[4],
                    "status": self._enum_value(row[5]),
                    "turn_count": row[6],
                    "duration_seconds": row[7],
                    "created_at": self._json_value(row[8]),
                    "ended_at": self._json_value(row[9]),
                    "deleted_at": self._json_value(row[10]),
                    "source": "LEGACY_COMPATIBILITY_DIALOG_SESSION",
                }
                for row in session_rows
            ],
            "dialog_messages": [
                {
                    "message_id": row[0],
                    "session_id": row[1],
                    "role": self._enum_value(row[2]),
                    "content": row[3],
                    "turn_number": row[4],
                    "created_at": self._json_value(row[5]),
                    "source": "LEGACY_COMPATIBILITY_DIALOG_MESSAGE",
                }
                for row in message_rows
            ],
            "assessment_summaries": [
                {
                    "result_id": row[0],
                    "assessment_type": row[1],
                    "subject": row[2],
                    "knowledge_point_ids": row[3],
                    "total_items": row[4],
                    "correct_count": row[5],
                    "score": row[6],
                    "time_spent_seconds": row[7],
                    "detected_misconceptions": self._sanitize(row[8]),
                    "started_at": self._json_value(row[9]),
                    "completed_at": self._json_value(row[10]),
                    "source": "LEGACY_COMPATIBILITY_ASSESSMENT_SUMMARY",
                }
                for row in assessment_rows
            ],
            "canonical_attempts": attempts,
            "canonical_results": results,
            "learner_evidence": evidence,
            "mastery_estimates": mastery,
            "learner_states": learner_states,
            "learning_goals": goals,
            "learning_plans": plans,
            "learning_activities": activities,
            "review_observations": review_observations,
            "review_schedules": reviews,
        }

    async def _model_execution(self, user: User) -> dict[str, Any]:
        sessions = (
            await self.session.execute(
                select(
                    DialogSession.id,
                    DialogSession.model_provider,
                    DialogSession.model_name,
                    DialogSession.total_tokens,
                    DialogSession.created_at,
                    DialogSession.ended_at,
                ).where(DialogSession.user_id == user.id)
            )
        ).all()
        messages = (
            await self.session.execute(
                select(
                    DialogMessage.id,
                    DialogMessage.session_id,
                    DialogMessage.input_tokens,
                    DialogMessage.output_tokens,
                    DialogMessage.total_tokens,
                    DialogMessage.ttft_ms,
                    DialogMessage.generation_ms,
                    DialogMessage.created_at,
                ).where(DialogMessage.user_id == user.id)
            )
        ).all()
        inference_rows = (
            await self.session.execute(
                select(
                    GoalFormationInferenceRecord.inference_id,
                    GoalFormationInferenceRecord.goal_id,
                    GoalFormationInferenceRecord.provider,
                    GoalFormationInferenceRecord.model_name,
                    GoalFormationInferenceRecord.status,
                    GoalFormationInferenceRecord.created_at,
                )
                .join(
                    LearningGoalRecord,
                    LearningGoalRecord.goal_id == GoalFormationInferenceRecord.goal_id,
                )
                .where(LearningGoalRecord.user_id == user.id)
                .distinct()
            )
        ).all()
        return {
            "schema_version": "1.0",
            "dialog_model_runs": [
                {
                    "session_id": row[0],
                    "provider": row[1],
                    "model_name": row[2],
                    "total_tokens": row[3],
                    "started_at": self._json_value(row[4]),
                    "ended_at": self._json_value(row[5]),
                    "source": "LEGACY_COMPATIBILITY_DIALOG_EXECUTION",
                }
                for row in sessions
            ],
            "message_generation_metrics": [
                {
                    "message_id": row[0],
                    "session_id": row[1],
                    "input_tokens": row[2],
                    "output_tokens": row[3],
                    "total_tokens": row[4],
                    "ttft_ms": row[5],
                    "generation_ms": row[6],
                    "created_at": self._json_value(row[7]),
                    "source": "LEGACY_COMPATIBILITY_MESSAGE_EXECUTION",
                }
                for row in messages
            ],
            "goal_formation_inferences": [
                {
                    "inference_id": row[0],
                    "goal_id": row[1],
                    "provider": row[2],
                    "model_name": row[3],
                    "status": row[4],
                    "created_at": self._json_value(row[5]),
                    "source": "SYS06_GOAL_FORMATION_INFERENCE_METADATA_V1",
                }
                for row in inference_rows
            ],
        }

    async def _canonical_results(self, user_id: str) -> list[dict[str, Any]]:
        rows = (
            await self.session.execute(
                select(
                    CanonicalAssessmentResultRecord.id,
                    CanonicalAssessmentResultRecord.attempt_id,
                    CanonicalAssessmentResultRecord.result_version,
                    CanonicalAssessmentResultRecord.payload,
                    CanonicalAssessmentResultRecord.created_at,
                )
                .join(
                    CanonicalAssessmentAttemptRecord,
                    CanonicalAssessmentAttemptRecord.id
                    == CanonicalAssessmentResultRecord.attempt_id,
                )
                .where(CanonicalAssessmentAttemptRecord.user_id == user_id)
            )
        ).all()
        return [
            {
                "record_id": row[0],
                "attempt_id": row[1],
                "version": row[2],
                "data": self._allow_payload(row[3], RESULT_PAYLOAD_FIELDS),
                "created_at": self._json_value(row[4]),
                "source": "SYS04_ASSESSMENT_RESULT_V1",
            }
            for row in rows
        ]

    async def _learner_evidence(self, user_id: str) -> list[dict[str, Any]]:
        rows = (
            await self.session.execute(
                select(
                    LearnerEvidenceRecord.id,
                    LearnerEvidenceRecord.source_result_id,
                    LearnerEvidenceRecord.knowledge_unit_id,
                    LearnerEvidenceRecord.status,
                    LearnerEvidenceRecord.reason_codes,
                    LearnerEvidenceRecord.payload,
                    LearnerEvidenceRecord.invalidated_at,
                    LearnerEvidenceRecord.created_at,
                ).where(LearnerEvidenceRecord.user_id == user_id)
            )
        ).all()
        return [
            {
                "record_id": row[0],
                "source_result_id": row[1],
                "knowledge_unit_id": row[2],
                "status": row[3],
                "reason_codes": self._sanitize(row[4]),
                "data": self._allow_payload(row[5], EVIDENCE_PAYLOAD_FIELDS),
                "invalidated_at": self._json_value(row[6]),
                "created_at": self._json_value(row[7]),
                "source": "SYS03_LEARNER_EVIDENCE_V1",
            }
            for row in rows
        ]

    async def _review_observations(self, user_id: str) -> list[dict[str, Any]]:
        rows = (
            await self.session.execute(
                select(
                    ReviewObservationRecord.id,
                    ReviewObservationRecord.knowledge_unit_id,
                    ReviewObservationRecord.actual_reviewed_at,
                    ReviewObservationRecord.payload,
                    ReviewObservationRecord.invalidated_at,
                    ReviewObservationRecord.created_at,
                ).where(ReviewObservationRecord.user_id == user_id)
            )
        ).all()
        return [
            {
                "record_id": row[0],
                "knowledge_unit_id": row[1],
                "actual_reviewed_at": self._json_value(row[2]),
                "data": self._allow_payload(
                    row[3],
                    REVIEW_OBSERVATION_PAYLOAD_FIELDS,
                ),
                "invalidated_at": self._json_value(row[4]),
                "created_at": self._json_value(row[5]),
                "source": "SYS07_REVIEW_OBSERVATION_V1",
            }
            for row in rows
        ]

    async def _payload_records(
        self,
        statement: Any,
        allowed_payload_fields: set[str],
        source: str,
    ) -> list[dict[str, Any]]:
        rows = (await self.session.execute(statement)).all()
        return [
            {
                "record_id": row[0],
                "entity_ref": row[1],
                "version": row[2],
                "data": self._allow_payload(row[3], allowed_payload_fields),
                "created_at": self._json_value(row[4]),
                "source": source,
            }
            for row in rows
        ]

    def _resolve_document(self, storage_path: str) -> Path:
        self._validate_archive_path(storage_path)
        target = (self.documents_dir / storage_path).resolve()
        if self.documents_dir not in target.parents:
            raise RecoveryError(
                DataControlErrorCode.BACKUP_INTEGRITY_FAILED,
                "资料路径越界",
            )
        return target

    @staticmethod
    def _manifest_entry(
        item: tuple[str, str, bytes | Path],
    ) -> UserExportManifestFileV1:
        archive_path, media_type, content = item
        if isinstance(content, Path):
            data_hash = hashlib.sha256()
            with content.open("rb") as reader:
                while chunk := reader.read(1024 * 1024):
                    data_hash.update(chunk)
            size = content.stat().st_size
            digest = data_hash.hexdigest()
        else:
            size = len(content)
            digest = hashlib.sha256(content).hexdigest()
        return UserExportManifestFileV1(
            path=archive_path,
            media_type=media_type,
            size_bytes=size,
            sha256=digest,
        )

    @staticmethod
    def _json_file(path: str, payload: dict[str, Any]) -> tuple[str, str, bytes | Path]:
        content = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return path, "application/json", content

    @staticmethod
    def _user_ref(user_id: str) -> str:
        return hashlib.sha256(f"askora-user-export:{user_id}".encode()).hexdigest()[:24]

    @classmethod
    def _allow_payload(cls, value: Any, allowed_fields: set[str]) -> dict[str, Any]:
        if not isinstance(value, dict):
            return {}
        return {key: cls._sanitize(item) for key, item in value.items() if key in allowed_fields}

    @classmethod
    def _sanitize(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: cls._sanitize(item)
                for key, item in value.items()
                if not any(part in key.lower() for part in FORBIDDEN_NESTED_KEY_PARTS)
            }
        if isinstance(value, (list, tuple)):
            return [cls._sanitize(item) for item in value]
        return cls._json_value(value)

    @staticmethod
    def _json_value(value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, Enum):
            return value.value
        return value

    @staticmethod
    def _enum_value(value: Any) -> Any:
        return value.value if isinstance(value, Enum) else value

    @staticmethod
    def _validate_archive_path(value: str) -> None:
        path = PurePosixPath(value)
        if (
            not value
            or value.startswith("/")
            or "\\" in value
            or any(part in {"", ".", ".."} for part in path.parts)
        ):
            raise RecoveryError(
                DataControlErrorCode.BACKUP_INTEGRITY_FAILED,
                "导出路径无效",
            )

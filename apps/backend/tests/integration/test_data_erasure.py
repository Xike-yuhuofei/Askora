from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app import models  # noqa: F401
from app.contracts.data_control import DataControlErrorCode, ErasureScope, ErasureWorkflowStatus
from app.core.database import Base
from app.data_control.erasure import ErasureCoordinator, ErasurePreviewRegistry
from app.data_control.recovery import RecoveryError
from app.infrastructure.privacy import PrivacyInventoryRepository
from app.models.adaptive import (
    ExperimentAssignmentRecord,
    PolicyBundleRecord,
    TeachingActionV03Record,
    TeachingContextRecord,
)
from app.models.assessment import CanonicalAssessmentAttemptRecord
from app.models.consent import ConsentRecord, ConsentStatus, ConsentType
from app.models.data_control import (
    DataErasureCheckpointRecord,
    DataErasureReceiptRecord,
    DataErasureWorkflowRecord,
)
from app.models.dialog import DialogMessage, DialogSession, MessageRole
from app.models.document import DocumentChunk, UserDocument
from app.models.ledger import DecisionTraceInputRecord, DecisionTraceRecord, LearningEventRecord
from app.models.planning import (
    GoalFormationInferenceRecord,
    LearningActivityRecord,
    LearningGoalRecord,
    LearningPlanRecord,
    ReviewObservationRecord,
)
from app.models.profile import UserProfile
from app.models.user import User, UserRole, UserStatus


async def _count(session: AsyncSession, model: type, *criteria: object) -> int:
    statement = select(func.count()).select_from(model)
    if criteria:
        statement = statement.where(*criteria)
    return int(await session.scalar(statement) or 0)


@pytest.mark.asyncio
async def test_learning_records_erasure_is_current_user_scoped_idempotent_and_checkpointed(
    tmp_path: Path,
) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'erasure.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    current = User(
        id="user-current",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        nickname="Current",
        pseudonym_id="pseudonym-current",
        password_hash="hash-current",
    )
    other = User(
        id="user-other",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        nickname="Other",
        pseudonym_id="pseudonym-other",
        password_hash="hash-other",
    )
    async with factory() as session:
        session.add_all(
            [
                current,
                other,
                DialogSession(
                    id="session-current",
                    user_id=current.id,
                    pseudonym_id=current.pseudonym_id,
                    title="CURRENT-TRANSCRIPT",
                ),
                DialogMessage(
                    id="message-current",
                    session_id="session-current",
                    user_id=current.id,
                    role=MessageRole.USER,
                    content="CURRENT-MESSAGE",
                    turn_number=1,
                ),
                DialogSession(
                    id="session-other",
                    user_id=other.id,
                    pseudonym_id=other.pseudonym_id,
                    title="OTHER-TRANSCRIPT",
                ),
                CanonicalAssessmentAttemptRecord(
                    id="attempt-current",
                    idempotency_key="attempt-current-idem",
                    user_id=current.id,
                    item_id="item-current",
                    item_version="1.0",
                    payload={"attempt_id": "attempt-current"},
                ),
                LearningGoalRecord(
                    id="goal-current:v1",
                    goal_id="goal-current",
                    user_id=current.id,
                    version=1,
                    status="ACTIVE",
                    idempotency_key="goal-current-idem",
                    payload={"goal_id": "goal-current"},
                ),
                LearningPlanRecord(
                    id="plan-current:v1",
                    plan_id="plan-current",
                    learning_goal_id="goal-current",
                    idempotency_key="plan-current-idem",
                    version=1,
                    status="ACTIVE",
                    payload={"plan_id": "plan-current"},
                ),
                LearningActivityRecord(
                    id="activity-current",
                    plan_id="plan-current",
                    plan_version=1,
                    priority=1.0,
                    payload={"activity_id": "activity-current"},
                ),
                ReviewObservationRecord(
                    id="review-current",
                    user_id=current.id,
                    knowledge_unit_id="ku-current",
                    actual_reviewed_at=datetime.now(UTC),
                    payload={"observation_id": "review-current"},
                ),
                PolicyBundleRecord(
                    bundle_id="global-policy",
                    schema_version="1.0",
                    policy_version="global-v1",
                    content_digest="global-digest",
                    payload={"global": True},
                    published_at=datetime.now(UTC),
                ),
                TeachingContextRecord(
                    context_id="context-current",
                    schema_version="1.0",
                    context_fingerprint="context-current-fingerprint",
                    decision_time=datetime.now(UTC),
                    payload={"goal_id": "goal-current"},
                ),
                TeachingContextRecord(
                    context_id="context-other",
                    schema_version="1.0",
                    context_fingerprint="context-other-fingerprint",
                    decision_time=datetime.now(UTC),
                    payload={"user_id": other.id},
                ),
                DecisionTraceRecord(
                    decision_id="decision-current",
                    decision_type="TEACHING_ACTION",
                    schema_version="1.0",
                    owner_system="SYS05",
                    inputs=[],
                    candidates=[],
                    selected={},
                    constraints=[],
                    reason_codes=[],
                    confidence=None,
                    algorithm={},
                    algorithm_id="policy",
                    algorithm_version="1.0",
                    experiment={},
                    teaching_context_id="context-current",
                    created_at=datetime.now(UTC),
                    correlation_id="correlation-current",
                    trace_id="trace-current",
                ),
                DecisionTraceRecord(
                    decision_id="decision-other",
                    decision_type="TEACHING_ACTION",
                    schema_version="1.0",
                    owner_system="SYS05",
                    inputs=[],
                    candidates=[],
                    selected={},
                    constraints=[],
                    reason_codes=[],
                    confidence=None,
                    algorithm={},
                    algorithm_id="policy",
                    algorithm_version="1.0",
                    experiment={},
                    teaching_context_id="context-other",
                    created_at=datetime.now(UTC),
                    correlation_id="correlation-other",
                    trace_id="trace-other",
                ),
                DecisionTraceInputRecord(
                    decision_id="decision-current",
                    entity_type="LEARNING_GOAL",
                    entity_id="goal-current",
                    entity_version="1",
                ),
                DecisionTraceInputRecord(
                    decision_id="decision-other",
                    entity_type="USER",
                    entity_id=other.id,
                    entity_version=None,
                ),
                TeachingActionV03Record(
                    action_id="action-current",
                    schema_version="1.0",
                    decision_id="decision-current",
                    context_id="context-current",
                    policy_bundle_id="global-policy",
                    strategy_family="EXPLAIN",
                    payload={"goal_id": "goal-current"},
                    created_at=datetime.now(UTC),
                ),
                ExperimentAssignmentRecord(
                    assignment_id="assignment-current",
                    schema_version="1.0",
                    experiment_id="experiment",
                    experiment_version="1.0",
                    unit_ref=current.id,
                    variant_id="variant-a",
                    assigned_at=datetime.now(UTC),
                    payload={"user_id": current.id},
                ),
                ExperimentAssignmentRecord(
                    assignment_id="assignment-other",
                    schema_version="1.0",
                    experiment_id="experiment",
                    experiment_version="1.0",
                    unit_ref=other.id,
                    variant_id="variant-a",
                    assigned_at=datetime.now(UTC),
                    payload={"user_id": other.id},
                ),
                TeachingActionV03Record(
                    action_id="action-other",
                    schema_version="1.0",
                    decision_id="decision-other",
                    context_id="context-other",
                    policy_bundle_id="global-policy",
                    strategy_family="EXPLAIN",
                    payload={"user_id": other.id},
                    created_at=datetime.now(UTC),
                ),
            ]
        )
        await session.commit()

        coordinator = ErasureCoordinator(
            session,
            registry=ErasurePreviewRegistry(),
            documents_dir=tmp_path / "documents",
            fail_closed_marker=tmp_path / "recovery" / "erasure-pending.json",
        )
        preview = await coordinator.preview(
            user=current,
            scope=ErasureScope.LEARNING_RECORDS,
        )
        report = await coordinator.confirm(
            user=current,
            preview_id=preview.preview_id,
            token=preview.confirmation_token,
            confirmation_phrase=preview.confirmation_phrase,
            idempotency_key="erase-learning-current",
        )
        replay = await coordinator.confirm(
            user=current,
            preview_id=preview.preview_id,
            token=preview.confirmation_token,
            confirmation_phrase=preview.confirmation_phrase,
            idempotency_key="erase-learning-current",
        )

        assert report.status == ErasureWorkflowStatus.AWAITING_RECOVERY_BASELINE
        assert replay.workflow_id == report.workflow_id
        assert await _count(session, DialogSession, DialogSession.user_id == current.id) == 0
        assert await _count(session, DialogSession, DialogSession.user_id == other.id) == 1
        assert (
            await _count(
                session,
                CanonicalAssessmentAttemptRecord,
                CanonicalAssessmentAttemptRecord.user_id == current.id,
            )
            == 0
        )
        assert await _count(session, LearningGoalRecord) == 0
        assert await _count(session, LearningPlanRecord) == 0
        assert await _count(session, LearningActivityRecord) == 0
        assert await _count(session, ReviewObservationRecord) == 0
        assert await session.get(DecisionTraceRecord, "decision-current") is None
        assert await session.get(TeachingActionV03Record, "action-current") is None
        assert await session.get(TeachingContextRecord, "context-current") is None
        assert await session.get(ExperimentAssignmentRecord, "assignment-current") is None
        assert await session.get(DecisionTraceRecord, "decision-other") is not None
        assert await session.get(TeachingActionV03Record, "action-other") is not None
        assert await session.get(TeachingContextRecord, "context-other") is not None
        assert await session.get(ExperimentAssignmentRecord, "assignment-other") is not None
        assert await _count(session, PolicyBundleRecord) == 1
        assert await _count(session, DataErasureReceiptRecord) == 1
        checkpoint = await session.get(DataErasureCheckpointRecord, 1)
        assert checkpoint is not None and checkpoint.checkpoint == 1
        assert (tmp_path / "recovery" / "erasure-pending.json").is_file()

    await engine.dispose()


@pytest.mark.asyncio
async def test_document_erasure_removes_only_owned_target_and_raw_asset(tmp_path: Path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'document.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    documents = tmp_path / "documents"
    target_asset = documents / "current" / "target.txt"
    keep_asset = documents / "current" / "keep.txt"
    other_asset = documents / "other" / "other.txt"
    for path, content in (
        (target_asset, "TARGET"),
        (keep_asset, "KEEP"),
        (other_asset, "OTHER"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    current = User(
        id="user-current",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        pseudonym_id="pseudonym-current",
    )
    other = User(
        id="user-other",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        pseudonym_id="pseudonym-other",
    )
    async with factory() as session:
        session.add_all(
            [
                current,
                other,
                UserDocument(
                    id="doc-target",
                    pseudonym_id=current.pseudonym_id,
                    original_filename="target.txt",
                    file_extension="txt",
                    file_size_bytes=target_asset.stat().st_size,
                    storage_path="current/target.txt",
                ),
                UserDocument(
                    id="doc-keep",
                    pseudonym_id=current.pseudonym_id,
                    original_filename="keep.txt",
                    file_extension="txt",
                    file_size_bytes=keep_asset.stat().st_size,
                    storage_path="current/keep.txt",
                ),
                UserDocument(
                    id="doc-other",
                    pseudonym_id=other.pseudonym_id,
                    original_filename="other.txt",
                    file_extension="txt",
                    file_size_bytes=other_asset.stat().st_size,
                    storage_path="other/other.txt",
                ),
                DocumentChunk(
                    id="chunk-target",
                    document_id="doc-target",
                    chunk_index=0,
                    content="TARGET-CONTENT",
                ),
            ]
        )
        await session.commit()
        coordinator = ErasureCoordinator(
            session,
            registry=ErasurePreviewRegistry(),
            documents_dir=documents,
            fail_closed_marker=tmp_path / "recovery" / "erasure-pending.json",
        )
        preview = await coordinator.preview(
            user=current,
            scope=ErasureScope.DOCUMENT,
            target_ref="doc-target",
        )
        report = await coordinator.confirm(
            user=current,
            preview_id=preview.preview_id,
            token=preview.confirmation_token,
            confirmation_phrase=preview.confirmation_phrase,
            idempotency_key="erase-document-target",
        )

        assert report.status == ErasureWorkflowStatus.AWAITING_RECOVERY_BASELINE
        assert await session.get(UserDocument, "doc-target") is None
        assert await session.get(DocumentChunk, "chunk-target") is None
        assert await session.get(UserDocument, "doc-keep") is not None
        assert await session.get(UserDocument, "doc-other") is not None
        assert not target_asset.exists()
        assert keep_asset.is_file()
        assert other_asset.is_file()
    await engine.dispose()


@pytest.mark.asyncio
async def test_document_file_cleanup_partial_retries_without_second_checkpoint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'file-retry.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    documents = tmp_path / "documents"
    raw_asset = documents / "current" / "target.txt"
    raw_asset.parent.mkdir(parents=True)
    raw_asset.write_text("PRIVATE-RAW-ASSET", encoding="utf-8")
    user = User(
        id="user-current",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        pseudonym_id="pseudonym-current",
    )
    async with factory() as session:
        session.add_all(
            [
                user,
                UserDocument(
                    id="doc-target",
                    pseudonym_id=user.pseudonym_id,
                    original_filename="target.txt",
                    file_extension="txt",
                    file_size_bytes=raw_asset.stat().st_size,
                    storage_path="current/target.txt",
                ),
            ]
        )
        await session.commit()
        coordinator = ErasureCoordinator(
            session,
            registry=ErasurePreviewRegistry(),
            documents_dir=documents,
            fail_closed_marker=tmp_path / "recovery" / "erasure-pending.json",
        )
        preview = await coordinator.preview(
            user=user,
            scope=ErasureScope.DOCUMENT,
            target_ref="doc-target",
        )
        original_purge = coordinator._purge_file_journal
        failed = False

        def fail_once(workflow_id):
            nonlocal failed
            if not failed:
                failed = True
                raise PermissionError("injected file cleanup failure")
            return original_purge(workflow_id)

        monkeypatch.setattr(coordinator, "_purge_file_journal", fail_once)
        first = await coordinator.confirm(
            user=user,
            preview_id=preview.preview_id,
            token=preview.confirmation_token,
            confirmation_phrase=preview.confirmation_phrase,
            idempotency_key="erase-document-file-retry",
        )
        second = await coordinator.confirm(
            user=user,
            preview_id=preview.preview_id,
            token=preview.confirmation_token,
            confirmation_phrase=preview.confirmation_phrase,
            idempotency_key="erase-document-file-retry",
        )

        assert first.status == ErasureWorkflowStatus.PARTIAL
        assert second.status == ErasureWorkflowStatus.AWAITING_RECOVERY_BASELINE
        assert first.checkpoint == second.checkpoint == 1
        assert not raw_asset.exists()
        assert await _count(session, DataErasureReceiptRecord) == 1
    await engine.dispose()


@pytest.mark.asyncio
async def test_model_execution_erasure_preserves_goal_and_global_policy(tmp_path: Path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'model.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    current = User(
        id="user-current",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        pseudonym_id="pseudonym-current",
    )
    async with factory() as session:
        session.add_all(
            [
                current,
                DialogSession(
                    id="session-current",
                    user_id=current.id,
                    pseudonym_id=current.pseudonym_id,
                    title="MODEL-TRANSCRIPT",
                ),
                LearningGoalRecord(
                    id="goal-current:v1",
                    goal_id="goal-current",
                    user_id=current.id,
                    version=1,
                    status="ACTIVE",
                    idempotency_key="goal-current-model-test",
                    payload={"goal_id": "goal-current"},
                ),
                GoalFormationInferenceRecord(
                    inference_id="inference-current",
                    goal_id="goal-current",
                    input_digest="d" * 64,
                    provider="provider",
                    model_name="model",
                    status="COMPLETED",
                    payload={"candidate": "PRIVATE-MODEL-OUTPUT"},
                ),
                LearningEventRecord(
                    event_id="model-event-current",
                    event_type="ModelInferenceCompleted",
                    schema_version="1.0",
                    aggregate_type="dialog_session",
                    aggregate_id="session-current",
                    aggregate_version=1,
                    sequence=1,
                    occurred_at=datetime.now(UTC),
                    recorded_at=datetime.now(UTC),
                    idempotency_key="model-event-current",
                    correlation_id="model-correlation",
                    actor={"actor_id": current.id},
                    context={"session_id": "session-current"},
                    payload={"session_id": "session-current"},
                    provenance={},
                    trace={},
                    privacy={},
                ),
                LearningEventRecord(
                    event_id="learning-event-current",
                    event_type="LearningGoalConfirmed",
                    schema_version="1.0",
                    aggregate_type="learning_goal",
                    aggregate_id="goal-current",
                    aggregate_version=1,
                    sequence=1,
                    occurred_at=datetime.now(UTC),
                    recorded_at=datetime.now(UTC),
                    idempotency_key="learning-event-current",
                    correlation_id="learning-correlation",
                    actor={"actor_id": current.id},
                    context={"goal_id": "goal-current"},
                    payload={"goal_id": "goal-current"},
                    provenance={},
                    trace={},
                    privacy={},
                ),
                PolicyBundleRecord(
                    bundle_id="global-policy-model",
                    schema_version="1.0",
                    policy_version="global-model-v1",
                    content_digest="global-model-digest",
                    payload={"global": True},
                    published_at=datetime.now(UTC),
                ),
            ]
        )
        await session.commit()
        coordinator = ErasureCoordinator(
            session,
            registry=ErasurePreviewRegistry(),
            documents_dir=tmp_path / "documents",
            fail_closed_marker=tmp_path / "recovery" / "erasure-pending.json",
        )
        preview = await coordinator.preview(
            user=current,
            scope=ErasureScope.MODEL_EXECUTION,
        )
        await coordinator.confirm(
            user=current,
            preview_id=preview.preview_id,
            token=preview.confirmation_token,
            confirmation_phrase=preview.confirmation_phrase,
            idempotency_key="erase-model-current",
        )

        assert await session.get(DialogSession, "session-current") is None
        assert await session.get(GoalFormationInferenceRecord, "inference-current") is None
        assert await session.get(LearningEventRecord, "model-event-current") is None
        assert await session.get(LearningEventRecord, "learning-event-current") is not None
        assert await session.get(LearningGoalRecord, "goal-current:v1") is not None
        assert await session.get(PolicyBundleRecord, "global-policy-model") is not None
    await engine.dispose()


@pytest.mark.asyncio
async def test_all_personal_data_erasure_removes_identity_but_keeps_tombstone(
    tmp_path: Path,
) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'all.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    current = User(
        id="user-current",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        pseudonym_id="pseudonym-current",
        password_hash="PRIVATE-HASH",
    )
    other = User(
        id="user-other",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        pseudonym_id="pseudonym-other",
    )
    async with factory() as session:
        session.add_all(
            [
                current,
                other,
                UserProfile(id="profile-current", pseudonym_id=current.pseudonym_id),
                ConsentRecord(
                    id="consent-current",
                    user_id=current.id,
                    consent_type=ConsentType.PRIVACY_POLICY,
                    status=ConsentStatus.GRANTED,
                    consent_version="1.0",
                    consent_text="PRIVATE-CONSENT",
                    action_method="button_click",
                ),
            ]
        )
        await session.commit()
        manifest = await PrivacyInventoryRepository(session).build_manifest(
            user_id=current.id,
            pseudonym_id=current.pseudonym_id,
            subject_digest="account-subject-current",
            storage_base_path=tmp_path / "documents",
        )
        coordinator = ErasureCoordinator(
            session,
            registry=ErasurePreviewRegistry(),
            documents_dir=tmp_path / "documents",
            fail_closed_marker=tmp_path / "recovery" / "erasure-pending.json",
            account_manifest=manifest,
        )
        with pytest.raises(RecoveryError) as direct_preview:
            await coordinator.preview(user=current, scope=ErasureScope.ALL_PERSONAL_DATA)
        assert direct_preview.value.code == DataControlErrorCode.ERASURE_CONFIRMATION_INVALID
        report = await coordinator.execute_authorized_account_deletion(
            user=current,
            account_request_id=uuid4(),
        )

        assert await _count(session, User, User.id == "user-current") == 0
        assert await _count(session, User, User.id == "user-other") == 1
        assert await _count(session, UserProfile, UserProfile.id == "profile-current") == 0
        assert await _count(session, ConsentRecord, ConsentRecord.id == "consent-current") == 0
        receipt = await session.get(DataErasureReceiptRecord, str(report.receipt_id))
        workflow = await session.get(DataErasureWorkflowRecord, str(report.workflow_id))
        assert receipt is not None
        assert workflow is not None
        assert receipt.user_ref != "user-current"
        assert workflow.user_id == receipt.user_ref
        assert workflow.target_ref is None
        assert "PRIVATE" not in json.dumps(receipt.__dict__, default=str)
    await engine.dispose()

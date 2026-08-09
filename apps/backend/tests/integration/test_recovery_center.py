"""P1-07 owner-scoped issues, idempotent actions and learning-safety evidence."""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.contracts.recovery import RecoveryCommandV1
from app.core.database import Base
from app.domains.content_knowledge import SAFETY_SCAN_CURRENT_KEY, SAFETY_SCANNER_VERSION
from app.infrastructure.outbox import OutboxStatus
from app.models.document import ProcessingStatus, UserDocument
from app.models.ledger import LearningEventRecord, OutboxTaskRecord, RecoveryEventRecord
from app.models.user import User
from app.queries.recovery import RecoveryQueryService
from app.services.documents.document_service import DocumentService
from app.services.recovery import RecoveryActionService, RecoveryIncidentService
from app.services.storage.local_storage import LocalFileStorage


async def _factory(tmp_path, monkeypatch):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'recovery.db'}")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    storage = LocalFileStorage(str(tmp_path / "documents"))
    monkeypatch.setattr(
        "app.services.documents.document_service.get_local_storage", lambda: storage
    )
    monkeypatch.setattr("app.queries.recovery.get_local_storage", lambda: storage)
    return engine, factory, storage


@pytest.mark.asyncio
async def test_failed_document_retry_is_owner_scoped_idempotent_and_preserves_dlq(
    tmp_path, monkeypatch
) -> None:
    engine, factory, storage = await _factory(tmp_path, monkeypatch)
    async with factory() as session:
        owner = User(id=str(uuid4()), pseudonym_id="recovery-owner")
        other = User(id=str(uuid4()), pseudonym_id="recovery-other")
        session.add_all((owner, other))
        await session.commit()

        documents = DocumentService(session)
        documents.storage = storage
        document = await documents.upload_document(
            owner.pseudonym_id,
            "failed.md",
            b"# Preserved source\n\nRecovery must be idempotent.",
        )
        original = await session.scalar(
            select(OutboxTaskRecord).where(
                OutboxTaskRecord.payload["document_id"].as_string() == document.id
            )
        )
        assert original is not None
        original.status = OutboxStatus.DEAD_LETTER.value
        original.attempt_count = 5
        original.last_error = "OUTBOX_TRANSIENT_ERROR:RuntimeError"
        document.processing_status = ProcessingStatus.FAILED
        document.processing_error = "safe summary"
        await session.commit()
        await session.refresh(document)

        listing = await RecoveryQueryService(session).list_issues(owner, correlation_id="query-1")
        issue = next(item for item in listing.issues if item.issue_ref.endswith(":processing"))
        assert issue.data_safety == "preserved"
        assert issue.duplicate_risk == "prevented_by_idempotency"
        assert [action.action_code for action in issue.actions] == ["retry_owner_command"]
        assert not (
            await RecoveryQueryService(session).list_issues(other, correlation_id="query-other")
        ).issues

        command = RecoveryCommandV1(
            issue_ref=issue.issue_ref,
            expected_issue_version=issue.issue_version,
            action_code="retry_owner_command",
            idempotency_key="recover-failed-document-1",
        )
        result = await RecoveryActionService(session).execute(
            owner, command, correlation_id="action-1"
        )
        assert result.status == "accepted"
        assert result.replacement_task_ref is not None

        await session.refresh(document)
        await session.refresh(original)
        assert document.processing_status == ProcessingStatus.PENDING
        assert original.status == OutboxStatus.DEAD_LETTER.value
        assert original.attempt_count == 5
        replacements = (
            await session.scalars(
                select(OutboxTaskRecord).where(
                    OutboxTaskRecord.idempotency_key.like("document:%:recovery:%")
                )
            )
        ).all()
        assert len(replacements) == 1
        assert replacements[0].payload["recovery_of"] == f"document:{document.id}:failed"

        duplicate = await RecoveryActionService(session).execute(
            owner, command, correlation_id="action-duplicate"
        )
        assert duplicate == result
        assert (
            await session.scalar(
                select(func.count()).select_from(OutboxTaskRecord).where(
                    OutboxTaskRecord.idempotency_key.like("document:%:recovery:%")
                )
            )
            == 1
        )
        assert (
            await session.scalar(select(func.count()).select_from(RecoveryEventRecord)) == 2
        )
        assert not any(
            item.issue_ref == f"outbox:{original.id}"
            for item in (
                await RecoveryQueryService(session).list_issues(
                    owner, correlation_id="after-recovery"
                )
            ).issues
        )
    await engine.dispose()


@pytest.mark.asyncio
async def test_missing_file_has_no_server_retry_and_provider_failure_is_not_learning_evidence(
    tmp_path, monkeypatch
) -> None:
    engine, factory, storage = await _factory(tmp_path, monkeypatch)
    async with factory() as session:
        owner = User(id=str(uuid4()), pseudonym_id="missing-owner")
        session.add(owner)
        missing = UserDocument(
            id=str(uuid4()),
            pseudonym_id=owner.pseudonym_id,
            original_filename="missing.pdf",
            file_extension="pdf",
            file_size_bytes=100,
            storage_path=f"{owner.pseudonym_id}/does-not-exist.pdf",
            processing_status=ProcessingStatus.FAILED,
            moderation_status="pending",
        )
        session.add(missing)
        await session.commit()

        listing = await RecoveryQueryService(session).list_issues(owner, correlation_id="missing")
        issue = next(item for item in listing.issues if item.issue_ref.endswith(":file"))
        assert issue.data_safety == "preserved_but_unavailable"
        assert [action.action_code for action in issue.actions] == ["open_data_recovery"]
        assert issue.actions[0].route == "/settings/data"

        incidents = RecoveryIncidentService(session)
        await incidents.record_model_failure(
            owner,
            activity_id="activity-1",
            code="AI_PROVIDER_TIMEOUT",
            retryable=True,
            retry_after_seconds=9,
            correlation_id="provider-failure",
        )
        provider_issue = next(
            item
            for item in (
                await RecoveryQueryService(session).list_issues(owner, correlation_id="after-failure")
            ).issues
            if item.issue_ref == "provider:activity-1"
        )
        assert provider_issue.code == "AI_PROVIDER_TIMEOUT"
        assert provider_issue.status == "waiting"
        activity_action = next(
            action for action in provider_issue.actions if action.action_code == "open_activity"
        )
        assert activity_action.route == "/learn/activity-1"
        assert await session.scalar(select(func.count()).select_from(LearningEventRecord)) == 0

        await incidents.resolve_model_issue(
            owner, activity_id="activity-1", correlation_id="provider-success"
        )
        await session.commit()
        assert not any(
            item.issue_ref == "provider:activity-1"
            for item in (
                await RecoveryQueryService(session).list_issues(owner, correlation_id="resolved")
            ).issues
        )
        events = (
            await session.scalars(
                select(RecoveryEventRecord)
                .where(RecoveryEventRecord.issue_key == "provider:activity-1")
                .order_by(RecoveryEventRecord.issue_version)
            )
        ).all()
        assert [event.event_type for event in events] == ["opened", "resolved"]
        assert await session.scalar(select(func.count()).select_from(LearningEventRecord)) == 0
    await engine.dispose()


@pytest.mark.asyncio
async def test_quarantine_action_requires_a_newer_policy(tmp_path, monkeypatch) -> None:
    engine, factory, storage = await _factory(tmp_path, monkeypatch)
    async with factory() as session:
        owner = User(id=str(uuid4()), pseudonym_id="quarantine-owner")
        session.add(owner)
        await session.commit()
        documents = DocumentService(session)
        documents.storage = storage
        document = await documents.upload_document(
            owner.pseudonym_id,
            "quarantined.md",
            b"# Preserved but unavailable",
        )
        document.processing_status = ProcessingStatus.QUARANTINED
        document.moderation_details = {
            **document.moderation_details,
            SAFETY_SCAN_CURRENT_KEY: {
                "scanner_version": SAFETY_SCANNER_VERSION,
                "verdict": "quarantine",
            },
        }
        await session.commit()

        issue = next(
            item
            for item in (
                await RecoveryQueryService(session).list_issues(
                    owner, correlation_id="same-policy"
                )
            ).issues
            if item.issue_ref.endswith(":quarantine")
        )
        assert issue.actions[0].action_code == "reinspect_document"
        assert issue.actions[0].enabled is False
        assert (
            issue.actions[0].disabled_reason_code
            == "CONTENT_REINSPECTION_POLICY_UNCHANGED"
        )
    await engine.dispose()

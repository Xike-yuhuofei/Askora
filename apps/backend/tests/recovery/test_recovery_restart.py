"""P1-07 action/result state survives process-style engine restart."""

from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.contracts.recovery import RecoveryCommandV1
from app.core.database import Base
from app.infrastructure.outbox import OutboxStatus
from app.models.document import ProcessingStatus
from app.models.ledger import OutboxTaskRecord, RecoveryEventRecord
from app.models.user import User
from app.queries.recovery import RecoveryQueryService
from app.services.documents.document_service import DocumentService
from app.services.recovery import RecoveryActionService
from app.services.storage.local_storage import LocalFileStorage


@pytest.mark.asyncio
async def test_recovery_result_and_replacement_are_restart_durable(tmp_path, monkeypatch) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'restart.db'}"
    storage = LocalFileStorage(str(tmp_path / "documents"))
    monkeypatch.setattr(
        "app.services.documents.document_service.get_local_storage", lambda: storage
    )
    monkeypatch.setattr("app.queries.recovery.get_local_storage", lambda: storage)

    first_engine = create_async_engine(database_url)
    first_factory = async_sessionmaker(first_engine, expire_on_commit=False)
    async with first_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with first_factory() as session:
        owner = User(id=str(uuid4()), pseudonym_id="restart-owner")
        session.add(owner)
        await session.commit()
        documents = DocumentService(session)
        documents.storage = storage
        document = await documents.upload_document(
            owner.pseudonym_id,
            "restart.md",
            b"# Restart durable recovery",
        )
        original = await session.scalar(
            select(OutboxTaskRecord).where(
                OutboxTaskRecord.payload["document_id"].as_string() == document.id
            )
        )
        assert original is not None
        original.status = OutboxStatus.DEAD_LETTER.value
        document.processing_status = ProcessingStatus.FAILED
        await session.commit()
        issue = next(
            item
            for item in (
                await RecoveryQueryService(session).list_issues(
                    owner, correlation_id="before-restart"
                )
            ).issues
            if item.issue_ref.endswith(":processing")
        )
        command = RecoveryCommandV1(
            issue_ref=issue.issue_ref,
            expected_issue_version=issue.issue_version,
            action_code="retry_owner_command",
            idempotency_key="restart-durable-command",
        )
        first_result = await RecoveryActionService(session).execute(
            owner, command, correlation_id="first-process"
        )
        original_id = original.id
    await first_engine.dispose()

    second_engine = create_async_engine(database_url)
    second_factory = async_sessionmaker(second_engine, expire_on_commit=False)
    async with second_factory() as session:
        restarted_owner = await session.scalar(
            select(User).where(User.pseudonym_id == "restart-owner")
        )
        assert restarted_owner is not None
        duplicate = await RecoveryActionService(session).execute(
            restarted_owner, command, correlation_id="second-process"
        )
        assert duplicate == first_result
        assert (
            await session.scalar(
                select(func.count())
                .select_from(OutboxTaskRecord)
                .where(OutboxTaskRecord.idempotency_key.like("document:%:recovery:%"))
            )
            == 1
        )
        original = await session.get(OutboxTaskRecord, original_id)
        assert original is not None
        assert original.status == OutboxStatus.DEAD_LETTER.value
        assert await session.scalar(select(func.count()).select_from(RecoveryEventRecord)) == 2
    await second_engine.dispose()

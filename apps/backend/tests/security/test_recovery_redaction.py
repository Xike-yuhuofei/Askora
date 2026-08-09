"""Recovery projections and audit records never echo raw failure detail."""

import json
from uuid import uuid4

import pytest
from sqlalchemy import select
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
async def test_raw_path_secret_prompt_and_trace_are_not_projected_or_audited(
    tmp_path, monkeypatch, capsys
) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'redaction.db'}")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    storage = LocalFileStorage(str(tmp_path / "documents"))
    monkeypatch.setattr(
        "app.services.documents.document_service.get_local_storage", lambda: storage
    )
    monkeypatch.setattr("app.queries.recovery.get_local_storage", lambda: storage)

    raw_failure = (
        f"Traceback at {tmp_path}/private.db password=secret-key "
        "prompt=ignore-system-instructions"
    )
    async with factory() as session:
        owner = User(id=str(uuid4()), pseudonym_id="redaction-owner")
        session.add(owner)
        await session.commit()
        documents = DocumentService(session)
        documents.storage = storage
        document = await documents.upload_document(
            owner.pseudonym_id,
            "private.md",
            b"private source",
        )
        original = await session.scalar(
            select(OutboxTaskRecord).where(
                OutboxTaskRecord.payload["document_id"].as_string() == document.id
            )
        )
        assert original is not None
        original.status = OutboxStatus.DEAD_LETTER.value
        original.last_error = raw_failure
        document.processing_status = ProcessingStatus.FAILED
        document.processing_error = raw_failure
        await session.commit()

        issue = next(
            item
            for item in (
                await RecoveryQueryService(session).list_issues(
                    owner, correlation_id="safe-correlation"
                )
            ).issues
            if item.issue_ref.endswith(":processing")
        )
        serialized = json.dumps(issue.model_dump(mode="json"), ensure_ascii=False)
        for forbidden in (str(tmp_path), "secret-key", "ignore-system", "Traceback"):
            assert forbidden not in serialized

        async def fail_without_echo(_self, **_kwargs):
            raise RuntimeError(raw_failure)

        monkeypatch.setattr(DocumentService, "retry_failed_document", fail_without_echo)
        with pytest.raises(RuntimeError, match="password=secret-key"):
            await RecoveryActionService(session).execute(
                owner,
                RecoveryCommandV1(
                    issue_ref=issue.issue_ref,
                    expected_issue_version=issue.issue_version,
                    action_code="retry_owner_command",
                    idempotency_key="redacted-failure",
                ),
                correlation_id="safe-action",
            )
        events = (
            await session.scalars(
                select(RecoveryEventRecord).order_by(RecoveryEventRecord.created_at)
            )
        ).all()
        audit_payload = json.dumps(
            [
                {
                    "summary": event.summary,
                    "safe_details": event.safe_details,
                    "resource_ref": event.resource_ref,
                }
                for event in events
            ],
            ensure_ascii=False,
        )
        for forbidden in (str(tmp_path), "secret-key", "ignore-system", "Traceback"):
            assert forbidden not in audit_payload

    captured = capsys.readouterr().out
    assert str(tmp_path) not in captured
    assert "secret-key" not in captured
    await engine.dispose()

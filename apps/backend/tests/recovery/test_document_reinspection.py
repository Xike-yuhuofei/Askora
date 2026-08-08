"""Explicit newer-policy reinspection remains durable, owner-scoped and fail-closed."""

from __future__ import annotations

import hashlib
import io
import zipfile
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.exceptions import ContentReinspectionPolicyUnchangedError
from app.domains.content_knowledge import (
    RAW_ASSET_CHECKSUM_KEY,
    SAFETY_REINSPECTION_KEY,
    SAFETY_SCAN_CURRENT_KEY,
    SAFETY_SCAN_RUNS_KEY,
)
from app.infrastructure.outbox import OutboxStatus
from app.main import app as fastapi_app
from app.models.document import ProcessingStatus, UserDocument
from app.models.ledger import OutboxTaskRecord
from app.models.user import User
from app.queries.library import WorkspaceLibraryQueryService
from app.services.auth.dependencies import get_current_user
from app.services.documents.document_service import (
    DOCUMENT_REINSPECTION_TASK_TYPE,
    DocumentService,
    document_processing_idempotency_key,
)
from app.services.documents.processing_worker import DocumentProcessingWorker
from app.services.storage.local_storage import LocalFileStorage


def _epub_bytes() -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        mimetype = zipfile.ZipInfo("mimetype")
        mimetype.compress_type = zipfile.ZIP_STORED
        archive.writestr(mimetype, b"application/epub+zip")
        archive.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
  <rootfiles><rootfile full-path="OEBPS/content.opf"
    media-type="application/oebps-package+xml"/></rootfiles>
</container>""",
            compress_type=zipfile.ZIP_DEFLATED,
        )
        archive.writestr(
            "OEBPS/content.opf",
            """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid" version="2.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">reinspection-book</dc:identifier>
    <dc:title>复检教材</dc:title><dc:language>zh</dc:language>
  </metadata>
  <manifest><item id="chapter" href="chapter.xhtml"
    media-type="application/xhtml+xml"/></manifest>
  <spine><itemref idref="chapter"/></spine>
</package>""",
            compress_type=zipfile.ZIP_DEFLATED,
        )
        archive.writestr(
            "OEBPS/chapter.xhtml",
            """<html xmlns="http://www.w3.org/1999/xhtml"><body>
<h1>递归与形式系统</h1><p>合法教材内容。</p>
</body></html>""",
            compress_type=zipfile.ZIP_DEFLATED,
        )
    return stream.getvalue()


async def _factory(tmp_path, monkeypatch):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'reinspection.db'}")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    storage = LocalFileStorage(str(tmp_path / "documents"))
    monkeypatch.setattr(
        "app.services.documents.document_service.get_local_storage",
        lambda: storage,
    )
    return engine, factory, storage


async def _legacy_quarantined_document(session, storage, pseudonym_id: str) -> UserDocument:
    service = DocumentService(session)
    service.storage = storage
    document = await service.upload_document(
        pseudonym_id,
        "legacy.epub",
        _epub_bytes(),
    )
    original_task = await session.scalar(
        select(OutboxTaskRecord).where(
            OutboxTaskRecord.idempotency_key == document_processing_idempotency_key(document.id)
        )
    )
    assert original_task is not None
    original_task.status = OutboxStatus.COMPLETED.value
    document.processing_status = ProcessingStatus.QUARANTINED
    document.moderation_status = "rejected"
    document.moderation_details = {
        "reason": "security_scan_failed",
        "threats": ["legacy false positive"],
    }
    await session.commit()
    return document


@pytest.mark.asyncio
async def test_legacy_quarantine_reinspection_is_append_only_durable_and_modelable(
    tmp_path, monkeypatch
) -> None:
    engine, factory, storage = await _factory(tmp_path, monkeypatch)
    async with factory() as session:
        user = User(id=str(uuid4()), pseudonym_id="reinspection-owner")
        session.add(user)
        await session.commit()
        document = await _legacy_quarantined_document(session, storage, user.pseudonym_id)
        service = DocumentService(session)
        service.storage = storage

        queued, status = await service.request_reinspection(
            document_id=document.id,
            pseudonym_id=user.pseudonym_id,
        )
        assert status == "accepted"
        assert queued.processing_status == ProcessingStatus.QUARANTINED
        assert queued.moderation_details[SAFETY_REINSPECTION_KEY]["status"] == "pending"
        _, duplicate_status = await service.request_reinspection(
            document_id=document.id,
            pseudonym_id=user.pseudonym_id,
        )
        assert duplicate_status == "already_pending"
        assert (
            await session.scalar(
                select(func.count())
                .select_from(OutboxTaskRecord)
                .where(OutboxTaskRecord.type == DOCUMENT_REINSPECTION_TASK_TYPE)
            )
            == 1
        )

        library = await WorkspaceLibraryQueryService(session).list_library(
            user,
            status=None,
            subject=None,
            page=1,
            page_size=20,
            correlation_id="reinspection-pending",
        )
        assert "CONTENT_REINSPECTION_PENDING" in library.data.documents[0].reason_codes
        blocked_map = await WorkspaceLibraryQueryService(session).get_knowledge_map(
            user,
            document_id=document.id,
            correlation_id="reinspection-blocked-map",
        )
        assert blocked_map.data.nodes == ()
        assert "CONTENT_QUARANTINED" in blocked_map.source_status[0].reason_codes

    worker = DocumentProcessingWorker(factory)
    assert await worker.run_once() is True
    async with factory() as session:
        rescanned = await session.get(UserDocument, document.id)
        assert rescanned is not None
        assert rescanned.processing_status == ProcessingStatus.PENDING
        assert rescanned.moderation_details[SAFETY_REINSPECTION_KEY]["outcome"] == "allow"
        assert RAW_ASSET_CHECKSUM_KEY in rescanned.moderation_details
        runs = rescanned.moderation_details[SAFETY_SCAN_RUNS_KEY]
        assert len(runs) == 2
        assert runs[0]["scanner_version"] == "legacy-unversioned"
        assert runs[0]["threats"] == ["legacy false positive"]
        assert "LEGACY_RAW_ASSET_CHECKSUM_BASELINE_ESTABLISHED" in runs[1]["reason_codes"]

        # Simulate a crash after the domain commit but before the outbox task was acknowledged.
        reinspection_task = await session.scalar(
            select(OutboxTaskRecord).where(OutboxTaskRecord.type == DOCUMENT_REINSPECTION_TASK_TYPE)
        )
        assert reinspection_task is not None
        reinspection_task.status = OutboxStatus.PENDING.value
        await session.commit()

    assert await worker.run_once() is True
    async with factory() as session:
        replayed = await session.get(UserDocument, document.id)
        assert replayed is not None
        assert replayed.processing_status == ProcessingStatus.PENDING
        assert len(replayed.moderation_details[SAFETY_SCAN_RUNS_KEY]) == 2

    assert await worker.run_once() is True
    async with factory() as session:
        completed = await session.get(UserDocument, document.id)
        assert completed is not None
        assert completed.processing_status == ProcessingStatus.COMPLETED
        assert completed.chunk_count > 0
        assert len(completed.moderation_details[SAFETY_SCAN_RUNS_KEY]) == 2
        assert completed.moderation_details[SAFETY_SCAN_CURRENT_KEY]["verdict"] == "allow"
    await engine.dispose()


@pytest.mark.asyncio
async def test_same_scanner_policy_cannot_reinspect_quarantine(tmp_path, monkeypatch) -> None:
    engine, factory, storage = await _factory(tmp_path, monkeypatch)
    async with factory() as session:
        user = User(id=str(uuid4()), pseudonym_id="same-policy-owner")
        session.add(user)
        await session.commit()
        service = DocumentService(session)
        service.storage = storage
        document = await service.upload_document(
            user.pseudonym_id,
            "unsafe.epub",
            _epub_bytes(),
        )
        document.processing_status = ProcessingStatus.QUARANTINED
        document.moderation_status = "rejected"
        document.moderation_details = {
            **document.moderation_details,
            SAFETY_SCAN_CURRENT_KEY: {
                "scanner_version": "document-safety-v2",
                "verdict": "quarantine",
                "reason_codes": ["EPUB_ENTRY_PATH_UNSAFE"],
            },
        }
        await session.commit()

        with pytest.raises(ContentReinspectionPolicyUnchangedError):
            await service.request_reinspection(
                document_id=document.id,
                pseudonym_id=user.pseudonym_id,
            )
    await engine.dispose()


@pytest.mark.asyncio
async def test_reinspection_checksum_mismatch_dead_letters_and_stays_quarantined(
    tmp_path, monkeypatch
) -> None:
    engine, factory, storage = await _factory(tmp_path, monkeypatch)
    async with factory() as session:
        user = User(id=str(uuid4()), pseudonym_id="checksum-owner")
        session.add(user)
        await session.commit()
        document = await _legacy_quarantined_document(session, storage, user.pseudonym_id)
        original_checksum = hashlib.sha256(storage.read_file(document.storage_path)).hexdigest()
        document.moderation_details = {
            **document.moderation_details,
            RAW_ASSET_CHECKSUM_KEY: original_checksum,
        }
        await session.commit()
        service = DocumentService(session)
        service.storage = storage
        await service.request_reinspection(
            document_id=document.id,
            pseudonym_id=user.pseudonym_id,
        )
        stored_path = storage.base_path / document.storage_path
        stored_path.write_bytes(_epub_bytes() + b"changed")

    worker = DocumentProcessingWorker(factory)
    assert await worker.run_once() is True
    async with factory() as session:
        stored = await session.get(UserDocument, document.id)
        assert stored is not None
        assert stored.processing_status == ProcessingStatus.QUARANTINED
        assert stored.moderation_details[SAFETY_REINSPECTION_KEY]["status"] == "failed"
        task = await session.scalar(
            select(OutboxTaskRecord).where(OutboxTaskRecord.type == DOCUMENT_REINSPECTION_TASK_TYPE)
        )
        assert task is not None
        assert task.status == OutboxStatus.DEAD_LETTER.value
    await engine.dispose()


@pytest.mark.asyncio
async def test_reinspection_http_is_owner_scoped_and_idempotent(tmp_path, monkeypatch) -> None:
    engine, factory, storage = await _factory(tmp_path, monkeypatch)
    owner_id = str(uuid4())
    async with factory() as session:
        owner = User(id=owner_id, pseudonym_id="http-reinspection-owner")
        other = User(id=str(uuid4()), pseudonym_id="http-reinspection-other")
        session.add_all([owner, other])
        await session.commit()
        document = await _legacy_quarantined_document(session, storage, owner.pseudonym_id)
        other_document = await _legacy_quarantined_document(session, storage, other.pseudonym_id)

    async def override_get_db():
        async with factory() as session:
            yield session

    async def override_get_current_user():
        async with factory() as session:
            user = await session.get(User, owner_id)
            assert user is not None
            return user

    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[get_current_user] = override_get_current_user
    try:
        async with AsyncClient(
            transport=ASGITransport(app=fastapi_app),
            base_url="http://test",
        ) as client:
            accepted = await client.post(f"/api/v1/documents/{document.id}/reinspect")
            duplicate = await client.post(f"/api/v1/documents/{document.id}/reinspect")
            hidden = await client.post(f"/api/v1/documents/{other_document.id}/reinspect")
        assert accepted.status_code == 202, accepted.text
        assert accepted.json()["status"] == "accepted"
        assert duplicate.status_code == 202
        assert duplicate.json()["status"] == "already_pending"
        assert hidden.status_code == 404
        assert hidden.json()["error"]["code"] == "DATA-0001"
    finally:
        fastapi_app.dependency_overrides.clear()
    await engine.dispose()

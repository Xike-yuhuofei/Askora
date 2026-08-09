"""SQLite/API integration tests for UI-02A library and scoped knowledge map."""

from __future__ import annotations

import io
import zipfile
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base
from app.core.exceptions import ResourceNotFoundError
from app.models.user import User
from app.queries.library import WorkspaceLibraryQueryService
from app.services.documents.document_service import DocumentService
from app.services.storage.local_storage import LocalFileStorage

NOW = datetime(2026, 8, 8, 2, 0, tzinfo=timezone.utc)


def _epub_bytes(*, unsafe_path: bool = False) -> bytes:
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
    <dc:identifier id="bookid">integration-book</dc:identifier>
    <dc:title>SQL 教材</dc:title><dc:language>zh</dc:language>
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
<h1>SQL 查询</h1><p>教材可以展示 ' OR SELECT，但内容永远不执行。</p>
</body></html>""",
            compress_type=zipfile.ZIP_DEFLATED,
        )
        if unsafe_path:
            archive.writestr("../escape.txt", b"blocked")
    return stream.getvalue()


def _engine_and_factory(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'library.db'}")

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine, async_sessionmaker(engine, expire_on_commit=False)


@pytest.mark.asyncio
async def test_ui02a_library_query_is_scoped_source_bound_and_relation_honest(tmp_path) -> None:
    """UI02A-AC-001/004/005/006: real source candidates, no fake edges/leak."""
    engine, factory = _engine_and_factory(tmp_path)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as session:
        user = User(id=str(uuid4()), pseudonym_id="library-owner")
        other = User(id=str(uuid4()), pseudonym_id="library-other")
        session.add_all([user, other])
        await session.commit()

        service = DocumentService(session)
        service.storage = LocalFileStorage(str(tmp_path / "documents"))
        document = await service.upload_document(
            user.pseudonym_id,
            "algebra.md",
            (
                "# 等式性质\n\n等式两边同时加上相同的数，等式仍成立。\n\n"
                "# 解一元一次方程\n\n移项后合并同类项。\n\n"
                "[grader-only]\n参考答案：x = 2"
            ).encode(),
            subject="math",
        )
        other_document = await service.upload_document(
            other.pseudonym_id,
            "private.md",
            b"# Other secret\n\nDo not leak this document.",
        )
        await service.process_document(document.id)
        await service.process_document(other_document.id)

        query = WorkspaceLibraryQueryService(session, clock=lambda: NOW)
        library = await query.list_library(
            user,
            status=None,
            subject=None,
            page=1,
            page_size=20,
            correlation_id="library-query",
        )
        assert library.data.total == 1
        item = library.data.documents[0]
        assert item.title == "algebra.md"
        assert item.knowledge_status == "PUBLISHED"
        assert item.knowledge_unit_count == 2
        assert "storage_path" not in item.model_dump()

        targeted = await query.list_library(
            user,
            status=None,
            subject=None,
            document_id=document.id,
            page=1,
            page_size=20,
            correlation_id="library-targeted-query",
        )
        assert [entry.document_id for entry in targeted.data.documents] == [UUID(document.id)]
        cross_owner_target = await query.list_library(
            user,
            status=None,
            subject=None,
            document_id=other_document.id,
            page=1,
            page_size=20,
            correlation_id="library-cross-owner-target",
        )
        assert cross_owner_target.data.documents == ()

        knowledge_map = await query.get_knowledge_map(
            user,
            document_id=document.id,
            correlation_id="map-query",
        )
        assert [node.canonical_name for node in knowledge_map.data.nodes] == [
            "等式性质",
            "解一元一次方程",
        ]
        assert all(node.status == "published" for node in knowledge_map.data.nodes)
        assert knowledge_map.data.edges == ()
        assert all("参考答案" not in span.excerpt for span in knowledge_map.data.source_spans)
        assert "NO_VERIFIED_RELATIONS" in knowledge_map.source_status[0].reason_codes
        with pytest.raises(ResourceNotFoundError):
            await query.get_knowledge_map(
                user,
                document_id=other_document.id,
                correlation_id="cross-user",
            )
    await engine.dispose()


@pytest.mark.asyncio
async def test_epub_processing_persists_scan_record_and_exposes_safe_reason_codes(tmp_path) -> None:
    """Valid code textbooks process; unsafe archives quarantine before modeling."""
    engine, factory = _engine_and_factory(tmp_path)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as session:
        user = User(id=str(uuid4()), pseudonym_id="epub-owner")
        session.add(user)
        await session.commit()
        service = DocumentService(session)
        service.storage = LocalFileStorage(str(tmp_path / "epub-documents"))

        valid = await service.upload_document(user.pseudonym_id, "sql.epub", _epub_bytes())
        await service.process_document(valid.id)
        assert valid.processing_status == "completed"
        assert valid.moderation_details["security_scan"]["scanner_version"] == "document-safety-v3"
        assert valid.moderation_details["security_scan"]["verdict"] == "allow"
        assert valid.moderation_details["security_scan"]["reason_codes"] == []
        assert valid.chunk_count > 0

        unsafe = await service.upload_document(
            user.pseudonym_id,
            "unsafe.epub",
            _epub_bytes(unsafe_path=True),
        )
        await service.process_document(unsafe.id)
        assert unsafe.processing_status == "quarantined"
        assert unsafe.moderation_details["security_scan"]["verdict"] == "quarantine"
        assert (
            "EPUB_ENTRY_PATH_UNSAFE" in unsafe.moderation_details["security_scan"]["reason_codes"]
        )
        assert unsafe.chunk_count == 0
        assert "content_knowledge_v1" not in unsafe.moderation_details

        broken = await service.upload_document(
            user.pseudonym_id,
            "broken.epub",
            b"PK\x03\x04not-a-valid-archive",
        )
        await service.process_document(broken.id)
        assert broken.processing_status == "rejected"
        assert broken.moderation_details["security_scan"]["verdict"] == "reject"
        assert "EPUB_ARCHIVE_INVALID" in broken.moderation_details["security_scan"]["reason_codes"]

        query = WorkspaceLibraryQueryService(session, clock=lambda: NOW)
        library = await query.list_library(
            user,
            status=None,
            subject=None,
            page=1,
            page_size=20,
            correlation_id="epub-library-query",
        )
        by_title = {item.title: item for item in library.data.documents}
        assert by_title["sql.epub"].knowledge_status == "PUBLISHED"
        assert by_title["unsafe.epub"].knowledge_status == "NOT_MODELED"
        assert by_title["unsafe.epub"].reason_codes == (
            "CONTENT_REVISION_MISSING",
            "CONTENT_QUARANTINED",
            "EPUB_ENTRY_PATH_UNSAFE",
        )
        assert by_title["broken.epub"].reason_codes == (
            "CONTENT_REVISION_MISSING",
            "CONTENT_REJECTED",
            "EPUB_ARCHIVE_INVALID",
        )
        assert library.data.view_state == "PARTIAL"
    await engine.dispose()


@pytest.mark.asyncio
async def test_ui02a_http_queries_are_private_and_require_valid_scope(tmp_path) -> None:
    """EXEC016-AC-002/005: HTTP is private, current-user scoped and strict."""
    from httpx import ASGITransport, AsyncClient

    from app.core.database import get_db
    from app.main import app as fastapi_app
    from app.services.auth.dependencies import get_current_user

    engine, factory = _engine_and_factory(tmp_path)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    user_id = str(uuid4())
    async with factory() as session:
        user = User(id=user_id, pseudonym_id="library-http")
        session.add(user)
        await session.commit()
        service = DocumentService(session)
        service.storage = LocalFileStorage(str(tmp_path / "http-documents"))
        document = await service.upload_document(user.pseudonym_id, "topic.md", b"# Topic\n\nFact.")
        await service.process_document(document.id)

    async def override_get_db():
        async with factory() as session:
            yield session

    async def override_get_current_user():
        async with factory() as session:
            user = await session.get(User, user_id)
            assert user is not None
            return user

    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[get_current_user] = override_get_current_user
    try:
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            library = await client.get("/api/v1/workspace/library")
            knowledge_map = await client.get(
                "/api/v1/workspace/knowledge-map",
                params={"document_id": document.id},
            )
            invalid = await client.get(
                "/api/v1/workspace/knowledge-map",
                params={"document_id": "not-a-uuid"},
            )
        assert library.status_code == 200, library.text
        assert knowledge_map.status_code == 200, knowledge_map.text
        assert library.headers["cache-control"] == "private, no-store"
        assert knowledge_map.headers["cache-control"] == "private, no-store"
        assert "storage_path" not in library.text
        assert invalid.status_code == 422
    finally:
        fastapi_app.dependency_overrides.clear()
    await engine.dispose()

"""SQLite/API integration tests for UI-02A library and scoped knowledge map."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

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
        assert item.knowledge_status == "CANDIDATES"
        assert item.knowledge_unit_count == 2
        assert "storage_path" not in item.model_dump()

        knowledge_map = await query.get_knowledge_map(
            user,
            document_id=document.id,
            correlation_id="map-query",
        )
        assert [node.canonical_name for node in knowledge_map.data.nodes] == [
            "等式性质",
            "解一元一次方程",
        ]
        assert all(node.status == "candidate" for node in knowledge_map.data.nodes)
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

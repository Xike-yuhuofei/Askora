"""P1-04A/B integration coverage for canonical SYS01 library management."""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base
from app.core.exceptions import LibraryMetadataVersionConflictError
from app.models.user import User
from app.queries.library import WorkspaceLibraryQueryService
from app.services.documents.document_service import DocumentService
from app.services.documents.library_management import LibraryManagementService
from app.services.storage.local_storage import LocalFileStorage


async def _database(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'p104.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


@pytest.mark.asyncio
async def test_metadata_search_and_batch_are_versioned_idempotent_and_owner_scoped(
    tmp_path,
) -> None:
    """LIB-AC-001..003/005: canonical metadata and explicit batch behavior."""
    engine, factory = await _database(tmp_path)
    async with factory() as session:
        owner = User(id=str(uuid4()), pseudonym_id="p104-owner")
        other = User(id=str(uuid4()), pseudonym_id="p104-other")
        session.add_all([owner, other])
        await session.commit()
        service = DocumentService(session)
        service.storage = LocalFileStorage(str(tmp_path / "documents"))
        document = await service.upload_document(
            owner.pseudonym_id,
            "original.md",
            "# 热力学\n\n熵增原理描述孤立系统的演化方向。".encode(),
        )
        private = await service.upload_document(
            other.pseudonym_id,
            "private.md",
            "# 私密\n\n熵增原理不能跨用户泄漏。".encode(),
        )
        await service.process_document(document.id)
        await service.process_document(private.id)
        original_revision = document.moderation_details["content_knowledge_v1"][
            "current_revision_id"
        ]

        management = LibraryManagementService(session)
        tag = await management.create_tag(
            pseudonym_id=owner.pseudonym_id,
            name="核心概念",
            idempotency_key="tag-create-001",
        )
        collection = await management.create_collection(
            pseudonym_id=owner.pseudonym_id,
            name="物理教材",
            idempotency_key="collection-create-001",
        )
        updated = await management.update_metadata(
            document_id=document.id,
            pseudonym_id=owner.pseudonym_id,
            expected_version=1,
            idempotency_key="metadata-update-001",
            changes={
                "display_title": "热力学导论",
                "author": "测试作者",
                "language": "zh-CN",
            },
        )
        replay = await management.update_metadata(
            document_id=document.id,
            pseudonym_id=owner.pseudonym_id,
            expected_version=1,
            idempotency_key="metadata-update-001",
            changes={
                "display_title": "热力学导论",
                "author": "测试作者",
                "language": "zh-CN",
            },
        )
        assert replay == updated
        assert (
            document.moderation_details["content_knowledge_v1"]["current_revision_id"]
            == original_revision
        )
        with pytest.raises(LibraryMetadataVersionConflictError):
            await management.update_metadata(
                document_id=document.id,
                pseudonym_id=owner.pseudonym_id,
                expected_version=1,
                idempotency_key="metadata-update-stale",
                changes={"display_title": "错误覆盖"},
            )

        batch = await management.batch_organize(
            pseudonym_id=owner.pseudonym_id,
            document_ids=[document.id],
            expected_versions={document.id: 2},
            idempotency_key="batch-organize-001",
            subject_supplied=True,
            subject="physics",
            add_tag_ids=[str(tag.tag_id)],
            remove_tag_ids=[],
            add_collection_ids=[str(collection.collection_id)],
            remove_collection_ids=[],
            archive=None,
        )
        batch_replay = await management.batch_organize(
            pseudonym_id=owner.pseudonym_id,
            document_ids=[document.id],
            expected_versions={document.id: 2},
            idempotency_key="batch-organize-001",
            subject_supplied=True,
            subject="physics",
            add_tag_ids=[str(tag.tag_id)],
            remove_tag_ids=[],
            add_collection_ids=[str(collection.collection_id)],
            remove_collection_ids=[],
            archive=None,
        )
        assert batch_replay == batch

        result = await WorkspaceLibraryQueryService(session).list_library(
            owner,
            workspace_id=document.workspace_id,
            status=None,
            subject="physics",
            query_text="熵增原理",
            tag_id=tag.tag_id,
            collection_id=collection.collection_id,
            page=1,
            page_size=20,
            correlation_id="search",
        )
        assert result.data.total == 1
        item = result.data.documents[0]
        assert item.title == "热力学导论"
        assert item.match_field == "body"
        assert item.match_source_span_ref is not None
        assert [value.name for value in item.tags] == ["核心概念"]
        assert [value.name for value in item.collections] == ["物理教材"]

        await management.batch_organize(
            pseudonym_id=owner.pseudonym_id,
            document_ids=[document.id],
            expected_versions={document.id: 3},
            idempotency_key="batch-archive-001",
            subject_supplied=False,
            subject=None,
            add_tag_ids=[],
            remove_tag_ids=[],
            add_collection_ids=[],
            remove_collection_ids=[],
            archive=True,
        )
        active = await WorkspaceLibraryQueryService(session).list_library(
            owner,
            workspace_id=document.workspace_id,
            status=None,
            subject=None,
            page=1,
            page_size=20,
            correlation_id="active",
        )
        archived = await WorkspaceLibraryQueryService(session).list_library(
            owner,
            workspace_id=document.workspace_id,
            status=None,
            subject=None,
            archived=True,
            page=1,
            page_size=20,
            correlation_id="archived",
        )
        assert active.data.total == 0
        assert archived.data.total == 1
        assert service.storage.get_file_size(document.storage_path) == document.file_size_bytes
    await engine.dispose()


@pytest.mark.asyncio
async def test_exact_duplicate_stays_a_user_decision_and_archive_keeps_raw_asset(tmp_path) -> None:
    """LIB-AC-004/005: checksum match proposes; it never silently merges."""
    engine, factory = await _database(tmp_path)
    async with factory() as session:
        owner = User(id=str(uuid4()), pseudonym_id="p104-duplicate-owner")
        session.add(owner)
        await session.commit()
        service = DocumentService(session)
        service.storage = LocalFileStorage(str(tmp_path / "duplicate-documents"))
        raw = "# 同一资料\n\n重复内容必须由用户决定。".encode()
        first = await service.upload_document(owner.pseudonym_id, "first.md", raw)
        second = await service.upload_document(owner.pseudonym_id, "second.md", raw)
        await service.process_document(first.id)
        await service.process_document(second.id)

        management = LibraryManagementService(session)
        suggestions = await management.list_duplicate_suggestions(owner.pseudonym_id)
        assert len(suggestions) == 1
        suggestion = suggestions[0]
        assert suggestion.kind == "EXACT_DUPLICATE"
        assert not first.is_deleted and not second.is_deleted

        resolved = await management.resolve_duplicate(
            suggestion_id=str(suggestion.suggestion_id),
            pseudonym_id=owner.pseudonym_id,
            expected_version=suggestion.version,
            idempotency_key="duplicate-resolve-001",
            action="ARCHIVE_CANDIDATE",
        )
        assert resolved.status == "archived"
        assert second.is_deleted
        assert service.storage.get_file_size(second.storage_path) == second.file_size_bytes
    await engine.dispose()

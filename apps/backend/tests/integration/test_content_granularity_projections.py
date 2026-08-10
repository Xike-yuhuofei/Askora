"""EXEC-018 deterministic multi-granularity projection acceptance tests."""

from __future__ import annotations

import copy
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models  # noqa: F401
from app.core.database import Base
from app.domains.content_knowledge import CONTENT_RECORD_KEY
from app.models.document import DocumentChunk
from app.models.user import User, UserRole, UserStatus
from app.queries.library import WorkspaceLibraryQueryService
from app.services.documents.document_service import DocumentService
from app.services.storage.local_storage import LocalFileStorage
from tests.fixtures.minimal_epub import minimal_structured_epub

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
async def granularity_db(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'granularity.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session, tmp_path
    await engine.dispose()


async def _create_user(db, suffix: str) -> User:
    user = User(
        id=str(uuid4()),
        pseudonym_id=f"exec018-{suffix}",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    await db.commit()
    return user


def _service(db, tmp_path) -> DocumentService:
    service = DocumentService(db)
    service.storage = LocalFileStorage(str(tmp_path / "documents"))
    return service


@pytest.mark.asyncio
async def test_exec018_epub_granularities_trace_and_rebuild_independently(
    granularity_db,
) -> None:
    """D02-AC-001..006: working sets differ, trace and rebuild without truth drift."""
    db, tmp_path = granularity_db
    user = await _create_user(db, "epub")
    service = _service(db, tmp_path)
    document = await service.upload_document(
        user.pseudonym_id,
        "structured.epub",
        minimal_structured_epub(),
    )
    await service.process_document(document.id)
    await db.refresh(document)

    revision = document.moderation_details[CONTENT_RECORD_KEY]["revisions"][0]
    span_ids = {item["span_id"] for item in revision["source_spans"]}
    document_node_ids = {item["node_id"] for item in revision["document_nodes"]}
    hierarchy_ids = {item["hierarchy_node_id"] for item in revision["hierarchy_nodes"]}

    assert revision["semantic_segmentation_version"] != revision["retrieval_segmentation_version"]
    assert revision["semantic_units"]
    assert revision["retrieval_chunks"]
    assert any(len(item["source_span_ids"]) == 2 for item in revision["retrieval_chunks"])
    assert all(len(item["source_span_ids"]) == 1 for item in revision["semantic_units"])
    assert all(set(item["source_span_ids"]) <= span_ids for item in revision["semantic_units"])
    assert all(
        set(item["parent_node_ids"]) <= document_node_ids for item in revision["semantic_units"]
    )
    assert all(
        item["evidence_ref"]["source_span_ids"] == item["source_span_ids"]
        and item["evidence_ref"]["evidence_hash"]
        for item in revision["semantic_units"]
    )
    assert all(
        set(item["hierarchy_scope_refs"]) <= hierarchy_ids for item in revision["retrieval_chunks"]
    )
    assert all("prerequisite" not in key for item in revision["hierarchy_nodes"] for key in item)
    assert all("evidence_spans" not in key for key in revision)

    canonical_before = copy.deepcopy(
        {
            "knowledge_units": revision["knowledge_units"],
            "relations": revision["relations"],
        }
    )
    projections_before = copy.deepcopy(
        {
            "semantic_units": revision["semantic_units"],
            "hierarchy_nodes": revision["hierarchy_nodes"],
            "retrieval_chunks": revision["retrieval_chunks"],
        }
    )
    removed = copy.deepcopy(document.moderation_details)
    removed_revision = removed[CONTENT_RECORD_KEY]["revisions"][0]
    for key in projections_before:
        removed_revision.pop(key)
    document.moderation_details = removed
    await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
    await db.commit()

    rebuilt_revision = await service.rebuild_content_projections(document.id)
    assert {key: rebuilt_revision[key] for key in projections_before} == projections_before
    assert {
        "knowledge_units": rebuilt_revision["knowledge_units"],
        "relations": rebuilt_revision["relations"],
    } == canonical_before

    rebuilt_count = await service.rebuild_chunk_projection(document.id)
    chunks = (
        await db.scalars(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document.id)
            .order_by(DocumentChunk.chunk_index)
        )
    ).all()
    assert rebuilt_count == len(projections_before["retrieval_chunks"]) == len(chunks)
    assert all(item.chunk_metadata["revision_id"] == revision["revision_id"] for item in chunks)
    assert all(item.chunk_metadata["hierarchy_scope_refs"] for item in chunks)
    await db.refresh(document)
    final_revision = document.moderation_details[CONTENT_RECORD_KEY]["revisions"][0]
    assert {
        "knowledge_units": final_revision["knowledge_units"],
        "relations": final_revision["relations"],
    } == canonical_before

    knowledge_map = await WorkspaceLibraryQueryService(db).get_knowledge_map(
        user,
        workspace_id=document.workspace_id,
        document_id=UUID(document.id),
        correlation_id="exec018-map",
    )
    assert "HIERARCHY_PROJECTION_AVAILABLE" in knowledge_map.source_status[0].reason_codes


@pytest.mark.asyncio
async def test_exec018_grader_only_projection_never_mixes_visibility(granularity_db) -> None:
    """EXEC018-AC-006: protected material has explicit exposure and isolated chunks."""
    db, tmp_path = granularity_db
    user = await _create_user(db, "visibility")
    service = _service(db, tmp_path)
    content = (FIXTURES / "malicious_document.md").read_bytes()
    document = await service.upload_document(user.pseudonym_id, "visibility.md", content)
    await service.process_document(document.id)
    await db.refresh(document)

    revision = document.moderation_details[CONTENT_RECORD_KEY]["revisions"][0]
    grader_chunks = [
        item for item in revision["retrieval_chunks"] if item["allowed_use"] == "grader_only"
    ]
    learner_chunks = [
        item for item in revision["retrieval_chunks"] if item["allowed_use"] == "learner_visible"
    ]
    assert grader_chunks and learner_chunks
    assert all(item["answer_exposure"] == "COMPLETE" for item in grader_chunks)
    assert all(item["answer_exposure"] == "NONE" for item in learner_chunks)
    grader_spans = {span_id for item in grader_chunks for span_id in item["source_span_ids"]}
    learner_spans = {span_id for item in learner_chunks for span_id in item["source_span_ids"]}
    assert grader_spans.isdisjoint(learner_spans)

    persisted = (
        await db.scalars(select(DocumentChunk).where(DocumentChunk.document_id == document.id))
    ).all()
    assert any(
        item.chunk_metadata["allowed_use"] == "grader_only"
        and item.chunk_metadata["answer_exposure"] == "COMPLETE"
        and item.chunk_metadata["exposure_level"] == 4
        for item in persisted
    )

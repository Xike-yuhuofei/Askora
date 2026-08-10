"""EXEC-020 published knowledge projection and canonical SYS02 binding tests."""

from __future__ import annotations

import copy
from dataclasses import replace
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models  # noqa: F401
from app.contracts.adaptive import AnswerExposure
from app.core.database import Base
from app.domains.content_knowledge import CONTENT_RECORD_KEY
from app.domains.retrieval import AdaptiveEvidenceRetriever, HybridEvidenceRetriever
from app.models.document import DocumentChunk
from app.models.user import User, UserRole, UserStatus
from app.services.documents.document_service import DocumentService
from app.services.rag_service import PublishedKnowledgeRAGService
from app.services.storage.local_storage import LocalFileStorage
from tests.fixtures.v03_execution_factory import make_action, make_candidate
from tests.fixtures.v03_policy_factory import fixed_uuid


@pytest.fixture
async def retrieval_db(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'retrieval.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session, tmp_path
    await engine.dispose()


async def _user(db) -> User:
    user = User(
        id=str(uuid4()),
        pseudonym_id="exec020-owner",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    await db.commit()
    return user


def _document_service(db, tmp_path: Path) -> DocumentService:
    service = DocumentService(db)
    service.storage = LocalFileStorage(str(tmp_path / "documents"))
    return service


def _current_revision(document) -> dict:
    record = document.moderation_details[CONTENT_RECORD_KEY]
    return next(
        item for item in record["revisions"] if item["revision_id"] == record["current_revision_id"]
    )


@pytest.mark.asyncio
async def test_exec020_published_projection_builds_traceable_bundle_and_rebuilds(
    retrieval_db,
) -> None:
    """AC-001/003/007/008: one hybrid path binds exact published refs and rebuilds."""
    db, tmp_path = retrieval_db
    user = await _user(db)
    documents = _document_service(db, tmp_path)
    document = await documents.upload_document(
        user.pseudonym_id,
        "fractions.md",
        (
            "# Fractions\n\nDefinition: Fractions represent parts of a whole.\n\n"
            "# Ratios\n\nFractions are a prerequisite for Ratios."
        ).encode(),
    )
    await documents.process_document(document.id)
    await db.refresh(document)
    revision = _current_revision(document)
    published_ids = {
        UUID(item["knowledge_unit_id"])
        for item in revision["knowledge_units"]
        if item["status"] == "published"
    }
    assert published_ids
    assert any(item["relation_refs"] for item in revision["retrieval_chunks"])
    assert all(
        item["projection_versions"]["material_revision"] == revision["revision_id"]
        for item in revision["retrieval_chunks"]
    )

    result = await PublishedKnowledgeRAGService(db).build_evidence_bundle(
        workspace_id=document.workspace_id,
        pseudonym_id=user.pseudonym_id,
        query="Fractions parts whole prerequisite Ratios",
        teaching_action=make_action({"case_id": "exec020", "mastery": 0.9}),
        source_scope={"document_ids": [document.id]},
    )
    assert result.bundle.items
    assert result.trace.reason_codes[0] == "hybrid-rrf-tightening/2.0"
    assert len(result.trace.cache_identity) == 64
    assert all(set(item.knowledge_unit_ids) <= published_ids for item in result.bundle.items)
    selected_trace = {
        item.evidence_id: item for item in result.trace.candidate_table if item.selected
    }
    for item in result.bundle.items:
        trace = selected_trace[str(item.evidence_id)]
        assert trace.knowledge_unit_refs
        assert trace.projection_versions
        for span_id in item.source_span_ids:
            replay = await documents.get_source_span(document.id, str(span_id))
            assert replay is not None
            assert replay["revision_id"] == revision["revision_id"]
    assert all(key.startswith(f"document:{document.id}:") for key in result.bundle.index_versions)

    truth_before = copy.deepcopy(
        {
            "knowledge_units": revision["knowledge_units"],
            "relations": revision["relations"],
            "knowledge_publication_result": revision["knowledge_publication_result"],
        }
    )
    projection_before = copy.deepcopy(revision["retrieval_chunks"])
    details = copy.deepcopy(document.moderation_details)
    current = _current_revision(document)
    current.pop("retrieval_chunks")
    document.moderation_details = details
    await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
    await db.commit()

    rebuilt = await documents.rebuild_content_projections(document.id)
    assert rebuilt["retrieval_chunks"] == projection_before
    assert {key: rebuilt[key] for key in truth_before} == truth_before
    assert await documents.rebuild_chunk_projection(document.id) == len(projection_before)


@pytest.mark.asyncio
async def test_exec020_tampered_stale_or_unpublished_projection_is_not_executable(
    retrieval_db,
) -> None:
    """AC-002/004/006: invalid binding is excluded before learner-visible selection."""
    db, tmp_path = retrieval_db
    user = await _user(db)
    documents = _document_service(db, tmp_path)
    document = await documents.upload_document(
        user.pseudonym_id,
        "protected.md",
        b"# Algebra\n\nDefinition: Algebra preserves equality while solving equations.",
    )
    await documents.process_document(document.id)
    chunks = (
        await db.scalars(select(DocumentChunk).where(DocumentChunk.document_id == document.id))
    ).all()
    assert chunks
    for chunk in chunks:
        metadata = copy.deepcopy(chunk.chunk_metadata)
        metadata["knowledge_unit_refs"] = [f"knowledge_unit:{uuid4()}:v1"]
        metadata["revision_id"] = str(uuid4())
        chunk.chunk_metadata = metadata
    await db.commit()

    result = await PublishedKnowledgeRAGService(db).build_evidence_bundle(
        workspace_id=document.workspace_id,
        pseudonym_id=user.pseudonym_id,
        query="Algebra equality equations",
        teaching_action=make_action({"case_id": "exec020-invalid", "mastery": 0.2}),
    )
    assert result.bundle.items == ()
    reasons = {reason for item in result.trace.candidate_table for reason in item.reason_codes}
    assert "V03_RETRIEVAL_CANONICAL_ELIGIBILITY_DENIED" in reasons
    assert "V03_RETRIEVAL_UNPUBLISHED_KNOWLEDGE" in reasons
    assert "V03_RETRIEVAL_REVISION_STALE" in reasons


@pytest.mark.asyncio
async def test_exec020_review_required_and_grader_only_content_stay_outside_bundle(
    retrieval_db,
) -> None:
    """AC-002/006: review working sets and protected answers never leak."""
    db, tmp_path = retrieval_db
    user = await _user(db)
    documents = _document_service(db, tmp_path)
    review_document = await documents.upload_document(
        user.pseudonym_id,
        "review.md",
        b"Unheaded narrative requires review before it can become canonical knowledge.",
    )
    protected_document = await documents.upload_document(
        user.pseudonym_id,
        "solution.md",
        (
            "# Equality\n\nDefinition: Equality means both sides have the same value.\n\n"
            "# Protected Solution\n\n[grader-only] Reference answer: x equals four."
        ).encode(),
    )
    await documents.process_document(review_document.id)
    await documents.process_document(protected_document.id)
    await db.refresh(review_document)
    review_revision = _current_revision(review_document)
    assert any(
        item["status"] == "review_required" for item in review_revision["knowledge_candidates"]
    )
    assert not any(
        item["canonical_retrieval_eligible"] for item in review_revision["retrieval_chunks"]
    )

    review_result = await PublishedKnowledgeRAGService(db).build_evidence_bundle(
        workspace_id=review_document.workspace_id,
        pseudonym_id=user.pseudonym_id,
        query="Unheaded narrative canonical knowledge",
        teaching_action=make_action({"case_id": "exec020-review", "mastery": 0.2}),
        source_scope={"document_ids": [review_document.id]},
    )
    assert review_result.bundle.items == ()

    protected_result = await PublishedKnowledgeRAGService(db).build_evidence_bundle(
        workspace_id=protected_document.workspace_id,
        pseudonym_id=user.pseudonym_id,
        query="reference answer x equals four",
        teaching_action=make_action(
            {
                "case_id": "exec020-protected",
                "mastery": 0.2,
                "direct_answer_request": True,
            }
        ),
        source_scope={"document_ids": [protected_document.id]},
    )
    assert all(item.allowed_use == "learner_visible" for item in protected_result.bundle.items)
    assert all(
        "x equals four" not in item.content.casefold() for item in protected_result.bundle.items
    )
    assert "V03_RETRIEVAL_VISIBILITY_DENIED" in {
        reason for item in protected_result.trace.candidate_table for reason in item.reason_codes
    }


def test_exec020_cache_identity_and_hybrid_degrade_obey_security_inputs() -> None:
    """AC-004/005/007: cache varies by scope/exposure/version and hybrid degrades."""

    def unavailable(*_args):
        raise RuntimeError("unavailable")

    retriever = AdaptiveEvidenceRetriever(
        HybridEvidenceRetriever(dense_scorer=unavailable, reranker=unavailable)
    )
    candidate = replace(
        make_candidate("exec020-cache", exposure=AnswerExposure.NONE),
        projection_versions={"document:one:material_revision": "revision-1"},
    )
    action = make_action({"case_id": "exec020-cache-none", "mastery": 0.9})
    base = {
        "teaching_action": action,
        "query": "fractions evidence",
        "candidates": (candidate,),
        "source_scope": {
            "workspace_id": "ws-a",
            "document_ids": [str(candidate.document_id)],
        },
        "index_versions": {"document:one:material_revision": "revision-1"},
    }
    first = retriever.cache_identity(**base)
    assert first != retriever.cache_identity(
        **{
            **base,
            "source_scope": {
                "workspace_id": "ws-a",
                "document_ids": [str(fixed_uuid("other"))],
            },
        }
    )
    # EXEC063-AC-005: a different Workspace must never share a cache identity.
    assert first != retriever.cache_identity(
        **{
            **base,
            "source_scope": {
                "workspace_id": "ws-b",
                "document_ids": [str(candidate.document_id)],
            },
        }
    )
    assert first != retriever.cache_identity(
        **{**base, "index_versions": {"document:one:material_revision": "revision-2"}}
    )
    complete_action = make_action(
        {"case_id": "exec020-cache-complete", "mastery": 0.2, "direct_answer_request": True}
    )
    assert first != retriever.cache_identity(**{**base, "teaching_action": complete_action})

    result = retriever.build(request_id=fixed_uuid("exec020-request"), **base)
    assert result.bundle.items
    assert "RETRIEVAL_DENSE_UNAVAILABLE_LEXICAL_ONLY" in result.trace.reason_codes
    assert "RETRIEVAL_RERANKER_UNAVAILABLE_RRF_USED" in result.trace.reason_codes
    assert all(item.answer_exposure is AnswerExposure.NONE for item in result.bundle.items)

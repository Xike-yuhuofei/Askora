"""EXEC-003 content revision, citation and EvidenceBundle acceptance tests."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models  # noqa: F401
from app.contracts.learning import TeachingAction
from app.core.database import Base
from app.domains.content_knowledge import CONTENT_RECORD_KEY
from app.domains.retrieval import HybridEvidenceRetriever, RetrievalCandidate
from app.models.document import DocumentChunk, ModerationStatus, ProcessingStatus
from app.models.user import User, UserRole, UserStatus
from app.services.documents.document_service import DocumentService
from app.services.documents.rag_service import RAGService
from app.services.storage.local_storage import LocalFileStorage

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
async def content_db(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'content.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session, tmp_path
    await engine.dispose()


async def _user(db, suffix: str) -> User:
    user = User(
        id=str(uuid4()),
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        pseudonym_id=f"content-{suffix}",
    )
    db.add(user)
    await db.commit()
    return user


def _action(*, exposure: int = 1, requirements: list[str] | None = None) -> TeachingAction:
    return TeachingAction(
        action_id=uuid4(),
        learning_objective_id=uuid4(),
        learning_activity_id=uuid4(),
        strategy_id="guided-practice",
        strategy_version="1.0",
        action_type="practice",
        scaffold_level=1,
        hint_level=1,
        answer_exposure_max=exposure,
        evidence_requirements=requirements or ["context"],
        expected_evidence_type="routine_application",
        success_condition={"score_gte": 0.8},
        failure_condition={"attempts_gte": 3},
        max_attempts=3,
        time_budget_seconds=600,
        reason_codes=["TEACH_GUIDED_PRACTICE"],
        policy_version="1.0",
        decision_id=uuid4(),
    )


def _service(db, tmp_path) -> DocumentService:
    service = DocumentService(db)
    service.storage = LocalFileStorage(str(tmp_path / "documents"))
    return service


def test_sys02_rrf_fixture_is_deterministic_and_deduplicated():
    """SYS02-022/TEST-040: fixed hybrid inputs produce a stable RRF decision."""
    document_id = UUID(int=10)
    revision_id = UUID(int=11)
    span_id = UUID(int=12)
    knowledge_id = UUID(int=13)
    candidates = [
        RetrievalCandidate(
            chunk_id=UUID(int=20),
            document_id=document_id,
            revision_id=revision_id,
            source_span_ids=(span_id,),
            knowledge_unit_ids=(knowledge_id,),
            content="linear equation equality balance",
        ),
        RetrievalCandidate(
            chunk_id=UUID(int=21),
            document_id=document_id,
            revision_id=revision_id,
            source_span_ids=(UUID(int=14),),
            knowledge_unit_ids=(knowledge_id,),
            content="linear equation equality balance",
        ),
        RetrievalCandidate(
            chunk_id=UUID(int=22),
            document_id=document_id,
            revision_id=revision_id,
            source_span_ids=(UUID(int=15),),
            knowledge_unit_ids=(knowledge_id,),
            content="quadratic roots and discriminant",
        ),
    ]
    retriever = HybridEvidenceRetriever()
    kwargs = {
        "request_id": UUID(int=30),
        "teaching_action": _action(exposure=1),
        "query": "linear equation balance",
        "candidates": candidates,
        "source_scope": {"document_ids": [str(document_id)]},
        "index_versions": {"fusion": "rrf-v1"},
    }

    first = retriever.build_evidence_bundle(**kwargs)
    second = retriever.build_evidence_bundle(**kwargs)

    assert [item.content for item in first.bundle.items] == [
        item.content for item in second.bundle.items
    ]
    assert [item.chunk_id for item in first.trace.candidates if item.selected] == [str(UUID(int=20))]
    duplicate = next(item for item in first.trace.candidates if item.chunk_id == str(UUID(int=21)))
    assert duplicate.reason_codes == ["RETRIEVAL_DUPLICATE"]


@pytest.mark.asyncio
async def test_sys01_revision_citation_replay_and_projection_rebuild(content_db):
    """SYS01-AC-001/002/004/005: canonical spans survive revision and index rebuild."""
    db, tmp_path = content_db
    user = await _user(db, "revision")
    service = _service(db, tmp_path)
    first_content = (
        "# Photosynthesis\n\nPlants convert light energy into chemical energy. "
        "Chlorophyll absorbs light and supports glucose production. " * 3
    ).encode()
    document = await service.upload_document(
        user.pseudonym_id,
        "biology.md",
        first_content,
        subject="biology",
        knowledge_point_id="photosynthesis",
    )
    await service.process_document(document.id)
    await db.refresh(document)
    record_v1 = document.moderation_details[CONTENT_RECORD_KEY]
    revision_v1 = record_v1["revisions"][0]
    span_v1 = revision_v1["source_spans"][0]
    knowledge_id = revision_v1["knowledge_units"][0]["knowledge_unit_id"]

    replayed = await service.get_source_span(document.id, span_v1["span_id"])
    assert replayed is not None
    assert replayed["text"] == span_v1["text"]
    assert replayed["start_offset"] == 0

    await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
    await db.commit()
    assert await service.rebuild_chunk_projection(document.id) == document.chunk_count
    rebuilt = (
        await db.execute(
            select(DocumentChunk).where(DocumentChunk.document_id == document.id)
        )
    ).scalars().all()
    assert rebuilt
    assert rebuilt[0].chunk_metadata["source_span_ids"] == [span_v1["span_id"]]

    changed = first_content + b"\n\nA new source-supported revision adds carbon dioxide uptake."
    (service.storage.base_path / document.storage_path).write_bytes(changed)
    await service.process_document(document.id)
    await db.refresh(document)
    record_v2 = document.moderation_details[CONTENT_RECORD_KEY]
    assert len(record_v2["revisions"]) == 2
    assert record_v2["revisions"][0]["revision_id"] == revision_v1["revision_id"]
    assert record_v2["revisions"][1]["supersedes_revision_id"] == revision_v1["revision_id"]
    assert record_v2["revisions"][1]["knowledge_units"][0]["knowledge_unit_id"] == knowledge_id
    assert await service.get_source_span(document.id, span_v1["span_id"]) is not None


@pytest.mark.asyncio
async def test_pdf_source_span_preserves_page_anchor(content_db):
    """EXEC003-AC-003: a parsed PDF citation identifies its source page."""
    db, tmp_path = content_db
    user = await _user(db, "pdf")
    service = _service(db, tmp_path)
    document = await service.upload_document(
        user.pseudonym_id,
        "water.pdf",
        _minimal_pdf("Water boils at 100 degrees Celsius at standard pressure."),
        subject="science",
    )

    await service.process_document(document.id)
    await db.refresh(document)
    revision = document.moderation_details[CONTENT_RECORD_KEY]["revisions"][0]
    span = revision["source_spans"][0]
    assert span["page"] == 1
    assert "Water boils" in span["text"]


@pytest.mark.asyncio
async def test_sys02_exposure_injection_citation_and_missing_evidence(content_db):
    """SYS02-AC-001/002/005/006 and SEC-010/040/050."""
    db, tmp_path = content_db
    user = await _user(db, "malicious")
    service = _service(db, tmp_path)
    source = (FIXTURES / "malicious_document.md").read_bytes()
    document = await service.upload_document(user.pseudonym_id, "malicious.md", source)
    await service.process_document(document.id)
    await db.refresh(document)
    assert document.moderation_status == ModerationStatus.APPROVED

    result = await RAGService(db).build_evidence_bundle(
        pseudonym_id=user.pseudonym_id,
        query="水的沸点",
        teaching_action=_action(exposure=1),
        source_scope={"document_ids": [document.id]},
    )
    assert result.bundle.items
    assert all(item.exposure_level <= 1 for item in result.bundle.items)
    assert all(item.allowed_use == "learner_visible" for item in result.bundle.items)
    assert all(item.source_span_ids for item in result.bundle.items)
    excluded = [
        item
        for item in result.trace.candidates
        if "RETRIEVAL_EXPOSURE_LIMIT" in item.reason_codes
        or "RETRIEVAL_VISIBILITY_DENIED" in item.reason_codes
    ]
    assert excluded
    span = await service.get_source_span(
        document.id, str(result.bundle.items[0].source_span_ids[0])
    )
    assert span is not None

    missing = await RAGService(db).build_evidence_bundle(
        pseudonym_id=user.pseudonym_id,
        query="nonexistent quantum zebra topic",
        teaching_action=_action(exposure=0, requirements=["definition"]),
        source_scope={"document_ids": [document.id]},
    )
    assert missing.bundle.items == []
    assert missing.bundle.missing_roles == ["definition"]


@pytest.mark.asyncio
async def test_sys02_dense_reranker_failure_degrades_and_acl_scope_is_hard(content_db):
    """SYS02-AC-003/004: optional rankers degrade and source scope cannot leak."""
    db, tmp_path = content_db
    owner = await _user(db, "owner")
    other = await _user(db, "other")
    service = _service(db, tmp_path)
    owner_doc = await service.upload_document(
        owner.pseudonym_id,
        "owner.md",
        ("# Algebra\n\nA linear equation keeps equality balanced. " * 4).encode(),
    )
    other_doc = await service.upload_document(
        other.pseudonym_id,
        "other.md",
        ("# Secret\n\nPrivate trigonometry source content. " * 4).encode(),
    )
    await service.process_document(owner_doc.id)
    await service.process_document(other_doc.id)

    def unavailable(*_args):
        raise RuntimeError("unavailable")

    retriever = HybridEvidenceRetriever(dense_scorer=unavailable, reranker=unavailable)
    result = await RAGService(db, retriever=retriever).build_evidence_bundle(
        pseudonym_id=owner.pseudonym_id,
        query="linear equation equality",
        teaching_action=_action(exposure=1),
        source_scope={"document_ids": [owner_doc.id]},
    )
    assert result.bundle.items
    assert result.trace.degraded_reason_codes == [
        "RETRIEVAL_DENSE_UNAVAILABLE_LEXICAL_ONLY",
        "RETRIEVAL_RERANKER_UNAVAILABLE_RRF_USED",
    ]

    denied = await RAGService(db).build_evidence_bundle(
        pseudonym_id=owner.pseudonym_id,
        query="trigonometry",
        teaching_action=_action(exposure=1),
        source_scope={"document_ids": [other_doc.id]},
    )
    assert denied.bundle.items == []


@pytest.mark.asyncio
async def test_quarantined_document_never_enters_retrieval(content_db):
    """LIFE-AC-001/SEC-AC-005: blocked content has no retrievable projection."""
    db, tmp_path = content_db
    user = await _user(db, "quarantine")
    service = _service(db, tmp_path)
    content = ("eval('system(command)') malicious executable text " * 4).encode()
    document = await service.upload_document(user.pseudonym_id, "blocked.txt", content)
    await service.process_document(document.id)
    await db.refresh(document)

    assert document.processing_status == ProcessingStatus.FAILED
    assert document.moderation_status == ModerationStatus.REJECTED
    count = await db.scalar(
        select(func.count())
        .select_from(DocumentChunk)
        .where(DocumentChunk.document_id == document.id)
    )
    assert count == 0
    result = await RAGService(db).build_evidence_bundle(
        pseudonym_id=user.pseudonym_id,
        query="malicious executable",
        teaching_action=_action(),
    )
    assert result.bundle.items == []


def _minimal_pdf(text: str) -> bytes:
    """Create a deterministic one-page Helvetica PDF without another dependency."""
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    result = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(result))
        result.extend(f"{index} 0 obj\n".encode())
        result.extend(obj)
        result.extend(b"\nendobj\n")
    xref = len(result)
    result.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    result.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        result.extend(f"{offset:010d} 00000 n \n".encode())
    result.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    return bytes(result)

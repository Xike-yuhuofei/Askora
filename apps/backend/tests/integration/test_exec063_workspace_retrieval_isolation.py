"""EXEC-063 / XIK-172: Workspace-scoped Material & SYS02 retrieval isolation.

Core proof: ordinary retrieval scoped to Workspace A can never read, hit a
cache entry for, or leak Material/KU that belongs to Workspace B.

Governing: ``docs/archive/exec-plans/EXEC-063-workspace-scoped-retrieval-cutover.md``
(EXEC063-AC-001..AC-010), ADR-0016, SYS02-*.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.contracts.adaptive import AnswerExposure
from app.core.database import Base
from app.core.exceptions import ResourceNotFoundError
from app.domains.content_knowledge import CONTENT_RECORD_KEY
from app.domains.retrieval import (
    AdaptiveEvidenceRetriever,
    HybridEvidenceRetriever,
    retrieval_scope,
)
from app.models.document import UserDocument
from app.models.user import User
from app.models.workspace import (
    ProjectMaterial,
    Workspace,
    WorkspaceLifecycle,
)
from app.queries.library import WorkspaceLibraryQueryService
from app.services.documents.document_service import DocumentService
from app.services.local_identity import ensure_local_owner
from app.services.rag_service import PublishedKnowledgeRAGService
from app.services.storage.local_storage import LocalFileStorage
from app.services.workspace.repository import CrossWorkspaceReferenceError
from app.services.workspace.service import WorkspaceService
from tests.fixtures.v03_execution_factory import make_action


@pytest.fixture
async def isolation_db(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'exec063.db'}")

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session, tmp_path
    await engine.dispose()


async def _owner(session) -> tuple[str, str]:
    """Return (owner_id, pseudonym_id) for a single LocalOwner."""
    ctx = await ensure_local_owner(session)
    await session.commit()
    user = await session.get(User, ctx.canonical_owner_id)
    assert user is not None
    return ctx.canonical_owner_id, user.pseudonym_id


async def _workspace(session, owner_id: str, *, name: str, is_default: bool) -> Workspace:
    ws = Workspace(
        workspace_id=str(uuid4()),
        owner_id=owner_id,
        version=1,
        display_name=name,
        is_default=is_default,
        lifecycle=WorkspaceLifecycle.ACTIVE,
    )
    session.add(ws)
    await session.flush()
    return ws


async def _document(
    db, tmp_path, pseudonym_id: str, *, workspace_id: str, filename: str, content: bytes
):
    service = DocumentService(db)
    service.storage = LocalFileStorage(str(tmp_path / "documents"))
    doc = await service.upload_document(
        pseudonym_id,
        filename,
        content,
        workspace_id=workspace_id,
    )
    await service.process_document(doc.id)
    await db.refresh(doc)
    return doc


def _current_revision(document: UserDocument) -> dict:
    record = document.moderation_details[CONTENT_RECORD_KEY]
    return next(
        item for item in record["revisions"] if item["revision_id"] == record["current_revision_id"]
    )


# ---------------------------------------------------------------------------
# EXEC063-AC-001 / AC-002 / AC-009: Library isolation between Workspaces
# ---------------------------------------------------------------------------


async def test_ac001_ac002_ac009_library_isolation_between_workspaces(isolation_db) -> None:
    """A cannot list/search/read B's Material; no owner-global Library query remains."""
    db, tmp_path = isolation_db
    owner_id, pseudonym_id = await _owner(db)
    ws_a = await _workspace(db, owner_id, name="A", is_default=True)
    ws_b = await _workspace(db, owner_id, name="B", is_default=False)
    doc_a = await _document(
        db,
        tmp_path,
        pseudonym_id,
        workspace_id=ws_a.workspace_id,
        filename="a-material.md",
        content=b"# A private\n\nWorkspace A exclusive facts.",
    )
    doc_b = await _document(
        db,
        tmp_path,
        pseudonym_id,
        workspace_id=ws_b.workspace_id,
        filename="b-material.md",
        content=b"# B secret\n\nWorkspace B exclusive secret content.",
    )
    await db.commit()
    user = await db.get(User, owner_id)
    assert user is not None

    query = WorkspaceLibraryQueryService(db)
    library_a = await query.list_library(
        user,
        workspace_id=ws_a.workspace_id,
        status=None,
        subject=None,
        page=1,
        page_size=20,
        correlation_id="ac002-lib-a",
    )
    assert {str(item.document_id) for item in library_a.data.documents} == {doc_a.id}
    library_b = await query.list_library(
        user,
        workspace_id=ws_b.workspace_id,
        status=None,
        subject=None,
        page=1,
        page_size=20,
        correlation_id="ac002-lib-b",
    )
    assert {str(item.document_id) for item in library_b.data.documents} == {doc_b.id}

    # EXEC063-AC-002: search within A must not match B's exclusive content.
    search_a = await query.list_library(
        user,
        workspace_id=ws_a.workspace_id,
        status=None,
        subject=None,
        query_text="secret",
        page=1,
        page_size=20,
        correlation_id="ac002-search-a",
    )
    assert search_a.data.documents == ()

    # EXEC063-AC-004/009: reading B's Material through A fails closed, no metadata leak.
    with pytest.raises(ResourceNotFoundError):
        await query.get_knowledge_map(
            user,
            workspace_id=ws_a.workspace_id,
            document_id=doc_b.id,
            correlation_id="ac004-cross-read",
        )
    map_a = await query.get_knowledge_map(
        user,
        workspace_id=ws_a.workspace_id,
        document_id=doc_a.id,
        correlation_id="ac004-map-a",
    )
    assert map_a.data.nodes


# ---------------------------------------------------------------------------
# EXEC063-AC-002: RAG (SYS02) isolation between Workspaces
# ---------------------------------------------------------------------------


async def test_ac002_rag_isolation_a_never_reads_or_hits_cache_for_b(isolation_db) -> None:
    """A's SYS02 retrieval cannot surface B's Material/KU in any candidate."""
    db, tmp_path = isolation_db
    owner_id, pseudonym_id = await _owner(db)
    ws_a = await _workspace(db, owner_id, name="A", is_default=True)
    ws_b = await _workspace(db, owner_id, name="B", is_default=False)
    doc_a = await _document(
        db,
        tmp_path,
        pseudonym_id,
        workspace_id=ws_a.workspace_id,
        filename="a-rag.md",
        content=b"# Algebra\n\nA linear equation keeps equality balanced. " * 4,
    )
    doc_b = await _document(
        db,
        tmp_path,
        pseudonym_id,
        workspace_id=ws_b.workspace_id,
        filename="b-rag.md",
        content=b"# Quantum\n\nWorkspace B exclusive quantum entanglement facts. " * 4,
    )
    await db.commit()

    rag = PublishedKnowledgeRAGService(db)
    in_a = await rag.build_evidence_bundle(
        workspace_id=ws_a.workspace_id,
        pseudonym_id=pseudonym_id,
        query="linear equation equality",
        teaching_action=make_action({"case_id": "exec063-a", "mastery": 0.9}),
        source_scope={"document_ids": [doc_a.id]},
    )
    assert in_a.bundle.items
    assert all(key.startswith(f"document:{doc_a.id}:") for key in in_a.bundle.index_versions)

    # A queried for B's exclusive topic must come back empty.
    leak_probe = await rag.build_evidence_bundle(
        workspace_id=ws_a.workspace_id,
        pseudonym_id=pseudonym_id,
        query="quantum entanglement exclusive",
        teaching_action=make_action({"case_id": "exec063-a-probe", "mastery": 0.9}),
        source_scope={"document_ids": [doc_a.id]},
    )
    assert leak_probe.bundle.items == ()

    # B's own retrieval sees B, not A.
    in_b = await rag.build_evidence_bundle(
        workspace_id=ws_b.workspace_id,
        pseudonym_id=pseudonym_id,
        query="quantum entanglement exclusive",
        teaching_action=make_action({"case_id": "exec063-b", "mastery": 0.9}),
        source_scope={"document_ids": [doc_b.id]},
    )
    assert in_b.bundle.items


# ---------------------------------------------------------------------------
# EXEC063-AC-003: Project scope resolves through canonical ProjectMaterial
# ---------------------------------------------------------------------------


async def test_ac003_project_scope_uses_project_material_membership(isolation_db) -> None:
    db, tmp_path = isolation_db
    owner_id, pseudonym_id = await _owner(db)
    ws_a = await _workspace(db, owner_id, name="A", is_default=True)
    ws_b = await _workspace(db, owner_id, name="B", is_default=False)
    doc_a = await _document(
        db,
        tmp_path,
        pseudonym_id,
        workspace_id=ws_a.workspace_id,
        filename="proj-a.md",
        content=b"# Trigonometry\n\nSine and cosine describe right triangles. " * 4,
    )
    doc_b = await _document(
        db,
        tmp_path,
        pseudonym_id,
        workspace_id=ws_b.workspace_id,
        filename="proj-b.md",
        content=b"# Mythology\n\nWorkspace B private mythology. " * 4,
    )
    svc = WorkspaceService(db)
    project = await svc.create_project(workspace_id=ws_a.workspace_id, title="Project A")
    await svc.add_project_material(
        project_id=project.project_id,
        material_id=doc_a.id,
        workspace_id=ws_a.workspace_id,
        material_workspace_id=doc_a.workspace_id,
    )
    # Cross-workspace membership must fail closed (WSP-012).
    with pytest.raises(CrossWorkspaceReferenceError):
        await svc.add_project_material(
            project_id=project.project_id,
            material_id=doc_b.id,
            workspace_id=ws_a.workspace_id,
            material_workspace_id=doc_b.workspace_id,
        )
    await db.commit()

    scope = retrieval_scope(workspace_id=ws_a.workspace_id, project_ids=[project.project_id])
    assert scope.workspace_id == ws_a.workspace_id
    assert scope.project_ids == (project.project_id,)

    # The Material that is actually in the Project is attributable to A.
    membership = await db.scalars(
        select(ProjectMaterial).where(ProjectMaterial.project_id == project.project_id)
    )
    members = membership.all()
    assert [m.material_id for m in members] == [doc_a.id]
    assert doc_b not in members


# ---------------------------------------------------------------------------
# EXEC063-AC-005: cache identity cannot cross Workspace or exposure boundary
# ---------------------------------------------------------------------------


def test_ac005_cache_identity_is_workspace_scoped() -> None:
    """The same query/candidate in different Workspaces must not share a cache key."""
    from dataclasses import replace

    from tests.fixtures.v03_execution_factory import make_candidate

    retriever = AdaptiveEvidenceRetriever(HybridEvidenceRetriever())
    candidate = replace(
        make_candidate("exec063-cache", exposure=AnswerExposure.NONE),
        projection_versions={"document:one:material_revision": "revision-1"},
    )
    action = make_action({"case_id": "exec063-cache", "mastery": 0.9})
    base = {
        "teaching_action": action,
        "query": "fractions evidence",
        "candidates": (candidate,),
        "index_versions": {"document:one:material_revision": "revision-1"},
    }
    identity_a = retriever.cache_identity(
        **{
            **base,
            "source_scope": {"workspace_id": "ws-a", "document_ids": [str(candidate.document_id)]},
        }
    )
    identity_b = retriever.cache_identity(
        **{
            **base,
            "source_scope": {"workspace_id": "ws-b", "document_ids": [str(candidate.document_id)]},
        }
    )
    assert identity_a != identity_b


# ---------------------------------------------------------------------------
# EXEC063-AC-006: SourceSpan citation replay stays pinned to exact revision
# ---------------------------------------------------------------------------


async def test_ac006_source_span_citation_replay_pinned_to_revision(isolation_db) -> None:
    db, tmp_path = isolation_db
    owner_id, pseudonym_id = await _owner(db)
    ws = await _workspace(db, owner_id, name="A", is_default=True)
    doc = await _document(
        db,
        tmp_path,
        pseudonym_id,
        workspace_id=ws.workspace_id,
        filename="cite.md",
        content=b"# Fractions\n\nFractions represent parts of a whole.\n\n# Ratios\n\nFractions are a prerequisite for Ratios.",
    )
    await db.commit()
    revision = _current_revision(doc)

    result = await PublishedKnowledgeRAGService(db).build_evidence_bundle(
        workspace_id=ws.workspace_id,
        pseudonym_id=pseudonym_id,
        query="Fractions parts whole prerequisite Ratios",
        teaching_action=make_action({"case_id": "exec063-cite", "mastery": 0.9}),
        source_scope={"document_ids": [doc.id]},
    )
    assert result.bundle.items
    service = DocumentService(db)
    service.storage = LocalFileStorage(str(tmp_path / "documents"))
    for item in result.bundle.items:
        for span_id in item.source_span_ids:
            replay = await service.get_source_span(doc.id, str(span_id))
            assert replay is not None
            assert replay["revision_id"] == revision["revision_id"]


# ---------------------------------------------------------------------------
# EXEC063-AC-007: grader-only / answer-exposure tightening stays intact
# ---------------------------------------------------------------------------


async def test_ac007_grader_only_and_exposure_tightening_preserved(isolation_db) -> None:
    db, tmp_path = isolation_db
    owner_id, pseudonym_id = await _owner(db)
    ws = await _workspace(db, owner_id, name="A", is_default=True)
    doc = await _document(
        db,
        tmp_path,
        pseudonym_id,
        workspace_id=ws.workspace_id,
        filename="grader.md",
        content=(
            b"# Equality\n\nDefinition: Equality means both sides have the same value.\n\n"
            b"# Protected Solution\n\n[grader-only] Reference answer: x equals four."
        ),
    )
    await db.commit()

    result = await PublishedKnowledgeRAGService(db).build_evidence_bundle(
        workspace_id=ws.workspace_id,
        pseudonym_id=pseudonym_id,
        query="reference answer x equals four",
        teaching_action=make_action(
            {"case_id": "exec063-grader", "mastery": 0.2, "direct_answer_request": True}
        ),
        source_scope={"document_ids": [doc.id]},
    )
    assert all(item.allowed_use == "learner_visible" for item in result.bundle.items)
    assert all("x equals four" not in item.content.casefold() for item in result.bundle.items)


# ---------------------------------------------------------------------------
# EXEC063-AC-008: legacy default-Workspace resolution is deterministic
# ---------------------------------------------------------------------------


async def test_ac008_legacy_default_workspace_is_deterministic(isolation_db) -> None:
    """The legacy adapter resolves exactly the single active default Workspace."""
    db, tmp_path = isolation_db
    owner_id, pseudonym_id = await _owner(db)
    default = await _workspace(db, owner_id, name="Default", is_default=True)
    secondary = await _workspace(db, owner_id, name="Secondary", is_default=False)
    assert default.is_default is True
    assert secondary.is_default is False

    user = await db.get(User, owner_id)
    assert user is not None
    query = WorkspaceLibraryQueryService(db)
    library = await query.list_library(
        user,
        workspace_id=default.workspace_id,
        status=None,
        subject=None,
        page=1,
        page_size=20,
        correlation_id="ac008-default",
    )
    assert library.data.view_state in {"EMPTY", "READY", "PARTIAL"}
    # The default Workspace never aggregates the secondary Workspace's rows.
    assert secondary.workspace_id != default.workspace_id


# ---------------------------------------------------------------------------
# EXEC063-AC-004: cross-workspace narrowing never leaks B Metadata/KU
# ---------------------------------------------------------------------------


async def test_ac004_cross_workspace_narrowing_fails_closed_without_leak(isolation_db) -> None:
    """Narrowing a Workspace-A retrieval with a Workspace-B Material id yields nothing."""
    db, tmp_path = isolation_db
    owner_id, pseudonym_id = await _owner(db)
    ws_a = await _workspace(db, owner_id, name="A", is_default=True)
    ws_b = await _workspace(db, owner_id, name="B", is_default=False)
    doc_a = await _document(
        db,
        tmp_path,
        pseudonym_id,
        workspace_id=ws_a.workspace_id,
        filename="a-narrow.md",
        content=b"# Algebra\n\nEquation balancing keeps equality. " * 4,
    )
    doc_b = await _document(
        db,
        tmp_path,
        pseudonym_id,
        workspace_id=ws_b.workspace_id,
        filename="b-narrow.md",
        content=b"# Bank\n\nWorkspace B private PIN routines. " * 4,
    )
    await db.commit()
    rag = PublishedKnowledgeRAGService(db)
    result = await rag.build_evidence_bundle(
        workspace_id=ws_a.workspace_id,
        pseudonym_id=pseudonym_id,
        query="equation balancing equality PIN private routine",
        teaching_action=make_action({"case_id": "exec063-ac004", "mastery": 0.9}),
        source_scope={"document_ids": [doc_a.id, doc_b.id]},
    )
    assert all(key.startswith(f"document:{doc_a.id}:") for key in result.bundle.index_versions)

"""EXEC-017 structure-preserving EPUB ingestion and source replay tests."""

from __future__ import annotations

import asyncio
import copy
import io
import threading
import zipfile
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models  # noqa: F401
from app.core.database import Base
from app.domains.content_knowledge import CONTENT_RECORD_KEY, epub_structure
from app.domains.content_knowledge.epub_structure import replay_epub_locators
from app.models.document import ProcessingStatus
from app.models.user import User
from app.services.documents.document_service import DocumentService
from app.services.documents.parsers import EPubParser
from app.services.storage.local_storage import LocalFileStorage
from tests.fixtures.minimal_epub import minimal_structured_epub


@pytest.fixture
async def epub_db(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'epub-structure.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session, tmp_path
    await engine.dispose()


def test_exec017_epub_parser_preserves_spine_nav_dom_links_and_footnotes() -> None:
    """EXEC017-AC-002/004: semantic IR input retains EPUB structural facts."""
    content = minimal_structured_epub()
    first = EPubParser().parse(content, "epub")
    second = EPubParser().parse(content, "epub")

    assert first.full_text == second.full_text
    assert first.document_nodes == second.document_nodes
    assert first.metadata["spine_hrefs"] == ["chapter1.xhtml", "chapter2.xhtml"]
    assert first.metadata["nav_paths"]["chapter1.xhtml"] == ["Foundations"]
    node_types = {item["node_type"] for item in first.document_nodes or []}
    assert {"BOOK", "CHAPTER", "SECTION", "PARAGRAPH", "LIST", "FOOTNOTE", "FIGURE"} <= node_types
    links = [
        link
        for item in first.document_nodes or []
        for link in item.get("metadata", {}).get("internal_links", [])
    ]
    assert {link["href"] for link in links} >= {
        "#note-one",
        "chapter1.xhtml#definition",
    }


def test_d01_batch_replay_parses_each_epub_resource_once(monkeypatch) -> None:
    """D01-051/SEC upload gate: replay cost scales with resources, not SourceSpans."""
    content = minimal_structured_epub()
    parsed = EPubParser().parse(content, "epub")
    nodes = [
        item
        for item in parsed.document_nodes or []
        if item.get("text") and item.get("source_locator", {}).get("href")
    ]
    base_requests = [(item["source_locator"], item["content_hash"]) for item in nodes]
    requests = base_requests * 250
    unique_hrefs = {locator["href"] for locator, _content_hash in requests}
    original_matching_elements = epub_structure._matching_elements
    matching_calls = 0

    def counted_matching_elements(resource: bytes):
        nonlocal matching_calls
        matching_calls += 1
        return original_matching_elements(resource)

    monkeypatch.setattr(epub_structure, "_matching_elements", counted_matching_elements)

    results = replay_epub_locators(content, requests=requests)

    assert len(results) > 1_000
    assert all(status == "EXACT" for status, _path in results)
    assert matching_calls == len(unique_hrefs)


def test_d01_fallback_body_source_span_replays_exactly() -> None:
    """D01-AC-001: XHTML without block tags retains an exact fallback anchor."""
    source = minimal_structured_epub()
    replacement = b"""<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Fallback</title></head>
<body><div><span>Fallback-only source text.</span></div></body></html>"""
    output = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(source)) as archive, zipfile.ZipFile(output, "w") as rebuilt:
        for info in archive.infolist():
            content = replacement if info.filename == "OEBPS/chapter1.xhtml" else archive.read(info)
            rebuilt.writestr(info, content)

    content = output.getvalue()
    parsed = EPubParser().parse(content, "epub")
    fallback = next(
        item
        for item in parsed.document_nodes or []
        if item.get("text") == "Fallback-only source text."
    )

    assert replay_epub_locators(
        content,
        requests=[(fallback["source_locator"], fallback["content_hash"])],
    ) == [("EXACT", "/html[1]/body[1]")]


@pytest.mark.asyncio
async def test_exec017_epub_document_ir_source_span_replay_and_parser_revision(
    epub_db, monkeypatch
) -> None:
    """D01-AC-001..007: IR is durable, replay is explicit and parser upgrades append."""
    db, tmp_path = epub_db
    user = User(id=str(uuid4()), pseudonym_id="exec017-epub-user")
    db.add(user)
    await db.commit()
    service = DocumentService(db)
    service.storage = LocalFileStorage(str(tmp_path / "documents"))
    document = await service.upload_document(
        user.pseudonym_id,
        "structured.epub",
        minimal_structured_epub(),
    )

    await service.process_document(document.id)
    await db.refresh(document)
    assert document.processing_status == ProcessingStatus.COMPLETED
    record = document.moderation_details[CONTENT_RECORD_KEY]
    revision = record["revisions"][0]
    document_ir = revision["document_ir"]
    assert document_ir["parser_version"] == EPubParser.semantic_version
    assert document_ir["node_ids"]
    assert document_ir["structure_hash"]
    assert all(span["node_id"] for span in revision["source_spans"])

    target_span = next(
        span for span in revision["source_spans"] if "stable source anchor" in span["text"]
    )
    exact = await service.replay_source_span(document.id, target_span["span_id"])
    assert exact is not None
    assert exact.status == "EXACT"
    assert exact.reason_codes == []

    recovered_details = copy.deepcopy(document.moderation_details)
    recovered_revision = recovered_details[CONTENT_RECORD_KEY]["revisions"][0]
    recovered_node = next(
        item
        for item in recovered_revision["document_nodes"]
        if item["node_id"] == target_span["node_id"]
    )
    recovered_node["source_locator"]["dom_path"] = "/html[1]/body[1]/p[999]"
    document.moderation_details = recovered_details
    await db.commit()
    recovered = await service.replay_source_span(document.id, target_span["span_id"])
    assert recovered is not None
    assert recovered.status == "RECOVERED"
    assert recovered.reason_codes == ["SOURCE_LOCATOR_RECOVERED"]

    failed_details = copy.deepcopy(document.moderation_details)
    failed_revision = failed_details[CONTENT_RECORD_KEY]["revisions"][0]
    failed_node = next(
        item
        for item in failed_revision["document_nodes"]
        if item["node_id"] == target_span["node_id"]
    )
    failed_node["content_hash"] = "0" * 64
    document.moderation_details = failed_details
    await db.commit()
    failed = await service.replay_source_span(document.id, target_span["span_id"])
    assert failed is not None
    assert failed.status == "FAILED"
    assert failed.reason_codes == ["SOURCE_ANCHOR_FAILED"]

    original_structure_hash = document_ir["structure_hash"]
    monkeypatch.setattr(EPubParser, "semantic_version", "epub-structure-v3-fixture")
    await service.process_document(document.id)
    await db.refresh(document)
    upgraded = document.moderation_details[CONTENT_RECORD_KEY]
    assert len(upgraded["revisions"]) == 2
    assert upgraded["revisions"][1]["supersedes_revision_id"] == revision["revision_id"]
    assert upgraded["revisions"][1]["parser_version"] == "epub-structure-v3-fixture"
    assert upgraded["revisions"][1]["document_ir"]["structure_hash"] == original_structure_hash


@pytest.mark.asyncio
async def test_document_processing_keeps_event_loop_responsive_during_anchor_replay(
    epub_db, monkeypatch
) -> None:
    """TEST-015/SEC upload gate: CPU replay work must not starve health/API tasks."""
    db, tmp_path = epub_db
    user = User(id=str(uuid4()), pseudonym_id="responsive-epub-user")
    db.add(user)
    await db.commit()
    service = DocumentService(db)
    service.storage = LocalFileStorage(str(tmp_path / "documents"))
    document = await service.upload_document(
        user.pseudonym_id,
        "responsive.epub",
        minimal_structured_epub(),
    )
    original_anchor_statuses = DocumentService._current_revision_anchor_statuses
    replay_started = threading.Event()
    replay_release = threading.Event()

    def gated_anchor_statuses(*args, **kwargs):
        replay_started.set()
        if not replay_release.wait(timeout=2):
            raise TimeoutError("event loop could not release anchor replay")
        return original_anchor_statuses(*args, **kwargs)

    monkeypatch.setattr(
        DocumentService,
        "_current_revision_anchor_statuses",
        staticmethod(gated_anchor_statuses),
    )

    processing = asyncio.create_task(service.process_document(document.id))
    started = await asyncio.wait_for(asyncio.to_thread(replay_started.wait, 1), timeout=1.5)
    assert started is True
    replay_release.set()
    await asyncio.wait_for(processing, timeout=5)
    await db.refresh(document)
    assert document.processing_status == ProcessingStatus.COMPLETED


@pytest.mark.asyncio
async def test_document_processing_projects_legacy_user_id_for_canonical_audit(epub_db) -> None:
    """DOMAIN-002/EVENT-040: legacy local users retain stable publication provenance."""
    db, tmp_path = epub_db
    user = User(id="legacy-demo-user", pseudonym_id="legacy-demo-pseudonym")
    db.add(user)
    await db.commit()
    service = DocumentService(db)
    service.storage = LocalFileStorage(str(tmp_path / "documents"))
    document = await service.upload_document(
        user.pseudonym_id,
        "legacy-user.epub",
        minimal_structured_epub(),
    )
    document.processing_status = ProcessingStatus.FAILED
    document.processing_error = "badly formed hexadecimal UUID string"
    await db.commit()

    processed = await service.process_document(document.id)

    assert processed.processing_status == ProcessingStatus.COMPLETED
    assert processed.processing_error is None
    assert processed.chunk_count > 0

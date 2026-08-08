"""EXEC-017 structure-preserving EPUB ingestion and source replay tests."""

from __future__ import annotations

import copy
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models  # noqa: F401
from app.core.database import Base
from app.domains.content_knowledge import CONTENT_RECORD_KEY
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

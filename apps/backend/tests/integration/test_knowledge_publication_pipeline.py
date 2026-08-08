"""EXEC-019 canonical knowledge verification/publication integration tests."""

from __future__ import annotations

import copy
from pathlib import Path
from uuid import UUID, uuid4, uuid5

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models  # noqa: F401
from app.contracts.content import KnowledgeUnit, KnowledgeUnitCandidate, RelationCandidate
from app.core.database import Base
from app.domains.content_knowledge import CONTENT_RECORD_KEY
from app.domains.content_knowledge.publication import (
    KNOWLEDGE_EXTRACTOR_VERSION,
    KNOWLEDGE_PUBLICATION_POLICY_VERSION,
    build_extraction_run,
    publish_revision_knowledge,
    replay_persisted_knowledge_publication,
)
from app.infrastructure.ledger import DecisionTraceRepository, LearningEventRepository
from app.models.document import UserDocument
from app.models.ledger import DecisionTraceRecord, LearningEventRecord
from app.models.user import User, UserRole, UserStatus
from app.services.documents.document_service import DocumentService
from app.services.storage.local_storage import LocalFileStorage
from tests.fixtures.minimal_epub import minimal_structured_epub

APP_ROOT = Path(__file__).resolve().parents[2] / "app"


@pytest.fixture
async def publication_db(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'publication.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session, tmp_path
    await engine.dispose()


async def _user(db, suffix: str) -> User:
    user = User(
        id=str(uuid4()),
        pseudonym_id=f"exec019-{suffix}",
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


def _revision(document: UserDocument) -> dict:
    record = document.moderation_details[CONTENT_RECORD_KEY]
    return next(
        item for item in record["revisions"] if item["revision_id"] == record["current_revision_id"]
    )


@pytest.mark.asyncio
async def test_exec019_source_explicit_publication_trace_events_replay_and_idempotency(
    publication_db,
) -> None:
    """D03-AC-001/EXEC019-AC-002/006: exact refs survive durable no-model replay."""
    db, tmp_path = publication_db
    user = await _user(db, "explicit")
    service = _service(db, tmp_path)
    document = await service.upload_document(
        user.pseudonym_id,
        "relations.md",
        (
            "# Fractions\n\nDefinition: Fractions represent parts of a whole.\n\n"
            "# Ratios\n\nFractions are a prerequisite for Ratios."
        ).encode(),
    )
    await service.process_document(document.id)
    await db.refresh(document)
    revision = _revision(document)

    assert revision["knowledge_extractor_version"] == KNOWLEDGE_EXTRACTOR_VERSION
    assert revision["knowledge_publication_policy_version"] == KNOWLEDGE_PUBLICATION_POLICY_VERSION
    assert revision["extraction_runs"][0]["model_provider"] is None
    assert revision["extraction_runs"][0]["reason_codes"] == [
        "DETERMINISTIC_EXTRACTION_NO_MODEL_CALL"
    ]
    assert {item["candidate_type"] for item in revision["knowledge_candidates"]} == {
        "concept",
        "knowledge_unit",
        "pedagogical_asset",
        "relation",
    }
    assert all(item["status"] == "published" for item in revision["knowledge_units"])
    assert len(revision["relations"]) == 1
    assert revision["relations"][0]["status"] == "published"

    result = revision["knowledge_publication_result"]
    bindings = revision["knowledge_publication_bindings"]
    assert len(bindings["knowledge_units"]) == 2
    assert len(bindings["relations"]) == 1
    assert all(
        item["revision_id"] == revision["revision_id"] for item in bindings["knowledge_units"]
    )
    assert all(item["source_span_ids"] for item in bindings["knowledge_units"])
    assert all(
        item["extraction_run_id"] == result["extraction_run_id"]
        and item["publication_policy_version"] == result["policy_version"]
        for item in [*bindings["knowledge_units"], *bindings["relations"]]
    )

    replayed = replay_persisted_knowledge_publication(revision)
    assert replayed["knowledge_units"] == revision["knowledge_units"]
    assert replayed["relations"] == revision["relations"]
    assert replayed["publication_result"] == result
    publication_source = (APP_ROOT / "domains" / "content_knowledge" / "publication.py").read_text(
        encoding="utf-8"
    )
    assert "app.services.llm" not in publication_source
    assert "ModelRouter" not in publication_source

    decision = await DecisionTraceRepository(db).get(result["decision_id"])
    assert decision is not None
    assert decision.owner_system == "content_knowledge"
    assert decision.selected["knowledge_unit_refs"] == result["published_knowledge_unit_refs"]
    events = await LearningEventRepository(db).query(
        correlation_id=decision.correlation_id,
        limit=10,
    )
    assert {item.event_type for item in events} == {
        "ContentPublished",
        "KnowledgeRelationPublished",
    }
    assert all(
        item.payload["extraction_run_id"] == result["extraction_run_id"]
        and item.payload["publication_policy_version"] == result["policy_version"]
        for item in events
    )

    event_count = await db.scalar(select(func.count()).select_from(LearningEventRecord))
    decision_count = await db.scalar(select(func.count()).select_from(DecisionTraceRecord))
    await service.process_document(document.id)
    assert await db.scalar(select(func.count()).select_from(LearningEventRecord)) == event_count
    assert await db.scalar(select(func.count()).select_from(DecisionTraceRecord)) == decision_count


@pytest.mark.asyncio
async def test_exec019_model_only_self_loop_invalid_anchor_and_ambiguity_are_blocked(
    publication_db,
    monkeypatch,
) -> None:
    """EXEC019-AC-003/005/007: unsafe candidates never become canonical truth."""
    db, tmp_path = publication_db
    user = await _user(db, "negative")
    service = _service(db, tmp_path)
    document = await service.upload_document(
        user.pseudonym_id,
        "two-topics.md",
        b"# Alpha\n\nAlpha fact.\n\n# Beta\n\nBeta fact.",
    )
    await service.process_document(document.id)
    await db.refresh(document)
    revision = _revision(document)
    run = build_extraction_run(revision)
    units = [KnowledgeUnit.model_validate(item) for item in revision["knowledge_units"]]
    span_id = UUID(revision["source_spans"][0]["span_id"])
    semantic_id = UUID(revision["semantic_units"][0]["semantic_unit_id"])

    model_unit_id = uuid4()
    model_candidate = KnowledgeUnitCandidate(
        candidate_id=uuid5(run.extraction_run_id, "model-only-unit"),
        revision_id=UUID(revision["revision_id"]),
        source_span_ids=[span_id],
        semantic_unit_ids=[semantic_id],
        extraction_run_id=run.extraction_run_id,
        proposed_payload={
            "knowledge_unit": {
                "knowledge_unit_id": str(model_unit_id),
                "revision": 1,
                "kind": "concept",
                "canonical_name": "Model-only claim",
                "description": "Untrusted model JSON",
                "concept_ids": [],
                "evidence_span_ids": [str(span_id)],
                "provenance_type": "system_inferred",
                "confidence": 0.999,
                "status": "candidate",
            },
            "structural_basis": "explicit_heading",
        },
        provenance_type="model_inferred",
        confidence=0.999,
    )
    self_relation_id = uuid4()
    self_loop = RelationCandidate(
        candidate_id=uuid5(run.extraction_run_id, "self-loop"),
        revision_id=UUID(revision["revision_id"]),
        source_span_ids=[span_id],
        semantic_unit_ids=[semantic_id],
        extraction_run_id=run.extraction_run_id,
        proposed_payload={
            "relation": {
                "relation_id": str(self_relation_id),
                "revision": 1,
                "prerequisite_id": str(units[0].knowledge_unit_id),
                "target_knowledge_unit_id": str(units[0].knowledge_unit_id),
                "strength": "hard",
                "evidence_span_ids": [str(span_id)],
                "inference_method": "human",
                "confidence": None,
                "status": "candidate",
            },
            "reverse_verification": {"review_decision_ref": "review:fixture"},
        },
        provenance_type="human_curated",
    )
    model_relation = RelationCandidate(
        candidate_id=uuid5(run.extraction_run_id, "model-hard-relation"),
        revision_id=UUID(revision["revision_id"]),
        source_span_ids=[span_id],
        semantic_unit_ids=[semantic_id],
        extraction_run_id=run.extraction_run_id,
        proposed_payload={
            "relation": {
                "relation_id": str(uuid4()),
                "revision": 1,
                "prerequisite_id": str(units[0].knowledge_unit_id),
                "target_knowledge_unit_id": str(units[1].knowledge_unit_id),
                "strength": "hard",
                "evidence_span_ids": [str(span_id)],
                "inference_method": "model",
                "confidence": 0.999,
                "status": "candidate",
            },
            "reverse_verification": {"method": "model_self_assertion"},
        },
        provenance_type="model_inferred",
        confidence=0.999,
    )
    rule_relation = RelationCandidate(
        candidate_id=uuid5(run.extraction_run_id, "rule-backed-relation"),
        revision_id=UUID(revision["revision_id"]),
        source_span_ids=[span_id],
        semantic_unit_ids=[semantic_id],
        extraction_run_id=run.extraction_run_id,
        proposed_payload={
            "relation": {
                "relation_id": str(uuid4()),
                "revision": 1,
                "prerequisite_id": str(units[0].knowledge_unit_id),
                "target_knowledge_unit_id": str(units[1].knowledge_unit_id),
                "strength": "hard",
                "evidence_span_ids": [str(span_id)],
                "inference_method": "rule",
                "confidence": None,
                "status": "candidate",
            },
            "reverse_verification": {
                "rule_id": "source-explicit-prerequisite-v1",
                "applicability": {
                    "source_scope": "current_material_revision",
                    "matched_conditions": ["fixture-rule-condition"],
                },
            },
        },
        provenance_type="deterministic",
    )
    chapter_order = RelationCandidate(
        candidate_id=uuid5(run.extraction_run_id, "chapter-order-relation"),
        revision_id=UUID(revision["revision_id"]),
        source_span_ids=[span_id],
        semantic_unit_ids=[semantic_id],
        extraction_run_id=run.extraction_run_id,
        proposed_payload={
            "relation": {
                "relation_id": str(uuid4()),
                "revision": 1,
                "prerequisite_id": str(units[1].knowledge_unit_id),
                "target_knowledge_unit_id": str(units[0].knowledge_unit_id),
                "strength": "hard",
                "evidence_span_ids": [str(span_id)],
                "inference_method": "chapter_order",
                "confidence": None,
                "status": "candidate",
            },
            "reverse_verification": {"method": "chapter_order"},
        },
        provenance_type="deterministic",
    )
    evaluated = publish_revision_knowledge(
        revision,
        anchor_status_by_span={item["span_id"]: "EXACT" for item in revision["source_spans"]},
        additional_candidates=[
            model_candidate,
            self_loop,
            model_relation,
            rule_relation,
            chapter_order,
        ],
    )
    by_id = {item["candidate_id"]: item for item in evaluated["knowledge_candidates"]}
    assert by_id[str(model_candidate.candidate_id)]["status"] == "review_required"
    assert by_id[str(model_candidate.candidate_id)]["reason_codes"] == [
        "MODEL_INFERENCE_REQUIRES_INDEPENDENT_VERIFICATION"
    ]
    assert by_id[str(self_loop.candidate_id)]["status"] == "rejected"
    assert by_id[str(self_loop.candidate_id)]["reason_codes"] == ["RELATION_SELF_LOOP_BLOCKED"]
    assert by_id[str(model_relation.candidate_id)]["status"] == "review_required"
    assert by_id[str(model_relation.candidate_id)]["reason_codes"] == [
        "MODEL_ONLY_HARD_PREREQUISITE_BLOCKED"
    ]
    assert by_id[str(rule_relation.candidate_id)]["status"] == "published"
    assert by_id[str(rule_relation.candidate_id)]["reason_codes"] == [
        "PREREQUISITE_RELATION_PUBLISHED"
    ]
    assert by_id[str(chapter_order.candidate_id)]["status"] == "rejected"
    assert by_id[str(chapter_order.candidate_id)]["reason_codes"] == [
        "RELATION_SCHEMA_VALIDATION_FAILED"
    ]
    assert all(
        item["knowledge_unit_id"] != str(model_unit_id) for item in evaluated["knowledge_units"]
    )

    invalid = await service.upload_document(
        user.pseudonym_id,
        "invalid-anchor.md",
        b"# Valid-looking heading\n\nSource fact.",
    )

    def failed_anchors(revision, **_kwargs):
        return {item["span_id"]: "FAILED" for item in revision["source_spans"]}

    monkeypatch.setattr(
        DocumentService,
        "_current_revision_anchor_statuses",
        staticmethod(failed_anchors),
    )
    await service.process_document(invalid.id)
    await db.refresh(invalid)
    invalid_revision = _revision(invalid)
    assert all(item["status"] != "published" for item in invalid_revision["knowledge_units"])
    assert any(
        "CANDIDATE_SOURCE_ANCHOR_REPLAY_FAILED" in item["reason_codes"]
        for item in invalid_revision["knowledge_candidates"]
    )

    monkeypatch.undo()
    ambiguous = await service.upload_document(
        user.pseudonym_id,
        "ambiguous.md",
        b"# Repeated\n\nFirst meaning.\n\n# Repeated\n\nSecond meaning.",
    )
    await service.process_document(ambiguous.id)
    await db.refresh(ambiguous)
    ambiguous_revision = _revision(ambiguous)
    assert all(item["status"] != "published" for item in ambiguous_revision["knowledge_units"])
    assert (
        sum(
            item["reason_codes"] == ["ENTITY_RESOLUTION_BLOCKING_AMBIGUITY"]
            for item in ambiguous_revision["knowledge_candidates"]
        )
        >= 2
    )

    legacy = copy.deepcopy(ambiguous_revision)
    legacy["extraction_version"] = "minimal-binding-v1"
    with pytest.raises(ValueError, match="MINIMAL_BINDING_LEGACY_COMPATIBILITY_ONLY"):
        publish_revision_knowledge(
            legacy,
            anchor_status_by_span={item["span_id"]: "EXACT" for item in legacy["source_spans"]},
        )


@pytest.mark.asyncio
async def test_exec019_explicit_cycle_rejected_and_chapter_order_creates_no_relation(
    publication_db,
) -> None:
    """D03-AC-003/005: explicit relations are gated; hierarchy alone stays non-semantic."""
    db, tmp_path = publication_db
    user = await _user(db, "cycle")
    service = _service(db, tmp_path)
    cycle_document = await service.upload_document(
        user.pseudonym_id,
        "cycle.md",
        (
            "# Alpha\n\nGamma is a prerequisite for Alpha.\n\n"
            "# Beta\n\nAlpha is a prerequisite for Beta.\n\n"
            "# Gamma\n\nBeta is a prerequisite for Gamma."
        ).encode(),
    )
    await service.process_document(cycle_document.id)
    await db.refresh(cycle_document)
    cycle_revision = _revision(cycle_document)
    assert len(cycle_revision["relations"]) == 2
    relation_candidates = [
        item
        for item in cycle_revision["knowledge_candidates"]
        if item["candidate_type"] == "relation"
    ]
    assert len(relation_candidates) == 3
    assert sum(item["status"] == "published" for item in relation_candidates) == 2
    assert any(
        item["status"] == "rejected" and item["reason_codes"] == ["HARD_PREREQUISITE_CYCLE_BLOCKED"]
        for item in relation_candidates
    )

    ordered_book = await service.upload_document(
        user.pseudonym_id,
        "ordered.epub",
        minimal_structured_epub(),
    )
    await service.process_document(ordered_book.id)
    await db.refresh(ordered_book)
    book_revision = _revision(ordered_book)
    assert book_revision["hierarchy_nodes"]
    assert book_revision["relations"] == []
    assert all(
        item["candidate_type"] != "relation" for item in book_revision["knowledge_candidates"]
    )


@pytest.mark.asyncio
async def test_exec019_ledger_failure_rolls_back_truth_and_is_visible(
    publication_db,
    monkeypatch,
) -> None:
    """EVENT-040/SYS08-063: critical audit failure cannot commit published truth."""
    db, tmp_path = publication_db
    user = await _user(db, "ledger-failure")
    service = _service(db, tmp_path)
    document = await service.upload_document(
        user.pseudonym_id,
        "audit.md",
        b"# Audited fact\n\nEvidence.",
    )

    async def fail_append(_self, _event):
        raise RuntimeError("fixture ledger unavailable")

    monkeypatch.setattr(LearningEventRepository, "append", fail_append)
    with pytest.raises(RuntimeError, match="fixture ledger unavailable"):
        await service.process_document(document.id)
    await db.refresh(document)
    assert document.processing_status == "failed"
    assert CONTENT_RECORD_KEY not in document.moderation_details
    assert await db.scalar(select(func.count()).select_from(DecisionTraceRecord)) == 0
    assert await db.scalar(select(func.count()).select_from(LearningEventRecord)) == 0

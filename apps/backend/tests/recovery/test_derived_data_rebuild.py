"""EXEC-055 CI v2 Quality Gate: derived data rebuild tests."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.assessment import (
    LearnerEvidenceRecord,
    LearnerStateRecord,
    MasteryEstimateRecord,
)
from app.models.document import DocumentChunk, ProcessingStatus, UserDocument
from app.models.user import User


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_derived_chunks_can_be_deleted_and_rebuilt(tmp_path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'rebuild.db'}"
    engine = create_async_engine(database_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with factory() as session:
        user = User(id=str(uuid4()), pseudonym_id="rebuild-owner")
        session.add(user)
        await session.commit()

        doc = UserDocument(
            id=str(uuid4()),
            pseudonym_id="rebuild-owner",
            original_filename="source.md",
            file_extension="md",
            file_size_bytes=512,
            storage_path="rebuild-owner/source.md",
            processing_status=ProcessingStatus.COMPLETED,
            chunk_count=3,
        )
        session.add(doc)
        await session.commit()

        chunks = [
            DocumentChunk(
                id=str(uuid4()),
                document_id=doc.id,
                chunk_index=i,
                content=f"Chunk {i} content",
                token_count=10,
            )
            for i in range(3)
        ]
        for c in chunks:
            session.add(c)
        await session.commit()

        chunk_count = (await session.execute(text("SELECT COUNT(*) FROM document_chunks"))).scalar()
        assert chunk_count == 3

        await session.execute(
            text("DELETE FROM document_chunks WHERE document_id = :doc_id"),
            {"doc_id": doc.id},
        )
        await session.commit()

        chunk_count = (await session.execute(text("SELECT COUNT(*) FROM document_chunks"))).scalar()
        assert chunk_count == 0

        new_chunks = [
            DocumentChunk(
                id=str(uuid4()),
                document_id=doc.id,
                chunk_index=i,
                content=f"Rebuilt chunk {i}",
                token_count=10,
            )
            for i in range(3)
        ]
        for c in new_chunks:
            session.add(c)
        await session.commit()

        rebuilt_count = (
            await session.execute(text("SELECT COUNT(*) FROM document_chunks"))
        ).scalar()
        assert rebuilt_count == 3

        doc_row = (
            await session.execute(
                text("SELECT id, chunk_count FROM user_documents WHERE id = :doc_id"),
                {"doc_id": doc.id},
            )
        ).fetchone()
        assert doc_row is not None
        assert doc_row[1] == 3
    await engine.dispose()


@pytest.mark.asyncio
async def test_learner_state_recomputed_after_evidence_deletion(tmp_path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'evidence.db'}"
    engine = create_async_engine(database_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with factory() as session:
        user = User(id=str(uuid4()), pseudonym_id="evidence-owner")
        session.add(user)
        await session.commit()

        evidence = LearnerEvidenceRecord(
            id=str(uuid4()),
            source_result_id="result-001",
            user_id=user.id,
            knowledge_unit_id="kp_algebra",
            status="active",
            reason_codes=["correct_answer"],
            payload={"correct": True, "confidence": 0.9},
        )
        session.add(evidence)
        await session.commit()

        state = LearnerStateRecord(
            id=str(uuid4()),
            learner_state_id="state-001",
            user_id=user.id,
            version=1,
            payload={"mastery": 0.75, "evidence_count": 1},
        )
        session.add(state)
        await session.commit()

        evidence_count = (
            await session.execute(
                text("SELECT COUNT(*) FROM learner_evidence WHERE user_id = :uid"),
                {"uid": user.id},
            )
        ).scalar()
        assert evidence_count == 1

        state_count = (
            await session.execute(
                text("SELECT COUNT(*) FROM learner_state_versions WHERE user_id = :uid"),
                {"uid": user.id},
            )
        ).scalar()
        assert state_count == 1

        await session.execute(
            text("DELETE FROM learner_evidence WHERE user_id = :uid"),
            {"uid": user.id},
        )
        await session.commit()

        evidence_count_after = (
            await session.execute(
                text("SELECT COUNT(*) FROM learner_evidence WHERE user_id = :uid"),
                {"uid": user.id},
            )
        ).scalar()
        assert evidence_count_after == 0

        new_state = LearnerStateRecord(
            id=str(uuid4()),
            learner_state_id="state-001",
            user_id=user.id,
            version=2,
            payload={"mastery": 0.0, "evidence_count": 0, "recomputed": True},
        )
        session.add(new_state)
        await session.commit()

        all_states = (
            await session.execute(
                text(
                    "SELECT version, payload FROM learner_state_versions WHERE user_id = :uid ORDER BY version"
                ),
                {"uid": user.id},
            )
        ).fetchall()
        assert len(all_states) == 2
        assert all_states[1][0] == 2
        payload_data = all_states[1][1]
        if isinstance(payload_data, str):
            payload_data = json.loads(payload_data)
        assert payload_data["recomputed"] is True
    await engine.dispose()


@pytest.mark.asyncio
async def test_rebuild_does_not_require_online_llm(tmp_path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'no_llm.db'}"
    engine = create_async_engine(database_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with factory() as session:
        user = User(id=str(uuid4()), pseudonym_id="no-llm-owner")
        session.add(user)
        await session.commit()

        doc = UserDocument(
            id=str(uuid4()),
            pseudonym_id="no-llm-owner",
            original_filename="offline.md",
            file_extension="md",
            file_size_bytes=128,
            storage_path="no-llm-owner/offline.md",
            processing_status=ProcessingStatus.COMPLETED,
            chunk_count=0,
        )
        session.add(doc)
        await session.commit()

        mastery = MasteryEstimateRecord(
            id=str(uuid4()),
            user_id=user.id,
            knowledge_unit_id="kp_offline",
            version=1,
            payload={"p": 0.5, "se": 0.1, "n_attempts": 3},
        )
        session.add(mastery)
        await session.commit()

        state_before = (
            await session.execute(
                text("SELECT COUNT(*) FROM learner_state_versions WHERE user_id = :uid"),
                {"uid": user.id},
            )
        ).scalar()
        assert state_before == 0

        state = LearnerStateRecord(
            id=str(uuid4()),
            learner_state_id="offline-state",
            user_id=user.id,
            version=1,
            payload={
                "mastery": 0.5,
                "source": "rebuild",
                "llm_called": False,
            },
        )
        session.add(state)
        await session.commit()

        state_after = (
            await session.execute(
                text("SELECT payload FROM learner_state_versions WHERE user_id = :uid"),
                {"uid": user.id},
            )
        ).fetchone()
        assert state_after is not None
        payload_raw = state_after[0]
        if isinstance(payload_raw, str):
            payload_raw = json.loads(payload_raw)
        assert payload_raw["llm_called"] is False
        assert payload_raw["source"] == "rebuild"

        chunk_count_before = (
            await session.execute(
                text("SELECT COUNT(*) FROM document_chunks WHERE document_id = :did"),
                {"did": doc.id},
            )
        ).scalar()
        assert chunk_count_before == 0

        chunk = DocumentChunk(
            id=str(uuid4()),
            document_id=doc.id,
            chunk_index=0,
            content="Offline rebuild chunk",
            token_count=5,
        )
        session.add(chunk)
        await session.commit()

        chunk_count_after = (
            await session.execute(
                text("SELECT COUNT(*) FROM document_chunks WHERE document_id = :did"),
                {"did": doc.id},
            )
        ).scalar()
        assert chunk_count_after == 1
    await engine.dispose()

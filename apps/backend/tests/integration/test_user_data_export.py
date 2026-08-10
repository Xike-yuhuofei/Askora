from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models  # noqa: F401
from app.contracts.data_control import ExportScope
from app.core.database import Base
from app.data_control.export import UserDataExporter, export_registry
from app.models.assessment import CanonicalAssessmentAttemptRecord
from app.models.dialog import DialogMessage, DialogSession, MessageRole
from app.models.document import UserDocument
from app.models.planning import (
    LearningActivityRecord,
    LearningGoalRecord,
    LearningPlanRecord,
    ReviewObservationRecord,
)
from app.models.user import User, UserRole, UserStatus


@pytest.mark.asyncio
async def test_current_user_export_is_readable_allowlisted_and_includes_opted_originals(
    tmp_path: Path,
) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'export.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    documents_dir = tmp_path / "documents"
    current_document = documents_dir / "current-user" / "doc.txt"
    current_document.parent.mkdir(parents=True)
    current_document.write_text("CURRENT-USER-DOCUMENT", encoding="utf-8")
    other_document = documents_dir / "other-user" / "other.txt"
    other_document.parent.mkdir(parents=True)
    other_document.write_text("OTHER-USER-DOCUMENT", encoding="utf-8")

    current = User(
        id="user-current",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        nickname="Current User",
        pseudonym_id="current-user",
    )
    other = User(
        id="user-other",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        nickname="OTHER-USER-NICKNAME",
        pseudonym_id="other-user",
    )
    async with factory() as session:
        session.add_all(
            [
                current,
                other,
                UserDocument(
                    id="doc-current",
                    pseudonym_id=current.pseudonym_id,
                    original_filename="notes.txt",
                    file_extension="txt",
                    file_size_bytes=current_document.stat().st_size,
                    storage_path="current-user/doc.txt",
                    processing_status="completed",
                    moderation_status="approved",
                ),
                UserDocument(
                    id="doc-other",
                    pseudonym_id=other.pseudonym_id,
                    original_filename="OTHER-USER-FILE.txt",
                    file_extension="txt",
                    file_size_bytes=other_document.stat().st_size,
                    storage_path="other-user/other.txt",
                    processing_status="completed",
                    moderation_status="approved",
                ),
                DialogSession(
                    id="session-current",
                    user_id=current.id,
                    pseudonym_id=current.pseudonym_id,
                    title="My session",
                    subject="math",
                    model_provider="test-provider",
                    model_name="test-model",
                ),
                DialogSession(
                    id="session-other",
                    user_id=other.id,
                    pseudonym_id=other.pseudonym_id,
                    title="OTHER-USER-SESSION",
                    subject="private",
                ),
                DialogMessage(
                    id="message-visible",
                    session_id="session-current",
                    user_id=current.id,
                    role=MessageRole.USER,
                    content="CURRENT-USER-MESSAGE",
                    turn_number=1,
                ),
                DialogMessage(
                    id="message-system",
                    session_id="session-current",
                    user_id=current.id,
                    role=MessageRole.SYSTEM,
                    content="FORBIDDEN-SYSTEM-PROMPT",
                    turn_number=1,
                ),
                DialogMessage(
                    id="message-other",
                    session_id="session-other",
                    user_id=other.id,
                    role=MessageRole.USER,
                    content="OTHER-USER-MESSAGE",
                    turn_number=1,
                ),
                CanonicalAssessmentAttemptRecord(
                    id="attempt-current",
                    idempotency_key="attempt-export-current",
                    user_id=current.id,
                    item_id="item-1",
                    item_version="1.0",
                    payload={
                        "attempt_id": "attempt-current",
                        "raw_response": "MY-RESPONSE",
                        "answer_key": "FORBIDDEN-ANSWER-KEY",
                        "system_prompt": "FORBIDDEN-NESTED-PROMPT",
                    },
                ),
                LearningGoalRecord(
                    id="goal-current:v1",
                    goal_id="goal-current",
                    user_id=current.id,
                    version=1,
                    status="ACTIVE",
                    idempotency_key="goal-export-current",
                    payload={"goal_id": "goal-current", "title": "MY-GOAL"},
                ),
                LearningPlanRecord(
                    id="plan-current:v1",
                    plan_id="plan-current",
                    learning_goal_id="goal-current",
                    idempotency_key="plan-export-current",
                    version=1,
                    status="ACTIVE",
                    payload={
                        "plan_id": "plan-current",
                        "assumptions": {"note": "MY-PLAN"},
                    },
                ),
                LearningActivityRecord(
                    id="activity-current",
                    plan_id="plan-current",
                    plan_version=1,
                    priority=1.0,
                    payload={
                        "activity_id": "activity-current",
                        "reason_codes": ["MY-ACTIVITY"],
                    },
                ),
                ReviewObservationRecord(
                    id="review-observation-current",
                    user_id=current.id,
                    knowledge_unit_id="knowledge-current",
                    actual_reviewed_at=datetime.now(UTC),
                    payload={
                        "observation_id": "review-observation-current",
                        "outcome": "success",
                    },
                ),
            ]
        )
        await session.commit()

        exporter = UserDataExporter(
            session,
            artifact_dir=tmp_path / "exports",
            documents_dir=documents_dir,
        )
        ready = await exporter.create(
            user=current,
            scopes=tuple(ExportScope),
            include_document_originals=True,
        )

    artifact = export_registry.consume(ready.export_id, current.id, ready.download_token)
    with zipfile.ZipFile(artifact) as package:
        names = set(package.namelist())
        combined = b"".join(package.read(name) for name in names)
        manifest = json.loads(package.read("manifest.json"))
        learning_records = json.loads(package.read("learning-records.json"))

    assert manifest["format"] == "askora-user-export"
    assert manifest["schema_version"] == "1.0"
    assert "documents/originals/doc-current.txt" in names
    assert b"CURRENT-USER-DOCUMENT" in combined
    assert b"CURRENT-USER-MESSAGE" in combined
    assert b"MY-RESPONSE" in combined
    assert b"MY-GOAL" in combined
    assert learning_records["learning_plans"][0]["record_id"] == "plan-current:v1"
    assert learning_records["learning_activities"][0]["record_id"] == "activity-current"
    assert learning_records["review_observations"][0]["record_id"] == "review-observation-current"
    for forbidden in (
        b"FORBIDDEN-PASSWORD-HASH",
        b"FORBIDDEN-SYSTEM-PROMPT",
        b"FORBIDDEN-ANSWER-KEY",
        b"FORBIDDEN-NESTED-PROMPT",
        b"OTHER-USER",
    ):
        assert forbidden not in combined
    assert str(documents_dir).encode() not in combined

    export_registry.delete(ready.export_id, artifact)
    await engine.dispose()

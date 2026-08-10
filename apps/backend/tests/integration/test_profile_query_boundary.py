"""GET /users/profile canonical/compatibility response tests (EXEC-007 Required Tests).

Covers:
- integration: GET /users/profile canonical/compatibility response
- regression: legacy mastery cannot override canonical SYS03 projection
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.assessment import MasteryEstimateRecord
from app.models.profile import UserProfile
from app.models.user import User
from app.queries.profile import ProfileQueryService


def _engine_and_factory(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'profile.db'}")

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine, async_sessionmaker(engine, expire_on_commit=False)


def _seed_user_with_legacy_and_canonical(
    session: AsyncSession,
    *,
    user_id: str,
    pseudonym_id: str,
    legacy_skills_mastered: int,
    legacy_mastery_summary: dict,
    canonical_versions: list[tuple[int, float]],
) -> str:
    session.add(User(id=user_id, pseudonym_id=pseudonym_id))
    session.add(
        UserProfile(
            id=str(uuid4()),
            pseudonym_id=pseudonym_id,
            total_sessions=10,
            total_learning_minutes=120,
            streak_days=3,
            skills_mastered=legacy_skills_mastered,
            mastery_summary=legacy_mastery_summary,
            metacognition={"planning_ability": 0.5},
            affective={"engagement_level": 0.7},
            favorite_subjects=["math", "science"],
            grade_level="k12",
        )
    )
    knowledge_unit_id = str(uuid4())
    for version, competence in canonical_versions:
        session.add(
            MasteryEstimateRecord(
                id=str(uuid4()),
                user_id=user_id,
                knowledge_unit_id=knowledge_unit_id,
                version=version,
                payload={
                    "version": version,
                    "competence_probability": competence,
                    "confidence": 0.8,
                    "algorithm_id": "weighted-bkt",
                    "algorithm_version": "1.0",
                    "independent_success_count": 2,
                    "delayed_recall_evidence_count": 1,
                    "transfer_evidence_count": 1,
                    "evidence_count": 3,
                    "effective_evidence_weight": 2.4,
                    "active_misconception_ids": [],
                },
            )
        )
    return knowledge_unit_id


@pytest.mark.asyncio
async def test_profile_query_uses_canonical_mastery_not_legacy_summary(tmp_path) -> None:
    """EXEC007-AC-002: canonical mastery comes from the SYS03 projection."""
    engine, factory = _engine_and_factory(tmp_path)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    user_id = str(uuid4())
    async with factory() as session:
        _seed_user_with_legacy_and_canonical(
            session,
            user_id=user_id,
            pseudonym_id="profile-query-user",
            legacy_skills_mastered=99,
            legacy_mastery_summary={"math": {"mastery": 0.95, "mastered_count": 50}},
            canonical_versions=[(1, 0.3), (2, 0.85)],
        )
        await session.commit()
        user = await session.get(User, user_id)
        assert user is not None

        model = await ProfileQueryService(session).get_profile(user)

        # canonical aggregate uses the latest version (0.85) and keeps the
        # evidence dimensions required by the frozen MasteryEstimate contract.
        assert model.canonical_mastery.knowledge_units_assessed == 1
        assert model.canonical_mastery.entries[0].competence_probability == 0.85
        assert model.canonical_mastery.entries[0].independent_success_count == 2
        assert model.canonical_mastery.entries[0].delayed_recall_evidence_count == 1
        assert model.canonical_mastery.entries[0].transfer_evidence_count == 1
        assert model.canonical_mastery.entries[0].evidence_count == 3
        # legacy fields retained only as compatibility projection
        assert model.compatibility.skills_mastered == 99
        assert model.compatibility.mastery_summary == {
            "math": {"mastery": 0.95, "mastered_count": 50}
        }
        assert model.compatibility.favorite_subjects == ["math", "science"]
        assert model.compatibility.grade_level == "k12"
    await engine.dispose()


@pytest.mark.asyncio
async def test_legacy_mastery_cannot_override_canonical_projection(tmp_path) -> None:
    """EXEC007-AC-002 regression: legacy high mastery never overrides SYS03."""
    engine, factory = _engine_and_factory(tmp_path)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    user_id = str(uuid4())
    async with factory() as session:
        _seed_user_with_legacy_and_canonical(
            session,
            user_id=user_id,
            pseudonym_id="profile-override-user",
            legacy_skills_mastered=100,
            legacy_mastery_summary={"math": {"mastery": 1.0, "mastered_count": 100}},
            canonical_versions=[(1, 0.1)],  # canonical says NOT mastered
        )
        await session.commit()
        user = await session.get(User, user_id)
        assert user is not None

        model = await ProfileQueryService(session).get_profile(user)

        assert model.canonical_mastery.entries[0].competence_probability == 0.1
        assert model.canonical_mastery.entries[0].evidence_count == 3
        # legacy claims full mastery but must not shape canonical projection
        assert model.compatibility.skills_mastered == 100
        assert model.compatibility.mastery_summary["math"]["mastery"] == 1.0
    await engine.dispose()


@pytest.mark.asyncio
async def test_get_profile_http_endpoint_uses_query_boundary(tmp_path) -> None:
    """EXEC007-AC-001/004: HTTP handler returns frontend-compatible response."""
    from httpx import ASGITransport, AsyncClient

    from app.core.database import get_db
    from app.main import app as fastapi_app
    from app.services.owner.dependencies import get_current_owner_projection

    engine, factory = _engine_and_factory(tmp_path)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    user_id = str(uuid4())
    async with factory() as session:
        _seed_user_with_legacy_and_canonical(
            session,
            user_id=user_id,
            pseudonym_id="http-profile-user",
            legacy_skills_mastered=7,
            legacy_mastery_summary={"science": {"mastery": 0.9, "mastered_count": 3}},
            canonical_versions=[],
        )
        await session.commit()

    async def override_get_db():
        async with factory() as session:
            yield session

    async def override_get_current_owner_projection():
        async with factory() as session:
            user = await session.get(User, user_id)
            assert user is not None
            return user

    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[get_current_owner_projection] = (
        override_get_current_owner_projection
    )
    try:
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/users/profile")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["user"]["id"] == user_id
        profile = data["profile"]
        # frontend-compatible core fields preserved
        assert profile["mastery_summary"] == {"science": {"mastery": 0.9, "mastered_count": 3}}
        assert profile["favorite_subjects"] == ["math", "science"]
        assert "total_sessions" in profile
        # Existing frontend field remains compatibility-only. Canonical mastery
        # is exposed separately without inventing a single-threshold label.
        assert profile["skills_mastered"] == 7
        assert profile["mastery"]["knowledge_units_assessed"] == 0
        # explicit source markers
        assert profile["sources"]["skills_mastered"] == "legacy_compatibility"
        assert profile["sources"]["mastery_summary"] == "legacy_compatibility"
    finally:
        fastapi_app.dependency_overrides.clear()
    await engine.dispose()

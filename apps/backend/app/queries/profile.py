"""Canonical profile query boundary (EXEC-007 T1).

Establishes an application/query → read-model boundary so the API handler
depends only on a stable query contract instead of the legacy ORM
persistence model.

Spec coverage: VSLICE-300, EXEC-007.
State ownership: canonical SYS03 mastery is read from the immutable
``MasteryEstimate`` version stream. Legacy ``UserProfile`` learning fields are
retained only as an explicitly-marked compatibility projection and MUST NOT
become a second factual source (DEP-204 / STATE-250).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment import MasteryEstimateRecord
from app.models.profile import UserProfile
from app.models.user import User

# Versioned/configurable UI aggregate threshold; NOT a learning-science
# constant (docs/specs/README.md §9).
MASTERED_PROBABILITY_THRESHOLD = 0.7


@dataclass(frozen=True)
class CanonicalMasteryEntry:
    """A single latest SYS03 MasteryEstimate for one knowledge unit."""

    knowledge_unit_id: str
    version: int
    competence_probability: float | None
    confidence: float
    algorithm_id: str
    algorithm_version: str
    mastered: bool


@dataclass(frozen=True)
class CanonicalMasteryProjection:
    """Read-only canonical SYS03 learner mastery projection."""

    knowledge_units_assessed: int
    skills_mastered: int
    entries: list[CanonicalMasteryEntry] = field(default_factory=list)


@dataclass(frozen=True)
class LegacyProfileCompatibility:
    """Legacy-only profile fields with no canonical source.

    Compatibility projection only: these are not canonical learner/mastery
    truth and must not be treated as a second factual source.
    """

    total_sessions: int
    total_learning_minutes: int
    streak_days: int
    mastery_summary: dict[str, Any]
    metacognition: dict[str, Any]
    affective: dict[str, Any]
    favorite_subjects: list[Any]
    grade_level: str | None


@dataclass(frozen=True)
class ProfileReadModel:
    """Immutable profile read model returned by the canonical query boundary."""

    user_id: str
    role: str
    status: str
    is_verified: bool
    canonical_mastery: CanonicalMasteryProjection
    compatibility: LegacyProfileCompatibility


class ProfileQueryService:
    """Read-only application query; the API transport depends only on this."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_profile(self, current_user: User) -> ProfileReadModel:
        """Assemble the profile from canonical SYS03 + legacy compatibility."""
        canonical = await self._load_canonical_mastery(current_user)
        compatibility = await self._load_compatibility(current_user)
        return ProfileReadModel(
            user_id=str(current_user.id),
            role=current_user.role.value,
            status=current_user.status.value,
            is_verified=current_user.is_verified,
            canonical_mastery=canonical,
            compatibility=compatibility,
        )

    async def _load_canonical_mastery(self, user: User) -> CanonicalMasteryProjection:
        records = (
            await self._db.scalars(
                select(MasteryEstimateRecord)
                .where(MasteryEstimateRecord.user_id == str(user.id))
                .order_by(
                    MasteryEstimateRecord.user_id,
                    MasteryEstimateRecord.knowledge_unit_id,
                    MasteryEstimateRecord.version.desc(),
                )
            )
        ).all()
        latest_by_unit: dict[str, MasteryEstimateRecord] = {}
        for record in records:
            latest_by_unit.setdefault(record.knowledge_unit_id, record)

        entries: list[CanonicalMasteryEntry] = []
        for record in latest_by_unit.values():
            payload = record.payload
            competence = payload.get("competence_probability")
            mastered = (
                competence is not None
                and float(competence) >= MASTERED_PROBABILITY_THRESHOLD
            )
            entries.append(
                CanonicalMasteryEntry(
                    knowledge_unit_id=record.knowledge_unit_id,
                    version=int(payload.get("version", record.version) or 0),
                    competence_probability=(
                        float(competence) if competence is not None else None
                    ),
                    confidence=float(payload.get("confidence", 0.0) or 0.0),
                    algorithm_id=str(payload.get("algorithm_id", "") or ""),
                    algorithm_version=str(payload.get("algorithm_version", "") or ""),
                    mastered=bool(mastered),
                )
            )
        return CanonicalMasteryProjection(
            knowledge_units_assessed=len(entries),
            skills_mastered=sum(1 for entry in entries if entry.mastered),
            entries=entries,
        )

    async def _load_compatibility(self, user: User) -> LegacyProfileCompatibility:
        profile = await self._db.scalar(
            select(UserProfile).where(UserProfile.pseudonym_id == user.pseudonym_id)
        )
        raw_favorite = profile.favorite_subjects if profile else []
        favorite_subjects = raw_favorite if isinstance(raw_favorite, list) else []
        return LegacyProfileCompatibility(
            total_sessions=profile.total_sessions if profile else 0,
            total_learning_minutes=profile.total_learning_minutes if profile else 0,
            streak_days=profile.streak_days if profile else 0,
            mastery_summary=profile.mastery_summary if profile else {},
            metacognition=profile.metacognition if profile else {},
            affective=profile.affective if profile else {},
            favorite_subjects=favorite_subjects,
            grade_level=profile.grade_level if profile else None,
        )
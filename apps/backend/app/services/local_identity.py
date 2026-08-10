"""LocalOwner resolution boundary for the single-user Askora instance.

This module establishes the canonical ownership truth and the unified
resolution boundary that later EXECs will migrate business endpoints onto.
It deliberately does *not* cut over any existing ``get_current_user`` path:
EXEC-048 handles that. Here we only build a stable, idempotent, replayable
foundation plus a compatibility projection from the legacy ``User`` identity.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.local_owner import LocalOwnerRepository
from app.services.auth.canonical_identity import canonical_user_id

#: Stable provenance labels recorded on the LocalOwner row.
PROVENANCE_FRESH = "fresh"
PROVENANCE_LEGACY = "legacy_single_learner"
PROVENANCE_REUSED = "reused"

# Stable error codes (LID-080).
LOCAL_OWNER_AMBIGUOUS = "LOCAL_OWNER_AMBIGUOUS"
LOCAL_OWNER_MISSING = "LOCAL_OWNER_MISSING"
LOCAL_OWNER_MIGRATION_FAILED = "LOCAL_OWNER_MIGRATION_FAILED"


class LocalOwnerError(RuntimeError):
    """Base class for LocalOwner resolution failures."""

    error_code: str = "LOCAL_OWNER_ERROR"

    def __init__(self, message: str, *, detail: dict | None = None) -> None:
        self.error_code = self.__class__.error_code
        self.detail = detail or {}
        super().__init__(message)


class LocalOwnerAmbiguousError(LocalOwnerError):
    """Multiple legacy learner subjects cannot be merged automatically."""

    error_code = LOCAL_OWNER_AMBIGUOUS

    def __init__(self, subject_count: int) -> None:
        self.subject_count = subject_count
        super().__init__(
            "检测到多个无法安全归并的学习者身份，拒绝自动选择",
            detail={"reason_code": LOCAL_OWNER_AMBIGUOUS, "subject_count": subject_count},
        )


class LocalOwnerMigrationFailedError(LocalOwnerError):
    error_code = LOCAL_OWNER_MIGRATION_FAILED


@dataclass(frozen=True)
class LocalOwnerContext:

    owner_id: UUID
    #: How the owner was established (fresh / legacy_single_learner / reused).
    provenance: str
    #: Compatibility projection to the legacy user primary key, if any.
    legacy_user_id: str | None = None
    #: Compatibility projection to the legacy pseudonym storage key, if any.
    legacy_pseudonym_id: str | None = None

    @property
    def canonical_owner_id(self) -> str:
        return str(self.owner_id)


async def ensure_local_owner(db: AsyncSession) -> LocalOwnerContext:
    """Resolve exactly one LocalOwner, creating it if needed.

    Order of resolution:
      1. If a LocalOwner row exists, reuse it (stable across restarts).
      2. Otherwise inspect legacy learner subjects:
         - none -> create a fresh opaque UUID;
         - one  -> reuse its stable canonical UUID (deterministic mapping);
         - many -> fail closed with ``LOCAL_OWNER_AMBIGUOUS``.

    The insert is guarded by the singleton primary key so concurrent calls can
    never produce more than one owner.
    """
    repo = LocalOwnerRepository(db)
    existing = await repo.get()
    if existing is not None:
        return _context_from_record(existing, provenance=PROVENANCE_REUSED)

    subject_count = await repo.count_eligible_legacy_subjects()
    if subject_count == 0:
        owner_id = uuid4()
        provenance = PROVENANCE_FRESH
        legacy_user_id = None
        legacy_pseudonym_id = None
    elif subject_count == 1:
        subject = await repo.get_single_eligible_legacy_subject()
        if subject is None:
            raise LocalOwnerMigrationFailedError(
                "legacy subject count was 1 but none could be loaded"
            )
        owner_id = canonical_user_id(subject.id)
        provenance = PROVENANCE_LEGACY
        legacy_user_id = subject.id
        legacy_pseudonym_id = subject.pseudonym_id
    else:
        raise LocalOwnerAmbiguousError(subject_count=subject_count)

    record = await repo.create_if_absent(
        owner_id=str(owner_id),
        provenance=provenance,
        legacy_user_id=legacy_user_id,
        legacy_pseudonym_id=legacy_pseudonym_id,
    )
    return _context_from_record(record, provenance=provenance)


async def get_local_owner_context(db: AsyncSession) -> LocalOwnerContext:
    """Return the resolved LocalOwnerContext, failing if it does not exist.

    Unlike ``ensure_local_owner`` this does not create an owner; it is the
    strict read boundary for already-bootstrapped stores.
    """
    repo = LocalOwnerRepository(db)
    existing = await repo.get()
    if existing is None:
        raise LocalOwnerError(
            "LocalOwner 尚未初始化",
            detail={"reason_code": LOCAL_OWNER_MISSING},
        )
    return _context_from_record(existing, provenance=existing.provenance)


def legacy_learner_is_ambiguous(user_ids: list[str]) -> bool:
    """Compatibility helper: whether multiple distinct legacy subjects exist.

    Used by tests and downstream cutover to assert the fail-closed boundary
    without touching the database.
    """
    real = [uid for uid in user_ids if uid]
    return len(real) > 1


def _context_from_record(record, *, provenance: str) -> LocalOwnerContext:
    return LocalOwnerContext(
        owner_id=canonical_user_id(record.owner_id),
        provenance=provenance,
        legacy_user_id=record.legacy_user_id,
        legacy_pseudonym_id=record.legacy_pseudonym_id,
    )

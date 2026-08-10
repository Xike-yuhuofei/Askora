"""LocalOwner resolution boundary for the single-user Askora instance."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.local_owner import LocalOwnerRepository
from app.models.user import User, UserRole, UserStatus
from app.services.auth.canonical_identity import canonical_user_id

PROVENANCE_FRESH = "fresh"
PROVENANCE_LEGACY = "legacy_single_learner"
PROVENANCE_REUSED = "reused"

LOCAL_OWNER_AMBIGUOUS = "LOCAL_OWNER_AMBIGUOUS"
LOCAL_OWNER_MISSING = "LOCAL_OWNER_MISSING"
LOCAL_OWNER_MIGRATION_FAILED = "LOCAL_OWNER_MIGRATION_FAILED"


class LocalOwnerError(RuntimeError):
    error_code: str = "LOCAL_OWNER_ERROR"

    def __init__(self, message: str, *, detail: dict | None = None) -> None:
        self.error_code = self.__class__.error_code
        self.detail = detail or {}
        super().__init__(message)


class LocalOwnerAmbiguousError(LocalOwnerError):
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
    provenance: str
    legacy_user_id: str | None = None
    legacy_pseudonym_id: str | None = None

    @property
    def canonical_owner_id(self) -> str:
        return str(self.owner_id)


async def _ensure_compatibility_user(db: AsyncSession, context: LocalOwnerContext) -> None:
    """Keep legacy FK storage valid without reintroducing account semantics.

    LID-053 allows historical ``user_id`` / ``pseudonym_id`` columns to remain
    during migration. On a fresh LocalOwner store those columns still reference
    ``users`` in several historical tables, so a credential-free compatibility
    row is required for referential integrity. LocalOwner remains the only
    identity truth; this row carries no login credential or PII.
    """
    if context.legacy_user_id is not None:
        return
    if await db.get(User, context.canonical_owner_id) is not None:
        return

    now = datetime.now(timezone.utc)
    db.add(
        User(
            id=context.canonical_owner_id,
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            account_lifecycle="active",
            phone_encrypted=None,
            phone_hash=None,
            email_encrypted=None,
            nickname=None,
            password_hash=None,
            credential_version=1,
            password_changed_at=None,
            wechat_openid_encrypted=None,
            real_name_encrypted=None,
            is_verified=False,
            pseudonym_id=context.owner_id.hex,
            created_at=now,
            updated_at=now,
            last_login_at=None,
            deleted_at=None,
        )
    )
    await db.flush()


async def ensure_local_owner(db: AsyncSession) -> LocalOwnerContext:
    """Resolve exactly one LocalOwner and its transitional storage projection."""
    repo = LocalOwnerRepository(db)
    existing = await repo.get()
    if existing is not None:
        context = _context_from_record(existing, provenance=PROVENANCE_REUSED)
        await _ensure_compatibility_user(db, context)
        return context

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
    context = _context_from_record(record, provenance=provenance)
    await _ensure_compatibility_user(db, context)
    return context


async def _ensure_fresh_local_owner(db: AsyncSession) -> LocalOwnerContext:
    """Force-create a fresh LocalOwner without legacy subject scanning.

    Used as a development-mode escape hatch when legacy subjects are ambiguous
    and prevent normal bootstrapping.
    """
    repo = LocalOwnerRepository(db)
    owner_id = uuid4()
    record = await repo.create_if_absent(
        owner_id=str(owner_id),
        provenance=PROVENANCE_FRESH,
        legacy_user_id=None,
        legacy_pseudonym_id=None,
    )
    return _context_from_record(record, provenance=PROVENANCE_FRESH)


async def get_local_owner_context(db: AsyncSession) -> LocalOwnerContext:
    """Return the resolved LocalOwnerContext, failing if it does not exist."""
    repo = LocalOwnerRepository(db)
    existing = await repo.get()
    if existing is None:
        raise LocalOwnerError(
            "LocalOwner 尚未初始化",
            detail={"reason_code": LOCAL_OWNER_MISSING},
        )
    return _context_from_record(existing, provenance=existing.provenance)


def legacy_learner_is_ambiguous(user_ids: list[str]) -> bool:
    real = [uid for uid in user_ids if uid]
    return len(real) > 1


def _context_from_record(record, *, provenance: str) -> LocalOwnerContext:
    return LocalOwnerContext(
        owner_id=canonical_user_id(record.owner_id),
        provenance=provenance,
        legacy_user_id=record.legacy_user_id,
        legacy_pseudonym_id=record.legacy_pseudonym_id,
    )

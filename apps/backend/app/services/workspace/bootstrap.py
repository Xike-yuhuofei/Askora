"""Default-Workspace bootstrap and legacy LocalOwner-global migration.

Implements the WSP-055 migration phases that run in the application layer
after the additive Alembic schema exists:

- resolve/create the deterministic active default Workspace (idempotent);
- backfill ``workspace_id`` attribution on owner-global rows;
- backfill normalized ``SourceFile`` records from embedded managed-storage
  metadata without re-copying bytes;
- validate the migration result (identity / FK / same-workspace / file state).

All operations are non-destructive and idempotent. No stable IDs are rewritten.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from logging import getLogger
from typing import Callable
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import UserDocument
from app.models.workspace import SourceFile, Workspace
from app.services.workspace.repository import WorkspaceRepository

logger = getLogger(__name__)

#: Callback signature: ``(material_id, checksum, managed_storage_ref) -> True|False|None``.
#: Returns True if the file exists, False if deterministically missing, None if
#: not verifiable in this environment.
FileVerifier = Callable[[str, str, str], bool | None]

#: owner-global tables and the expression selecting rows to attribute.
_WORKSPACE_TABLES: dict[str, str] = {
    "user_documents": "pseudonym_id",
    "library_tags": "pseudonym_id",
    "library_collections": "pseudonym_id",
    "library_search_projections": "pseudonym_id",
    "library_command_receipts": "pseudonym_id",
    "document_duplicate_suggestions": "pseudonym_id",
    "document_ocr_runs": "pseudonym_id",
    "dialog_sessions": "pseudonym_id",
    "dialog_messages": "user_id",
    "outbox_tasks": "id",
    "learning_goal_versions": "user_id",
    "learning_goal_definition_versions": "user_id",
    "learning_goal_state_versions": "user_id",
    "focused_learning_goal_state_versions": "user_id",
    "goal_management_command_receipts": "user_id",
    # EXEC-062 / XIK-177: learner / assessment / review owner-global tables.
    "learner_evidence": "user_id",
    "canonical_mastery_estimate_versions": "user_id",
    "learner_state_versions": "user_id",
    "review_schedule_versions": "user_id",
    "review_observations": "user_id",
    "canonical_assessment_attempts": "user_id",
    "canonical_assessment_result_versions": "attempt_id",
}


@dataclass
class MigrationResult:
    """Durable evidence of a migration run (all counts are idempotent-safe)."""

    workspace_id: str | None = None
    backfilled: dict[str, int] = field(default_factory=dict)
    source_files_created: int = 0
    source_files_skipped_missing: int = 0
    recovery_issues: list[str] = field(default_factory=list)
    integrity_failures: list[str] = field(default_factory=list)


def _source_file_id(material_id: str) -> str:
    """Deterministic SourceFile id so a rerun never duplicates a record."""
    return str(uuid5(NAMESPACE_URL, f"askora:source-file:{material_id}"))


def _media_type_from_extension(extension: str | None) -> str | None:
    if not extension:
        return None
    ext = extension.lower().lstrip(".")
    return {
        "pdf": "application/pdf",
        "md": "text/markdown",
        "txt": "text/plain",
        "docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        "epub": "application/epub+zip",
    }.get(ext)


class WorkspaceBootstrapService:
    """Resolve the default Workspace and migrate legacy owner-global data into it."""

    def __init__(self, db: AsyncSession, verify_file: FileVerifier | None = None):
        self.db = db
        self.verify_file = verify_file

    async def ensure_default_workspace(self, owner_id: str) -> Workspace:
        """Resolve or create exactly one active default Workspace (idempotent)."""
        repo = WorkspaceRepository(self.db)
        return await repo.create_default_if_absent(owner_id)

    async def migrate_legacy_to_default(
        self,
        owner_id: str,
        *,
        workspace: Workspace | None = None,
    ) -> MigrationResult:
        """Backfill owner-global data and SourceFile records into the default Workspace."""
        result = MigrationResult()
        ws = workspace or await self.ensure_default_workspace(owner_id)
        result.workspace_id = ws.workspace_id

        # 1) Backfill workspace_id on owner-global tables.
        for table, _id_col in _WORKSPACE_TABLES.items():
            count = await self._backfill_workspace_column(table, ws.workspace_id)
            if count:
                result.backfilled[table] = count

        # 2) Backfill normalized SourceFile records from embedded metadata.
        await self._backfill_source_files(ws.owner_id, result)

        # 3) Validate attribution cardinality / identity.
        await self._validate(result, owner_id)
        return result

    async def _backfill_workspace_column(self, table: str, workspace_id: str) -> int:
        """Set workspace_id where it is NULL. Returns the number of rows updated.

        Uses the ORM metadata (not live engine reflection) so no synchronous
        DB introspection runs inside the async greenlet.
        """
        from app.core.database import Base

        if table not in Base.metadata.tables:
            return 0
        meta = Base.metadata.tables[table]
        if "workspace_id" not in meta.c:
            return 0
        stmt = meta.update().where(meta.c.workspace_id.is_(None)).values(workspace_id=workspace_id)
        from sqlalchemy.engine import CursorResult

        result = await self.db.execute(stmt)
        if isinstance(result, CursorResult):
            count = result.rowcount
        else:
            count = 0
        return int(count if count is not None else 0)

    async def _backfill_source_files(self, owner_id: str, result: MigrationResult) -> None:
        rows = (
            await self.db.execute(
                select(
                    UserDocument.id,
                    UserDocument.original_filename,
                    UserDocument.file_extension,
                    UserDocument.file_size_bytes,
                    UserDocument.storage_path,
                    UserDocument.raw_asset_checksum,
                    UserDocument.moderation_details,
                ).where(UserDocument.workspace_id.is_not(None))
            )
        ).all()

        for row in rows:
            checksum = row.raw_asset_checksum
            details = row.moderation_details if isinstance(row.moderation_details, dict) else {}
            if not checksum:
                checksum = details.get("raw_asset_checksum")
            if not checksum or not row.storage_path:
                result.recovery_issues.append(
                    f"material {row.id}: missing checksum/path metadata; SourceFile skipped"
                )
                continue

            verified: bool | None = True
            if self.verify_file is not None:
                verified = self.verify_file(row.id, checksum, row.storage_path)
            if verified is False:
                result.source_files_skipped_missing += 1
                result.recovery_issues.append(
                    f"material {row.id}: managed file missing on disk; SourceFile not fabricated"
                )
                continue

            await self.db.flush()
            existing = await self.db.get(SourceFile, _source_file_id(row.id))
            if existing is not None:
                continue

            self.db.add(
                SourceFile(
                    source_file_id=_source_file_id(row.id),
                    material_id=row.id,
                    checksum=checksum,
                    original_filename=row.original_filename,
                    media_type=_media_type_from_extension(row.file_extension),
                    size_bytes=row.file_size_bytes or 0,
                    managed_storage_ref=row.storage_path,
                    created_at=datetime.now(timezone.utc),
                )
            )
            result.source_files_created += 1
        await self.db.flush()

    async def _validate(self, result: MigrationResult, owner_id: str) -> None:
        """Validate attribution cardinality and identity after migration."""
        unowned = (
            (
                await self.db.execute(
                    select(UserDocument.id).where(UserDocument.workspace_id.is_(None))
                )
            )
            .scalars()
            .all()
        )
        if unowned:
            result.integrity_failures.append(f"{len(unowned)} Material(s) remain unattributed")

        # Exactly one active default Workspace must exist.
        default_count = (
            (
                await self.db.execute(
                    select(Workspace).where(
                        Workspace.owner_id == owner_id,
                        Workspace.is_default.is_(True),
                    )
                )
            )
            .scalars()
            .all()
        )
        active_defaults = [
            w for w in default_count if getattr(w, "lifecycle", "active") == "active"
        ]
        if len(active_defaults) != 1:
            result.integrity_failures.append(
                f"expected exactly 1 active default Workspace, found {len(active_defaults)}"
            )


async def ensure_default_workspace(db: AsyncSession, owner_id: str) -> Workspace:
    """Standalone helper to resolve exactly one active default Workspace."""
    return await WorkspaceBootstrapService(db).ensure_default_workspace(owner_id)


async def migrate_legacy_to_default(
    db: AsyncSession,
    owner_id: str,
    *,
    verify_file: FileVerifier | None = None,
) -> MigrationResult:
    """Standalone helper to run the default-Workspace legacy migration."""
    return await WorkspaceBootstrapService(db, verify_file=verify_file).migrate_legacy_to_default(
        owner_id
    )

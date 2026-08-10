"""Material Trash / Restore / Permanent Delete lifecycle service (XIK-174 / EXEC-065).

Implements ``MATLIFE-*``:

```text
active --normal delete--> trash --restore--> active
trash --permanent delete--> Data Control DOCUMENT erasure (physical SourceFile removal)
```

Canonical lifecycle truth (``MATLIFE-085``): ``UserDocument.lifecycle`` is the
single source of truth for Material presence/visibility. ``processing_status``
is never lifecycle truth. Ordinary Trash preserves Material identity, SourceFile
bytes and ProjectMaterial membership; it never calls ``storage.delete_file`` and
never deletes the SourceFile record or ProjectMaterial membership.

Permanent Delete delegates entirely to the canonical Data Control ``DOCUMENT``
erasure workflow (preview -> confirm with idempotency). Physical SourceFile
deletion happens only inside that accepted erasure owner step.
"""

from __future__ import annotations

import asyncio
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.data_control import (
    ErasurePreviewV1,
    ErasureReportV1,
    ErasureScope,
)
from app.core.config import settings
from app.core.exceptions import (
    MaterialAlreadyTrashedError,
    MaterialDeleteVersionConflictError,
    MaterialNotFoundError,
    MaterialNotInTrashError,
    MaterialSourceMissingError,
    MaterialWorkspaceScopeViolationError,
)
from app.core.logging import get_logger
from app.data_control.erasure import ErasureCoordinator
from app.models.document import (
    DocumentChunk,
    MaterialLifecycle,
    MaterialLifecycleReceipt,
    ProcessingStatus,
    TrashReason,
    UserDocument,
)
from app.models.user import User
from app.services.documents.library_management import LibraryManagementService
from app.services.storage.local_storage import LocalFileStorage, get_local_storage

logger = get_logger(__name__)


def _normalize_checksum(value: str | None) -> str | None:
    """Normalise a managed-asset checksum to a bare hex digest for comparison."""
    if not value:
        return None
    normalized = value.replace("sha256-", "").replace("sha256:", "").lower()
    return normalized if normalized else None


def _payload_digest(*, target: str, version: int | None) -> str:
    payload = f"material:{target}:{version or ''}"
    return hashlib.sha256(payload.encode()).hexdigest()


class MaterialLifecycleService:
    """Controller for Material Trash / list / Restore / Permanent Delete.

    Ownership: this service transitions ``UserDocument.lifecycle`` (Material
    lifecycle owner, MATLIFE-010). Permanent Delete is delegated to the Data
    Control ``ErasureCoordinator`` (the canonical ``DOCUMENT`` erasure owner);
    this service never performs its own physical file deletion cascade.
    """

    def __init__(
        self,
        db: AsyncSession,
        *,
        storage: LocalFileStorage | None = None,
        erasure_coordinator_factory: Any | None = None,
    ) -> None:
        self.db = db
        self.storage = storage or get_local_storage()
        self._coordinator_factory = erasure_coordinator_factory or self._default_coordinator

    # ------------------------------------------------------------------
    # Erasure coordinator factory
    # ------------------------------------------------------------------

    def _default_coordinator(self, db: AsyncSession) -> ErasureCoordinator:
        documents_dir = Path(settings.local_storage_base_path).resolve()
        return ErasureCoordinator(
            db,
            documents_dir=documents_dir,
            fail_closed_marker=documents_dir.parent / "recovery" / "erasure-pending.json",
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _resolve_material(
        self, *, user: User, material_id: str, workspace_id: str
    ) -> UserDocument:
        document = (
            await self.db.execute(
                select(UserDocument).where(
                    UserDocument.id == material_id,
                    UserDocument.pseudonym_id == user.pseudonym_id,
                )
            )
        ).scalar_one_or_none()
        if document is None:
            raise MaterialNotFoundError(tombstone=False)
        if document.lifecycle == MaterialLifecycle.DELETED:
            # Terminal legacy tombstone (MATLIFE-083): never restorable, never trashed.
            raise MaterialNotFoundError(tombstone=True)
        if document.workspace_id is not None and document.workspace_id != workspace_id:
            raise MaterialWorkspaceScopeViolationError()
        return document

    async def _consume_receipt(
        self,
        *,
        user: User,
        command_type: str,
        idempotency_key: str,
        payload: str,
    ) -> dict | None:
        """Return a stored idempotency result if the same command already ran."""
        if not idempotency_key:
            return None
        receipt = (
            await self.db.execute(
                select(MaterialLifecycleReceipt).where(
                    MaterialLifecycleReceipt.pseudonym_id == user.pseudonym_id,
                    MaterialLifecycleReceipt.command_type == command_type,
                    MaterialLifecycleReceipt.idempotency_key == idempotency_key,
                )
            )
        ).scalar_one_or_none()
        if receipt is None:
            return None
        if receipt.payload_digest != payload:
            raise MaterialDeleteVersionConflictError()
        return receipt.result_payload

    async def _store_receipt(
        self,
        *,
        user: User,
        workspace_id: str | None,
        material_id: str,
        command_type: str,
        idempotency_key: str,
        payload: str,
        result: dict,
    ) -> None:
        if not idempotency_key:
            return
        self.db.add(
            MaterialLifecycleReceipt(
                id=str(uuid4()),
                pseudonym_id=user.pseudonym_id,
                workspace_id=workspace_id,
                material_id=material_id,
                command_type=command_type,
                idempotency_key=idempotency_key,
                payload_digest=payload,
                result_payload=result,
            )
        )

    @staticmethod
    def _assert_version(document: UserDocument, expected_version: int | None) -> None:
        if expected_version is not None and document.lifecycle_version != expected_version:
            raise MaterialDeleteVersionConflictError()

    # ------------------------------------------------------------------
    # Trash
    # ------------------------------------------------------------------

    async def trash(
        self,
        *,
        user: User,
        workspace_id: str,
        material_id: str,
        idempotency_key: str = "",
        expected_version: int | None = None,
        reason: str = TrashReason.USER_DELETE,
    ) -> dict[str, Any]:
        """Move an active Material to Trash (recoverable).

        Preserves Material identity, SourceFile bytes and ProjectMaterial
        memberships. Never calls ``storage.delete_file`` and never deletes the
        SourceFile record or ProjectMaterial membership.
        """
        payload = _payload_digest(target=material_id, version=expected_version)
        cached = await self._consume_receipt(
            user=user,
            command_type="trash",
            idempotency_key=idempotency_key,
            payload=payload,
        )
        if cached is not None:
            return cached

        document = await self._resolve_material(
            user=user, material_id=material_id, workspace_id=workspace_id
        )
        if document.lifecycle == MaterialLifecycle.TRASH:
            raise MaterialAlreadyTrashedError()

        self._assert_version(document, expected_version)
        document.lifecycle = MaterialLifecycle.TRASH
        document.trashed_at = datetime.now(timezone.utc)
        document.trash_reason = reason
        document.lifecycle_version += 1
        await self._store_receipt(
            user=user,
            workspace_id=workspace_id,
            material_id=material_id,
            command_type="trash",
            idempotency_key=idempotency_key,
            payload=payload,
            result=self._trash_result(document),
        )
        await self.db.commit()
        logger.info(
            "material_trashed",
            document_id=material_id,
            pseudonym_id=user.pseudonym_id,
            reason=reason,
            lifecycle_version=document.lifecycle_version,
        )
        return self._trash_result(document)

    @staticmethod
    def _trash_result(document: UserDocument) -> dict[str, Any]:
        return {
            "material_id": document.id,
            "status": MaterialLifecycle.TRASH,
            "lifecycle_version": document.lifecycle_version,
            "trashed_at": document.trashed_at.isoformat() if document.trashed_at else None,
            "trash_reason": document.trash_reason,
        }

    # ------------------------------------------------------------------
    # List Trash
    # ------------------------------------------------------------------

    async def list_trash(
        self,
        *,
        user: User,
        workspace_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """List trashed Materials in the given Workspace (excluded from Library/search/RAG)."""
        page = max(page, 1)
        page_size = max(1, min(page_size, 100))
        base = select(UserDocument).where(
            UserDocument.pseudonym_id == user.pseudonym_id,
            UserDocument.lifecycle == MaterialLifecycle.TRASH,
        )
        if workspace_id:
            base = base.where(UserDocument.workspace_id == workspace_id)
        total = (
            await self.db.execute(select(func.count()).select_from(base.subquery()))
        ).scalar_one()
        rows = (
            (
                await self.db.execute(
                    base.order_by(UserDocument.trashed_at.desc().nullslast())
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
            )
            .scalars()
            .all()
        )
        return {
            "items": [self._trash_item(row) for row in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    @staticmethod
    def _trash_item(document: UserDocument) -> dict[str, Any]:
        return {
            "material_id": document.id,
            "original_filename": document.original_filename,
            "display_title": document.display_title,
            "file_extension": document.file_extension,
            "file_size_bytes": document.file_size_bytes,
            "trashed_at": document.trashed_at.isoformat() if document.trashed_at else None,
            "trash_reason": document.trash_reason,
            "workspace_id": document.workspace_id,
        }

    # ------------------------------------------------------------------
    # Restore
    # ------------------------------------------------------------------

    async def restore(
        self,
        *,
        user: User,
        workspace_id: str,
        material_id: str,
        idempotency_key: str = "",
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        """Restore a trashed Material to active after validating its retained SourceFile.

        Restore never guesses READY: the managed SourceFile must be present and
        its checksum must match the retained revision. Stale derived projections
        (chunks / search projection) are rebuilt/validated before advertising the
        Material as active.
        """
        payload = _payload_digest(target=material_id, version=expected_version)
        cached = await self._consume_receipt(
            user=user,
            command_type="restore",
            idempotency_key=idempotency_key,
            payload=payload,
        )
        if cached is not None:
            return cached

        document = await self._resolve_material(
            user=user, material_id=material_id, workspace_id=workspace_id
        )
        if document.lifecycle != MaterialLifecycle.TRASH:
            raise MaterialNotInTrashError()
        self._assert_version(document, expected_version)

        # Validate the retained SourceFile (presence + checksum) before RSVPing READY.
        await self._validate_source(document)

        document.lifecycle = MaterialLifecycle.ACTIVE
        document.trashed_at = None
        document.trash_reason = None
        document.lifecycle_version += 1

        # Rebuild/validate stale derived projections so restore does not guess READY.
        await self._validate_and_rebuild_projections(document)
        result = {
            "material_id": document.id,
            "status": MaterialLifecycle.ACTIVE,
            "lifecycle_version": document.lifecycle_version,
            "source_verified": True,
        }
        await self._store_receipt(
            user=user,
            workspace_id=workspace_id,
            material_id=material_id,
            command_type="restore",
            idempotency_key=idempotency_key,
            payload=payload,
            result=result,
        )
        await self.db.commit()
        logger.info(
            "material_restored",
            document_id=material_id,
            pseudonym_id=user.pseudonym_id,
            lifecycle_version=document.lifecycle_version,
        )
        return result

    async def _validate_source(self, document: UserDocument) -> None:
        """Verify the managed SourceFile is present and matches its retained checksum."""
        try:
            size = await asyncio.to_thread(self.storage.get_file_size, document.storage_path)
        except (OSError, ValueError):
            raise MaterialSourceMissingError(corrupted=False)
        if size <= 0:
            # Missing/empty managed source: fail closed as "missing" (never READY).
            raise MaterialSourceMissingError(corrupted=False)
        expected = _normalize_checksum(document.raw_asset_checksum)
        if expected:
            try:
                content = await asyncio.to_thread(self.storage.read_file, document.storage_path)
            except FileNotFoundError:
                raise MaterialSourceMissingError(corrupted=False)
            except (OSError, ValueError):
                raise MaterialSourceMissingError(corrupted=True)
            actual = hashlib.sha256(content).hexdigest()
            if actual != expected:
                raise MaterialSourceMissingError(corrupted=True)

    async def _validate_and_rebuild_projections(self, document: UserDocument) -> None:
        """Rebuild/validate stale derived projections for a restored Material."""
        from app.services.documents.document_service import DocumentService

        if document.processing_status != ProcessingStatus.COMPLETED:
            # Not READY: do not fabricate a ready state. Only the lifecycle is restored.
            return
        chunk_count = (
            await self.db.execute(
                select(func.count())
                .select_from(DocumentChunk)
                .where(DocumentChunk.document_id == document.id)
            )
        ).scalar_one()
        if chunk_count == 0:
            await DocumentService(self.db).rebuild_chunk_projection(document.id)
            await self.db.refresh(document)
        # Refresh the library search projection freshness so it is AVAILABLE again.
        await LibraryManagementService(self.db).rebuild_search_projection(document)

    # ------------------------------------------------------------------
    # Permanent Delete (delegated to canonical Data Control DOCUMENT erasure)
    # ------------------------------------------------------------------

    async def _require_trashed_material(
        self, *, user: User, workspace_id: str, material_id: str
    ) -> UserDocument:
        """Resolve a trashed Material and fail closed if it is not in Trash."""
        document = await self._resolve_material(
            user=user, material_id=material_id, workspace_id=workspace_id
        )
        if document.lifecycle != MaterialLifecycle.TRASH:
            raise MaterialNotInTrashError()
        return document

    async def preview_permanent_delete(
        self,
        *,
        user: User,
        workspace_id: str,
        material_id: str,
    ) -> ErasurePreviewV1:
        """Build a delete-impact preview delegated to the canonical DOCUMENT erasure.

        The material must already be in Trash (fail-closed two-stage separation).
        Physical SourceFile deletion is never planned here: it happens only inside
        the accepted Data Control erasure owner step.
        """
        await self._require_trashed_material(
            user=user, workspace_id=workspace_id, material_id=material_id
        )
        coordinator = self._coordinator_factory(self.db)
        return await coordinator.preview(
            user=user,
            scope=ErasureScope.DOCUMENT,
            target_ref=material_id,
        )

    async def confirm_permanent_delete(
        self,
        *,
        user: User,
        workspace_id: str,
        material_id: str,
        preview: ErasurePreviewV1,
        confirmation_token: str,
        confirmation_phrase: str,
        idempotency_key: str = "",
    ) -> ErasureReportV1:
        """Confirm and execute Permanent Delete via the Data Control DOCUMENT erasure.

        Idempotency is owned by the canonical Data Control workflow receipt keyed on
        workspace + material. A partial erasure is never reported as complete.
        """
        # Fail closed: Permanent Delete requires the Material to be in Trash. A
        # repeat of an already-confirmed Permanent Delete (idempotency) is allowed
        # to proceed even after the Material row is gone; the canonical Data Control
        # workflow owns the idempotency receipt keyed on workspace + material.
        try:
            await self._require_trashed_material(
                user=user, workspace_id=workspace_id, material_id=material_id
            )
        except (MaterialNotFoundError, MaterialNotInTrashError):
            if not idempotency_key:
                raise
        coordinator = self._coordinator_factory(self.db)
        return await coordinator.confirm(
            user=user,
            preview_id=preview.preview_id,
            token=confirmation_token,
            confirmation_phrase=confirmation_phrase,
            idempotency_key=(
                f"material-perm-delete:{workspace_id}:{material_id}:{idempotency_key}"
            ),
        )


def get_material_lifecycle_service(db: AsyncSession) -> MaterialLifecycleService:
    return MaterialLifecycleService(db)

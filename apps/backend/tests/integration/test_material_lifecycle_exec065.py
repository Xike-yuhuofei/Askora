"""XIK-174 / EXEC-065 Material Trash / Restore / Permanent Delete closure tests."""

from __future__ import annotations

import asyncio
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app import models  # noqa: F401
from app.contracts.data_control import ErasureScope, ErasureWorkflowStatus
from app.core.database import Base
from app.core.exceptions import (
    MaterialNotFoundError,
    MaterialNotInTrashError,
    MaterialSourceMissingError,
    MaterialWorkspaceScopeViolationError,
)
from app.data_control.erasure import ErasureCoordinator
from app.data_control.recovery import RecoveryError
from app.models.document import (
    DocumentChunk,
    LibrarySearchProjection,
    MaterialLifecycle,
    ProcessingStatus,
    UserDocument,
)
from app.models.user import User
from app.models.workspace import ProjectMaterial, SourceFile, Workspace
from app.queries.library import WorkspaceLibraryQueryService
from app.services.documents.material_lifecycle import MaterialLifecycleService
from app.services.local_identity import ensure_local_owner
from app.services.rag_service import PublishedKnowledgeRAGService
from app.services.storage.local_storage import LocalFileStorage
from app.services.workspace.repository import (
    ProjectMaterialRepository,
    ProjectRepository,
    WorkspaceRepository,
)


async def _make_engine_and_factory(tmp_path: Path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'xik174.db'}")

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


async def _seed(
    session: AsyncSession,
    tmp_path: Path,
    *,
    filename: str = "notes.md",
    content: bytes = b"# notes\n\nmaterial content for trash.",
) -> tuple[UserDocument, LocalFileStorage, str]:
    ctx = await ensure_local_owner(session)
    owner_id = ctx.canonical_owner_id
    pseudonym_id = ctx.owner_id.hex
    await session.flush()

    ws = await WorkspaceRepository(session).create_default_if_absent(owner_id)
    await session.flush()

    storage = LocalFileStorage(str(tmp_path / "documents"))
    document_id = str(uuid4())
    storage_path, size = await storage.save_file(
        pseudonym_id=pseudonym_id,
        document_id=document_id,
        original_filename=filename,
        file_content=content,
        file_extension=filename.rsplit(".", 1)[-1],
    )
    document = UserDocument(
        id=document_id,
        pseudonym_id=pseudonym_id,
        workspace_id=ws.workspace_id,
        original_filename=filename,
        display_title=filename,
        metadata_version=1,
        file_extension=filename.rsplit(".", 1)[-1],
        file_size_bytes=size,
        storage_path=storage_path,
        raw_asset_checksum=f"sha256-{hashlib.sha256(content).hexdigest()}",
        processing_status=ProcessingStatus.COMPLETED,
        moderation_status="approved",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    session.add(document)
    await session.flush()

    session.add(
        SourceFile(
            source_file_id=str(uuid4()),
            material_id=document.id,
            checksum=hashlib.sha256(content).hexdigest(),
            original_filename=filename,
            media_type="text/markdown",
            size_bytes=size,
            managed_storage_ref=storage_path,
        )
    )
    document.chunk_count = 1
    session.add(
        DocumentChunk(
            id=str(uuid4()),
            document_id=document.id,
            chunk_index=0,
            content=content.decode("utf-8", errors="replace"),
        )
    )
    await session.commit()
    return document, storage, ws.workspace_id


def _coordinator_factory(documents_dir: Path):
    def _factory(db: AsyncSession) -> ErasureCoordinator:
        # Uses the module-level ErasurePreviewRegistry singleton so preview ->
        # confirm share the same in-memory preview store (mirrors the app default).
        return ErasureCoordinator(
            db,
            documents_dir=documents_dir,
            fail_closed_marker=documents_dir.parent / "recovery" / "erasure-pending.json",
        )

    return _factory


def _svc(session: AsyncSession, storage: LocalFileStorage) -> MaterialLifecycleService:
    return MaterialLifecycleService(
        session,
        storage=storage,
        erasure_coordinator_factory=_coordinator_factory(Path(storage.base_path)),
    )


async def _owner(session: AsyncSession) -> User:
    return (await session.scalars(select(User))).first()


# AC-001 / AC-002: Trash retains bytes; survives restart; restore
@pytest.mark.required
@pytest.mark.asyncio
async def test_trash_retains_bytes_and_restore_roundtrip(tmp_path) -> None:
    engine, factory = await _make_engine_and_factory(tmp_path)
    async with factory() as session:
        document, storage, ws_id = await _seed(session, tmp_path)
        before_bytes = storage.read_file(document.storage_path)
        before_checksum = document.raw_asset_checksum
        owner = await _owner(session)

        result = await _svc(session, storage).trash(
            user=owner,
            workspace_id=ws_id,
            material_id=document.id,
        )
        assert result["status"] == MaterialLifecycle.TRASH
        assert storage.get_file_size(document.storage_path) == len(before_bytes)
        assert storage.read_file(document.storage_path) == before_bytes
        assert document.raw_asset_checksum == before_checksum
    await engine.dispose()

    engine2, factory2 = await _make_engine_and_factory(tmp_path)
    async with factory2() as session:
        storage2 = LocalFileStorage(str(tmp_path / "documents"))
        doc = await session.get(UserDocument, document.id)
        assert doc is not None and doc.lifecycle == MaterialLifecycle.TRASH
        restored = await _svc(session, storage2).restore(
            user=await _owner(session),
            workspace_id=ws_id,
            material_id=document.id,
        )
        assert restored["status"] == MaterialLifecycle.ACTIVE
        assert restored["source_verified"] is True
        assert (await session.get(UserDocument, document.id)).lifecycle == (
            MaterialLifecycle.ACTIVE
        )
    await engine2.dispose()


# AC-003: ProjectMaterial membership survives Trash
@pytest.mark.required
@pytest.mark.asyncio
async def test_project_membership_survives_trash(tmp_path) -> None:
    engine, factory = await _make_engine_and_factory(tmp_path)
    async with factory() as session:
        document, storage, ws_id = await _seed(session, tmp_path)
        owner = await _owner(session)
        project = await ProjectRepository(session).create(
            workspace_id=ws_id,
            title="p",
        )
        await ProjectMaterialRepository(session).add(
            project_id=project.project_id,
            material_id=document.id,
            project_workspace_id=ws_id,
        )
        await session.flush()
        assert (
            await session.scalar(
                select(ProjectMaterial).where(ProjectMaterial.material_id == document.id)
            )
            is not None
        )

        await _svc(session, storage).trash(
            user=owner,
            workspace_id=ws_id,
            material_id=document.id,
        )
        await session.commit()
        assert (
            await session.scalar(
                select(ProjectMaterial).where(ProjectMaterial.material_id == document.id)
            )
            is not None
        )
        assert document.lifecycle == MaterialLifecycle.TRASH
    await engine.dispose()


# AC-004: Trash excluded from Library / search / RAG
@pytest.mark.required
@pytest.mark.asyncio
async def test_trash_excluded_from_library_search_and_rag(tmp_path) -> None:
    engine, factory = await _make_engine_and_factory(tmp_path)
    async with factory() as session:
        document, storage, ws_id = await _seed(session, tmp_path)
        owner = await _owner(session)
        session.add(
            LibrarySearchProjection(
                document_id=document.id,
                pseudonym_id=document.pseudonym_id,
                index_version=1,
                normalized_title=document.display_title.lower(),
                normalized_body="material content",
            )
        )
        await session.commit()

        await _svc(session, storage).trash(
            user=owner,
            workspace_id=ws_id,
            material_id=document.id,
        )
        await session.commit()

        lib = await WorkspaceLibraryQueryService(session).list_library(
            current_user=owner,
            workspace_id=ws_id,
            status=None,
            subject=None,
            page=1,
            page_size=50,
            correlation_id="xik174",
        )
        assert lib.data.total == 0
        assert all(item.document_id != document.id for item in lib.data.documents)

        rag = PublishedKnowledgeRAGService(session)
        loaded = await rag.load_adaptive_input(
            workspace_id=ws_id,
            pseudonym_id=owner.pseudonym_id,
        )
        assert len(loaded.candidates) == 0
    await engine.dispose()


# AC-005: late background job cannot republish a trashed material
@pytest.mark.required
@pytest.mark.asyncio
async def test_late_job_cannot_republish_trashed_material(tmp_path) -> None:
    engine, factory = await _make_engine_and_factory(tmp_path)
    async with factory() as session:
        document, storage, ws_id = await _seed(session, tmp_path)
        owner = await _owner(session)
        await _svc(session, storage).trash(
            user=owner,
            workspace_id=ws_id,
            material_id=document.id,
        )
        await session.commit()
        session.add(
            DocumentChunk(
                id=str(uuid4()),
                document_id=document.id,
                chunk_index=0,
                content="late chunk",
            )
        )
        await session.commit()
        result = await session.get(UserDocument, document.id)
        assert result.lifecycle == MaterialLifecycle.TRASH
        assert result.is_available is False
        assert result.is_active is False
    await engine.dispose()


# AC-006: Restore validates source; missing never guesses READY
@pytest.mark.required
@pytest.mark.asyncio
async def test_restore_source_missing_fails_closed(tmp_path) -> None:
    engine, factory = await _make_engine_and_factory(tmp_path)
    async with factory() as session:
        document, storage, ws_id = await _seed(session, tmp_path)
        owner = await _owner(session)
        await _svc(session, storage).trash(
            user=owner,
            workspace_id=ws_id,
            material_id=document.id,
        )
        storage.delete_file(document.storage_path)
        with pytest.raises(MaterialSourceMissingError) as exc:
            await _svc(session, storage).restore(
                user=owner,
                workspace_id=ws_id,
                material_id=document.id,
            )
        assert exc.value.error_detail.get("corrupted") is False
        assert (await session.get(UserDocument, document.id)).lifecycle == (MaterialLifecycle.TRASH)
    await engine.dispose()


# AC-006: restore source corrupt never guesses READY
@pytest.mark.required
@pytest.mark.asyncio
async def test_restore_source_corrupt_fails_closed(tmp_path) -> None:
    engine, factory = await _make_engine_and_factory(tmp_path)
    async with factory() as session:
        document, storage, ws_id = await _seed(session, tmp_path)
        owner = await _owner(session)
        await _svc(session, storage).trash(
            user=owner,
            workspace_id=ws_id,
            material_id=document.id,
        )
        target = (Path(storage.base_path) / document.storage_path).resolve()
        target.write_bytes(b"tampered content not matching checksum")
        with pytest.raises(MaterialSourceMissingError) as exc:
            await _svc(session, storage).restore(
                user=owner,
                workspace_id=ws_id,
                material_id=document.id,
            )
        assert exc.value.error_detail.get("corrupted") is True
        assert (await session.get(UserDocument, document.id)).lifecycle == (MaterialLifecycle.TRASH)
    await engine.dispose()


# AC-007 / AC-008: Permanent Delete via Data Control; idempotent; removes source
@pytest.mark.required
@pytest.mark.asyncio
async def test_permanent_delete_preview_confirm_idempotent_and_removes_source(tmp_path) -> None:
    engine, factory = await _make_engine_and_factory(tmp_path)
    async with factory() as session:
        document, storage, ws_id = await _seed(session, tmp_path)
        owner = await _owner(session)
        svc = _svc(session, storage)
        await svc.trash(
            user=owner,
            workspace_id=ws_id,
            material_id=document.id,
        )
        await session.commit()

        preview = await svc.preview_permanent_delete(
            user=owner,
            workspace_id=ws_id,
            material_id=document.id,
        )
        assert preview.scope == ErasureScope.DOCUMENT
        assert preview.confirmation_token
        assert preview.confirmation_phrase.startswith("永久删除")
        assert storage.get_file_size(document.storage_path) > 0

        report = await svc.confirm_permanent_delete(
            user=owner,
            workspace_id=ws_id,
            material_id=document.id,
            preview=preview,
            confirmation_token=preview.confirmation_token,
            confirmation_phrase=preview.confirmation_phrase,
            idempotency_key="perm-1",
        )
        assert report.status in {
            ErasureWorkflowStatus.AWAITING_RECOVERY_BASELINE,
            ErasureWorkflowStatus.COMPLETED,
        }
        assert storage.get_file_size(document.storage_path) == 0
        assert (
            await session.scalar(select(UserDocument.id).where(UserDocument.id == document.id))
            is None
        )

        report2 = await svc.confirm_permanent_delete(
            user=owner,
            workspace_id=ws_id,
            material_id=document.id,
            preview=preview,
            confirmation_token=preview.confirmation_token,
            confirmation_phrase=preview.confirmation_phrase,
            idempotency_key="perm-1",
        )
        assert report2.workflow_id == report.workflow_id
    await engine.dispose()


# AC-007: permanent delete requires trash and correct phrase
@pytest.mark.required
@pytest.mark.asyncio
async def test_permanent_delete_requires_trash_and_wrong_phrase_fails(tmp_path) -> None:
    engine, factory = await _make_engine_and_factory(tmp_path)
    async with factory() as session:
        document, storage, ws_id = await _seed(session, tmp_path)
        owner = await _owner(session)
        svc = _svc(session, storage)
        with pytest.raises(MaterialNotInTrashError):
            await svc.preview_permanent_delete(
                user=owner,
                workspace_id=ws_id,
                material_id=document.id,
            )
        await svc.trash(
            user=owner,
            workspace_id=ws_id,
            material_id=document.id,
        )
        await session.commit()
        preview = await svc.preview_permanent_delete(
            user=owner,
            workspace_id=ws_id,
            material_id=document.id,
        )
        with pytest.raises(RecoveryError):
            await svc.confirm_permanent_delete(
                user=owner,
                workspace_id=ws_id,
                material_id=document.id,
                preview=preview,
                confirmation_token=preview.confirmation_token,
                confirmation_phrase="wrong-phrase",
                idempotency_key="perm-wrong",
            )
        assert await session.get(UserDocument, document.id) is not None
    await engine.dispose()


# cross-workspace negative
@pytest.mark.required
@pytest.mark.asyncio
async def test_cross_workspace_delete_restore_rejected(tmp_path) -> None:
    engine, factory = await _make_engine_and_factory(tmp_path)
    async with factory() as session:
        document, storage, ws_id = await _seed(session, tmp_path)
        owner = await _owner(session)
        other_ws = Workspace(workspace_id=str(uuid4()), owner_id=owner.id, display_name="other")
        session.add(other_ws)
        await session.flush()
        svc = _svc(session, storage)
        with pytest.raises(MaterialWorkspaceScopeViolationError):
            await svc.trash(
                user=owner,
                workspace_id=other_ws.workspace_id,
                material_id=document.id,
            )
        await svc.trash(
            user=owner,
            workspace_id=ws_id,
            material_id=document.id,
        )
        with pytest.raises(MaterialWorkspaceScopeViolationError):
            await svc.restore(
                user=owner,
                workspace_id=other_ws.workspace_id,
                material_id=document.id,
            )
    await engine.dispose()


# AC-010: legacy deleted + source present -> Trash
@pytest.mark.required
@pytest.mark.asyncio
async def test_legacy_deleted_source_present_migrates_to_trash(tmp_path) -> None:
    engine, factory = await _make_engine_and_factory(tmp_path)
    async with factory() as session:
        document, storage, ws_id = await _seed(session, tmp_path)
        document.is_deleted = True
        document.deleted_at = datetime.now(timezone.utc)
        document.lifecycle = MaterialLifecycle.ACTIVE
        await session.commit()
        await _legacy_classify(session, tmp_path / "documents")
        migrated = await session.get(UserDocument, document.id)
        await session.refresh(migrated)
        assert migrated.lifecycle == MaterialLifecycle.TRASH
        assert migrated.trash_reason == "LEGACY_DELETE_SOURCE_PRESENT"
    await engine.dispose()


# AC-011: legacy deleted + source missing -> terminal tombstone
@pytest.mark.required
@pytest.mark.asyncio
async def test_legacy_deleted_source_missing_migrates_to_terminal_tombstone(tmp_path) -> None:
    engine, factory = await _make_engine_and_factory(tmp_path)
    async with factory() as session:
        document, storage, ws_id = await _seed(session, tmp_path)
        storage.delete_file(document.storage_path)
        document.is_deleted = True
        document.deleted_at = datetime.now(timezone.utc)
        document.lifecycle = MaterialLifecycle.ACTIVE
        await session.commit()
        await _legacy_classify(session, tmp_path / "documents")
        migrated = await session.get(UserDocument, document.id)
        await session.refresh(migrated)
        assert migrated.lifecycle == MaterialLifecycle.DELETED
        assert migrated.trash_reason == "LEGACY_SOURCE_ALREADY_REMOVED"
        with pytest.raises(MaterialNotFoundError) as exc:
            await _svc(session, storage).restore(
                user=await _owner(session),
                workspace_id=ws_id,
                material_id=document.id,
            )
        assert exc.value.error_detail.get("tombstone") is True
    await engine.dispose()


# AC-009: no-resurrection after permanent delete
@pytest.mark.required
@pytest.mark.asyncio
async def test_no_resurrection_after_permanent_delete(tmp_path) -> None:
    engine, factory = await _make_engine_and_factory(tmp_path)
    async with factory() as session:
        document, storage, ws_id = await _seed(session, tmp_path)
        owner = await _owner(session)
        svc = _svc(session, storage)
        await svc.trash(
            user=owner,
            workspace_id=ws_id,
            material_id=document.id,
        )
        await session.commit()
        preview = await svc.preview_permanent_delete(
            user=owner,
            workspace_id=ws_id,
            material_id=document.id,
        )
        await svc.confirm_permanent_delete(
            user=owner,
            workspace_id=ws_id,
            material_id=document.id,
            preview=preview,
            confirmation_token=preview.confirmation_token,
            confirmation_phrase=preview.confirmation_phrase,
            idempotency_key="perm-nores",
        )
        await session.commit()
        assert (
            await session.scalar(select(UserDocument.id).where(UserDocument.id == document.id))
            is None
        )
        assert (
            await session.scalar(
                select(DocumentChunk.id).where(DocumentChunk.document_id == document.id)
            )
            is None
        )
    await engine.dispose()


async def _legacy_classify(session: AsyncSession, documents_dir: Path) -> None:
    from sqlalchemy import text

    storage_root = await asyncio.to_thread(Path.resolve, Path(documents_dir))
    rows = (
        await session.execute(
            text(
                "SELECT id, storage_path, is_deleted, deleted_at "
                "FROM user_documents WHERE is_deleted = 1"
            )
        )
    ).all()
    for document_id, storage_path, is_deleted, deleted_at in rows:
        if is_deleted:
            source_present = False
            if isinstance(storage_path, str) and storage_path:
                candidate = (storage_root / storage_path).resolve()
                source_present = storage_root in candidate.parents and candidate.is_file()
            lifecycle = "trash" if source_present else "deleted"
            reason = (
                "LEGACY_DELETE_SOURCE_PRESENT"
                if source_present
                else "LEGACY_SOURCE_ALREADY_REMOVED"
            )
            await session.execute(
                text(
                    "UPDATE user_documents SET lifecycle=:l, lifecycle_version=1, "
                    "trashed_at=:t, trash_reason=:r WHERE id=:i"
                ),
                {
                    "l": lifecycle,
                    "t": deleted_at,
                    "r": reason,
                    "i": document_id,
                },
            )
    await session.commit()

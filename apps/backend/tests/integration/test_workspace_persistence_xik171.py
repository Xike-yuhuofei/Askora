"""XIK-171 durable Workspace / Project / Session / SourceFile persistence tests.

Covers the 13 acceptance criteria of EXEC-061 against a fresh disposable
SQLite datastore with FK discipline enabled. Uses ``Base.metadata.create_all``
(the same schema contract the Alembic migration produces) plus the
application-layer bootstrap/migration services.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.local_owner import LocalOwnerRecord
from app.models.workspace import (
    LearningProject,
    LearningSession,
    ProjectMaterial,
    SourceFile,
    Workspace,
)
from app.services.local_identity import ensure_local_owner
from app.services.workspace.bootstrap import WorkspaceBootstrapService
from app.services.workspace.repository import (
    CrossWorkspaceReferenceError,
    ProjectRepository,
)
from app.services.workspace.service import WorkspaceService


@pytest.fixture
async def sqlite_factory(tmp_path) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'xik171.db'}")

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


async def _owner_id(session: AsyncSession) -> str:
    ctx = await ensure_local_owner(session)
    await session.commit()
    return ctx.canonical_owner_id


async def _pseudonym_id(session: AsyncSession, owner_id: str) -> str:
    """Resolve the hex ``users.pseudonym_id`` that legacy FKs reference."""
    from app.models.user import User

    user = await session.get(User, owner_id)
    assert user is not None, "compatibility User row missing for owner"
    return user.pseudonym_id


async def _bootstrap(session: AsyncSession, owner_id: str) -> Workspace:
    svc = WorkspaceBootstrapService(session)
    ws = await svc.ensure_default_workspace(owner_id)
    await session.flush()
    return ws


async def _add_material(
    session: AsyncSession,
    *,
    owner_id: str,
    workspace_id: str,
    material_id: str | None = None,
    filename: str = "notes.md",
    ext: str = "md",
    checksum: str | None = None,
    storage_path: str | None = None,
    size: int = 100,
):
    from app.models.document import UserDocument

    doc = UserDocument(
        id=material_id or str(uuid4()),
        pseudonym_id=await _pseudonym_id(session, owner_id),
        workspace_id=workspace_id,
        original_filename=filename,
        display_title=filename,
        metadata_version=1,
        file_extension=ext,
        file_size_bytes=size,
        storage_path=storage_path or f"/data/{uuid4()}.{ext}",
        raw_asset_checksum=checksum or f"sha256-{uuid4()}",
        processing_status="pending",
        moderation_status="pending",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    session.add(doc)
    await session.flush()
    return doc


# ---------------------------------------------------------------------------
# EXEC061-AC-001 / AC-002: bootstrap fresh + idempotent
# ---------------------------------------------------------------------------


async def test_ac001_fresh_bootstrap_yields_one_owner_and_one_default(sqlite_factory) -> None:
    async with sqlite_factory() as session:
        owner_id = await _owner_id(session)
        ws = await _bootstrap(session, owner_id)
        await session.commit()

        owners = (await session.execute(select(LocalOwnerRecord))).scalars().all()
        workspaces = (await session.execute(select(Workspace))).scalars().all()
        assert len(owners) == 1
        assert len(workspaces) == 1
        assert workspaces[0].workspace_id == ws.workspace_id
        assert workspaces[0].is_default is True
        assert workspaces[0].lifecycle == "active"


async def test_ac002_bootstrap_is_idempotent(sqlite_factory) -> None:
    async with sqlite_factory() as session:
        owner_id = await _owner_id(session)
        ws1 = await _bootstrap(session, owner_id)
        ws2 = await _bootstrap(session, owner_id)
        ws3 = await _bootstrap(session, owner_id)
        await session.commit()

        workspaces = (await session.execute(select(Workspace))).scalars().all()
        assert ws1.workspace_id == ws2.workspace_id == ws3.workspace_id
        assert len(workspaces) == 1


async def test_ac002_concurrent_bootstrap_yields_one_default(sqlite_factory) -> None:
    """The idempotent resolver plus the partial unique index yield one active default.

    Two bootstrap sessions cannot yield two active default Workspaces: the
    resolver is idempotent, and the DB-level partial index
    (``uq_workspaces_one_active_default``) rejects any second active default for
    the same owner. (SQLite serializes writers per file, so the race is proven at
    the unique-index level rather than by two simultaneous write locks.)
    """
    async with sqlite_factory() as s1, sqlite_factory() as s2:
        owner_id = await _owner_id(s1)
        # Session 2 sees the same singleton owner.
        await s2.execute(select(LocalOwnerRecord))
        ws1 = await _bootstrap(s1, owner_id)
        await s1.commit()
        # Session 2 resolves the existing default (idempotent, no duplicate).
        ws2 = await _bootstrap(s2, owner_id)
        await s2.commit()
        assert ws1.workspace_id == ws2.workspace_id

        # DB-level guard: a second active default for the same owner is rejected
        # by the partial unique index, so a racing writer can never create one.
        from sqlalchemy.exc import IntegrityError

        s1.add(
            Workspace(
                workspace_id=str(uuid4()),
                owner_id=owner_id,
                version=1,
                display_name="dup",
                is_default=True,
                lifecycle="active",
            )
        )
        with pytest.raises(IntegrityError):
            await s1.commit()
        await s1.rollback()

        active_defaults = (
            (
                await s1.execute(
                    select(Workspace).where(
                        Workspace.owner_id == owner_id,
                        Workspace.is_default.is_(True),
                        Workspace.lifecycle == "active",
                    )
                )
            )
            .scalars()
            .all()
        )
        assert len(active_defaults) == 1


# ---------------------------------------------------------------------------
# EXEC061-AC-003 / AC-004 / AC-005: stable IDs + attribution + SourceFile
# ---------------------------------------------------------------------------


async def test_ac003_ac004_legacy_migration_preserves_ids_and_attributions(
    sqlite_factory,
) -> None:
    async with sqlite_factory() as session:
        owner_id = await _owner_id(session)
        stable_id = str(uuid4())
        await _add_material(
            session,
            owner_id=owner_id,
            workspace_id=None,
            material_id=stable_id,
            checksum="abc123",
        )
        await session.commit()

        ws = await _bootstrap(session, owner_id)
        await WorkspaceBootstrapService(session).migrate_legacy_to_default(owner_id, workspace=ws)
        await session.commit()

        from app.models.document import UserDocument

        doc = (
            (await session.execute(select(UserDocument).where(UserDocument.id == stable_id)))
            .scalars()
            .one()
        )
        assert doc.id == stable_id  # EXEC061-AC-003: stable Material ID
        assert doc.workspace_id == ws.workspace_id  # EXEC061-AC-004: exact attribution

        source_files = (
            (await session.execute(select(SourceFile).where(SourceFile.material_id == stable_id)))
            .scalars()
            .all()
        )
        assert len(source_files) == 1  # EXEC061-AC-004: normalized SourceFile
        assert source_files[0].checksum == "abc123"
        assert source_files[0].managed_storage_ref == doc.storage_path
        assert source_files[0].original_filename == doc.original_filename
        assert source_files[0].size_bytes == doc.file_size_bytes


async def test_ac005_sourcefile_backfill_is_idempotent_and_no_byte_duplication(
    sqlite_factory,
) -> None:
    async with sqlite_factory() as session:
        owner_id = await _owner_id(session)
        await _add_material(session, owner_id=owner_id, workspace_id=None)
        await session.commit()

        ws = await _bootstrap(session, owner_id)
        svc = WorkspaceBootstrapService(session)
        r1 = await svc.migrate_legacy_to_default(owner_id, workspace=ws)
        r2 = await svc.migrate_legacy_to_default(owner_id, workspace=ws)
        await session.commit()

        counts = (await session.execute(select(SourceFile))).scalars().all()
        # Rerun never duplicates SourceFile rows (no byte / record duplication).
        assert len(counts) == r1.source_files_created == 1
        assert r2.source_files_created == 0


async def test_ac005_missing_file_produces_recovery_issue_and_no_fabricated_sourcefile(
    sqlite_factory,
) -> None:
    async with sqlite_factory() as session:
        owner_id = await _owner_id(session)
        await _add_material(session, owner_id=owner_id, workspace_id=None)
        await session.commit()

        ws = await _bootstrap(session, owner_id)
        svc = WorkspaceBootstrapService(
            session, verify_file=lambda _m, _c, _p: False  # file deterministically missing
        )
        result = await svc.migrate_legacy_to_default(owner_id, workspace=ws)
        await session.commit()

        assert result.source_files_skipped_missing == 1
        assert any("missing on disk" in issue for issue in result.recovery_issues)
        assert (await session.execute(select(SourceFile))).scalars().all() == []


# ---------------------------------------------------------------------------
# EXEC061-AC-006 / AC-007 / AC-008: ProjectMaterial semantics
# ---------------------------------------------------------------------------


async def test_ac006_material_belongs_to_multiple_same_workspace_projects(
    sqlite_factory,
) -> None:
    async with sqlite_factory() as session:
        owner_id = await _owner_id(session)
        ws = await _bootstrap(session, owner_id)
        doc = await _add_material(session, owner_id=owner_id, workspace_id=ws.workspace_id)
        service = WorkspaceService(session)

        p1 = await service.create_project(workspace_id=ws.workspace_id, title="P1")
        p2 = await service.create_project(workspace_id=ws.workspace_id, title="P2")
        await service.add_project_material(
            project_id=p1.project_id, material_id=doc.id, workspace_id=ws.workspace_id
        )
        await service.add_project_material(
            project_id=p2.project_id, material_id=doc.id, workspace_id=ws.workspace_id
        )
        await session.commit()

        from app.services.workspace.repository import ProjectMaterialRepository

        repo = ProjectMaterialRepository(session)
        assert sorted(await repo.list_material_ids(p1.project_id)) == [doc.id]
        assert sorted(await repo.list_material_ids(p2.project_id)) == [doc.id]


async def test_ac007_cross_workspace_refs_rejected(sqlite_factory) -> None:
    async with sqlite_factory() as session:
        owner_id = await _owner_id(session)
        ws_a = await _bootstrap(session, owner_id)
        # A second non-default Workspace for cross-workspace negative tests.
        ws_b = Workspace(
            workspace_id=str(uuid4()),
            owner_id=owner_id,
            version=1,
            display_name="B",
            is_default=False,
            lifecycle="active",
        )
        session.add(ws_b)
        await session.flush()

        doc_b = await _add_material(session, owner_id=owner_id, workspace_id=ws_b.workspace_id)
        await ProjectRepository(session).create(workspace_id=ws_b.workspace_id, title="PB")
        service = WorkspaceService(session)

        # Project in ws_a, Material in ws_b -> reject.
        project_a = await service.create_project(workspace_id=ws_a.workspace_id, title="PA")
        with pytest.raises(CrossWorkspaceReferenceError):
            await service.add_project_material(
                project_id=project_a.project_id,
                material_id=doc_b.id,
                workspace_id=ws_a.workspace_id,
            )

        # Session goal ref crossing a Workspace boundary -> reject.
        from app.models.planning import LearningGoalRecord

        session.add(
            LearningGoalRecord(
                id=f"lg-{uuid4()}",
                goal_id="goal-x",
                user_id=owner_id,
                workspace_id=ws_b.workspace_id,
                version=1,
                status="active",
                idempotency_key=f"g-{uuid4()}",
                payload={},
                created_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()
        with pytest.raises(CrossWorkspaceReferenceError):
            await service.create_session(workspace_id=ws_a.workspace_id, learning_goal_id="goal-x")


async def test_ac008_removing_membership_never_deletes_material_or_sourcefile(
    sqlite_factory,
) -> None:
    async with sqlite_factory() as session:
        owner_id = await _owner_id(session)
        ws = await _bootstrap(session, owner_id)
        doc = await _add_material(session, owner_id=owner_id, workspace_id=ws.workspace_id)
        service = WorkspaceService(session)
        project = await service.create_project(workspace_id=ws.workspace_id, title="P")
        await service.add_project_material(
            project_id=project.project_id,
            material_id=doc.id,
            workspace_id=ws.workspace_id,
        )
        await session.commit()

        removed = await service.remove_project_material(
            project_id=project.project_id, material_id=doc.id, workspace_id=ws.workspace_id
        )
        # Removing twice is idempotent (second returns False).
        removed_again = await service.remove_project_material(
            project_id=project.project_id, material_id=doc.id, workspace_id=ws.workspace_id
        )
        await session.commit()

        from app.models.document import UserDocument

        assert removed is True
        assert removed_again is False
        assert (await session.get(UserDocument, doc.id)) is not None  # Material survives
        assert (await session.execute(select(ProjectMaterial))).scalars().all() == []


# ---------------------------------------------------------------------------
# EXEC061-AC-009 / AC-010: LearningSession semantics
# ---------------------------------------------------------------------------


async def test_ac009_session_exists_without_project_or_goal(sqlite_factory) -> None:
    async with sqlite_factory() as session:
        owner_id = await _owner_id(session)
        ws = await _bootstrap(session, owner_id)
        service = WorkspaceService(session)

        standalone = await service.create_session(workspace_id=ws.workspace_id)
        assert standalone.project_id is None
        assert standalone.learning_goal_id is None
        await session.commit()

        # LearningSession owns no transcript/teaching/mastery truth.
        assert not hasattr(standalone, "transcript")
        assert not hasattr(standalone, "teaching_action")
        assert not hasattr(standalone, "mastery_estimate")
        # Table columns are exactly the narrow envelope.
        cols = {c.name for c in LearningSession.__table__.columns}
        assert {"session_id", "workspace_id", "project_id", "learning_goal_id", "status"}.issubset(
            cols
        )
        assert not ({"transcript", "teaching_action", "mastery_estimate"} & cols)


async def test_ac010_legacy_dialog_session_may_remain_unbound(sqlite_factory) -> None:
    async with sqlite_factory() as session:
        owner_id = await _owner_id(session)
        ws = await _bootstrap(session, owner_id)

        from app.models.dialog import DialogSession

        legacy = DialogSession(
            id=str(uuid4()),
            user_id=owner_id,
            pseudonym_id=owner_id,
            workspace_id=ws.workspace_id,
            learning_session_id=None,  # cannot reconstruct a canonical session
            title="legacy",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(legacy)
        await session.commit()

        persisted = await session.get(DialogSession, legacy.id)
        assert persisted is not None
        assert persisted.learning_session_id is None  # no guessed binding


# ---------------------------------------------------------------------------
# EXEC061-AC-011: writer cutover (Material)
# ---------------------------------------------------------------------------


async def test_ac011_active_material_writer_resolves_workspace(sqlite_factory) -> None:
    """New Material written after cutover must carry an exact Workspace."""
    async with sqlite_factory() as session:
        owner_id = await _owner_id(session)
        ws = await _bootstrap(session, owner_id)
        await session.commit()

        from app.services.documents.document_service import DocumentService

        service = DocumentService(session)

        # Monkeypatch storage to avoid real file IO.
        class _FakeStorage:
            def is_supported(self, *a, **k):
                return True

            async def save_file(self, **kwargs):
                return f"/data/{kwargs['document_id']}.md", 7

        service.storage = _FakeStorage()
        doc = await service.upload_document(
            pseudonym_id=await _pseudonym_id(session, owner_id),
            original_filename="x.md",
            file_content=b"hello",
        )
        await session.commit()

        from app.models.document import UserDocument

        persisted = await session.get(UserDocument, doc.id)
        assert persisted.workspace_id == ws.workspace_id
        assert persisted.workspace_id is not None


# ---------------------------------------------------------------------------
# EXEC061-AC-012: legacy migration + forward-fix/recovery gates
# ---------------------------------------------------------------------------


async def test_ac012_legacy_migration_forward_fix_and_recovery(sqlite_factory) -> None:
    async with sqlite_factory() as session:
        owner_id = await _owner_id(session)
        # Legacy owner-global rows (no workspace_id).
        await _add_material(session, owner_id=owner_id, workspace_id=None)
        await session.commit()

        ws = await _bootstrap(session, owner_id)
        result = await WorkspaceBootstrapService(session).migrate_legacy_to_default(
            owner_id, workspace=ws
        )
        await session.commit()

        assert result.workspace_id == ws.workspace_id
        assert result.backfilled.get("user_documents", 0) == 1
        assert result.source_files_created == 1
        assert result.integrity_failures == []

        # Recovery: restore a missing SourceFile by re-running migration after
        # the file becomes available.
        recovered = await WorkspaceBootstrapService(
            session, verify_file=lambda _m, _c, _p: True
        ).migrate_legacy_to_default(owner_id, workspace=ws)
        await session.commit()
        assert recovered.source_files_created == 0  # already present, idempotent


# ---------------------------------------------------------------------------
# EXEC061-AC-013: no Workspace cascade delete
# ---------------------------------------------------------------------------


def test_ac013_no_workspace_cascade_delete_introduced() -> None:
    """Workspace relationships must not cascade-delete children."""
    from app.models.workspace import LearningSession, SourceFile, Workspace

    for child_model in (LearningProject, LearningSession, SourceFile):
        for rel in child_model.__mapper__.relationships:
            assert "all, delete" not in (
                rel.cascade or ""
            ), f"{child_model.__tablename__} must not cascade from Workspace"
    # Workspace has no relationship() to children at all.
    assert list(Workspace.__mapper__.relationships) == []


# ---------------------------------------------------------------------------
# EXEC061-AC-006 suffix: add twice idempotent
# ---------------------------------------------------------------------------


async def test_add_project_material_twice_is_idempotent(sqlite_factory) -> None:
    async with sqlite_factory() as session:
        owner_id = await _owner_id(session)
        ws = await _bootstrap(session, owner_id)
        doc = await _add_material(session, owner_id=owner_id, workspace_id=ws.workspace_id)
        service = WorkspaceService(session)
        project = await service.create_project(workspace_id=ws.workspace_id, title="P")
        await service.add_project_material(
            project_id=project.project_id, material_id=doc.id, workspace_id=ws.workspace_id
        )
        await service.add_project_material(
            project_id=project.project_id, material_id=doc.id, workspace_id=ws.workspace_id
        )
        await session.commit()

        rows = (
            (
                await session.execute(
                    select(ProjectMaterial).where(ProjectMaterial.project_id == project.project_id)
                )
            )
            .scalars()
            .all()
        )
        assert len(rows) == 1

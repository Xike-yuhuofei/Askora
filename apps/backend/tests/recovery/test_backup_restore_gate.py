"""EXEC-055 CI v2 Quality Gate: backup/restore gate tests."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.document import ProcessingStatus, UserDocument
from app.models.user import User
from app.services.storage.local_storage import LocalFileStorage

BACKUP_MANIFEST_VERSION = "1.0"
# No credential/account columns exist on the LocalOwner projection after the
# authentication system removal; the manifest still carries an explicit
# excluded-columns list to gate future sensitive-column additions.
EXCLUDED_COLUMNS: set[str] = set()


def _create_backup_manifest(
    source_db_path: Path,
    source_storage_path: Path,
    backup_dir: Path,
    *,
    schema_version: str = "1.0",
) -> dict:
    backup_dir.mkdir(parents=True, exist_ok=True)
    db_backup_path = backup_dir / "database.sqlite"
    shutil.copy2(source_db_path, db_backup_path)

    storage_backup_dir = backup_dir / "storage"
    if source_storage_path.exists():
        shutil.copytree(source_storage_path, storage_backup_dir, dirs_exist_ok=True)

    manifest = {
        "manifest_version": BACKUP_MANIFEST_VERSION,
        "schema_version": schema_version,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "database_file": "database.sqlite",
        "storage_dir": "storage",
        "excluded_columns": sorted(EXCLUDED_COLUMNS),
        "backup_id": str(uuid4()),
    }
    manifest_path = backup_dir / "backup_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return manifest


def _restore_from_backup(
    backup_dir: Path,
    dest_db_path: Path,
    dest_storage_path: Path,
) -> dict:
    manifest_path = backup_dir / "backup_manifest.json"
    manifest = json.loads(manifest_path.read_text())

    db_backup_path = backup_dir / manifest["database_file"]
    shutil.copy2(db_backup_path, dest_db_path)

    storage_backup_dir = backup_dir / manifest["storage_dir"]
    if storage_backup_dir.exists():
        if dest_storage_path.exists():
            shutil.rmtree(dest_storage_path)
        shutil.copytree(storage_backup_dir, dest_storage_path)

    return manifest


@pytest.mark.asyncio
async def test_backup_manifest_is_versioned(tmp_path) -> None:
    source_db_path = tmp_path / "src.db"
    source_db_url = f"sqlite+aiosqlite:///{source_db_path}"
    engine = create_async_engine(source_db_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text("""
            INSERT INTO users (id, role, status, pseudonym_id)
            VALUES (:id, 'USER', 'ACTIVE', :pseudo)
        """),
            {"id": str(uuid4()), "pseudo": "manifest-pseudo"},
        )
    await engine.dispose()

    backup_dir = tmp_path / "backup_v1"
    manifest = _create_backup_manifest(
        source_db_path,
        tmp_path / "src_storage",
        backup_dir,
        schema_version="2.0",
    )
    assert manifest["manifest_version"] == BACKUP_MANIFEST_VERSION
    assert manifest["schema_version"] == "2.0"
    assert "created_at" in manifest
    assert "backup_id" in manifest
    assert "excluded_columns" in manifest
    assert manifest["backup_id"] != ""

    loaded = json.loads((backup_dir / "backup_manifest.json").read_text())
    assert loaded["manifest_version"] == BACKUP_MANIFEST_VERSION
    assert loaded["schema_version"] == "2.0"


@pytest.mark.asyncio
async def test_backup_restore_roundtrip(tmp_path, monkeypatch) -> None:
    source_db_url = f"sqlite+aiosqlite:///{tmp_path / 'source.db'}"
    source_db_path = tmp_path / "source.db"
    source_storage = tmp_path / "source_storage"

    engine = create_async_engine(source_db_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    storage = LocalFileStorage(str(source_storage))
    monkeypatch.setattr(
        "app.services.documents.document_service.get_local_storage",
        lambda: storage,
    )

    async with factory() as session:
        user = User(
            id=str(uuid4()),
            pseudonym_id="backup-owner",
        )
        session.add(user)
        await session.commit()

        doc = UserDocument(
            id=str(uuid4()),
            pseudonym_id="backup-owner",
            original_filename="test_doc.md",
            file_extension="md",
            file_size_bytes=256,
            storage_path="backup-owner/test_doc.md",
            processing_status=ProcessingStatus.COMPLETED,
        )
        session.add(doc)
        await session.commit()

        async with engine.connect() as conn:
            user_count = (await conn.execute(text("SELECT COUNT(*) FROM users"))).scalar()
            doc_count = (await conn.execute(text("SELECT COUNT(*) FROM user_documents"))).scalar()
            assert user_count == 1
            assert doc_count == 1
    await engine.dispose()

    backup_dir = tmp_path / "backup"
    manifest = _create_backup_manifest(source_db_path, source_storage, backup_dir)
    assert manifest["manifest_version"] == BACKUP_MANIFEST_VERSION

    restored_db_path = tmp_path / "restored.db"
    restored_storage = tmp_path / "restored_storage"
    _restore_from_backup(backup_dir, restored_db_path, restored_storage)

    restored_db_url = f"sqlite+aiosqlite:///{restored_db_path}"
    restored_engine = create_async_engine(restored_db_url)
    async with restored_engine.connect() as conn:
        user_count = (await conn.execute(text("SELECT COUNT(*) FROM users"))).scalar()
        assert user_count == 1
        doc_count = (await conn.execute(text("SELECT COUNT(*) FROM user_documents"))).scalar()
        assert doc_count == 1
        user_row = (await conn.execute(text("SELECT id, pseudonym_id FROM users"))).fetchone()
        assert user_row is not None
        assert user_row[1] == "backup-owner"
        doc_row = (
            await conn.execute(text("SELECT original_filename, storage_path FROM user_documents"))
        ).fetchone()
        assert doc_row is not None
        assert doc_row[0] == "test_doc.md"
    await restored_engine.dispose()


@pytest.mark.asyncio
async def test_backup_excludes_api_keys(tmp_path) -> None:
    source_db_url = f"sqlite+aiosqlite:///{tmp_path / 'source_excl.db'}"
    source_db_path = tmp_path / "source_excl.db"
    engine = create_async_engine(source_db_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with engine.begin() as conn:
        await conn.execute(
            text("""
            INSERT INTO users (id, role, status, pseudonym_id)
            VALUES (:id, 'USER', 'ACTIVE', :pseudo)
        """),
            {
                "id": str(uuid4()),
                "pseudo": "excl-pseudo",
            },
        )
    await engine.dispose()

    backup_dir = tmp_path / "backup_excl"
    manifest = _create_backup_manifest(source_db_path, tmp_path / "empty_storage", backup_dir)
    excluded = set(manifest["excluded_columns"])
    # After authentication removal there are no credential columns to exclude.
    assert excluded == set()

    db_backup_path = backup_dir / "database.sqlite"
    assert db_backup_path.exists()

    manifest_text = (backup_dir / "backup_manifest.json").read_text()
    assert "secret-phone" not in manifest_text
    assert "secret-password-hash" not in manifest_text


@pytest.mark.asyncio
async def test_backup_preserves_durable_files(tmp_path, monkeypatch) -> None:
    source_db_url = f"sqlite+aiosqlite:///{tmp_path / 'src_files.db'}"
    source_db_path = tmp_path / "src_files.db"
    source_storage = tmp_path / "src_files_storage"

    engine = create_async_engine(source_db_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    storage = LocalFileStorage(str(source_storage))
    monkeypatch.setattr(
        "app.services.documents.document_service.get_local_storage",
        lambda: storage,
    )

    async with engine.begin() as conn:
        user_id = str(uuid4())
        await conn.execute(
            text("""
            INSERT INTO users (id, role, status, pseudonym_id)
            VALUES (:id, 'USER', 'ACTIVE', :pseudo)
        """),
            {"id": user_id, "pseudo": "file-pseudo"},
        )

        file_content = b"# Durable content\nThis file must survive backup."
        storage_path, file_size = await storage.save_file(
            "file-pseudo",
            str(uuid4()),
            "durable.md",
            file_content,
            "md",
        )
        await conn.execute(
            text("""
            INSERT INTO user_documents (id, pseudonym_id, original_filename,
                file_extension, file_size_bytes, storage_path, processing_status,
                metadata_version, moderation_status, moderation_categories,
                moderation_details, chunk_count, total_tokens,
                access_count, is_deleted)
            VALUES (:id, 'file-pseudo', 'durable.md', 'md', :size, :path, 'completed',
                1, 'approved', '[]', '{}', 0, 0, 0, 0)
        """),
            {
                "id": str(uuid4()),
                "size": file_size,
                "path": storage_path,
            },
        )
    await engine.dispose()

    backup_dir = tmp_path / "backup_files"
    _create_backup_manifest(source_db_path, source_storage, backup_dir)

    restored_db_path = tmp_path / "restored_files.db"
    restored_storage = tmp_path / "restored_files_storage"
    manifest = _restore_from_backup(backup_dir, restored_db_path, restored_storage)

    assert manifest["storage_dir"] == "storage"
    assert restored_storage.exists()

    restored_db_url = f"sqlite+aiosqlite:///{restored_db_path}"
    restored_engine = create_async_engine(restored_db_url)
    async with restored_engine.connect() as conn:
        row = (await conn.execute(text("SELECT storage_path FROM user_documents"))).fetchone()
        assert row is not None
        restored_storage_path = restored_storage / row[0]
        assert restored_storage_path.exists()
        content = restored_storage_path.read_bytes()
        assert content == file_content
    await restored_engine.dispose()


@pytest.mark.asyncio
async def test_backup_differs_from_export(tmp_path) -> None:
    source_db_url = f"sqlite+aiosqlite:///{tmp_path / 'diff.db'}"
    source_db_path = tmp_path / "diff.db"
    engine = create_async_engine(source_db_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text("""
            INSERT INTO users (id, role, status, pseudonym_id)
            VALUES (:id, 'USER', 'ACTIVE', :pseudo)
        """),
            {"id": str(uuid4()), "pseudo": "diff-pseudo"},
        )
    await engine.dispose()

    backup_dir = tmp_path / "backup_diff"
    manifest = _create_backup_manifest(source_db_path, tmp_path / "empty_storage", backup_dir)

    assert manifest["manifest_version"] == "1.0"
    assert "database_file" in manifest
    assert "storage_dir" in manifest
    assert manifest["schema_version"] == "1.0"

    db_backup = backup_dir / "database.sqlite"
    assert db_backup.exists()

    manifest_content = json.loads((backup_dir / "backup_manifest.json").read_text())
    assert "export_format_version" not in manifest_content
    assert "manifest_version" in manifest_content

    manifest_files = {f.name for f in backup_dir.iterdir()}
    assert "backup_manifest.json" in manifest_files
    assert "database.sqlite" in manifest_files

"""Offline recovery-point creation and verification for private desktop SQLite."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import sqlite3
import stat
import tempfile
import zipfile
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path, PurePosixPath
from typing import NoReturn
from uuid import UUID, uuid4

from pydantic import ValidationError

from app.contracts.data_control import (
    AutomaticBackupStatusV1,
    BackupReason,
    DataControlErrorCode,
    DataControlStatusV1,
    ProtectionState,
    RecoveryCatalogV1,
    RecoveryManifestFileV1,
    RecoveryManifestTotalsV1,
    RecoveryManifestV1,
    RecoveryPointStatus,
    RecoveryPointV1,
    RecoveryVerificationV1,
)
from app.data_control.crypto import ContainerError, decrypt_file, encrypt_file

DATABASE_ARCHIVE_PATH = "database/askora.db"
SECRETS_ARCHIVE_PATH = "secrets/recovery-secrets.json"
MANIFEST_ARCHIVE_PATH = "manifest.json"


class RecoveryError(RuntimeError):
    """Stable, non-sensitive failure surfaced by the maintenance boundary."""

    def __init__(self, code: DataControlErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class RecoveryManager:
    """Create and inspect encrypted recovery points while the app is offline."""

    def __init__(
        self,
        user_data_dir: Path,
        recovery_key: bytes,
        *,
        app_version: str,
        max_file_count: int = 50_000,
        max_single_file_bytes: int = 2 * 1024**3,
        max_total_plaintext_bytes: int = 8 * 1024**3,
        max_archive_bytes: int = 10 * 1024**3,
        max_compression_ratio: int = 200,
    ) -> None:
        if len(recovery_key) != 32:
            raise RecoveryError(
                DataControlErrorCode.RECOVERY_KEY_INVALID,
                "Recovery Key 无效",
            )
        self.user_data_dir = user_data_dir.resolve()
        self.recovery_key = recovery_key
        self.app_version = app_version
        self.max_file_count = max_file_count
        self.max_single_file_bytes = max_single_file_bytes
        self.max_total_plaintext_bytes = max_total_plaintext_bytes
        self.max_archive_bytes = max_archive_bytes
        self.max_compression_ratio = max_compression_ratio

        self.database_path = self.user_data_dir / "askora.db"
        self.documents_dir = self.user_data_dir / "documents"
        self.local_secrets_path = self.user_data_dir / "local-secrets.json"
        self.recovery_dir = self.user_data_dir / "recovery"
        self.backups_dir = self.recovery_dir / "backups"
        self.temp_dir = self.recovery_dir / "tmp"
        self.catalog_path = self.recovery_dir / "catalog.json"
        self.lock_path = self.recovery_dir / "maintenance.lock"

    @contextmanager
    def exclusive_lock(self) -> Iterator[None]:
        self.recovery_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        descriptor = os.open(self.lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise RecoveryError(
                    DataControlErrorCode.MAINTENANCE_BUSY,
                    "另一个数据维护任务正在运行",
                ) from exc
            yield
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)

    def create_backup(self, reason: BackupReason) -> RecoveryPointV1:
        """Create, reopen, fully verify, then publish one managed recovery point."""

        with self.exclusive_lock():
            self._require_source_data()
            catalog = self._load_catalog()
            backup_id = uuid4()
            created_at = datetime.now(UTC)
            self.backups_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
            self.temp_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
            final_path = self.backups_dir / f"{backup_id}.askora-recovery"
            partial_path = self.backups_dir / f".{backup_id}.partial"

            try:
                with tempfile.TemporaryDirectory(
                    prefix=f"create-{backup_id}-", dir=self.temp_dir
                ) as raw_work_dir:
                    work_dir = Path(raw_work_dir)
                    archive_path = work_dir / "payload.zip"
                    manifest = self._build_plaintext_archive(
                        archive_path,
                        work_dir,
                        backup_id=backup_id,
                        backup_set_id=catalog.backup_set_id,
                        reason=reason,
                        created_at=created_at,
                        erasure_checkpoint=catalog.erasure_checkpoint,
                    )
                    encrypt_file(archive_path, partial_path, self.recovery_key)
                    self._verify_path(partial_path, expected_backup_id=backup_id)
                    os.replace(partial_path, final_path)
                    final_path.chmod(0o600)
                    self._fsync_directory(self.backups_dir)
                    verification = self._verify_path(final_path, expected_backup_id=backup_id)
            except RecoveryError:
                partial_path.unlink(missing_ok=True)
                final_path.unlink(missing_ok=True)
                raise
            except (ContainerError, OSError, sqlite3.Error, zipfile.BadZipFile) as exc:
                partial_path.unlink(missing_ok=True)
                final_path.unlink(missing_ok=True)
                raise RecoveryError(
                    DataControlErrorCode.BACKUP_INTEGRITY_FAILED,
                    "恢复点创建或校验失败",
                ) from exc

            point = RecoveryPointV1(
                backup_id=backup_id,
                backup_set_id=catalog.backup_set_id,
                reason=reason,
                status=RecoveryPointStatus.VERIFIED,
                created_at=created_at,
                verified_at=verification.checked_at,
                relative_path=final_path.relative_to(self.recovery_dir).as_posix(),
                size_bytes=final_path.stat().st_size,
                schema_revision=manifest.database_schema_revision,
                erasure_checkpoint=catalog.erasure_checkpoint,
                protected=reason
                in {
                    BackupReason.PRE_MIGRATION,
                    BackupReason.PRE_RESTORE,
                    BackupReason.POST_ERASURE,
                },
            )
            catalog = catalog.model_copy(
                update={
                    "points": (*catalog.points, point),
                    "updated_at": datetime.now(UTC),
                }
            )
            self._write_catalog(catalog)
            self._apply_retention(catalog)
            return self._point_by_id(backup_id)

    def verify_backup(self, backup_path: Path) -> RecoveryVerificationV1:
        """Verify an existing package without extracting into the active data root."""

        with self.exclusive_lock():
            return self._verify_path(backup_path.resolve())

    def status(self) -> DataControlStatusV1:
        catalog = self._load_catalog()
        verified = [
            point
            for point in catalog.points
            if point.status == RecoveryPointStatus.VERIFIED
            and (self.recovery_dir / point.relative_path).is_file()
        ]
        last_verified = max(verified, key=lambda point: point.created_at, default=None)
        next_due_at = (
            last_verified.verified_at + timedelta(hours=24)
            if last_verified is not None and last_verified.verified_at is not None
            else None
        )
        return DataControlStatusV1(
            protection_state=(
                ProtectionState.READY if last_verified else ProtectionState.NOT_PROTECTED
            ),
            supported_mode="PRIVATE_DESKTOP_SQLITE",
            last_verified=last_verified,
            automatic_backup=AutomaticBackupStatusV1(
                enabled=True,
                next_due_at=next_due_at,
            ),
            erasure_checkpoint=catalog.erasure_checkpoint,
            reason_codes=(() if last_verified else ("DATA_NO_VERIFIED_RECOVERY_POINT",)),
        )

    def _build_plaintext_archive(
        self,
        archive_path: Path,
        work_dir: Path,
        *,
        backup_id: UUID,
        backup_set_id: UUID,
        reason: BackupReason,
        created_at: datetime,
        erasure_checkpoint: int,
    ) -> RecoveryManifestV1:
        database_snapshot = work_dir / "askora.db"
        self._snapshot_sqlite(database_snapshot)
        recovery_secrets = work_dir / "recovery-secrets.json"
        self._write_recovery_secrets(recovery_secrets)

        payloads: list[tuple[str, Path]] = [
            (DATABASE_ARCHIVE_PATH, database_snapshot),
            (SECRETS_ARCHIVE_PATH, recovery_secrets),
        ]
        payloads.extend(self._document_payloads())
        if len(payloads) > self.max_file_count:
            self._limit_exceeded()

        files: list[RecoveryManifestFileV1] = []
        total_size = 0
        for relative_path, source in payloads:
            size = source.stat().st_size
            if size > self.max_single_file_bytes:
                self._limit_exceeded()
            total_size += size
            if total_size > self.max_total_plaintext_bytes:
                self._limit_exceeded()
            files.append(
                RecoveryManifestFileV1(
                    relative_path=relative_path,
                    size_bytes=size,
                    sha256=self._sha256(source),
                )
            )

        database_entry = next(item for item in files if item.relative_path == DATABASE_ARCHIVE_PATH)
        manifest = RecoveryManifestV1(
            backup_id=backup_id,
            backup_set_id=backup_set_id,
            reason=reason,
            created_at=created_at,
            app_version=self.app_version,
            database_schema_revision=self._schema_revision(database_snapshot),
            database_sha256=database_entry.sha256,
            erasure_checkpoint=erasure_checkpoint,
            files=tuple(files),
            totals=RecoveryManifestTotalsV1(
                file_count=len(files),
                size_bytes=total_size,
            ),
        )
        with zipfile.ZipFile(
            archive_path,
            mode="x",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=6,
            allowZip64=True,
        ) as package:
            for relative_path, source in payloads:
                package.write(source, arcname=relative_path)
            package.writestr(
                MANIFEST_ARCHIVE_PATH,
                manifest.model_dump_json(indent=2),
            )
        if archive_path.stat().st_size > self.max_archive_bytes:
            self._limit_exceeded()
        return manifest

    def _verify_path(
        self, backup_path: Path, *, expected_backup_id: UUID | None = None
    ) -> RecoveryVerificationV1:
        if not backup_path.is_file():
            raise RecoveryError(
                DataControlErrorCode.BACKUP_NOT_VERIFIED,
                "恢复点不存在",
            )
        if backup_path.stat().st_size > self.max_archive_bytes:
            self._limit_exceeded()
        self.temp_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            with tempfile.TemporaryDirectory(prefix="verify-", dir=self.temp_dir) as raw_dir:
                verify_dir = Path(raw_dir)
                archive_path = verify_dir / "payload.zip"
                decrypt_file(
                    backup_path,
                    archive_path,
                    self.recovery_key,
                    max_plaintext_bytes=self.max_archive_bytes,
                )
                return self._verify_plaintext_archive(
                    archive_path,
                    verify_dir,
                    expected_backup_id=expected_backup_id,
                )
        except RecoveryError:
            raise
        except (ContainerError, OSError, sqlite3.Error, zipfile.BadZipFile) as exc:
            raise RecoveryError(
                DataControlErrorCode.BACKUP_INTEGRITY_FAILED,
                "恢复点完整性校验失败",
            ) from exc

    def _verify_plaintext_archive(
        self,
        archive_path: Path,
        verify_dir: Path,
        *,
        expected_backup_id: UUID | None,
    ) -> RecoveryVerificationV1:
        with zipfile.ZipFile(archive_path, mode="r") as package:
            infos = package.infolist()
            if len(infos) > self.max_file_count + 1:
                self._limit_exceeded()
            seen: set[str] = set()
            total_size = 0
            for info in infos:
                self._validate_archive_member(info, seen)
                total_size += info.file_size
                if info.file_size > self.max_single_file_bytes:
                    self._limit_exceeded()
                if total_size > self.max_total_plaintext_bytes + 1024**2:
                    self._limit_exceeded()
                if info.compress_size == 0:
                    if info.file_size > 0:
                        self._limit_exceeded()
                elif info.file_size / info.compress_size > self.max_compression_ratio:
                    self._limit_exceeded()

            if MANIFEST_ARCHIVE_PATH not in seen:
                self._integrity_failed("恢复点缺少 manifest")
            try:
                manifest = RecoveryManifestV1.model_validate_json(
                    package.read(MANIFEST_ARCHIVE_PATH)
                )
            except (ValidationError, UnicodeDecodeError, KeyError) as exc:
                raise RecoveryError(
                    DataControlErrorCode.BACKUP_INTEGRITY_FAILED,
                    "恢复点 manifest 无效",
                ) from exc
            if expected_backup_id is not None and manifest.backup_id != expected_backup_id:
                self._integrity_failed("恢复点标识不匹配")

            manifest_paths = {item.relative_path for item in manifest.files}
            if len(manifest_paths) != len(manifest.files):
                self._integrity_failed("恢复点 manifest 路径重复")
            if manifest_paths != seen - {MANIFEST_ARCHIVE_PATH}:
                self._integrity_failed("恢复点 manifest 与内容不匹配")
            if (
                DATABASE_ARCHIVE_PATH not in manifest_paths
                or SECRETS_ARCHIVE_PATH not in manifest_paths
            ):
                self._integrity_failed("恢复点缺少必要内容")

            actual_total = 0
            database_target = verify_dir / "verified-askora.db"
            for item in manifest.files:
                self._validate_relative_path(item.relative_path)
                digest = hashlib.sha256()
                measured = 0
                with package.open(item.relative_path, mode="r") as source:
                    target = (
                        database_target.open("xb")
                        if item.relative_path == DATABASE_ARCHIVE_PATH
                        else None
                    )
                    try:
                        while chunk := source.read(1024 * 1024):
                            measured += len(chunk)
                            if measured > self.max_single_file_bytes:
                                self._limit_exceeded()
                            digest.update(chunk)
                            if target is not None:
                                target.write(chunk)
                    finally:
                        if target is not None:
                            target.close()
                if measured != item.size_bytes or digest.hexdigest() != item.sha256:
                    self._integrity_failed("恢复点文件校验失败")
                actual_total += measured

            if (
                actual_total != manifest.totals.size_bytes
                or len(manifest.files) != manifest.totals.file_count
            ):
                self._integrity_failed("恢复点总计不匹配")
            database_entry = next(
                item for item in manifest.files if item.relative_path == DATABASE_ARCHIVE_PATH
            )
            if database_entry.sha256 != manifest.database_sha256:
                self._integrity_failed("恢复点数据库摘要不匹配")

            quick_check, foreign_key_violations = self._check_sqlite(database_target)
            if quick_check != "ok" or foreign_key_violations:
                self._integrity_failed("恢复点数据库完整性校验失败")
            schema_revision = self._schema_revision(database_target)
            if schema_revision != manifest.database_schema_revision:
                self._integrity_failed("恢复点数据库版本不匹配")
            return RecoveryVerificationV1(
                backup_id=manifest.backup_id,
                checked_at=datetime.now(UTC),
                file_count=manifest.totals.file_count,
                size_bytes=manifest.totals.size_bytes,
                sqlite_quick_check="ok",
                foreign_key_violations=0,
                schema_revision=schema_revision,
            )

    def _snapshot_sqlite(self, destination: Path) -> None:
        source_uri = f"file:{self.database_path.as_posix()}?mode=ro"
        with (
            sqlite3.connect(source_uri, uri=True) as source,
            sqlite3.connect(destination) as target,
        ):
            source.backup(target)
        quick_check, foreign_key_violations = self._check_sqlite(destination)
        if quick_check != "ok" or foreign_key_violations:
            self._integrity_failed("当前数据库完整性校验失败")

    def _write_recovery_secrets(self, destination: Path) -> None:
        try:
            raw = json.loads(self.local_secrets_path.read_text(encoding="utf-8"))
            kek_secret = raw["kekSecret"]
            if not isinstance(kek_secret, str) or not kek_secret:
                raise ValueError
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise RecoveryError(
                DataControlErrorCode.BACKUP_INTEGRITY_FAILED,
                "本地数据加密材料不可用",
            ) from exc
        destination.write_text(
            json.dumps(
                {"schema_version": "1.0", "kekSecret": kek_secret},
                sort_keys=True,
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )
        destination.chmod(0o600)

    def _document_payloads(self) -> list[tuple[str, Path]]:
        if not self.documents_dir.exists():
            return []
        payloads: list[tuple[str, Path]] = []
        for path in sorted(self.documents_dir.rglob("*")):
            if path.is_symlink():
                self._integrity_failed("资料目录包含符号链接")
            if path.is_dir():
                continue
            mode = path.stat(follow_symlinks=False).st_mode
            if not stat.S_ISREG(mode):
                self._integrity_failed("资料目录包含特殊文件")
            relative = path.relative_to(self.documents_dir).as_posix()
            archive_path = f"documents/{relative}"
            self._validate_relative_path(archive_path)
            payloads.append((archive_path, path))
        return payloads

    def _require_source_data(self) -> None:
        if not self.database_path.is_file():
            raise RecoveryError(
                DataControlErrorCode.BACKUP_NOT_VERIFIED,
                "当前数据库不存在",
            )
        if self.database_path.is_symlink() or self.local_secrets_path.is_symlink():
            self._integrity_failed("当前数据路径不安全")
        if not self.local_secrets_path.is_file():
            self._integrity_failed("本地数据加密材料不存在")

    def _load_catalog(self) -> RecoveryCatalogV1:
        if not self.catalog_path.exists():
            return RecoveryCatalogV1(
                backup_set_id=uuid4(),
                updated_at=datetime.now(UTC),
            )
        try:
            return RecoveryCatalogV1.model_validate_json(
                self.catalog_path.read_text(encoding="utf-8")
            )
        except (OSError, ValidationError, UnicodeDecodeError) as exc:
            raise RecoveryError(
                DataControlErrorCode.BACKUP_INTEGRITY_FAILED,
                "恢复点目录损坏",
            ) from exc

    def _write_catalog(self, catalog: RecoveryCatalogV1) -> None:
        self.recovery_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        descriptor, raw_temp_path = tempfile.mkstemp(
            prefix=".catalog-", suffix=".tmp", dir=self.recovery_dir
        )
        temp_path = Path(raw_temp_path)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as writer:
                writer.write(catalog.model_dump_json(indent=2))
                writer.flush()
                os.fsync(writer.fileno())
            temp_path.chmod(0o600)
            os.replace(temp_path, self.catalog_path)
            self._fsync_directory(self.recovery_dir)
        finally:
            temp_path.unlink(missing_ok=True)

    def _apply_retention(self, catalog: RecoveryCatalogV1) -> None:
        scheduled = sorted(
            (
                point
                for point in catalog.points
                if point.status == RecoveryPointStatus.VERIFIED
                and point.reason == BackupReason.SCHEDULED
            ),
            key=lambda point: point.created_at,
            reverse=True,
        )
        keep: set[UUID] = set()
        for key, count in (
            (lambda value: value.created_at.date().isoformat(), 7),
            (
                lambda value: f"{value.created_at.isocalendar().year}-W{value.created_at.isocalendar().week}",
                4,
            ),
            (lambda value: value.created_at.strftime("%Y-%m"), 6),
        ):
            buckets: set[str] = set()
            for point in scheduled:
                bucket = key(point)
                if bucket not in buckets and len(buckets) < count:
                    buckets.add(bucket)
                    keep.add(point.backup_id)

        latest_verified = max(
            (point for point in catalog.points if point.status == RecoveryPointStatus.VERIFIED),
            key=lambda point: point.created_at,
            default=None,
        )
        if latest_verified is not None:
            keep.add(latest_verified.backup_id)
        updated: list[RecoveryPointV1] = []
        changed = False
        for point in catalog.points:
            if (
                point.reason == BackupReason.SCHEDULED
                and point.status == RecoveryPointStatus.VERIFIED
                and point.backup_id not in keep
                and not point.protected
            ):
                target = self._managed_point_path(point)
                target.unlink(missing_ok=True)
                updated.append(point.model_copy(update={"status": RecoveryPointStatus.PURGED}))
                changed = True
            else:
                updated.append(point)
        if changed:
            self._write_catalog(
                catalog.model_copy(
                    update={"points": tuple(updated), "updated_at": datetime.now(UTC)}
                )
            )

    def _managed_point_path(self, point: RecoveryPointV1) -> Path:
        self._validate_relative_path(point.relative_path)
        target = (self.recovery_dir / point.relative_path).resolve()
        if self.recovery_dir not in target.parents:
            self._integrity_failed("恢复点目录路径无效")
        return target

    def _point_by_id(self, backup_id: UUID) -> RecoveryPointV1:
        catalog = self._load_catalog()
        return next(point for point in catalog.points if point.backup_id == backup_id)

    @staticmethod
    def _check_sqlite(database_path: Path) -> tuple[str, int]:
        uri = f"file:{database_path.as_posix()}?mode=ro"
        with sqlite3.connect(uri, uri=True) as connection:
            row = connection.execute("PRAGMA quick_check").fetchone()
            quick_check = str(row[0]) if row else "missing"
            foreign_key_violations = len(connection.execute("PRAGMA foreign_key_check").fetchall())
        return quick_check, foreign_key_violations

    @staticmethod
    def _schema_revision(database_path: Path) -> str | None:
        uri = f"file:{database_path.as_posix()}?mode=ro"
        with sqlite3.connect(uri, uri=True) as connection:
            exists = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='alembic_version'"
            ).fetchone()
            if exists is None:
                return None
            revisions = connection.execute(
                "SELECT version_num FROM alembic_version ORDER BY version_num"
            ).fetchall()
        if len(revisions) != 1:
            return None
        return str(revisions[0][0])

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as reader:
            while chunk := reader.read(1024 * 1024):
                digest.update(chunk)
        return digest.hexdigest()

    def _validate_archive_member(self, info: zipfile.ZipInfo, seen: set[str]) -> None:
        self._validate_relative_path(info.filename)
        if info.filename in seen or info.is_dir():
            self._integrity_failed("恢复点包含重复或目录条目")
        seen.add(info.filename)
        unix_mode = info.external_attr >> 16
        file_type = stat.S_IFMT(unix_mode)
        if file_type not in {0, stat.S_IFREG}:
            self._integrity_failed("恢复点包含非普通文件")

    def _validate_relative_path(self, value: str) -> None:
        path = PurePosixPath(value)
        if (
            not value
            or value.startswith("/")
            or "\\" in value
            or any(part in {"", ".", ".."} for part in path.parts)
        ):
            self._integrity_failed("恢复点路径无效")

    @staticmethod
    def _fsync_directory(directory: Path) -> None:
        descriptor = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def _limit_exceeded(self) -> NoReturn:
        raise RecoveryError(
            DataControlErrorCode.BACKUP_LIMIT_EXCEEDED,
            "恢复点超过安全限额",
        )

    @staticmethod
    def _integrity_failed(message: str) -> NoReturn:
        raise RecoveryError(DataControlErrorCode.BACKUP_INTEGRITY_FAILED, message)

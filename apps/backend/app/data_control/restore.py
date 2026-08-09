"""Crash-consistent staged restore orchestration for desktop SQLite."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any, NoReturn
from uuid import UUID, uuid4

from app.contracts.data_control import (
    ActiveMigrationResultV1,
    BackupReason,
    DataControlErrorCode,
    RecoveryManifestV1,
    RecoveryReportV1,
)
from app.data_control.crypto import decrypt_file
from app.data_control.migration import SchemaCompatibilityError, StagedSchemaMigrator
from app.data_control.recovery import (
    DATABASE_ARCHIVE_PATH,
    MANIFEST_ARCHIVE_PATH,
    SECRETS_ARCHIVE_PATH,
    RecoveryError,
    RecoveryManager,
)

JOURNAL_SCHEMA_VERSION = "1.0"


class RestoreCoordinator:
    def __init__(
        self,
        manager: RecoveryManager,
        *,
        migrator: StagedSchemaMigrator | None = None,
    ) -> None:
        self.manager = manager
        self.migrator = migrator or StagedSchemaMigrator()
        self.restore_staging_dir = manager.recovery_dir / "restore-staging"
        self.activation_old_dir = manager.recovery_dir / "activation-old"
        self.reports_dir = manager.recovery_dir / "reports"
        self.journal_path = manager.recovery_dir / "activation-journal.json"

    def migrate_active(self) -> ActiveMigrationResultV1:
        """Protect, stage-migrate and activate the current desktop dataset."""

        try:
            quick_check, foreign_key_violations = self.manager._check_sqlite(
                self.manager.database_path
            )
        except (OSError, sqlite3.Error) as exc:
            raise RecoveryError(
                DataControlErrorCode.BACKUP_INTEGRITY_FAILED,
                "当前数据库完整性检查失败",
            ) from exc
        if quick_check != "ok" or foreign_key_violations:
            raise RecoveryError(
                DataControlErrorCode.BACKUP_INTEGRITY_FAILED,
                "当前数据库完整性检查失败",
            )

        try:
            schema_before, schema_after, required = self.migrator.plan(
                self.manager.database_path
            )
        except SchemaCompatibilityError as exc:
            raise RecoveryError(
                DataControlErrorCode.RESTORE_SCHEMA_UNSUPPORTED,
                "当前数据库版本不受支持",
            ) from exc
        if not required:
            return ActiveMigrationResultV1(
                required=False,
                schema_before=schema_before,
                schema_after=schema_after,
            )

        pre_migration_point = self.manager.create_backup(BackupReason.PRE_MIGRATION)
        report = self.restore(
            self.manager.recovery_dir / pre_migration_point.relative_path,
            preserve_active_jwt=True,
            staged_reason_code="DATA_MIGRATION_STAGED_AND_ACTIVATED",
        )
        return ActiveMigrationResultV1(
            required=True,
            schema_before=report.schema_before,
            schema_after=report.schema_after or schema_after,
            pre_migration_point=pre_migration_point,
            recovery_report=report,
        )

    def restore(
        self,
        backup_path: Path,
        *,
        preserve_active_jwt: bool = False,
        staged_reason_code: str = "DATA_RESTORE_STAGED_AND_ACTIVATED",
    ) -> RecoveryReportV1:
        """Stage and activate; caller must prove backend readiness before finalize."""

        rescue = self.manager.create_backup(BackupReason.PRE_RESTORE)
        with self.manager.exclusive_lock():
            self._ensure_no_pending_activation()
            started_at = datetime.now(UTC)
            verification = self.manager._verify_path(backup_path.resolve())
            catalog = self.manager._load_catalog()
            transaction_id = uuid4()
            report_id = uuid4()
            staging_root = self.restore_staging_dir / str(transaction_id)
            old_root = self.activation_old_dir / str(transaction_id)
            staging_root.mkdir(parents=True, mode=0o700)
            old_root.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            try:
                manifest = self._extract_verified(
                    backup_path.resolve(),
                    staging_root,
                    expected_backup_id=verification.backup_id,
                )
                if manifest.erasure_checkpoint < catalog.erasure_checkpoint:
                    self._reconciliation_failed("恢复点早于当前删除检查点")
                staged_database = staging_root / DATABASE_ARCHIVE_PATH
                try:
                    schema_before, schema_after = self.migrator.prepare(staged_database)
                except SchemaCompatibilityError as exc:
                    raise RecoveryError(
                        DataControlErrorCode.RESTORE_SCHEMA_UNSUPPORTED,
                        "恢复点数据库版本不受支持",
                    ) from exc
                document_refs = self._reconcile_staging(staging_root)
                self._prepare_runtime_secrets(
                    staging_root,
                    preserve_active_jwt=preserve_active_jwt,
                )
                report = RecoveryReportV1(
                    report_id=report_id,
                    transaction_id=transaction_id,
                    backup_id=manifest.backup_id,
                    rescue_backup_id=rescue.backup_id,
                    status="AWAITING_READINESS",
                    schema_before=schema_before,
                    schema_after=schema_after,
                    file_count=verification.file_count,
                    size_bytes=verification.size_bytes,
                    document_refs_checked=document_refs,
                    projection_actions=(
                        "OUTBOX_RUNNING_TO_PENDING",
                        "DERIVED_PROJECTIONS_REVALIDATE_ON_STARTUP",
                    ),
                    erasure_checkpoint=manifest.erasure_checkpoint,
                    started_at=started_at,
                    reason_codes=(staged_reason_code,),
                )
                self._activate(
                    staging_root,
                    old_root,
                    report,
                )
                self._write_report(report)
                return report
            except RecoveryError:
                if self.journal_path.exists():
                    self._rollback_from_journal(expected_transaction_id=transaction_id)
                else:
                    shutil.rmtree(staging_root, ignore_errors=True)
                    shutil.rmtree(old_root, ignore_errors=True)
                raise
            except Exception as exc:
                if self.journal_path.exists():
                    self._rollback_from_journal(expected_transaction_id=transaction_id)
                else:
                    shutil.rmtree(staging_root, ignore_errors=True)
                    shutil.rmtree(old_root, ignore_errors=True)
                raise RecoveryError(
                    DataControlErrorCode.RESTORE_FAILED_ROLLED_BACK,
                    "恢复失败，当前数据已保持或回滚",
                ) from exc

    def finalize(self, transaction_id: UUID) -> RecoveryReportV1:
        with self.manager.exclusive_lock():
            journal = self._load_journal(transaction_id)
            if journal["phase"] != "AWAITING_READINESS":
                self._activation_failed("恢复事务不等待就绪确认")
            document_refs = self._reconcile_active()
            report = self._load_report(UUID(journal["report_id"]))
            completed = report.model_copy(
                update={
                    "status": "COMPLETED",
                    "completed_at": datetime.now(UTC),
                    "document_refs_checked": document_refs,
                    "reason_codes": (*report.reason_codes, "DATA_RESTORE_READINESS_CONFIRMED"),
                }
            )
            self._write_report(completed)
            catalog = self.manager._load_catalog()
            self.manager._write_catalog(
                catalog.model_copy(
                    update={
                        "erasure_checkpoint": max(
                            catalog.erasure_checkpoint, report.erasure_checkpoint
                        ),
                        "updated_at": datetime.now(UTC),
                    }
                )
            )
            self._cleanup_activation(journal)
            return completed

    def rollback(self, transaction_id: UUID) -> RecoveryReportV1:
        with self.manager.exclusive_lock():
            journal = self._load_journal(transaction_id)
            report = self._load_report(UUID(journal["report_id"]))
            self._rollback_from_journal(expected_transaction_id=transaction_id)
            rolled_back = report.model_copy(
                update={
                    "status": "FAILED_ROLLED_BACK",
                    "completed_at": datetime.now(UTC),
                    "reason_codes": (*report.reason_codes, "DATA_RESTORE_FAILED_ROLLED_BACK"),
                }
            )
            self._write_report(rolled_back)
            return rolled_back

    def recover_interrupted_activation(self) -> str | None:
        with self.manager.exclusive_lock():
            if not self.journal_path.exists():
                return None
            journal = self._read_json(self.journal_path)
            transaction_id = UUID(journal["transaction_id"])
            phase = journal.get("phase")
            if phase == "PREPARED":
                self._cleanup_activation(journal)
                return "DISCARDED_PREPARED_RESTORE"
            self._rollback_from_journal(expected_transaction_id=transaction_id)
            return "ROLLED_BACK_INTERRUPTED_RESTORE"

    def _extract_verified(
        self,
        backup_path: Path,
        staging_root: Path,
        *,
        expected_backup_id: UUID,
    ) -> RecoveryManifestV1:
        descriptor, raw_archive = tempfile.mkstemp(
            prefix="restore-", suffix=".zip", dir=staging_root
        )
        os.close(descriptor)
        archive_path = Path(raw_archive)
        archive_path.unlink()
        try:
            decrypt_file(
                backup_path,
                archive_path,
                self.manager.recovery_key,
                max_plaintext_bytes=self.manager.max_archive_bytes,
            )
            with zipfile.ZipFile(archive_path, "r") as package:
                manifest = RecoveryManifestV1.model_validate_json(
                    package.read(MANIFEST_ARCHIVE_PATH)
                )
                if manifest.backup_id != expected_backup_id:
                    self._reconciliation_failed("恢复点在校验后发生变化")
                expected_files = {item.relative_path: item for item in manifest.files}
                seen: set[str] = set()
                for info in package.infolist():
                    self.manager._validate_archive_member(info, seen)
                    if info.filename == MANIFEST_ARCHIVE_PATH:
                        continue
                    target = staging_root / PurePosixPath(info.filename)
                    resolved = target.resolve()
                    if staging_root.resolve() not in resolved.parents:
                        self._reconciliation_failed("恢复点路径越界")
                    resolved.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                    with package.open(info, "r") as source, resolved.open("xb") as destination:
                        measured = 0
                        digest = hashlib.sha256()
                        while chunk := source.read(1024 * 1024):
                            measured += len(chunk)
                            if measured > self.manager.max_single_file_bytes:
                                self.manager._limit_exceeded()
                            digest.update(chunk)
                            destination.write(chunk)
                    expected = expected_files.get(info.filename)
                    if (
                        expected is None
                        or measured != expected.size_bytes
                        or digest.hexdigest() != expected.sha256
                    ):
                        self._reconciliation_failed("恢复点解压内容校验失败")
                    resolved.chmod(0o600)
                if set(expected_files) != seen - {MANIFEST_ARCHIVE_PATH}:
                    self._reconciliation_failed("恢复点解压清单不匹配")
                return manifest
        finally:
            archive_path.unlink(missing_ok=True)

    def _reconcile_staging(self, staging_root: Path) -> int:
        database_path = staging_root / DATABASE_ARCHIVE_PATH
        documents_path = staging_root / "documents"
        documents_path.mkdir(parents=True, exist_ok=True, mode=0o700)
        checked = self._reconcile_database(database_path, documents_path, recover_outbox=True)
        quick_check, foreign_keys = self.manager._check_sqlite(database_path)
        if quick_check != "ok" or foreign_keys:
            self._reconciliation_failed("迁移后数据库完整性校验失败")
        return checked

    def _reconcile_active(self) -> int:
        return self._reconcile_database(
            self.manager.database_path,
            self.manager.documents_dir,
            recover_outbox=False,
        )

    def _reconcile_database(
        self,
        database_path: Path,
        documents_path: Path,
        *,
        recover_outbox: bool,
    ) -> int:
        with sqlite3.connect(database_path) as connection:
            tables = {
                str(row[0])
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            if recover_outbox and "outbox_tasks" in tables:
                connection.execute(
                    "UPDATE outbox_tasks SET status = 'pending' WHERE status = 'running'"
                )
            if "user_documents" not in tables:
                return 0
            rows = connection.execute(
                "SELECT storage_path, file_size_bytes, moderation_details "
                "FROM user_documents WHERE is_deleted = 0"
            ).fetchall()
            for storage_path, expected_size, raw_details in rows:
                relative_path = self._safe_document_path(str(storage_path))
                source = documents_path / relative_path
                if not source.is_file() or source.is_symlink():
                    self._reconciliation_failed("恢复点缺少已登记资料文件")
                if source.stat().st_size != int(expected_size):
                    self._reconciliation_failed("恢复点资料文件大小不匹配")
                details = self._json_object(raw_details)
                expected_checksum = details.get("raw_asset_checksum")
                if expected_checksum and self._sha256(source) != expected_checksum:
                    self._reconciliation_failed("恢复点资料文件摘要不匹配")
            connection.commit()
            return len(rows)

    def _prepare_runtime_secrets(
        self,
        staging_root: Path,
        *,
        preserve_active_jwt: bool,
    ) -> None:
        source_path = staging_root / SECRETS_ARCHIVE_PATH
        try:
            recovered = self._read_json(source_path)
            if set(recovered) != {"schema_version", "kekSecret"}:
                raise ValueError
            if recovered["schema_version"] != "1.0":
                raise ValueError
            kek_secret = recovered["kekSecret"]
            if not isinstance(kek_secret, str) or not kek_secret:
                raise ValueError
        except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as exc:
            raise RecoveryError(
                DataControlErrorCode.RESTORE_RECONCILIATION_FAILED,
                "恢复点数据加密材料无效",
            ) from exc
        jwt_secret = secrets.token_urlsafe(48)
        if preserve_active_jwt:
            try:
                current = self._read_json(self.manager.local_secrets_path)
                candidate = current["jwtSecret"]
                if not isinstance(candidate, str) or len(candidate) < 16:
                    raise ValueError
                jwt_secret = candidate
            except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as exc:
                raise RecoveryError(
                    DataControlErrorCode.RESTORE_RECONCILIATION_FAILED,
                    "当前会话加密材料无效",
                ) from exc
        runtime_path = staging_root / "local-secrets.json"
        runtime_path.write_text(
            json.dumps(
                {
                    "jwtSecret": jwt_secret,
                    "kekSecret": kek_secret,
                },
                separators=(",", ":"),
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        runtime_path.chmod(0o600)

    def _activate(
        self,
        staging_root: Path,
        old_root: Path,
        report: RecoveryReportV1,
    ) -> None:
        journal = {
            "schema_version": JOURNAL_SCHEMA_VERSION,
            "transaction_id": str(report.transaction_id),
            "report_id": str(report.report_id),
            "backup_id": str(report.backup_id),
            "rescue_backup_id": str(report.rescue_backup_id),
            "phase": "PREPARED",
            "staging_relative_path": staging_root.relative_to(self.manager.recovery_dir).as_posix(),
            "old_relative_path": old_root.relative_to(self.manager.recovery_dir).as_posix(),
        }
        self._write_journal(journal)
        old_root.mkdir(parents=True, mode=0o700)
        for active in (
            self.manager.database_path,
            self.manager.documents_dir,
            self.manager.local_secrets_path,
        ):
            if active.exists():
                os.replace(active, old_root / active.name)
        journal["phase"] = "ACTIVE_MOVED"
        self._write_journal(journal)

        os.replace(staging_root / DATABASE_ARCHIVE_PATH, self.manager.database_path)
        staged_documents = staging_root / "documents"
        os.replace(staged_documents, self.manager.documents_dir)
        os.replace(staging_root / "local-secrets.json", self.manager.local_secrets_path)
        self.manager.database_path.chmod(0o600)
        self.manager.documents_dir.chmod(0o700)
        self.manager.local_secrets_path.chmod(0o600)
        journal["phase"] = "AWAITING_READINESS"
        self._write_journal(journal)

    def _rollback_from_journal(self, *, expected_transaction_id: UUID) -> None:
        journal = self._load_journal(expected_transaction_id)
        if journal["phase"] == "PREPARED":
            self._cleanup_activation(journal)
            return
        old_root = self._journal_directory(journal, "old_relative_path")
        failed_root = self.manager.recovery_dir / "failed-activation" / str(expected_transaction_id)
        failed_root.mkdir(parents=True, mode=0o700)
        for active in (
            self.manager.database_path,
            self.manager.documents_dir,
            self.manager.local_secrets_path,
        ):
            if active.exists():
                os.replace(active, failed_root / active.name)
            previous = old_root / active.name
            if previous.exists():
                os.replace(previous, active)
        self._reconcile_active()
        shutil.rmtree(failed_root, ignore_errors=True)
        self._cleanup_activation(journal)

    def _cleanup_activation(self, journal: dict[str, Any]) -> None:
        staging_root = self._journal_directory(journal, "staging_relative_path")
        old_root = self._journal_directory(journal, "old_relative_path")
        shutil.rmtree(staging_root, ignore_errors=True)
        shutil.rmtree(old_root, ignore_errors=True)
        self.journal_path.unlink(missing_ok=True)

    def _ensure_no_pending_activation(self) -> None:
        if self.journal_path.exists():
            raise RecoveryError(
                DataControlErrorCode.MAINTENANCE_BUSY,
                "存在待完成或待回滚的恢复事务",
            )

    def _load_journal(self, expected_transaction_id: UUID) -> dict[str, Any]:
        if not self.journal_path.is_file():
            self._activation_failed("恢复事务日志不存在")
        journal = self._read_json(self.journal_path)
        if journal.get("schema_version") != JOURNAL_SCHEMA_VERSION or journal.get(
            "transaction_id"
        ) != str(expected_transaction_id):
            self._activation_failed("恢复事务日志不匹配")
        return journal

    def _write_journal(self, journal: dict[str, Any]) -> None:
        self._write_private_json(self.journal_path, journal)

    def _write_report(self, report: RecoveryReportV1) -> None:
        self.reports_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._write_private_json(
            self.reports_dir / f"{report.report_id}.json",
            report.model_dump(mode="json"),
        )

    def _load_report(self, report_id: UUID) -> RecoveryReportV1:
        return RecoveryReportV1.model_validate_json(
            (self.reports_dir / f"{report_id}.json").read_text(encoding="utf-8")
        )

    def _write_private_json(self, target: Path, payload: dict[str, Any]) -> None:
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        descriptor, raw_temp = tempfile.mkstemp(prefix=f".{target.name}-", dir=target.parent)
        temporary = Path(raw_temp)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as writer:
                json.dump(payload, writer, sort_keys=True, separators=(",", ":"))
                writer.flush()
                os.fsync(writer.fileno())
            temporary.chmod(0o600)
            os.replace(temporary, target)
            self.manager._fsync_directory(target.parent)
        finally:
            temporary.unlink(missing_ok=True)

    def _journal_directory(self, journal: dict[str, Any], field: str) -> Path:
        relative = str(journal[field])
        self.manager._validate_relative_path(relative)
        target = (self.manager.recovery_dir / relative).resolve()
        if self.manager.recovery_dir not in target.parents:
            self._activation_failed("恢复事务目录越界")
        return target

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("JSON object required")
        return value

    @staticmethod
    def _json_object(value: Any) -> dict[str, Any]:
        if isinstance(value, str):
            value = json.loads(value)
        return value if isinstance(value, dict) else {}

    def _safe_document_path(self, value: str) -> PurePosixPath:
        path = PurePosixPath(value)
        self.manager._validate_relative_path(value)
        if path.parts[0] in {"database", "documents", "secrets", "recovery"}:
            self._reconciliation_failed("资料路径不是 storage-relative path")
        return path

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as reader:
            while chunk := reader.read(1024 * 1024):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _reconciliation_failed(message: str) -> NoReturn:
        raise RecoveryError(DataControlErrorCode.RESTORE_RECONCILIATION_FAILED, message)

    @staticmethod
    def _activation_failed(message: str) -> NoReturn:
        raise RecoveryError(DataControlErrorCode.RESTORE_FAILED_ROLLED_BACK, message)

"""Narrow JSON CLI used by the trusted Electron maintenance process."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any
from uuid import UUID

from app.contracts.data_control import BackupReason, DataControlErrorCode
from app.data_control.crypto import ContainerError, parse_recovery_key
from app.data_control.recovery import RecoveryError, RecoveryManager

RECOVERY_KEY_ENV = "ASKORA_RECOVERY_KEY"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="askora-backend data-control")
    parser.add_argument("--user-data-dir", required=True, type=Path)
    parser.add_argument("--app-version", default="0.1.0")
    subparsers = parser.add_subparsers(dest="command", required=True)

    backup = subparsers.add_parser("backup")
    backup.add_argument(
        "--reason",
        choices=[reason.value for reason in BackupReason],
        default=BackupReason.MANUAL.value,
    )
    subparsers.add_parser("status")
    verify = subparsers.add_parser("verify")
    verify.add_argument("--path", required=True, type=Path)
    restore = subparsers.add_parser("restore")
    restore.add_argument("--path", required=True, type=Path)
    finalize = subparsers.add_parser("finalize-restore")
    finalize.add_argument("--transaction-id", required=True, type=UUID)
    rollback = subparsers.add_parser("rollback-restore")
    rollback.add_argument("--transaction-id", required=True, type=UUID)
    subparsers.add_parser("recover-interrupted-restore")
    return parser


def run(
    argv: Sequence[str],
    *,
    environ: Mapping[str, str] | None = None,
) -> tuple[int, dict[str, Any]]:
    args = _parser().parse_args(list(argv))
    environment = os.environ if environ is None else environ
    raw_key = environment.get(RECOVERY_KEY_ENV)
    if not raw_key:
        return _error(
            DataControlErrorCode.RECOVERY_KEY_REQUIRED,
            "Recovery Key 不可用",
        )
    try:
        key = parse_recovery_key(raw_key)
    except ContainerError:
        return _error(
            DataControlErrorCode.RECOVERY_KEY_INVALID,
            "Recovery Key 无效",
        )

    manager = RecoveryManager(
        args.user_data_dir,
        key,
        app_version=args.app_version,
    )
    try:
        if args.command == "backup":
            result_payload = manager.create_backup(BackupReason(args.reason)).model_dump(
                mode="json"
            )
        elif args.command == "verify":
            result_payload = manager.verify_backup(args.path).model_dump(mode="json")
        elif args.command in {
            "restore",
            "finalize-restore",
            "rollback-restore",
            "recover-interrupted-restore",
        }:
            from app.data_control.restore import RestoreCoordinator

            coordinator = RestoreCoordinator(manager)
            if args.command == "restore":
                result_payload = coordinator.restore(args.path).model_dump(mode="json")
            elif args.command == "finalize-restore":
                result_payload = coordinator.finalize(args.transaction_id).model_dump(mode="json")
            elif args.command == "rollback-restore":
                result_payload = coordinator.rollback(args.transaction_id).model_dump(mode="json")
            else:
                result_payload = {"action": coordinator.recover_interrupted_activation()}
        else:
            result_payload = manager.status().model_dump(mode="json")
    except RecoveryError as exc:
        return _error(exc.code, exc.message)
    except Exception:
        code = (
            DataControlErrorCode.RESTORE_FAILED_ROLLED_BACK
            if args.command
            in {
                "restore",
                "finalize-restore",
                "rollback-restore",
                "recover-interrupted-restore",
            }
            else DataControlErrorCode.BACKUP_INTEGRITY_FAILED
        )
        return _error(code, "数据维护任务失败")
    return 0, {"ok": True, "result": result_payload}


def main(argv: Sequence[str] | None = None) -> int:
    import sys

    code, payload = run(sys.argv[1:] if argv is None else argv)
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return code


def _error(code: DataControlErrorCode, message: str) -> tuple[int, dict[str, Any]]:
    return 2, {
        "ok": False,
        "error": {
            "code": code.value,
            "message": message,
        },
    }


if __name__ == "__main__":
    raise SystemExit(main())

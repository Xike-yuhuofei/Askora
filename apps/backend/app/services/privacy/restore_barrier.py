"""Atomic restore barrier stored outside the ordinary database snapshot."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


class RestoreBarrierStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> dict[str, dict[str, Any]]:
        if not self.path.exists():
            return {}
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != "1.0" or not isinstance(payload.get("barriers"), dict):
            raise ValueError("PRIVACY_RESTORE_BARRIER_INVALID")
        return dict(payload["barriers"])

    def append(
        self,
        *,
        subject_digest: str,
        request_id: str,
        policy_version: str,
        manifest_digest: str,
        completed_at: datetime,
        cache_scope_digests: tuple[str, ...] = (),
    ) -> str:
        barriers = self.load()
        entry: dict[str, Any] = {
            "request_id": request_id,
            "policy_version": policy_version,
            "manifest_digest": manifest_digest,
            "completed_at": completed_at.isoformat(),
            "cache_scope_digests": list(cache_scope_digests),
        }
        entry["barrier_digest"] = self._digest(entry)
        barriers[subject_digest] = entry
        payload = {"schema_version": "1.0", "barriers": barriers}
        self._atomic_write(payload)
        return entry["barrier_digest"]

    def _atomic_write(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{self.path.name}.", dir=self.path.parent
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(
                    payload, stream, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                )
                stream.flush()
                os.fsync(stream.fileno())
            temporary.chmod(0o600)
            os.replace(temporary, self.path)
            directory_fd = os.open(self.path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if temporary.exists():
                temporary.unlink()

    @staticmethod
    def _digest(value: Any) -> str:
        encoded = json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return "sha256:" + hashlib.sha256(encoded).hexdigest()

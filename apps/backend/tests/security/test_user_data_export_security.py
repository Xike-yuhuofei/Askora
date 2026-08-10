"""Data export security tests for v1 LocalOwner architecture.

EXEC-053: Updated comments to reflect no-auth LocalOwner context.
The export token security logic remains valid and unchanged.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from app.contracts.data_control import DataControlErrorCode
from app.data_control.export import ExportArtifact, ExportRegistry
from app.data_control.recovery import RecoveryError


def test_export_token_is_one_time_and_owner_bound(tmp_path: Path) -> None:
    """Verify export token is one-time use and bound to LocalOwner."""
    registry = ExportRegistry()
    export_id = uuid4()
    artifact = tmp_path / "artifact.zip"
    artifact.write_bytes(b"export")
    token = "t" * 48
    registry.register(
        ExportArtifact(
            export_id=export_id,
            user_id="local-owner",
            path=artifact,
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            expires_at=datetime.now(UTC) + timedelta(minutes=1),
        )
    )

    # Cross-owner consumption should fail
    with pytest.raises(RecoveryError) as cross_owner:
        registry.consume(export_id, "other-owner", token)
    assert cross_owner.value.code == DataControlErrorCode.EXPORT_EXPIRED

    # Correct owner can consume once
    assert registry.consume(export_id, "local-owner", token) == artifact
    # Second consumption should fail (one-time use)
    with pytest.raises(RecoveryError) as replay:
        registry.consume(export_id, "local-owner", token)
    assert replay.value.code == DataControlErrorCode.EXPORT_EXPIRED


def test_expired_export_is_removed_and_rejected(tmp_path: Path) -> None:
    """Verify expired export is removed and rejected."""
    registry = ExportRegistry()
    export_id = uuid4()
    artifact = tmp_path / "expired.zip"
    artifact.write_bytes(b"expired")
    token = "t" * 48
    registry.register(
        ExportArtifact(
            export_id=export_id,
            user_id="local-owner",
            path=artifact,
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            expires_at=datetime.now(UTC) - timedelta(seconds=1),
        )
    )

    with pytest.raises(RecoveryError) as expired:
        registry.consume(export_id, "local-owner", token)

    assert expired.value.code == DataControlErrorCode.EXPORT_EXPIRED
    assert not artifact.exists()

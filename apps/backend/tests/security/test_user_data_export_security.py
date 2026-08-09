from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from app.contracts.data_control import DataControlErrorCode
from app.data_control.export import ExportArtifact, ExportRegistry
from app.data_control.recovery import RecoveryError


def test_export_token_is_one_time_and_current_user_bound(tmp_path: Path) -> None:
    registry = ExportRegistry()
    export_id = uuid4()
    artifact = tmp_path / "artifact.zip"
    artifact.write_bytes(b"export")
    token = "t" * 48
    registry.register(
        ExportArtifact(
            export_id=export_id,
            user_id="owner",
            path=artifact,
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            expires_at=datetime.now(UTC) + timedelta(minutes=1),
        )
    )

    with pytest.raises(RecoveryError) as cross_user:
        registry.consume(export_id, "other-user", token)
    assert cross_user.value.code == DataControlErrorCode.EXPORT_EXPIRED

    assert registry.consume(export_id, "owner", token) == artifact
    with pytest.raises(RecoveryError) as replay:
        registry.consume(export_id, "owner", token)
    assert replay.value.code == DataControlErrorCode.EXPORT_EXPIRED


def test_expired_export_is_removed_and_rejected(tmp_path: Path) -> None:
    registry = ExportRegistry()
    export_id = uuid4()
    artifact = tmp_path / "expired.zip"
    artifact.write_bytes(b"expired")
    token = "t" * 48
    registry.register(
        ExportArtifact(
            export_id=export_id,
            user_id="owner",
            path=artifact,
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            expires_at=datetime.now(UTC) - timedelta(seconds=1),
        )
    )

    with pytest.raises(RecoveryError) as expired:
        registry.consume(export_id, "owner", token)

    assert expired.value.code == DataControlErrorCode.EXPORT_EXPIRED
    assert not artifact.exists()

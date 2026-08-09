from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.contracts.data_control import (
    ErasureOwnerImpactV1,
    ErasurePreviewV1,
    ErasureReceiptV1,
    ErasureReportV1,
    ErasureScope,
    ErasureWorkflowStatus,
)


def test_erasure_preview_report_and_receipt_are_strict_and_content_free() -> None:
    now = datetime.now(UTC)
    preview = ErasurePreviewV1(
        preview_id=uuid4(),
        user_ref="u" * 24,
        scope=ErasureScope.DOCUMENT,
        target_ref="document-1",
        impacts=(
            ErasureOwnerImpactV1(
                owner_system="SYS01",
                estimated_records=3,
                actions=("DELETE_DOCUMENT_FACTS",),
            ),
        ),
        backup_impact="旧恢复点将失效并被清理；随后创建删除后基线。",
        irreversible=True,
        confirmation_phrase="永久删除 document-1",
        expires_at=now,
        confirmation_token="t" * 48,
    )
    report = ErasureReportV1(
        workflow_id=uuid4(),
        scope=preview.scope,
        target_ref_hash="a" * 64,
        status=ErasureWorkflowStatus.AWAITING_RECOVERY_BASELINE,
        checkpoint=1,
        owner_results=(),
        started_at=now,
        reason_codes=("DATA_ERASURE_DATABASE_COMMITTED",),
    )
    receipt = ErasureReceiptV1(
        receipt_id=uuid4(),
        workflow_id=report.workflow_id,
        user_ref=preview.user_ref,
        scope=preview.scope,
        target_ref_hash=report.target_ref_hash,
        checkpoint=1,
        result_digest="b" * 64,
        completed_at=now,
    )

    assert preview.schema_version == "1.0"
    assert report.status == ErasureWorkflowStatus.AWAITING_RECOVERY_BASELINE
    assert "content" not in receipt.model_dump()
    with pytest.raises(ValidationError):
        ErasureReceiptV1.model_validate({**receipt.model_dump(), "checkpoint": 0})
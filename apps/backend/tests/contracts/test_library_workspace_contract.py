"""UI-02A strict library and knowledge-map contract tests."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.contracts.workspace import (
    KnowledgeMapDataV1,
    KnowledgeMapResponseV1,
    KnowledgeMapScopeV1,
    LibraryWorkspaceDataV1,
    LibraryWorkspaceResponseV1,
)

NOW = datetime(2026, 8, 8, tzinfo=timezone.utc)


def test_ui02a_library_contract_is_strict_versioned_and_path_free() -> None:
    """UI02A-VSLICE-AC-001/005: strict v1 query has no storage path field."""
    response = LibraryWorkspaceResponseV1(
        generated_at=NOW,
        correlation_id="request-library",
        data=LibraryWorkspaceDataV1(
            view_state="EMPTY",
            total=0,
            page=1,
            page_size=20,
            documents=(),
        ),
        source_status=(),
    )
    payload = response.model_dump(mode="json")
    assert response.schema_version == "1.0"
    assert "storage_path" not in str(payload)
    with pytest.raises(ValidationError):
        LibraryWorkspaceResponseV1.model_validate({**payload, "storage_path": "/private"})
    with pytest.raises(ValidationError):
        LibraryWorkspaceResponseV1.model_validate({**payload, "schema_version": "2.0"})


def test_ui02a_knowledge_map_contract_rejects_unknown_and_naive_time() -> None:
    """UI-DATA-020/SCHEMA-003: map v1 is immutable, strict and timezone-aware."""
    response = KnowledgeMapResponseV1(
        generated_at=NOW,
        correlation_id="request-map",
        data=KnowledgeMapDataV1(
            scope=KnowledgeMapScopeV1(
                document_refs=(f"source_document:{uuid4()}:revision:imported",),
                graph_version="unavailable",
            ),
            nodes=(),
            edges=(),
            source_spans=(),
        ),
        source_status=(),
    )
    payload = response.model_dump()
    payload["generated_at"] = datetime(2026, 8, 8)
    with pytest.raises(ValidationError):
        KnowledgeMapResponseV1.model_validate(payload)
    with pytest.raises(ValidationError):
        KnowledgeMapResponseV1.model_validate(
            {**response.model_dump(mode="json"), "unexpected": True}
        )

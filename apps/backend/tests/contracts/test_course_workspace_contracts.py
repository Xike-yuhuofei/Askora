"""CWSP-020..027 strict public contract coverage for XIK-189."""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.contracts.workspace import (
    CreateWorkspaceV1,
    SwitchWorkspaceV1,
    WorkspaceTransitionGuardV1,
)


def _guard() -> WorkspaceTransitionGuardV1:
    return WorkspaceTransitionGuardV1(
        composer_draft="CLEAR",
        stream="CLEAR",
        user_note="CLEAR",
        material_position="PRESERVED",
    )


def test_cwsp_090_contracts_are_strict_and_reject_unknown_major() -> None:
    """CWSP-090: v1 rejects unknown fields and an unsupported schema major."""
    with pytest.raises(ValidationError):
        CreateWorkspaceV1.model_validate(
            {
                "schema_version": "2.0",
                "display_name": "线性代数",
                "expected_selection_version": None,
                "transition_guard": _guard().model_dump(mode="json"),
                "idempotency_key": "create-1",
            }
        )
    with pytest.raises(ValidationError):
        SwitchWorkspaceV1.model_validate(
            {
                "target_workspace_id": str(uuid4()),
                "expected_selection_version": 1,
                "transition_guard": _guard().model_dump(mode="json"),
                "idempotency_key": "switch-1",
                "owner_id": str(uuid4()),
            }
        )


@pytest.mark.parametrize(
    "display_name",
    ["", "   ", "a\ncourse", "a\x00course", "a\x7fcourse", "x" * 121],
)
def test_cwsp_024_workspace_name_validation(display_name: str) -> None:
    """CWSP-024/CWSP-060: names are trimmed, bounded and control-free."""
    with pytest.raises(ValidationError):
        CreateWorkspaceV1(
            display_name=display_name,
            expected_selection_version=None,
            transition_guard=_guard(),
            idempotency_key="create-invalid",
        )


def test_cwsp_024_workspace_name_is_canonicalized() -> None:
    command = CreateWorkspaceV1(
        display_name="  线性代数  ",
        expected_selection_version=None,
        transition_guard=_guard(),
        idempotency_key="create-trimmed",
    )
    assert command.display_name == "线性代数"

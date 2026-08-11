"""EXEC-068 canonical current-Workspace read projection coverage."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.models.user import User
from app.models.workspace import Workspace
from app.queries.workspace import WorkspaceContextQueryService

NOW = datetime(2026, 8, 11, 8, 0, tzinfo=timezone.utc)


def _workspace() -> Workspace:
    return Workspace(
        workspace_id=str(uuid4()),
        owner_id=str(uuid4()),
        version=3,
        display_name="线性代数",
        is_default=True,
        lifecycle="active",
    )


def test_exec068_workspace_context_uses_exact_platform_owner_record() -> None:
    """EXEC068-AC-002/003, UXA-DATA-200: no frontend/default alias truth."""
    workspace = _workspace()

    result = WorkspaceContextQueryService(clock=lambda: NOW).get_context(
        workspace,
        correlation_id="exec068-query",
    )

    assert result.schema_version == "1.0"
    assert result.data.view_state == "READY"
    assert result.data.switch_capability == "SINGLE_WORKSPACE"
    assert result.data.current_workspace is not None
    assert str(result.data.current_workspace.workspace_id) == workspace.workspace_id
    assert result.data.current_workspace.display_name == "线性代数"
    assert result.data.current_workspace.version == 3
    assert result.data.current_workspace.workspace_ref == (f"workspace:{workspace.workspace_id}:v3")
    assert result.source_status[0].source_system.value == "PLATFORM_WORKSPACE"
    assert result.source_status[0].source_ref == result.data.current_workspace.workspace_ref


@pytest.mark.asyncio
async def test_exec068_workspace_context_http_is_private_and_side_effect_free() -> None:
    """API-310/STATE-AC-310: strict query endpoint performs no command."""
    from httpx import ASGITransport, AsyncClient

    from app.main import app as fastapi_app
    from app.services.owner.dependencies import get_current_owner_projection
    from app.services.workspace.dependencies import get_default_workspace

    workspace = _workspace()
    current_user = User(id=str(uuid4()), pseudonym_id="ui04-workspace-user")

    async def override_workspace() -> Workspace:
        return workspace

    async def override_owner() -> User:
        return current_user

    fastapi_app.dependency_overrides[get_default_workspace] = override_workspace
    fastapi_app.dependency_overrides[get_current_owner_projection] = override_owner
    try:
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.get("/api/v1/workspace/context")
            second = await client.get("/api/v1/workspace/context")

        assert first.status_code == 200, first.text
        assert first.headers["cache-control"] == "private, no-store"
        assert first.json()["data"] == second.json()["data"]
        assert first.json()["data"]["current_workspace"]["workspace_id"] == (workspace.workspace_id)
        assert first.json()["data"]["switch_capability"] == "SINGLE_WORKSPACE"
    finally:
        fastapi_app.dependency_overrides.clear()

"""L0 ownership/import boundaries for ADR-0023 / CWSP-090."""

from __future__ import annotations

import inspect

from app.api.v1 import workspace as workspace_api
from app.queries.workspace import CourseActivityIndexQueryService
from app.services.workspace import selection


def test_cwsp_api_is_transport_only_and_does_not_import_repositories() -> None:
    """API-320/DEP-023: transport dispatches application/query services only."""
    source = inspect.getsource(workspace_api)
    assert "WorkspaceRepository" not in source
    assert "WorkspaceSelectionRepository" not in source
    assert ".add(" not in source
    assert ".delete(" not in source


def test_cwsp_activity_index_is_read_only_and_selection_has_one_writer() -> None:
    """STATE-AC-311/CWSP-090: no SYS06 write path or second selection writer."""
    query_source = inspect.getsource(CourseActivityIndexQueryService)
    assert "self._db.add(" not in query_source
    assert "self._db.delete(" not in query_source
    assert "ActivityLifecycleRepository(self._db).append" not in query_source

    writer_source = inspect.getsource(selection.WorkspaceSelectionService)
    assert "WorkspaceSelectionRepository" in writer_source
    assert "localStorage" not in writer_source
    assert "is_default =" not in writer_source

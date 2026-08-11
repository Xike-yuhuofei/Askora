"""Typed RetrievalScope for SYS02 workspace-scoped retrieval (EXEC-063 / XIK-172).

Historical implementation contract (``docs/archive/exec-plans/EXEC-063-*.md`` §4):

    workspace_id:       required
    project_ids:        optional
    material_ids:       optional
    knowledge_unit_ids: optional
    session_context:    optional

``LocalOwner`` is the ownership context, NOT RetrievalScope. Ordinary
production retrieval MUST resolve an exact ``workspace_id`` before SYS02
execution. Optional refs may only narrow *inside* the required Workspace.

Governing: ADR-0016 (WSP-073), SYS02-*, WSP-040/042/043.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RetrievalScope:
    """The single typed scope every production SYS02 retrieval must carry.

    ``workspace_id`` is required and non-empty. Optional subordinate refs
    (projects / materials / knowledge units) may only narrow inside that
    Workspace; they are validated by the service layer that builds the scope
    from the exact Workspace-scoped available set.
    """

    workspace_id: str
    project_ids: tuple[str, ...] = ()
    material_ids: tuple[str, ...] = ()
    knowledge_unit_ids: tuple[str, ...] = ()
    session_context: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.workspace_id:
            raise ValueError("RetrievalScope requires an exact non-empty workspace_id")
        object.__setattr__(self, "project_ids", tuple(sorted(self.project_ids, key=str)))
        object.__setattr__(self, "material_ids", tuple(sorted(self.material_ids, key=str)))
        object.__setattr__(
            self, "knowledge_unit_ids", tuple(sorted(self.knowledge_unit_ids, key=str))
        )

    def cache_salt(self) -> str:
        """Deterministic scope-only salt for cache/index keys (EXEC063-AC-005).

        Two scopes that differ in Workspace or any subordinate narrowing MUST
        never hash to the same salt, so cache entries can never be reused
        across Workspace or exposure boundaries.
        """
        return "|".join(
            (
                self.workspace_id,
                ",".join(self.project_ids),
                ",".join(self.material_ids),
                ",".join(self.knowledge_unit_ids),
            )
        )

    def to_source_scope(self) -> dict[str, Any]:
        """Project the scope back onto the legacy ``source_scope`` dict shape.

        ``material_ids`` maps to the historical ``document_ids`` key used by
        SYS02; the Workspace is carried explicitly so downstream cache identity
        and provenance stay exact.
        """
        return {
            "workspace_id": self.workspace_id,
            "document_ids": list(self.material_ids),
            "project_ids": list(self.project_ids),
            "knowledge_unit_ids": list(self.knowledge_unit_ids),
        }


def retrieval_scope(
    *,
    workspace_id: str,
    project_ids: Any = (),
    material_ids: Any = (),
    knowledge_unit_ids: Any = (),
    session_context: dict[str, Any] | None = None,
) -> RetrievalScope:
    """Build a :class:`RetrievalScope`, tolerating list/tuple/set shapes."""
    return RetrievalScope(
        workspace_id=str(workspace_id),
        project_ids=tuple(str(item) for item in (project_ids or ())),
        material_ids=tuple(str(item) for item in (material_ids or ())),
        knowledge_unit_ids=tuple(str(item) for item in (knowledge_unit_ids or ())),
        session_context=session_context,
    )

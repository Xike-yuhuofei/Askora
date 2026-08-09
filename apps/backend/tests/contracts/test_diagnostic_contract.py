"""EXEC-022 public contract invariants."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.contracts.adaptive import VersionedRef
from app.contracts.planning import DiagnosticNeedV1

NOW = datetime(2026, 8, 8, 20, 0, tzinfo=timezone.utc)


def _need(**updates) -> DiagnosticNeedV1:
    prerequisite = uuid4()
    values = {
        "need_id": uuid4(),
        "version": 1,
        "user_id": uuid4(),
        "goal_mapping_ref": VersionedRef(
            entity_type="goal_knowledge_mapping", entity_id=str(uuid4()), version=1
        ),
        "goal_subgraph_ref": VersionedRef(
            entity_type="goal_specific_knowledge_subgraph",
            entity_id=str(uuid4()),
            version=1,
        ),
        "target_knowledge_unit_id": uuid4(),
        "prerequisite_knowledge_unit_ids": (prerequisite,),
        "prerequisite_edges": (),
        "unknown_ids": (prerequisite,),
        "unmet_ids": (),
        "sufficient_current_evidence_ids": (),
        "reason_codes": ("DIAGNOSTIC_DECISION_RELEVANT_ONLY",),
        "planner_version": "heuristic-greedy/1.0",
        "diagnostic_planner_version": "graph-adaptive-diagnostic-v1",
        "budget_policy_version": "diagnostic-budget-v1",
        "max_attempts": 2,
        "attempts_used": 0,
        "created_from_learner_state_version": 1,
        "knowledge_graph_versions": ("graph-v1",),
        "current_knowledge_unit_id": prerequisite,
        "status": "active",
        "created_at": NOW,
    }
    values.update(updates)
    return DiagnosticNeedV1.model_validate(values)


def test_diagnostic_need_requires_disjoint_unknown_unmet_sufficient_partition() -> None:
    need = _need()
    with pytest.raises(ValidationError):
        _need(unmet_ids=need.unknown_ids)


def test_diagnostic_need_keeps_unknown_at_budget_stop() -> None:
    need = _need(
        attempts_used=2,
        status="stopped",
        stop_reason="DIAGNOSTIC_BUDGET_EXHAUSTED",
    )
    assert need.unknown_ids
    assert need.attempts_used == need.max_attempts


def test_terminal_diagnostic_requires_explicit_versioned_stop_reason() -> None:
    with pytest.raises(ValidationError):
        _need(status="blocked", stop_reason=None)

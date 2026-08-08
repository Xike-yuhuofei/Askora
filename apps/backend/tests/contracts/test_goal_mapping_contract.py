"""SPEC-D04 additive SYS06 contract validation."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.contracts.planning import GoalKnowledgeMappingV1, LearningGoalV1

NOW = datetime(2026, 8, 8, 18, 0, tzinfo=timezone.utc)


def _goal(**updates) -> LearningGoalV1:
    values = {
        "goal_id": uuid4(),
        "version": 1,
        "user_id": uuid4(),
        "title": "掌握比例",
        "topic": "比例",
        "target_capabilities": ("解释并应用比例",),
        "success_criteria": ("独立解决新的比例问题",),
        "source_document_ids": (uuid4(),),
        "status": "candidate",
        "confirmed_by_user": False,
        "created_at": NOW,
        "reason_codes": ("GOAL_FORMATION_DETERMINISTIC_FALLBACK",),
    }
    values.update(updates)
    return LearningGoalV1(**values)


def test_d04_goal_confirmation_cannot_be_asserted_by_candidate_or_model() -> None:
    with pytest.raises(ValidationError, match="explicit user confirmation"):
        _goal(status="confirmed", confirmed_by_user=False)
    with pytest.raises(ValidationError, match="candidate goal cannot"):
        _goal(status="candidate", confirmed_by_user=True)


def test_d04_blocked_mapping_requires_bounded_clarification() -> None:
    with pytest.raises(ValidationError, match="bounded clarification"):
        GoalKnowledgeMappingV1(
            mapping_id=uuid4(),
            mapping_version=1,
            goal_id=uuid4(),
            goal_version=1,
            source_document_ids=(),
            knowledge_graph_versions=(),
            candidate_target_ids=(),
            selected_target_ids=(),
            excluded_target_ids=(),
            target_evidence=(),
            reason_codes=("SOURCE_SCOPE_EMPTY",),
            mapper_version="goal-knowledge-rrf-v1",
            status="blocked",
            created_at=NOW,
        )


def test_d04_unknown_major_schema_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _goal(goal_schema_version="2.0")

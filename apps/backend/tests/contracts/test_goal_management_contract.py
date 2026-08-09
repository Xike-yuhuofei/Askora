"""P1-01 public contract invariants."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.contracts.goal_management import (
    GoalChangePreviewV1,
    LearningGoalDefinitionV2,
    LearningGoalStateV1,
    SuccessCriterionV1,
)


def test_definition_is_strict_and_has_no_current_status() -> None:
    criterion = SuccessCriterionV1(
        criterion_id=uuid4(),
        cognitive_process="explain",
        statement="不查看资料，独立解释热力学第二定律并给出一个例子",
        target_refs=(),
        evidence_requirements=("independent_explanation", "delayed_independent"),
    )
    definition = LearningGoalDefinitionV2(
        goal_id=uuid4(),
        definition_version=1,
        user_id=uuid4(),
        title="热力学",
        topic="热力学第二定律",
        target_capabilities=("解释",),
        application_context="分析实际热过程",
        success_criteria=(criterion,),
        source_document_ids=(uuid4(),),
        deadline_at=None,
        weekly_time_budget_minutes=90,
        semantic_fingerprint="a" * 64,
        created_at=datetime.now(timezone.utc),
        reason_codes=("GOAL_USER_DEFINED",),
    )
    assert "status" not in definition.model_dump()
    with pytest.raises(ValidationError):
        LearningGoalDefinitionV2.model_validate({**definition.model_dump(), "status": "active"})


def test_state_and_preview_require_exact_versions() -> None:
    goal_id = uuid4()
    state = LearningGoalStateV1(
        goal_id=goal_id,
        state_version=1,
        status="confirmed",
        definition_version=1,
        mapping_ref=None,
        plan_ref=None,
        previous_status=None,
        reason_codes=("GOAL_CONFIRMED",),
        correlation_id=uuid4(),
        created_at=datetime.now(timezone.utc),
    )
    assert state.state_version == 1
    with pytest.raises(ValidationError):
        GoalChangePreviewV1.model_validate(
            {
                "preview_id": uuid4(),
                "preview_version": 1,
                "draft_id": uuid4(),
                "draft_version": 1,
                "goal_id": goal_id,
                "input_refs": [],
                "field_diffs": [],
                "target_cards": [],
                "selected_target_ids": [],
                "plan_impact": {},
                "effective_timing": "immediate",
                "expires_at": datetime.now(timezone.utc),
                "created_at": datetime.now(timezone.utc),
                "unexpected": True,
            }
        )

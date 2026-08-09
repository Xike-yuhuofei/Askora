"""EXEC-021 SYS06 ownership and no-second-graph boundary tests."""

from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2] / "app"


def test_exec021_mapper_has_no_sys01_or_cross_owner_write_path() -> None:
    source = (APP_ROOT / "domains" / "learning_planner" / "goal_mapping.py").read_text(
        encoding="utf-8"
    )
    assert "publish_revision_knowledge" not in source
    assert "LearnerStateRepository" not in source
    assert "ReviewScheduleRepository" not in source
    assert "TeachingPolicy" not in source
    assert "LearningPlan(" not in source


def test_exec021_subgraph_is_ref_only_and_not_a_second_graph_truth() -> None:
    source = (APP_ROOT / "contracts" / "planning.py").read_text(encoding="utf-8")
    marker = source.index("class GoalSpecificKnowledgeSubgraphV1")
    subgraph_source = source[marker:]
    assert "relation_refs" in subgraph_source
    assert "knowledge_graph_versions" in subgraph_source
    assert "PrerequisiteRelation" not in subgraph_source
    assert "relation_payload" not in subgraph_source


def test_exec021_model_is_candidate_only_and_cannot_persist_plan() -> None:
    source = (APP_ROOT / "services" / "learning_goals.py").read_text(encoding="utf-8")
    assert "confirmed_by_user" in source
    assert "GOAL_MODEL_SOURCE_SCOPE_IGNORED" in source
    assert "LearningPlanRepository" not in source
    assert "LearningPlan(" not in source

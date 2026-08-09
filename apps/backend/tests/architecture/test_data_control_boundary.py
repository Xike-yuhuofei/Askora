from __future__ import annotations

from app.data_control.erasure import SUBJECT_BINDINGS, erasure_fail_closed


def test_every_user_data_table_has_explicit_export_and_erasure_disposition() -> None:
    expected = {
        "users",
        "user_profiles",
        "child_profiles",
        "parent_child_relations",
        "consent_records",
        "user_documents",
        "document_chunks",
        "dialog_sessions",
        "dialog_messages",
        "assessment_results",
        "canonical_assessment_attempts",
        "canonical_assessment_result_versions",
        "learner_evidence",
        "canonical_mastery_estimate_versions",
        "learner_state_versions",
        "review_observations",
        "review_schedule_versions",
        "learning_goal_versions",
        "learning_plan_versions",
        "learning_activities",
        "goal_knowledge_mapping_versions",
        "goal_knowledge_subgraph_versions",
        "goal_formation_inferences",
        "diagnostic_need_versions",
        "learning_events",
        "decision_traces",
        "decision_trace_inputs",
        "outbox_tasks",
        "teaching_contexts",
        "teaching_action_versions",
        "experiment_assignments",
        "teaching_episodes",
        "learning_trajectories",
        "outcome_observations",
    }
    by_table = {binding.table_name: binding for binding in SUBJECT_BINDINGS}

    assert set(by_table) == expected
    assert all(binding.owner_system for binding in by_table.values())
    assert all(binding.subject_binding for binding in by_table.values())
    assert all(binding.export_disposition for binding in by_table.values())
    assert all(binding.erasure_scopes for binding in by_table.values())
    assert by_table["users"].export_disposition == "PROFILE_ALLOWLIST_V1"
    assert by_table["user_profiles"].export_disposition == "PROFILE_ALLOWLIST_V1"
    assert by_table["child_profiles"].export_disposition.startswith("EXCLUDED_")
    assert by_table["parent_child_relations"].export_disposition.startswith("EXCLUDED_")
    assert by_table["consent_records"].export_disposition.startswith("EXCLUDED_")
    assert by_table["policy_bundles"] if "policy_bundles" in by_table else True
    assert "policy_bundles" not in by_table


def test_pending_erasure_blocks_product_data_but_keeps_recovery_control_available(
    tmp_path,
) -> None:
    marker = tmp_path / "erasure-pending.json"
    assert not erasure_fail_closed(marker, "/api/v1/dialog/sessions")
    marker.write_text("{}", encoding="utf-8")

    assert erasure_fail_closed(marker, "/api/v1/dialog/sessions")
    assert erasure_fail_closed(marker, "/api/v1/documents")
    assert erasure_fail_closed(marker, "/api/v1/workspace/today")
    assert not erasure_fail_closed(marker, "/api/v1/data-control/erasures/confirm")
    assert not erasure_fail_closed(marker, "/api/v1/auth/login")
    assert not erasure_fail_closed(marker, "/api/v1/users/me")
    assert not erasure_fail_closed(marker, "/ready")

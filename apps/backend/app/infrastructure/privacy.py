"""Privacy-only Core inventory/erasure path for IDP-050..054.

The registry is deliberately explicit.  A newly added table remains unsupported
until it is classified here, causing preview/reconciliation to fail closed.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from sqlalchemy import and_, delete, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base


class RegistryDisposition(str, Enum):
    ERASE = "erase"
    GLOBAL = "global"
    GOVERNANCE = "governance"
    IDENTITY = "identity"


@dataclass(frozen=True)
class SubjectRegistryEntry:
    owner: str
    disposition: RegistryDisposition
    storage_class: str
    deletion_order: int
    subject_columns: tuple[str, ...] = ()
    subject_digest_column: str | None = None
    reference_columns: tuple[str, ...] = ()
    json_columns: tuple[str, ...] = ()
    projection: bool = False
    task_status_column: str | None = None
    propagate_columns: tuple[str, ...] = ()


@dataclass(frozen=True)
class ManifestEntry:
    owner: str
    table_name: str
    record_id: str
    primary_key: tuple[tuple[str, Any], ...]
    storage_class: str
    deletion_order: int
    projection: bool = False
    file_path: str | None = None


@dataclass(frozen=True)
class ManifestBlockingIssue:
    code: str
    table_name: str | None = None
    record_id: str | None = None


@dataclass(frozen=True)
class FrozenSubjectManifest:
    schema_version: str
    policy_version: str
    user_id: str
    pseudonym_id: str
    subject_digest: str
    entries: tuple[ManifestEntry, ...]
    blocking_issues: tuple[ManifestBlockingIssue, ...]
    manifest_digest: str
    data_fingerprint: str


@dataclass(frozen=True)
class OwnerEraseCounts:
    requested_count: int
    deleted_count: int
    missing_count: int
    error_count: int


OWNER_ERASURE_ORDER = (
    "IDENTITY_FREEZE",
    "SYS08_TASKS",
    "SYS01",
    "SYS02",
    "SYS03",
    "SYS04",
    "SYS05",
    "SYS06",
    "SYS07",
    "SYS08_LEDGER",
    "PROJECTIONS",
    "IDENTITY_FINALIZE",
)


def _entry(
    owner: str,
    disposition: RegistryDisposition,
    storage_class: str,
    *,
    subject: tuple[str, ...] = (),
    digest: str | None = None,
    refs: tuple[str, ...] = (),
    json: tuple[str, ...] = (),
    projection: bool = False,
    task_status: str | None = None,
    propagate: tuple[str, ...] = (),
    within_order: int = 0,
) -> SubjectRegistryEntry:
    order = (
        OWNER_ERASURE_ORDER.index(owner) * 100 + within_order
        if owner in OWNER_ERASURE_ORDER
        else 9999
    )
    return SubjectRegistryEntry(
        owner=owner,
        disposition=disposition,
        storage_class=storage_class,
        deletion_order=order,
        subject_columns=subject,
        subject_digest_column=digest,
        reference_columns=refs,
        json_columns=json,
        projection=projection,
        task_status_column=task_status,
        propagate_columns=propagate,
    )


_G = RegistryDisposition.GLOBAL
_E = RegistryDisposition.ERASE
_V = RegistryDisposition.GOVERNANCE
_I = RegistryDisposition.IDENTITY

# All tables registered in app.models are classified here; no heuristic default exists.
SUBJECT_REGISTRY: dict[str, SubjectRegistryEntry] = {
    "assessment_items": _entry("SYS04", _G, "global_canonical"),
    "assessment_results": _entry(
        "SYS04",
        _E,
        "canonical",
        subject=("user_id", "pseudonym_id"),
        json=(
            "knowledge_point_ids",
            "mastery_estimates",
            "detected_misconceptions",
            "item_results",
        ),
    ),
    "book_learning_advance_records": _entry(
        "SYS08_LEDGER",
        _E,
        "workflow_receipt",
        subject=("user_id",),
        refs=("document_id",),
        json=("response_payload",),
    ),
    "book_learning_transcript_turns": _entry(
        "SYS08_LEDGER",
        _E,
        "transcript",
        subject=("user_id",),
        refs=("goal_id", "plan_id", "activity_id", "session_id"),
        json=("response_payload",),
    ),
    "canonical_assessment_attempts": _entry(
        "SYS04", _E, "canonical", subject=("user_id",), json=("payload",), propagate=("id",)
    ),
    "canonical_assessment_result_versions": _entry(
        "SYS04", _E, "canonical", refs=("attempt_id", "supersedes_result_id"), json=("payload",)
    ),
    "canonical_mastery_estimate_versions": _entry(
        "SYS03", _E, "canonical", subject=("user_id",), json=("payload",)
    ),
    "consent_records": _entry(
        "IDENTITY_FINALIZE",
        _E,
        "legacy_identity",
        subject=("user_id", "guardian_user_id"),
    ),
    "child_profiles": _entry(
        "SYS03",
        _E,
        "legacy",
        subject=("child_pseudonym_id",),
        json=("allowed_subjects", "blocked_keywords", "learning_goals", "learning_summary"),
    ),
    "decision_trace_inputs": _entry(
        "SYS08_LEDGER", _E, "immutable_ledger", refs=("decision_id", "entity_id"), within_order=0
    ),
    "decision_traces": _entry(
        "SYS08_LEDGER",
        _E,
        "immutable_ledger",
        refs=("teaching_context_id",),
        json=(
            "inputs",
            "candidates",
            "selected",
            "constraints",
            "algorithm",
            "experiment",
            "v03_payload",
        ),
        within_order=10,
    ),
    "diagnostic_need_versions": _entry(
        "SYS06",
        _E,
        "canonical",
        subject=("user_id",),
        refs=("goal_mapping_id",),
        json=("payload",),
        propagate=("need_id",),
    ),
    "dialog_messages": _entry(
        "SYS08_LEDGER",
        _E,
        "transcript",
        subject=("user_id",),
        refs=("session_id",),
        json=("render_payload", "moderation_result", "watermark_info"),
        within_order=0,
    ),
    "dialog_sessions": _entry(
        "SYS08_LEDGER",
        _E,
        "transcript",
        subject=("user_id", "pseudonym_id"),
        propagate=("id",),
        within_order=10,
    ),
    "document_collection_assignments": _entry(
        "SYS01", _E, "canonical", refs=("document_id", "collection_id"), within_order=0
    ),
    "document_duplicate_suggestions": _entry(
        "SYS01",
        _E,
        "candidate",
        subject=("pseudonym_id",),
        refs=("primary_document_id", "candidate_document_id"),
        json=("evidence",),
        within_order=0,
    ),
    "document_ocr_candidates": _entry(
        "SYS01",
        _E,
        "candidate",
        refs=("run_id",),
        json=("bbox",),
        within_order=0,
    ),
    "document_ocr_runs": _entry(
        "SYS01",
        _E,
        "canonical",
        subject=("pseudonym_id",),
        refs=("document_id", "input_revision_id"),
        json=("languages", "reason_codes"),
        propagate=("id",),
        within_order=5,
    ),
    "document_tag_assignments": _entry(
        "SYS01", _E, "canonical", refs=("document_id", "tag_id"), within_order=0
    ),
    "document_chunks": _entry(
        "SYS01",
        _E,
        "projection",
        refs=("document_id",),
        json=("chunk_metadata",),
        projection=True,
        within_order=0,
    ),
    "experiment_assignments": _entry(
        "SYS08_LEDGER",
        _E,
        "immutable_ledger",
        refs=("unit_ref",),
        json=("payload",),
        propagate=("assignment_id",),
        within_order=30,
    ),
    "goal_formation_inferences": _entry(
        "SYS06", _E, "model_inference", refs=("goal_id",), json=("payload",)
    ),
    "focused_learning_goal_state_versions": _entry(
        "SYS06",
        _E,
        "canonical",
        subject=("user_id",),
        refs=("goal_id",),
        json=("payload",),
    ),
    "goal_achievement_evaluation_versions": _entry(
        "SYS06",
        _E,
        "canonical",
        subject=("user_id",),
        refs=("goal_id",),
        json=("payload",),
    ),
    "goal_achievement_policy_versions": _entry("SYS06", _G, "global_policy", json=("payload",)),
    "goal_assessment_activity_versions": _entry(
        "SYS06",
        _E,
        "canonical",
        subject=("user_id",),
        refs=("goal_id",),
        json=("payload", "grader_payload"),
    ),
    "goal_change_preview_versions": _entry(
        "SYS06",
        _E,
        "candidate",
        subject=("user_id",),
        refs=("draft_id",),
        json=("payload",),
    ),
    "goal_management_command_receipts": _entry(
        "SYS06",
        _E,
        "command_receipt",
        subject=("user_id",),
        json=("response_payload",),
    ),
    "goal_knowledge_mapping_versions": _entry(
        "SYS06", _E, "canonical", refs=("goal_id",), json=("payload",), propagate=("mapping_id",)
    ),
    "goal_knowledge_subgraph_versions": _entry(
        "PROJECTIONS", _E, "projection", refs=("mapping_id",), json=("payload",), projection=True
    ),
    "knowledge_points": _entry("SYS01", _G, "global_canonical"),
    "learner_evidence": _entry(
        "SYS03",
        _E,
        "canonical",
        subject=("user_id",),
        refs=("source_result_id",),
        json=("reason_codes", "payload"),
    ),
    "learner_state_versions": _entry(
        "SYS03",
        _E,
        "canonical",
        subject=("user_id",),
        json=("payload",),
        propagate=("learner_state_id",),
    ),
    "learning_activity_state_versions": _entry(
        "SYS06",
        _E,
        "canonical",
        refs=("activity_id", "plan_id"),
        json=("source_refs",),
        propagate=("id",),
    ),
    "activity_lifecycle_command_receipts": _entry(
        "SYS06",
        _E,
        "command_receipt",
        subject=("user_id",),
        refs=("activity_id",),
        json=("response_payload",),
    ),
    "learning_activities": _entry(
        "SYS06", _E, "canonical", refs=("plan_id",), json=("payload",), propagate=("id",)
    ),
    "learning_events": _entry(
        "SYS08_LEDGER",
        _E,
        "immutable_ledger",
        refs=("aggregate_id", "correlation_id", "causation_id"),
        json=("actor", "context", "payload", "provenance", "trace", "privacy", "v03_payload"),
    ),
    "learning_goal_versions": _entry(
        "SYS06", _E, "canonical", subject=("user_id",), json=("payload",), propagate=("goal_id",)
    ),
    "learning_goal_definition_versions": _entry(
        "SYS06",
        _E,
        "canonical",
        subject=("user_id",),
        json=("payload",),
        propagate=("goal_id",),
    ),
    "learning_goal_draft_versions": _entry(
        "SYS06",
        _E,
        "candidate",
        subject=("user_id",),
        refs=("goal_id",),
        json=("payload",),
        propagate=("draft_id",),
    ),
    "learning_goal_state_versions": _entry(
        "SYS06",
        _E,
        "canonical",
        subject=("user_id",),
        refs=("goal_id",),
        json=("payload",),
    ),
    "learning_materials": _entry("SYS01", _G, "global_canonical"),
    "local_owners": _entry("IDENTITY_FINALIZE", _V, "privacy_governance"),
    "library_collections": _entry(
        "SYS01", _E, "canonical", subject=("pseudonym_id",), propagate=("id",), within_order=15
    ),
    "library_command_receipts": _entry(
        "SYS01",
        _E,
        "command_receipt",
        subject=("pseudonym_id",),
        json=("result_payload",),
    ),
    "library_search_projections": _entry(
        "SYS01",
        _E,
        "projection",
        subject=("pseudonym_id",),
        refs=("document_id", "revision_id"),
        json=("source_span_refs",),
        projection=True,
        within_order=0,
    ),
    "library_tags": _entry(
        "SYS01", _E, "canonical", subject=("pseudonym_id",), propagate=("id",), within_order=15
    ),
    "learning_plan_versions": _entry(
        "SYS06",
        _E,
        "canonical",
        refs=("learning_goal_id",),
        json=("payload",),
        propagate=("plan_id",),
    ),
    "learning_plan_state_versions": _entry(
        "SYS06", _E, "canonical", refs=("plan_id",), json=("payload",)
    ),
    "learning_objective_versions": _entry(
        "SYS06",
        _E,
        "canonical",
        subject=("user_id",),
        refs=("goal_id",),
        json=("payload",),
    ),
    "learning_projects": _entry(
        "IDENTITY_FINALIZE",
        _E,
        "platform_scope",
        refs=("workspace_id",),
        propagate=("project_id",),
    ),
    "learning_session_materials": _entry(
        "IDENTITY_FINALIZE",
        _E,
        "platform_scope",
        refs=("session_id", "material_id"),
    ),
    "learning_sessions": _entry(
        "IDENTITY_FINALIZE",
        _E,
        "platform_scope",
        refs=("workspace_id",),
        propagate=("session_id",),
    ),
    "learning_trajectories": _entry(
        "SYS08_LEDGER",
        _E,
        "immutable_ledger",
        subject=("user_id",),
        json=("payload",),
        propagate=("trajectory_id",),
        within_order=30,
    ),
    "material_lifecycle_receipts": _entry(
        "SYS01",
        _E,
        "material_lifecycle_receipt",
        subject=("pseudonym_id",),
        refs=("material_id",),
        json=("result_payload",),
    ),
    "outbox_tasks": _entry(
        "SYS08_TASKS",
        _E,
        "durable_task",
        refs=("idempotency_key",),
        json=("payload",),
        task_status="status",
    ),
    "outcome_observations": _entry(
        "SYS08_LEDGER",
        _E,
        "immutable_ledger",
        refs=(
            "measurement_entity_id",
            "teaching_episode_id",
            "learning_trajectory_id",
            "experiment_assignment_id",
        ),
        json=("payload",),
        within_order=20,
    ),
    "onboarding_preference_command_receipts": _entry(
        "PROJECTIONS", _E, "platform_preference_receipt", subject=("user_id",)
    ),
    "onboarding_preferences": _entry(
        "PROJECTIONS", _E, "platform_preference", subject=("user_id",)
    ),
    "parent_child_relations": _entry(
        "IDENTITY_FINALIZE", _E, "legacy_identity", subject=("parent_id", "child_id")
    ),
    "policy_bundle_activations": _entry("SYS05", _G, "global_policy"),
    "policy_bundles": _entry("SYS05", _G, "global_policy"),
    "project_materials": _entry(
        "IDENTITY_FINALIZE",
        _E,
        "platform_scope",
        refs=("project_id", "material_id"),
        propagate=("project_id",),
    ),
    "recovery_events": _entry(
        "SYS08_LEDGER",
        _E,
        "operational_audit",
        subject=("pseudonym_id",),
        refs=("resource_ref", "correlation_id"),
        json=("safe_details",),
        within_order=40,
    ),
    "review_observations": _entry(
        "SYS07", _E, "canonical", subject=("user_id",), json=("payload",)
    ),
    "review_schedule_versions": _entry(
        "SYS07", _E, "canonical", subject=("user_id",), json=("payload",)
    ),
    "source_files": _entry(
        "SYS01",
        _E,
        "canonical_file",
        refs=("material_id",),
        within_order=0,
    ),
    "strategy_templates": _entry("SYS05", _G, "global_policy"),
    "teaching_action_versions": _entry(
        "SYS05", _E, "immutable_decision", refs=("decision_id", "context_id"), json=("payload",)
    ),
    "teaching_contexts": _entry(
        "SYS05", _E, "immutable_decision", json=("payload",), propagate=("context_id",)
    ),
    "teaching_episodes": _entry(
        "SYS08_LEDGER",
        _E,
        "immutable_ledger",
        subject=("user_id",),
        json=("payload",),
        propagate=("episode_id",),
        within_order=30,
    ),
    "user_documents": _entry(
        "SYS01",
        _E,
        "canonical_file",
        subject=("pseudonym_id",),
        json=("moderation_categories", "moderation_details"),
        propagate=("id",),
        within_order=20,
    ),
    "user_profiles": _entry(
        "SYS03",
        _E,
        "canonical",
        subject=("pseudonym_id",),
        json=("favorite_subjects", "mastery_summary", "metacognition", "affective"),
    ),
    "users": _entry("IDENTITY_FINALIZE", _I, "identity", subject=("id", "pseudonym_id")),
    "workspace_command_receipts": _entry(
        "IDENTITY_FINALIZE",
        _E,
        "platform_command_receipt",
        refs=("owner_id",),
        json=("response_payload",),
    ),
    "workspace_selections": _entry(
        "IDENTITY_FINALIZE",
        _E,
        "platform_preference",
        refs=("owner_id", "current_workspace_id", "previous_workspace_id"),
    ),
    "workspaces": _entry(
        "IDENTITY_FINALIZE",
        _E,
        "platform_scope",
        refs=("owner_id",),
        propagate=("workspace_id",),
    ),
    "data_erasure_workflows": _entry("DATA_CONTROL", _V, "privacy_governance"),
    "data_erasure_steps": _entry("DATA_CONTROL", _V, "privacy_governance"),
    "data_erasure_receipts": _entry("DATA_CONTROL", _V, "privacy_governance"),
    "data_erasure_checkpoints": _entry("DATA_CONTROL", _V, "privacy_governance"),
}


class PrivacyInventoryRepository:
    """Only adapter allowed to physically erase frozen manifest rows."""

    def __init__(self, session: AsyncSession, *, storage_base_path: Path | None = None) -> None:
        self._session = session
        self._storage_base_path = storage_base_path

    async def build_manifest(
        self,
        *,
        user_id: str,
        pseudonym_id: str,
        subject_digest: str,
        subject_digests: tuple[str, ...] = (),
        storage_base_path: Path | None = None,
        policy_version: str = "account-deletion-v1",
    ) -> FrozenSubjectManifest:
        runtime_tables = await self._session.run_sync(
            lambda sync: set(inspect(sync.connection()).get_table_names())
        )
        issues: list[ManifestBlockingIssue] = []
        unknown = runtime_tables - set(SUBJECT_REGISTRY) - {"alembic_version"}
        issues.extend(
            ManifestBlockingIssue(code="PRIVACY_REGISTRY_TABLE_UNCLASSIFIED", table_name=name)
            for name in sorted(unknown)
        )

        other_subject_values: set[str] = set()
        users = Base.metadata.tables["users"]
        for user_row in (await self._session.execute(select(users))).mappings():
            if user_row["id"] != user_id:
                other_subject_values.update({str(user_row["id"]), str(user_row["pseudonym_id"])})

        owned_tokens: set[str] = {user_id, pseudonym_id, subject_digest, *subject_digests}
        selected: dict[tuple[str, str], ManifestEntry] = {}
        rows_by_table: dict[str, list[dict[str, Any]]] = {}
        for table_name, registry in SUBJECT_REGISTRY.items():
            if table_name not in runtime_tables or registry.disposition in {
                RegistryDisposition.GOVERNANCE,
                RegistryDisposition.IDENTITY,
            }:
                continue
            table = Base.metadata.tables[table_name]
            rows_by_table[table_name] = [
                dict(row) for row in (await self._session.execute(select(table))).mappings()
            ]

        changed = True
        while changed:
            changed = False
            for table_name, rows in rows_by_table.items():
                registry = SUBJECT_REGISTRY[table_name]
                if registry.disposition is RegistryDisposition.GLOBAL:
                    for record_row in rows:
                        if self._row_json_contains(
                            record_row, registry.json_columns, {user_id, pseudonym_id}
                        ):
                            issues.append(
                                ManifestBlockingIssue(
                                    code="PRIVACY_GLOBAL_RECORD_CONTAINS_SUBJECT",
                                    table_name=table_name,
                                    record_id=self._record_id(
                                        Base.metadata.tables[table_name], record_row
                                    ),
                                )
                            )
                    continue
                for record_row in rows:
                    table = Base.metadata.tables[table_name]
                    record_id = self._record_id(table, record_row)
                    key = (table_name, record_id)
                    if key in selected:
                        continue
                    direct_values = {
                        str(record_row[column])
                        for column in registry.subject_columns
                        if record_row.get(column) is not None
                    }
                    direct_match = bool(direct_values & {user_id, pseudonym_id})
                    digest_match = bool(
                        registry.subject_digest_column
                        and record_row.get(registry.subject_digest_column) in subject_digests
                    )
                    # A row with an explicit different owner cannot be pulled in by a ref/JSON token.
                    if registry.subject_columns and not direct_match:
                        continue
                    reference_match = any(
                        isinstance(record_row.get(column), str)
                        and record_row[column] in owned_tokens
                        for column in registry.reference_columns
                    )
                    json_match = self._row_json_contains(
                        record_row, registry.json_columns, owned_tokens
                    )
                    if not (direct_match or digest_match or reference_match or json_match):
                        continue
                    if direct_values & other_subject_values:
                        issues.append(
                            ManifestBlockingIssue(
                                code="PRIVACY_SUBJECT_AMBIGUOUS",
                                table_name=table_name,
                                record_id=record_id,
                            )
                        )
                        continue
                    file_path = None
                    if table_name == "user_documents":
                        file_path = self._validated_file_path(
                            record_row.get("storage_path"),
                            pseudonym_id,
                            storage_base_path,
                            issues,
                            record_id,
                        )
                    entry = ManifestEntry(
                        owner=registry.owner,
                        table_name=table_name,
                        record_id=record_id,
                        primary_key=tuple(
                            (column.name, record_row[column.name]) for column in table.primary_key
                        ),
                        storage_class=registry.storage_class,
                        deletion_order=registry.deletion_order,
                        projection=registry.projection,
                        file_path=file_path,
                    )
                    selected[key] = entry
                    for column in table.primary_key:
                        value = record_row[column.name]
                        if isinstance(value, str):
                            owned_tokens.add(value)
                    for propagate_column in registry.propagate_columns:
                        value = record_row.get(propagate_column)
                        if isinstance(value, str):
                            owned_tokens.add(value)
                    changed = True

        entries = tuple(
            sorted(
                selected.values(),
                key=lambda item: (item.deletion_order, item.table_name, item.record_id),
            )
        )
        if storage_base_path is not None:
            user_dir = storage_base_path.resolve() / pseudonym_id  # noqa: ASYNC240
            known_files = {entry.file_path for entry in entries if entry.file_path}
            if user_dir.exists():  # noqa: ASYNC240
                orphan_entries: list[ManifestEntry] = []
                for path in sorted(user_dir.rglob("*")):  # noqa: ASYNC240
                    if path.is_symlink():
                        issues.append(
                            ManifestBlockingIssue(
                                code="PRIVACY_FILE_PATH_INVALID",
                                table_name="__local_files__",
                                record_id=str(
                                    path.relative_to(storage_base_path.resolve())  # noqa: ASYNC240
                                ),
                            )
                        )
                        continue
                    if not path.is_file():
                        continue
                    relative = str(path.relative_to(storage_base_path.resolve()))  # noqa: ASYNC240
                    if relative in known_files:
                        continue
                    orphan_entries.append(
                        ManifestEntry(
                            owner="SYS01",
                            table_name="__local_files__",
                            record_id=relative,
                            primary_key=(("path", relative),),
                            storage_class="orphan_file",
                            deletion_order=OWNER_ERASURE_ORDER.index("SYS01") * 100 + 5,
                            file_path=relative,
                        )
                    )
                entries = tuple(
                    sorted(
                        (*entries, *orphan_entries),
                        key=lambda item: (item.deletion_order, item.table_name, item.record_id),
                    )
                )
        issues_tuple = tuple(
            sorted(
                set(issues),
                key=lambda issue: (issue.code, issue.table_name or "", issue.record_id or ""),
            )
        )
        semantic = {
            "schema_version": "1.0",
            "policy_version": policy_version,
            "subject_digest": subject_digest,
            "entries": [self._entry_payload(entry, storage_base_path) for entry in entries],
            "blocking_issues": [issue.__dict__ for issue in issues_tuple],
        }
        manifest_digest = self._sha256(semantic)
        fingerprint = self._sha256(
            {
                "manifest_digest": manifest_digest,
                "entries": semantic["entries"],
            }
        )
        return FrozenSubjectManifest(
            schema_version="1.0",
            policy_version=policy_version,
            user_id=user_id,
            pseudonym_id=pseudonym_id,
            subject_digest=subject_digest,
            entries=entries,
            blocking_issues=issues_tuple,
            manifest_digest=manifest_digest,
            data_fingerprint=fingerprint,
        )

    async def erase_owner(
        self,
        *,
        owner: str,
        manifest: FrozenSubjectManifest,
    ) -> OwnerEraseCounts:
        if manifest.blocking_issues:
            raise ValueError("PRIVACY_SUBJECT_AMBIGUOUS")
        entries = tuple(entry for entry in manifest.entries if entry.owner == owner)
        deleted_count = 0
        missing_count = 0
        for entry in entries:
            if entry.file_path is not None:
                if self._storage_base_path is None:
                    raise ValueError("PRIVACY_FILE_STORAGE_UNAVAILABLE")
                file_path = (self._storage_base_path.resolve() / entry.file_path).resolve()
                if not file_path.is_relative_to(self._storage_base_path.resolve()):
                    raise ValueError("PRIVACY_FILE_PATH_INVALID")
                if file_path.is_file():
                    file_path.unlink()
                    deleted_count += 1
                else:
                    missing_count += 1
            if entry.table_name == "__local_files__":
                continue
            table = Base.metadata.tables[entry.table_name]
            predicate = and_(*(table.c[column] == value for column, value in entry.primary_key))
            result = await self._session.execute(delete(table).where(predicate))
            affected = int(getattr(result, "rowcount", 0) or 0)
            deleted_count += affected
            missing_count += max(0, 1 - affected)
        return OwnerEraseCounts(
            requested_count=len(entries) + sum(entry.file_path is not None for entry in entries),
            deleted_count=deleted_count,
            missing_count=missing_count,
            error_count=0,
        )

    @staticmethod
    def _record_id(table: Any, row: dict[str, Any]) -> str:
        return "|".join(f"{column.name}={row[column.name]}" for column in table.primary_key)

    @classmethod
    def _row_json_contains(
        cls, row: dict[str, Any], columns: tuple[str, ...], tokens: set[str]
    ) -> bool:
        return any(cls._value_contains(row.get(column), tokens) for column in columns)

    @classmethod
    def _value_contains(cls, value: Any, tokens: set[str]) -> bool:
        if isinstance(value, str):
            return value in tokens
        if isinstance(value, dict):
            return any(cls._value_contains(item, tokens) for item in value.values())
        if isinstance(value, (list, tuple)):
            return any(cls._value_contains(item, tokens) for item in value)
        return False

    @staticmethod
    def _validated_file_path(
        storage_path: Any,
        pseudonym_id: str,
        storage_base_path: Path | None,
        issues: list[ManifestBlockingIssue],
        record_id: str,
    ) -> str | None:
        if not isinstance(storage_path, str) or not storage_path:
            issues.append(
                ManifestBlockingIssue("PRIVACY_FILE_PATH_INVALID", "user_documents", record_id)
            )
            return None
        path = Path(storage_path)
        if (
            path.is_absolute()
            or ".." in path.parts
            or not path.parts
            or path.parts[0] != pseudonym_id
        ):
            issues.append(
                ManifestBlockingIssue("PRIVACY_FILE_PATH_INVALID", "user_documents", record_id)
            )
            return None
        if storage_base_path is not None:
            base = storage_base_path.resolve()
            resolved = (base / path).resolve()
            if not resolved.is_relative_to(base):
                issues.append(
                    ManifestBlockingIssue("PRIVACY_FILE_PATH_INVALID", "user_documents", record_id)
                )
                return None
        return storage_path

    @classmethod
    def _entry_payload(cls, entry: ManifestEntry, storage_base_path: Path | None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "owner": entry.owner,
            "table_name": entry.table_name,
            "record_id": entry.record_id,
            "primary_key": list(entry.primary_key),
            "storage_class": entry.storage_class,
            "deletion_order": entry.deletion_order,
            "projection": entry.projection,
            "file_path": entry.file_path,
        }
        if entry.file_path and storage_base_path is not None:
            path = storage_base_path / entry.file_path
            payload["file_exists"] = path.is_file()
            payload["file_size"] = path.stat().st_size if path.is_file() else 0
        return payload

    @staticmethod
    def _sha256(value: Any) -> str:
        encoded = json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
        ).encode("utf-8")
        return "sha256:" + hashlib.sha256(encoded).hexdigest()


def manifest_to_payload(manifest: FrozenSubjectManifest) -> dict[str, Any]:
    return {
        "schema_version": manifest.schema_version,
        "policy_version": manifest.policy_version,
        "user_id": manifest.user_id,
        "pseudonym_id": manifest.pseudonym_id,
        "subject_digest": manifest.subject_digest,
        "entries": [
            {
                "owner": entry.owner,
                "table_name": entry.table_name,
                "record_id": entry.record_id,
                "primary_key": [list(item) for item in entry.primary_key],
                "storage_class": entry.storage_class,
                "deletion_order": entry.deletion_order,
                "projection": entry.projection,
                "file_path": entry.file_path,
            }
            for entry in manifest.entries
        ],
        "blocking_issues": [issue.__dict__ for issue in manifest.blocking_issues],
        "manifest_digest": manifest.manifest_digest,
        "data_fingerprint": manifest.data_fingerprint,
    }


def manifest_from_payload(payload: dict[str, Any]) -> FrozenSubjectManifest:
    return FrozenSubjectManifest(
        schema_version=payload["schema_version"],
        policy_version=payload["policy_version"],
        user_id=payload["user_id"],
        pseudonym_id=payload["pseudonym_id"],
        subject_digest=payload["subject_digest"],
        entries=tuple(
            ManifestEntry(
                owner=item["owner"],
                table_name=item["table_name"],
                record_id=item["record_id"],
                primary_key=tuple((pair[0], pair[1]) for pair in item["primary_key"]),
                storage_class=item["storage_class"],
                deletion_order=item["deletion_order"],
                projection=item.get("projection", False),
                file_path=item.get("file_path"),
            )
            for item in payload["entries"]
        ),
        blocking_issues=tuple(ManifestBlockingIssue(**item) for item in payload["blocking_issues"]),
        manifest_digest=payload["manifest_digest"],
        data_fingerprint=payload["data_fingerprint"],
    )

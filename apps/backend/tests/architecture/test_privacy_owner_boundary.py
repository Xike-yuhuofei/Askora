"""EXEC036 / IDP-050..053 privacy-only ownership boundary tests."""

from __future__ import annotations

import inspect
import typing
from pathlib import Path

from app.core.database import Base
from app.infrastructure.privacy import (
    OWNER_ERASURE_ORDER,
    SUBJECT_REGISTRY,
    FrozenSubjectManifest,
    PrivacyInventoryRepository,
    RegistryDisposition,
)


def test_subject_registry_explicitly_classifies_every_current_table() -> None:
    import app.models  # noqa: F401

    assert set(SUBJECT_REGISTRY) == set(Base.metadata.tables)
    assert SUBJECT_REGISTRY["users"].disposition is RegistryDisposition.IDENTITY
    assert SUBJECT_REGISTRY["policy_bundles"].disposition is RegistryDisposition.GLOBAL
    assert SUBJECT_REGISTRY["learning_events"].disposition is RegistryDisposition.ERASE
    assert SUBJECT_REGISTRY["outbox_tasks"].disposition is RegistryDisposition.ERASE
    assert SUBJECT_REGISTRY["recovery_events"].disposition is RegistryDisposition.ERASE
    assert SUBJECT_REGISTRY["recovery_events"].subject_columns == ("pseudonym_id",)
    assert SUBJECT_REGISTRY["data_erasure_receipts"].disposition is RegistryDisposition.GOVERNANCE
    assert "owner_erasure_step_receipts" not in Base.metadata.tables


def test_owner_order_matches_frozen_design_and_privacy_repo_requires_manifest() -> None:
    assert OWNER_ERASURE_ORDER == (
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
    assert inspect.signature(PrivacyInventoryRepository.erase_owner)
    hints = typing.get_type_hints(PrivacyInventoryRepository.erase_owner)
    assert hints["manifest"] is FrozenSubjectManifest


def test_privacy_core_path_does_not_import_cross_owner_repositories_or_orm_delete() -> None:
    source = (
        Path(__file__).resolve().parents[2] / "app" / "infrastructure" / "privacy.py"
    ).read_text(encoding="utf-8")
    assert "AssessmentRepository" not in source
    assert "LearningPlanRepository" not in source
    assert "ReviewScheduleRepository" not in source
    assert "OutboxRepository" not in source
    assert ".delete(" not in source
    assert "session.delete" not in source

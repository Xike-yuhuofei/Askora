"""SPEC-D03 candidate, extraction and publication policy contract tests."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.contracts.content import (
    ConceptCandidate,
    ExtractionRun,
    KnowledgePublicationPolicy,
    KnowledgeUnitCandidate,
    PedagogicalAssetCandidate,
    RelationCandidate,
)
from app.domains.content_knowledge.publication import DEFAULT_KNOWLEDGE_PUBLICATION_POLICY


def _candidate_payload(candidate_type: str) -> dict:
    return {
        "candidate_id": uuid4(),
        "candidate_type": candidate_type,
        "revision_id": uuid4(),
        "source_span_ids": [uuid4()],
        "semantic_unit_ids": [uuid4()],
        "extraction_run_id": uuid4(),
        "proposed_payload": {"value": "candidate only"},
        "provenance_type": "model_inferred",
        "confidence": 0.99,
        "status": "candidate",
        "reason_codes": [],
    }


def test_d03_all_candidate_families_are_strict_immutable_envelopes() -> None:
    models = {
        "concept": ConceptCandidate,
        "knowledge_unit": KnowledgeUnitCandidate,
        "relation": RelationCandidate,
        "pedagogical_asset": PedagogicalAssetCandidate,
    }
    for candidate_type, model in models.items():
        candidate = model.model_validate(_candidate_payload(candidate_type))
        assert candidate.candidate_type == candidate_type
        with pytest.raises(ValidationError):
            model.model_validate({**_candidate_payload(candidate_type), "unknown": True})
        with pytest.raises(ValidationError):
            candidate.status = "published"  # type: ignore[misc]


def test_d03_extraction_and_policy_versions_are_complete_and_model_confidence_is_not_truth() -> (
    None
):
    run = ExtractionRun(
        extraction_run_id=uuid4(),
        input_revision_id=uuid4(),
        parser_version="parser-v1",
        semantic_segmentation_version="semantic-v1",
        extractor_version="extractor-v1",
        model_provider="fixture",
        model_name="fixture-model",
        model_snapshot="snapshot-1",
        prompt_version="prompt-1",
        schema_version="schema-1",
        publication_policy_version=DEFAULT_KNOWLEDGE_PUBLICATION_POLICY.policy_version,
        created_at=datetime.now(timezone.utc),
        execution_mode="model_assisted",
    )
    assert run.model_snapshot == "snapshot-1"
    assert DEFAULT_KNOWLEDGE_PUBLICATION_POLICY.model_confidence_is_calibrated is False
    with pytest.raises(ValidationError):
        KnowledgePublicationPolicy.model_validate(
            {
                **DEFAULT_KNOWLEDGE_PUBLICATION_POLICY.model_dump(mode="json"),
                "model_confidence_is_calibrated": True,
            }
        )

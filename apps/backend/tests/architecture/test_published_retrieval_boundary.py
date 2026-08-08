"""EXEC-020 SYS01 projection -> unique SYS02 hybrid owner boundary."""

from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2] / "app"


def test_exec020_canonical_adapter_reuses_hybrid_retriever() -> None:
    """AC-007/008: v0.3 adapter owns no second lexical/vector/graph algorithm."""
    source = (APP_ROOT / "domains" / "retrieval" / "adaptive_evidence_service.py").read_text(
        encoding="utf-8"
    )
    assert "HybridEvidenceRetriever" in source
    assert "rank_candidates" in source
    assert "_lexical_score" not in source
    assert "_dense_cosine" not in source
    assert "GraphRAG" not in source


def test_exec020_projection_service_does_not_write_knowledge_truth() -> None:
    """AC-003/008: the SYS02 adapter only reads canonical content records."""
    source = (APP_ROOT / "services" / "rag_service.py").read_text(encoding="utf-8")
    assert "publish_revision_knowledge" not in source
    assert "KnowledgeUnit(" not in source
    assert "KnowledgeRelation(" not in source
    assert "db.commit" not in source

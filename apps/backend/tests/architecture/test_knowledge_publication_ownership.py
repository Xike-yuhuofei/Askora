"""EXEC-019 SYS01 single-writer and model-boundary architecture tests."""

from __future__ import annotations

from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2] / "app"


def test_exec019_publication_domain_has_no_cross_owner_or_online_model_dependency() -> None:
    source = (APP_ROOT / "domains" / "content_knowledge" / "publication.py").read_text(
        encoding="utf-8"
    )
    forbidden = (
        "app.domains.learner_model",
        "app.domains.assessment",
        "app.domains.learning_planner",
        "app.domains.review_scheduler",
        "app.services.llm",
        "ModelRouter",
        "DocumentChunk",
        "SourceChunk",
    )
    assert all(item not in source for item in forbidden)


def test_exec019_only_sys01_service_invokes_publication_writer() -> None:
    call_sites: list[str] = []
    for path in APP_ROOT.rglob("*.py"):
        if path.name == "publication.py":
            continue
        source = path.read_text(encoding="utf-8")
        if "publish_revision_knowledge(" in source:
            call_sites.append(str(path.relative_to(APP_ROOT)))
    assert call_sites == ["services/documents/document_service.py"]

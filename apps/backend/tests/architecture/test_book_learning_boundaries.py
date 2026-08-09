"""EXEC-023 architecture guards against a second truth or tutor path."""

import ast
from pathlib import Path

BACKEND = Path(__file__).parents[2]


def test_exec023_api_is_transport_only() -> None:
    source = (BACKEND / "app/api/v1/book_learning.py").read_text()
    tree = ast.parse(source)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert not {
        "app.models.document",
        "app.models.planning",
        "app.models.assessment",
        "app.models.adaptive",
    }.intersection(imports)
    assert not any(name.startswith("app.domains") for name in imports)
    assert "TeachingPolicyKernel" not in source
    assert "LearningPlanner(" not in source
    assert "PrerequisiteDiagnosticPlanner(" not in source


def test_exec023_reuses_canonical_teaching_and_owner_contracts() -> None:
    source = (BACKEND / "app/application/book_learning.py").read_text()
    assert "LearningOrchestrationFacade" in source
    assert "CanonicalTurnRequest" in source
    assert "PublishedKnowledgeRAGService" in source
    assert "policy_runtime_resolver or ActivePolicyRuntimeResolver(db)" in source
    assert "UnavailableBookLearningPolicyRuntimeResolver" not in source
    assert "TeachingPolicyKernel" not in source
    assert "class BookTutor" not in source
    assert "class EpubTutor" not in source
    assert "class LearnerState" not in source
    assert "class LearningPlan" not in source
    assert "class TeachingAction" not in source


def test_exec023_has_no_second_default_book_tutor_module() -> None:
    forbidden = {
        "book_tutor.py",
        "epub_tutor.py",
        "book_teaching_policy.py",
        "book_learner_state.py",
    }
    assert not forbidden.intersection({path.name for path in (BACKEND / "app").rglob("*.py")})


def test_exec023_production_policy_runtime_never_imports_test_fixtures() -> None:
    production_source = "\n".join(
        path.read_text(encoding="utf-8") for path in (BACKEND / "app").rglob("*.py")
    )
    assert "tests.fixtures.v03_policy" not in production_source
    assert "exec009-fixture-profile" not in production_source

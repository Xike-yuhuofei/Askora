"""EXEC-075 static guardrails for the LCMS owner and frontend boundary."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FRONTEND_MESSAGES = ROOT / "frontend/src/components/messages"


def test_lcms_130_frontend_message_boundary_exists_without_business_rules() -> None:
    required = {
        "ConversationView.jsx",
        "MessageRenderer.jsx",
        "BlockRenderer.jsx",
        "InteractiveElement.jsx",
    }
    actual = {path.name for path in FRONTEND_MESSAGES.glob("*.jsx")}
    assert required <= actual

    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in FRONTEND_MESSAGES.rglob("*.jsx")
        if path.name in required or "blocks" in path.parts
    )
    forbidden = (
        "SetMastery",
        "next_due_at =",
        "masteryThreshold",
        "scoreAttempt",
        "selectTeachingAction",
        "createReviewItem",
        "dangerouslySetInnerHTML",
        "import(`",
    )
    assert not [token for token in forbidden if token in source]


def test_lcms_130_backend_message_contract_has_no_owner_repository_imports() -> None:
    source = (ROOT / "backend/app/contracts/learning_messages.py").read_text(encoding="utf-8")
    assert "app.models" not in source
    assert "app.repositories" not in source
    assert "SetMastery" not in source
    assert "SetReviewSchedule" not in source


def test_lcms_080_activity_learning_uses_the_stable_conversation_component_chain() -> None:
    source = (ROOT / "frontend/src/pages/ActivityLearning.jsx").read_text(encoding="utf-8")
    assert "components/messages/ConversationView" in source
    assert "<ConversationView" in source
    assert "components/messages/MessageRenderer" not in source

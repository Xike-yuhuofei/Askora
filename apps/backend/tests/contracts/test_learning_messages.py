"""EXEC-075 / LCMS strict message, block, capability, and adapter contracts."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.contracts.learning_messages import (
    EvidenceBlockPayloadV1,
    EvidenceBlockV1,
    ExplanationBlockPayloadV1,
    ExplanationBlockV1,
    FeedbackBlockPayloadV1,
    FeedbackBlockV1,
    InteractiveElementV1,
    KnowledgeBlockPayloadV1,
    KnowledgeBlockV1,
    LearningActivityBlockPayloadV1,
    LearningActivityBlockV1,
    LearningMessageCompatibilityV1,
    LearningMessageContextV1,
    LearningMessageV1,
    MessageBlockMetadataV1,
    ProvenanceV1,
    ReviewApplyBlockPayloadV1,
    ReviewApplyBlockV1,
    TraceReferencesV1,
    VersionedOwnerRefV1,
    adapt_plain_text_message,
    adapt_render_payload_message,
)
from app.contracts.rendering import CardBlockV1, RenderPayloadV1

NOW = datetime(2026, 8, 11, 9, 0, tzinfo=timezone.utc)
WORKSPACE_ID = UUID("11111111-1111-4111-8111-111111111111")


def _ref(system: str, entity_type: str, *, version: str | int = 1) -> VersionedOwnerRefV1:
    return VersionedOwnerRefV1(
        source_system=system,
        entity_type=entity_type,
        entity_id=str(uuid4()),
        version=version,
        workspace_id=WORKSPACE_ID,
        availability="READY",
        freshness_at=NOW,
    )


def _metadata(*refs: VersionedOwnerRefV1, mode: str = "NOT_APPLICABLE") -> MessageBlockMetadataV1:
    return MessageBlockMetadataV1(
        semantic_role="test",
        provenance=ProvenanceV1(
            mode=mode,
            source_refs=refs if mode == "SOURCE_GROUNDED" else (),
        ),
        owner_refs=refs,
        availability="READY",
    )


def _context() -> LearningMessageContextV1:
    return LearningMessageContextV1(
        workspace_ref=_ref("PLATFORM", "Workspace"),
        learning_activity_ref=_ref("SYS06", "LearningActivity"),
        transcript_turn_ref=_ref("SYS08", "BookLearningTranscriptTurn"),
        teaching_action_ref=_ref("SYS05", "TeachingAction", version="3.0"),
        evidence_bundle_ref=_ref("SYS02", "EvidenceBundle", version="3.0"),
    )


def _capability() -> InteractiveElementV1:
    return InteractiveElementV1(
        id="ask-follow-up",
        capability_id="ask-follow-up-v1",
        semantic_primitive="ACTION",
        action_type="ASK_FOLLOW_UP",
        label="继续提问",
        command_contract_ref="SYS08.BookLearningAskFollowUpV1",
        input_refs=(_ref("SYS06", "LearningActivity"),),
        input_schema_ref="LearningInteractionInvocationV1.user_response.text/1.0",
        expected_result_ref_types=("BookLearningTranscriptTurn", "LearningMessage"),
        availability="AVAILABLE",
        requires_idempotency_key=True,
        risk="LOW_RISK_WRITE",
    )


def test_lcms_131_supports_exactly_six_strict_block_types() -> None:
    activity = _ref("SYS06", "LearningActivity")
    action = _ref("SYS05", "TeachingAction", version="3.0")
    assessment = _ref("SYS04", "AssessmentResult")
    blocks = (
        ExplanationBlockV1(
            id="explanation",
            payload=ExplanationBlockPayloadV1(body_markdown="解释"),
            metadata=_metadata(action),
            interactions=(_capability(),),
        ),
        KnowledgeBlockV1(
            id="knowledge",
            payload=KnowledgeBlockPayloadV1(
                title="概念", body_markdown="定义", knowledge_status="PRESENTATION_ONLY"
            ),
            metadata=_metadata(),
        ),
        EvidenceBlockV1(
            id="evidence",
            payload=EvidenceBlockPayloadV1(excerpt="原文", source_label="资料", locator="第 1 节"),
            metadata=_metadata(
                _ref("SYS01", "SourceSpan"),
                _ref("SYS02", "EvidenceBundle"),
                mode="SOURCE_GROUNDED",
            ),
        ),
        LearningActivityBlockV1(
            id="activity",
            payload=LearningActivityBlockPayloadV1(prompt_markdown="请作答", response_mode="TEXT"),
            metadata=_metadata(activity, action),
        ),
        FeedbackBlockV1(
            id="feedback",
            payload=FeedbackBlockPayloadV1(
                feedback_basis="ASSESSMENT_RESULT",
                heading="反馈",
                body_markdown="需要更精确",
                correctness="PARTIAL",
            ),
            metadata=_metadata(assessment),
        ),
        ReviewApplyBlockV1(
            id="review",
            payload=ReviewApplyBlockPayloadV1(
                mode="REVIEW", title="延迟复习", description_markdown="重新回忆"
            ),
            metadata=_metadata(activity),
        ),
    )

    message = LearningMessageV1(
        id="message-1",
        revision=1,
        conversation_id="conversation-1",
        sequence=1,
        role="ASSISTANT",
        timestamp=NOW,
        content="可读降级内容",
        blocks=blocks,
        context=_context(),
        trace_references=TraceReferencesV1(correlation_id="lcms-contract"),
        compatibility=LearningMessageCompatibilityV1(source="CANONICAL", fidelity="FULL"),
    )

    assert [block.type for block in message.blocks] == [
        "EXPLANATION",
        "KNOWLEDGE",
        "EVIDENCE",
        "LEARNING_ACTIVITY",
        "FEEDBACK",
        "REVIEW_APPLY",
    ]

    payload = message.model_dump(mode="json")
    payload["blocks"][0]["arbitrary_command"] = "SetMastery"
    with pytest.raises(ValidationError):
        LearningMessageV1.model_validate(payload)


def test_lcms_131_rejects_duplicate_blocks_and_assessment_feedback_without_result_ref() -> None:
    block = ExplanationBlockV1(
        id="duplicate",
        payload=ExplanationBlockPayloadV1(body_markdown="解释"),
        metadata=_metadata(_ref("SYS05", "TeachingAction")),
    )
    with pytest.raises(ValidationError, match="block ids"):
        LearningMessageV1(
            id="message-duplicate",
            revision=1,
            conversation_id="conversation-1",
            sequence=1,
            role="ASSISTANT",
            timestamp=NOW,
            content="fallback",
            blocks=(block, block),
            context=_context(),
            trace_references=TraceReferencesV1(correlation_id="duplicate"),
            compatibility=LearningMessageCompatibilityV1(source="CANONICAL", fidelity="FULL"),
        )

    with pytest.raises(ValidationError, match="AssessmentResult"):
        FeedbackBlockV1(
            id="invalid-feedback",
            payload=FeedbackBlockPayloadV1(
                feedback_basis="ASSESSMENT_RESULT",
                heading="反馈",
                body_markdown="文本不能替代评分事实",
            ),
            metadata=_metadata(),
        )


def test_lcms_050_rejects_action_command_mismatch() -> None:
    payload = _capability().model_dump(mode="json")
    payload["command_contract_ref"] = "SYS03.SetMasteryV1"
    with pytest.raises(ValidationError, match="command contract"):
        InteractiveElementV1.model_validate(payload)


def test_lcms_092_adapters_are_deterministic_and_never_invent_capabilities() -> None:
    context = _context()
    trace = TraceReferencesV1(correlation_id="adapter")
    plain = adapt_plain_text_message(
        message_id="plain-1",
        conversation_id="conversation-1",
        sequence=1,
        role="ASSISTANT",
        timestamp=NOW,
        content="旧纯文本",
        context=context,
        trace_references=trace,
    )
    rich = adapt_render_payload_message(
        message_id="render-1",
        conversation_id="conversation-1",
        sequence=2,
        role="ASSISTANT",
        timestamp=NOW,
        content="卡片降级文本",
        context=context,
        trace_references=trace,
        render_payload=RenderPayloadV1(
            blocks=(
                CardBlockV1(
                    id="legacy-question",
                    variant="question",
                    title="旧问题",
                    body_markdown="旧卡片没有 exact AssessmentItem。",
                ),
            )
        ),
    )

    assert plain == adapt_plain_text_message(
        message_id="plain-1",
        conversation_id="conversation-1",
        sequence=1,
        role="ASSISTANT",
        timestamp=NOW,
        content="旧纯文本",
        context=context,
        trace_references=trace,
    )
    assert all(not block.interactions for block in (*plain.blocks, *rich.blocks))
    assert plain.compatibility.source == "PLAIN_TEXT_ADAPTER"
    assert rich.compatibility.source == "RENDER_PAYLOAD_V1_ADAPTER"
    assert rich.compatibility.fidelity == "PARTIAL"

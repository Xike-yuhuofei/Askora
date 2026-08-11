"""LCMS-* strict Learning Conversation Message public contracts.

These models describe a SYS08 presentation/transcript artifact.  They contain
references to owner state, never writable copies of SYS01-SYS07 truth.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.contracts.base import ContractModel
from app.contracts.rendering import RenderPayloadV1

SourceSystem = Literal["SYS01", "SYS02", "SYS03", "SYS04", "SYS05", "SYS06", "SYS07", "SYS08", "PLATFORM"]
OwnerAvailability = Literal[
    "READY", "MISSING", "PARTIAL", "STALE", "NOT_APPLICABLE", "LEGACY_COMPAT"
]
MessageRole = Literal["LEARNER", "ASSISTANT", "SYSTEM_NOTICE"]
ActionType = Literal[
    "ASK_FOLLOW_UP",
    "INSPECT_SOURCE",
    "SUBMIT_ATTEMPT",
    "REQUEST_HINT",
    "REQUEST_EXPLANATION",
    "START_ACTIVITY",
]


class VersionedOwnerRefV1(ContractModel):
    source_system: SourceSystem
    entity_type: str = Field(min_length=1, max_length=120)
    entity_id: str = Field(min_length=1, max_length=200)
    version: str | int
    workspace_id: UUID
    availability: OwnerAvailability
    freshness_at: datetime | None = None

    @model_validator(mode="after")
    def require_exact_ready_ref(self) -> VersionedOwnerRefV1:
        if self.availability == "READY" and (
            not str(self.entity_id).strip() or not str(self.version).strip()
        ):
            raise ValueError("READY owner ref requires exact id and version")
        return self


class TraceReferencesV1(ContractModel):
    correlation_id: str = Field(min_length=1, max_length=200)
    workflow_run_ref: VersionedOwnerRefV1 | None = None
    decision_trace_ref: VersionedOwnerRefV1 | None = None
    model_inference_ref: VersionedOwnerRefV1 | None = None
    learning_event_refs: tuple[VersionedOwnerRefV1, ...] = Field(default=(), max_length=64)


class ProvenanceV1(ContractModel):
    mode: Literal[
        "SOURCE_GROUNDED", "EXTERNAL_MODEL", "MIXED", "USER_AUTHORED", "NOT_APPLICABLE"
    ]
    source_refs: tuple[VersionedOwnerRefV1, ...] = Field(default=(), max_length=32)
    source_span_refs: tuple[VersionedOwnerRefV1, ...] = Field(default=(), max_length=32)
    evidence_bundle_ref: VersionedOwnerRefV1 | None = None
    generated_by_ref: VersionedOwnerRefV1 | None = None

    @model_validator(mode="after")
    def require_traceable_grounding(self) -> ProvenanceV1:
        if self.mode == "SOURCE_GROUNDED" and not (
            self.source_refs or self.source_span_refs or self.evidence_bundle_ref
        ):
            raise ValueError("SOURCE_GROUNDED provenance requires exact source refs")
        return self


class MessageBlockMetadataV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    semantic_role: str = Field(min_length=1, max_length=120)
    provenance: ProvenanceV1
    owner_refs: tuple[VersionedOwnerRefV1, ...] = Field(default=(), max_length=32)
    availability: OwnerAvailability
    reason_codes: tuple[str, ...] = Field(default=(), max_length=32)
    accessibility_label: str | None = Field(default=None, max_length=300)


COMMAND_CONTRACT_BY_ACTION: dict[str, str] = {
    "ASK_FOLLOW_UP": "SYS08.BookLearningAskFollowUpV1",
    "INSPECT_SOURCE": "SYS02.InspectSourceV1",
    "SUBMIT_ATTEMPT": "SYS04.SubmitAttemptV1",
    "REQUEST_HINT": "SYS08.RequestHintV1",
    "REQUEST_EXPLANATION": "SYS08.RequestExplanationV1",
    "START_ACTIVITY": "SYS06.StartLearningActivityV1",
}


class InteractiveElementV1(ContractModel):
    id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    capability_id: str = Field(min_length=1, max_length=200)
    semantic_primitive: Literal[
        "ACTION", "NAVIGATION", "DISCLOSURE", "INTERACTIVE_CONTENT", "STATUS_FEEDBACK"
    ]
    action_type: ActionType
    label: str = Field(min_length=1, max_length=200)
    command_contract_ref: str = Field(min_length=1, max_length=200)
    input_refs: tuple[VersionedOwnerRefV1, ...] = Field(default=(), max_length=32)
    input_schema_ref: str = Field(min_length=1, max_length=200)
    expected_result_ref_types: tuple[str, ...] = Field(default=(), max_length=16)
    availability: Literal["AVAILABLE", "UNAVAILABLE", "STALE", "COMPLETED"]
    reason_codes: tuple[str, ...] = Field(default=(), max_length=32)
    requires_idempotency_key: bool
    risk: Literal["READ_ONLY", "LOW_RISK_WRITE"]

    @model_validator(mode="after")
    def enforce_allowlisted_command_contract(self) -> InteractiveElementV1:
        expected = COMMAND_CONTRACT_BY_ACTION[self.action_type]
        if self.command_contract_ref != expected:
            raise ValueError("action and command contract do not match the server allowlist")
        if self.availability == "AVAILABLE" and any(
            ref.availability != "READY" for ref in self.input_refs
        ):
            raise ValueError("AVAILABLE capability requires READY input refs")
        return self


class ExplanationBlockPayloadV1(ContractModel):
    title: str | None = Field(default=None, max_length=200)
    body_markdown: str = Field(min_length=1, max_length=20_000)
    presentation: Literal["DEFAULT", "STEPS", "EXAMPLE", "COMPARISON", "SUMMARY"] = "DEFAULT"


class KnowledgeBlockPayloadV1(ContractModel):
    title: str = Field(min_length=1, max_length=200)
    body_markdown: str = Field(min_length=1, max_length=10_000)
    knowledge_status: Literal["CANONICAL_REF", "PRESENTATION_ONLY"]
    qualifier: str | None = Field(default=None, max_length=500)


class EvidenceBlockPayloadV1(ContractModel):
    excerpt: str = Field(min_length=1, max_length=2_000)
    source_label: str = Field(min_length=1, max_length=300)
    locator: str | None = Field(default=None, max_length=500)
    citation_label: str | None = Field(default=None, max_length=300)


class LearningActivityBlockPayloadV1(ContractModel):
    prompt_markdown: str = Field(min_length=1, max_length=20_000)
    response_mode: Literal["TEXT", "SINGLE_CHOICE", "MULTI_CHOICE", "NUMERIC", "CODE", "NONE"]
    options: tuple[dict[str, Any], ...] = Field(default=(), max_length=100)
    response_constraints: dict[str, Any] = Field(default_factory=dict)


class FeedbackBlockPayloadV1(ContractModel):
    feedback_basis: Literal["ASSESSMENT_RESULT", "NON_ASSESSMENT_EXECUTION_FEEDBACK"]
    heading: str = Field(min_length=1, max_length=200)
    body_markdown: str = Field(min_length=1, max_length=10_000)
    correctness: Literal["CORRECT", "PARTIAL", "INCORRECT", "UNSCORABLE"] | None = None
    assessment_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    diagnostic_summary: str | None = Field(default=None, max_length=2_000)


class ReviewApplyBlockPayloadV1(ContractModel):
    mode: Literal["REVIEW", "APPLY"]
    title: str = Field(min_length=1, max_length=200)
    description_markdown: str = Field(min_length=1, max_length=10_000)
    timing_label: str | None = Field(default=None, max_length=200)


def _has_owner_ref(metadata: MessageBlockMetadataV1, system: str, entity_type: str) -> bool:
    return any(
        ref.source_system == system
        and ref.entity_type.casefold() == entity_type.casefold()
        and ref.availability == "READY"
        for ref in metadata.owner_refs
    )


class ExplanationBlockV1(ContractModel):
    id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    type: Literal["EXPLANATION"] = "EXPLANATION"
    payload: ExplanationBlockPayloadV1
    metadata: MessageBlockMetadataV1
    interactions: tuple[InteractiveElementV1, ...] = Field(default=(), max_length=16)


class KnowledgeBlockV1(ContractModel):
    id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    type: Literal["KNOWLEDGE"] = "KNOWLEDGE"
    payload: KnowledgeBlockPayloadV1
    metadata: MessageBlockMetadataV1
    interactions: tuple[InteractiveElementV1, ...] = Field(default=(), max_length=16)

    @model_validator(mode="after")
    def require_canonical_knowledge_ref(self) -> KnowledgeBlockV1:
        if self.payload.knowledge_status == "CANONICAL_REF" and not _has_owner_ref(
            self.metadata, "SYS01", "KnowledgeUnit"
        ):
            raise ValueError("CANONICAL_REF knowledge requires a SYS01 KnowledgeUnit ref")
        return self


class EvidenceBlockV1(ContractModel):
    id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    type: Literal["EVIDENCE"] = "EVIDENCE"
    payload: EvidenceBlockPayloadV1
    metadata: MessageBlockMetadataV1
    interactions: tuple[InteractiveElementV1, ...] = Field(default=(), max_length=16)

    @model_validator(mode="after")
    def require_grounded_refs_when_ready(self) -> EvidenceBlockV1:
        if self.metadata.availability == "READY" and not (
            _has_owner_ref(self.metadata, "SYS01", "SourceSpan")
            and _has_owner_ref(self.metadata, "SYS02", "EvidenceBundle")
        ):
            raise ValueError("READY evidence requires SourceSpan and EvidenceBundle refs")
        return self


class LearningActivityBlockV1(ContractModel):
    id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    type: Literal["LEARNING_ACTIVITY"] = "LEARNING_ACTIVITY"
    payload: LearningActivityBlockPayloadV1
    metadata: MessageBlockMetadataV1
    interactions: tuple[InteractiveElementV1, ...] = Field(default=(), max_length=16)

    @model_validator(mode="after")
    def require_activity_action_refs(self) -> LearningActivityBlockV1:
        if self.metadata.availability == "READY" and not (
            _has_owner_ref(self.metadata, "SYS06", "LearningActivity")
            and _has_owner_ref(self.metadata, "SYS05", "TeachingAction")
        ):
            raise ValueError("READY learning activity requires SYS06/SYS05 refs")
        if any(item.action_type == "SUBMIT_ATTEMPT" for item in self.interactions) and not _has_owner_ref(
            self.metadata, "SYS04", "AssessmentItem"
        ):
            raise ValueError("SUBMIT_ATTEMPT requires an exact SYS04 AssessmentItem ref")
        return self


class FeedbackBlockV1(ContractModel):
    id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    type: Literal["FEEDBACK"] = "FEEDBACK"
    payload: FeedbackBlockPayloadV1
    metadata: MessageBlockMetadataV1
    interactions: tuple[InteractiveElementV1, ...] = Field(default=(), max_length=16)

    @model_validator(mode="after")
    def enforce_feedback_basis(self) -> FeedbackBlockV1:
        if self.payload.feedback_basis == "ASSESSMENT_RESULT" and not _has_owner_ref(
            self.metadata, "SYS04", "AssessmentResult"
        ):
            raise ValueError("ASSESSMENT_RESULT feedback requires an exact SYS04 AssessmentResult ref")
        if (
            self.payload.feedback_basis == "NON_ASSESSMENT_EXECUTION_FEEDBACK"
            and self.payload.correctness is not None
        ):
            raise ValueError("non-assessment feedback cannot claim correctness")
        return self


class ReviewApplyBlockV1(ContractModel):
    id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    type: Literal["REVIEW_APPLY"] = "REVIEW_APPLY"
    payload: ReviewApplyBlockPayloadV1
    metadata: MessageBlockMetadataV1
    interactions: tuple[InteractiveElementV1, ...] = Field(default=(), max_length=16)

    @model_validator(mode="after")
    def require_exact_activity(self) -> ReviewApplyBlockV1:
        if self.metadata.availability == "READY" and not _has_owner_ref(
            self.metadata, "SYS06", "LearningActivity"
        ):
            raise ValueError("READY review/apply requires an exact SYS06 LearningActivity ref")
        return self


MessageBlockV1 = Annotated[
    ExplanationBlockV1
    | KnowledgeBlockV1
    | EvidenceBlockV1
    | LearningActivityBlockV1
    | FeedbackBlockV1
    | ReviewApplyBlockV1,
    Field(discriminator="type"),
]


class LearningMessageContextV1(ContractModel):
    workspace_ref: VersionedOwnerRefV1
    learning_activity_ref: VersionedOwnerRefV1
    learning_session_ref: VersionedOwnerRefV1 | None = None
    transcript_turn_ref: VersionedOwnerRefV1
    teaching_action_ref: VersionedOwnerRefV1 | None = None
    evidence_bundle_ref: VersionedOwnerRefV1 | None = None
    attempt_ref: VersionedOwnerRefV1 | None = None
    assessment_result_ref: VersionedOwnerRefV1 | None = None

    @model_validator(mode="after")
    def require_single_workspace(self) -> LearningMessageContextV1:
        refs = (
            self.workspace_ref,
            self.learning_activity_ref,
            self.learning_session_ref,
            self.transcript_turn_ref,
            self.teaching_action_ref,
            self.evidence_bundle_ref,
            self.attempt_ref,
            self.assessment_result_ref,
        )
        workspace_ids = {ref.workspace_id for ref in refs if ref is not None}
        if workspace_ids != {self.workspace_ref.workspace_id}:
            raise ValueError("message context refs must share one exact Workspace")
        return self


class LearningMessageCompatibilityV1(ContractModel):
    source: Literal["CANONICAL", "RENDER_PAYLOAD_V1_ADAPTER", "PLAIN_TEXT_ADAPTER", "LEGACY_DIALOG"]
    fidelity: Literal["FULL", "PARTIAL"]
    reason_codes: tuple[str, ...] = Field(default=(), max_length=32)


class LearningMessageV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    id: str = Field(min_length=1, max_length=200)
    revision: int = Field(ge=1)
    conversation_id: str = Field(min_length=1, max_length=200)
    sequence: int = Field(ge=1)
    role: MessageRole
    timestamp: datetime
    content: str = Field(min_length=1, max_length=20_000)
    blocks: tuple[MessageBlockV1, ...] = Field(default=(), max_length=32)
    context: LearningMessageContextV1
    trace_references: TraceReferencesV1
    compatibility: LearningMessageCompatibilityV1

    @model_validator(mode="after")
    def enforce_message_boundary(self) -> LearningMessageV1:
        block_ids = [block.id for block in self.blocks]
        if len(block_ids) != len(set(block_ids)):
            raise ValueError("message block ids must be unique")
        if self.role == "ASSISTANT" and self.compatibility.source == "CANONICAL" and not self.blocks:
            raise ValueError("canonical assistant message requires at least one block")
        return self


class LearningConversationViewV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    conversation_id: str = Field(min_length=1, max_length=200)
    conversation_kind: Literal["LEARNING_ACTIVITY_TRANSCRIPT", "LEGACY_DIALOG_COMPAT"]
    workspace_ref: VersionedOwnerRefV1
    learning_activity_ref: VersionedOwnerRefV1
    learning_session_ref: VersionedOwnerRefV1 | None = None
    transcript_ref: VersionedOwnerRefV1
    messages: tuple[LearningMessageV1, ...]
    next_cursor: str | None = Field(default=None, max_length=500)
    view_state: Literal["READY", "EMPTY", "PARTIAL", "STALE"]
    generated_at: datetime
    correlation_id: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def require_ordered_unique_messages(self) -> LearningConversationViewV1:
        identities = [(item.id, item.revision) for item in self.messages]
        if len(identities) != len(set(identities)):
            raise ValueError("conversation cannot contain duplicate message revisions")
        if [item.sequence for item in self.messages] != sorted(
            item.sequence for item in self.messages
        ):
            raise ValueError("conversation messages must be sequence ordered")
        return self


class InteractionUserResponseV1(ContractModel):
    payload: dict[str, Any] | None = None
    accepted_response_ref: VersionedOwnerRefV1 | None = None


class LearningInteractionInvocationV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    interaction_id: UUID
    conversation_id: str = Field(min_length=1, max_length=200)
    message_id: str = Field(min_length=1, max_length=200)
    message_revision: int = Field(ge=1)
    block_id: str = Field(min_length=1, max_length=100)
    capability_id: str = Field(min_length=1, max_length=200)
    action_type: ActionType
    expected_owner_versions: tuple[VersionedOwnerRefV1, ...] = Field(default=(), max_length=32)
    user_response: InteractionUserResponseV1
    idempotency_key: str = Field(min_length=1, max_length=200)
    requested_at: datetime
    correlation_id: str = Field(min_length=1, max_length=200)


class StableErrorV1(ContractModel):
    code: str = Field(min_length=1, max_length=120)
    category: Literal[
        "validation", "business", "conflict", "not_found", "authorization", "security", "dependency", "transient", "internal"
    ]
    message: str = Field(min_length=1, max_length=1_000)
    retryable: bool
    correlation_id: str | None = Field(default=None, max_length=200)
    details: dict[str, Any] | None = None


class NextTransitionV1(ContractModel):
    kind: Literal[
        "REQUERY_OWNER",
        "AWAIT_ASSESSMENT",
        "REQUEST_NEW_TEACHING_DECISION",
        "OPEN_SOURCE",
        "NAVIGATE_ACTIVITY",
        "NONE",
    ]
    target_system: SourceSystem | None = None
    expected_ref_types: tuple[str, ...] = Field(default=(), max_length=16)


class LearningInteractionResultV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    interaction_id: UUID
    status: Literal["ACCEPTED", "SUCCEEDED", "FAILED", "CONFLICT", "UNAVAILABLE"]
    owner_receipt_ref: VersionedOwnerRefV1 | None = None
    result_refs: tuple[VersionedOwnerRefV1, ...] = Field(default=(), max_length=32)
    evaluation_result_ref: VersionedOwnerRefV1 | None = None
    next_transition: NextTransitionV1
    error: StableErrorV1 | None = None
    correlation_id: str = Field(min_length=1, max_length=200)


def _adapter_metadata(
    context: LearningMessageContextV1, *, role: str, reason: str
) -> MessageBlockMetadataV1:
    refs = tuple(
        ref
        for ref in (
            context.learning_activity_ref,
            context.transcript_turn_ref,
            context.teaching_action_ref,
            context.evidence_bundle_ref,
        )
        if ref is not None
    )
    return MessageBlockMetadataV1(
        semantic_role=role,
        provenance=ProvenanceV1(mode="NOT_APPLICABLE"),
        owner_refs=refs,
        availability="LEGACY_COMPAT",
        reason_codes=(reason,),
    )


def adapt_plain_text_message(
    *,
    message_id: str,
    conversation_id: str,
    sequence: int,
    role: MessageRole,
    timestamp: datetime,
    content: str,
    context: LearningMessageContextV1,
    trace_references: TraceReferencesV1,
) -> LearningMessageV1:
    """LCMS-092 deterministic, no-LLM plain-text compatibility adapter."""

    blocks: tuple[MessageBlockV1, ...] = ()
    if role == "ASSISTANT":
        blocks = (
            ExplanationBlockV1(
                id="content",
                payload=ExplanationBlockPayloadV1(body_markdown=content),
                metadata=_adapter_metadata(
                    context, role="legacy_plain_text", reason="PLAIN_TEXT_SEMANTICS_PARTIAL"
                ),
            ),
        )
    return LearningMessageV1(
        id=message_id,
        revision=1,
        conversation_id=conversation_id,
        sequence=sequence,
        role=role,
        timestamp=timestamp,
        content=content,
        blocks=blocks,
        context=context,
        trace_references=trace_references,
        compatibility=LearningMessageCompatibilityV1(
            source="PLAIN_TEXT_ADAPTER",
            fidelity="PARTIAL",
            reason_codes=("PLAIN_TEXT_SEMANTICS_PARTIAL",),
        ),
    )


def adapt_render_payload_message(
    *,
    message_id: str,
    conversation_id: str,
    sequence: int,
    role: MessageRole,
    timestamp: datetime,
    content: str,
    context: LearningMessageContextV1,
    trace_references: TraceReferencesV1,
    render_payload: RenderPayloadV1,
) -> LearningMessageV1:
    """LCMS-092 deterministic RenderPayloadV1 read adapter with no capabilities."""

    blocks: list[MessageBlockV1] = []
    for block in render_payload.blocks:
        metadata = _adapter_metadata(
            context, role=f"render_payload_{block.type}", reason="RENDER_PAYLOAD_OWNER_REFS_PARTIAL"
        )
        if block.type == "markdown":
            blocks.append(
                ExplanationBlockV1(
                    id=block.id,
                    payload=ExplanationBlockPayloadV1(body_markdown=block.source),
                    metadata=metadata,
                )
            )
        elif block.type == "card" and block.variant == "concept":
            blocks.append(
                KnowledgeBlockV1(
                    id=block.id,
                    payload=KnowledgeBlockPayloadV1(
                        title=block.title,
                        body_markdown=block.body_markdown,
                        knowledge_status="PRESENTATION_ONLY",
                    ),
                    metadata=metadata,
                )
            )
        elif block.type == "card" and block.variant == "question":
            blocks.append(
                LearningActivityBlockV1(
                    id=block.id,
                    payload=LearningActivityBlockPayloadV1(
                        prompt_markdown=f"### {block.title}\n\n{block.body_markdown}",
                        response_mode="NONE",
                    ),
                    metadata=metadata,
                )
            )
        elif block.type == "card" and block.variant == "feedback":
            blocks.append(
                FeedbackBlockV1(
                    id=block.id,
                    payload=FeedbackBlockPayloadV1(
                        feedback_basis="NON_ASSESSMENT_EXECUTION_FEEDBACK",
                        heading=block.title,
                        body_markdown=block.body_markdown,
                    ),
                    metadata=metadata,
                )
            )
        elif block.type == "card" and block.variant == "source":
            blocks.append(
                EvidenceBlockV1(
                    id=block.id,
                    payload=EvidenceBlockPayloadV1(
                        excerpt=block.body_markdown,
                        source_label=block.title,
                    ),
                    metadata=metadata,
                )
            )
        elif block.type == "card":
            blocks.append(
                ExplanationBlockV1(
                    id=block.id,
                    payload=ExplanationBlockPayloadV1(
                        title=block.title, body_markdown=block.body_markdown
                    ),
                    metadata=metadata,
                )
            )
        else:
            for index, item in enumerate(block.items):
                blocks.append(
                    EvidenceBlockV1(
                        id=f"{block.id}-{index + 1}",
                        payload=EvidenceBlockPayloadV1(
                            excerpt=item.label,
                            source_label=item.label,
                            citation_label=item.label,
                        ),
                        metadata=metadata,
                    )
                )
    return LearningMessageV1(
        id=message_id,
        revision=1,
        conversation_id=conversation_id,
        sequence=sequence,
        role=role,
        timestamp=timestamp,
        content=content,
        blocks=tuple(blocks),
        context=context,
        trace_references=trace_references,
        compatibility=LearningMessageCompatibilityV1(
            source="RENDER_PAYLOAD_V1_ADAPTER",
            fidelity="PARTIAL",
            reason_codes=("RENDER_PAYLOAD_OWNER_REFS_PARTIAL",),
        ),
    )

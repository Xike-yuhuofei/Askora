"""Askora 跨 bounded-context 的唯一公共合同入口。"""

from app.contracts.assessment import (
    AssessmentAttempt,
    AssessmentItemV1,
    AssistanceSnapshot,
    ResponseRevision,
)
from app.contracts.content import KnowledgeUnit, MaterialRevision, SourceChunk, SourceSpan
from app.contracts.decisions import (
    DecisionAlgorithm,
    DecisionExperiment,
    DecisionInput,
    DecisionTrace,
)
from app.contracts.events import (
    EventActor,
    EventContext,
    EventPrivacy,
    EventProvenance,
    EventTrace,
    LearningEventEnvelope,
)
from app.contracts.learning import (
    AssessmentResult,
    EvidenceBundle,
    EvidenceItem,
    LearnerEvidence,
    LearningActivity,
    LearningPlan,
    MasteryEstimate,
    ReviewSchedule,
    TeachingAction,
)
from app.contracts.planning import ConfirmedLearningGoal, ReviewDueCandidate, ReviewObservation

__all__ = [
    "AssessmentAttempt",
    "AssessmentItemV1",
    "AssistanceSnapshot",
    "ResponseRevision",
    "AssessmentResult",
    "ConfirmedLearningGoal",
    "DecisionAlgorithm",
    "DecisionExperiment",
    "DecisionInput",
    "DecisionTrace",
    "EvidenceBundle",
    "EvidenceItem",
    "EventActor",
    "EventContext",
    "EventPrivacy",
    "EventProvenance",
    "EventTrace",
    "LearnerEvidence",
    "LearningActivity",
    "LearningEventEnvelope",
    "LearningPlan",
    "KnowledgeUnit",
    "MaterialRevision",
    "MasteryEstimate",
    "ReviewSchedule",
    "ReviewDueCandidate",
    "ReviewObservation",
    "SourceChunk",
    "SourceSpan",
    "TeachingAction",
]

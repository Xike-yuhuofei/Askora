"""
数据库模型包
精简版：仅保留核心业务模型
"""

from app.models.adaptive import (
    ExperimentAssignmentRecord,
    LearningTrajectoryRecord,
    OutcomeObservationRecord,
    PolicyBundleActivationRecord,
    PolicyBundleRecord,
    TeachingActionV03Record,
    TeachingContextRecord,
    TeachingEpisodeRecord,
)
from app.models.assessment import (
    AssessmentItem,
    AssessmentResult,
    CanonicalAssessmentAttemptRecord,
    CanonicalAssessmentResultRecord,
    LearnerEvidenceRecord,
    LearnerStateRecord,
    MasteryEstimateRecord,
)
from app.models.dialog import DialogMessage, DialogSession, MessageRole
from app.models.document import DocumentChunk, ModerationStatus, ProcessingStatus, UserDocument
from app.models.identity import AuthSessionRecord, IdentityCommandReceiptRecord
from app.models.knowledge import KnowledgePoint, LearningMaterial
from app.models.ledger import (
    DecisionTraceInputRecord,
    DecisionTraceRecord,
    LearningEventRecord,
    OutboxTaskRecord,
)
from app.models.planning import (
    DiagnosticNeedRecord,
    GoalFormationInferenceRecord,
    GoalKnowledgeMappingRecord,
    GoalKnowledgeSubgraphRecord,
    LearningActivityRecord,
    LearningGoalRecord,
    LearningPlanRecord,
    ReviewObservationRecord,
    ReviewScheduleRecord,
)
from app.models.profile import UserProfile
from app.models.user import User, UserRole, UserStatus

__all__ = [
    "ExperimentAssignmentRecord",
    "LearningTrajectoryRecord",
    "OutcomeObservationRecord",
    "PolicyBundleActivationRecord",
    "PolicyBundleRecord",
    "TeachingActionV03Record",
    "TeachingContextRecord",
    "TeachingEpisodeRecord",
    "User",
    "UserRole",
    "UserStatus",
    "AuthSessionRecord",
    "IdentityCommandReceiptRecord",
    "UserProfile",
    "DialogSession",
    "DialogMessage",
    "MessageRole",
    "KnowledgePoint",
    "LearningMaterial",
    "AssessmentItem",
    "AssessmentResult",
    "CanonicalAssessmentAttemptRecord",
    "CanonicalAssessmentResultRecord",
    "LearnerEvidenceRecord",
    "LearnerStateRecord",
    "MasteryEstimateRecord",
    "LearningActivityRecord",
    "DiagnosticNeedRecord",
    "LearningGoalRecord",
    "GoalKnowledgeMappingRecord",
    "GoalKnowledgeSubgraphRecord",
    "GoalFormationInferenceRecord",
    "LearningPlanRecord",
    "ReviewObservationRecord",
    "ReviewScheduleRecord",
    "UserDocument",
    "DocumentChunk",
    "ProcessingStatus",
    "ModerationStatus",
    "LearningEventRecord",
    "DecisionTraceRecord",
    "DecisionTraceInputRecord",
    "OutboxTaskRecord",
]

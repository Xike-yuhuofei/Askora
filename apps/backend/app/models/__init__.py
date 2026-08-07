"""
数据库模型包
精简版：仅保留核心业务模型
"""

from app.models.assessment import AssessmentItem, AssessmentResult
from app.models.dialog import DialogMessage, DialogSession, MessageRole
from app.models.document import DocumentChunk, ModerationStatus, ProcessingStatus, UserDocument
from app.models.knowledge import KnowledgePoint, LearningMaterial
from app.models.ledger import (
    DecisionTraceInputRecord,
    DecisionTraceRecord,
    LearningEventRecord,
    OutboxTaskRecord,
)
from app.models.profile import UserProfile
from app.models.user import User, UserRole, UserStatus

__all__ = [
    "User",
    "UserRole",
    "UserStatus",
    "UserProfile",
    "DialogSession",
    "DialogMessage",
    "MessageRole",
    "KnowledgePoint",
    "LearningMaterial",
    "AssessmentItem",
    "AssessmentResult",
    "UserDocument",
    "DocumentChunk",
    "ProcessingStatus",
    "ModerationStatus",
    "LearningEventRecord",
    "DecisionTraceRecord",
    "DecisionTraceInputRecord",
    "OutboxTaskRecord",
]

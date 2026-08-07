"""
评估模型 - 学习效果量化
诊断性评估、形成性评估、总结性评估
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AssessmentItem(Base):
    """
    评估题目表
    用于诊断性和总结性评估
    """

    __tablename__ = "assessment_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # 关联知识点
    knowledge_point_id: Mapped[str] = mapped_column(String(36), index=True)
    subject: Mapped[str] = mapped_column(String(100), index=True)

    # 题目信息
    item_type: Mapped[str] = mapped_column(String(50))
    """
    multiple_choice: 选择题
    fill_blank: 填空题
    short_answer: 简答题
    problem_solving: 解答题
    """
    difficulty: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    grade_level: Mapped[int] = mapped_column(Integer, default=0)  # 0=不限制

    # 题目内容
    question_text: Mapped[str] = mapped_column(Text)
    options: Mapped[list] = mapped_column(JSON, default=list)  # 选择题选项
    correct_answer: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 认知目标分类（布鲁姆分类法）
    cognitive_level: Mapped[str] = mapped_column(String(50), default="understand")
    """
    remember: 记忆
    understand: 理解
    apply: 应用
    analyze: 分析
    evaluate: 评价
    create: 创造
    """

    # 常见错误模式
    common_misconceptions: Mapped[list] = mapped_column(JSON, default=list)

    # 状态
    is_active: Mapped[bool] = mapped_column(default=True)
    version: Mapped[str] = mapped_column(String(50), default="1.0")

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_assessment_kp_difficulty", "knowledge_point_id", "difficulty"),
        Index("idx_assessment_subject_grade", "subject", "grade_level"),
    )


class AssessmentResult(Base):
    """
    评估结果表
    记录用户的评估表现
    """

    __tablename__ = "assessment_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # 用户（使用假名化 ID）
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    pseudonym_id: Mapped[str] = mapped_column(String(32), index=True)

    # 评估类型
    assessment_type: Mapped[str] = mapped_column(String(50), index=True)
    """
    diagnostic: 诊断性评估（前测）
    formative: 形成性评估（学习中）
    summative: 总结性评估（后测）
    """

    # 评估范围
    subject: Mapped[str] = mapped_column(String(100), index=True)
    knowledge_point_ids: Mapped[list] = mapped_column(JSON, default=list)
    grade_level: Mapped[int] = mapped_column(Integer, default=0)

    # 结果
    total_items: Mapped[int] = mapped_column(Integer)
    correct_count: Mapped[int] = mapped_column(Integer)
    score: Mapped[float] = mapped_column(Float)  # 0-1
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)

    # 掌握度估计（BKT 模型输出）
    mastery_estimates: Mapped[dict] = mapped_column(JSON, default=dict)
    """
    示例:
    {
        "kp_algebra_transposition": {
            "p": 0.65,
            "se": 0.07,
            "n_attempts": 5
        },
        ...
    }
    """

    # 迷思概念检测
    detected_misconceptions: Mapped[list] = mapped_column(JSON, default=list)

    # 详细答题记录
    item_results: Mapped[list] = mapped_column(JSON, default=list)
    """
    示例:
    [
        {
            "item_id": "...",
            "correct": true,
            "response": "...",
            "time_spent_ms": 30000,
            "hint_used": 2
        },
        ...
    ]
    """

    # 时间戳
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("idx_result_user_type", "user_id", "assessment_type"),
        Index("idx_result_subject_completed", "subject", "completed_at"),
    )


class CanonicalAssessmentAttemptRecord(Base):
    """SYS04 canonical Attempt state；legacy assessment_results 不再承担该语义。"""

    __tablename__ = "canonical_assessment_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    item_id: Mapped[str] = mapped_column(String(36), index=True)
    item_version: Mapped[str] = mapped_column(String(50))
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CanonicalAssessmentResultRecord(Base):
    """SYS04 版本化 AssessmentResult state。"""

    __tablename__ = "canonical_assessment_result_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    attempt_id: Mapped[str] = mapped_column(String(36), index=True)
    result_version: Mapped[int] = mapped_column(Integer)
    supersedes_result_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("attempt_id", "result_version", name="uq_canonical_result_version"),
    )


class LearnerEvidenceRecord(Base):
    """SYS03 接纳后的 immutable evidence；result 一次且仅投影一次。"""

    __tablename__ = "learner_evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_result_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    knowledge_unit_id: Mapped[str] = mapped_column(String(36), index=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    reason_codes: Mapped[list] = mapped_column(JSON, default=list)
    payload: Mapped[dict] = mapped_column(JSON)
    invalidated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MasteryEstimateRecord(Base):
    """SYS03 canonical version stream；DKT 无写权限。"""

    __tablename__ = "canonical_mastery_estimate_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    knowledge_unit_id: Mapped[str] = mapped_column(String(36), index=True)
    version: Mapped[int] = mapped_column(Integer)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "user_id", "knowledge_unit_id", "version", name="uq_canonical_mastery_version"
        ),
    )

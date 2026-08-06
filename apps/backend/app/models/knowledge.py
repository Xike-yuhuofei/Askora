"""
知识点与内容模型
四层内容架构：学科 → 知识单元 → 知识点 → 学习素材
PostgreSQL 为唯一事实源，通过 Outbox 模式同步到向量库和知识图谱
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class KnowledgePoint(Base):
    """
    知识点目录表
    树形结构，PostgreSQL 为唯一事实源
    """

    __tablename__ = "knowledge_points"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # 层级结构
    subject: Mapped[str] = mapped_column(String(100), index=True)  # 学科：math/chinese/english
    unit_id: Mapped[str | None] = mapped_column(String(36), nullable=True)  # 知识单元
    parent_id: Mapped[str | None] = mapped_column(String(36), nullable=True)  # 父知识点

    # 基本信息
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    code: Mapped[str] = mapped_column(String(100), unique=True)  # 知识点编码

    # 层级与难度
    level: Mapped[int] = mapped_column(Integer, default=1)  # 层级深度
    difficulty: Mapped[int] = mapped_column(Integer, default=3)  # 难度 1-5
    grade_range: Mapped[dict] = mapped_column(JSON, default=list)  # 适用年级 [3,4,5]

    # 前置/后继关系
    prerequisites: Mapped[list] = mapped_column(JSON, default=list)  # 前置知识点 ID 列表
    successors: Mapped[list] = mapped_column(JSON, default=list)  # 后继知识点 ID 列表

    # 常见迷思概念
    misconceptions: Mapped[list] = mapped_column(JSON, default=list)
    """
    示例:
    [
        {"id": "miscon_sign_change", "name": "移项变号错误", "description": "..."},
        ...
    ]
    """

    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[str] = mapped_column(String(50), default="1.0")

    # 向量同步状态
    vector_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    graph_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 关系
    materials: Mapped[list["LearningMaterial"]] = relationship(
        "LearningMaterial", back_populates="knowledge_point"
    )

    __table_args__ = (
        Index("idx_kp_subject_level", "subject", "level"),
        Index("idx_kp_parent_id", "parent_id"),
    )


class LearningMaterial(Base):
    """
    学习素材表
    与知识点关联的各种学习资源
    """

    __tablename__ = "learning_materials"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    knowledge_point_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("knowledge_points.id"), index=True
    )

    # 素材类型
    material_type: Mapped[str] = mapped_column(String(50), index=True)
    """
    example: 例题
    explanation: 讲解
    exercise: 练习题
    video: 视频
    article: 文章
    template: 引导话术模板
    """

    # 内容
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    content_json: Mapped[dict] = mapped_column(JSON, default=dict)  # 结构化内容

    # 难度与适配
    difficulty: Mapped[int] = mapped_column(Integer, default=3)
    hint_levels: Mapped[list] = mapped_column(JSON, default=list)  # 各提示级别对应的内容

    # 模板级缓存相关
    template_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    is_cacheable: Mapped[bool] = mapped_column(Boolean, default=False)

    # 版权信息
    source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    license: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # 审核状态
    review_status: Mapped[str] = mapped_column(String(50), default="draft")
    """
    draft: 草稿
    pending_review: 待审核
    approved: 已通过
    rejected: 已拒绝
    """
    reviewed_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # 版本管理
    version: Mapped[str] = mapped_column(String(50), default="1.0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 关系
    knowledge_point: Mapped["KnowledgePoint"] = relationship(
        "KnowledgePoint", back_populates="materials"
    )

    __table_args__ = (
        Index("idx_material_kp_type", "knowledge_point_id", "material_type"),
        Index("idx_material_template_id", "template_id"),
    )


class StrategyTemplate(Base):
    """
    苏格拉底策略模板表
    三级分类体系：元认知目标 -> 认知技能 -> 学科情境
    """

    __tablename__ = "strategy_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # 三级分类
    level_1_goal: Mapped[str] = mapped_column(
        String(100), index=True
    )  # planning, monitoring, evaluation, core_guidance
    level_2_skill: Mapped[str] = mapped_column(
        String(100), index=True
    )  # goal_setting, strategy_selection, etc.
    level_3_context: Mapped[str] = mapped_column(
        String(100), index=True
    )  # algebra_equation, essay_writing, etc.

    # 基本信息
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 核心内容
    prompt_template: Mapped[str] = mapped_column(Text)
    follow_up_strategies: Mapped[list] = mapped_column(JSON, default=list)

    # 动态调整阈值
    escalation_threshold: Mapped[int] = mapped_column(Integer, default=3)  # 连续 N 轮无进展升级
    de_escalation_threshold: Mapped[int] = mapped_column(Integer, default=2)  # 连续 N 轮答对降级

    # 状态与版本
    version: Mapped[str] = mapped_column(String(50), default="1.0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_strategy_l1_l2_l3", "level_1_goal", "level_2_skill", "level_3_context"),
    )

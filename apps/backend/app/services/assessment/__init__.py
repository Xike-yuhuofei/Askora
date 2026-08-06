"""
评估服务 (Assessment Service)

支持诊断性评估、形成性评估和总结性评估三种模式。
集成 BKT 模型进行知识点掌握度估计与误区识别。
"""

from app.services.assessment.assessment_service import (
    AssessmentConfig,
    AssessmentItem,
    AssessmentResult,
    AssessmentService,
    ItemResult,
    get_assessment_service,
)

__all__ = [
    "AssessmentConfig",
    "AssessmentItem",
    "AssessmentResult",
    "AssessmentService",
    "ItemResult",
    "get_assessment_service",
]

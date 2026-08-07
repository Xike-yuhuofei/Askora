"""用户 API - 用户信息
简化版：移除了儿童账号/家长绑定/防沉迷等多用户平台功能
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.queries.profile import ProfileQueryService
from app.services.auth.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["用户"])

# 每个 profile 字段的来源标注：canonical 来自 SYS03 query projection，
# legacy 仅作为明确标注的 compatibility projection，不作为第二事实源。
_FIELD_SOURCES = {
    "skills_mastered": "canonical_sys03",
    "mastery": "canonical_sys03",
    "total_sessions": "legacy_compatibility",
    "total_learning_minutes": "legacy_compatibility",
    "streak_days": "legacy_compatibility",
    "mastery_summary": "legacy_compatibility",
    "metacognition": "legacy_compatibility",
    "affective": "legacy_compatibility",
    "favorite_subjects": "legacy_compatibility",
    "grade_level": "legacy_compatibility",
}


@router.get("/profile", summary="获取当前用户资料")
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的资料信息（canonical query boundary，EXEC-007）。"""
    model = await ProfileQueryService(db).get_profile(current_user)
    canonical = model.canonical_mastery
    compat = model.compatibility
    return {
        "user": {
            "id": model.user_id,
            "role": model.role,
            "status": model.status,
            "is_verified": model.is_verified,
        },
        "profile": {
            "total_sessions": compat.total_sessions,
            "total_learning_minutes": compat.total_learning_minutes,
            "streak_days": compat.streak_days,
            "skills_mastered": canonical.skills_mastered,
            "mastery_summary": compat.mastery_summary,
            "metacognition": compat.metacognition,
            "affective": compat.affective,
            "favorite_subjects": compat.favorite_subjects,
            "grade_level": compat.grade_level,
            "mastery": {
                "knowledge_units_assessed": canonical.knowledge_units_assessed,
                "skills_mastered": canonical.skills_mastered,
                "entries": [
                    {
                        "knowledge_unit_id": entry.knowledge_unit_id,
                        "version": entry.version,
                        "competence_probability": entry.competence_probability,
                        "confidence": entry.confidence,
                        "algorithm_id": entry.algorithm_id,
                        "algorithm_version": entry.algorithm_version,
                        "mastered": entry.mastered,
                    }
                    for entry in canonical.entries
                ],
            },
            "sources": _FIELD_SOURCES,
        },
    }

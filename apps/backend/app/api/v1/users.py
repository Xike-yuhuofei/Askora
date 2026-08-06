"""
用户 API - 用户信息
简化版：移除了儿童账号/家长绑定/防沉迷等多用户平台功能
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.services.auth.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["用户"])


@router.get("/profile", summary="获取当前用户资料")
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的资料信息"""
    from sqlalchemy import select

    from app.models.profile import UserProfile

    result = await db.execute(
        select(UserProfile).where(UserProfile.pseudonym_id == current_user.pseudonym_id)
    )
    profile = result.scalar_one_or_none()

    return {
        "user": {
            "id": current_user.id,
            "role": current_user.role.value,
            "status": current_user.status.value,
            "is_verified": current_user.is_verified,
        },
        "profile": {
            "total_sessions": profile.total_sessions if profile else 0,
            "total_learning_minutes": profile.total_learning_minutes if profile else 0,
            "streak_days": profile.streak_days if profile else 0,
            "skills_mastered": profile.skills_mastered if profile else 0,
            "mastery_summary": profile.mastery_summary if profile else {},
            "metacognition": profile.metacognition if profile else {},
            "affective": profile.affective if profile else {},
            "favorite_subjects": profile.favorite_subjects if profile else [],
            "grade_level": profile.grade_level if profile else None,
        },
    }

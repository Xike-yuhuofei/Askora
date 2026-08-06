"""
简化版授权服务
个人用户场景：仅需基本的身份验证，无需复杂的 RBAC 权限矩阵
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InsufficientPermissionsError
from app.core.logging import get_logger
from app.models.user import User

logger = get_logger(__name__)


class DataDomain(str, Enum):
    """数据域（简化版）"""

    DIALOG_RECORDS = "dialog_records"
    USER_PROFILE = "user_profile"
    KNOWLEDGE = "knowledge"
    ASSESSMENT = "assessment"
    DOCUMENTS = "documents"


class Permission(str, Enum):
    """权限类型（简化版）"""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"


class AuthorizationService:
    """简化版授权服务 - 仅支持单用户场景"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def require_permission(
        self,
        user: User,
        data_domain: Optional[DataDomain] = None,
        permission: Permission = Permission.READ,
    ) -> None:
        """
        要求用户具有指定权限（简化版）

        在个人用户场景下，只要用户已登录即可访问
        """
        if not user:
            raise InsufficientPermissionsError()

    async def check_data_ownership(
        self,
        user: User,
        resource_owner_id: str,
        resource_type: str = "",
    ) -> None:
        """
        简化版数据归属检查

        个人用户场景：只要资源属于当前用户即可
        """
        if user.id != resource_owner_id:
            raise InsufficientPermissionsError()

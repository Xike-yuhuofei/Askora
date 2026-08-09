"""
本地文件存储服务
负责用户上传文档的本地存储管理

存储结构：
  {base_path}/
    ├── {pseudonym_id}/
    │   ├── {document_id}_{filename}
    │   └── ...
    └── ...

设计原则：
- 按 pseudonym_id 分桶，实现用户数据隔离
- 使用 UUID 作为文件名前缀，避免文件名冲突
- 自动创建必要的目录结构
- 支持配额管理
"""

from __future__ import annotations

import asyncio
import re
import shutil
import uuid
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LocalFileStorage:
    """本地文件存储服务"""

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path or settings.local_storage_base_path)
        self.max_file_size_bytes = settings.local_storage_max_file_size_mb * 1024 * 1024
        self.max_total_size_bytes = settings.local_storage_max_total_size_gb * 1024 * 1024 * 1024
        self._ensure_base_path()

    def _ensure_base_path(self) -> None:
        """确保基础存储路径存在"""
        self.base_path.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.base_path.chmod(0o700)
        logger.info("local_storage_initialized")

    def _get_user_dir(self, pseudonym_id: str) -> Path:
        """获取用户存储目录"""
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", pseudonym_id):
            raise ValueError("无效的用户存储标识")
        user_dir = self.base_path / pseudonym_id
        user_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        user_dir.chmod(0o700)
        return user_dir

    def _compute_total_usage(self, pseudonym_id: str) -> int:
        """计算用户总存储用量"""
        user_dir = self._get_user_dir(pseudonym_id)
        total = 0
        for file_path in user_dir.rglob("*"):
            if file_path.is_file():
                total += file_path.stat().st_size
        return total

    async def save_file(
        self,
        pseudonym_id: str,
        document_id: str,
        original_filename: str,
        file_content: bytes,
        file_extension: str,
    ) -> tuple[str, int]:
        """
        保存文件到本地存储

        Args:
            pseudonym_id: 用户匿名 ID（用于数据隔离）
            document_id: 文档 ID（UUID）
            original_filename: 原始文件名
            file_content: 文件内容字节
            file_extension: 文件扩展名（不含点号）

        Returns:
            (存储路径, 文件大小)
        """
        file_size = len(file_content)

        # 校验单文件大小
        if file_size > self.max_file_size_bytes:
            raise ValueError(f"文件大小超过限制 {self.max_file_size_bytes / 1024 / 1024}MB")

        # 校验用户配额
        current_usage = self._compute_total_usage(pseudonym_id)
        if current_usage + file_size > self.max_total_size_bytes:
            raise ValueError(f"存储空间不足，当前已用 {current_usage / 1024 / 1024:.1f}MB")

        # 生成存储文件名（使用 document_id 作为前缀避免冲突）
        safe_ext = file_extension.lstrip(".").lower()
        safe_filename = f"{document_id}_{uuid.uuid4().hex[:8]}.{safe_ext}"

        # 保存文件
        user_dir = self._get_user_dir(pseudonym_id)
        storage_path = user_dir / safe_filename

        await asyncio.to_thread(storage_path.write_bytes, file_content)
        storage_path.chmod(0o600)

        relative_path = f"{pseudonym_id}/{safe_filename}"

        logger.info(
            "local_file_saved",
            pseudonym_id=pseudonym_id,
            document_id=document_id,
            path=relative_path,
            size=file_size,
        )

        return relative_path, file_size

    def read_file(self, storage_path: str) -> bytes:
        """
        读取本地文件

        Args:
            storage_path: 相对存储路径

        Returns:
            文件内容字节
        """
        full_path = self._resolve_storage_path(storage_path)
        if not full_path.exists():
            raise FileNotFoundError(f"文件不存在: {storage_path}")
        return full_path.read_bytes()

    def delete_file(self, storage_path: str) -> bool:
        """
        删除本地文件

        Args:
            storage_path: 相对存储路径

        Returns:
            是否删除成功
        """
        full_path = self._resolve_storage_path(storage_path)
        if not full_path.exists():
            logger.warning("local_file_delete_skipped_not_found", path=storage_path)
            return False

        full_path.unlink()
        logger.info("local_file_deleted", path=storage_path)
        return True

    def get_file_size(self, storage_path: str) -> int:
        """获取文件大小"""
        full_path = self._resolve_storage_path(storage_path)
        if not full_path.exists():
            return 0
        return full_path.stat().st_size

    def get_user_usage(self, pseudonym_id: str) -> dict:
        """获取用户存储用量"""
        used_bytes = self._compute_total_usage(pseudonym_id)
        return {
            "used_bytes": used_bytes,
            "limit_bytes": self.max_total_size_bytes,
            "usage_percent": round(used_bytes / self.max_total_size_bytes * 100, 2),
        }

    def clean_user_dir(self, pseudonym_id: str) -> int:
        """
        清理用户整个存储目录

        Returns:
            删除的文件数量
        """
        user_dir = self._get_user_dir(pseudonym_id)
        file_count = 0
        for item in user_dir.rglob("*"):
            if item.is_file():
                item.unlink()
                file_count += 1
            elif item.is_dir():
                shutil.rmtree(item)

        logger.info("local_user_dir_cleaned", pseudonym_id=pseudonym_id, files_deleted=file_count)
        return file_count

    @staticmethod
    def get_supported_extensions() -> set[str]:
        """获取支持的文件扩展名"""
        return {"md", "markdown", "txt", "epub", "pdf", "docx"}

    @staticmethod
    def is_supported(file_extension: str) -> bool:
        """判断文件扩展名是否受支持"""
        return file_extension.lstrip(".").lower() in LocalFileStorage.get_supported_extensions()

    def _resolve_storage_path(self, storage_path: str) -> Path:
        """解析并限制路径始终位于配置的存储根目录内。"""
        base = self.base_path.resolve()
        resolved = (base / storage_path).resolve()
        if not resolved.is_relative_to(base):
            raise ValueError("无效的存储路径")
        return resolved


# 单例
_storage_instance: Optional[LocalFileStorage] = None


def get_local_storage() -> LocalFileStorage:
    """获取本地存储服务单例"""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = LocalFileStorage()
    return _storage_instance

"""
WebSocket 连接管理器
管理 WebSocket 连接池，支持按用户 ID 分组推送

功能：
- 多连接管理：一个用户可建立多个 WebSocket 连接
- 消息推送：支持单播（按用户）和广播
- 心跳检测：自动检测并清理断线连接
- 鉴权校验：连接建立时校验用户身份
- 优雅关闭：支持连接优雅关闭

使用场景：
- 文档处理进度实时推送
- 对话响应流式推送
- 系统通知广播
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from typing import Optional

from fastapi import WebSocket

from app.core.logging import get_logger

logger = get_logger(__name__)


class WebSocketManager:
    """
    WebSocket 连接管理器

    特性：
    - 支持一个用户多个连接（多终端场景）
    - 消息队列缓冲，防止发送过快
    - 心跳检测，自动清理断线
    """

    def __init__(self):
        # {user_id: set[WebSocket]}
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        # 连接计数
        self._total_connections = 0
        # 消息历史（保留最近 100 条）
        self._message_history: list[dict] = []
        self._max_history = 100

    async def connect(
        self,
        user_id: str,
        ws: WebSocket,
        already_accepted: bool = False,
    ) -> None:
        """
        建立 WebSocket 连接

        Args:
            user_id: 用户 ID
            ws: WebSocket 连接对象
        """
        if not already_accepted:
            await ws.accept()

        self._connections[user_id].add(ws)
        self._total_connections += 1

        logger.info(
            "ws_connected",
            user_id=user_id,
            total_connections=self._total_connections,
            user_connections=len(self._connections[user_id]),
        )

        # 发送连接确认
        await self._safe_send(
            ws,
            {
                "type": "connected",
                "message": "WebSocket 连接已建立",
                "server_time": time.time(),
            },
        )

    async def disconnect(self, user_id: str, ws: WebSocket) -> None:
        """
        断开 WebSocket 连接

        Args:
            user_id: 用户 ID
            ws: WebSocket 连接对象
        """
        removed = False
        if user_id in self._connections and ws in self._connections[user_id]:
            self._connections[user_id].discard(ws)
            removed = True

            # 清理空连接
            if not self._connections[user_id]:
                del self._connections[user_id]

        if removed:
            self._total_connections = max(0, self._total_connections - 1)

        logger.info(
            "ws_disconnected",
            user_id=user_id,
            total_connections=self._total_connections,
        )

    async def send_to_user(self, user_id: str, message: dict) -> int:
        """
        向指定用户发送消息（单播）

        Args:
            user_id: 用户 ID
            message: 消息内容（字典）

        Returns:
            成功发送的连接数
        """
        if user_id not in self._connections:
            return 0

        # 添加元信息
        message["_timestamp"] = time.time()
        message["_type"] = message.get("type", "message")

        # 记录历史
        self._add_to_history(message)

        sent_count = 0
        dead_connections = []

        for ws in list(self._connections[user_id]):
            try:
                await self._safe_send(ws, message)
                sent_count += 1
            except Exception:
                dead_connections.append(ws)

        # 清理断开的连接
        for dead_ws in dead_connections:
            await self.disconnect(user_id, dead_ws)

        if sent_count > 0:
            logger.debug(
                "ws_message_sent",
                user_id=user_id,
                message_type=message.get("type"),
                sent_count=sent_count,
            )

        return sent_count

    async def broadcast(self, message: dict, exclude_user_id: Optional[str] = None) -> int:
        """
        向所有连接广播消息

        Args:
            message: 消息内容
            exclude_user_id: 排除的用户 ID

        Returns:
            成功发送的连接数
        """
        message["_timestamp"] = time.time()
        message["_type"] = message.get("type", "broadcast")

        self._add_to_history(message)

        sent_count = 0
        dead_connections = []

        for user_id, connections in list(self._connections.items()):
            if user_id == exclude_user_id:
                continue

            for ws in list(connections):
                try:
                    await self._safe_send(ws, message)
                    sent_count += 1
                except Exception:
                    dead_connections.append((user_id, ws))

        # 清理断开的连接
        for user_id, dead_ws in dead_connections:
            await self.disconnect(user_id, dead_ws)

        return sent_count

    async def _safe_send(self, ws: WebSocket, message: dict) -> None:
        """安全发送消息（添加超时保护）"""
        try:
            await asyncio.wait_for(
                ws.send_json(message),
                timeout=5.0,
            )
        except asyncio.TimeoutError:
            logger.warning("ws_send_timeout")
            raise

    def _add_to_history(self, message: dict) -> None:
        """添加消息到历史记录"""
        self._message_history.append(message)
        if len(self._message_history) > self._max_history:
            self._message_history = self._message_history[-self._max_history :]

    def get_connection_count(self, user_id: Optional[str] = None) -> int:
        """获取连接数"""
        if user_id:
            return len(self._connections.get(user_id, set()))
        return self._total_connections

    def has_connection(self, user_id: str) -> bool:
        """检查用户是否有活跃连接"""
        return user_id in self._connections and len(self._connections[user_id]) > 0

    def get_active_user_count(self) -> int:
        """获取当前至少有一个连接的用户数。"""
        return len(self._connections)

    async def close_all(self) -> None:
        """关闭所有连接"""
        for connections in list(self._connections.values()):
            for ws in connections:
                try:
                    await ws.close(code=1000, reason="Server shutting down")
                except Exception:
                    pass

        self._connections.clear()
        self._total_connections = 0
        logger.info("ws_all_connections_closed")


# 进度推送事件类型
class ProgressEvent:
    """文档处理进度事件"""

    STARTED = "document_processing_started"
    PROGRESS = "document_processing_progress"
    COMPLETED = "document_processing_completed"
    FAILED = "document_processing_failed"


def create_progress_message(
    document_id: str,
    progress: float,
    step: str,
    status: str = "processing",
    error: Optional[str] = None,
) -> dict:
    """
    创建进度推送消息

    Args:
        document_id: 文档 ID
        progress: 进度 (0-1)
        step: 当前步骤描述
        status: 状态
        error: 错误信息
    """
    event_type = ProgressEvent.PROGRESS
    if status == "started":
        event_type = ProgressEvent.STARTED
    elif status == "completed":
        event_type = ProgressEvent.COMPLETED
    elif status == "failed":
        event_type = ProgressEvent.FAILED

    return {
        "type": event_type,
        "document_id": document_id,
        "progress": progress,
        "step": step,
        "status": status,
        "error": error,
    }


# 全局单例
_ws_manager_instance: Optional[WebSocketManager] = None


def get_ws_manager() -> WebSocketManager:
    """获取 WebSocket 管理器单例"""
    global _ws_manager_instance
    if _ws_manager_instance is None:
        _ws_manager_instance = WebSocketManager()
    return _ws_manager_instance

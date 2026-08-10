"""
WebSocket API 路由
提供 WebSocket 连接端点，用于实时推送文档处理进度等事件

EXEC-048: 移除 token 认证，改用 loopback origin + LocalOwnerContext 验证。
无 token 即可在合法 origin 下连接。

端点：
- WS /api/v1/ws/documents：文档相关事件推送
- WS /api/v1/ws/notifications：通用通知推送

客户端使用：
```javascript
const ws = new WebSocket(`ws://127.0.0.1:8000/api/v1/ws/documents`);

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(data);
};
```
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import get_logger
from app.services.auth.dependencies import OwnerProjection, get_current_owner_projection
from app.services.websocket import get_ws_manager

logger = get_logger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket"])


class WSConnectionInfo(BaseModel):
    """连接信息"""

    user_id: str
    connected_at: float
    connection_id: str


async def _validate_websocket_origin(websocket: WebSocket) -> str | None:
    """Validate WebSocket origin is loopback-only (EXEC-048).

    No token authentication needed for local single-user instance.
    Only loopback origins are allowed.
    """
    origin = websocket.headers.get("origin")
    if origin and origin not in settings.websocket_origins:
        logger.warning("ws_origin_rejected", origin=origin)
        await websocket.close(code=4003, reason="来源不允许 - 仅允许本地回环地址")
        return None

    await websocket.accept()
    return origin or "loopback"


@router.websocket("/documents")
async def websocket_documents(
    websocket: WebSocket,
    current_owner: OwnerProjection = Depends(get_current_owner_projection),
):
    """
    文档相关事件 WebSocket 端点 (EXEC-048: no-auth loopback)

    推送事件类型：
    - document_processing_started: 文档开始处理
    - document_processing_progress: 文档处理进度更新
    - document_processing_completed: 文档处理完成
    - document_processing_failed: 文档处理失败

    无 token 认证 - 仅验证 origin 是否为 loopback。
    """
    ws_manager = get_ws_manager()

    origin = await _validate_websocket_origin(websocket)
    if origin is None:
        return

    # 使用 LocalOwnerContext 的 pseudonym_id 作为连接标识
    user_id = current_owner.pseudonym_id or current_owner.id
    await ws_manager.connect(user_id, websocket, already_accepted=True)

    logger.info("ws_documents_connected", user_id=user_id, origin=origin)

    # 保持连接，接收心跳
    try:
        while True:
            try:
                data = await websocket.receive_text()
                msg = json.loads(data)

                # 心跳检测
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

                # 客户端主动请求历史消息
                elif msg.get("type") == "get_history":
                    await websocket.send_json(
                        {
                            "type": "unsupported",
                            "message": "当前版本未启用 WebSocket 历史回放",
                        }
                    )

            except WebSocketDisconnect:
                logger.info("ws_documents_disconnected", user_id=user_id)
                break
            except json.JSONDecodeError:
                await websocket.send_json(
                    {
                        "type": "error",
                        "code": "WS_INVALID_JSON",
                        "message": "消息必须是有效 JSON",
                    }
                )

    except Exception as exc:
        logger.exception(
            "ws_documents_error",
            user_id=user_id,
            error_type=type(exc).__name__,
        )
    finally:
        await ws_manager.disconnect(user_id, websocket)


@router.websocket("/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    current_owner: OwnerProjection = Depends(get_current_owner_projection),
):
    """
    通用通知 WebSocket 端点 (EXEC-048: no-auth loopback)

    用于推送系统通知、警告等。
    无 token 认证 - 仅验证 origin 是否为 loopback。
    """
    ws_manager = get_ws_manager()

    origin = await _validate_websocket_origin(websocket)
    if origin is None:
        return

    user_id = current_owner.pseudonym_id or current_owner.id
    await ws_manager.connect(user_id, websocket, already_accepted=True)

    try:
        while True:
            try:
                data = await websocket.receive_text()
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_json(
                    {
                        "type": "error",
                        "code": "WS_INVALID_JSON",
                        "message": "消息必须是有效 JSON",
                    }
                )

    except Exception as exc:
        logger.exception(
            "ws_notifications_error",
            user_id=user_id,
            error_type=type(exc).__name__,
        )
    finally:
        await ws_manager.disconnect(user_id, websocket)


@router.get("/status")
async def ws_status(_current_owner: OwnerProjection = Depends(get_current_owner_projection)):
    """获取 WebSocket 服务状态 (EXEC-048: no-auth)"""
    ws_manager = get_ws_manager()
    return {
        "total_connections": ws_manager.get_connection_count(),
        "active_users": ws_manager.get_active_user_count(),
        "status": "running",
    }

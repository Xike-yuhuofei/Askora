"""
WebSocket API 路由
提供 WebSocket 连接端点，用于实时推送文档处理进度等事件

端点：
- WS /api/v1/ws/documents：文档相关事件推送
- WS /api/v1/ws/notifications：通用通知推送

客户端使用：
```javascript
const ws = new WebSocket(`ws://127.0.0.1:8000/api/v1/ws/documents`);
ws.onopen = () => ws.send(JSON.stringify({type: "auth", token, device_fingerprint}));

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // data.type: document_processing_progress
    // data.progress: 0.5
    // data.step: "正在解析文档..."
    console.log(data);
};
```
"""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import get_logger
from app.models.user import User
from app.services.auth.dependencies import get_current_user, get_current_user_ws
from app.services.websocket import get_ws_manager

logger = get_logger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket"])


class WSConnectionInfo(BaseModel):
    """连接信息"""

    user_id: str
    connected_at: float
    connection_id: str


async def _authenticate_websocket(websocket: WebSocket) -> User | None:
    """接受连接后在 5 秒内通过首条 JSON 消息认证，避免令牌出现在 URL。"""
    origin = websocket.headers.get("origin")
    if origin and origin not in settings.websocket_origins:
        await websocket.close(code=4003, reason="来源不允许")
        return None

    await websocket.accept()
    try:
        initial_msg = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
        message = json.loads(initial_msg)
        if message.get("type") != "auth" or not message.get("token"):
            await websocket.close(code=4001, reason="认证失败")
            return None
        return await get_current_user_ws(
            message["token"],
            device_fingerprint=message.get("device_fingerprint"),
        )
    except asyncio.TimeoutError:
        await websocket.close(code=4002, reason="认证超时")
    except WebSocketDisconnect:
        return None
    except Exception as exc:
        logger.warning("ws_auth_failed", error_type=type(exc).__name__)
        await websocket.close(code=4001, reason="认证失败")
    return None


@router.websocket("/documents")
async def websocket_documents(
    websocket: WebSocket,
):
    """
    文档相关事件 WebSocket 端点

    推送事件类型：
    - document_processing_started: 文档开始处理
    - document_processing_progress: 文档处理进度更新
    - document_processing_completed: 文档处理完成
    - document_processing_failed: 文档处理失败

    连接后 5 秒内发送首条认证消息：
    `{"type":"auth","token":"...","device_fingerprint":"..."}`
    """
    ws_manager = get_ws_manager()

    user = await _authenticate_websocket(websocket)
    if user is None:
        return

    # 建立连接
    user_id = user.pseudonym_id
    await ws_manager.connect(user_id, websocket, already_accepted=True)

    logger.info("ws_documents_connected", user_id=user_id)

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
):
    """
    通用通知 WebSocket 端点

    用于推送系统通知、警告等
    """
    ws_manager = get_ws_manager()

    user = await _authenticate_websocket(websocket)
    if user is None:
        return

    await ws_manager.connect(user.pseudonym_id, websocket, already_accepted=True)

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
            user_id=user.pseudonym_id,
            error_type=type(exc).__name__,
        )
    finally:
        await ws_manager.disconnect(user.pseudonym_id, websocket)


@router.get("/status")
async def ws_status(_current_user: User = Depends(get_current_user)):
    """获取 WebSocket 服务状态"""
    ws_manager = get_ws_manager()
    return {
        "total_connections": ws_manager.get_connection_count(),
        "active_users": ws_manager.get_active_user_count(),
        "status": "running",
    }

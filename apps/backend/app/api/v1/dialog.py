"""
对话 API - 会话管理、消息发送、流式对话
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ResourceNotFoundError
from app.core.logging import get_logger
from app.models.user import User
from app.services.auth.authorization_service import (
    AuthorizationService,
)
from app.services.auth.dependencies import get_current_user
from app.services.dialog.dialog_service import DialogService

router = APIRouter(prefix="/dialog", tags=["对话"])
logger = get_logger(__name__)


# ========== 请求/响应模型 ==========


class CreateSessionRequest(BaseModel):
    subject: str = Field("general", description="学科")
    knowledge_point_id: Optional[str] = Field(None, description="知识点 ID")


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000, description="消息内容")


class StreamQueryParams:
    """兼容 EventSource GET 方式（无自定义 header，content 走 query）"""

    def __init__(
        self,
        content: Optional[str] = Query(
            None,
            min_length=1,
            max_length=2000,
            description="消息内容（GET 方式用 query；POST 方式用 body）",
        ),
    ):
        self.content = content


def _coerce_stream_content(
    req: Optional[SendMessageRequest],
    qp: StreamQueryParams,
) -> str:
    content = (req.content if req else None) or qp.content
    if not content:
        from app.core.exceptions import ValidationInputError

        raise ValidationInputError("content 不能为空")
    return content


# ========== 路由 ==========


@router.post("/sessions", summary="创建新会话")
async def create_session(
    req: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建一个新的对话会话"""
    dialog_service = DialogService(db)
    session = await dialog_service.create_session(
        user=current_user,
        subject=req.subject,
        knowledge_point_id=req.knowledge_point_id,
    )

    return {
        "id": session.id,
        "subject": session.subject,
        "knowledge_point_id": session.knowledge_point_id,
        "knowledge_point": session.knowledge_point_id,  # 前端字段兼容
        "title": session.title,
        "status": session.status.value,
        "turn_count": session.turn_count,
        "current_hint_level": session.current_hint_level,
        "mastery_estimate": session.mastery_estimate,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
    }


@router.get("/sessions", summary="获取会话列表")
async def list_sessions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的会话列表"""
    dialog_service = DialogService(db)
    sessions = await dialog_service.get_user_sessions(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )

    return {
        "items": [
            {
                "id": s.id,
                "title": s.title,
                "subject": s.subject,
                "knowledge_point_id": s.knowledge_point_id,
                "knowledge_point": s.knowledge_point_id,  # 前端字段兼容
                "status": s.status.value,
                "turn_count": s.turn_count,
                "current_hint_level": s.current_hint_level,
                "mastery_estimate": s.mastery_estimate,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat(),
            }
            for s in sessions
        ],
        "limit": limit,
        "offset": offset,
    }


@router.get("/sessions/{session_id}", summary="获取会话详情")
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取指定会话的详情"""
    dialog_service = DialogService(db)
    session = await dialog_service.get_session(session_id)

    if not session:
        raise ResourceNotFoundError("会话")

    # 数据归属校验
    authz_service = AuthorizationService(db)
    await authz_service.check_data_ownership(
        user=current_user,
        resource_owner_id=session.user_id,
        resource_type="会话",
    )

    return {
        "id": session.id,
        "subject": session.subject,
        "topic": session.topic,
        "status": session.status.value,
        "turn_count": session.turn_count,
        "current_hint_level": session.current_hint_level,
        "current_strategy": session.current_strategy,
        "mastery_estimate": session.mastery_estimate,
        "total_tokens": session.total_tokens,
        "moderation_status": session.moderation_status,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
    }


@router.get("/sessions/{session_id}/messages", summary="获取会话消息")
async def list_messages(
    session_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取指定会话的消息列表"""
    dialog_service = DialogService(db)
    session = await dialog_service.get_session(session_id)

    if not session:
        raise ResourceNotFoundError("会话")

    # 数据归属校验
    authz_service = AuthorizationService(db)
    await authz_service.check_data_ownership(
        user=current_user,
        resource_owner_id=session.user_id,
        resource_type="会话消息",
    )

    messages = await dialog_service.get_session_messages(
        session_id=session_id,
        limit=limit,
        offset=offset,
    )

    return {
        "items": [
            {
                "id": m.id,
                "role": m.role.value,
                "content": m.content,
                "turn_number": m.turn_number,
                "strategy": m.strategy,
                "hint_level": m.hint_level,
                "intent": m.intent,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
        "limit": limit,
        "offset": offset,
    }


@router.post("/sessions/{session_id}/messages", summary="发送消息（非流式）")
async def send_message(
    session_id: str,
    req: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    发送消息并获取 AI 回复（非流式）

    对于需要实时体验的场景，请使用流式接口。
    """
    dialog_service = DialogService(db)
    session = await dialog_service.get_session(session_id)

    if not session:
        raise ResourceNotFoundError("会话")

    # 数据归属校验
    authz_service = AuthorizationService(db)
    await authz_service.check_data_ownership(
        user=current_user,
        resource_owner_id=session.user_id,
        resource_type="会话",
    )

    result = await dialog_service.send_message(
        session=session,
        user=current_user,
        content=req.content,
    )

    # 兼容前端：顶层直接暴露 content 字段（同时保留结构化 message 对象）
    if isinstance(result, dict) and "message" in result and "content" not in result:
        result["content"] = result["message"]["content"]

    return result


async def _stream_common(
    session_id: str,
    current_user: User,
    db: AsyncSession,
    content: str,
):
    """流式响应的公共处理逻辑（被 GET/POST 两个端点复用）"""
    dialog_service = DialogService(db)
    session = await dialog_service.get_session(session_id)

    if not session:
        raise ResourceNotFoundError("会话")

    # 数据归属校验
    authz_service = AuthorizationService(db)
    await authz_service.check_data_ownership(
        user=current_user,
        resource_owner_id=session.user_id,
        resource_type="会话",
    )

    async def event_generator():
        try:
            async for chunk in dialog_service.stream_message(
                session=session,
                user=current_user,
                content=content,
            ):
                import json

                chunk_type = chunk.get("type")
                if chunk_type == "content":
                    yield (
                        f"event: content\ndata: "
                        f"{json.dumps({'content': chunk['content']}, ensure_ascii=False)}\n\n"
                    )
                elif chunk_type == "delta":
                    yield (
                        f"event: delta\ndata: "
                        f"{json.dumps({'delta': chunk['delta']}, ensure_ascii=False)}\n\n"
                    )
                elif chunk_type == "violation":
                    yield (
                        f"event: violation\ndata: "
                        f"{json.dumps({'reason': chunk.get('reason'), 'partial_text': chunk.get('partial_text')}, ensure_ascii=False)}\n\n"
                    )
                elif chunk_type == "final":
                    yield (f"event: final\ndata: " f"{json.dumps(chunk, ensure_ascii=False)}\n\n")
                elif chunk_type == "done":
                    yield f"event: done\ndata: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                elif chunk_type == "error":
                    yield f"event: error\ndata: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                else:
                    # 兼容：未知类型统一当作 delta（保证不丢内容）
                    if "delta" in chunk or "content" in chunk:
                        yield (
                            f"event: delta\ndata: "
                            f"{json.dumps({'delta': chunk.get('delta') or chunk.get('content','')}, ensure_ascii=False)}\n\n"
                        )
        except Exception as exc:
            import json

            logger.exception(
                "dialog_stream_failed",
                session_id=session_id,
                error_type=type(exc).__name__,
            )
            yield (
                f"event: error\ndata: "
                f"{json.dumps({'code': 'STREAM-ERR', 'message': '流式响应失败，请重试'}, ensure_ascii=False)}\n\n"
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/sessions/{session_id}/stream", summary="发送消息（流式 SSE，GET 兼容 EventSource）")
async def stream_message_get(
    session_id: str,
    qp: StreamQueryParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    EventSource/浏览器原生 SSE 只支持 GET，content 通过 query 传递。
    推荐调用方式：POST 版本（可自定义 headers，带 Bearer token）。
    """
    content = _coerce_stream_content(None, qp)
    return await _stream_common(session_id, current_user, db, content)


@router.post("/sessions/{session_id}/stream", summary="发送消息（流式 SSE，POST 推荐）")
async def stream_message_post(
    session_id: str,
    req: Optional[SendMessageRequest] = None,
    qp: StreamQueryParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    发送消息并流式接收 AI 回复（SSE 格式）。
    优先读取 POST body 中的 content；为空时回退到 query 参数。

    返回 SSE 流，事件类型：
    - delta / content: 内容块（增量或完整片段）
    - violation: 内容违规，输出被截断
    - final / done: 最终结果
    - error: 流式异常
    """
    content = _coerce_stream_content(req, qp)
    return await _stream_common(session_id, current_user, db, content)


@router.post("/sessions/{session_id}/end", summary="结束会话")
async def end_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """主动结束对话会话"""
    dialog_service = DialogService(db)
    session = await dialog_service.get_session(session_id)

    if not session:
        raise ResourceNotFoundError("会话")

    # 数据归属校验
    authz_service = AuthorizationService(db)
    await authz_service.check_data_ownership(
        user=current_user,
        resource_owner_id=session.user_id,
        resource_type="会话",
    )

    ended_session = await dialog_service.end_session(session)

    return {
        "id": ended_session.id,
        "status": ended_session.status.value,
        "duration_seconds": ended_session.duration_seconds,
        "ended_at": ended_session.ended_at.isoformat() if ended_session.ended_at else None,
    }

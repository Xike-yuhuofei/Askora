"""
任务处理器注册
注册所有支持的任务类型处理器

当前支持的任务类型：
- document_process: 文档解析处理
- embedding: 向量生成处理
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.logging import get_logger
from app.workers.task_queue import Task, TaskQueue

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


async def document_process_handler(task: Task) -> dict:
    """
    文档处理任务处理器

    负责：读取文件 → 解析 → 审核 → 分块 → 存储
    """
    from app.core.database import get_session_factory
    from app.services.documents import get_document_service

    document_id = task.payload.get("document_id")
    if not document_id:
        raise ValueError("Missing document_id in payload")

    logger.info(
        "document_process_started",
        task_id=task.id,
        document_id=document_id,
    )

    async with get_session_factory()() as session:
        doc_service = get_document_service(session)

        # 处理文档
        document = await doc_service.process_document(document_id)

        return {
            "document_id": document_id,
            "status": document.processing_status,
            "chunk_count": document.chunk_count,
            "total_tokens": document.total_tokens,
        }


async def embedding_handler(task: Task) -> dict:
    """
    向量生成任务处理器

    负责：为文档分块生成向量嵌入
    """
    document_id = task.payload.get("document_id")
    chunk_ids = task.payload.get("chunk_ids", [])

    if not document_id:
        raise ValueError("Missing document_id in payload")

    logger.info(
        "embedding_started",
        task_id=task.id,
        document_id=document_id,
        chunks_count=len(chunk_ids),
    )

    # 向量生成逻辑（后续实现）
    # TODO: 调用 EmbeddingService 生成向量

    return {
        "document_id": document_id,
        "chunks_processed": len(chunk_ids),
        "status": "completed",
    }


# 任务处理器注册表
HANDLERS: dict[str, callable] = {
    "document_process": document_process_handler,
    "embedding": embedding_handler,
}


def register_handlers(task_queue: TaskQueue) -> None:
    """
    注册所有任务处理器到任务队列

    Args:
        task_queue: 任务队列实例
    """
    for task_type, handler in HANDLERS.items():
        task_queue.register_handler(task_type, handler)

    logger.info(f"task_handlers_registered: {list(HANDLERS.keys())}")

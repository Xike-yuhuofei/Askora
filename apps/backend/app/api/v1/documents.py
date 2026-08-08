"""
文档管理 API 路由
提供文档上传、管理、删除、检索等接口

权限要求：
- 所有接口需要认证
- 用户只能访问自己的文档
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, ConfigDict
from pydantic import Field as PydanticField
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.document import ProcessingStatus
from app.models.user import User
from app.services.auth.dependencies import get_current_user
from app.services.documents import get_document_service, get_rag_service

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["文档管理"])


# ==================== 请求/响应模型 ====================


class DocumentResponse(BaseModel):
    """文档响应"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    original_filename: str
    file_extension: str
    file_size_bytes: int
    storage_path: str
    processing_status: str
    moderation_status: str
    subject: Optional[str] = None
    knowledge_point_id: Optional[str] = None
    chunk_count: int
    total_tokens: int
    created_at: datetime
    updated_at: datetime
    last_accessed_at: Optional[datetime] = None
    access_count: int


class DocumentListResponse(BaseModel):
    """文档列表响应"""

    total: int
    items: list[DocumentResponse]
    page: int
    page_size: int


class DocumentStatusResponse(BaseModel):
    """文档处理状态响应"""

    document_id: str
    processing_status: str
    progress: float  # 0-100
    current_step: str
    error: Optional[str] = None


class StorageInfoResponse(BaseModel):
    """存储信息响应"""

    used_bytes: int
    limit_bytes: int
    usage_percent: float
    document_count: int
    total_document_size: int


class UploadResponse(BaseModel):
    """上传响应"""

    document_id: str
    status: str
    message: str


class RAGQueryRequest(BaseModel):
    """RAG 查询请求"""

    query: str = PydanticField(..., min_length=1, max_length=4000)
    max_chunks: int = PydanticField(5, ge=1, le=20)
    subject: Optional[str] = PydanticField(None, max_length=100)


class RAGQueryResponse(BaseModel):
    """RAG 查询响应"""

    chunks_found: int
    total_tokens: int
    used_documents: list[str]
    context_text: str
    chunks: list[dict]


# ==================== API 端点 ====================


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    subject: Optional[str] = Form(None),
    knowledge_point_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    上传文档

    - 支持格式：.md, .txt, .epub, .pdf, .docx
    - 单文件大小限制：50MB
    - 上传后立即返回，文档在后台异步处理
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    file_content = await _read_upload_limited(file)

    if len(file_content) == 0:
        raise HTTPException(status_code=400, detail="文件内容为空")

    # 校验文件大小
    try:
        doc_service = get_document_service(db)
        document = await doc_service.upload_document(
            pseudonym_id=current_user.pseudonym_id,
            original_filename=file.filename,
            file_content=file_content,
            subject=subject,
            knowledge_point_id=knowledge_point_id,
        )

        return UploadResponse(
            document_id=document.id,
            status=document.processing_status,
            message="文档已接收，正在后台处理",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("document_upload_failed", error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="上传失败，请稍后重试")


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    status: Optional[str] = Query(None, description="处理状态筛选"),
    subject: Optional[str] = Query(None, description="学科筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户文档列表

    支持按状态、学科筛选，支持分页
    """
    doc_service = get_document_service(db)
    documents, total = await doc_service.list_user_documents(
        pseudonym_id=current_user.pseudonym_id,
        status=status,
        subject=subject,
        page=page,
        page_size=page_size,
    )

    return DocumentListResponse(
        total=total,
        items=[DocumentResponse.model_validate(doc) for doc in documents],
        page=page,
        page_size=page_size,
    )


@router.get("/storage", response_model=StorageInfoResponse)
async def get_storage_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户存储使用信息"""
    doc_service = get_document_service(db)
    info = await doc_service.get_user_storage_info(current_user.pseudonym_id)
    return StorageInfoResponse(**info)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个文档详情"""
    doc_service = get_document_service(db)
    document = await doc_service.get_document(document_id)

    if document is None:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 权限校验
    if document.pseudonym_id != current_user.pseudonym_id:
        raise HTTPException(status_code=403, detail="无权访问此文档")

    return DocumentResponse.model_validate(document)


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取文档处理状态"""
    doc_service = get_document_service(db)
    document = await doc_service.get_document(document_id)

    if document is None:
        raise HTTPException(status_code=404, detail="文档不存在")

    if document.pseudonym_id != current_user.pseudonym_id:
        raise HTTPException(status_code=403, detail="无权访问此文档")

    # 估算进度
    progress_map = {
        ProcessingStatus.PENDING: 10,
        ProcessingStatus.PROCESSING: 50,
        ProcessingStatus.COMPLETED: 100,
        ProcessingStatus.FAILED: 100,
        ProcessingStatus.REJECTED: 100,
        ProcessingStatus.QUARANTINED: 100,
    }

    step_map = {
        ProcessingStatus.PENDING: "等待处理",
        ProcessingStatus.PROCESSING: "正在解析与向量化...",
        ProcessingStatus.COMPLETED: "处理完成",
        ProcessingStatus.FAILED: "处理失败",
        ProcessingStatus.REJECTED: "内容审核未通过",
        ProcessingStatus.QUARANTINED: "资料已安全隔离",
    }

    return DocumentStatusResponse(
        document_id=document_id,
        processing_status=document.processing_status,
        progress=progress_map.get(document.processing_status, 0),
        current_step=step_map.get(document.processing_status, "未知状态"),
        error=document.processing_error,
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除文档"""
    doc_service = get_document_service(db)
    success = await doc_service.delete_document(
        document_id=document_id,
        pseudonym_id=current_user.pseudonym_id,
    )

    if not success:
        raise HTTPException(status_code=404, detail="文档不存在")

    return {"success": True, "message": "文档已删除"}


@router.post("/rag/query", response_model=RAGQueryResponse)
async def query_rag(
    request: RAGQueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    RAG 检索查询

    从用户知识库中检索与查询相关的文档片段
    """
    rag_service = get_rag_service(db)
    result = await rag_service.retrieve_context(
        pseudonym_id=current_user.pseudonym_id,
        query=request.query,
        max_chunks=request.max_chunks,
        subject=request.subject,
    )

    return RAGQueryResponse(
        chunks_found=result.total_chunks_found,
        total_tokens=result.total_tokens,
        used_documents=result.used_documents,
        context_text=result.context_text,
        chunks=[
            {
                "chunk_id": c.chunk_id,
                "document_id": c.document_id,
                "document_title": c.document_title,
                "content": c.content,
                "relevance_score": c.relevance_score,
                "source_file": c.source_file,
            }
            for c in result.chunks
        ],
    )


async def _read_upload_limited(file: UploadFile) -> bytes:
    """分块读取上传内容，在超过配置上限时立即停止。"""
    max_size = settings.local_storage_max_file_size_mb * 1024 * 1024
    content = bytearray()
    while chunk := await file.read(1024 * 1024):
        content.extend(chunk)
        if len(content) > max_size:
            raise HTTPException(
                status_code=413,
                detail=("文件大小超过限制（最大 " f"{settings.local_storage_max_file_size_mb}MB）"),
            )
    return bytes(content)

"""
RAG 检索服务 - 文档向量检索
负责从用户知识库中检索相关文档片段，注入到对话上下文中

检索策略：
1. 关键词匹配：基于 jieba 分词 + TF-IDF 评分
2. 语义检索：调用 Embedding API 进行向量相似度匹配（后续升级）
3. 结果过滤：仅返回审核通过的可用文档
4. 上下文注入：将检索结果格式化后注入 SharedContext

MVP 阶段：
- 使用关键词匹配 + TF-IDF 评分作为简化版检索
- 后续可接入 pgvector / Milvus 等向量数据库
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.learning import TeachingAction
from app.core.logging import get_logger
from app.domains.content_knowledge import CONTENT_RECORD_KEY, SEGMENTATION_VERSION
from app.domains.retrieval import (
    EvidenceBundleBuildResult,
    HybridEvidenceRetriever,
    RetrievalCandidate,
)
from app.models.document import (
    DocumentChunk,
    ModerationStatus,
    ProcessingStatus,
    UserDocument,
)

# jieba 分词服务（延迟导入，降级支持）
try:
    from app.services.documents.tokenizer import get_tokenizer

    _tokenizer_available = True
except ImportError:
    _tokenizer_available = False

logger = get_logger(__name__)


@dataclass
class RetrievedChunk:
    """检索到的文档分块"""

    chunk_id: str
    document_id: str
    document_title: str
    content: str
    relevance_score: float
    metadata: dict
    source_file: str


@dataclass
class RAGRetrievalResult:
    """RAG 检索结果"""

    chunks: list[RetrievedChunk]
    total_chunks_found: int
    total_tokens: int
    used_documents: list[str]

    @property
    def context_text(self) -> str:
        """将检索结果格式化为上下文文本"""
        if not self.chunks:
            return ""

        parts = ["[参考资料]"]
        for i, chunk in enumerate(self.chunks, 1):
            parts.append(
                f"{i}. 《{chunk.document_title}》(相关性: {chunk.relevance_score:.2f})\n"
                f"{chunk.content}"
            )
        return "\n\n".join(parts)


class RAGService:
    """
    RAG 检索服务

    MVP 实现：基于关键词的 TF-IDF 简化检索
    后续可升级为向量相似度检索
    """

    def __init__(
        self,
        db: AsyncSession,
        retriever: HybridEvidenceRetriever | None = None,
    ):
        self.db = db
        self.retriever = retriever or HybridEvidenceRetriever()
        self.max_context_chunks = 5  # 最多返回的分块数量
        self.min_score_threshold = 0.3  # 最低相关性分数

    async def build_evidence_bundle(
        self,
        *,
        pseudonym_id: str,
        query: str,
        teaching_action: TeachingAction,
        request_id: UUID | None = None,
        source_scope: dict[str, object] | None = None,
        max_chunks: int | None = None,
        learner_visible: bool = True,
    ) -> EvidenceBundleBuildResult:
        """Build the SYS02 structured decision result (SYS02-001/002)."""
        doc_ids = await self._get_available_document_ids(pseudonym_id=pseudonym_id)
        scope = source_scope or {"document_ids": doc_ids, "pseudonym_id": pseudonym_id}
        if not doc_ids:
            return self.retriever.build_evidence_bundle(
                request_id=request_id or uuid4(),
                teaching_action=teaching_action,
                query=query,
                candidates=[],
                source_scope=scope,
                index_versions={"segmentation": SEGMENTATION_VERSION, "content": "none"},
                learner_visible=learner_visible,
                max_items=max_chunks or self.max_context_chunks,
            )

        rows = (
            await self.db.execute(
                select(DocumentChunk, UserDocument)
                .join(UserDocument, DocumentChunk.document_id == UserDocument.id)
                .where(DocumentChunk.document_id.in_(doc_ids))
            )
        ).all()
        candidates: list[RetrievalCandidate] = []
        revision_versions: set[str] = set()
        for chunk, document in rows:
            metadata = chunk.chunk_metadata or {}
            revision_id = self._parse_uuid(metadata.get("revision_id"))
            document_uuid = self._parse_uuid(document.id)
            if revision_id is None or document_uuid is None:
                continue
            revision_versions.add(str(revision_id))
            valid_span_ids = self._validated_span_ids(document, metadata)
            candidates.append(
                RetrievalCandidate(
                    chunk_id=UUID(chunk.id),
                    document_id=document_uuid,
                    revision_id=revision_id,
                    source_span_ids=tuple(valid_span_ids),
                    knowledge_unit_ids=tuple(
                        value
                        for raw in metadata.get("knowledge_unit_ids", [])
                        if (value := self._parse_uuid(raw)) is not None
                    ),
                    content=chunk.content,
                    pedagogical_role=str(metadata.get("pedagogical_role", "context")),
                    exposure_level=int(metadata.get("exposure_level", 0)),
                    allowed_use=str(metadata.get("allowed_use", "learner_visible")),
                )
            )
        return self.retriever.build_evidence_bundle(
            request_id=request_id or uuid4(),
            teaching_action=teaching_action,
            query=query,
            candidates=candidates,
            source_scope=scope,
            index_versions={
                "segmentation": SEGMENTATION_VERSION,
                "content_revisions": ",".join(sorted(revision_versions)),
                "fusion": "rrf-v1",
            },
            learner_visible=learner_visible,
            max_items=max_chunks or self.max_context_chunks,
        )

    @classmethod
    def _validated_span_ids(cls, document: UserDocument, metadata: dict) -> list[UUID]:
        record = (document.moderation_details or {}).get(CONTENT_RECORD_KEY, {})
        revision_id = metadata.get("revision_id")
        revision = next(
            (
                item
                for item in record.get("revisions", [])
                if item.get("revision_id") == revision_id
            ),
            None,
        )
        if revision is None:
            return []
        canonical_ids = {item.get("span_id") for item in revision.get("source_spans", [])}
        return [
            value
            for raw in metadata.get("source_span_ids", [])
            if raw in canonical_ids and (value := cls._parse_uuid(raw)) is not None
        ]

    @staticmethod
    def _parse_uuid(value: object) -> UUID | None:
        try:
            return UUID(str(value))
        except (TypeError, ValueError, AttributeError):
            return None

    async def retrieve_context(
        self,
        pseudonym_id: str,
        query: str,
        max_chunks: Optional[int] = None,
        subject: Optional[str] = None,
    ) -> RAGRetrievalResult:
        """
        从用户知识库检索相关上下文

        Args:
            pseudonym_id: 用户匿名 ID
            query: 查询文本（用户的问题）
            max_chunks: 最大返回分块数
            subject: 学科过滤

        Returns:
            RAGRetrievalResult 检索结果
        """
        if max_chunks is None:
            max_chunks = self.max_context_chunks

        # 1. 获取用户可用文档 ID 列表
        doc_ids = await self._get_available_document_ids(
            pseudonym_id=pseudonym_id,
            subject=subject,
        )

        if not doc_ids:
            return RAGRetrievalResult(
                chunks=[],
                total_chunks_found=0,
                total_tokens=0,
                used_documents=[],
            )

        # 2. 提取查询关键词
        keywords = self._extract_keywords(query)

        if not keywords:
            return RAGRetrievalResult(
                chunks=[],
                total_chunks_found=0,
                total_tokens=0,
                used_documents=[],
            )

        # 3. 检索相关分块
        chunks = await self._search_chunks(
            doc_ids=doc_ids,
            keywords=keywords,
            max_chunks=max_chunks,
        )

        # 4. 构建结果
        used_docs = list(set(c.document_id for c in chunks))
        total_tokens = sum(chunk.content.count(" ") + len(chunk.content) / 2 for chunk in chunks)

        result = RAGRetrievalResult(
            chunks=chunks,
            total_chunks_found=len(chunks),
            total_tokens=int(total_tokens),
            used_documents=used_docs,
        )

        if chunks:
            logger.info(
                "rag_retrieval_success",
                pseudonym_id=pseudonym_id,
                query_len=len(query),
                chunks_found=len(chunks),
                docs_used=len(used_docs),
            )

        return result

    async def _get_available_document_ids(
        self,
        pseudonym_id: str,
        subject: Optional[str] = None,
    ) -> list[str]:
        """获取用户可用的文档 ID 列表"""
        query = select(UserDocument.id).where(
            UserDocument.pseudonym_id == pseudonym_id,
            UserDocument.processing_status == ProcessingStatus.COMPLETED,
            UserDocument.moderation_status == ModerationStatus.APPROVED,
            UserDocument.is_deleted.is_(False),
        )

        if subject:
            query = query.where(UserDocument.subject == subject)

        result = await self.db.execute(query)
        return [row[0] for row in result.all()]

    async def _search_chunks(
        self,
        doc_ids: list[str],
        keywords: list[str],
        max_chunks: int,
    ) -> list[RetrievedChunk]:
        """
        搜索文档分块（基于关键词匹配 + 评分）

        算法：TF-IDF 简化版
        - 词频（TF）：关键词在分块中出现的次数
        - 逆文档频率（IDF）：关键词在所有分块中的稀有度
        """
        # 构建搜索条件
        conditions = []
        for keyword in keywords:
            conditions.append(DocumentChunk.content.ilike(f"%{keyword}%"))

        if not conditions:
            return []

        # 查询匹配的分块
        query = (
            select(DocumentChunk, UserDocument)
            .join(UserDocument, DocumentChunk.document_id == UserDocument.id)
            .where(
                DocumentChunk.document_id.in_(doc_ids),
                or_(*conditions),
            )
            .order_by(DocumentChunk.chunk_index)
            .limit(max_chunks * 3)  # 多取一些用于排序筛选
        )

        result = await self.db.execute(query)
        rows = result.all()

        if not rows:
            return []

        # 计算每个分块的相关性分数
        scored_chunks = []
        for chunk, doc in rows:
            score = self._calculate_relevance_score(chunk.content, keywords)
            if score >= self.min_score_threshold:
                scored_chunks.append(
                    RetrievedChunk(
                        chunk_id=chunk.id,
                        document_id=chunk.document_id,
                        document_title=doc.original_filename,
                        content=chunk.content,
                        relevance_score=score,
                        metadata=chunk.chunk_metadata or {},
                        source_file=doc.original_filename,
                    )
                )

        # 按相关性分数排序，取 Top-N
        scored_chunks.sort(key=lambda x: x.relevance_score, reverse=True)
        return scored_chunks[:max_chunks]

    def _calculate_relevance_score(self, content: str, keywords: list[str]) -> float:
        """
        计算内容与关键词的相关性分数

        简化版 TF-IDF：
        - 完全匹配（整个关键词出现）：+0.3
        - 部分匹配（子串匹配）：+0.1
        - 位置加权：靠前的匹配加分
        """
        score = 0.0
        content_lower = content.lower()

        for keyword in keywords:
            keyword_lower = keyword.lower()

            # 完全匹配
            count = content_lower.count(keyword_lower)
            if count > 0:
                score += 0.3 * min(count, 3)  # 最多计 3 次
                # 位置加权：首次出现位置越靠前分越高
                first_pos = content_lower.find(keyword_lower)
                if first_pos < len(content) * 0.2:
                    score += 0.1

        # 归一化到 0-1
        return min(1.0, score / max(len(keywords) * 0.6, 1))

    def _extract_keywords(self, text: str) -> list[str]:
        """
        从查询文本中提取关键词（使用 jieba 分词）

        降级策略：
        - jieba 可用 → 使用专业分词 + 停用词过滤
        - jieba 不可用 → 回退到简单正则提取
        """
        if _tokenizer_available:
            return self._extract_keywords_with_jieba(text)
        else:
            logger.warning("jieba_not_available_using_fallback")
            return self._extract_keywords_fallback(text)

    def _extract_keywords_with_jieba(self, text: str) -> list[str]:
        """使用 jieba 分词提取关键词"""
        tokenizer = get_tokenizer()

        # 使用关键词提取接口（带词性权重）
        keywords_with_weights = tokenizer.extract_keywords(
            text,
            top_k=15,
            with_weight=True,
        )

        # 额外提取数字（年份、编号等）
        keywords = {kw for kw, _ in keywords_with_weights}
        numbers = re.findall(r"\d{2,}", text)
        for num in numbers:
            keywords.add(num)

        return list(keywords)

    def _extract_keywords_fallback(self, text: str) -> list[str]:
        """降级方案：简单正则提取"""
        cn_stopwords = {
            "的",
            "了",
            "在",
            "是",
            "我",
            "有",
            "和",
            "就",
            "不",
            "人",
            "都",
            "一",
            "一个",
            "上",
            "也",
            "很",
            "到",
            "说",
            "要",
            "去",
            "你",
            "会",
            "着",
            "没有",
            "看",
            "好",
            "自己",
            "这",
            "什么",
            "怎么",
            "如何",
            "请",
            "帮",
            "能",
            "可以",
            "吗",
            "呢",
        }

        en_stopwords = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "do",
            "does",
            "did",
            "have",
            "has",
            "had",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "shall",
            "can",
            "need",
            "dare",
            "ought",
            "used",
            "to",
            "of",
            "in",
            "for",
            "on",
            "with",
            "at",
            "by",
            "from",
            "as",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "out",
            "off",
            "over",
            "under",
            "again",
            "further",
            "then",
            "once",
            "here",
            "there",
            "when",
            "where",
            "why",
            "how",
            "all",
            "both",
            "each",
            "few",
            "more",
            "most",
            "other",
            "some",
            "such",
            "no",
            "nor",
            "not",
            "only",
            "own",
            "same",
            "so",
            "than",
            "too",
            "very",
            "just",
            "because",
            "but",
            "and",
            "or",
            "if",
            "while",
            "although",
            "though",
        }

        keywords = set()

        cn_segments = re.findall(r"[\u4e00-\u9fff]{2,}", text)
        for seg in cn_segments:
            cleaned = "".join(c for c in seg if c not in cn_stopwords)
            if cleaned:
                keywords.add(cleaned)

        en_words = re.findall(r"[a-zA-Z]{2,}", text.lower())
        for word in en_words:
            if word not in en_stopwords:
                keywords.add(word)

        numbers = re.findall(r"\d+", text)
        for num in numbers:
            if len(num) >= 2:
                keywords.add(num)

        return list(keywords)


def get_rag_service(db: AsyncSession) -> RAGService:
    """获取 RAG 服务实例"""
    return RAGService(db)

"""
向量嵌入服务
负责文本向量化和相似度检索

功能：
- 文本嵌入：调用 Embedding API 生成向量
- 批量嵌入：批量处理多个文本
- 相似度检索：基于向量余弦相似度检索
- 缓存优化：缓存常用嵌入结果

降级策略：
- Embedding API 可用 → 使用语义检索
- Embedding API 不可用 → 回退到关键词检索
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class EmbeddingResult:
    """嵌入结果"""

    text: str
    vector: list[float]
    model: str
    dimension: int
    cached: bool = False
    created_at: float = field(default_factory=time.monotonic)


@dataclass
class SearchResult:
    """检索结果"""

    content: str
    score: float
    metadata: dict


class EmbeddingService:
    """
    向量嵌入服务

    支持：
    - 阿里通义 Embedding（默认）
    - 兼容其他 Embedding API
    - 本地缓存（LRU + TTL）
    """

    def __init__(self):
        self._api_key = getattr(settings, "embedding_api_key", "")
        self._api_base = getattr(settings, "embedding_api_base", "https://dashscope.aliyuncs.com")
        self._model = getattr(settings, "embedding_model", "text-embedding-v2")
        self._dimension = getattr(settings, "embedding_dimension", 1536)

        # 本地缓存
        self._cache: dict[str, EmbeddingResult] = {}
        self._cache_max_size = 10000
        self._cache_ttl = 3600  # 缓存有效期（秒）

        # 可用状态
        self._available = bool(self._api_key)
        if not self._available:
            logger.warning("embedding_service_no_api_key_will_use_fallback")

    async def embed_text(self, text: str) -> Optional[list[float]]:
        """
        将文本转换为向量

        Args:
            text: 输入文本

        Returns:
            向量列表或 None（不可用时）
        """
        if not self._available:
            return None

        # 检查缓存
        cache_key = self._get_cache_key(text)
        cached = self._cache.get(cache_key)
        if cached and not self._is_cache_expired(cached):
            cached.cached = True
            return cached.vector

        try:
            vector = await self._call_embedding_api(text)

            # 写入缓存
            result = EmbeddingResult(
                text=text,
                vector=vector,
                model=self._model,
                dimension=self._dimension,
            )
            self._set_cache(cache_key, result)

            return vector

        except Exception as e:
            logger.exception("embedding_failed", error_type=type(e).__name__)
            return None

    async def embed_batch(
        self,
        texts: list[str],
        batch_size: int = 10,
    ) -> list[Optional[list[float]]]:
        """
        批量文本嵌入

        Args:
            texts: 文本列表
            batch_size: 批次大小

        Returns:
            向量列表（失败时对应位置为 None）
        """
        if not self._available:
            return [None] * len(texts)

        results: list[list[float] | None] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]

            try:
                batch_vectors = await self._call_embedding_api_batch(batch)
                results.extend(batch_vectors)
            except Exception as e:
                logger.exception("embedding_batch_failed", error_type=type(e).__name__)
                results.extend([None] * len(batch))

        return results

    async def compute_similarity(
        self,
        vector_a: list[float],
        vector_b: list[float],
    ) -> float:
        """
        计算两个向量的余弦相似度

        Args:
            vector_a: 向量 A
            vector_b: 向量 B

        Returns:
            相似度 (-1 到 1)
        """
        if not vector_a or not vector_b:
            return 0.0

        if len(vector_a) != len(vector_b):
            return 0.0

        # 计算点积和范数
        dot_product = sum(a * b for a, b in zip(vector_a, vector_b, strict=True))
        norm_a = sum(a * a for a in vector_a) ** 0.5
        norm_b = sum(b * b for b in vector_b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    async def search_similar(
        self,
        query_vector: list[float],
        candidates: list[dict],
        top_k: int = 5,
        min_score: float = 0.3,
    ) -> list[SearchResult]:
        """
        从候选列表中检索最相似的文本

        Args:
            query_vector: 查询向量
            candidates: 候选列表 [{"content": str, "vector": list[float], "metadata": dict}]
            top_k: 返回数量
            min_score: 最低分数

        Returns:
            检索结果列表
        """
        scored_results = []

        for candidate in candidates:
            candidate_vector = candidate.get("vector")
            if not candidate_vector:
                continue

            score = await self.compute_similarity(query_vector, candidate_vector)

            if score >= min_score:
                scored_results.append(
                    SearchResult(
                        content=candidate["content"],
                        score=score,
                        metadata=candidate.get("metadata", {}),
                    )
                )

        # 排序取 Top-K
        scored_results.sort(key=lambda x: x.score, reverse=True)
        return scored_results[:top_k]

    async def _call_embedding_api(self, text: str) -> list[float]:
        """调用 Embedding API"""
        url = f"{self._api_base}/compatible-mode/v1/embeddings"

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self._model,
            "input": text,
            "dimensions": self._dimension,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()

            data = response.json()
            return data["data"][0]["embedding"]

    async def _call_embedding_api_batch(self, texts: list[str]) -> list[list[float]]:
        """批量调用 Embedding API"""
        url = f"{self._api_base}/compatible-mode/v1/embeddings"

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self._model,
            "input": texts,
            "dimensions": self._dimension,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()

            data = response.json()
            # 按索引排序返回结果
            embeddings = sorted(data["data"], key=lambda x: x["index"])
            return [item["embedding"] for item in embeddings]

    def _get_cache_key(self, text: str) -> str:
        """获取缓存键"""
        return hashlib.md5(text.encode()).hexdigest()

    def _is_cache_expired(self, result: EmbeddingResult) -> bool:
        """检查缓存是否过期"""
        return time.monotonic() - result.created_at >= self._cache_ttl

    def _set_cache(self, key: str, result: EmbeddingResult) -> None:
        """设置缓存"""
        if len(self._cache) >= self._cache_max_size:
            # 淘汰最早的缓存
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]

        self._cache[key] = result

    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()
        logger.info("embedding_cache_cleared")

    @property
    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self._available


# 全局实例
_embedding_service_instance: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """获取向量服务实例"""
    global _embedding_service_instance
    if _embedding_service_instance is None:
        _embedding_service_instance = EmbeddingService()
    return _embedding_service_instance

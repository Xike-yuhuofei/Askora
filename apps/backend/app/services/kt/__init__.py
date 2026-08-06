"""
知识追踪服务 (Knowledge Tracing)
基于 BKT (Bayesian Knowledge Tracing) 模型的简化实现
"""

from app.services.kt.knowledge_tracing_service import KnowledgeTracingService, get_kt_service

__all__ = [
    "KnowledgeTracingService",
    "get_kt_service",
]

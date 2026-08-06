"""
知识图谱服务 (Knowledge Graph)
管理知识点之间的前置依赖关系和学习路径规划
"""

from app.services.knowledge_graph.kg_service import (
    KGEdge,
    KGNode,
    KnowledgeGraph,
    get_knowledge_graph,
    get_math_graph,
    get_physics_graph,
)

__all__ = [
    "KGNode",
    "KGEdge",
    "KnowledgeGraph",
    "get_math_graph",
    "get_physics_graph",
    "get_knowledge_graph",
]

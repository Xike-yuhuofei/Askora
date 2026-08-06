"""
知识图谱服务

管理知识点之间的前置依赖关系，为知识追踪、练习推荐和学习路径规划提供基础支撑。

核心功能：
- 知识点节点管理（KGNode）
- 前置依赖关系建模（KGEdge）
- 学习路径规划（最短路径搜索）
- 学科子图过滤
- 个性化学习路径推荐

存储方案：基于内存的 dict 存储，预留 Neo4j 持久化接口
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class KGNode:
    """知识图谱节点 - 知识点"""

    kp_id: str
    name: str
    subject: str
    difficulty: float = 0.5  # 0.0~1.0 难度等级
    cognitive_level: str = (
        "knowledge"  # knowledge/comprehension/application/analysis/synthesis/evaluation
    )
    description: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class KGEdge:
    """知识图谱边 - 知识点关系"""

    from_id: str
    to_id: str
    relation_type: str = "prerequisite"  # prerequisite/depends_on/related
    weight: float = 1.0


class KnowledgeGraph:
    """
    知识图谱核心类

    使用邻接表存储节点和边，支持：
    - 知识点增删改查
    - 前置依赖关系管理
    - 学习路径规划（BFS 最短路径）
    - 学科子图过滤
    """

    def __init__(self):
        self._nodes: dict[str, KGNode] = {}
        self._edges: list[KGEdge] = []
        self._adj_out: dict[str, list[str]] = {}  # from -> [to] 依赖方向
        self._adj_in: dict[str, list[str]] = {}  # to -> [from] 被依赖方向

    # ------------------------------------------------------------------
    # 节点管理
    # ------------------------------------------------------------------

    def add_node(
        self,
        kp_id: str,
        name: str,
        subject: str,
        difficulty: float = 0.5,
        cognitive_level: str = "knowledge",
        description: str = "",
        tags: Optional[list[str]] = None,
    ) -> KGNode:
        """添加知识点节点"""
        node = KGNode(
            kp_id=kp_id,
            name=name,
            subject=subject,
            difficulty=difficulty,
            cognitive_level=cognitive_level,
            description=description,
            tags=tags or [],
        )
        self._nodes[kp_id] = node
        if kp_id not in self._adj_out:
            self._adj_out[kp_id] = []
        if kp_id not in self._adj_in:
            self._adj_in[kp_id] = []
        logger.debug(f"KG node added: {kp_id} ({name})")
        return node

    def get_node(self, kp_id: str) -> Optional[KGNode]:
        """获取知识点节点"""
        return self._nodes.get(kp_id)

    def remove_node(self, kp_id: str) -> bool:
        """删除知识点节点（同时移除关联的边）"""
        if kp_id not in self._nodes:
            return False
        self._nodes.pop(kp_id)
        self._adj_out.pop(kp_id, None)
        self._adj_in.pop(kp_id, None)
        self._edges = [e for e in self._edges if e.from_id != kp_id and e.to_id != kp_id]
        for targets in self._adj_out.values():
            if kp_id in targets:
                targets.remove(kp_id)
        for sources in self._adj_in.values():
            if kp_id in sources:
                sources.remove(kp_id)
        logger.debug(f"KG node removed: {kp_id}")
        return True

    # ------------------------------------------------------------------
    # 边管理
    # ------------------------------------------------------------------

    def add_edge(
        self,
        from_id: str,
        to_id: str,
        relation_type: str = "prerequisite",
        weight: float = 1.0,
    ) -> KGEdge:
        """
        添加知识点关系边

        relation_type 含义：
        - prerequisite: from_id 是 to_id 的前置知识
        - depends_on: to_id 依赖 from_id
        - related: 相关关系（无前置依赖）
        """
        if from_id not in self._nodes:
            raise ValueError(f"Source node '{from_id}' not found in graph")
        if to_id not in self._nodes:
            raise ValueError(f"Target node '{to_id}' not found in graph")

        edge = KGEdge(
            from_id=from_id,
            to_id=to_id,
            relation_type=relation_type,
            weight=weight,
        )
        self._edges.append(edge)
        self._adj_out.setdefault(from_id, []).append(to_id)
        self._adj_in.setdefault(to_id, []).append(from_id)
        logger.debug(f"KG edge added: {from_id} --[{relation_type}]--> {to_id}")
        return edge

    def remove_edge(
        self,
        from_id: str,
        to_id: str,
        relation_type: str = "prerequisite",
    ) -> bool:
        """删除知识点关系边"""
        initial_len = len(self._edges)
        self._edges = [
            e
            for e in self._edges
            if not (e.from_id == from_id and e.to_id == to_id and e.relation_type == relation_type)
        ]
        removed = len(self._edges) < initial_len
        if removed:
            if to_id in self._adj_out.get(from_id, []):
                self._adj_out[from_id].remove(to_id)
            if from_id in self._adj_in.get(to_id, []):
                self._adj_in[to_id].remove(from_id)
        return removed

    # ------------------------------------------------------------------
    # 查询方法
    # ------------------------------------------------------------------

    def get_prerequisites(self, kp_id: str) -> list[KGNode]:
        """获取指定知识点的所有前置依赖节点"""
        if kp_id not in self._nodes:
            return []
        prereq_ids = self._adj_in.get(kp_id, [])
        return [self._nodes[pid] for pid in prereq_ids if pid in self._nodes]

    def get_dependents(self, kp_id: str) -> list[KGNode]:
        """获取依赖该知识点的所有后续节点"""
        if kp_id not in self._nodes:
            return []
        dep_ids = self._adj_out.get(kp_id, [])
        return [self._nodes[did] for did in dep_ids if did in self._nodes]

    def get_all_prerequisites(self, kp_id: str) -> list[KGNode]:
        """递归获取所有前置依赖（传递闭包）"""
        visited = set()
        result = []
        queue = deque(self._adj_in.get(kp_id, []))
        while queue:
            current = queue.popleft()
            if current in visited or current not in self._nodes:
                continue
            visited.add(current)
            result.append(self._nodes[current])
            for pre_id in self._adj_in.get(current, []):
                if pre_id not in visited:
                    queue.append(pre_id)
        return result

    def get_all_dependents(self, kp_id: str) -> list[KGNode]:
        """递归获取所有后续依赖（传递闭包）"""
        visited = set()
        result = []
        queue = deque(self._adj_out.get(kp_id, []))
        while queue:
            current = queue.popleft()
            if current in visited or current not in self._nodes:
                continue
            visited.add(current)
            result.append(self._nodes[current])
            for dep_id in self._adj_out.get(current, []):
                if dep_id not in visited:
                    queue.append(dep_id)
        return result

    def find_path(
        self,
        start_kp: str,
        target_kp: str,
    ) -> list[KGNode]:
        """
        查找从 start_kp 到 target_kp 的最短学习路径（BFS）

        返回包括起点和终点的节点列表，表示需要学习的顺序。
        如无可达路径返回空列表。
        """
        if start_kp not in self._nodes or target_kp not in self._nodes:
            return []

        if start_kp == target_kp:
            return [self._nodes[start_kp]]

        visited = {start_kp}
        queue: deque[tuple[str, list[str]]] = deque()
        queue.append((start_kp, [start_kp]))

        while queue:
            current, path = queue.popleft()
            for neighbor in self._adj_out.get(current, []):
                if neighbor == target_kp:
                    full_path = path + [neighbor]
                    return [self._nodes[nid] for nid in full_path]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return []

    def get_subject_graph(self, subject: str) -> "KnowledgeGraph":
        """获取指定学科的子图"""
        sub_graph = KnowledgeGraph()
        subject_nodes = {nid for nid, node in self._nodes.items() if node.subject == subject}
        for nid in subject_nodes:
            node = self._nodes[nid]
            sub_graph.add_node(
                kp_id=node.kp_id,
                name=node.name,
                subject=node.subject,
                difficulty=node.difficulty,
                cognitive_level=node.cognitive_level,
                description=node.description,
                tags=node.tags,
            )
        for edge in self._edges:
            if edge.from_id in subject_nodes and edge.to_id in subject_nodes:
                sub_graph.add_edge(
                    from_id=edge.from_id,
                    to_id=edge.to_id,
                    relation_type=edge.relation_type,
                    weight=edge.weight,
                )
        return sub_graph

    def suggest_learning_path(
        self,
        user_mastery: dict[str, float],
        target_kp: str,
    ) -> list[dict[str, object]]:
        """
        根据用户当前掌握度和目标知识点，规划个性化学习路径

        策略：
        1. 获取目标知识点的所有前置依赖（包括传递闭包）
        2. 按依赖拓扑排序 + 掌握度升序排列
        3. 优先学习掌握度低的前置知识点
        4. 最后安排目标知识点本身

        Args:
            user_mastery: 用户对各知识点的掌握度映射
            target_kp: 目标知识点 ID

        Returns:
            学习路径规划列表，每项包含 kp_id、name、reason
        """
        if target_kp not in self._nodes:
            return []

        all_prereqs = self.get_all_prerequisites(target_kp)
        nodes_to_learn = list(all_prereqs)
        target_node = self._nodes[target_kp]

        nodes_to_learn.sort(key=lambda n: user_mastery.get(n.kp_id, 0.3))

        path: list[dict[str, object]] = []
        for node in nodes_to_learn:
            mastery = user_mastery.get(node.kp_id, 0.3)
            if mastery >= 0.85:
                continue

            in_degree = len(self._adj_in.get(node.kp_id, []))
            prereqs_done = all(
                user_mastery.get(pid, 0.0) >= 0.7 for pid in self._adj_in.get(node.kp_id, [])
            )

            if not prereqs_done:
                continue

            reason_parts = []
            if mastery < 0.3:
                reason_parts.append("薄弱知识点")
            elif mastery < 0.6:
                reason_parts.append("需要加强")
            else:
                reason_parts.append("接近掌握")

            if in_degree > 2:
                reason_parts.append("多知识点交叉")

            path.append(
                {
                    "kp_id": node.kp_id,
                    "name": node.name,
                    "mastery": round(mastery, 4),
                    "reason": "、".join(reason_parts),
                    "step": len(path) + 1,
                }
            )

        prereqs_of_target_ready = all(
            user_mastery.get(pid, 0.0) >= 0.7 for pid in self._adj_in.get(target_kp, [])
        )
        if prereqs_of_target_ready or not self._adj_in.get(target_kp, []):
            path.append(
                {
                    "kp_id": target_node.kp_id,
                    "name": target_node.name,
                    "mastery": user_mastery.get(target_kp, 0.3),
                    "reason": "目标知识点",
                    "step": len(path) + 1,
                    "is_target": True,
                }
            )

        return path

    # ------------------------------------------------------------------
    # 统计与工具
    # ------------------------------------------------------------------

    def get_node_count(self) -> int:
        return len(self._nodes)

    def get_edge_count(self) -> int:
        return len(self._edges)

    def get_subjects(self) -> list[str]:
        return sorted({node.subject for node in self._nodes.values()})

    def get_nodes_by_subject(self, subject: str) -> list[KGNode]:
        return [n for n in self._nodes.values() if n.subject == subject]

    def to_dict(self) -> dict:
        """序列化为字典（用于持久化）"""
        return {
            "nodes": [
                {
                    "kp_id": n.kp_id,
                    "name": n.name,
                    "subject": n.subject,
                    "difficulty": n.difficulty,
                    "cognitive_level": n.cognitive_level,
                    "description": n.description,
                    "tags": n.tags,
                }
                for n in self._nodes.values()
            ],
            "edges": [
                {
                    "from_id": e.from_id,
                    "to_id": e.to_id,
                    "relation_type": e.relation_type,
                    "weight": e.weight,
                }
                for e in self._edges
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "KnowledgeGraph":
        """从字典反序列化"""
        graph = cls()
        for node_data in data.get("nodes", []):
            graph.add_node(
                kp_id=node_data["kp_id"],
                name=node_data["name"],
                subject=node_data["subject"],
                difficulty=node_data.get("difficulty", 0.5),
                cognitive_level=node_data.get("cognitive_level", "knowledge"),
                description=node_data.get("description", ""),
                tags=node_data.get("tags", []),
            )
        for edge_data in data.get("edges", []):
            graph.add_edge(
                from_id=edge_data["from_id"],
                to_id=edge_data["to_id"],
                relation_type=edge_data.get("relation_type", "prerequisite"),
                weight=edge_data.get("weight", 1.0),
            )
        return graph


# ------------------------------------------------------------------
# 预构建知识图谱
# ------------------------------------------------------------------


def _build_math_graph() -> KnowledgeGraph:
    """
    构建预定义的数学知识图谱（25 个知识点）

    结构：有理数 → 实数 → 代数式 → 方程/不等式 → 函数
         → 几何（三角形/四边形/圆）→ 坐标几何
         → 微积分入门（极限/导数/积分）
    """
    g = KnowledgeGraph()

    # --- 基础数与式 ---
    g.add_node("math_001", "有理数", "数学", 0.2, "knowledge", "整数和分数统称有理数", ["数与式"])
    g.add_node("math_002", "无理数", "数学", 0.3, "knowledge", "无限不循环小数", ["数与式"])
    g.add_node("math_003", "实数", "数学", 0.2, "knowledge", "有理数和无理数统称实数", ["数与式"])
    g.add_node(
        "math_004",
        "代数式",
        "数学",
        0.3,
        "comprehension",
        "由数和字母通过运算符号连接而成",
        ["数与式"],
    )
    g.add_node(
        "math_005", "整式运算", "数学", 0.4, "application", "整式的加减乘除乘方运算", ["数与式"]
    )
    g.add_node(
        "math_006", "因式分解", "数学", 0.5, "application", "将多项式化为几个整式的积", ["数与式"]
    )
    g.add_node(
        "math_007", "分式", "数学", 0.4, "comprehension", "形如 A/B（B 不为零）的式子", ["数与式"]
    )

    # --- 方程与不等式 ---
    g.add_node(
        "math_010",
        "一元一次方程",
        "数学",
        0.3,
        "application",
        "只含一个未知数且次数为 1 的等式",
        ["方程"],
    )
    g.add_node(
        "math_011",
        "二元一次方程组",
        "数学",
        0.4,
        "application",
        "两个二元一次方程组成的方程组",
        ["方程"],
    )
    g.add_node(
        "math_012",
        "一元二次方程",
        "数学",
        0.5,
        "application",
        "只含一个未知数且最高次数为 2 的等式",
        ["方程"],
    )
    g.add_node(
        "math_013", "不等式与不等式组", "数学", 0.4, "application", "用不等号连接的式子", ["不等式"]
    )

    # --- 函数 ---
    g.add_node("math_020", "函数基础", "数学", 0.4, "comprehension", "变量之间的依赖关系", ["函数"])
    g.add_node(
        "math_021", "一次函数", "数学", 0.4, "application", "形如 y=kx+b (k≠0) 的函数", ["函数"]
    )
    g.add_node(
        "math_022", "反比例函数", "数学", 0.4, "application", "形如 y=k/x (k≠0) 的函数", ["函数"]
    )
    g.add_node(
        "math_023", "二次函数", "数学", 0.6, "application", "形如 y=ax²+bx+c (a≠0) 的函数", ["函数"]
    )
    g.add_node(
        "math_024",
        "指数函数",
        "数学",
        0.6,
        "comprehension",
        "形如 y=aˣ (a>0, a≠1) 的函数",
        ["函数"],
    )
    g.add_node("math_025", "对数函数", "数学", 0.7, "comprehension", "指数函数的反函数", ["函数"])
    g.add_node("math_026", "三角函数", "数学", 0.7, "application", "正弦、余弦、正切等", ["函数"])

    # --- 几何 ---
    g.add_node("math_030", "三角形基础", "数学", 0.4, "knowledge", "三角形的边角关系", ["几何"])
    g.add_node(
        "math_031", "全等三角形", "数学", 0.5, "application", "能够完全重合的两个三角形", ["几何"]
    )
    g.add_node(
        "math_032", "相似三角形", "数学", 0.5, "application", "对应角相等、对应边成比例", ["几何"]
    )
    g.add_node(
        "math_033",
        "勾股定理",
        "数学",
        0.5,
        "application",
        "直角三角形两直角边平方和等于斜边平方",
        ["几何"],
    )
    g.add_node(
        "math_034",
        "四边形",
        "数学",
        0.4,
        "comprehension",
        "平行四边形、矩形、菱形、正方形",
        ["几何"],
    )
    g.add_node(
        "math_035", "圆的基本性质", "数学", 0.5, "comprehension", "圆的对称性、垂径定理等", ["几何"]
    )
    g.add_node(
        "math_036", "坐标与图形", "数学", 0.4, "application", "平面直角坐标系中的图形变换", ["几何"]
    )

    # --- 微积分入门 ---
    g.add_node("math_040", "数列与极限", "数学", 0.8, "analysis", "数列的极限概念", ["微积分"])
    g.add_node("math_041", "导数", "数学", 0.8, "analysis", "函数的瞬时变化率", ["微积分"])
    g.add_node("math_042", "积分", "数学", 0.9, "synthesis", "导数的逆运算", ["微积分"])

    # --- 建立前置依赖边 ---
    # 数与式内部
    g.add_edge("math_001", "math_003", "prerequisite")
    g.add_edge("math_002", "math_003", "prerequisite")
    g.add_edge("math_003", "math_004", "prerequisite")
    g.add_edge("math_004", "math_005", "prerequisite")
    g.add_edge("math_005", "math_006", "prerequisite")
    g.add_edge("math_005", "math_007", "prerequisite")

    # 方程与不等式
    g.add_edge("math_004", "math_010", "prerequisite")
    g.add_edge("math_010", "math_011", "prerequisite")
    g.add_edge("math_005", "math_012", "prerequisite")
    g.add_edge("math_004", "math_013", "prerequisite")

    # 函数
    g.add_edge("math_010", "math_020", "prerequisite")
    g.add_edge("math_020", "math_021", "prerequisite")
    g.add_edge("math_020", "math_022", "prerequisite")
    g.add_edge("math_021", "math_023", "prerequisite")
    g.add_edge("math_023", "math_024", "prerequisite")
    g.add_edge("math_024", "math_025", "prerequisite")
    g.add_edge("math_020", "math_026", "prerequisite")
    g.add_edge("math_003", "math_026", "prerequisite")

    # 几何
    g.add_edge("math_003", "math_030", "prerequisite")
    g.add_edge("math_030", "math_031", "prerequisite")
    g.add_edge("math_031", "math_032", "prerequisite")
    g.add_edge("math_030", "math_033", "prerequisite")
    g.add_edge("math_033", "math_034", "prerequisite")
    g.add_edge("math_030", "math_035", "prerequisite")
    g.add_edge("math_020", "math_036", "prerequisite")
    g.add_edge("math_036", "math_023", "related")

    # 微积分
    g.add_edge("math_025", "math_040", "prerequisite")
    g.add_edge("math_021", "math_040", "prerequisite")
    g.add_edge("math_040", "math_041", "prerequisite")
    g.add_edge("math_041", "math_042", "prerequisite")
    g.add_edge("math_023", "math_041", "related")

    return g


def _build_physics_graph() -> KnowledgeGraph:
    """
    构建预定义的物理知识图谱（12 个知识点）

    结构：力学 → 电磁学 → 光学 → 热学
    """
    g = KnowledgeGraph()

    # --- 力学 ---
    g.add_node(
        "phy_001", "质点运动", "物理", 0.3, "comprehension", "匀速直线运动、变速直线运动", ["力学"]
    )
    g.add_node(
        "phy_002",
        "牛顿运动定律",
        "物理",
        0.4,
        "application",
        "惯性、F=ma、作用力与反作用力",
        ["力学"],
    )
    g.add_node(
        "phy_003", "功和能", "物理", 0.5, "application", "功、功率、动能定理、机械能守恒", ["力学"]
    )
    g.add_node("phy_004", "动量", "物理", 0.5, "application", "动量定理、动量守恒定律", ["力学"])
    g.add_node(
        "phy_005", "万有引力", "物理", 0.6, "application", "万有引力定律、天体运动", ["力学"]
    )

    # --- 电磁学 ---
    g.add_node(
        "phy_010", "电场", "物理", 0.6, "comprehension", "库仑定律、电场强度、电势能", ["电磁学"]
    )
    g.add_node(
        "phy_011", "电路", "物理", 0.5, "application", "欧姆定律、电功率、串并联电路", ["电磁学"]
    )
    g.add_node("phy_012", "磁场", "物理", 0.6, "comprehension", "安培力、洛伦兹力", ["电磁学"])
    g.add_node(
        "phy_013", "电磁感应", "物理", 0.7, "analysis", "法拉第电磁感应定律、楞次定律", ["电磁学"]
    )

    # --- 光学 ---
    g.add_node(
        "phy_020", "光的反射与折射", "物理", 0.4, "comprehension", "反射定律、折射定律", ["光学"]
    )
    g.add_node("phy_021", "光的波动性", "物理", 0.6, "comprehension", "干涉、衍射、偏振", ["光学"])

    # --- 热学 ---
    g.add_node(
        "phy_030", "热运动", "物理", 0.4, "comprehension", "分子热运动、温度、热膨胀", ["热学"]
    )

    # --- 建立前置依赖边 ---
    # 力学内部
    g.add_edge("phy_001", "phy_002", "prerequisite")
    g.add_edge("phy_002", "phy_003", "prerequisite")
    g.add_edge("phy_002", "phy_004", "prerequisite")
    g.add_edge("phy_003", "phy_005", "prerequisite")
    g.add_edge("phy_004", "phy_005", "related")

    # 电磁学
    g.add_edge("phy_002", "phy_010", "prerequisite")
    g.add_edge("phy_010", "phy_011", "prerequisite")
    g.add_edge("phy_010", "phy_012", "prerequisite")
    g.add_edge("phy_012", "phy_013", "prerequisite")
    g.add_edge("phy_011", "phy_013", "related")

    # 光学
    g.add_edge("phy_001", "phy_020", "prerequisite")
    g.add_edge("phy_020", "phy_021", "prerequisite")

    # 热学
    g.add_edge("phy_001", "phy_030", "prerequisite")

    return g


# ------------------------------------------------------------------
# 预构建图谱单例
# ------------------------------------------------------------------

_math_graph: Optional[KnowledgeGraph] = None
_physics_graph: Optional[KnowledgeGraph] = None


def get_math_graph() -> KnowledgeGraph:
    """获取预构建的数学知识图谱"""
    global _math_graph
    if _math_graph is None:
        _math_graph = _build_math_graph()
        logger.info(
            f"Math KG loaded: {_math_graph.get_node_count()} nodes, "
            f"{_math_graph.get_edge_count()} edges"
        )
    return _math_graph


def get_physics_graph() -> KnowledgeGraph:
    """获取预构建的物理知识图谱"""
    global _physics_graph
    if _physics_graph is None:
        _physics_graph = _build_physics_graph()
        logger.info(
            f"Physics KG loaded: {_physics_graph.get_node_count()} nodes, "
            f"{_physics_graph.get_edge_count()} edges"
        )
    return _physics_graph


def get_knowledge_graph(subject: Optional[str] = None) -> KnowledgeGraph:
    """
    获取知识图谱

    Args:
        subject: 学科标识（math/physics），不传则返回包含所有学科的图谱

    Returns:
        知识图谱实例
    """
    if subject == "math":
        return get_math_graph()
    elif subject == "physics":
        return get_physics_graph()
    else:
        math_g = get_math_graph()
        physics_g = get_physics_graph()

        merged = KnowledgeGraph()
        for node in math_g._nodes.values():
            merged.add_node(
                node.kp_id,
                node.name,
                node.subject,
                node.difficulty,
                node.cognitive_level,
                node.description,
                node.tags,
            )
        for edge in math_g._edges:
            merged.add_edge(edge.from_id, edge.to_id, edge.relation_type, edge.weight)

        for node in physics_g._nodes.values():
            merged.add_node(
                node.kp_id,
                node.name,
                node.subject,
                node.difficulty,
                node.cognitive_level,
                node.description,
                node.tags,
            )
        for edge in physics_g._edges:
            merged.add_edge(edge.from_id, edge.to_id, edge.relation_type, edge.weight)

        return merged

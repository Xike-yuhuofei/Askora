"""
数学知识点种子数据脚本
生成代数、几何、数论等学科的知识点数据

用法:
    python scripts/seed_knowledge.py generate   # 生成 JSON 数据文件
    python scripts/seed_knowledge.py import      # 导入到数据库
    python scripts/seed_knowledge.py status     # 查看当前知识点统计
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

KNOWLEDGE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "app",
    "data",
    "knowledge",
    "seed_knowledge.json",
)


def load_knowledge() -> list[dict[str, Any]]:
    with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_knowledge(knowledge: list[dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(KNOWLEDGE_PATH), exist_ok=True)
    with open(KNOWLEDGE_PATH, "w", encoding="utf-8") as f:
        json.dump(knowledge, f, ensure_ascii=False, indent=2)


def generate() -> list[dict[str, Any]]:
    knowledge: list[dict[str, Any]] = [
        {
            "id": "b1c2d3e4-0001-4000-8000-000000000101",
            "subject": "math",
            "unit_id": None,
            "parent_id": None,
            "name": "代数",
            "description": "代数是数学的一个分支，研究代数结构、方程和函数等内容",
            "code": "MATH-ALGEBRA",
            "level": 1,
            "difficulty": 3,
            "grade_range": [7, 8, 9],
            "prerequisites": [],
            "successors": [],
            "misconceptions": [],
            "is_active": True,
            "version": "1.0",
        },
        {
            "id": "b1c2d3e4-0002-4000-8000-000000000102",
            "subject": "math",
            "unit_id": "b1c2d3e4-0001-4000-8000-000000000101",
            "parent_id": "b1c2d3e4-0001-4000-8000-000000000101",
            "name": "线性方程",
            "description": "线性方程是含有未知数的等式，未知数的次数为一次",
            "code": "MATH-ALGEBRA-LINEAR",
            "level": 2,
            "difficulty": 2,
            "grade_range": [7, 8],
            "prerequisites": ["MATH-ALGEBRA-EXPRESSION"],
            "successors": ["MATH-ALGEBRA-QUADRATIC"],
            "misconceptions": [
                {
                    "id": "mc_linear_sign",
                    "name": "移项变号错误",
                    "description": "移项时忘记改变符号，如 x+3=7 写成 x=7+3",
                },
                {
                    "id": "mc_linear_check",
                    "name": "忘记检验",
                    "description": "解完方程后不代入原方程检验答案是否正确",
                },
            ],
            "is_active": True,
            "version": "1.0",
        },
        {
            "id": "b1c2d3e4-0003-4000-8000-000000000103",
            "subject": "math",
            "unit_id": "b1c2d3e4-0001-4000-8000-000000000101",
            "parent_id": "b1c2d3e4-0002-4000-8000-000000000102",
            "name": "一元一次方程",
            "description": "只含有一个未知数，且未知数次数为一次的方程",
            "code": "MATH-ALGEBRA-LINEAR-SINGLE",
            "level": 3,
            "difficulty": 2,
            "grade_range": [7],
            "prerequisites": ["MATH-ALGEBRA-LINEAR"],
            "successors": ["MATH-ALGEBRA-LINEAR-DOUBLE"],
            "misconceptions": [
                {
                    "id": "mc_single_coeff",
                    "name": "系数化为1错误",
                    "description": "两边除以系数时只除了一边或忘记变号",
                },
                {
                    "id": "mc_single_frac",
                    "name": "分数系数处理错误",
                    "description": "含有分数系数时通分和约分出现错误",
                },
            ],
            "is_active": True,
            "version": "1.0",
        },
        {
            "id": "b1c2d3e4-0004-4000-8000-000000000104",
            "subject": "math",
            "unit_id": "b1c2d3e4-0001-4000-8000-000000000101",
            "parent_id": "b1c2d3e4-0002-4000-8000-000000000102",
            "name": "二元一次方程组",
            "description": "含有两个未知数，每个未知数的次数都是一次的方程组",
            "code": "MATH-ALGEBRA-LINEAR-DOUBLE",
            "level": 3,
            "difficulty": 3,
            "grade_range": [7, 8],
            "prerequisites": ["MATH-ALGEBRA-LINEAR-SINGLE"],
            "successors": [],
            "misconceptions": [
                {
                    "id": "mc_double_method",
                    "name": "消元方法选择不当",
                    "description": "不知道何时用代入法、何时用加减法更简便",
                },
                {
                    "id": "mc_double_solve",
                    "name": "只求出一个未知数",
                    "description": "解完一个未知数忘记求另一个未知数",
                },
            ],
            "is_active": True,
            "version": "1.0",
        },
        {
            "id": "b1c2d3e4-0005-4000-8000-000000000105",
            "subject": "math",
            "unit_id": "b1c2d3e4-0001-4000-8000-000000000101",
            "parent_id": "b1c2d3e4-0001-4000-8000-000000000101",
            "name": "二次方程",
            "description": "含有未知数的二次项的方程，一般形式为 ax²+bx+c=0 (a≠0)",
            "code": "MATH-ALGEBRA-QUADRATIC",
            "level": 2,
            "difficulty": 4,
            "grade_range": [9],
            "prerequisites": ["MATH-ALGEBRA-LINEAR", "MATH-ALGEBRA-FUNCTION"],
            "successors": [],
            "misconceptions": [
                {
                    "id": "mc_quadratic_degree",
                    "name": "忽视 a≠0 条件",
                    "description": "使用求根公式时忘记检查二次项系数不为零",
                },
                {
                    "id": "mc_quadratic_sign",
                    "name": "求根公式符号错误",
                    "description": "求根公式中-b±√(b²-4ac)的符号容易出错",
                },
                {
                    "id": "mc_quadratic_sqroot",
                    "name": "开方忘取正负",
                    "description": "两边开平方时只取正根，忘记负根",
                },
            ],
            "is_active": True,
            "version": "1.0",
        },
        {
            "id": "b1c2d3e4-0006-4000-8000-000000000106",
            "subject": "math",
            "unit_id": "b1c2d3e4-0001-4000-8000-000000000101",
            "parent_id": "b1c2d3e4-0005-4000-8000-000000000105",
            "name": "因式分解法",
            "description": "将二次方程化为两个一次因式的乘积等于零的形式来求解",
            "code": "MATH-ALGEBRA-QUADRATIC-FACTOR",
            "level": 3,
            "difficulty": 3,
            "grade_range": [9],
            "prerequisites": ["MATH-ALGEBRA-QUADRATIC"],
            "successors": [],
            "misconceptions": [
                {
                    "id": "mc_factor_zero",
                    "name": "忽视零乘积性质",
                    "description": "不知道若 A·B=0 则 A=0 或 B=0 的原理",
                },
                {
                    "id": "mc_factor_miss",
                    "name": "漏解",
                    "description": "因式分解后只令一个因式为零，忘记另一个",
                },
            ],
            "is_active": True,
            "version": "1.0",
        },
        {
            "id": "b1c2d3e4-0007-4000-8000-000000000107",
            "subject": "math",
            "unit_id": "b1c2d3e4-0001-4000-8000-000000000101",
            "parent_id": "b1c2d3e4-0005-4000-8000-000000000105",
            "name": "配方法",
            "description": "将二次方程化为完全平方形式来求解",
            "code": "MATH-ALGEBRA-QUADRATIC-COMPLETE",
            "level": 3,
            "difficulty": 4,
            "grade_range": [9],
            "prerequisites": ["MATH-ALGEBRA-QUADRATIC"],
            "successors": [],
            "misconceptions": [
                {
                    "id": "mc_complete_const",
                    "name": "配方时常数项错误",
                    "description": "完全平方公式 (x+a)²=x²+2ax+a² 中，常数项计算错误",
                },
                {
                    "id": "mc_complete_both",
                    "name": "忘记两边加常数",
                    "description": "只在一边加了配方所需的常数，忘记另一边也要加",
                },
            ],
            "is_active": True,
            "version": "1.0",
        },
        {
            "id": "b1c2d3e4-0008-4000-8000-000000000108",
            "subject": "math",
            "unit_id": "b1c2d3e4-0001-4000-8000-000000000101",
            "parent_id": "b1c2d3e4-0001-4000-8000-000000000101",
            "name": "函数",
            "description": "函数是描述变量之间依赖关系的数学模型",
            "code": "MATH-ALGEBRA-FUNCTION",
            "level": 2,
            "difficulty": 3,
            "grade_range": [8, 9],
            "prerequisites": ["MATH-ALGEBRA-EXPRESSION"],
            "successors": [],
            "misconceptions": [
                {
                    "id": "mc_function_def",
                    "name": "函数与方程混淆",
                    "description": "将函数 y=f(x) 与方程 f(x)=0 混淆，不理解输入输出关系",
                },
                {
                    "id": "mc_function_pair",
                    "name": "一对多误解",
                    "description": "认为一个输入可以对应多个输出，不理解函数的唯一性要求",
                },
            ],
            "is_active": True,
            "version": "1.0",
        },
        {
            "id": "b1c2d3e4-0009-4000-8000-000000000109",
            "subject": "math",
            "unit_id": "b1c2d3e4-0001-4000-8000-000000000101",
            "parent_id": "b1c2d3e4-0008-4000-8000-000000000108",
            "name": "一次函数",
            "description": "形如 y=kx+b（k≠0）的函数，其图像是一条直线",
            "code": "MATH-ALGEBRA-FUNCTION-LINEAR",
            "level": 3,
            "difficulty": 2,
            "grade_range": [8],
            "prerequisites": ["MATH-ALGEBRA-FUNCTION"],
            "successors": [],
            "misconceptions": [
                {
                    "id": "mc_k_b",
                    "name": "k 和 b 的几何意义混淆",
                    "description": "不知道 k 决定斜率，b 决定截距",
                },
                {
                    "id": "mc_k_zero",
                    "name": "忽视 k≠0",
                    "description": "不知道当 k=0 时函数退化为常数函数",
                },
            ],
            "is_active": True,
            "version": "1.0",
        },
        {
            "id": "b1c2d3e4-000a-4000-8000-00000000010a",
            "subject": "math",
            "unit_id": "b1c2d3e4-0001-4000-8000-000000000101",
            "parent_id": "b1c2d3e4-0008-4000-8000-000000000108",
            "name": "二次函数",
            "description": "形如 y=ax²+bx+c（a≠0）的函数，其图像是抛物线",
            "code": "MATH-ALGEBRA-FUNCTION-QUADRATIC",
            "level": 3,
            "difficulty": 4,
            "grade_range": [9],
            "prerequisites": ["MATH-ALGEBRA-FUNCTION-LINEAR", "MATH-ALGEBRA-QUADRATIC"],
            "successors": [],
            "misconceptions": [
                {
                    "id": "mc_vertex",
                    "name": "顶点坐标计算错误",
                    "description": "顶点坐标公式 (-b/2a, (4ac-b²)/4a) 中符号或计算错误",
                },
                {
                    "id": "mc_direction",
                    "name": "开口方向判断错误",
                    "description": "不知道 a>0 开口向上，a<0 开口向下",
                },
            ],
            "is_active": True,
            "version": "1.0",
        },
        {
            "id": "b1c2d3e4-000b-4000-8000-00000000010b",
            "subject": "math",
            "unit_id": "b1c2d3e4-0001-4000-8000-000000000101",
            "parent_id": "b1c2d3e4-0008-4000-8000-000000000108",
            "name": "反比例函数",
            "description": "形如 y=k/x（k≠0）的函数，其图像是双曲线",
            "code": "MATH-ALGEBRA-FUNCTION-INVERSE",
            "level": 3,
            "difficulty": 3,
            "grade_range": [8],
            "prerequisites": ["MATH-ALGEBRA-FUNCTION"],
            "successors": [],
            "misconceptions": [
                {
                    "id": "mc_inverse_domain",
                    "name": "忽视定义域",
                    "description": "不知道 x≠0 是反比例函数的必要条件",
                },
                {
                    "id": "mc_inverse_sym",
                    "name": "对称性理解困难",
                    "description": "不理解双曲线关于原点对称的性质",
                },
            ],
            "is_active": True,
            "version": "1.0",
        },
        {
            "id": "b1c2d3e4-000c-4000-8000-00000000010c",
            "subject": "math",
            "unit_id": "b1c2d3e4-0001-4000-8000-000000000101",
            "parent_id": None,
            "name": "代数式与整式",
            "description": "用运算符号把数和字母连接而成的式子叫做代数式",
            "code": "MATH-ALGEBRA-EXPRESSION",
            "level": 2,
            "difficulty": 2,
            "grade_range": [7],
            "prerequisites": [],
            "successors": ["MATH-ALGEBRA-LINEAR"],
            "misconceptions": [
                {
                    "id": "mc_expr_term",
                    "name": "项的概念不清",
                    "description": "在合并同类项时，对'项'的定义理解模糊",
                },
                {
                    "id": "mc_expr_sign",
                    "name": "符号处理错误",
                    "description": "去括号或添括号时符号变化规则不熟悉",
                },
            ],
            "is_active": True,
            "version": "1.0",
        },
        {
            "id": "b1c2d3e4-000d-4000-8000-00000000010d",
            "subject": "math",
            "unit_id": None,
            "parent_id": None,
            "name": "几何",
            "description": "几何是研究空间图形性质的数学分支",
            "code": "MATH-GEOMETRY",
            "level": 1,
            "difficulty": 3,
            "grade_range": [7, 8, 9],
            "prerequisites": [],
            "successors": [],
            "misconceptions": [],
            "is_active": True,
            "version": "1.0",
        },
        {
            "id": "b1c2d3e4-000e-4000-8000-00000000010e",
            "subject": "math",
            "unit_id": "b1c2d3e4-000d-4000-8000-00000000010d",
            "parent_id": "b1c2d3e4-000d-4000-8000-00000000010d",
            "name": "三角形",
            "description": "由三条线段首尾顺次连接组成的封闭图形",
            "code": "MATH-GEOMETRY-TRIANGLE",
            "level": 2,
            "difficulty": 2,
            "grade_range": [7, 8],
            "prerequisites": [],
            "successors": [],
            "misconceptions": [
                {
                    "id": "mc_tri_ineq",
                    "name": "三边关系误用",
                    "description": "不知道三角形任意两边之和大于第三边的判定条件",
                },
                {
                    "id": "mc_tri_angle",
                    "name": "内角和证明困难",
                    "description": "知道内角和为180°但不会证明",
                },
            ],
            "is_active": True,
            "version": "1.0",
        },
        {
            "id": "b1c2d3e4-000f-4000-8000-00000000010f",
            "subject": "math",
            "unit_id": "b1c2d3e4-000d-4000-8000-00000000010d",
            "parent_id": "b1c2d3e4-000e-4000-8000-00000000010e",
            "name": "全等三角形",
            "description": "能够完全重合的两个三角形叫做全等三角形",
            "code": "MATH-GEOMETRY-TRIANGLE-CONGRUENT",
            "level": 3,
            "difficulty": 3,
            "grade_range": [8],
            "prerequisites": ["MATH-GEOMETRY-TRIANGLE"],
            "successors": ["MATH-GEOMETRY-TRIANGLE-SIMILAR"],
            "misconceptions": [
                {
                    "id": "mc_congruent_sss",
                    "name": "SSA 误用",
                    "description": "用'SSA'（边边角）来判定全等，实际上 SSA 不能唯一确定三角形",
                },
                {
                    "id": "mc_congruent_corresp",
                    "name": "对应关系混乱",
                    "description": "找错对应边和对应角，导致证明错误",
                },
            ],
            "is_active": True,
            "version": "1.0",
        },
        {
            "id": "b1c2d3e4-0010-4000-8000-000000000110",
            "subject": "math",
            "unit_id": "b1c2d3e4-000d-4000-8000-00000000010d",
            "parent_id": "b1c2d3e4-000e-4000-8000-00000000010e",
            "name": "相似三角形",
            "description": "对应角相等、对应边成比例的两个三角形叫做相似三角形",
            "code": "MATH-GEOMETRY-TRIANGLE-SIMILAR",
            "level": 3,
            "difficulty": 4,
            "grade_range": [9],
            "prerequisites": ["MATH-GEOMETRY-TRIANGLE-CONGRUENT"],
            "successors": [],
            "misconceptions": [
                {
                    "id": "mc_similar_ratio",
                    "name": "比例关系混乱",
                    "description": "找不到正确的对应边比例关系",
                },
                {
                    "id": "mc_similar_aa",
                    "name": "AA 判定理解不清",
                    "description": "只用两组角相等判定相似时不理解为什么成立",
                },
            ],
            "is_active": True,
            "version": "1.0",
        },
        {
            "id": "b1c2d3e4-0011-4000-8000-000000000111",
            "subject": "math",
            "unit_id": "b1c2d3e4-000d-4000-8000-00000000010d",
            "parent_id": "b1c2d3e4-000d-4000-8000-00000000010d",
            "name": "圆",
            "description": "平面内到定点距离等于定长的所有点组成的图形",
            "code": "MATH-GEOMETRY-CIRCLE",
            "level": 2,
            "difficulty": 3,
            "grade_range": [8, 9],
            "prerequisites": [],
            "successors": [],
            "misconceptions": [
                {
                    "id": "mc_circle_radius",
                    "name": "半径与直径关系",
                    "description": "不知道同圆中直径是半径的2倍",
                },
                {
                    "id": "mc_circle_arc",
                    "name": "弧与弦混淆",
                    "description": "混淆弧（曲线）和弦（直线段）的概念",
                },
            ],
            "is_active": True,
            "version": "1.0",
        },
        {
            "id": "b1c2d3e4-0012-4000-8000-000000000112",
            "subject": "math",
            "unit_id": "b1c2d3e4-000d-4000-8000-00000000010d",
            "parent_id": "b1c2d3e4-0011-4000-8000-000000000111",
            "name": "圆心角与圆周角",
            "description": "顶点在圆心的角叫圆心角，顶点在圆上且两边与圆相交的角叫圆周角",
            "code": "MATH-GEOMETRY-CIRCLE-ANGLE",
            "level": 3,
            "difficulty": 3,
            "grade_range": [9],
            "prerequisites": ["MATH-GEOMETRY-CIRCLE"],
            "successors": [],
            "misconceptions": [
                {
                    "id": "mc_angle_relation",
                    "name": "圆心角与圆周角关系错误",
                    "description": "不知道同弧所对的圆周角是圆心角的一半",
                },
                {
                    "id": "mc_angle_arc",
                    "name": "弧的度数与圆心角",
                    "description": "不理解弧的度数等于它所对圆心角的度数",
                },
            ],
            "is_active": True,
            "version": "1.0",
        },
        {
            "id": "b1c2d3e4-0013-4000-8000-000000000113",
            "subject": "math",
            "unit_id": "b1c2d3e4-000d-4000-8000-00000000010d",
            "parent_id": "b1c2d3e4-0011-4000-8000-000000000111",
            "name": "圆的切线",
            "description": "与圆只有一个公共点的直线叫做圆的切线",
            "code": "MATH-GEOMETRY-CIRCLE-TANGENT",
            "level": 3,
            "difficulty": 4,
            "grade_range": [9],
            "prerequisites": ["MATH-GEOMETRY-CIRCLE-ANGLE"],
            "successors": [],
            "misconceptions": [
                {
                    "id": "mc_tangent_perp",
                    "name": "切线性质误用",
                    "description": "不知道切线垂直于过切点的半径",
                },
                {
                    "id": "mc_tangent_equal",
                    "name": "切线长定理不熟悉",
                    "description": "不知道从圆外一点引圆的两条切线长相等",
                },
            ],
            "is_active": True,
            "version": "1.0",
        },
        {
            "id": "b1c2d3e4-0014-4000-8000-000000000114",
            "subject": "math",
            "unit_id": None,
            "parent_id": None,
            "name": "数论",
            "description": "数论是研究整数性质的数学分支",
            "code": "MATH-NUMBER-THEORY",
            "level": 1,
            "difficulty": 3,
            "grade_range": [6, 7, 8],
            "prerequisites": [],
            "successors": [],
            "misconceptions": [],
            "is_active": True,
            "version": "1.0",
        },
        {
            "id": "b1c2d3e4-0015-4000-8000-000000000115",
            "subject": "math",
            "unit_id": "b1c2d3e4-0014-4000-8000-000000000114",
            "parent_id": "b1c2d3e4-0014-4000-8000-000000000114",
            "name": "整除与因数",
            "description": "若整数 a 除以整数 b(b≠0) 的商是整数且没有余数，则称 a 能被 b 整除",
            "code": "MATH-NUMBER-THEORY-DIVISIBILITY",
            "level": 2,
            "difficulty": 2,
            "grade_range": [6],
            "prerequisites": [],
            "successors": ["MATH-NUMBER-THEORY-PRIME", "MATH-NUMBER-THEORY-GCD"],
            "misconceptions": [
                {
                    "id": "mc_div_zero",
                    "name": "0的整除问题",
                    "description": "混淆0能被非零整数整除与0不能作除数",
                },
                {
                    "id": "mc_div_factor",
                    "name": "因数与倍数混淆",
                    "description": "因数和倍数是相互依存的，不能单独说某数是因数或倍数",
                },
            ],
            "is_active": True,
            "version": "1.0",
        },
        {
            "id": "b1c2d3e4-0016-4000-8000-000000000116",
            "subject": "math",
            "unit_id": "b1c2d3e4-0014-4000-8000-000000000114",
            "parent_id": "b1c2d3e4-0015-4000-8000-000000000115",
            "name": "素数与合数",
            "description": "只有1和它本身两个因数的数叫素数（质数），有两个以上因数的数叫合数",
            "code": "MATH-NUMBER-THEORY-PRIME",
            "level": 2,
            "difficulty": 2,
            "grade_range": [6],
            "prerequisites": ["MATH-NUMBER-THEORY-DIVISIBILITY"],
            "successors": [],
            "misconceptions": [
                {
                    "id": "mc_prime_one",
                    "name": "1是素数",
                    "description": "错误地认为1是素数，实际上1既不是素数也不是合数",
                },
                {
                    "id": "mc_prime_even",
                    "name": "所有素数都是奇数",
                    "description": "忘记2是唯一的偶素数",
                },
            ],
            "is_active": True,
            "version": "1.0",
        },
        {
            "id": "b1c2d3e4-0017-4000-8000-000000000117",
            "subject": "math",
            "unit_id": "b1c2d3e4-0014-4000-8000-000000000114",
            "parent_id": "b1c2d3e4-0015-4000-8000-000000000115",
            "name": "最大公约数与最小公倍数",
            "description": "几个数公有的因数中最大的一个叫最大公约数，公有的倍数中最小的一个叫最小公倍数",
            "code": "MATH-NUMBER-THEORY-GCD",
            "level": 2,
            "difficulty": 3,
            "grade_range": [6, 7],
            "prerequisites": ["MATH-NUMBER-THEORY-DIVISIBILITY", "MATH-NUMBER-THEORY-PRIME"],
            "successors": [],
            "misconceptions": [
                {
                    "id": "mc_gcd_lcm",
                    "name": "GCD 与 LCM 混淆",
                    "description": "分不清什么时候求最大公约数，什么时候求最小公倍数",
                },
                {
                    "id": "mc_gcd_method",
                    "name": "短除法使用不当",
                    "description": "用短除法时找不准公有的质因数",
                },
            ],
            "is_active": True,
            "version": "1.0",
        },
    ]

    return knowledge


async def import_to_database(knowledge: list[dict[str, Any]]) -> None:
    from sqlalchemy import text

    from app.core.database import close_db, get_engine, init_db

    await init_db()
    engine = get_engine()

    async with engine.begin() as conn:
        inserted = 0
        skipped = 0
        for kp in knowledge:
            result = await conn.execute(
                text("SELECT id FROM knowledge_points WHERE id = :id"),
                {"id": kp["id"]},
            )
            if result.fetchone() is not None:
                skipped += 1
                continue

            await conn.execute(
                text("""
                    INSERT INTO knowledge_points (
                        id, subject, unit_id, parent_id, name, description, code,
                        level, difficulty, grade_range, prerequisites, successors,
                        misconceptions, is_active, version
                    ) VALUES (
                        :id, :subject, :unit_id, :parent_id, :name, :description, :code,
                        :level, :difficulty,
                        cast(:grade_range as jsonb),
                        :prerequisites_raw,
                        :successors_raw,
                        cast(:misconceptions as jsonb),
                        :is_active, :version
                    )
                """),
                {
                    "id": kp["id"],
                    "subject": kp["subject"],
                    "unit_id": kp.get("unit_id"),
                    "parent_id": kp.get("parent_id"),
                    "name": kp["name"],
                    "description": kp.get("description"),
                    "code": kp["code"],
                    "level": kp.get("level", 1),
                    "difficulty": kp.get("difficulty", 3),
                    "grade_range": json.dumps(kp.get("grade_range", [])),
                    "prerequisites_raw": ",".join(kp.get("prerequisites", [])),
                    "successors_raw": ",".join(kp.get("successors", [])),
                    "misconceptions": json.dumps(kp.get("misconceptions", [])),
                    "is_active": kp.get("is_active", True),
                    "version": kp.get("version", "1.0"),
                },
            )
            inserted += 1

    await close_db()
    print(f"\n知识点导入完成！新增 {inserted} 条，跳过 {skipped} 条（已存在）")


def show_status(knowledge: list[dict[str, Any]]) -> None:
    from collections import Counter

    print(f"\n知识点统计（共 {len(knowledge)} 条）")
    print("=" * 60)

    subject_counter = Counter(k["subject"] for k in knowledge)
    print("\n按学科分布：")
    for subject, count in sorted(subject_counter.items(), key=lambda x: -x[1]):
        print(f"  {subject}: {count} 条")

    level_counter = Counter(k["level"] for k in knowledge)
    print("\n按层级分布：")
    for level, count in sorted(level_counter.items()):
        print(f"  Level {level}: {count} 条")

    diff_counter = Counter(k["difficulty"] for k in knowledge)
    print("\n按难度分布：")
    for diff, count in sorted(diff_counter.items()):
        print(f"  难度 {diff}: {count} 条")

    print("\n完整知识点列表：")
    print("-" * 60)
    for k in knowledge:
        mc_count = len(k.get("misconceptions", []))
        prereq_count = len(k.get("prerequisites", []))
        print(
            f"  [L{k['level']}|D{k['difficulty']}] {k['name']}"
            f" (code={k['code']}, 前置={prereq_count}, 迷思={mc_count})"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="数学知识点种子数据管理")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    subparsers.add_parser("generate", help="生成知识点 JSON 文件")
    subparsers.add_parser("import", help="导入知识点到数据库")
    subparsers.add_parser("status", help="查看知识点统计")

    args = parser.parse_args()

    if args.command == "generate":
        knowledge = generate()
        save_knowledge(knowledge)
        print(f"已生成 {len(knowledge)} 条知识点到: {KNOWLEDGE_PATH}")
    elif args.command == "import":
        knowledge = load_knowledge()
        asyncio.run(import_to_database(knowledge))
    elif args.command == "status":
        knowledge = load_knowledge()
        show_status(knowledge)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

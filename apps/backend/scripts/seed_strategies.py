"""
策略模板种子数据脚本
生成 34+ 苏格拉底策略模板，覆盖数学、物理、化学、生物、语文、英语、编程等学科

用法:
    python scripts/seed_strategies.py generate   # 生成 JSON 数据文件
    python scripts/seed_strategies.py import     # 导入到数据库
    python scripts/seed_strategies.py status     # 查看当前策略统计
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

STRATEGIES_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "app",
    "data",
    "strategies",
    "seed_strategies.json",
)


def load_strategies() -> list[dict[str, Any]]:
    with open(STRATEGIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_strategies(strategies: list[dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(STRATEGIES_PATH), exist_ok=True)
    with open(STRATEGIES_PATH, "w", encoding="utf-8") as f:
        json.dump(strategies, f, ensure_ascii=False, indent=2)


def generate() -> list[dict[str, Any]]:
    strategies: list[dict[str, Any]] = [
        {
            "id": "a1b2c3d4-0001-4000-8000-000000000001",
            "level_1_goal": "core_guidance",
            "level_2_skill": "concept_clarification",
            "level_3_context": "math_algebra_linear_equation",
            "name": "线性方程概念澄清策略",
            "description": "通过苏格拉底式提问帮助学生理解线性方程的基本概念，如未知数、等式性质、移项变号等",
            "prompt_template": (
                "学生正在学习线性方程。请通过递进式提问帮助学生澄清对线性方程的理解。\n\n"
                "要求：\n"
                "1. 不要直接给出定义，而是通过问题引导学生自己表达\n"
                "2. 从学生已有的知识出发，如'你之前学过等式的哪些性质？'\n"
                "3. 逐步聚焦到关键概念：什么是未知数？为什么可以移项？\n"
                "4. 当学生能正确表述后，追问'为什么这样做是合法的？'"
            ),
            "follow_up_strategies": [
                {
                    "type": "error_analysis",
                    "template": "当学生在移项时出现符号错误，追问：'你在移项时改变了什么？为什么要这样变？'",
                },
                {
                    "type": "counter_example",
                    "template": "给出一个常见错误过程，让学生判断：'小明解方程时写成了 2x+3=7 → 2x=7+3，你觉得对吗？为什么？'",
                },
            ],
            "escalation_threshold": 3,
            "de_escalation_threshold": 2,
        },
        {
            "id": "a1b2c3d4-0002-4000-8000-000000000002",
            "level_1_goal": "monitoring",
            "level_2_skill": "error_analysis",
            "level_3_context": "math_algebra_linear_equation",
            "name": "线性方程错误分析策略",
            "description": "引导学生识别和解方程过程中的常见错误，如移项未变号、运算错误等",
            "prompt_template": (
                "学生在解线性方程时出现了错误。请引导学生自己发现并分析错误。\n\n"
                "要求：\n"
                "1. 将学生的错误过程温和地呈现出来\n"
                "2. 引导学生一步步检查：'请检查你第一步的运算'\n"
                "3. 如果学生无法发现，缩小范围：'看看移项这一步的符号是否正确'\n"
                "4. 让学生自己说出错在哪里以及正确的做法"
            ),
            "follow_up_strategies": [
                {
                    "type": "self_explanation",
                    "template": "当学生修正错误后，追问：'如果下次再做类似题目，你会如何避免这个错误？'",
                },
                {
                    "type": "concept_clarification",
                    "template": "如果学生反复犯同类错误，回到概念层面：'移项的本质是什么？为什么要变号？'",
                },
            ],
            "escalation_threshold": 2,
            "de_escalation_threshold": 2,
        },
        {
            "id": "a1b2c3d4-0003-4000-8000-000000000003",
            "level_1_goal": "planning",
            "level_2_skill": "guided_discovery",
            "level_3_context": "math_algebra_quadratic_equation",
            "name": "二次方程引导发现策略",
            "description": "引导学生通过观察和归纳发现二次方程的解法，如因式分解、配方法等",
            "prompt_template": (
                "学生正在学习二次方程。请引导学生通过观察具体例子发现解法规律。\n\n"
                "要求：\n"
                "1. 先让学生观察几个可以因式分解的二次三项式\n"
                "2. 提问：'你能发现这些式子的共同特点吗？'\n"
                "3. 引导学生自己总结出因式分解的条件\n"
                "4. 再引入一般形式，引导思考：'如果不能直接分解，还能怎么做？'"
            ),
            "follow_up_strategies": [
                {
                    "type": "analogy",
                    "template": "将配方法类比为'凑成完全平方'：'如果 x²+6x 加上什么可以变成一个完全平方？'",
                },
                {
                    "type": "error_analysis",
                    "template": "展示常见错误：如忘记两边开方时取正负，让学生分析",
                },
            ],
            "escalation_threshold": 3,
            "de_escalation_threshold": 3,
        },
        {
            "id": "a1b2c3d4-0004-4000-8000-000000000004",
            "level_1_goal": "core_guidance",
            "level_2_skill": "counter_example",
            "level_3_context": "math_algebra_quadratic_equation",
            "name": "二次方程反例构造策略",
            "description": "通过构造反例帮助学生深入理解二次方程的各种情况",
            "prompt_template": (
                "学生正在学习二次方程的解。请通过反例帮助学生理解判别式的意义。\n\n"
                "要求：\n"
                "1. 先问：'所有二次方程都有实数解吗？'\n"
                "2. 引导学生尝试构造一个没有实数解的二次方程\n"
                "3. 追问：'你是怎么想到这个例子的？它的判别式是什么？'\n"
                "4. 再引导构造有两个相等实根和两个不等实根的例子"
            ),
            "follow_up_strategies": [
                {
                    "type": "self_explanation",
                    "template": "让学生总结：'什么样的二次方程有两个不等实根？你能用判别式来解释吗？'",
                },
                {
                    "type": "guided_discovery",
                    "template": "进一步引导：'对于系数 a、b、c 都是实数的情况，判别式能告诉我们什么？'",
                },
            ],
            "escalation_threshold": 3,
            "de_escalation_threshold": 2,
        },
        {
            "id": "a1b2c3d4-0005-4000-8000-000000000005",
            "level_1_goal": "core_guidance",
            "level_2_skill": "analogy",
            "level_3_context": "math_algebra_function",
            "name": "函数概念类比策略",
            "description": "通过生活化类比帮助学生理解函数的输入输出关系",
            "prompt_template": (
                "学生正在学习函数概念。请用生活化的类比帮助学生理解。\n\n"
                "要求：\n"
                "1. 提问：'你见过自动售货机吗？投入硬币，选择饮料，就出来饮料。这像什么？'\n"
                "2. 引导学生将函数类比为'输入-处理-输出'的机器\n"
                "3. 追问：'对于每个输入，输出是否唯一确定？这对应函数的什么性质？'\n"
                "4. 再引入数学表示：'如果把输入记为 x，输出记为 y，你能写出一个函数的例子吗？'"
            ),
            "follow_up_strategies": [
                {
                    "type": "counter_example",
                    "template": "给出'一对多'的例子（如 x² 开方）让学生判断是否是函数",
                },
                {
                    "type": "self_explanation",
                    "template": "让学生用自己的话解释：'用你的话说说什么是函数？'",
                },
            ],
            "escalation_threshold": 3,
            "de_escalation_threshold": 2,
        },
        {
            "id": "a1b2c3d4-0006-4000-8000-000000000006",
            "level_1_goal": "monitoring",
            "level_2_skill": "self_explanation",
            "level_3_context": "math_algebra_function",
            "name": "函数自我解释策略",
            "description": "引导学生用自己的语言解释函数的核心概念，检验理解深度",
            "prompt_template": (
                "学生已学习函数的基本概念。请引导学生进行自我解释。\n\n"
                "要求：\n"
                "1. 让学生向'一个没学过函数的朋友'解释什么是函数\n"
                "2. 要求用生活中的例子来辅助说明\n"
                "3. 追问：'你觉得函数和方程有什么区别？'\n"
                "4. 如果学生能清晰区分，再追问：'函数图像上的每个点代表什么？'"
            ),
            "follow_up_strategies": [
                {
                    "type": "error_analysis",
                    "template": "如果学生混淆函数与方程，给出 y=x+1 和 x+y=1 让学生辨析",
                },
                {
                    "type": "concept_clarification",
                    "template": "进一步追问：'定义域和值域在你的例子中对应什么？'",
                },
            ],
            "escalation_threshold": 3,
            "de_escalation_threshold": 2,
        },
        {
            "id": "a1b2c3d4-0007-4000-8000-000000000007",
            "level_1_goal": "core_guidance",
            "level_2_skill": "concept_clarification",
            "level_3_context": "math_geometry_triangle",
            "name": "三角形概念澄清策略",
            "description": "帮助学生理解三角形的基本性质，如内角和、三边关系等",
            "prompt_template": (
                "学生正在学习三角形。请通过提问帮助学生澄清三角形的关键性质。\n\n"
                "要求：\n"
                "1. 先问：'画一个三角形，它的三个内角加起来是多少度？你怎么验证？'\n"
                "2. 如果学生知道 180°，追问：'为什么是 180°？你能证明吗？'\n"
                "3. 引导学生通过平行线性质证明内角和\n"
                "4. 再引导思考三边关系：'任意三条线段都能组成三角形吗？'"
            ),
            "follow_up_strategies": [
                {
                    "type": "guided_discovery",
                    "template": "给学生三根不同长度的吸管让他们尝试拼接，引导发现三边关系",
                },
                {
                    "type": "counter_example",
                    "template": "给出 1cm, 2cm, 4cm 的线段，让学生判断能否构成三角形并说明理由",
                },
            ],
            "escalation_threshold": 3,
            "de_escalation_threshold": 2,
        },
        {
            "id": "a1b2c3d4-0008-4000-8000-000000000008",
            "level_1_goal": "monitoring",
            "level_2_skill": "error_analysis",
            "level_3_context": "math_geometry_circle",
            "name": "圆的概念错误分析策略",
            "description": "分析学生在圆的相关概念上的常见误解，如圆周角与圆心角的关系",
            "prompt_template": (
                "学生在学习圆的概念时出现了混淆。请引导学生分析错误。\n\n"
                "要求：\n"
                "1. 呈现学生的错误表述：'圆周角等于圆心角'\n"
                "2. 追问：'你能在图上画出一个圆周角和一个圆心角吗？它们有什么关系？'\n"
                "3. 引导学生自己发现：'同弧所对的圆周角和圆心角有什么数量关系？'\n"
                "4. 如果学生仍然混淆，用具体度数的例子引导验证"
            ),
            "follow_up_strategies": [
                {
                    "type": "self_explanation",
                    "template": "让学生重新表述正确关系：'现在你能正确说出圆周角和圆心角的关系吗？'",
                },
                {
                    "type": "guided_discovery",
                    "template": "引导学生证明：'你能证明同弧所对的圆周角是圆心角的一半吗？'",
                },
            ],
            "escalation_threshold": 2,
            "de_escalation_threshold": 2,
        },
        {
            "id": "a1b2c3d4-0009-4000-8000-000000000009",
            "level_1_goal": "planning",
            "level_2_skill": "guided_discovery",
            "level_3_context": "math_geometry_similarity",
            "name": "相似三角形引导发现策略",
            "description": "引导学生通过操作和测量发现相似三角形的判定条件",
            "prompt_template": (
                "学生正在学习相似三角形。请引导学生通过实践发现相似条件。\n\n"
                "要求：\n"
                "1. 给学生两个形状相同、大小不同的三角形\n"
                "2. 提问：'这两个三角形看起来很像，它们的边和角有什么关系？'\n"
                "3. 引导学生测量对应边的比例和对应角的大小\n"
                "4. 追问：'如果两个三角形的三组对应边成比例，它们一定相似吗？'"
            ),
            "follow_up_strategies": [
                {
                    "type": "counter_example",
                    "template": "给出两个边角边(SAS)条件的三角形，让学生判断是否相似并说明",
                },
                {
                    "type": "metacognitive_monitoring",
                    "template": "引导学生反思：'你用了哪些方法来判断两个三角形是否相似？哪种方法最可靠？'",
                },
            ],
            "escalation_threshold": 3,
            "de_escalation_threshold": 3,
        },
        {
            "id": "a1b2c3d4-0010-4000-8000-000000000010",
            "level_1_goal": "monitoring",
            "level_2_skill": "metacognitive_monitoring",
            "level_3_context": "math_geometry_coordinate",
            "name": "坐标系元认知监控策略",
            "description": "引导学生在使用坐标系解题时进行元认知监控，检查思路的有效性",
            "prompt_template": (
                "学生正在使用坐标系解决几何问题。请引导学生进行元认知监控。\n\n"
                "要求：\n"
                "1. 提问：'用坐标系解题的第一步通常是什么？'\n"
                "2. 引导学生反思：'你选择的坐标系原点和方向是否方便计算？'\n"
                "3. 追问：'你在计算过程中有没有遇到困难？是否有更简便的建系方式？'\n"
                "4. 让学生评价：'用坐标法和用几何方法相比，这次你觉得哪种更好？'"
            ),
            "follow_up_strategies": [
                {
                    "type": "error_analysis",
                    "template": "如果学生计算出错，引导检查：'计算过程中哪一步最容易出错？你如何验证？'",
                },
                {
                    "type": "self_explanation",
                    "template": "让学生总结：'用坐标法解题的关键步骤有哪些？'",
                },
            ],
            "escalation_threshold": 3,
            "de_escalation_threshold": 2,
        },
        {
            "id": "a1b2c3d4-0011-4000-8000-000000000011",
            "level_1_goal": "core_guidance",
            "level_2_skill": "concept_clarification",
            "level_3_context": "math_number_theory_divisibility",
            "name": "整除概念澄清策略",
            "description": "帮助学生理解整除的概念和性质，区分整除与除法的不同",
            "prompt_template": (
                "学生正在学习整除。请通过提问帮助学生澄清概念。\n\n"
                "要求：\n"
                "1. 先问：'6 ÷ 3 = 2，我们说 6 能被 3 整除。那么 7 ÷ 3 呢？'\n"
                "2. 引导学生说出整除的定义：'整除要求什么条件？商必须是什么数？'\n"
                "3. 追问：'整除和除法有什么区别？0 能作为除数吗？'\n"
                "4. 引导学生举例：'你能举出几个整除的例子吗？'"
            ),
            "follow_up_strategies": [
                {
                    "type": "counter_example",
                    "template": "给出 5 ÷ 2 = 2.5，让学生判断是否为整除并说明理由",
                },
                {
                    "type": "self_explanation",
                    "template": "让学生用自己的话定义：'现在你能准确定义什么是整除吗？'",
                },
            ],
            "escalation_threshold": 3,
            "de_escalation_threshold": 2,
        },
        {
            "id": "a1b2c3d4-0012-4000-8000-000000000012",
            "level_1_goal": "core_guidance",
            "level_2_skill": "counter_example",
            "level_3_context": "math_number_theory_prime",
            "name": "素数反例构造策略",
            "description": "通过构造反例帮助学生深刻理解素数与合数的区别",
            "prompt_template": (
                "学生正在学习素数与合数。请通过反例帮助学生理解。\n\n"
                "要求：\n"
                "1. 先问：'什么是素数？最小的素数是几？'\n"
                "2. 追问：'1 是素数吗？为什么？'\n"
                "3. 引导学生思考：'所有奇数都是素数吗？你能举出一个反例吗？'\n"
                "4. 进一步追问：'能被 3 整除的数都是合数吗？'"
            ),
            "follow_up_strategies": [
                {
                    "type": "guided_discovery",
                    "template": "让学生尝试找出 1-20 之间所有的素数，并总结素数的判定方法",
                },
                {
                    "type": "metacognitive_monitoring",
                    "template": "引导反思：'你在判断一个数是否为素数时，用的是什么方法？为什么 1 不是素数？'",
                },
            ],
            "escalation_threshold": 3,
            "de_escalation_threshold": 2,
        },
        {
            "id": "a1b2c3d4-0013-4000-8000-000000000013",
            "level_1_goal": "core_guidance",
            "level_2_skill": "concept_clarification",
            "level_3_context": "physics_mechanics_newton_laws",
            "name": "牛顿定律概念澄清策略",
            "description": "帮助学生理解牛顿运动定律的含义，特别是惯性和力的概念",
            "prompt_template": (
                "学生正在学习牛顿定律。请通过提问帮助学生澄清概念。\n\n"
                "要求：\n"
                "1. 先问：'你知道牛顿第一定律说的是什么吗？能用自己的话说说吗？'\n"
                "2. 如果学生说'物体不受力就静止'，追问：'做匀速直线运动的物体受力吗？'\n"
                "3. 引导学生区分'静止'和'匀速直线运动'都是平衡状态\n"
                "4. 用生活例子：'汽车突然启动时，乘客会向后仰。这是什么原因？'"
            ),
            "follow_up_strategies": [
                {
                    "type": "analogy",
                    "template": "将惯性类比为'惰性'：'物体喜欢保持原来的运动状态，这就是惯性。你能举出更多例子吗？'",
                },
                {
                    "type": "error_analysis",
                    "template": "如果学生认为'力是维持运动的原因'，引导分析错误：'踢出去的足球还受脚的力吗？为什么还会继续运动？'",
                },
            ],
            "escalation_threshold": 3,
            "de_escalation_threshold": 2,
        },
        {
            "id": "a1b2c3d4-0014-4000-8000-000000000014",
            "level_1_goal": "core_guidance",
            "level_2_skill": "analogy",
            "level_3_context": "physics_mechanics_momentum",
            "name": "动量类比运用策略",
            "description": "通过生活化类比帮助学生理解动量和动量守恒",
            "prompt_template": (
                "学生正在学习动量。请用类比帮助学生理解。\n\n"
                "要求：\n"
                "1. 提问：'一辆卡车和一辆自行车以相同速度行驶，哪个更难停下来？为什么？'\n"
                "2. 引导学生认识到'质量 × 速度'这个量的重要性\n"
                "3. 给出动量定义后，追问：'你能举出动量守恒的例子吗？'\n"
                "4. 用碰撞小球演示，引导学生观察碰撞前后的动量变化"
            ),
            "follow_up_strategies": [
                {
                    "type": "guided_discovery",
                    "template": "引导学生推导：'由牛顿第三定律和 F=ma，你能推导出动量守恒定律吗？'",
                },
                {
                    "type": "self_explanation",
                    "template": "让学生解释：'为什么动量守恒在碰撞中成立？用你的话说说。'",
                },
            ],
            "escalation_threshold": 3,
            "de_escalation_threshold": 2,
        },
        {
            "id": "a1b2c3d4-0015-4000-8000-000000000015",
            "level_1_goal": "monitoring",
            "level_2_skill": "error_analysis",
            "level_3_context": "physics_mechanics_energy",
            "name": "能量守恒错误分析策略",
            "description": "分析学生在能量守恒应用中的常见错误，如忽略摩擦力等",
            "prompt_template": (
                "学生在应用能量守恒时出现了错误。请引导学生分析。\n\n"
                "要求：\n"
                "1. 呈现学生的解题过程（忽略了摩擦力做功）\n"
                "2. 追问：'这个过程中有哪些力做了功？你都考虑到了吗？'\n"
                "3. 引导学生思考：'如果有摩擦力，机械能还守恒吗？为什么？'\n"
                "4. 让学生修正：'现在请重新做这道题，并检验你的答案'"
            ),
            "follow_up_strategies": [
                {
                    "type": "concept_clarification",
                    "template": "回到概念：'机械能守恒的条件是什么？什么时候用能量守恒而不是机械能守恒？'",
                },
                {
                    "type": "metacognitive_monitoring",
                    "template": "引导反思：'在应用能量守恒时，你通常会忘记考虑什么？如何避免？'",
                },
            ],
            "escalation_threshold": 2,
            "de_escalation_threshold": 2,
        },
        {
            "id": "a1b2c3d4-0016-4000-8000-000000000016",
            "level_1_goal": "core_guidance",
            "level_2_skill": "analogy",
            "level_3_context": "physics_electricity_field",
            "name": "电场类比运用策略",
            "description": "通过重力场类比帮助学生理解电场的概念和性质",
            "prompt_template": (
                "学生正在学习电场。请用重力场类比帮助理解。\n\n"
                "要求：\n"
                "1. 提问：'你知道重力场吗？物体在重力场中受到重力。'\n"
                "2. 引导：'电荷周围存在电场，电场对放入其中的电荷有力的作用。这和重力场有什么相似之处？'\n"
                "3. 追问：'重力场的方向是向下的，电场的方向如何规定的？'\n"
                "4. 引导学生用类比总结电场线的性质"
            ),
            "follow_up_strategies": [
                {
                    "type": "counter_example",
                    "template": "引导思考不同点：'电场和重力场有什么不同？电荷有几种？'",
                },
                {
                    "type": "self_explanation",
                    "template": "让学生向别人解释：'用你的话说说电场是什么，它的性质有哪些？'",
                },
            ],
            "escalation_threshold": 3,
            "de_escalation_threshold": 2,
        },
        {
            "id": "a1b2c3d4-0017-4000-8000-000000000017",
            "level_1_goal": "monitoring",
            "level_2_skill": "error_analysis",
            "level_3_context": "physics_electricity_circuit",
            "name": "电路错误分析策略",
            "description": "分析学生在电路分析中的常见错误，如串并联判断错误、欧姆定律误用等",
            "prompt_template": (
                "学生在电路分析中出现了错误。请引导学生分析。\n\n"
                "要求：\n"
                "1. 呈现学生的电路分析过程\n"
                "2. 追问：'你判断的是串联还是并联？你的依据是什么？'\n"
                "3. 如果判断错误，引导重新分析电路结构\n"
                "4. 追问：'欧姆定律的使用条件是什么？你在使用时是否满足条件？'"
            ),
            "follow_up_strategies": [
                {
                    "type": "guided_discovery",
                    "template": "引导学生总结串并联电路的判断方法：'有哪些方法可以判断电路是串联还是并联？'",
                },
                {
                    "type": "metacognitive_monitoring",
                    "template": "引导反思：'分析电路时你一般按什么步骤？哪一步最容易出错？'",
                },
            ],
            "escalation_threshold": 2,
            "de_escalation_threshold": 2,
        },
        {
            "id": "a1b2c3d4-0018-4000-8000-000000000018",
            "level_1_goal": "core_guidance",
            "level_2_skill": "concept_clarification",
            "level_3_context": "chemistry_equation",
            "name": "化学方程式概念澄清策略",
            "description": "帮助学生理解化学方程式的配平原理和质量守恒定律",
            "prompt_template": (
                "学生正在学习化学方程式。请通过提问帮助学生澄清。\n\n"
                "要求：\n"
                "1. 先问：'化学方程式表示什么？H₂ + O₂ → H₂O 配平了吗？'\n"
                "2. 引导学生数原子个数：'反应前后每种元素的原子数相等吗？'\n"
                "3. 追问：'配平化学方程式的依据是什么？这和质量守恒定律有什么关系？'\n"
                "4. 让学生尝试配平：'请尝试配平 Fe + O₂ → Fe₂O₃'"
            ),
            "follow_up_strategies": [
                {
                    "type": "guided_discovery",
                    "template": "引导学生总结配平方法：'你用了什么方法配平？还能想到其他方法吗？'",
                },
                {
                    "type": "error_analysis",
                    "template": "展示常见错误（如改下标而不是改系数），让学生分析",
                },
            ],
            "escalation_threshold": 3,
            "de_escalation_threshold": 2,
        },
        {
            "id": "a1b2c3d4-0019-4000-8000-000000000019",
            "level_1_goal": "planning",
            "level_2_skill": "guided_discovery",
            "level_3_context": "chemistry_periodic_table",
            "name": "元素周期表引导发现策略",
            "description": "引导学生发现元素周期表的排列规律和周期性",
            "prompt_template": (
                "学生正在学习元素周期表。请引导学生发现规律。\n\n"
                "要求：\n"
                "1. 提问：'观察元素周期表，你能发现哪些规律？'\n"
                "2. 引导学生从原子序数、电子排布、化合价等角度分析\n"
                "3. 追问：'为什么元素会有周期性变化？这和原子结构有什么关系？'\n"
                "4. 引导学生预测：'根据周期表，你能预测某元素的哪些性质？'"
            ),
            "follow_up_strategies": [
                {
                    "type": "analogy",
                    "template": "将周期表类比为'班级座位表'：'就像座位有规律，元素的排列也有规律。你能找到类似的规律吗？'",
                },
                {
                    "type": "metacognitive_monitoring",
                    "template": "引导反思：'你用了哪些方法来发现周期表的规律？哪种方法最有效？'",
                },
            ],
            "escalation_threshold": 3,
            "de_escalation_threshold": 3,
        },
        {
            "id": "a1b2c3d4-0020-4000-8000-000000000020",
            "level_1_goal": "core_guidance",
            "level_2_skill": "counter_example",
            "level_3_context": "chemistry_reaction_types",
            "name": "化学反应类型反例构造策略",
            "description": "通过构造反例帮助学生理解不同反应类型的区别",
            "prompt_template": (
                "学生正在学习化学反应类型。请通过反例帮助理解。\n\n"
                "要求：\n"
                "1. 先问：'化合反应和分解反应有什么区别？各举一个例子。'\n"
                "2. 追问：'置换反应和复分解反应又是什么？你能举出一个不属于这四种类型的反应吗？'\n"
                "3. 引导学生思考氧化还原反应与四种基本反应的关系\n"
                "4. 让学生分类：'给出几个反应方程式，你能判断它们分别属于什么类型吗？'"
            ),
            "follow_up_strategies": [
                {
                    "type": "concept_clarification",
                    "template": "辨析氧化还原：'有化合价变化的反应一定是氧化还原反应。你能举出一个没有化合价变化的反应吗？'",
                },
                {
                    "type": "self_explanation",
                    "template": "让学生总结：'你能用自己的话区分四种基本反应类型吗？'",
                },
            ],
            "escalation_threshold": 3,
            "de_escalation_threshold": 2,
        },
        {
            "id": "a1b2c3d4-0021-4000-8000-000000000021",
            "level_1_goal": "core_guidance",
            "level_2_skill": "analogy",
            "level_3_context": "biology_cell",
            "name": "细胞结构类比策略",
            "description": "通过工厂类比帮助学生理解细胞各结构的功能",
            "prompt_template": (
                "学生正在学习细胞结构。请用类比帮助理解。\n\n"
                "要求：\n"
                "1. 提问：'你能把一个细胞想象成一个工厂吗？'\n"
                "2. 引导类比：'细胞核像工厂的控制室，线粒体像发电站，核糖体像生产车间。你还能想到哪些类比？'\n"
                "3. 追问：'细胞膜像什么？它的功能是什么？'\n"
                "4. 让学生画出自定义的类比图并解释"
            ),
            "follow_up_strategies": [
                {
                    "type": "self_explanation",
                    "template": "让学生解释：'用你的类比，向同学介绍细胞的各个结构和功能。'",
                },
                {
                    "type": "counter_example",
                    "template": "引导思考：'如果细胞膜受损，细胞会怎样？这说明细胞膜的什么功能？'",
                },
            ],
            "escalation_threshold": 3,
            "de_escalation_threshold": 2,
        },
        {
            "id": "a1b2c3d4-0022-4000-8000-000000000022",
            "level_1_goal": "monitoring",
            "level_2_skill": "self_explanation",
            "level_3_context": "biology_genetics",
            "name": "遗传自我解释策略",
            "description": "引导学生用自己的语言解释遗传的基本原理",
            "prompt_template": (
                "学生正在学习遗传。请引导学生进行自我解释。\n\n"
                "要求：\n"
                "1. 让学生向一个'没有学过遗传的朋友'解释什么是遗传\n"
                "2. 追问：'DNA、基因、染色体三者是什么关系？'\n"
                "3. 要求用类比辅助说明\n"
                "4. 进一步追问：'为什么孩子长得像父母？你能用遗传的原理解释吗？'"
            ),
            "follow_up_strategies": [
                {
                    "type": "analogy",
                    "template": "建议类比：'DNA 像一本说明书，基因像说明书中的某一页，染色体像装订成册的书。这个类比合适吗？'",
                },
                {
                    "type": "error_analysis",
                    "template": "如果学生混淆 DNA 和基因，追问：'你能说出 DNA 和基因的关系吗？它们有什么区别？'",
                },
            ],
            "escalation_threshold": 3,
            "de_escalation_threshold": 2,
        },
        {
            "id": "a1b2c3d4-0023-4000-8000-000000000023",
            "level_1_goal": "core_guidance",
            "level_2_skill": "concept_clarification",
            "level_3_context": "chinese_reading_poetry",
            "name": "诗词鉴赏概念澄清策略",
            "description": "帮助学生理解诗词鉴赏的核心要素，如意象、意境、情感等",
            "prompt_template": (
                "学生正在学习诗词鉴赏。请通过提问帮助学生澄清鉴赏方法。\n\n"
                "要求：\n"
                "1. 以一首具体的古诗为例\n"
                "2. 提问：'读这首诗，你感受到了什么样的画面？'\n"
                "3. 追问：'诗中描写了哪些景物？这些景物传达了怎样的情感？'\n"
                "4. 引导：'什么是意象？什么是意境？你能结合这首诗说说吗？'"
            ),
            "follow_up_strategies": [
                {
                    "type": "guided_discovery",
                    "template": "引导比较：'如果把'春风又绿江南岸'的'绿'换成'吹'或'过'，效果有什么不同？'",
                },
                {
                    "type": "self_explanation",
                    "template": "让学生总结：'鉴赏古诗词时，你通常从哪些方面入手？'",
                },
            ],
            "escalation_threshold": 3,
            "de_escalation_threshold": 2,
        },
        {
            "id": "a1b2c3d4-0024-4000-8000-000000000024",
            "level_1_goal": "planning",
            "level_2_skill": "guided_discovery",
            "level_3_context": "chinese_reading_modern",
            "name": "现代文阅读理解引导策略",
            "description": "引导学生掌握现代文阅读理解的方法和技巧",
            "prompt_template": (
                "学生正在进行现代文阅读。请引导学生掌握阅读方法。\n\n"
                "要求：\n"
                "1. 提问：'读完全文，你认为这篇文章的主旨是什么？'\n"
                "2. 追问：'你从哪些地方得出这个结论？能找到相关的语句吗？'\n"
                "3. 引导关注文章结构：'文章是如何组织的？各段落之间有什么关系？'\n"
                "4. 引导深度思考：'作者写这篇文章的目的可能是什么？'"
            ),
            "follow_up_strategies": [
                {
                    "type": "self_explanation",
                    "template": "让学生总结：'做现代文阅读时，你一般按什么步骤？有什么技巧？'",
                },
                {
                    "type": "error_analysis",
                    "template": "如果学生理解偏差，引导回到文本：'你说的这个观点在文中哪里提到了？能找到原文依据吗？'",
                },
            ],
            "escalation_threshold": 3,
            "de_escalation_threshold": 2,
        },
        {
            "id": "a1b2c3d4-0025-4000-8000-000000000025",
            "level_1_goal": "monitoring",
            "level_2_skill": "self_explanation",
            "level_3_context": "chinese_reading_classical",
            "name": "文言文自我解释策略",
            "description": "引导学生用自己的话解释文言文的词句含义和文化背景",
            "prompt_template": (
                "学生正在学习文言文。请引导学生进行自我解释。\n\n"
                "要求：\n"
                "1. 选取一段文言文\n"
                "2. 让学生用现代汉语翻译，并说明每个关键词的意思\n"
                "3. 追问：'你觉得这句话的大意是什么？它讲述了什么道理或故事？'\n"
                "4. 引导思考文化背景：'这段文字反映了当时怎样的社会背景？'"
            ),
            "follow_up_strategies": [
                {
                    "type": "error_analysis",
                    "template": "如果学生翻译错误，追问：'你确定这个字的意思是这样吗？在古文中它还有哪些意思？'",
                },
                {
                    "type": "analogy",
                    "template": "引导类比：'这个成语在今天还在使用吗？用法有什么变化？'",
                },
            ],
            "escalation_threshold": 2,
            "de_escalation_threshold": 2,
        },
        {
            "id": "a1b2c3d4-0026-4000-8000-000000000026",
            "level_1_goal": "monitoring",
            "level_2_skill": "metacognitive_monitoring",
            "level_3_context": "chinese_writing_argumentative",
            "name": "议论文元认知监控策略",
            "description": "引导学生在写议论文时进行元认知监控，确保逻辑清晰、论据充分",
            "prompt_template": (
                "学生正在写议论文。请引导学生进行元认知监控。\n\n"
                "要求：\n"
                "1. 提问：'你的中心论点是什么？能明确说出来吗？'\n"
                "2. 追问：'你用了哪些论据来支持这个论点？论据是否充分？'\n"
                "3. 引导检查逻辑：'你的论证过程有没有漏洞？有没有考虑反方观点？'\n"
                "4. 引导自评：'如果给你自己的作文打分，你会打多少分？为什么？'"
            ),
            "follow_up_strategies": [
                {
                    "type": "error_analysis",
                    "template": "如果论据不足，引导补充：'除了这个例子，还有什么可以支持你的观点？'",
                },
                {
                    "type": "self_explanation",
                    "template": "让学生反思：'这次写作中最大的困难是什么？下次如何改进？'",
                },
            ],
            "escalation_threshold": 3,
            "de_escalation_threshold": 2,
        },
        {
            "id": "a1b2c3d4-0027-4000-8000-000000000027",
            "level_1_goal": "core_guidance",
            "level_2_skill": "self_explanation",
            "level_3_context": "chinese_writing_narrative",
            "name": "记叙文自我解释策略",
            "description": "引导学生反思记叙文的写作手法和情感表达",
            "prompt_template": (
                "学生正在写记叙文。请引导学生进行自我解释和反思。\n\n"
                "要求：\n"
                "1. 提问：'你写的记叙文想表达什么情感或主题？'\n"
                "2. 追问：'你用了哪些手法来表达这个情感？（细节描写、环境描写、对比等）'\n"
                "3. 引导检查：'读者读了你的文章，能感受到你想表达的情感吗？'\n"
                "4. 引导修改：'你觉得哪些地方可以改进？怎么改会更好？'"
            ),
            "follow_up_strategies": [
                {
                    "type": "analogy",
                    "template": "引导借鉴：'你读过的哪篇文章的写法值得借鉴？它用了什么手法？'",
                },
                {
                    "type": "metacognitive_monitoring",
                    "template": "引导反思：'这次写作经历让你学到了什么？下次写类似主题会有什么不同？'",
                },
            ],
            "escalation_threshold": 3,
            "de_escalation_threshold": 2,
        },
        {
            "id": "a1b2c3d4-0028-4000-8000-000000000028",
            "level_1_goal": "monitoring",
            "level_2_skill": "error_analysis",
            "level_3_context": "english_grammar_tense",
            "name": "英语时态错误分析策略",
            "description": "分析学生在英语时态使用中的常见错误，如一般现在时与现在完成时混淆",
            "prompt_template": (
                "学生在使用英语时态时出现了错误。请引导学生分析。\n\n"
                "要求：\n"
                "1. 呈现学生的错误句子\n"
                "2. 追问：'这句话想表达什么意思？你觉得应该用什么时态？'\n"
                "3. 引导比较：'一般现在时和现在完成时有什么区别？各举一个例子。'\n"
                "4. 让学生修正并解释：'现在请改正这句话，并说明理由'"
            ),
            "follow_up_strategies": [
                {
                    "type": "concept_clarification",
                    "template": "辨析时态：'现在完成时和一般过去时有什么不同？时间状语有什么区别？'",
                },
                {"type": "counter_example", "template": "给出几个句子让学生判断时态是否正确并说明"},
            ],
            "escalation_threshold": 2,
            "de_escalation_threshold": 2,
        },
        {
            "id": "a1b2c3d4-0029-4000-8000-000000000029",
            "level_1_goal": "core_guidance",
            "level_2_skill": "concept_clarification",
            "level_3_context": "english_grammar_clause",
            "name": "英语从句概念澄清策略",
            "description": "帮助学生理解名词性从句、定语从句和状语从句的区别和用法",
            "prompt_template": (
                "学生正在学习英语从句。请通过提问帮助学生澄清。\n\n"
                "要求：\n"
                "1. 给出一个包含从句的复合句\n"
                "2. 提问：'你能找出这句话中的从句吗？它在句中充当什么成分？'\n"
                "3. 引导区分：'名词性从句、定语从句和状语从句分别在句中起什么作用？'\n"
                "4. 让学生造句：'你能分别造一个包含这三种从句的句子吗？'"
            ),
            "follow_up_strategies": [
                {
                    "type": "guided_discovery",
                    "template": "引导发现关系词的选择：'在定语从句中，什么时候用 that？什么时候用 which？'",
                },
                {
                    "type": "error_analysis",
                    "template": "分析常见错误（如介词后误用 that），让学生说明原因",
                },
            ],
            "escalation_threshold": 3,
            "de_escalation_threshold": 2,
        },
        {
            "id": "a1b2c3d4-0030-4000-8000-000000000030",
            "level_1_goal": "core_guidance",
            "level_2_skill": "analogy",
            "level_3_context": "english_vocabulary_affix",
            "name": "英语词根词缀类比策略",
            "description": "通过词根词缀的类比帮助学生扩大词汇量",
            "prompt_template": (
                "学生正在学习英语词根词缀。请用类比帮助学生理解。\n\n"
                "要求：\n"
                "1. 给出一个含有常见词根的单词，如 'predict'\n"
                "2. 提问：'你能从 predict 中识别出哪些部分？pre- 意思是...，dict 意思是...'\n"
                "3. 引导类比：'你还知道哪些含有 dict 的单词？它们都和什么有关？'\n"
                "4. 让学生推理：'如果 pre- 表示'在...之前'，un- 表示'不'，你能猜出 unprecedented 的意思吗？'"
            ),
            "follow_up_strategies": [
                {
                    "type": "guided_discovery",
                    "template": "引导归纳：'你知道哪些常见的前缀和后缀？它们的意思分别是什么？'",
                },
                {
                    "type": "self_explanation",
                    "template": "让学生分享：'你用什么方法来记忆单词？词根词缀法对你有帮助吗？'",
                },
            ],
            "escalation_threshold": 3,
            "de_escalation_threshold": 2,
        },
        {
            "id": "a1b2c3d4-0031-4000-8000-000000000031",
            "level_1_goal": "planning",
            "level_2_skill": "guided_discovery",
            "level_3_context": "english_vocabulary_context",
            "name": "语境猜词引导发现策略",
            "description": "引导学生通过上下文语境推测生词的含义",
            "prompt_template": (
                "学生正在进行英语阅读，遇到了生词。请引导学生通过语境猜测词义。\n\n"
                "要求：\n"
                "1. 给出包含生词的句子或段落\n"
                "2. 提问：'这个词在句子中是什么词性？'\n"
                "3. 引导利用上下文：'附近有没有对这个词的解释、举例或对比？'\n"
                "4. 让学生猜测并验证：'根据上下文，你猜这个词是什么意思？你怎么验证？'"
            ),
            "follow_up_strategies": [
                {
                    "type": "self_explanation",
                    "template": "让学生总结：'你用了哪些线索来猜测词义？哪种线索最有帮助？'",
                },
                {
                    "type": "metacognitive_monitoring",
                    "template": "引导反思：'下次遇到生词时，你的猜测策略会有什么不同？'",
                },
            ],
            "escalation_threshold": 3,
            "de_escalation_threshold": 2,
        },
        {
            "id": "a1b2c3d4-0032-4000-8000-000000000032",
            "level_1_goal": "core_guidance",
            "level_2_skill": "concept_clarification",
            "level_3_context": "programming_variables",
            "name": "编程变量与函数概念澄清策略",
            "description": "帮助学生理解编程中变量、函数的概念及其在程序中的作用",
            "prompt_template": (
                "学生正在学习编程基础。请通过提问帮助学生澄清概念。\n\n"
                "要求：\n"
                "1. 提问：'你能把变量想象成什么？它和数学中的变量有什么相同和不同？'\n"
                "2. 引导区分：'变量名和变量值有什么区别？给变量命名需要注意什么？'\n"
                "3. 关于函数：'函数就像一个'黑盒子'，输入什么，输出什么。你能举例说明吗？'\n"
                "4. 追问：'什么时候应该使用函数？它带来了什么好处？'"
            ),
            "follow_up_strategies": [
                {
                    "type": "analogy",
                    "template": "将函数类比为'自动售货机'：'输入硬币（参数），输出饮料（返回值）。你能举出其他类比吗？'",
                },
                {
                    "type": "error_analysis",
                    "template": "展示常见错误（如变量未赋值就使用），让学生分析问题所在",
                },
            ],
            "escalation_threshold": 3,
            "de_escalation_threshold": 2,
        },
        {
            "id": "a1b2c3d4-0033-4000-8000-000000000033",
            "level_1_goal": "planning",
            "level_2_skill": "guided_discovery",
            "level_3_context": "programming_control_flow",
            "name": "编程控制流引导发现策略",
            "description": "引导学生探索循环和条件语句的用法和适用场景",
            "prompt_template": (
                "学生正在学习编程中的循环和条件。请引导学生探索。\n\n"
                "要求：\n"
                "1. 提问：'如果要打印 1 到 100，你会怎么做？有没有比写 100 次 print 更好的方法？'\n"
                "2. 引出循环概念后，追问：'while 循环和 for 循环有什么区别？分别适用于什么情况？'\n"
                "3. 引导思考条件：'if-else 语句在程序中的作用是什么？你能举出一个生活中的例子吗？'\n"
                "4. 让学生编写简单程序并解释"
            ),
            "follow_up_strategies": [
                {"type": "counter_example", "template": "给出死循环的例子，让学生分析问题并修正"},
                {
                    "type": "metacognitive_monitoring",
                    "template": "引导反思：'你在选择循环结构时考虑了哪些因素？如何避免死循环？'",
                },
            ],
            "escalation_threshold": 3,
            "de_escalation_threshold": 2,
        },
        {
            "id": "a1b2c3d4-0034-4000-8000-000000000034",
            "level_1_goal": "monitoring",
            "level_2_skill": "error_analysis",
            "level_3_context": "programming_debugging",
            "name": "编程调试错误分析策略",
            "description": "引导学生分析编程错误并学会使用调试技巧",
            "prompt_template": (
                "学生的程序出现了错误。请引导学生分析和调试。\n\n"
                "要求：\n"
                "1. 呈现错误信息或错误行为\n"
                "2. 引导阅读错误信息：'错误信息说的是什么意思？它指向代码的哪个位置？'\n"
                "3. 引导缩小范围：'你能定位到出错的行吗？这行代码想做什么？'\n"
                "4. 引导验证修复：'你觉得应该怎么修改？修改后如何验证？'"
            ),
            "follow_up_strategies": [
                {
                    "type": "metacognitive_monitoring",
                    "template": "引导反思：'你通常如何调试程序？有哪些有效的调试方法？'",
                },
                {
                    "type": "concept_clarification",
                    "template": "如果涉及概念误解（如类型错误），回到概念：'在 Python 中，数字和字符串有什么区别？如何转换？'",
                },
            ],
            "escalation_threshold": 2,
            "de_escalation_threshold": 2,
        },
    ]

    return strategies


async def import_to_database(strategies: list[dict[str, Any]]) -> None:
    from sqlalchemy import text

    from app.core.database import close_db, get_engine, init_db

    await init_db()
    engine = get_engine()

    async with engine.begin() as conn:
        inserted = 0
        skipped = 0
        for strategy in strategies:
            result = await conn.execute(
                text("SELECT id FROM strategy_templates WHERE id = :id"),
                {"id": strategy["id"]},
            )
            if result.fetchone() is not None:
                skipped += 1
                continue

            await conn.execute(
                text("""
                    INSERT INTO strategy_templates (
                        id, level_1_goal, level_2_skill, level_3_context,
                        name, description, prompt_template, follow_up_strategies,
                        escalation_threshold, de_escalation_threshold, version, is_active
                    ) VALUES (
                        :id, :level_1_goal, :level_2_skill, :level_3_context,
                        :name, :description, :prompt_template,
                        cast(:follow_up as jsonb),
                        :escalation, :de_escalation, :version, :is_active
                    )
                """),
                {
                    "id": strategy["id"],
                    "level_1_goal": strategy["level_1_goal"],
                    "level_2_skill": strategy["level_2_skill"],
                    "level_3_context": strategy["level_3_context"],
                    "name": strategy["name"],
                    "description": strategy.get("description"),
                    "prompt_template": strategy["prompt_template"],
                    "follow_up": json.dumps(strategy.get("follow_up_strategies", [])),
                    "escalation": strategy.get("escalation_threshold", 3),
                    "de_escalation": strategy.get("de_escalation_threshold", 2),
                    "version": strategy.get("version", "1.0"),
                    "is_active": strategy.get("is_active", True),
                },
            )
            inserted += 1

    await close_db()
    print(f"\n策略模板导入完成！新增 {inserted} 条，跳过 {skipped} 条（已存在）")


def show_status(strategies: list[dict[str, Any]]) -> None:
    from collections import Counter

    print(f"\n策略模板统计（共 {len(strategies)} 条）")
    print("=" * 60)

    l1_counter = Counter(s["level_1_goal"] for s in strategies)
    print("\n按 Level 1 目标分布：")
    for goal, count in sorted(l1_counter.items(), key=lambda x: -x[1]):
        print(f"  {goal}: {count} 条")

    l2_counter = Counter(s["level_2_skill"] for s in strategies)
    print("\n按 Level 2 技能分布：")
    for skill, count in sorted(l2_counter.items(), key=lambda x: -x[1]):
        print(f"  {skill}: {count} 条")

    l3_counter = Counter(s["level_3_context"] for s in strategies)
    print("\n按 Level 3 学科情境分布：")
    for ctx, count in sorted(l3_counter.items(), key=lambda x: -x[1]):
        print(f"  {ctx}: {count} 条")

    print("\n完整策略列表：")
    print("-" * 60)
    for s in strategies:
        print(f"  [{s['level_1_goal'][:4]}|{s['level_2_skill'][:8]}] {s['name']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="策略模板种子数据管理")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    subparsers.add_parser("generate", help="生成策略模板 JSON 文件")
    subparsers.add_parser("import", help="导入策略模板到数据库")
    subparsers.add_parser("status", help="查看策略模板统计")

    args = parser.parse_args()

    if args.command == "generate":
        strategies = generate()
        save_strategies(strategies)
        print(f"已生成 {len(strategies)} 条策略模板到: {STRATEGIES_PATH}")
    elif args.command == "import":
        strategies = load_strategies()
        asyncio.run(import_to_database(strategies))
    elif args.command == "status":
        strategies = load_strategies()
        show_status(strategies)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

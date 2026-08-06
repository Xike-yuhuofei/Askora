"""
策略库模块 (Strategy Library)
管理苏格拉底式提问策略的三级分类体系和模板
支持从 Python 内置列表和 YAML 文件两种来源加载
"""

from __future__ import annotations

import os
from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)

try:
    import yaml

    _YAML_AVAILABLE = True
except ImportError:
    import json as yaml

    _YAML_AVAILABLE = False


# 内置策略模板 (MVP 版本，硬编码在内存中)
# 后续将迁移到数据库
_BUILT_IN_STRATEGIES = [
    # === 规划类 (Planning) ===
    {
        "id": "strat_plan_goal_setting",
        "level_1_goal": "planning",
        "level_2_skill": "goal_setting",
        "level_3_context": "general",
        "name": "目标设定策略",
        "description": "引导学生明确学习目标",
        "prompt_template": "学生正在学习{concept}。请引导学生明确本次学习的具体目标。\n建议提问：你希望通过这次学习掌握什么？",
        "follow_up_strategies": ["strat_plan_strategy_selection"],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "1.0.0",
        "is_active": True,
    },
    {
        "id": "strat_plan_strategy_selection",
        "level_1_goal": "planning",
        "level_2_skill": "strategy_selection",
        "level_3_context": "general",
        "name": "策略选择策略",
        "description": "引导学生思考学习策略",
        "prompt_template": "学生已经设定了学习目标。请引导学生思考实现目标的可能策略。\n建议提问：为了达成这个目标，你认为可以从哪里开始？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "1.0.0",
        "is_active": True,
    },
    # === 监控类 (Monitoring) ===
    {
        "id": "strat_monitor_comprehension",
        "level_1_goal": "monitoring",
        "level_2_skill": "understanding_monitoring",
        "level_3_context": "general",
        "name": "理解监控策略",
        "description": "引导学生监控自己的理解程度",
        "prompt_template": "学生正在学习{concept}，可能遇到了困难。请引导学生反思自己的理解状态。\n建议提问：到目前为止，你对这个概念有几成把握？",
        "follow_up_strategies": ["strat_guide_clarify_concept"],
        "escalation_threshold": 2,
        "de_escalation_threshold": 2,
        "version": "1.0.0",
        "is_active": True,
    },
    {
        "id": "strat_monitor_process_check",
        "level_1_goal": "monitoring",
        "level_2_skill": "process_check",
        "level_3_context": "math_problem",
        "name": "过程检查策略",
        "description": "引导学生检查解题过程",
        "prompt_template": "学生正在解题。请引导学生检查解题过程中的关键步骤。\n建议提问：回顾一下你的解题过程，哪一步你觉得最不确定？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "1.0.0",
        "is_active": True,
    },
    # === 评估类 (Evaluation) ===
    {
        "id": "strat_eval_evidence_verification",
        "level_1_goal": "evaluation",
        "level_2_skill": "evidence_verification",
        "level_3_context": "general",
        "name": "证据验证策略",
        "description": "引导学生验证结论的依据",
        "prompt_template": "学生得出了某个结论。请引导学生验证结论的证据和依据。\n建议提问：你得出这个结论的依据是什么？",
        "follow_up_strategies": ["strat_eval_argument_assessment"],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "1.0.0",
        "is_active": True,
    },
    {
        "id": "strat_eval_argument_assessment",
        "level_1_goal": "evaluation",
        "level_2_skill": "argument_assessment",
        "level_3_context": "essay_writing",
        "name": "论证评估策略",
        "description": "引导学生评估论证的有效性",
        "prompt_template": "学生在写作中提出了论点。请引导学生评估论证的有效性。\n建议提问：你觉得这个论证是否充分？还有什么可以补充的？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "1.0.0",
        "is_active": True,
    },
    # === 核心引导类 (Core Guidance) ===
    {
        "id": "strat_guide_self_reflection",
        "level_1_goal": "core_guidance",
        "level_2_skill": "self_reflection",
        "level_3_context": "general",
        "name": "自我反思策略",
        "description": "引导学生进行深度自我反思",
        "prompt_template": "学生已完成一个学习单元。请引导学生进行自我反思。\n建议提问：通过这次学习，你觉得自己有什么收获？还有什么疑问？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "1.0.0",
        "is_active": True,
    },
    {
        "id": "strat_guide_viewpoint_clarification",
        "level_1_goal": "core_guidance",
        "level_2_skill": "viewpoint_clarification",
        "level_3_context": "general",
        "name": "观点澄清策略",
        "description": "引导学生澄清自己的观点",
        "prompt_template": "学生表达了某个观点。请引导学生澄清和深化这个观点。\n建议提问：能再详细说说你为什么会这样认为吗？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "1.0.0",
        "is_active": True,
    },
    {
        "id": "strat_guide_perspective_shift",
        "level_1_goal": "core_guidance",
        "level_2_skill": "perspective_shift",
        "level_3_context": "general",
        "name": "视角转换策略",
        "description": "引导学生从不同角度思考问题",
        "prompt_template": "学生对问题形成了一定看法。请引导学生从另一个角度重新审视。\n建议提问：如果从另一个角度来看这个问题，你会怎么看？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "1.0.0",
        "is_active": True,
    },
    # === 学科情境策略 ===
    {
        "id": "strat_clarify_concept",
        "level_1_goal": "monitoring",
        "level_2_skill": "viewpoint_clarification",
        "level_3_context": "algebra_equation",
        "name": "代数概念澄清策略",
        "description": "通过逐层追问帮助学生澄清代数概念理解",
        "prompt_template": "学生正在学习{concept}，当前状态是{student_state}。\n请用苏格拉底式提问引导学生澄清对{concept}的理解。\n提示级别：{hint_level} (1=最抽象，5=最具体)\n要求：\n1. 用问题回应，不要直接解释\n2. 从学生已有的理解出发\n3. 一次只问一个问题\n4. 问题要能激发思考",
        "follow_up_strategies": ["strat_evidence_verification", "strat_perspective_shift"],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.1.0",
        "is_active": True,
    },
    {
        "id": "strat_math_problem_solving",
        "level_1_goal": "planning",
        "level_2_skill": "strategy_selection",
        "level_3_context": "math_problem",
        "name": "数学解题策略",
        "description": "引导学生思考数学解题方法",
        "prompt_template": "学生正在解一道数学题。请引导学生思考解题思路。\n建议提问：你觉得这道题的关键是什么？可以用什么方法来解决？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "1.0.0",
        "is_active": True,
    },
    {
        "id": "strat_essay_planning",
        "level_1_goal": "planning",
        "level_2_skill": "goal_setting",
        "level_3_context": "essay_writing",
        "name": "议论文构思策略",
        "description": "引导学生进行议论文构思",
        "prompt_template": "学生正在写议论文。请引导学生进行构思和规划。\n建议提问：你想在文章中表达的中心观点是什么？有哪些论据可以支持？",
        "follow_up_strategies": ["strat_eval_argument_assessment"],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "1.0.0",
        "is_active": True,
    },
    {
        "id": "strat_reading_comprehension",
        "level_1_goal": "core_guidance",
        "level_2_skill": "viewpoint_clarification",
        "level_3_context": "reading_comprehension",
        "name": "阅读理解策略",
        "description": "引导学生深入理解文本",
        "prompt_template": "学生正在进行阅读理解。请引导学生深入思考文本内容。\n建议提问：你觉得这段话的主要意思是什么？作者想表达什么？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "1.0.0",
        "is_active": True,
    },
    # === 数学·代数策略 ===
    {
        "id": "strat_clarify_linear_equations",
        "level_1_goal": "core_guidance",
        "level_2_skill": "concept_clarification",
        "level_3_context": "linear_equations",
        "name": "线性方程概念澄清",
        "description": "帮助学生理解线性方程的基本概念和解法",
        "prompt_template": "学生正在学习线性方程。请用苏格拉底式提问引导学生理解：{concept}\n提示：从学生已有知识出发，通过递进问题帮助其理解等式两边的关系。",
        "follow_up_strategies": ["strat_guide_clarify_concept"],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_error_linear_equations",
        "level_1_goal": "monitoring",
        "level_2_skill": "error_analysis",
        "level_3_context": "linear_equations",
        "name": "线性方程错误分析",
        "description": "帮助学生分析解线性方程时的常见错误",
        "prompt_template": "学生在解线性方程时犯了错误。引导学生分析：{student_state}\n提问：你觉得哪一步可能出了问题？检查一下每步的运算是否正确。",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_clarify_quadratic_equations",
        "level_1_goal": "core_guidance",
        "level_2_skill": "concept_clarification",
        "level_3_context": "quadratic_equations",
        "name": "二次方程概念澄清",
        "description": "帮助学生理解二次方程的解法",
        "prompt_template": "学生正在学习二次方程。引导学生理解：{concept}\n提问：二次方程有哪些解法？各种解法适用于什么情况？",
        "follow_up_strategies": ["strat_clarify_linear_equations"],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_error_quadratic_equations",
        "level_1_goal": "monitoring",
        "level_2_skill": "error_analysis",
        "level_3_context": "quadratic_equations",
        "name": "二次方程错误分析",
        "description": "分析二次方程求解中的常见错误",
        "prompt_template": "学生在解二次方程时出错。引导分析：{student_state}\n提问：判别式计算是否正确？因式分解是否准确？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_clarify_functions",
        "level_1_goal": "core_guidance",
        "level_2_skill": "concept_clarification",
        "level_3_context": "functions",
        "name": "函数概念澄清",
        "description": "帮助学生理解函数的定义和性质",
        "prompt_template": "学生正在学习函数。引导理解：{concept}\n提问：什么是函数？函数的定义域和值域如何确定？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_analogy_functions",
        "level_1_goal": "core_guidance",
        "level_2_skill": "analogy",
        "level_3_context": "functions",
        "name": "函数类比策略",
        "description": "通过类比帮助学生理解函数",
        "prompt_template": "学生对函数概念困惑。使用类比帮助：{concept}\n提问：函数就像一台机器，输入x得到输出y。你能想到生活中的类似例子吗？",
        "follow_up_strategies": ["strat_clarify_functions"],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_clarify_inequalities",
        "level_1_goal": "core_guidance",
        "level_2_skill": "concept_clarification",
        "level_3_context": "inequalities",
        "name": "不等式概念澄清",
        "description": "帮助学生理解不等式的性质和解法",
        "prompt_template": "学生正在学习不等式。引导理解：{concept}\n提问：不等式两边乘以负数时需要注意什么？",
        "follow_up_strategies": ["strat_clarify_linear_equations"],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_self_explain_linear_equations",
        "level_1_goal": "core_guidance",
        "level_2_skill": "self_explanation",
        "level_3_context": "linear_equations",
        "name": "线性方程自我解释",
        "description": "要求学生解释解题思路以深化理解",
        "prompt_template": "学生解对了线性方程。要求自我解释：\n提问：你能一步步解释你是怎么解出这道题的吗？为什么选择这种方法？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_counter_example_equations",
        "level_1_goal": "core_guidance",
        "level_2_skill": "counter_example",
        "level_3_context": "linear_equations",
        "name": "方程反例构造",
        "description": "通过构造反例帮助学生理解概念边界",
        "prompt_template": "引导学生构造反例：\n提问：你能构造一个线性方程的例子吗？再想想什么情况下方程无解？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_guided_discovery_algebra",
        "level_1_goal": "core_guidance",
        "level_2_skill": "guided_discovery",
        "level_3_context": "algebra_equation",
        "name": "代数引导发现",
        "description": "引导学生通过发现学习代数规律",
        "prompt_template": "引导学生发现：{concept}\n提问：观察这些方程的解，你能发现什么规律？能总结出一般方法吗？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    # === 数学·几何策略 ===
    {
        "id": "strat_clarify_triangles",
        "level_1_goal": "core_guidance",
        "level_2_skill": "concept_clarification",
        "level_3_context": "triangles",
        "name": "三角形概念澄清",
        "description": "帮助学生理解三角形的性质和判定",
        "prompt_template": "学生正在学习三角形。引导理解：{concept}\n提问：三角形的内角和是多少？有哪些判定全等的方法？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_clarify_circles",
        "level_1_goal": "core_guidance",
        "level_2_skill": "concept_clarification",
        "level_3_context": "circles",
        "name": "圆的概念澄清",
        "description": "帮助学生理解圆的基本性质",
        "prompt_template": "学生正在学习圆。引导理解：{concept}\n提问：圆的面积和周长公式是什么？圆心角和圆周角的关系？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_error_geometry",
        "level_1_goal": "monitoring",
        "level_2_skill": "error_analysis",
        "level_3_context": "triangles",
        "name": "几何错误分析",
        "description": "分析几何证明中的常见错误",
        "prompt_template": "学生在几何证明中出错。引导分析：{student_state}\n提问：你的证明中用到了哪些定理？每一步的依据是否充分？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_analogy_geometry",
        "level_1_goal": "core_guidance",
        "level_2_skill": "analogy",
        "level_3_context": "coordinate_geometry",
        "name": "几何类比策略",
        "description": "通过类比帮助学生理解坐标几何",
        "prompt_template": "学生学习坐标几何。使用类比：{concept}\n提问：坐标系就像地图，如何用坐标确定位置？能类比到生活中的例子吗？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_self_explain_geometry",
        "level_1_goal": "core_guidance",
        "level_2_skill": "self_explanation",
        "level_3_context": "triangles",
        "name": "几何自我解释",
        "description": "要求学生解释几何证明思路",
        "prompt_template": "学生完成几何证明。要求解释：\n提问：你能一步步说明你的证明思路吗？为什么选择这些定理？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_guided_discovery_geometry",
        "level_1_goal": "core_guidance",
        "level_2_skill": "guided_discovery",
        "level_3_context": "circles",
        "name": "几何引导发现",
        "description": "引导学生发现几何规律",
        "prompt_template": "引导发现：{concept}\n提问：测量不同圆的周长和直径，你能发现什么比例关系？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    # === 数学·数论策略 ===
    {
        "id": "strat_clarify_divisibility",
        "level_1_goal": "core_guidance",
        "level_2_skill": "concept_clarification",
        "level_3_context": "divisibility",
        "name": "整除概念澄清",
        "description": "帮助学生理解整除的概念和性质",
        "prompt_template": "学生学习整除。引导理解：{concept}\n提问：什么是整除？2、3、5的整除特征分别是什么？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_clarify_primes",
        "level_1_goal": "core_guidance",
        "level_2_skill": "concept_clarification",
        "level_3_context": "primes",
        "name": "素数概念澄清",
        "description": "帮助学生理解素数和合数",
        "prompt_template": "学生学习素数。引导理解：{concept}\n提问：什么是素数？如何判断一个数是否为素数？",
        "follow_up_strategies": ["strat_clarify_divisibility"],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_clarify_gcd_lcm",
        "level_1_goal": "core_guidance",
        "level_2_skill": "concept_clarification",
        "level_3_context": "gcd_lcm",
        "name": "最大公约数与最小公倍数",
        "description": "帮助学生理解GCD和LCM",
        "prompt_template": "学生学习GCD/LCM。引导理解：{concept}\n提问：如何求两个数的最大公约数和最小公倍数？它们之间有什么关系？",
        "follow_up_strategies": ["strat_clarify_divisibility"],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    # === 物理策略 ===
    {
        "id": "strat_clarify_mechanics",
        "level_1_goal": "core_guidance",
        "level_2_skill": "concept_clarification",
        "level_3_context": "mechanics",
        "name": "力学概念澄清",
        "description": "帮助学生理力学基本概念",
        "prompt_template": "学生学习力学。引导理解：{concept}\n提问：牛顿三大定律分别是什么？在什么情况下使用？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_clarify_motion",
        "level_1_goal": "core_guidance",
        "level_2_skill": "concept_clarification",
        "level_3_context": "motion",
        "name": "运动概念澄清",
        "description": "帮助学生理解运动学概念",
        "prompt_template": "学生学习运动。引导理解：{concept}\n提问：速度和加速度有什么区别？匀速和加速运动的公式？",
        "follow_up_strategies": ["strat_clarify_mechanics"],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_clarify_forces",
        "level_1_goal": "core_guidance",
        "level_2_skill": "concept_clarification",
        "level_3_context": "forces",
        "name": "力的概念澄清",
        "description": "帮助学生理解力的概念和分析",
        "prompt_template": "学生学习力。引导理解：{concept}\n提问：有哪些常见的力？如何进行受力分析？",
        "follow_up_strategies": ["strat_clarify_mechanics"],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_clarify_energy",
        "level_1_goal": "core_guidance",
        "level_2_skill": "concept_clarification",
        "level_3_context": "energy",
        "name": "能量概念澄清",
        "description": "帮助学生理解能量守恒",
        "prompt_template": "学生学习能量。引导理解：{concept}\n提问：动能和势能如何转换？能量守恒定律是什么？",
        "follow_up_strategies": ["strat_clarify_mechanics"],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_error_physics",
        "level_1_goal": "monitoring",
        "level_2_skill": "error_analysis",
        "level_3_context": "mechanics",
        "name": "物理错误分析",
        "description": "分析物理题目中的常见错误",
        "prompt_template": "学生解物理题出错。引导分析：{student_state}\n提问：你的受力分析是否完整？公式选择是否正确？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_analogy_physics",
        "level_1_goal": "core_guidance",
        "level_2_skill": "analogy",
        "level_3_context": "motion",
        "name": "物理类比策略",
        "description": "通过类比帮助学生理解物理概念",
        "prompt_template": "学生学习物理概念。使用类比：{concept}\n提问：速度就像走路的快慢，加速度就像起步的感觉。你有类似的体验吗？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_self_explain_physics",
        "level_1_goal": "core_guidance",
        "level_2_skill": "self_explanation",
        "level_3_context": "forces",
        "name": "物理自我解释",
        "description": "要求学生解释物理思路",
        "prompt_template": "学生解对了物理题。要求解释：\n提问：你能说说你的解题思路吗？为什么选择这个公式？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_guided_discovery_physics",
        "level_1_goal": "core_guidance",
        "level_2_skill": "guided_discovery",
        "level_3_context": "energy",
        "name": "物理引导发现",
        "description": "引导学生通过实验发现物理规律",
        "prompt_template": "引导发现：{concept}\n提问：如果释放一个小球从不同高度落下，你觉得落地速度会如何变化？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    # === 化学策略 ===
    {
        "id": "strat_clarify_reactions",
        "level_1_goal": "core_guidance",
        "level_2_skill": "concept_clarification",
        "level_3_context": "reactions",
        "name": "化学反应概念澄清",
        "description": "帮助学生理解化学反应类型",
        "prompt_template": "学生学习化学反应。引导理解：{concept}\n提问：化合反应和分解反应有什么区别？你能各举一个例子吗？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_clarify_mole",
        "level_1_goal": "core_guidance",
        "level_2_skill": "concept_clarification",
        "level_3_context": "mole_concept",
        "name": "摩尔概念澄清",
        "description": "帮助学生理解摩尔的概念",
        "prompt_template": "学生学习摩尔。引导理解：{concept}\n提问：摩尔是什么？阿伏伽德罗常数的含义？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_clarify_periodic",
        "level_1_goal": "core_guidance",
        "level_2_skill": "concept_clarification",
        "level_3_context": "periodic_table",
        "name": "元素周期表",
        "description": "帮助学生理解元素周期律",
        "prompt_template": "学生学习周期表。引导理解：{concept}\n提问：元素周期表的排列规律是什么？同一周期元素有什么共同点？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    # === 生物策略 ===
    {
        "id": "strat_clarify_cell",
        "level_1_goal": "core_guidance",
        "level_2_skill": "concept_clarification",
        "level_3_context": "cell_structure",
        "name": "细胞结构概念澄清",
        "description": "帮助学生理解细胞结构",
        "prompt_template": "学生学习细胞。引导理解：{concept}\n提问：动物细胞和植物细胞有什么区别？各细胞器的功能？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_clarify_genetics",
        "level_1_goal": "core_guidance",
        "level_2_skill": "concept_clarification",
        "level_3_context": "genetics",
        "name": "遗传概念澄清",
        "description": "帮助学生理解遗传基本概念",
        "prompt_template": "学生学习遗传。引导理解：{concept}\n提问：DNA和基因的关系是什么？遗传密码如何工作？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_clarify_ecology",
        "level_1_goal": "core_guidance",
        "level_2_skill": "concept_clarification",
        "level_3_context": "ecology",
        "name": "生态概念澄清",
        "description": "帮助学生理解生态系统",
        "prompt_template": "学生学习生态。引导理解：{concept}\n提问：食物链和食物网有什么区别？生态系统的稳定性如何维持？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    # === 语文策略 ===
    {
        "id": "strat_chinese_reading",
        "level_1_goal": "core_guidance",
        "level_2_skill": "concept_clarification",
        "level_3_context": "reading_comprehension",
        "name": "语文阅读理解",
        "description": "引导学生深入理解语文课文",
        "prompt_template": "学生学习语文阅读。引导理解：{concept}\n提问：这篇文章的中心思想是什么？作者的写作意图？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_chinese_writing",
        "level_1_goal": "core_guidance",
        "level_2_skill": "guided_discovery",
        "level_3_context": "essay_writing",
        "name": "语文写作引导",
        "description": "引导学生进行语文写作",
        "prompt_template": "学生进行语文写作。引导思考：{concept}\n提问：你想表达的核心观点是什么？有哪些论据可以支撑？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_chinese_classical",
        "level_1_goal": "core_guidance",
        "level_2_skill": "concept_clarification",
        "level_3_context": "classical_chinese",
        "name": "文言文学习",
        "description": "引导学生理解文言文",
        "prompt_template": "学生学习文言文。引导理解：{concept}\n提问：这段文言文的主旨是什么？关键字词如何解释？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_chinese_analysis",
        "level_1_goal": "monitoring",
        "level_2_skill": "error_analysis",
        "level_3_context": "reading_comprehension",
        "name": "语文分析错误",
        "description": "分析语文学习中的理解错误",
        "prompt_template": "学生语文理解有误。引导分析：{student_state}\n提问：你的理解和原文有什么偏差？能找到原文依据吗？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_chinese_self_explain",
        "level_1_goal": "core_guidance",
        "level_2_skill": "self_explanation",
        "level_3_context": "reading_comprehension",
        "name": "语文自我解释",
        "description": "要求学生解释语文理解",
        "prompt_template": "学生答对了语文题。要求解释：\n提问：你能说说你是如何理解这句话的吗？为什么这么理解？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    # === 英语策略 ===
    {
        "id": "strat_english_grammar",
        "level_1_goal": "core_guidance",
        "level_2_skill": "concept_clarification",
        "level_3_context": "grammar",
        "name": "英语语法概念澄清",
        "description": "帮助学生理解英语语法",
        "prompt_template": "学生学习英语语法。引导理解：{concept}\n提问：这个语法规则是什么？你能造一个句子吗？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_english_vocab",
        "level_1_goal": "core_guidance",
        "level_2_skill": "concept_clarification",
        "level_3_context": "vocabulary",
        "name": "英语词汇学习",
        "description": "帮助学生理解和记忆词汇",
        "prompt_template": "学生学习英语词汇。引导理解：{concept}\n提问：这个词的意思是什么？能想出同义词或反义词吗？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_english_reading",
        "level_1_goal": "core_guidance",
        "level_2_skill": "guided_discovery",
        "level_3_context": "reading_comprehension",
        "name": "英语阅读引导",
        "description": "引导学生进行英语阅读",
        "prompt_template": "学生进行英语阅读。引导理解：{concept}\n提问：这篇文章的主旨是什么？你从哪里看出来的？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    # === 编程策略 ===
    {
        "id": "strat_programming_debug",
        "level_1_goal": "monitoring",
        "level_2_skill": "error_analysis",
        "level_3_context": "debugging",
        "name": "编程调试策略",
        "description": "帮助学生调试代码错误",
        "prompt_template": "学生编程出错。引导调试：{student_state}\n提问：错误信息是什么？你觉得问题可能出在哪里？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_programming_algo",
        "level_1_goal": "core_guidance",
        "level_2_skill": "concept_clarification",
        "level_3_context": "algorithm",
        "name": "算法概念澄清",
        "description": "帮助学生理解算法设计",
        "prompt_template": "学生学习算法。引导理解：{concept}\n提问：这个算法的时间复杂度是多少？有什么优化方案？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
    {
        "id": "strat_programming_self_explain",
        "level_1_goal": "core_guidance",
        "level_2_skill": "self_explanation",
        "level_3_context": "algorithm",
        "name": "编程自我解释",
        "description": "要求学生解释代码实现",
        "prompt_template": "学生完成编程任务。要求解释：\n提问：你能解释你的代码实现了什么功能吗？为什么选择这种数据结构？",
        "follow_up_strategies": [],
        "escalation_threshold": 3,
        "de_escalation_threshold": 2,
        "version": "2.0.0",
        "is_active": True,
    },
]


class StrategyLibrary:
    """
    策略库

    MVP 实现：从内存加载策略模板
    后续版本将支持从数据库动态加载
    """

    _YAML_DIR = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "data", "strategies", "yaml_strategies"
    )

    def __init__(self):
        self._strategies: dict[str, dict] = {}
        self._load_built_in_strategies()
        self._load_yaml_strategies()

    def _load_built_in_strategies(self) -> None:
        """加载内置策略模板"""
        for strategy in _BUILT_IN_STRATEGIES:
            strategy_id = strategy.get("id")
            if strategy.get("is_active", True) and isinstance(strategy_id, str):
                self._strategies[strategy_id] = strategy
        logger.info(f"Loaded {len(self._strategies)} built-in strategy templates")

    def _load_yaml_strategies(self) -> None:
        """从 YAML 目录加载策略"""
        yaml_dir = self._YAML_DIR
        if os.path.isdir(yaml_dir):
            count = self.load_from_directory(yaml_dir)
            logger.info(f"Loaded {count} strategies from YAML files")

    def load_from_yaml(self, filepath: str) -> int:
        """从 YAML/JSON 文件加载策略"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict) or "strategies" not in data:
                logger.warning(f"No 'strategies' key found in {filepath}")
                return 0
            count = 0
            for strategy in data["strategies"]:
                if strategy.get("is_active", True) and "id" in strategy:
                    self._strategies[strategy["id"]] = strategy
                    count += 1
            logger.info(f"Loaded {count} strategies from {filepath}")
            return count
        except Exception as e:
            logger.error(f"Failed to load YAML file {filepath}: {e}")
            return 0

    def load_from_directory(self, dirpath: str) -> int:
        """从目录加载所有 YAML/JSON 策略文件"""
        total = 0
        if not os.path.isdir(dirpath):
            return 0
        for filename in sorted(os.listdir(dirpath)):
            if filename.endswith((".yaml", ".yml", ".json")):
                filepath = os.path.join(dirpath, filename)
                total += self.load_from_yaml(filepath)
        return total

    def get_strategy(self, strategy_id: str) -> Optional[dict]:
        """根据 ID 获取策略"""
        return self._strategies.get(strategy_id)

    def find_strategies(
        self,
        level_1_goal: Optional[str] = None,
        level_2_skill: Optional[str] = None,
        level_3_context: Optional[str] = None,
    ) -> list[dict]:
        """
        按分类条件查找策略

        Args:
            level_1_goal: 元认知目标 (planning, monitoring, evaluation, core_guidance)
            level_2_skill: 认知技能 (goal_setting, understanding_monitoring, etc.)
            level_3_context: 学科情境 (algebra_equation, essay_writing, etc.)

        Returns:
            符合条件的策略列表
        """
        results = []
        for strategy in self._strategies.values():
            if level_1_goal and strategy.get("level_1_goal") != level_1_goal:
                continue
            if level_2_skill and strategy.get("level_2_skill") != level_2_skill:
                continue
            if level_3_context and strategy.get("level_3_context") != level_3_context:
                continue
            results.append(strategy)
        return results

    def get_all_active_strategies(self) -> list[dict]:
        """获取所有活跃的策略"""
        return list(self._strategies.values())

    def search_by_keyword(self, keyword: str) -> list[dict]:
        """根据关键词搜索策略"""
        keyword = keyword.lower()
        results = []
        for strategy in self._strategies.values():
            if (
                keyword in strategy.get("name", "").lower()
                or keyword in strategy.get("description", "").lower()
                or keyword in strategy.get("prompt_template", "").lower()
            ):
                results.append(strategy)
        return results

    def add_strategy(self, strategy: dict) -> None:
        """添加新策略 (MVP 阶段仅支持内存添加)"""
        if "id" not in strategy:
            raise ValueError("Strategy must have an 'id' field")
        self._strategies[strategy["id"]] = strategy
        logger.info(f"Added new strategy: {strategy['id']}")

    def get_count(self) -> int:
        """获取策略总数"""
        return len(self._strategies)

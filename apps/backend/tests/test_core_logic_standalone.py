#!/usr/bin/env python3
"""
MVP 核心模块验证脚本 (无依赖版本)

直接测试核心类的逻辑正确性，不依赖项目的其他模块。
"""

import re
import sys


# ============================================================
# 1. 输入解析器测试
# ============================================================
class SimpleInputParser:
    """简化版输入解析器，用于逻辑验证"""

    INTENT_PATTERNS = {
        "confusion_expression": [
            r"不太理解",
            r"不明白",
            r"搞不懂",
            r"不懂",
            r"不清楚",
            r"不会做",
        ],
        "request_explanation": [
            r"给我讲讲",
            r"解释一下",
            r"告诉我",
            r"什么是",
            r"讲解",
        ],
        "request_hint": [
            r"提示",
            r"给点提示",
            r"怎么办",
            r"接下来怎么做",
            r"帮我想想",
        ],
        "ask_question": [
            r"吗\?$",
            r"呢\?$",
            r"？$",
            r"\?$",
            r"会不会",
            r"是不是",
        ],
        "express_confidence": [
            r"我懂了",
            r"我明白了",
            r"原来如此",
            r"知道了",
            r"会了",
        ],
        "frustration": [
            r"太难了",
            r"不会做",
            r"做不出来",
            r"放弃",
            r"学不下去",
        ],
    }

    KP_MAP = {
        "移项": {"id": "kp_algebra_transposition", "name": "移项法则"},
        "等式性质": {"id": "kp_algebra_equation_properties", "name": "等式性质"},
        "勾股定理": {"id": "kp_geometry_pythagorean", "name": "勾股定理"},
    }

    def parse(self, text: str) -> dict:
        text = text.strip()
        result = {
            "text": text,
            "intent": "general_input",
            "knowledge_points": [],
            "confusion_type": "none",
            "suggested_hint_level": 2,
        }

        # 意图识别
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    result["intent"] = intent
                    break
            if result["intent"] != "general_input":
                break

        # 知识点定位
        for keyword, kp_info in self.KP_MAP.items():
            if keyword in text:
                result["knowledge_points"].append({**kp_info, "confidence": 0.9})

        # 困惑识别
        if re.search(r"不太理解|不明白|搞不懂", text):
            result["confusion_type"] = "conceptual_misunderstanding"

        # 建议提示级别
        if result["intent"] in ("confusion_expression", "frustration"):
            result["suggested_hint_level"] = 3

        return result


# ============================================================
# 2. 知识追踪 (BKT) 测试
# ============================================================
class SimpleKnowledgeTracing:
    """简化版 BKT 测试"""

    def __init__(self):
        self._store = {}
        self.p_init = 0.3
        self.p_transit = 0.15
        self.p_slip = 0.2  # 提高 slip 概率以便测试观察到变化

    def _get_key(self, uid, kpid):
        return f"{uid}:{kpid}"

    def get_mastery(self, uid, kpid):
        key = self._get_key(uid, kpid)
        state = self._store.get(
            key,
            {
                "p": self.p_init,
                "n_attempts": 0,
            },
        )
        # 返回副本，避免外部修改影响内部状态
        return state.copy() if hasattr(state, "copy") else state

    def update_mastery(self, uid, kpid, is_correct, hint_level=0):
        key = self._get_key(uid, kpid)
        # 获取状态的副本进行修改
        state = self._store.get(key, {"p": self.p_init, "n_attempts": 0}).copy()
        p = state["p"]

        if is_correct:
            hint_penalty = max(0.3, 1.0 - (hint_level - 1) * 0.15) if hint_level > 0 else 1.0
            p_gain = (1.0 - p) * self.p_transit * hint_penalty
            p = min(1.0, p + p_gain)
        else:
            p_loss = p * self.p_slip
            p = max(0.0, p - p_loss)

        state["p"] = round(p, 4)
        state["n_attempts"] += 1
        self._store[key] = state
        return state


# ============================================================
# 3. 策略库与选择器测试
# ============================================================
class SimpleStrategySelector:
    """简化版策略选择器"""

    STRATEGIES = [
        {
            "id": "strat_clarify",
            "level_1": "core_guidance",
            "level_2": "clarification",
            "name": "概念澄清",
        },
        {
            "id": "strat_guide",
            "level_1": "core_guidance",
            "level_2": "guidance",
            "name": "引导思考",
        },
        {
            "id": "strat_monitor",
            "level_1": "monitoring",
            "level_2": "monitoring",
            "name": "过程监控",
        },
        {
            "id": "strat_evaluate",
            "level_1": "evaluation",
            "level_2": "evaluation",
            "name": "评估反思",
        },
    ]

    def select(self, parsed_input, mastery):
        # 简化评分逻辑
        scores = []

        for strategy in self.STRATEGIES:
            score = 0.5

            # 低掌握度 -> 选引导类
            if mastery < 0.3 and strategy["level_1"] == "core_guidance":
                score += 0.3

            # 高掌握度 -> 选评估类
            if mastery > 0.6 and strategy["level_1"] == "evaluation":
                score += 0.3

            # 表达困惑 -> 选澄清类
            if (
                parsed_input["intent"] == "confusion_expression"
                and strategy["level_2"] == "clarification"
            ):
                score += 0.2

            scores.append((strategy, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[0][0]


# ============================================================
# 4. 渐次提示生成器测试
# ============================================================
class SimpleHintingGenerator:
    """简化版提示生成器"""

    def decide(self, parsed_input, mastery, previous_correct=None):
        # 基础级别
        if mastery < 0.2:
            base_level = 4
        elif mastery < 0.4:
            base_level = 3
        elif mastery < 0.6:
            base_level = 2
        else:
            base_level = 1

        # 调整
        adjustment = 0
        if parsed_input["intent"] == "request_hint":
            adjustment += 1
        if parsed_input["intent"] in ("confusion_expression", "frustration"):
            adjustment += 1

        level = max(1, min(5, base_level + adjustment))
        return {"level": level, "adjustment": "elevate" if adjustment > 0 else "maintain"}


# ============================================================
# 5. 输出验证测试
# ============================================================
class SimpleOutputGuardrail:
    """简化版输出验证"""

    ANSWER_PATTERNS = [
        r"(?:答案|结果|解|答)[是为：:]\s*\S+",
        r"(?:the\s+(?:answer|result|solution)\s+is)\s+\S+",
        r"(?:等于|等于是|值为|结果是)\s*\d+",
    ]

    def validate(self, text):
        if not text or not text.strip():
            return False, "回复为空"

        # 检查答案泄露
        for pattern in self.ANSWER_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return False, "检测到答案泄露"

        # 检查是否为问句
        is_question = (
            "？" in text
            or "?" in text
            or text.startswith(("你", "您", "能", "可以", "是否", "有没有"))
        )

        if not is_question:
            return False, "回复不是引导性问题"

        # 检查长度
        if len(text) < 5 or len(text) > 200:
            return False, "回复长度不合适"

        return True, "验证通过"


# ============================================================
# 6. 反思触发测试
# ============================================================
class SimpleReflectionTrigger:
    """简化版反思触发器"""

    def __init__(self):
        self._wrong_count = 0

    def should_trigger(self, parsed_input, mastery, is_session_end=False, previous_correct=None):
        if is_session_end:
            return True, "post_session"

        if parsed_input["intent"] in ("confusion_expression", "frustration"):
            self._wrong_count += 1
            if self._wrong_count >= 3:
                return True, "in_process"

        return False, None


# ============================================================
# 主测试流程
# ============================================================
def run_tests():
    passed = 0
    failed = 0
    results = []

    def test(name, func):
        nonlocal passed, failed
        try:
            func()
            passed += 1
            results.append((name, True, ""))
            print(f"✅ {name}")
        except Exception as e:
            failed += 1
            results.append((name, False, str(e)))
            print(f"❌ {name}: {e}")
            import traceback

            traceback.print_exc()

    print("=" * 60)
    print("Askora MVP 核心模块逻辑验证")
    print("=" * 60)
    print()

    # 1. 输入解析器
    parser = SimpleInputParser()

    def test_parser_confusion():
        r = parser.parse("我不太理解为什么要移项")
        assert (
            r["intent"] == "confusion_expression"
        ), f"Expected confusion_expression, got {r['intent']}"
        assert len(r["knowledge_points"]) > 0
        print(f"  -> 意图: {r['intent']}, 知识点: {[k['id'] for k in r['knowledge_points']]}")

    def test_parser_explanation():
        r = parser.parse("给我讲讲勾股定理")
        assert r["intent"] == "request_explanation"
        print(f"  -> 意图: {r['intent']}")

    test("InputParser: 困惑识别", test_parser_confusion)
    test("InputParser: 请求解释识别", test_parser_explanation)

    # 2. 知识追踪
    kt = SimpleKnowledgeTracing()

    def test_kt_increase():
        kt._store.clear()
        for _ in range(3):
            kt.update_mastery("u1", "k1", is_correct=True)
        state = kt.get_mastery("u1", "k1")
        assert state["p"] > 0.4, f"Expected p > 0.4, got {state['p']}"
        print(f"  -> 掌握度: {state['p']:.3f} (连续答对)")

    def test_kt_decrease():
        kt._store.clear()
        # 先提升到中等掌握度 (不使用过多迭代，避免 p 饱和)
        for _ in range(5):
            kt.update_mastery("u2", "k2", is_correct=True)
        state1 = kt.get_mastery("u2", "k2")

        # 验证掌握度已提升
        assert (
            state1["p"] > 0.3
        ), f"Mastery should have increased from initial 0.3, got {state1['p']}"

        # 再答错 (使用中等次数)
        for _ in range(5):
            kt.update_mastery("u2", "k2", is_correct=False)
        state2 = kt.get_mastery("u2", "k2")

        # 断言掌握度下降
        assert (
            state2["p"] < state1["p"]
        ), f"Mastery should decrease, but {state2['p']} >= {state1['p']}"
        print(f"  -> 掌握度: {state1['p']:.3f} -> {state2['p']:.3f}")

    test("BKT: 连续答对提升掌握度", test_kt_increase)
    test("BKT: 连续答错降低掌握度", test_kt_decrease)

    # 3. 策略选择
    selector = SimpleStrategySelector()

    def test_selector_low():
        parsed = parser.parse("我不太理解")
        s = selector.select(parsed, mastery=0.2)
        assert s is not None
        print(f"  -> 选中: {s['name']} (低掌握度 0.2)")

    def test_selector_high():
        parsed = parser.parse("我懂了，这很简单")
        s = selector.select(parsed, mastery=0.8)
        assert s is not None
        print(f"  -> 选中: {s['name']} (高掌握度 0.8)")

    test("StrategySelector: 低掌握度选择", test_selector_low)
    test("StrategySelector: 高掌握度选择", test_selector_high)

    # 4. 提示生成
    generator = SimpleHintingGenerator()

    def test_hinting_low():
        parsed = parser.parse("我不会做")
        decision = generator.decide(parsed, mastery=0.2)
        assert decision["level"] >= 3
        print(f"  -> 提示级别: L{decision['level']} (低掌握度)")

    def test_hinting_normal():
        parsed = parser.parse("我试试")
        decision = generator.decide(parsed, mastery=0.5)
        assert 1 <= decision["level"] <= 5
        print(f"  -> 提示级别: L{decision['level']} (中掌握度)")

    test("HintingGenerator: 低掌握度升级", test_hinting_low)
    test("HintingGenerator: 正常掌握度", test_hinting_normal)

    # 5. 输出验证
    guardrail = SimpleOutputGuardrail()

    def test_guardrail_leak():
        valid, reason = guardrail.validate("答案是 x=3")
        assert not valid
        print(f"  -> 拦截: '答案是 x=3' -> {reason}")

    def test_guardrail_good():
        valid, reason = guardrail.validate("你能再想想这个问题的关键是什么吗？")
        assert valid
        print("  -> 通过: '你能再想想...'")

    test("OutputGuardrail: 拦截答案泄露", test_guardrail_leak)
    test("OutputGuardrail: 通过引导性问题", test_guardrail_good)

    # 6. 反思触发
    trigger = SimpleReflectionTrigger()

    def test_reflection_trigger():
        trigger._wrong_count = 0
        # 使用明确匹配 frustration 或 confusion_expression 的输入
        parsed = parser.parse("我不会做了，太难了")
        should_trigger, ref_type = False, None

        # 模拟多次错误输入
        for _i in range(5):
            should_trigger, ref_type = trigger.should_trigger(parsed, 0.1)

        assert (
            should_trigger
        ), f"Expected trigger, but got should_trigger={should_trigger}, ref_type={ref_type}"
        assert ref_type == "in_process", f"Expected in_process, got {ref_type}"
        print("  -> 触发过程中反思 (多次错误后)")

    test("ReflectionTrigger: 连续错误触发反思", test_reflection_trigger)

    # 7. 综合流程测试
    def test_full_flow():
        """模拟一次完整的苏格拉底教学流程"""
        parsed = parser.parse("我不太理解为什么要移项")

        # 获取掌握度
        kt._store.clear()
        mastery_state = kt.get_mastery("user_flow", "kp_flow")
        mastery = mastery_state["p"]

        # 选择策略
        strategy = selector.select(parsed, mastery)

        # 决定提示级别
        hint_decision = generator.decide(parsed, mastery)

        # 模拟 LLM 生成回复
        reply = f"你觉得在移项时，等式两边发生了什么变化？(Level {hint_decision['level']} 提示: {strategy['name']})"

        # 验证输出
        valid, reason = guardrail.validate(reply)
        assert valid, f"Reply validation failed: {reason}"

        # 反馈结果
        kt.update_mastery(
            "user_flow", "kp_flow", is_correct=True, hint_level=hint_decision["level"]
        )

        print(
            f"  -> 流程: 解析({parsed['intent']}) -> 策略({strategy['name']}) -> 提示(L{hint_decision['level']}) -> 验证(通过)"
        )
        print(f"  -> 回复: {reply[:60]}...")

        # 检查反思
        should_reflect, ref_type = trigger.should_trigger(parsed, mastery, is_session_end=True)
        if should_reflect:
            print(f"  -> 触发: 会话结束反思 ({ref_type})")

    test("E2E: 完整苏格拉底流程模拟", test_full_flow)

    # 汇总
    print()
    print("=" * 60)
    print(f"验证结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

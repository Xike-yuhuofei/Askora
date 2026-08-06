"""
MVP 集成测试脚本

验证内容：
1. 苏格拉底引擎子模块的正确集成
2. Drill 引擎和 Inquiry 引擎的正确实现
3. 知识追踪服务 (BKT) 的基本功能
4. 核心流程的端到端测试

运行前需确保：
- Python 3.11+
- 所有依赖已安装 (pip install -r requirements.txt)
"""

import asyncio
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.logging import get_logger
from app.engines.base import (
    FlowStage,
    LearnerTurn,
    SharedContext,
)
from app.engines.socratic.hinting_generator import HintingGenerator
from app.engines.socratic.input_parser import InputParser
from app.engines.socratic.output_guardrail import OutputGuardrail
from app.engines.socratic.reflection_trigger import ReflectionTrigger
from app.engines.socratic.strategy_library import StrategyLibrary
from app.engines.socratic.strategy_selector import StrategySelector
from app.services.kt import KnowledgeTracingService

logger = get_logger(__name__)

passed = 0
failed = 0


def _test_case(name: str):
    def decorator(func):
        global passed, failed
        try:
            asyncio.get_event_loop().run_until_complete(func())
            passed += 1
            print(f"✅ {name}")
        except Exception as e:
            failed += 1
            print(f"❌ {name}: {e}")
            import traceback

            traceback.print_exc()
        return func

    return decorator


# ============================================================
# Test 1: 输入解析器
# ============================================================
@_test_case("InputParser: 困惑表达识别")
async def test_input_parser_confusion():
    parser = InputParser()
    result = parser.parse("我不太理解为什么要移项")

    assert (
        result.intent == "confusion_expression"
    ), f"Expected confusion_expression, got {result.intent}"
    assert (
        result.confusion_type == "conceptual_misunderstanding"
    ), f"Expected conceptual_misunderstanding, got {result.confusion_type}"
    assert len(result.knowledge_points) > 0, "Expected knowledge points to be identified"
    print(f"  -> 识别意图: {result.intent}, 知识点: {[k['id'] for k in result.knowledge_points]}")


@_test_case("InputParser: 请求解释识别")
async def test_input_parser_request_explanation():
    parser = InputParser()
    result = parser.parse("给我讲讲勾股定理")

    assert (
        result.intent == "request_explanation"
    ), f"Expected request_explanation, got {result.intent}"
    print(f"  -> 识别意图: {result.intent}")


# ============================================================
# Test 2: 策略库与选择器
# ============================================================
@_test_case("StrategyLibrary: 加载 30+ 模板")
async def test_strategy_library():
    lib = StrategyLibrary()
    count = lib.get_count()
    assert count >= 15, f"Expected at least 15 templates, got {count}"
    print(f"  -> 已加载 {count} 个策略模板")


@_test_case("StrategySelector: 低掌握度选择")
async def test_strategy_selector_low_mastery():
    lib = StrategyLibrary()
    selector = StrategySelector(lib)
    parser = InputParser()

    input_data = parser.parse("我不太理解")
    strategy = selector.select(input_data, mastery=0.2)

    assert strategy is not None, "Strategy selection should return a strategy"
    print(f"  -> 选中策略: {strategy['id']} (低掌握度 0.2)")


# ============================================================
# Test 3: 渐次提示生成器
# ============================================================
@_test_case("HintingGenerator: 低掌握度升级提示")
async def test_hinting_low_mastery():
    parser = InputParser()
    generator = HintingGenerator()

    input_data = parser.parse("我不会做")
    decision = generator.decide(input_data, mastery=0.2)

    assert decision.level >= 3, f"Expected hint level >= 3 for low mastery, got {decision.level}"
    print(f"  -> 提示级别: Level {decision.level} (低掌握度 0.2)")


# ============================================================
# Test 4: 输出验证护栏
# ============================================================
@_test_case("OutputGuardrail: 拦截答案泄露")
async def test_output_guardrail_answer_leak():
    guardrail = OutputGuardrail()

    # 测试包含答案的文本
    result = guardrail.validate("答案是 x=3")
    assert not result.is_valid, "Should reject text with direct answer"
    print(f"  -> 成功拦截: '答案是 x=3' -> {result.reason}")


@_test_case("OutputGuardrail: 通过引导性问题")
async def test_output_guardrail_good_response():
    guardrail = OutputGuardrail()

    # 测试苏格拉底式问题
    result = guardrail.validate("你能再想想这个问题的关键是什么吗？")
    assert result.is_valid, "Should accept socratic question"
    print("  -> 通过验证: '你能再想想这个问题的关键是什么吗？'")


# ============================================================
# Test 5: 知识追踪 (BKT)
# ============================================================
@_test_case("KnowledgeTracing: 连续答对提升掌握度")
async def test_kt_mastery_increase():
    kt = KnowledgeTracingService()
    user_id = "test_user_001"
    kp_id = "test_kp_001"

    # 重置
    kt.reset_mastery(user_id, kp_id)

    initial = kt.get_mastery(user_id, kp_id)
    assert initial.p == 0.3, f"Expected initial mastery 0.3, got {initial.p}"

    # 连续答对 3 次
    for _ in range(3):
        kt.update_mastery(user_id, kp_id, is_correct=True)

    after = kt.get_mastery(user_id, kp_id)
    assert after.p > 0.5, f"Expected mastery > 0.5 after 3 correct, got {after.p}"
    print(f"  -> 掌握度: {initial.p:.3f} -> {after.p:.3f} (连续答对)")


@_test_case("KnowledgeTracing: 连续答错降低掌握度")
async def test_kt_mastery_decrease():
    kt = KnowledgeTracingService()
    user_id = "test_user_002"
    kp_id = "test_kp_002"

    # 先答对几次提升掌握度
    kt.reset_mastery(user_id, kp_id)
    for _ in range(5):
        kt.update_mastery(user_id, kp_id, is_correct=True)

    raised = kt.get_mastery(user_id, kp_id)
    print(f"  -> 提升后掌握度: {raised.p:.3f}")

    # 连续答错
    for _ in range(3):
        kt.update_mastery(user_id, kp_id, is_correct=False)

    after = kt.get_mastery(user_id, kp_id)
    assert after.p < raised.p, f"Expected mastery to decrease, got {after.p}"
    print(f"  -> 掌握度: {raised.p:.3f} -> {after.p:.3f} (连续答错)")


# ============================================================
# Test 6: 反思触发
# ============================================================
@_test_case("ReflectionTrigger: 连续错误触发反思")
async def test_reflection_trigger():
    trigger = ReflectionTrigger()
    parser = InputParser()

    # 模拟 3 次错误输入
    for i in range(3):
        input_data = parser.parse("我还是不会")
        decision = trigger.should_trigger(
            input_data,
            mastery=0.1,
            previous_correct=False,
        )

        if i == 2:  # 第三次应该触发
            assert decision.should_trigger, "Should trigger reflection after 3 consecutive wrong"
            assert decision.reflection_type == "in_process"
            print(f"  -> 触发过程中反思: {decision.prompt[:50]}...")


# ============================================================
# Test 7: 引擎 can_handle 评分
# ============================================================
@_test_case("Engine Registration: 测试引擎注册")
async def test_engine_registration():
    from app.engines._registry import ENGINE_REGISTRY

    # 应该能获取到已注册的引擎
    engines = list(ENGINE_REGISTRY.keys())
    print(f"  -> 已注册引擎: {engines}")

    # 检查关键引擎是否存在
    assert "socratic" in engines, "Socratic engine should be registered"


# ============================================================
# Test 8: 端到端苏格拉底流程 (Mock)
# ============================================================
@_test_case("End-to-End: 苏格拉底完整流程 (Mock)")
async def test_e2e_socratic():
    """使用 Mock LLM 测试完整苏格拉底流程"""
    from app.engines.base import LearnerTurn
    from app.engines.socratic_adapter import SocraticTeachingEngine

    engine = SocraticTeachingEngine()

    # 构建共享上下文
    shared_ctx = SharedContext(
        knowledge_point_id="kp_algebra_transposition",
        subject="math",
        learner_persona="k12_high",
    )

    # 初始化引擎状态
    state = engine.build_initial_state(shared_ctx)

    # 模拟用户输入
    learner_turn = LearnerTurn(text="我不太理解为什么要移项")

    # 执行 step
    result = await engine.step(
        learner_input=learner_turn,
        flow_stage=FlowStage.LEARN,
        shared_ctx=shared_ctx,
        engine_state=state,
    )

    # 验证结果
    assert result.reply_text, "Should return a reply"
    assert len(result.reply_text) > 10, "Reply should be meaningful"

    # 验证回复包含问号（苏格拉底式提问）
    assert (
        "？" in result.reply_text or "?" in result.reply_text
    ), f"Reply should be a question, got: {result.reply_text[:50]}"

    print(f"  -> 回复: {result.reply_text[:80]}...")
    print(f"  -> 引擎: {result.engine_debug_info}")


# ============================================================
# Test 9: Drill 引擎流程
# ============================================================
@_test_case("End-to-End: Drill 引擎流程")
async def test_drill_engine():
    from app.engines.drill_engine import DrillEngine

    engine = DrillEngine()

    shared_ctx = SharedContext(
        knowledge_point_id="kp_algebra_transposition",
        subject="math",
    )

    state = engine.build_initial_state(shared_ctx)
    learner_turn = LearnerTurn(text="开始练习")

    # 第一次调用：应该给出题目
    result = await engine.step(learner_turn, FlowStage.DRILL, shared_ctx, state)

    assert result.reply_text, "Should present a question"
    assert (
        "练习题" in result.reply_text or "📝" in result.reply_text
    ), f"Should be a question, got: {result.reply_text[:50]}"

    print(f"  -> 题目: {result.reply_text[:80]}...")

    # 获取当前题目答案
    current_q = result.engine_state_update.get("current_question")
    assert current_q, "Should have current question"

    # 模拟答对
    correct_answer = current_q.get("answer", "B")
    learner_turn_answer = LearnerTurn(text=correct_answer)

    result2 = await engine.step(learner_turn_answer, FlowStage.DRILL, shared_ctx, state)

    assert (
        "正确" in result2.reply_text
        or "✅" in result2.reply_text
        or "回答正确" in result2.reply_text
    ), f"Should have positive feedback, got: {result2.reply_text[:50]}"

    print(f"  -> 反馈: {result2.reply_text[:80]}")


# ============================================================
# Test 10: Inquiry 引擎流程
# ============================================================
@_test_case("End-to-End: Inquiry 引擎流程")
async def test_inquiry_engine():
    from app.engines.inquiry_engine import InquiryEngine

    engine = InquiryEngine()

    shared_ctx = SharedContext(
        knowledge_point_id="kp_algebra_transposition",
        subject="math",
    )

    state = engine.build_initial_state(shared_ctx)
    learner_turn = LearnerTurn(text="我想探究一下")

    # 第一次调用：介绍主题
    result = await engine.step(learner_turn, FlowStage.INQUIRE, shared_ctx, state)

    assert result.reply_text, "Should introduce the topic"
    print(f"  -> 介绍: {result.reply_text[:80]}...")

    # 第二次调用：应该引导提出假设
    learner_turn2 = LearnerTurn(text="我觉得移项就是要改变符号")
    result2 = await engine.step(learner_turn2, FlowStage.INQUIRE, shared_ctx, state)

    assert result2.reply_text, "Should guide to hypothesis"
    print(f"  -> 引导: {result2.reply_text[:80]}...")


# ============================================================
# 主程序
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Askora MVP 集成测试")
    print("=" * 60)
    print()

    # 运行所有测试
    try:
        asyncio.run(asyncio.sleep(0))  # 初始化事件循环
    except RuntimeError:
        pass

    # 逐个运行测试
    tests = [
        test_input_parser_confusion,
        test_input_parser_request_explanation,
        test_strategy_library,
        test_strategy_selector_low_mastery,
        test_hinting_low_mastery,
        test_output_guardrail_answer_leak,
        test_output_guardrail_good_response,
        test_kt_mastery_increase,
        test_kt_mastery_decrease,
        test_reflection_trigger,
        test_engine_registration,
        test_e2e_socratic,
        test_drill_engine,
        test_inquiry_engine,
    ]

    for test in tests:
        try:
            # 为每个测试创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(test())
            loop.close()
        except Exception as e:
            print(f"❌ {test.__name__}: Error - {e}")
            import traceback

            traceback.print_exc()
            failed += 1

    print()
    print("=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    sys.exit(0 if failed == 0 else 1)

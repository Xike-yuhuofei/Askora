# HintingGenerator 增强计划

## 目标
增强 `/Users/xike/Documents/Docs/Askora/apps/backend/app/engines/socratic/hinting_generator.py`，添加五大功能。

## 变更清单

### 1. 新增 `generate_hint_content(level, concept, student_state) -> str` 方法
- 为五个级别各生成实际的提示文本
- Level 1: 元认知引导（思考核心概念）
- Level 2: 概念澄清（定义与特征）
- Level 3: 策略提示（已知条件/目标/路径）
- Level 4: 结构提示（识别-分析-建立联系）
- Level 5: 定向提示（具体方面/角度/特征）

### 2. 动态升降级增强
- 新增 `_consecutive_no_response` 和 `_consecutive_partial` 计数器
- 新增 `classify_response(input: ParsedInput) -> str` 方法，返回 correct/wrong/no_response/partial/asking_for_help
- 新增 `_response_classification` 历史记录
- 在 `_calculate_adjustment` 中增加精细调整逻辑：
  - 连续 2 次 wrong → 升级 1 级
  - 连续 3+ 次 wrong → 升级 2 级
  - 学生主动求助 → 立即跳至 Level 4-5
  - 连续 2 次 correct → 降级 1 级
  - 学生表达自信且掌握度高 → 降至 Level 1-2
  - 沮丧情绪 → 升级 1 级
  - "I don't understand" 明确表述 → 升至 Level 4

### 3. 新增 `get_hint_progression() -> list[dict]` 方法
- 返回完整的提示决策历史，用于分析

### 4. 概念感知提示
- 修改 `decide` 方法签名，增加可选 `concept: str` 参数
- 提示内容可根据概念定制

### 5. 新增 `compute_hint_text` 方法
- 接收 HintDecision + concept + context，返回实际要发送给学生的提示文本

## 实施步骤
1. 更新导入和类常量
2. 扩展 `__init__`，添加新的计数器和状态
3. 添加 `classify_response` 方法
4. 添加 `generate_hint_content` 方法
5. 添加 `get_hint_progression` 方法
6. 添加 `compute_hint_text` 方法
7. 修改 `decide` 方法，增加 concept 参数，调用 classify_response 和新的调整逻辑
8. 修改 `_calculate_adjustment`，增加精细调整规则
9. 更新 `reset` 方法

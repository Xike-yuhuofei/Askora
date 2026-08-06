# HintingGenerator 增强实施计划

## 概述
对 `hinting_generator.py` 进行以下 7 项增强。

---

## 1. 添加 `classify_response()` 方法
- **位置**: 在 `get_current_level()` 之后
- **签名**: `classify_response(parsed_input: ParsedInput, previous_correct: Optional[bool]) -> str`
- **返回值**: `"correct"`, `"wrong"`, `"no_response"`, `"partial"`, `"asking_for_help"`
- **逻辑**:
  - `intent == "request_hint"` → `"asking_for_help"`
  - `intent == "confusion_expression"` 或 `emotional_state == "frustrated"` → `"asking_for_help"`
  - `previous_correct == True` → `"correct"`
  - `previous_correct == False` → `"wrong"`
  - 文本过短或为空 → `"no_response"`
  - 包含部分正确但犹豫的表达 → `"partial"`
  - 默认 → `"no_response"`

## 2. 添加 `generate_hint_content()` 方法
- **位置**: 在 `classify_response()` 之后
- **签名**: `generate_hint_content(level: int, concept: str, student_state: str = "") -> str`
- **逻辑**: 为 5 个级别生成中文提示文本

## 3. 添加 `get_hint_progression()` 方法
- **位置**: 在 `generate_hint_content()` 之后
- **签名**: `get_hint_progression() -> list[dict]`
- **逻辑**: 将 `_history` 中的 `HintDecision` 对象转为 dict 返回

## 4. 修改 `decide()` 方法
- **新增参数**: `concept: str = ""`
- **行为**: 在决策过程中调用 `compute_hint_text()` 生成实际提示文本

## 5. 重写 `_calculate_adjustment()` 方法
- **新逻辑**:
  - 连续错误 ≥ 2 → +1 level
  - 连续错误 ≥ 3 → +2 levels
  - `intent == "request_hint"` 或学生求助 → 跳到 level 4（直接设置 adjustment 使结果为 4）
  - 连续正确 ≥ 2 → -1 level
  - `emotional_state == "frustrated"` → +1 level
  - 明确说 "不懂" / "不理解" → 跳到 level 4

## 6. 添加 `compute_hint_text()` 方法
- **位置**: 在 `_calculate_adjustment()` 之后
- **签名**: `compute_hint_text(decision: HintDecision, concept: str) -> str`
- **逻辑**: 调用 `generate_hint_content()` 并结合 decision 信息返回最终提示文本

## 7. 更新 `reset()` 方法
- **新增重置**: 新增的计数器（如 `_consecutive_help_requests` 等）

---

## 实施步骤
1. 添加新计数器到 `__init__`
2. 添加 `classify_response()`
3. 添加 `generate_hint_content()`
4. 添加 `get_hint_progression()`
5. 添加 `compute_hint_text()`
6. 修改 `decide()` 签名和实现
7. 重写 `_calculate_adjustment()`
8. 更新 `reset()`

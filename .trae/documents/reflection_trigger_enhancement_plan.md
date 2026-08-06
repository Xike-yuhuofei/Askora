# Reflection Trigger 增强计划

## 目标
增强 `reflection_trigger.py`，实现更精细的反思触发逻辑，包括三种模式的特定触发条件、结构化提示、冷却机制和会话状态追踪。

---

## 变更概览

### 1. 新增 `ReflectionSession` 数据类

在 `ReflectionDecision` 之后添加，用于追踪每次会话的反思状态：

```python
@dataclass
class ReflectionSession:
    triggers: list[ReflectionType]       # 已触发的反思类型列表
    cooldown_until: dict[ReflectionType, int]  # 各类型冷却结束的轮次
    stall_reasons: list[str]             # 过程中反思的停滞原因记录
```

### 2. 新增类常量

```python
COOLDOWN_TURNS = 10          # 同一类型反思的冷却轮次
MAX_REFLECTIONS_PER_SESSION = 3  # 每次会话最多触发次数
POST_SESSION_MIN_TURNS = 8   # 事后反思最小轮次
MASTERY_LOW_RANGE = (0.3, 0.6)  # 自我解释的掌握度区间
```

### 3. 增强三种反思模式

#### a) 事后反思 (Post-session)
- **触发条件**: `is_session_end` 且 `_session_turns >= 8` 且至少有一个知识点被涉及
- **新增方法**: `generate_structured_reflection(mastery_map: dict, topics_covered: list[str]) -> str`
  - 生成结构化提示，包含四个维度：
    1. 你学到了什么？
    2. 哪些策略有效/无效？
    3. 下次会有什么不同做法？
    4. 还有哪些未解答的问题？

#### b) 过程中反思 (In-process)
- **触发条件**: 3+ 次连续错误 或 5+ 轮无进展 或 学生表达挫败感
- **新增方法**: `classify_stall_reason(parsed_input: ParsedInput, consecutive_wrong: int, progress_made: bool) -> str`
  - 返回停滞原因分类：
    - `"repeated_errors"`: 连续错误
    - `"no_progress"`: 无进展
    - `"frustration"`: 挫败感表达
  - 不同原因使用不同提示模板

#### c) 自我解释 (Self-explanation)
- **触发条件**: 答对但掌握度在 0.3-0.6 区间 或 首次答对（可能是猜测）
- **新增方法**: `should_self_explain(previous_correct: bool, mastery: float, attempt_count: int) -> tuple[bool, str]`
  - 返回 `(是否触发, 子模式)`：
    - `"deep_explanation"`: 答对但掌握度低 → "能请你详细说说解题过程吗？"
    - `"alternative_method"`: 首次答对 → "能用另一种方法解这道题吗？"

### 4. 反思时机优化

在 `should_trigger` 方法中增加：
- 冷却检查：`_reflection_session.cooldown_until` 中的类型在冷却期内不可再次触发
- 最大次数限制：`len(_reflection_session.triggers) < MAX_REFLECTIONS_PER_SESSION`
- 触发后更新冷却：`cooldown_until[type] = current_turn + COOLDOWN_TURNS`

### 5. 现有功能保留

- 保留 `ReflectionType` 枚举、`ReflectionDecision` 数据类
- 保留 `should_trigger`、`_create_reflection_decision`、`_generate_reflection_prompt` 等方法
- 保留 `reset_session` 和 `reset` 方法（需扩展以重置新字段）

---

## 实施步骤

1. 添加新的类常量（`COOLDOWN_TURNS`、`MAX_REFLECTIONS_PER_SESSION` 等）
2. 添加 `ReflectionSession` 数据类
3. 在 `__init__` 中初始化 `_reflection_session` 和 `_current_turn`
4. 新增 `generate_structured_reflection` 方法
5. 新增 `classify_stall_reason` 方法
6. 新增 `should_self_explain` 方法
7. 增强 `should_trigger` 方法的触发逻辑和时机控制
8. 扩展 `_generate_reflection_prompt` 支持新的提示类型
9. 更新 `reset_session` 以重置新增状态

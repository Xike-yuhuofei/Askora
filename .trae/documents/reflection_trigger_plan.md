# ReflectionTrigger 修改计划

## 变更概述
对 `reflection_trigger.py` 进行以下 8 项修改，增强反思触发的精细化控制能力。

---

## 修改清单

### 1. 添加 `ReflectionSession` 数据类（第 36 行之后）
在 `ReflectionDecision` 之后、`ReflectionTrigger` 类之前插入新的数据类：

```python
@dataclass
class ReflectionSession:
    """会话级反思状态跟踪"""
    cooldown_turns: int = 0
    reflections_triggered: int = 0
    last_reflection_turn: int = 0
    stall_reason: Optional[str] = None
```

### 2. 添加三个新常量（`ReflectionTrigger` 类内部）
在现有常量后添加：

```python
COOLDOWN_TURNS = 10        # 两次反思间的冷却回合
MAX_REFLECTIONS_PER_SESSION = 3  # 单会话最大反思次数
POST_SESSION_MIN_TURNS = 8  # 事后反思所需最小回合
```

### 3. 添加 `classify_stall_reason` 方法
```python
def classify_stall_reason(
    self,
    parsed_input: ParsedInput,
    consecutive_wrong: int,
    progress_made: float,
) -> str:
    """分类学习停滞原因"""
    if consecutive_wrong >= self.MAX_WRONG_BEFORE_REFLECTION:
        return "repeated_errors"
    if progress_made < 0.1:
        return "no_progress"
    if parsed_input.emotion in ("frustrated", "confused"):
        return "frustration"
    return "no_progress"
```

### 4. 添加 `should_self_explain` 方法
```python
def should_self_explain(
    self,
    previous_correct: bool,
    mastery: float,
    attempt_count: int,
) -> tuple[bool, str]:
    """判断是否应触发自我解释"""
    if not previous_correct:
        return False, "need_correct_answer"
    if mastery >= 0.8:
        return False, "mastery_already_high"
    if attempt_count > 5:
        return True, "deeper_explanation_needed_after_recent_attempts"
    if 0.3 < mastery < 0.6:
        return True, "solid_answer_but_mastery_incomplete"
    return False, "not_applicable"
```

### 5. 添加 `generate_structured_reflection` 方法
```python
def generate_structured_reflection(
    self,
    mastery_map: dict,
    topics_covered: list,
) -> str:
    """生成结构化反思内容"""
    weak_topics = [t for t, m in mastery_map.items() if m < 0.5]
    strong_topics = [t for t, m in mastery_map.items() if m >= 0.7]
    parts = ["本次学习总结："]
    if strong_topics:
        parts.append(f"✅ 已掌握：{', '.join(strong_topics)}")
    if weak_topics:
        parts.append(f"⚠️ 需加强：{', '.join(weak_topics)}")
    parts.append(f"📚 涉及主题数：{len(topics_covered)}")
    return "\n".join(parts)
```

### 6. 更新 `should_trigger()` 方法
- 加入冷却期检查（`cooldown_turns`）
- 加入最大反思次数检查（`reflections_triggered < MAX_REFLECTIONS_PER_SESSION`）
- 加入停滞分类逻辑（调用 `classify_stall_reason`）
- 加入 `should_self_explain` 逻辑替换原有随机触发
- 事后反思使用 `POST_SESSION_MIN_TURNS`

### 7. 更新 `reset_session()` 方法
添加：
```python
self._reflection_session = ReflectionSession()
```

### 8. 更新 `__init__` 方法
添加：
```python
self._reflection_session: ReflectionSession = ReflectionSession()
```

---

## 执行顺序
1. 插入 `ReflectionSession` 数据类
2. 添加常量
3. 更新 `__init__`
4. 添加 `classify_stall_reason`
5. 添加 `should_self_explain`
6. 添加 `generate_structured_reflection`
7. 更新 `should_trigger`
8. 更新 `reset_session`

## 影响范围
- 仅修改 `reflection_trigger.py` 单文件
- 向后兼容：所有现有公开方法签名不变，仅增强内部逻辑

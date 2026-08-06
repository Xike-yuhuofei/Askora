# Askora 策略库增强计划

## 概述
对 `strategy_library.py` 进行三大增强：YAML 加载支持、内置策略扩展至 56 个模板、创建 4 个 YAML 配置文件。

---

## 一、修改 `strategy_library.py`

### 1.1 新增导入
```python
import os

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    import json as yaml_json_fallback
    _YAML_AVAILABLE = False
```

### 1.2 新增方法
- `load_from_yaml(filepath: str)` — 从单个 YAML 文件加载策略
- `load_from_directory(dirpath: str)` — 从目录加载所有 YAML 文件
- `_parse_yaml_or_json(filepath: str)` — 内部解析方法（支持 yaml/json 自动检测）

### 1.3 扩展 `_BUILT_IN_STRATEGIES` 至 56 个模板

保留现有 12 个策略，新增 44 个：

| 学科 | 主题 | 数量 |
|------|------|------|
| 数学·代数 | linear_equations, quadratic_equations, functions, inequalities | 10 |
| 数学·几何 | triangles, circles, coordinate_geometry | 6 |
| 数学·数论 | divisibility, primes, gcd_lcm | 3 |
| 物理 | mechanics, motion, forces, energy | 8 |
| 化学 | reactions, mole_concept, periodic_table | 3 |
| 生物 | cell_structure, genetics, ecology | 3 |
| 语文 | reading_comprehension, essay_writing, classical_chinese | 5 |
| 英语 | grammar, vocabulary, reading_comprehension | 3 |
| 编程 | debugging, algorithm, data_structures | 3 |

### 1.4 每个策略字段
- `id`: `strat_{skill}_{topic}` 格式
- `level_1_goal`: `core_guidance` / `monitoring` / `planning`
- `level_2_skill`: `concept_clarification` / `error_analysis` / `guided_discovery` / `analogy` / `self_explanation` / `counter_example`
- `level_3_context`: 具体主题（如 `linear_equations`）
- `name`: 中文描述名
- `prompt_template`: 苏格拉底式提问模板
- `follow_up_strategies`: 后续策略 ID 列表
- `escalation_threshold`: 3
- `de_escalation_threshold`: 2
- `version`: "2.0.0"
- `is_active`: True

---

## 二、创建 YAML 配置文件

### 2.1 目录结构
```
app/data/strategies/yaml_strategies/
├── math_algebra.yaml      (10 策略)
├── math_geometry.yaml     (6 策略)
├── physics.yaml           (8 策略)
└── chinese.yaml           (5 策略)
```

### 2.2 YAML 文件格式
```yaml
strategies:
  - id: strat_xxx
    level_1_goal: core_guidance
    level_2_skill: concept_clarification
    ...
```

---

## 三、执行顺序

1. 读取并修改 `strategy_library.py`（添加导入、方法、扩展策略列表）
2. 创建 YAML 目录和 4 个 YAML 文件

## 四、风险与注意事项
- 文件较大（50+ 策略），需要分段写入确保正确性
- 保持现有接口向后兼容，不修改已有方法签名
- follow_up_strategies 中的引用需要确保对应策略存在
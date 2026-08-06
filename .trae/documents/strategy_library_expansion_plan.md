# 策略库扩展实施计划

## 概述
对 `strategy_library.py` 进行三大改造：新增 YAML 导入能力、扩展内置策略模板到 56+、创建 4 个 YAML 策略数据文件。

---

## 第一部分：修改 `strategy_library.py`

### 1.1 新增导入
- 添加 `import os`
- 添加 `import yaml` 配合 try/except 回退到 `json`

### 1.2 新增两个方法
- `load_from_yaml(filepath: str)` — 从单个 YAML 文件加载策略
- `load_from_directory(dirpath: str)` — 从目录批量加载所有 YAML 文件

### 1.3 扩展 `_BUILT_IN_STRATEGIES` 到 56 个模板
保留现有 12 个通用策略，新增 44 个学科专属策略：

| 分类 | 数量 | 明细 |
|------|------|------|
| Math Algebra | 10 | linear_equations(3), quadratic_equations(2), functions(3), inequalities(2) |
| Math Geometry | 6 | triangles(2), circles(2), coordinate_geometry(2) |
| Math Number Theory | 3 | divisibility(1), primes(1), gcd_lcm(1) |
| Physics | 8 | mechanics(3), motion(2), forces(1), energy(2) |
| Chemistry | 3 | reactions(1), mole_concept(1), periodic_table(1) |
| Biology | 3 | cell_structure(1), genetics(1), ecology(1) |
| Chinese | 5 | reading_comprehension(2), essay_writing(2), classical_chinese(1) |
| English | 3 | grammar(2), vocabulary(1) |
| Programming | 3 | debugging(1), algorithm(2) |

每个策略字段：id, level_1_goal, level_2_skill, level_3_context, name, description, prompt_template, follow_up_strategies, escalation_threshold=3, de_escalation_threshold=2, version="2.0.0", is_active=True

### 1.4 新增 `_load_yaml_strategies()` 方法
在 `__init__` 中调用，自动从 YAML 目录加载策略（如存在）

---

## 第二部分：创建 YAML 策略文件

### 2.1 创建目录
`apps/backend/app/data/strategies/yaml_strategies/`

### 2.2 创建 4 个 YAML 文件

| 文件 | 策略数 | 内容 |
|------|--------|------|
| `math_algebra.yaml` | 10 | 代数类策略（线性方程、二次方程、函数、不等式） |
| `math_geometry.yaml` | 6 | 几何类策略（三角形、圆、坐标几何） |
| `physics.yaml` | 8 | 物理类策略（力学、运动、力、能量） |
| `chinese.yaml` | 5 | 语文类策略（阅读理解、议论文写作、文言文） |

每个 YAML 文件格式：
```yaml
strategies:
  - id: "strat_xxx"
    level_1_goal: "..."
    level_2_skill: "..."
    level_3_context: "..."
    name: "..."
    description: "..."
    prompt_template: "..."
    follow_up_strategies: [...]
    escalation_threshold: 3
    de_escalation_threshold: 2
    version: "2.0.0"
    is_active: true
```

---

## 第三部分：执行顺序

1. 修改 `strategy_library.py`（添加导入 → 添加方法 → 扩展 `_BUILT_IN_STRATEGIES` → 更新 `__init__`）
2. 创建 YAML 目录
3. 依次创建 4 个 YAML 文件
4. 验证代码可正常导入
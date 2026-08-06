# Askora 种子数据创建计划

## 概述
为 Askora 后端创建策略模板和知识点的种子数据文件，包括 Python 脚本和 JSON 数据文件。

## 已分析的现有代码
- `app/models/knowledge.py`：`StrategyTemplate` 和 `KnowledgePoint` ORM 模型
- `app/engines/socratic/strategy_library.py`：现有硬编码策略模板（10 个）作为参考
- `scripts/init_test_data.py`：现有种子数据脚本风格参考（使用 async SQLAlchemy + 原生 SQL）
- `app/core/database.py`：数据库连接管理

## 文件清单

### 1. `scripts/__init__.py`
空文件，使 scripts 成为 Python 包。

### 2. `scripts/seed_strategies.py`
生成 30+ 策略模板的脚本：
- 覆盖学科：数学（代数/几何/函数）、物理（力学/电磁学）、化学、生物、语文（阅读/写作）、英语（语法/词汇）、编程
- 覆盖策略类型：概念澄清、引导发现、错误分析、反例构造、类比运用、自我解释提示、元认知监控
- 功能：生成 JSON 数据 + CLI 导入数据库

### 3. `scripts/seed_knowledge.py`
生成数学知识点的脚本：
- 代数（线性方程、二次方程、函数）
- 几何（三角形、圆）
- 数论
- 功能：生成 JSON 数据 + CLI 导入数据库

### 4. `app/data/__init__.py`, `app/data/strategies/__init__.py`, `app/data/knowledge/__init__.py`
空文件，使 data 目录成为 Python 包。

### 5. `app/data/strategies/seed_strategies.json`
30+ 策略模板 JSON 数据。

### 6. `app/data/knowledge/seed_knowledge.json`
数学知识点 JSON 数据。

## 策略模板设计（30+ 个）

### 三级分类体系
- **Level 1 Goals**: planning, monitoring, evaluation, core_guidance
- **Level 2 Skills**: goal_setting, strategy_selection, error_analysis, concept_clarification, guided_discovery, counter_example, analogy, self_explanation, metacognitive_monitoring
- **Level 3 Context**: 学科+具体主题

### 策略分布
| 学科 | 数量 | 具体主题 |
|------|------|----------|
| 数学-代数 | 5 | 线性方程、二次方程、不等式、函数概念、函数图像 |
| 数学-几何 | 4 | 三角形、圆、相似/全等、坐标系 |
| 数学-数论 | 2 | 整除/因数、素数/合数 |
| 物理-力学 | 3 | 牛顿定律、动量、能量守恒 |
| 物理-电磁学 | 2 | 电场、电路 |
| 化学 | 3 | 化学方程式、元素周期、反应类型 |
| 生物 | 2 | 细胞、遗传 |
| 语文-阅读 | 3 | 诗词鉴赏、现代文理解、文言文 |
| 语文-写作 | 2 | 议论文、记叙文 |
| 英语-语法 | 2 | 时态、从句 |
| 英语-词汇 | 2 | 词根词缀、语境猜词 |
| 编程 | 3 | 变量/函数、循环/条件、调试/错误分析 |

每个学科主题配有 2-3 种不同策略类型的模板。

## 知识点设计（数学）

### 代数
- 线性方程（1 元 1 次、2 元 1 次）
- 二次方程（因式分解、求根公式、配方法）
- 函数（一次函数、二次函数、反比例函数）

### 几何
- 三角形（内角和、全等判定、相似判定）
- 圆（圆心角、圆周角、切线）

### 数论
- 整除与因数
- 素数与合数
- 最大公约数与最小公倍数

## 执行顺序
1. 创建 `scripts/__init__.py`
2. 创建 `app/data/` 下的三个 `__init__.py`
3. 创建 `app/data/strategies/seed_strategies.json`
4. 创建 `app/data/knowledge/seed_knowledge.json`
5. 创建 `scripts/seed_strategies.py`
6. 创建 `scripts/seed_knowledge.py`
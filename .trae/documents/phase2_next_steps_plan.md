# Askora 后续阶段规划

## 1. 当前状态总览

### MVP Phase 1 完成度

| 模块 | 状态 | 说明 |
|------|------|------|
| 苏格拉底引擎七大子模块 | ✅ 完成 | InputParser, StrategyLibrary, StrategySelector, HintingGenerator, ResponseGenerator, OutputGuardrail, ReflectionTrigger |
| BKT 知识追踪 | ✅ 完成 | 含 Redis 持久化 + 内存降级 |
| 基础 RAG 服务 | ✅ 完成 | 接口已实现，待向量库对接 |
| 教学引擎矩阵 | ✅ 完成 | Socratic, Explain, Quiz, Drill, Inquiry |
| TEI v1 架构 | ✅ 完成 | Orchestrator, base classes, ENGINE_REGISTRY |
| DialogService 集成 | ✅ 完成 | 双路径切换（Orchestrator / 直接调用） |
| API 端点 | ✅ 完成 | /api/v1/orchestrator 调试端点 |
| Redis 持久化 | ✅ 完成 | OrchestratorRepository + 降级 |

### 未完成项（需要环境支持）

- [ ] 数据库迁移（strategy_templates 表）
- [ ] RAG 向量检索实际效果验证
- [ ] API 端到端集成测试
- [ ] Orchestrator 路由正确性验证

---

## 2. Phase 2: 生产就绪 & 核心增强

### 方向一：环境搭建与集成验证

**目标**：将代码从"逻辑可验证"推进到"可运行、可测试"。

#### 2.1.1 数据库迁移
- 创建 Alembic 迁移脚本，创建 `strategy_templates` 表
- 预置 30+ 策略模板数据（JSON seed 脚本）
- 验证 ORM 模型与数据库一致性

#### 2.1.2 RAG 流水线落地
- 对接 pgvector 或 ChromaDB 向量存储
- 创建知识摄入管道（从 Markdown/JSON 文档导入）
- 实现检索增强的知识问答流程
- 验证检索相关性（Checkpoint 2.4）

#### 2.1.3 集成测试套件
- 启动 FastAPI 测试实例
- 编写 API 集成测试：
  - `POST /orchestrator/sessions` → 创建会话
  - `POST /orchestrator/sessions/{id}/turns` → 执行一轮
  - `GET /orchestrator/engines` → 验证引擎注册
- 端到端测试：Socratic → Quiz → Socratic 完整链路
- 引擎路由测试：Drill 阶段正确路由至 DrillEngine

#### 2.1.4 环境配置与启动脚本
- 完善 `.env.example` 配置项说明
- 编写本地开发启动脚本（Docker Compose 或本地 Shell）
- 预提交钩子（pre-commit）配置

**涉及文件**：
- **新建**: `apps/backend/alembic/versions/` (迁移脚本), `apps/backend/scripts/seed_strategies.py`, `apps/backend/tests/test_integration_api.py`
- **修改**: `apps/backend/.env.example`, `apps/backend/pyproject.toml`

---

### 方向二：核心功能增强

**目标**：增强苏格拉底教学法深度和引擎间协作。

#### 2.2.1 策略库扩充
- 基于三级分类（元认知目标 → 认知技能 → 学科情境）扩充至 50+ 策略模板
- 覆盖学科：数学、物理、化学、语文、英语、编程
- 为每个模板添加：适用场景、禁忌、升级/降级条件

#### 2.2.2 反思触发深化
- 实现三种反思模式：
  - 事后反思（post-session）：会话结束时引导学生总结
  - 过程中反思（in-process）：连续错误时触发元认知提问
  - 自我解释（self-explanation）：要求学生解释推理过程
- 添加反思质量评估器

#### 2.2.3 提示生成器增强
- 实现真正的五级渐次提示（L1→L5）：
  - L1: 元认知提示（"你觉得第一步应该做什么？"）
  - L2: 概念提示（"回忆一下移项的定义..."）
  - L3: 策略提示（"试试把 x 移到一边..."）
  - L4: 结构提示（展示解题框架）
  - L5: 定向提示（接近答案但不泄露）
- 添加动态升降级逻辑：连续答对自动降级、连续错误自动升级

#### 2.2.4 Drill 引擎实战化
- 对接错题本，实现错题回炉
- 变式练习生成器（基于模板变体生成多道同类题）
- 自适应难度调整

#### 2.2.5 Inquiry 引擎完善
- 添加探究主题库（预置 10+ 探究主题）
- 实现协作探究模式（多轮假设-验证循环）
- 添加探究成果评估

**涉及文件**：
- **修改**: `app/engines/socratic/strategy_library.py`, `app/engines/socratic/reflection_trigger.py`, `app/engines/socratic/hinting_generator.py`
- **修改**: `app/engines/drill_engine.py`, `app/engines/inquiry_engine.py`
- **新建**: `app/data/strategies/` (策略配置文件), `app/data/inquiry_themes/` (探究主题)

---

### 方向三：架构演进

**目标**：为更大规模的教学场景做好架构准备。

#### 2.3.1 多 Agent 编排 (StateGraph)
- 引入 LangGraph 或自研 StateGraph 工作流
- 实现教学状态机：
  ```
  DIAGNOSE → LEARN → VALIDATE → DRILL → PRODUCE
       ↑                              |
       └──────── feedback loop ←──────┘
  ```
- 支持条件分支：根据诊断结果选择不同学习路径
- 实现引擎间的上下文传递协议

#### 2.3.2 深度知识追踪 (DKT)
- 实现基于 LSTM/Transformer 的 DKT 模型
- 处理知识点间的依赖关系（知识图谱）
- 支持多任务学习（同时预测多个知识点掌握度）

#### 2.3.3 知识图谱集成
- 接入 Neo4j 或使用关系型数据库模拟
- 构建学科知识图谱（节点=知识点，边=前置依赖）
- 支持学习路径推荐

#### 2.3.4 独立评估服务
- 拆分 Assessment Service 为独立模块
- 实现形成性评估（Formative Assessment）
- 实现总结性评估（Summative Assessment）
- 支持评估报告生成

**涉及文件**：
- **新建**: `app/engines/state_graph.py`, `app/services/dkt/`, `app/services/assessment/`, `app/services/knowledge_graph/`
- **修改**: `app/engines/orchestrator.py` (状态机增强)

---

### 方向四：生产基础设施

**目标**：确保系统可观测、可扩展、可维护。

#### 2.4.1 部署与运维
- 编写 Dockerfile 与 docker-compose.yml
- 配置 CI/CD 流水线（GitHub Actions / GitLab CI）
- 实现健康检查与就绪探针
- 日志聚合（ELK / Loki）

#### 2.4.2 监控与可观测性
- 核心指标导出（Prometheus）：
  - 引擎调用延迟 (P50/P95/P99)
  - 知识点掌握度分布
  - 引擎切换频率
  - LLM Token 消耗
- 可视化仪表盘（Grafana）
- 关键告警配置

#### 2.4.3 性能优化
- LLM 调用批处理与缓存
- RAG 检索结果缓存
- Socratic 引擎热路径优化
- 前端 SSE 流式输出优化

#### 2.4.4 安全与合规
- 数据加密传输与存储
- 审计日志完善
- 防注入、防滥用
- 符合教育 App 备案要求

---

## 3. 推荐执行顺序

### 第一优先级（立即启动）

1. **方向一：环境搭建与集成验证**
   - 完成 MVP 剩余的 4 个 Checkpoint
   - 验证 API 端到端链路
   - 产出可运行的开发环境

2. **方向二：核心功能增强（按优先级）**
   - 2.2.1 策略库扩充 → 为教学深度打基础
   - 2.2.3 提示生成器增强 → 直接影响教学体验
   - 2.2.2 反思触发深化 → 提升元认知能力
   - 2.2.4 Drill 引擎实战化 → 形成练习闭环
   - 2.2.5 Inquiry 引擎完善 → 形成探究闭环

### 第二优先级（核心功能完成后）

3. **方向三：架构演进**
   - 2.3.1 多 Agent 编排 → 复杂度较高，需核心功能稳定后再启动
   - 2.3.2 DKT → 需要积累足够的用户数据
   - 2.3.3 知识图谱 → 依赖领域建模
   - 2.3.4 评估服务 → 独立部署

### 第三优先级（生产就绪阶段）

4. **方向四：生产基础设施**
   - 可与核心功能并行推进
   - Docker/CI 可提前启动

---

## 4. 开放问题

- [ ] RAG 初始知识数据源选择？（预置学科教材 / 开放教育资源 / 用户自建）
- [ ] BKT/DKT 模型的初始参数是否需要针对中文教育场景调优？
- [ ] 前端是否需要同步规划？（当前仅后端）
- [ ] 是否需要为不同学科（数学/语文/英语）建立差异化的教学策略？
- [ ] 生产环境 LLM 选型？（通义千问 / DeepSeek / 豆包 / 开源模型）
- [ ] 是否需要用户画像系统对接（从 user_profile 读取 learner_persona）？

---

## 5. 各方向文件清单

### 方向一：环境搭建与集成验证

| 操作 | 文件路径 | 说明 |
|------|----------|------|
| 新建 | `apps/backend/alembic/versions/xxxx_add_strategy_templates.py` | 数据库迁移脚本 |
| 新建 | `apps/backend/scripts/seed_strategies.py` | 策略模板数据导入脚本 |
| 新建 | `apps/backend/scripts/seed_knowledge.py` | 知识点数据导入脚本 |
| 新建 | `apps/backend/tests/conftest.py` | 测试 fixture 配置 |
| 新建 | `apps/backend/tests/test_integration_api.py` | API 集成测试 |
| 新建 | `apps/backend/tests/test_orchestrator_flow.py` | 编排器流程测试 |
| 修改 | `apps/backend/.env.example` | 环境变量说明 |
| 修改 | `apps/backend/README.md` | 本地开发指南 |

### 方向二：核心功能增强

| 操作 | 文件路径 | 说明 |
|------|----------|------|
| 修改 | `app/engines/socratic/strategy_library.py` | 扩充策略至 50+ |
| 修改 | `app/engines/socratic/reflection_trigger.py` | 三种反思模式 |
| 修改 | `app/engines/socratic/hinting_generator.py` | 五级提示实现 |
| 修改 | `app/engines/drill_engine.py` | 错题本 + 变式练习 |
| 修改 | `app/engines/inquiry_engine.py` | 探究主题库 |
| 新建 | `app/data/strategies/math_strategies.yaml` | 数学策略配置 |
| 新建 | `app/data/strategies/physics_strategies.yaml` | 物理策略配置 |
| 新建 | `app/data/inquiry_themes/default_themes.yaml` | 探究主题 |
| 新建 | `app/engines/socratic/strategy_config_loader.py` | YAML 配置加载器 |

### 方向三：架构演进

| 操作 | 文件路径 | 说明 |
|------|----------|------|
| 新建 | `app/engines/state_graph.py` | 状态机/状态图 |
| 新建 | `app/services/dkt/dkt_service.py` | 深度知识追踪 |
| 新建 | `app/services/assessment/assessment_service.py` | 评估服务 |
| 新建 | `app/services/knowledge_graph/kg_service.py` | 知识图谱 |
| 修改 | `app/engines/orchestrator.py` | 状态机集成 |

### 方向四：生产基础设施

| 操作 | 文件路径 | 说明 |
|------|----------|------|
| 新建 | `apps/backend/Dockerfile` | 后端镜像 |
| 新建 | `docker-compose.yml` | 本地开发编排 |
| 新建 | `.github/workflows/ci.yml` | CI 流水线 |
| 新建 | `apps/backend/app/metrics.py` | Prometheus 指标 |
| 新建 | `apps/backend/app/observability.py` | 可观测性配置 |
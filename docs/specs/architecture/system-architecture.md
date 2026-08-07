# Askora System Architecture Specification

> Spec ID 范围：`ARCH-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.1  
> 来源：`docs/design/个人AI辅助学习平台设计方案.md`、`docs/design/AI学习系统算法与教学内核设计.md` 及 `docs/design/research/` 八类技术系统研究。

## 1. 目标

本规范冻结 Askora 的顶层工程架构，使实现代理无需重新解释研究材料即可判断：

- 一个能力属于哪个系统；
- 哪个系统拥有最终决策权；
- 哪些状态只能由谁写；
- 跨系统如何交互；
- 现有 legacy 代码应向什么结构迁移。

Askora MUST 被实现为**模块化单体优先**的个人学习系统。除非新的 Canonical Design + ADR + Spec 明确批准，Codex MUST NOT 把八类系统拆成独立微服务。

## 2. 顶层架构原则

### ARCH-001：教学闭环而非聊天主线

唯一目标主链路 MUST 是：

```text
LearningGoal
→ Content/Knowledge
→ Diagnostic/Assessment
→ LearnerState
→ LearningPlan
→ TeachingAction
→ EvidenceBundle
→ Orchestrated Execution
→ Attempt/AssessmentResult
→ LearnerState Update
→ ReviewSchedule
→ Replan
```

普通请求、流式请求、桌面客户端请求 MUST 汇入同一教学编排边界，不得存在一条“直接聊天”路径和一条“正式教学”路径长期并存。

### ARCH-002：决策与生成分离

LLM MUST NOT 成为下列业务决策的唯一所有者：

- mastery；
- assessment score；
- TeachingAction；
- LearningPlan；
- ReviewSchedule；
- 知识事实发布。

LLM MAY 生成候选、做受约束分类/评分、生成表达，但最终状态变更 MUST 由对应领域系统通过显式合同接纳。

### ARCH-003：状态唯一写入者

每类核心业务状态 MUST 有且仅有一个系统拥有写权限。其他系统只能：

- 读取版本化快照；
- 提交 command；
- 发布 evidence/event；
- 执行已决定动作。

禁止跨系统直接 ORM 更新业务状态。

### ARCH-004：事实、测量、推断、决策、执行分层

下列语义 MUST 分开：

```text
Source fact        原始材料事实
Measurement        单次评估测量
Inference          学习者/记忆状态推断
Decision           教学/计划/检索选择
Execution          LLM/工具/交互执行
```

禁止把这些语义压缩到一个“大会话状态”或一个 LLM 输出对象中。

### ARCH-005：不可变事件 + 可重建投影

关键学习行为和领域事实 MUST 通过不可变事件记录。`LearnerState`、`MasteryEstimate`、必要的统计视图 SHOULD 可由事件与固定算法版本重放重建。

关键状态更正 MUST 采用新事件/新版本，不得静默改写历史证据。

### ARCH-006：本地优先、单用户优先

v0.2 实现 MUST 优先满足：

- 单用户；
- 单设备；
- 本地优先；
- SQLite 桌面运行可行；
- PostgreSQL 服务运行兼容。

不得为了未来多租户场景提前引入微服务、复杂消息基础设施或分布式一致性协议作为 v0.2 必选项。

### ARCH-007：高级算法必须有 baseline

任何高级算法进入生产路径前 MUST 与简单可解释 baseline 对比，并证明在目标指标上有稳定收益。

当前默认：

- Knowledge Modeling：规则 + schema-constrained extraction；
- Retrieval：BM25 + dense + RRF + rerank；
- Learner Model：证据加权 BKT / 简单可解释模型；
- Assessment：deterministic-first + rubric constrained model；
- Teaching Policy：规则 + 状态机 + 加权评分；
- Planner：约束可行集 + heuristic priority + greedy scheduling；
- Review：FSRS-compatible / simple baseline；
- AI Orchestration：确定性 workflow + 受约束生成。

Codex MUST NOT 自行用 DKT、RL、autonomous multi-agent 等替换 baseline。

## 3. 八类技术系统

### 3.1 4.1 Content & Knowledge

**唯一职责**：把不可信原始材料转换为可版本化、可定位原文、可审核、可教学的知识模型。

**唯一所有权**：

- SourceDocument / MaterialRevision 发布状态；
- KnowledgeUnit；
- Concept；
- PrerequisiteRelation；
- 规范 Misconception 定义。

**禁止负责**：mastery、TeachingAction、LearningPlan、ReviewSchedule、最终 EvidenceBundle。

### 3.2 4.2 Retrieval & Knowledge Supply

**唯一职责**：根据 TeachingAction 与教学约束生成本轮 `EvidenceBundle`。

**唯一所有权**：候选证据进入本轮 bundle 的最终选择、压缩、组合、引用和检索 trace。

**禁止负责**：决定为什么要学、怎么教、用户是否掌握、最终用户表达。

### 3.3 4.3 Learner Model

**唯一职责**：融合跨时间学习证据，维护 `LearnerState` 与 `MasteryEstimate`。

**唯一所有权**：

- LearnerState；
- MasteryEstimate；
- learner-specific misconception hypothesis。

**禁止负责**：单次评分、TeachingAction、LearningPlan、ReviewSchedule。

### 3.4 4.4 Assessment & Error Diagnosis

**唯一职责**：对一次 Attempt 产生可审计测量、评分、错误分类与误区证据。

**唯一所有权**：

- AssessmentItem 发布；
- Attempt；
- AssessmentResult；
- 单次 error type；
- 单次 misconception evidence；
- assessment confidence。

**禁止负责**：直接宣布长期 mastery。

### 3.5 4.5 Teaching Policy

**唯一职责**：决定当前一步“怎么教”。

**唯一所有权**：

- TeachingAction；
- TeachingStrategy version；
- scaffold/hint level；
- answer exposure max；
- evidence requirements；
- action success/failure/exit conditions。

**禁止负责**：长期课程排序、评分、复习日期、LLM 执行。

### 3.6 4.6 Learning Planner

**唯一职责**：决定“下一阶段/今天学什么、顺序如何”。

**唯一所有权**：

- LearningGoal 的结构化受控版本；
- LearningObjective；
- LearningActivity；
- LearningPlan；
- 日任务优先级和 replan。

**禁止负责**：怎么讲、怎么提示、next_due_at、知识关系真伪。

### 3.7 4.7 Review Scheduler

**唯一职责**：决定“某知识单元什么时候建议复习”。

**唯一所有权**：

- ReviewSchedule；
- memory scheduling state；
- retrievability estimate；
- next_due_at。

**禁止负责**：完整日计划、TeachingAction、mastery 裁决。

### 3.8 4.8 AI Orchestration & Trust

**唯一职责**：忠实执行 4.1～4.7 已确定的领域决策，并负责模型、工具、Prompt、安全、输出验证、事件账本与降级。

**唯一所有权**：

- Session/Workflow execution state；
- ModelRoute；
- ModelInference；
- ToolCall/ToolResult；
- PromptTemplate version；
- FeedbackSignal ledger；
- LearningEvent ledger 的持久化执行；
- DecisionTrace ledger 的持久化执行。

**禁止负责**：改 mastery、改 TeachingAction、改 LearningPlan、改 ReviewSchedule、发布知识事实。

## 4. 逻辑分层

```text
┌──────────────────────────────────────────┐
│ 交互执行与可信治理层                    │
│ 4.8 AI Orchestration & Trust            │
├──────────────────────────────────────────┤
│ 教学决策层                              │
│ 4.5 Teaching Policy | 4.6 Planner       │
├──────────────────────────────────────────┤
│ 学习证据与状态层                        │
│ 4.4 Assessment | 4.3 Learner | 4.7 Review│
├──────────────────────────────────────────┤
│ 知识基础设施层                          │
│ 4.1 Content/Knowledge | 4.2 Retrieval   │
└──────────────────────────────────────────┘
```

依赖 MUST 优先向下读取、通过事件向上反馈；不得通过共享 ORM 实体形成双向可写依赖。

## 5. 关键领域对象与所有者

| 对象 | 创建/写入所有者 | 其他系统权限 |
|---|---|---|
| SourceDocument | 4.1 | R |
| SourceChunk | 4.1 | R |
| KnowledgeUnit | 4.1 | R / submit conflict evidence |
| Concept | 4.1 | R |
| PrerequisiteRelation | 4.1 | R / submit conflict evidence |
| Misconception definition | 4.1 | R |
| EvidenceBundle | 4.2 | consume only |
| LearnerState | 4.3 | R / submit evidence |
| MasteryEstimate | 4.3 | R / submit evidence |
| learner misconception hypothesis | 4.3 | R / submit evidence |
| AssessmentItem | 4.4 | consume only |
| Attempt | 4.4 | append via command |
| AssessmentResult | 4.4 | consume only |
| TeachingAction | 4.5 | consume only |
| TeachingStrategy | 4.5 | consume only |
| LearningGoal | 4.6 | user-confirmed input; others R |
| LearningObjective | 4.6 | consume only |
| LearningActivity | 4.6 | consume only |
| LearningPlan | 4.6 | R |
| ReviewSchedule | 4.7 | R |
| LearningEvent | 4.8 ledger | append-only through contract |
| FeedbackSignal | 4.8 ledger | append-only |
| ModelInference | 4.8 | append-only |
| DecisionTrace | 4.8 ledger | domain owner submits payload |

## 6. 跨系统数据流

### ARCH-020：标准教学轮次

```text
4.6 selects LearningActivity
→ 4.5 creates TeachingAction
→ 4.2 creates EvidenceBundle if required
→ 4.8 executes action
→ user produces response/action
→ 4.4 records Attempt and AssessmentResult when measurable
→ 4.3 updates LearnerState from accepted evidence
→ 4.7 updates ReviewSchedule from valid retrieval evidence
→ 4.6 replans only if trigger conditions are met
```

### ARCH-021：不得同步循环写入

例如 4.4 → 4.3 → 4.5 → 4.8 → 4.4 的循环 MUST 通过新事件/新版本形成，禁止在一个数据库事务里跨四个系统层层直接修改对方实体。

### ARCH-022：失败回流

4.2 或 4.8 的执行失败 MAY 返回：

- missing evidence；
- conflict；
- low confidence；
- model unavailable；
- tool denied；
- validation failed。

它们 MUST NOT 自行改变 TeachingAction 语义。需要改变教学策略时 MUST 回到 4.5 形成新的 TeachingAction。

## 7. Target Module Layout

目标后端结构 SHOULD 逐步收敛为：

```text
apps/backend/app/
├── domains/
│   ├── content_knowledge/      # 4.1
│   ├── retrieval/              # 4.2
│   ├── learner_model/          # 4.3
│   ├── assessment/             # 4.4
│   ├── teaching_policy/        # 4.5
│   ├── learning_planner/       # 4.6
│   └── review_scheduler/       # 4.7
├── orchestration/              # 4.8 application/workflow
├── ai/                         # model gateway, prompt registry, validators
├── contracts/                  # public command/event/domain schemas
├── infrastructure/             # persistence, outbox, telemetry, storage
├── api/                        # transport adapters
└── legacy/ or adapters/        # 迁移期兼容层，仅在 EXEC 明确要求时建立
```

该目录结构是目标边界，不要求一次大爆炸迁移。Codex SHOULD 通过垂直切片逐步迁移。

## 8. 当前代码映射与迁移方向

当前仓库中：

| 现有路径 | 目标归属 | 迁移说明 |
|---|---|---|
| `services/documents/` | 4.1 + 4.2 | parser/document modeling 与 rag retrieval 必须分离 |
| `services/knowledge_graph/` | 4.1 projection / 4.2 graph retrieval | 图不能独立成为第二事实源 |
| `services/kt/` | 4.3 | 作为 learner model baseline 候选 |
| `services/dkt/` | 4.3 challenger | 不得成为 v0.2 默认事实源 |
| `services/assessment/` | 4.4 | 必须移除直接 mastery 写入能力（如存在） |
| `engines/socratic/strategy_selector.py` | 4.5 | 策略选择从具体引擎中抽离 |
| `engines/*_engine.py` | 4.8 execution adapters | 引擎执行 TeachingAction，不拥有长期状态 |
| `engines/orchestrator.py` | 4.8 | 收敛为唯一教学执行入口 |
| `services/dialog/` | API/4.8 legacy | 不得形成绕过 orchestrator 的第二教学路径 |
| `services/llm/model_router.py` | 4.8 AI gateway | 只做模型路由，不改教学语义 |
| `workers/` | infrastructure/4.8 | 持久化任务与 outbox 执行 |
| `models/*.py` | legacy persistence models | 逐步迁移为按领域所有权组织的 persistence adapter |

### ARCH-030：Legacy Freeze

在对应迁移完成前，Codex MAY 修复 legacy 模块，但 MUST NOT 继续向错误边界增加新的长期状态所有权。

### ARCH-031：禁止双真相源

迁移某状态后，旧路径 MUST 进入只读/adapter/删除阶段，不允许新旧两套状态持续双写且没有明确 reconciliation 合同。

## 9. v0.2 首个垂直切片

目标闭环固定为：

```text
导入 PDF/Markdown
→ 建立可定位来源
→ 确认一个可测量 LearningGoal
→ 生成一个 LearningActivity
→ TeachingAction 决策
→ RAG EvidenceBundle
→ 教学执行
→ 可确定性评分 Attempt
→ AssessmentResult
→ LearnerEvidence / MasteryEstimate
→ ReviewSchedule
→ 应用重启后恢复
```

v0.2 MUST NOT 为完成该闭环引入：

- 微服务；
- autonomous multi-agent；
- DKT 生产主模型；
- 强化学习；
- 通用大型知识图谱；
- 跨设备同步；
- 多租户学校部署。

## 10. 架构验收条件

### ARCH-AC-001

任一核心业务状态都能指出唯一 owner module，且代码中不存在第二个无合同写入者。

### ARCH-AC-002

普通和流式教学请求经过相同 orchestrator 主链路。

### ARCH-AC-003

AssessmentResult 不直接等于 MasteryEstimate；至少存在显式 evidence → learner model 更新边界。

### ARCH-AC-004

TeachingAction 与 LearningPlan 分离，Teaching Policy 不能重排长期学习目标。

### ARCH-AC-005

ReviewSchedule 与 LearnerState 分离，Planner 不重复计算遗忘模型。

### ARCH-AC-006

LLM/Agent 无直接写入 4.1/4.3/4.4/4.5/4.6/4.7 核心业务状态的通道。

### ARCH-AC-007

所有关键决策和模型调用可通过 version + trace id 追踪。

### ARCH-AC-008

事件重放在固定 projection/algorithm 版本下不得依赖在线 LLM。

## 11. Forbidden Implementations

以下实现一律禁止：

- 一个 `TutorAgent` 同时决定 mastery、plan、strategy、retrieval 和最终状态写入；
- `assessment_service.update_mastery(...)` 一类跨所有权直接调用；
- `orchestrator` 在模型输出中解析 `mastery=1` 后直接写数据库；
- RAG service 因检索不到资料而用模型常识伪造“来自用户资料”的答案；
- Planner 与 Review Scheduler 各保存一个不同的 `next_review_at`；
- 同时保留 `dialog direct LLM path` 与 `orchestrator path` 为默认生产入口；
- 把聊天历史作为唯一学习事实源；
- 把模型自报 confidence 当作已校准概率；
- 因现有目录结构不便而改变八类系统所有权。

# Askora State Ownership Specification

> Spec ID 范围：`STATE-*`  
> 状态：Canonical Implementation Contract  
> 版本：v0.1

## 1. 核心原则

### STATE-001：一个状态，一个唯一写入者

任何跨会话、可影响后续教学决策的核心业务状态 MUST 有唯一写入系统。

### STATE-002：读权限不等于写权限

一个系统可以读取另一个系统的状态用于决策，但不得因此获得更新该状态的权限。

### STATE-003：建议不是状态更新

LLM、评估器、检索器或用户反馈产生的“建议/证据/候选”必须先被状态 owner 接纳，才能形成新的 canonical state version。

### STATE-004：核心状态版本化

以下对象 MUST 采用 append/version 或 immutable snapshot 语义，不得原地静默覆盖历史：

- KnowledgeUnit/Relation 的已发布 revision；
- AssessmentResult；
- MasteryEstimate；
- TeachingAction；
- LearningPlan；
- ReviewSchedule；
- LearningEvent；
- DecisionTrace。

## 2. 状态所有权矩阵

符号：

- `C`：创建；
- `W`：更新/新版本；
- `R`：只读；
- `E`：只能提交 evidence/event；
- `X`：执行动作，无状态所有权。

| 状态 | 4.1 | 4.2 | 4.3 | 4.4 | 4.5 | 4.6 | 4.7 | 4.8 | 唯一写入者 |
|---|---|---|---|---|---|---|---|---|---|
| RawAsset metadata | C/W | R | - | - | - | R | - | R | 4.1 |
| SourceDocument/MaterialRevision | C/W | R | R | R | R | R | R | R | 4.1 |
| SourceChunk/SourceSpan projection | C/W | R | R | R | R | R | R | R | 4.1 |
| KnowledgeUnit | C/W | R | R | R | R | R/E | R | R | 4.1 |
| Concept | C/W | R | R | R | R | R | R | R | 4.1 |
| PrerequisiteRelation | C/W | R | R | R | R | R/E | R | R | 4.1 |
| Misconception definition | C/W | R | R | R | R | R | R | R | 4.1 |
| EvidenceBundle | R | C/W* | R | R | R | R | R | X | 4.2 |
| LearnerState | R | R | C/W | E | R | R | E | E | 4.3 |
| MasteryEstimate | R | R | C/W | E | R | R | E | R | 4.3 |
| learner misconception hypothesis | R | R | C/W | E | R | R | R | E | 4.3 |
| AssessmentItem | R | R | R | C/W | R | R | R | X | 4.4 |
| Attempt | R | R | R | C/W* | R | R | R | X/CMD | 4.4 |
| AssessmentResult | R | R | R | C/W* | R | R | R | X | 4.4 |
| TeachingStrategy | R | R | R | R | C/W | R | R | X | 4.5 |
| TeachingAction | R | R | R | R | C/W* | R | R | X | 4.5 |
| LearningGoal | R | R | R | R | R | C/W | R | X | 4.6 |
| LearningObjective | R | R | R | R | R | C/W* | R | X | 4.6 |
| LearningActivity | R | R | R | R | R | C/W* | R | X | 4.6 |
| LearningPlan | R | R | R | R | R | C/W | R | X | 4.6 |
| ReviewSchedule | R | R | R | E | R | R | C/W | X | 4.7 |
| memory model state | R | R | R | E | R | R | C/W | X | 4.7 |
| SessionState/WorkflowRun | R | R | R | R | R | R | R | C/W | 4.8 |
| ModelInference | R | R | R | R | R | R | R | C append-only | 4.8 |
| FeedbackSignal | E | E | E | E | E | E | E | C append-only | 4.8 ledger |
| LearningEvent | E | E | E | E | E | E | E | C append-only | 4.8 ledger |
| DecisionTrace | E | E | E | E | E | E | E | C append-only | 4.8 ledger |

`*`：结果对象通过新记录/新版本演进，不允许静默修改已发布结论。

## 3. 关键边界

### STATE-010：AssessmentResult ≠ MasteryEstimate

`AssessmentResult` 只描述一次 Attempt：

```text
score
correctness
rubric dimensions
error type
misconception evidence
independence
assessment confidence
```

只有 4.3 可以把一个或多个 AssessmentResult 与其他 evidence 融合为 MasteryEstimate。

任何代码如果存在：

```python
assessment_result.mastery = ...
learner.mastery = score
```

或等价逻辑，必须视为越权。

### STATE-011：ReviewSchedule ≠ MasteryEstimate

记忆可提取性与完整掌握不是同一状态。

4.7 可以维护：

- stability；
- difficulty；
- retrievability；
- next_due_at。

但不能宣布用户“稳定掌握/迁移掌握”。

### STATE-012：LearningPlan ≠ TeachingAction

4.6 决定：

- 学什么；
- 顺序；
- 今日任务；
- 任务优先级。

4.5 决定：

- 当前讲解/提问/练习/测试；
- 提示强度；
- 答案暴露；
- 本轮退出条件。

两个状态必须独立版本化。

### STATE-013：SourceChunk ≠ KnowledgeUnit

SourceChunk 是可重建检索投影；KnowledgeUnit 是规范教学/评估语义单元。

重新分块不得自动导致 KnowledgeUnit identity 全量漂移。

### STATE-014：Misconception definition ≠ learner hypothesis

4.1 维护“某种典型误区是什么”。

4.4 可以产生“本次回答与该误区匹配”的 evidence。

4.3 决定“当前是否有理由认为该用户存在该误区”。

## 4. 状态更新合同

### STATE-020：所有关键更新必须有 provenance

关键状态新版本 MUST 至少能追溯：

- 输入对象/事件 ID；
- algorithm/policy/model version；
- occurred/created time；
- reason codes；
- trace/correlation id。

### STATE-021：关键状态不得从聊天文本直接更新

聊天消息 MAY 触发 command，但 MUST 经结构化验证后才能成为领域事实。

示例：

```text
“我已经会了”
```

只能形成 self-report / feedback signal，不能直接把 mastery 设置为 1.0。

### STATE-022：用户纠错采用争议/复核流程

用户认为系统判断错误时：

```text
FeedbackSignal
→ disputed/review required
→ retest / evidence correction / replay
→ new state version
```

禁止直接编辑概率为用户指定值，除非未来 Spec 明确定义人工 override 类型且单独展示。

### STATE-023：删除与纠正

历史学习事件出现错误时：

- 普通纠正：追加 correction event；
- 用户依法/明确要求删除：执行删除策略并保留允许范围内的审计墓碑；
- 删除后需要重建受影响投影。

## 5. 并发与幂等

### STATE-030

同一 aggregate 的 canonical version MUST 单调递增，并在数据库建立唯一约束。

### STATE-031

重复 command 不得生成第二份等价 evidence 或第二次 mastery 更新。必须通过 `idempotency_key` 或等效机制返回原结果。

### STATE-032

投影消费者必须幂等；重放同一事件集合 + 同一 projection version MUST 产生相同状态。

### STATE-033

重放过程 MUST NOT 调用在线 LLM 重新“理解”历史事件。需要 LLM 产物时，应使用当时已持久化的结构化 result 或明确的新重评流程。

## 6. Persistence Boundary

每个领域 SHOULD 拥有逻辑独立 repository interface，即使物理上共用 SQLite/PostgreSQL。

目标示意：

```text
ContentKnowledgeRepository   → 4.1
RetrievalProjectionStore     → 4.2 可重建投影/cache
LearnerStateRepository       → 4.3
AssessmentRepository         → 4.4
TeachingPolicyRepository     → 4.5
LearningPlanRepository       → 4.6
ReviewScheduleRepository     → 4.7
Execution/EventLedger        → 4.8
```

共享数据库不代表共享写权限。

## 7. Legacy 数据治理

### STATE-040：迁移先确定 owner

任何现有表/模型在重构前必须先标注：

- target owner；
- 当前写入者；
- 是否存在多写入者；
- 迁移策略；
- legacy 删除条件。

### STATE-041：双写只允许短期迁移

若迁移必须双写：

- EXEC Plan 必须明确主 truth；
- 必须有 reconciliation check；
- 必须有明确停止双写条件；
- 不得把双写变成永久架构。

### STATE-042：DKT/KT 状态收敛

现有 `services/kt/` 和 `services/dkt/` 输出不得分别作为两个 canonical mastery source。v0.2 必须指定一个 canonical learner state projector；其他模型只能 challenger/feature provider。

## 8. 必须测试的所有权场景

### STATE-AC-001

提交 AssessmentResult 后，只有 learner-model application path 可以创建新的 MasteryEstimate。

### STATE-AC-002

LLM 返回包含 `mastery`, `next_review_at`, `plan` 等字段时，4.8 必须忽略/拒绝任何未授权业务状态写入。

### STATE-AC-003

Planner 接收 ReviewDue 后只能把其纳入 LearningActivity，不能修改 ReviewSchedule 的 memory state。

### STATE-AC-004

Assessment 识别误区后只发布 misconception evidence，Learner Model 决定 active hypothesis。

### STATE-AC-005

重放相同事件集合得到相同 MasteryEstimate version content（除不可避免的创建时间字段外应 deterministic）。

### STATE-AC-006

重新分块 SourceChunk 不得无条件重建全部 KnowledgeUnit identity。

## 9. Forbidden Implementations

禁止：

- 共享 `UserLearningState` 大表由所有模块任意更新；
- 通过 JSON blob 把 mastery/plan/review/teaching 混在一份 conversation state 中；
- `AssessmentService`、`Orchestrator`、`Planner` 同时拥有 `mastery` 更新方法；
- 4.3 和 4.7 同时保存语义相同但值不同的 `next_review_at`；
- 将用户点赞直接转换成 mastery 增量；
- 将 LLM confidence 直接作为 MasteryEstimate confidence；
- 历史 AssessmentResult 被新评分器静默覆盖；
- event replay 时重新请求在线模型导致同一事件集投影不同。

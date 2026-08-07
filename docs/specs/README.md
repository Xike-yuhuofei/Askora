# Askora Implementation Specifications

> 状态：Canonical Implementation Contract  
> 版本：v0.1  
> 生效日期：2026-08-07  
> 目的：把 `docs/design/` 的正式设计转化为可由 Codex 直接执行、可测试、可审计的工程合同。

## 1. 本目录的职责

`docs/specs/` 回答唯一问题：**Askora 必须怎样实现。**

它不负责重新论证“为什么这样设计”。设计依据、算法比较、研究证据和长期演进仍属于 `docs/design/` 与 `docs/design/research/`。

知识形成与执行链路固定为：

```text
Research
  ↓
Canonical Design
  ↓
Implementation Specs
  ↓
Execution Plan
  ↓
Code + Migration + Tests
  ↓
Implementation Validation
```

## 2. 权威性与冲突处理

实现阶段的权威优先级：

```text
1. docs/specs/               可执行实现合同
2. docs/adr/                 已接受的架构决策
3. docs/design/              Canonical Design
4. 代码、迁移和测试           当前实现事实
5. Codex 自主推断             不具备设计权威性
```

规则：

1. `docs/specs/` 不得与 Canonical Design 静默冲突；发现冲突必须先回到设计层解决；
2. 已冻结 Spec 与当前代码冲突时，默认判定为实现偏差，而不是用现有代码反推新规范；
3. 破坏性架构变化必须先建立 ADR，再更新对应 Spec，最后修改代码；
4. Codex 不得因为“现有实现更方便”而绕过状态所有权、领域边界或验收标准；
5. 未被 Spec 定义的重要决策属于 `SPEC GAP`，不得由 Codex自行补全。

## 3. 规范语言

本目录使用 RFC 风格约束词：

- **MUST / 必须**：违反即实现不合格；
- **MUST NOT / 禁止**：任何实现不得采用；
- **SHOULD / 应当**：默认必须遵守，偏离需要说明理由；
- **MAY / 可以**：允许的实现自由度。

Codex 只拥有 `MAY` 范围内的自主选择权。

## 4. 目录结构

```text
docs/specs/
├── README.md
├── architecture/
│   ├── system-architecture.md
│   ├── dependency-rules.md
│   └── state-ownership.md
├── domain/
│   ├── domain-model.md
│   ├── event-contract.md
│   ├── decision-contract.md
│   └── lifecycle-state-machines.md
├── systems/
│   ├── 01-content-knowledge.md
│   ├── 02-retrieval.md
│   ├── 03-learner-model.md
│   ├── 04-assessment.md
│   ├── 05-teaching-policy.md
│   ├── 06-learning-planner.md
│   ├── 07-review-scheduler.md
│   └── 08-ai-orchestration.md
├── interfaces/
│   ├── api-contract.md
│   ├── persistence-contract.md
│   ├── error-contract.md
│   └── schema-versioning.md
├── quality/
│   ├── testing-standard.md
│   ├── observability-standard.md
│   ├── security-standard.md
│   └── definition-of-done.md
└── vertical-slices/
    └── v0.2-learning-loop.md
```

文件按需要逐步建立；目录中不存在的文件不代表对应设计可以由 Codex 自由决定。

## 5. 每个系统 Spec 的固定模板

八类技术系统必须使用统一模板：

1. `Responsibility`：唯一职责；
2. `Non-responsibility`：明确禁止负责的内容；
3. `Owned State`：唯一可写状态；
4. `Inputs`：允许读取的对象；
5. `Outputs`：必须产生的对象；
6. `Domain Objects`：系统拥有/消费的领域模型；
7. `Commands`：接受的命令；
8. `Events`：消费与产生的事件；
9. `Algorithms`：baseline、可选算法、升级门槛；
10. `Persistence`：表、索引、事务、并发和版本语义；
11. `Failure Semantics`：失败、重试和降级；
12. `Idempotency`：幂等要求；
13. `Observability`：日志、指标和 trace；
14. `Security`：权限、数据边界和不可信输入；
15. `Tests`：必须存在的测试；
16. `Acceptance Criteria`：完成定义；
17. `Forbidden Implementations`：明确禁止实现方式。

## 6. Spec 标识与可追踪性

规范条款采用稳定 ID：

```text
ARCH-xxx       顶层架构规则
DEP-xxx        依赖规则
STATE-xxx      状态所有权规则
DOMAIN-xxx     公共领域模型
SYS01-xxx ... SYS08-xxx  八类系统规则
API-xxx        外部接口规则
PERSIST-xxx    持久化规则
TEST-xxx       测试规则
SEC-xxx        安全规则
AC-xxx         验收标准
```

执行任务必须引用对应规则：

```text
Design → Spec Rule → ADR（如有）→ EXEC → Code → Test
```

测试名称或测试说明应能追溯至少一个 Spec/AC ID。

## 7. Codex 的设计权限

### 7.1 Codex 可以自行决定

仅在不改变公共行为和系统边界的前提下，Codex 可以决定：

- 局部变量和私有函数命名；
- 私有函数拆分；
- 单模块内部等价重构；
- 测试 fixture 的局部组织；
- 不改变公共契约的错误消息细节；
- Spec 明确标记为 `MAY` 的实现选项。

### 7.2 Codex 不得自行决定

Codex **禁止**自行改变：

- bounded context 和模块边界；
- 状态所有权；
- 公共领域对象语义；
- 数据库领域模型和迁移语义；
- API / Command / Event Schema；
- 算法 baseline 或模型升级；
- 教学策略业务规则；
- 错误、重试和降级语义；
- 安全和隐私策略；
- 技术栈、基础设施或新增生产依赖；
- 跨模块调用方向。

## 8. SPEC GAP 协议

当 Codex 遇到下列情况时必须标记 `SPEC GAP`：

- 两份高权威规范互相冲突；
- 任务要求改变状态所有权或公共接口；
- 关键错误语义未定义；
- 需要新增生产依赖或基础设施；
- 存在多个会产生不同业务结果的合理实现，而 Spec 未指定；
- 为完成任务必须违反任一 `MUST NOT`。

处理规则：

1. 完成所有不依赖该缺口的工作；
2. 不对缺口做隐式架构选择；
3. 在执行结果中报告 `SPEC GAP`、受影响规则、候选方案与最小需要决策；
4. 等待 Spec/ADR 更新后再实现该部分。

## 9. Legacy Code 规则

当前代码结构是实现历史，不是最终领域边界。现有 `engines/`、`services/dkt/`、`services/kt/`、`services/documents/`、`services/knowledge_graph/` 等目录可以在迁移期继续存在，但：

- 不得因为历史目录存在就获得新的状态所有权；
- 新功能必须遵循 Target Architecture；
- 旧能力跨越多个未来系统时，应通过执行计划逐步拆分，而不是继续扩大耦合；
- 迁移过程中允许 adapter/compatibility layer，但必须有删除条件；
- 禁止产生第二套长期并存的业务事实源。

## 10. 规范变更流程

```text
发现需求/问题
→ 判断是否影响 Canonical Design
→ 如影响：先修改 design 并形成 ADR
→ 更新 Spec
→ 创建/更新 EXEC Plan
→ Codex 修改代码与测试
→ 验收
```

严禁先让 Codex 改代码，再倒推规范合理化实现。

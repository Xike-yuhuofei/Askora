# Askora 文档中心

> 状态：当前文档索引  
> 产品基线：`docs/product/PRODUCT-POSITIONING.md` Frozen Baseline  
> 学习内核基线：v0.3 Adaptive Teaching Loop  
> 最近校准：2026-08-10

`docs/` 保存 Askora 的上位产品定位、正式设计、架构决策、实现合同、执行归档和发布证据。同一事实只能有一个当前权威来源；当前合同、历史记录与实施证据不得混为一类。

## 1. 权威顺序

发生冲突时必须按以下顺序处理：

```text
docs/product/PRODUCT-POSITIONING.md
        ↓
docs/design/ 中当前有效的 Canonical Design / Design Delta
        ↓
docs/adr/ 中 Accepted / current-not-superseded decisions
        ↓
docs/specs/ Canonical Implementation Contracts
        ↓
docs/exec-plans/ Active EXEC
        ↓
当前代码、迁移与可执行测试
        ↓
Release Evidence / Research / Historical Records
```

[`product/PRODUCT-POSITIONING.md`](product/PRODUCT-POSITIONING.md) 是 Askora 产品级最高约束，冻结产品本质、v1 Scope、运行模型、数据边界、Non-goals 与 Hard Constraints。任何 Canonical Design、ADR、Spec、EXEC 或代码都不得自行 supersede 它；若必须突破，应先形成 Product Positioning Delta，并由用户接受后重新冻结，再同步下位治理文档。

代码与 Spec 冲突时默认属于 implementation drift，不得反向修改 Spec 迁就代码。Spec 与 Accepted ADR/Canonical Design 冲突时，应修正 Spec；ADR 与当前 Canonical Design 冲突时，应通过明确 supersession 处理；任何下位文档与 Product Positioning 冲突时，均视为上位对齐缺口。

Research 解释“为什么这样设计”，不能直接作为实现接口合同。历史 ADR/Vertical Slice/Release Report 可以保留当时事实，但必须明确哪些 mechanics 已被后续上位决策 supersede。

## 2. 当前 v1 产品/架构基线

最新 Product Positioning 冻结的正式产品运行模型：

```text
Browser (Chrome / Edge prioritized)
        ↓ loopback
Askora Local Server
├── Application / Learning Core
├── SQLite
├── Managed Local Files
├── Local Derived Indexes
├── Durable Local Jobs
└── BYOK AI Provider Adapter
        ↓ Internet when needed
External AI APIs
```

核心架构含义：

- Local Web Application 是 v1 正式产品形态，不是临时开发壳；
- macOS/Windows 原生客户端、Electron/Desktop shell 不属于 v1；
- 单用户、无 Account/Login/RBAC/Tenant；LocalOwner 是长期本地数据归属主体；
- Workspace 是高层隔离边界，不是 Tenant/Organization；
- SQLite 是 production-local structured persistence baseline；
- Redis/PostgreSQL/Docker/Kafka/Kubernetes 不得成为最终用户运行前提；
- Material Import = ingest + copy 到 Askora managed data directory；
- LearningEvidence 是 LearnerState 的事实基础；LearnerState/MasteryEstimate 是 SYS03 single-writer canonical rebuildable projections；
- SourceChunk/Embedding/Index/cache 是可重建 derived data；
- BYOK Secret 仅本地安全存储；Browser/普通 DB/日志/默认 Backup/Export 不持有 secret；
- v1 core import 为 EPUB、文本型 PDF、Markdown、TXT；完整 OCR Pipeline 不属于 v1 core；
- SYS01～SYS08 Learning Core、v0.3 deterministic Teaching Policy 继续保留，不因外围产品形态变化重做。

本轮 Product Positioning Alignment 已下沉到：

- `specs/architecture/system-architecture.md`；
- `specs/architecture/state-ownership.md`；
- `specs/architecture/dependency-rules.md`；
- `specs/domain/domain-model.md`；
- `specs/interfaces/persistence-contract.md`；
- `specs/interfaces/content-ingestion-contract.md`；
- `specs/systems/01-library-management.md`；
- `specs/systems/02-retrieval.md`；
- `specs/systems/03-learner-model.md`；
- `specs/systems/08-model-configuration.md`；
- `adr/ADR-0008-*` / `ADR-0013-*` supersession markers；
- `adr/README.md` / `specs/README.md` authority/index。

这些是**下位合同对齐**，不创建新的产品定位 truth，也不改变 v0.3 Teaching Policy ontology。

## 3. 目录与生命周期

| 路径 | 性质 | 当前状态 | 更新规则 |
|---|---|---|---|
| [`product/PRODUCT-POSITIONING.md`](product/PRODUCT-POSITIONING.md) | Product Boundary / Top-level Constraint | Frozen Baseline | 只有明确 Product Positioning Delta 且经用户接受后才能改变产品边界 |
| [`design/`](design/README.md) | Canonical Design / current conformance audit | current + historical mixed | 必须服从 Product Positioning；Design Delta 不能隐式扩大 v1 scope |
| [`adr/`](adr/README.md) | Architecture Decision Records | accepted + partially superseded history | 必须服从 Product Positioning；历史 ADR 保留并标记 supersession，不反向覆盖上位边界 |
| [`specs/`](specs/README.md) | Canonical Implementation Contract | v0.3 Learning Core + v1 alignment | 直接约束实现；必须与 Product/Design/ADR 一致 |
| [`exec-plans/`](exec-plans/README.md) | Implementation Task Contracts | active/completed（EXEC-042 已归档 DONE） | active EXEC 必须服从最新 Spec；实时状态以该目录索引为准 |
| [`releases/`](releases/README.md) | Release / Verification Evidence | historical/current snapshots | 历史测试结果不得当作当前 checkout 自动继续通过 |
| [`design/research/`](design/research/README.md) | Research Evidence / Synthesis | historical/supporting | 支持设计依据，不是直接实现合同 |
| [`document-inventory.md`](document-inventory.md) | 文档处置清单 | current | 文档治理后维护 disposition；部分 superseded ADR 可继续 retain 为决策历史 |

## 4. 当前关键治理边界

### 4.1 Learning Core

v0.3 Learning Core 的核心 invariants 继续有效：

```text
Knowledge / Material content semantics → SYS01
EvidenceBundle / RetrievalTrace        → SYS02
LearnerEvidence / LearnerState         → SYS03
Attempt / AssessmentResult             → SYS04
TeachingAction / Teaching Policy       → SYS05
Goal / Plan / Activity                 → SYS06
ReviewSchedule                         → SYS07
Model / Tool Execution                 → SYS08
```

并继续要求：

```text
TeachingStage != LearnerState
AssessmentResult != MasteryEstimate
DecisionTrace != OutcomeObservation
Conversation != LearningEvidence
SYS02/SYS08 only tighten TeachingAction envelope
LLM/Agent never directly writes canonical learning state
```

### 4.2 Platform Scope

Learning Core 外允许存在 Platform owner，但不能被误建模为“第九学习系统”：

```text
LocalOwner
Workspace / LearningProject relationships
Configuration / SecretStore
Local Job Runtime
Backup / Restore / Schema Migration
Local Observability
```

Workspace 负责 scope/isolation，不取得 SYS01～SYS08 的领域写权限。

Learning Core closure 已归档：
- [`EXEC-042 — v0.3 Production Sequential Teaching Policy Closure`](exec-plans/completed/EXEC-042-v0.3-production-sequential-teaching-policy-closure.md)：P0 Policy Correctness closure（已归档 DONE）；
- [`EXEC-1062 — P1-06B Onboarding Product Closure`](exec-plans/completed/EXEC-1062-p1-06b-onboarding-product-closure.md)：独立 P1-06 产品任务域。

### 4.3 Historical Supersession

当前需要特别注意：

- `ADR-0008`：OCR-as-v1-core、global/current-user library scope、archive-as-primary-delete mechanics 已被 Product Positioning 部分 supersede；metadata/provenance/dedup-as-suggestion 等原则保留。
- `ADR-0013`：Electron `safeStorage`、desktop vault/IPC/launcher mechanics 已被 Product Positioning 部分 supersede；SYS08 routing owner、secret separation、probe/revision/rollback/no-silent-failover 原则保留。
- `ADR-0009` / `ADR-0107`：Account/AuthSession/Account Deletion 产品语义由 ADR-0015 与 Product Positioning supersede；owner-safe data governance 继续有效。
- P1-04C OCR、P1-02 Desktop Model Settings、P1-05 Account Lifecycle 的历史实现/Release Evidence 可以保留，但不得成为 v1 新实现的上位依据。

## 5. Current Conformance 与 Release Evidence

历史 release report 只代表对应 commit/time 的验证快照。当前 checkout 是否满足 Engineering / Policy Correctness / Learning Evidence Gate，必须使用当前 main 的测试/CI/审计证据重新判断。

三类 Gate 必须始终分离：

```text
Engineering Gate
Policy / Contract Correctness Gate
Learning Evidence Gate
```

架构对齐、Local Web migration、Workspace isolation、SQLite correctness、OCR/Desktop 退役或 UI 改进都不能被描述为“已证明真人学习效果更好”。

Learning Evidence 的主要结果变量仍是：

- 无提示独立成功；
- 延迟保持；
- 独立迁移；
- 单位学习时间能力增益。

engagement、对话轮次、点赞、使用时长、阅读百分比等不得成为核心学习 KPI。

## 6. 设计系统边界

顶层导航、首页职责、页面布局、页面级 IA、交互入口、控件与具体 UX Flow 不在 Product Positioning 中冻结；这些事项继续由 **设计系统 → 交互元素（Interactive Elements）** 的 Canonical Design / ADR / UI Specs 冻结。

Product Positioning 只约束这些设计不得突破产品边界，不替代交互设计本身。

## 7. 执行代理规则

任何新的 Codex/engineering task 开始前：

1. MUST 读取 `docs/product/PRODUCT-POSITIONING.md`；
2. MUST 读取相关 Canonical Design / Accepted ADR / Spec；
3. MUST 检查历史 ADR 是否已 partially superseded；
4. 发现代码与 Spec 不一致时按 implementation drift 处理；
5. 发现 Spec/ADR 与 Product Positioning 不一致时先做文档对齐；
6. 如果目标必须突破 Product Positioning，必须停止并报告 Product Positioning Gap，由用户决定是否修改上位基线；
7. 不得因为历史代码存在 Electron/Redis/PostgreSQL/OCR/Auth 等路径就把它们重新提升为 v1 requirement。

## 8. 文档质量门禁

```bash
python3 .github/workflows/check_docs.py
```

门禁检查受 Git 跟踪的 Markdown/RST 本地链接和已知过时状态措辞。链接通过不能代替语义一致性审查，也不能代替相关测试/CI/release verification。

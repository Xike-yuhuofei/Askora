# Askora 文档中心

> 状态：Current Documentation Authority Index  
> 基线：GitHub `main` / `c293f5697bbff4bf050626d3c38addb9d78c3b4e`
> 最近校准：2026-08-11

这里是 Askora 长期文档的唯一导航入口。文档架构的目标不是按文件名收纳，而是让每份信息都有明确职责、authority、lifecycle 与唯一 current owner。

## 1. 从问题出发导航

| 我想知道…… | 入口 |
|---|---|
| Askora 为什么存在、服务谁、成功是什么 | [Product Strategy](product/PRODUCT-STRATEGY.md) |
| Askora 是什么、不是什么、v1 的硬边界 | [Product Positioning](product/PRODUCT-POSITIONING.md) |
| Askora 必须具备哪些能力、规则与产品验收 | [Product Definition](product/PRODUCT-DEFINITION.md) |
| 当前 Product 文档各自负责什么 | [Product Index](product/README.md) |
| 用户如何理解、导航和操作 Askora | [Experience Architecture](design/experience/EXPERIENCE-ARCHITECTURE.md) |
| Course-centric IA 为什么改变、冻结了什么 | [Course-centric IA Design Delta](design/features/course-centric-information-architecture-canonical-design-delta.md) 与 [ADR-0022](architecture/decisions/ADR-0022-course-centric-information-architecture.md) |
| 学习交互、Conversation、Attempt、Feedback 如何成立 | [Learning Experience](design/experience/LEARNING-EXPERIENCE.md) |
| 交互原语、层级与 progressive disclosure | [Interaction Model](design/experience/INTERACTION-MODEL.md) |
| Teaching / Learner Model / Assessment / Planner 的冻结设计 | [Learning Design Index](design/README.md) |
| 软件边界、single writer、运行架构 | [System Architecture](specs/architecture/system-architecture.md) 与 [State Ownership](specs/architecture/state-ownership.md) |
| 某个长期架构选择为什么这样决定 | [Architecture / ADR Index](architecture/README.md) |
| 我要实现一个功能，应读哪些合同 | [Implementation Specs](specs/README.md) |
| 正式 UI / UX implementation contracts | [UI Spec Index](specs/ui/README.md) |
| 当前代码在哪里、模块负责什么 | [Engineering Guide](engineering/README.md) |
| 现在仍可执行哪些 EXEC | [Planning Index](planning/README.md)，实时状态再核对 Linear |
| 产品或 Learning Core 的研究依据 | [Research Index](research/README.md) |
| 外部 Desktop UI 的截图逆向、布局测量与 Figma 研究输入 | [TraeCode UI Reverse Engineering](ui-reverse-engineering/00-overview.md) |
| 测试、安全、可观测性与 Definition of Done | [`specs/quality/`](specs/quality/) |
| 历史 Gap、旧设计、完成 EXEC、Release Evidence | [Archive](archive/README.md) |
| 新文档应该放在哪里、冲突如何处理 | [Documentation Governance](governance/README.md) |
| 每份文档从哪里迁到哪里、为何这样处置 | [Document Inventory](governance/document-inventory.md) |
| 产品到交付的端到端流程 | [Product Development Process](governance/product-development-process.md) |

## 2. Authority Chain

```text
docs/product/PRODUCT-STRATEGY.md
        ↓ Why / Who / Problem / Value / Success
docs/product/PRODUCT-POSITIONING.md
        ↓ Category / Product Shape / Hard Boundaries
docs/product/PRODUCT-DEFINITION.md
        ↓ Capabilities / Product Rules / Requirements / Product Acceptance
docs/design/ Canonical Design
        ↓ Experience / Learning / Feature semantics
docs/architecture/decisions/ Accepted ADR
        ↓ long-lived architecture choices
docs/specs/ Canonical Implementation / Quality Contracts
        ↓
docs/planning/ + Linear
        ↓
Code / Migration / Executable Tests
        ↓
docs/archive/ Release Evidence / Historical Records
```

Research 是所有层级的证据输入，不是并列 authority：

```text
Research Question
→ Evidence
→ Synthesis
→ Decision
→ Canonical Product / Design / ADR / Spec
→ Implementation
```

## 3. 目录树

```text
docs/
├── README.md
├── product/
├── design/
│   ├── experience/
│   ├── learning/
│   └── features/
├── architecture/
│   └── decisions/
├── specs/
│   ├── architecture/
│   ├── domain/
│   ├── systems/
│   ├── platform/
│   ├── interfaces/
│   ├── frontend/
│   ├── ui/
│   ├── quality/
│   └── vertical-slices/
├── research/
│   ├── product-discovery/
│   └── learning-core/
├── ui-reverse-engineering/
├── engineering/
├── planning/
│   └── execs/
├── governance/
└── archive/
    ├── audits/
    ├── design/
    ├── specs/
    ├── exec-plans/
    └── releases/
```

层级控制在 2–4 层。没有 current 文档的生命周期模块不预建空目录；例如未来出现稳定 runbook / incident / release process 时，再建立 `operations/`。

## 4. 目录职责

| 路径 | 应该进入 | 不应该进入 |
|---|---|---|
| `product/` | Strategy、Positioning、Definition、必要的 Product Feature Spec | UI、算法、API、schema、backlog |
| `design/experience/` | IA、User Flow、Interaction、UI 体验语义 | Product Scope、数据库合同 |
| `design/learning/` | Learning Core、Teaching、Evidence、Learner Model 的 canonical semantics | 研究综述、实现字段、当前 task 状态 |
| `design/features/` | 跨 Product/UX/System 的冻结 Feature Design | 普通小功能说明、一次性计划 |
| `architecture/decisions/` | 具有长期影响的 Accepted ADR | 普通实现记录、实时任务 |
| `specs/` | 有规范性语言、稳定合同、可验证 acceptance 的 current implementation/quality spec | Research、Gap、EXEC、Release Report |
| `research/` | Research Question、evidence、literature、finding、synthesis、protocol | 未经接受的 canonical decision |
| `ui-reverse-engineering/` | 外部 UI 截图证据、测量、结构假设与 Figma handoff | Askora Canonical Experience、UI Spec 或生产 Design Token |
| `engineering/` | Code Wiki、开发/构建/维护指南 | 第二套产品与架构事实 |
| `planning/` | 尚可执行的 EXEC 与执行提示 | DONE evidence、Canonical Design |
| `governance/` | 文档规则、流程、Inventory | 产品与技术内容本身 |
| `archive/` | audit snapshot、superseded design/spec、completed EXEC、release evidence | 新实现默认入口 |

## 5. `specs/` 为什么保留一级目录

Askora 的 `specs/` 不是所有“详细文档”的容器。文件只有在以下条件成立时才有资格进入：

- 有明确上位 Product / Design / ADR；
- 直接约束实现、迁移、兼容、错误、状态、接口或质量门禁；
- 使用 MUST / MUST NOT / SHOULD、稳定 requirement ID 或等价规范语言；
- 可以映射到自动化测试、迁移验证或明确验收；
- 声明 lifecycle 与 supersession；
- 不是 Research、Gap Analysis、EXEC 或 Release Report。

因此 current `architecture/domain/systems/platform/interfaces/frontend/ui/quality/vertical-slices` 仍留在 `specs/`；已被吸收或只代表历史交付范围的 UI Spec / Vertical Slice 已移至 `archive/specs/`。

## 6. Product / Experience / System 边界

```text
Product Strategy      WHY / WHO / VALUE / SUCCESS
Product Positioning   CATEGORY / HARD BOUNDARY
Product Definition    WHAT CAPABILITIES / BEHAVIORS / ACCEPTANCE
Experience Design     HOW THE USER UNDERSTANDS AND USES IT
Architecture / Specs  HOW THE SOFTWARE WORKS
```

特别地：

- Product Definition 中的 Workspace / Material / Goal / Activity / Evidence 是 Product Object；
- Experience IA 决定它们在哪里出现、如何导航和 progressive disclose；
- Architecture / Specs 决定 ownership、state、API、persistence 与 migration；
- SYS01～SYS08 是技术/教学 ownership，不是 Product Capability taxonomy；
- Research 解释依据，但不自动冻结任何一层。

## 7. Teaching / AI 文档边界

Askora 的 Teaching / AI 资产按职责分布：

- 产品承诺与可观察行为 → `product/PRODUCT-DEFINITION.md` 的 `CAP-02..07`；
- Teaching、Learner Model、Assessment、Planner 的共享语义 → `design/learning/`；
- 长期系统选择与 owner 决策 → `architecture/decisions/`；
- 可直接实现的 SYS01～SYS08 合同 → `specs/systems/`；
- 接口、数据、错误、持久化 → `specs/interfaces/`、`specs/domain/`、`specs/platform/`；
- 教育科学、ITS、检索、复习、LLM 治理证据 → `research/learning-core/`；
- 历史设计与交付证据 → `archive/`。

不得把这些内容因“都与 AI 有关”而重新堆入单一 `design/` 或 `ai/` 目录。

## 8. Lifecycle

| Lifecycle | 意义 | 默认位置 |
|---|---|---|
| Canonical / Current | 当前唯一正式事实源 | Product / Design / Architecture / Specs |
| Active Planning | 已冻结且仍可执行，状态需核对 Linear | `planning/` |
| Research / Supporting | 决策输入，允许保留不确定与冲突 | `research/`；外部 UI 逆向证据在 `ui-reverse-engineering/` |
| Historical / Superseded | 保留演进或迁移证据，不再 current | `archive/` |
| REVIEW | 重要但归属/authority 无法安全判断 | 原地保留并进入 Inventory，不猜测 |

Gap Analysis 只对记录的 commit/time 有效；Release Report 只证明当时候选 SHA；completed EXEC 只证明当时任务合同。三者都不能用来声称 current checkout 已通过。

## 9. Conflict Rule

- Strategy 与 Positioning 冲突 → `STRATEGY GAP` / Product Delta；
- Positioning 与 Product Definition 冲突 → `POSITIONING GAP`；
- Definition 与 Design / ADR / Spec 冲突 → 下位收敛或 `PRODUCT DEFINITION GAP`；
- Design / ADR 与 Spec 冲突 → 先修治理链；
- Spec 与代码冲突 → 默认 implementation drift；
- Research / Archive 与 current canonical docs 冲突 → 保留历史，但不覆盖 current truth；
- GitHub EXEC index 与 Linear 状态冲突 → Linear 管实时状态，随后修复或归档 GitHub 文档。

## 10. Professional App Development Framework 映射

本目录不机械复制 10 个 lifecycle module，而是按 Askora 当前真实资产压缩：

| Framework 工作 | Askora 文档位置 |
|---|---|
| Product Strategy & Discovery | `product/` + `research/product-discovery/` |
| Product Definition & Planning | `product/PRODUCT-DEFINITION.md` + `planning/` + Linear |
| Experience & Interface Design | `design/experience/` + `specs/ui/` |
| Architecture & Technical Design | `design/learning/` + `architecture/` + `specs/` |
| Engineering Implementation | `engineering/` + code |
| Quality Engineering & Risk Control | `specs/quality/` + executable tests |
| Engineering Platform & Delivery | `engineering/` + `.github/` + `planning/` |
| Release & Production Operations | current code/runtime docs；历史 release evidence 在 `archive/releases/` |
| Measurement & Product Learning | Product Strategy success model + `research/`；真人 Learning Evidence 独立报告 |
| Governance, Documentation & Evolution | `governance/` + `architecture/decisions/` + `archive/` |

Security、Privacy、Performance、Accessibility、Reliability、Observability 按 Product / Experience / Architecture / Quality / Operations 的实际职责落位，不各自创建一级目录。

## 11. 维护规则

1. 新 Agent 从本页开始，不从历史文件或代码目录反推产品范围；
2. 路径变更使用 `git mv`，同时修复链接、代码注释、CI 与 scripts；
3. current canonical truth 不复制到 Archive、Linear 或 EXEC；
4. 已被 consolidated 的旧文件归档，不要求 Agent 通过 supersession matrix 拼出 current truth；
5. 不因文件旧而删除；只有完全重复且无独立证据价值的文件才可删除，并记录替代来源；
6. 每次文档架构变更同步 [Inventory](governance/document-inventory.md)；
7. 至少运行 `python3 .github/workflows/check_docs.py` 与 `git diff --check`。

# Askora PRODUCT-DEFINITION

> 文档状态：Canonical Product Definition Baseline  
> 冻结日期：2026-08-13  
> 适用范围：Askora v1 Product Definition 及后续 Experience Design / Spec / Linear 工作  
> 上游战略：[`PRODUCT-STRATEGY.md`](PRODUCT-STRATEGY.md)  
> 上游产品边界：[`PRODUCT-POSITIONING.md`](PRODUCT-POSITIONING.md)  
> 文档职责：回答 Product Objects / Capabilities / Observable Behaviors / Product Rules / Requirements / Product Acceptance / Version Scope  
> 不包含：页面布局、导航实现、Teaching Policy 算法、API、数据库 schema、class/module、state-management mechanics、实时 backlog

---

## 1. Purpose

本文件定义：

> **为了履行 Askora 已冻结的产品承诺，产品本身必须具备什么能力、表现出什么可观察行为、遵守什么产品规则，以及当前 v1 哪些能力属于正式范围。**

它位于 Product Positioning 与下游 Experience Design / Specs 之间。完整权威顺序见 [`../README.md`](../README.md) 与仓库根 `AGENTS.md`。

本文件**不是 Master Technical PRD**。它只冻结用户或产品层可观察的 WHAT；下游 HOW 必须在 Experience Design 与 Specs 中定义。Decision Log / ADR 只解释为什么这样选，不是现行合同。

---

## 2. Authority and Boundary

### 2.1 Upstream

本文件必须服从：

1. [`PRODUCT-STRATEGY.md`](PRODUCT-STRATEGY.md)：Why / Who / Problem / Value / Success；
2. [`PRODUCT-POSITIONING.md`](PRODUCT-POSITIONING.md)：Category / Product Shape / Hard Boundaries / Non-goals。

若本文件与上游冲突，属于 `PRODUCT DEFINITION GAP`，不得通过下游实现反向覆盖 Strategy / Positioning。

### 2.2 Downstream

下游必须从本文件获得产品层输入：

- Experience Design：决定用户如何理解、导航和操作已定义 capability；
- `docs/specs/systems/`：决定学习能力内部如何通过 Teaching Policy / Learner Model / Assessment 等成立；
- `docs/specs/architecture.md` 与相关 Specs：决定 software ownership、state、persistence、interface 与 dependency；
- `docs/specs/quality.md`：决定 reliability / security / performance / accessibility 等验证合同；
- Linear：管理当前实施优先级、Milestone、Issue、dependency 与状态。

### 2.3 Explicit Non-ownership

本文件不拥有：

- route / screen / drawer / right rail / component；
- Interaction Pattern / Design Token；
- StrategyFamily / TeachingStage / PolicyBundle scoring algorithm；
- Mastery estimation algorithm；
- API endpoint / request payload；
- SQLite table / migration；
- ORM / class / module / Hook；
- retry / queue / concurrency / cache / logging mechanics；
- current work status。

---

## 3. Product Actors

Askora v1 只需要最小 actor model。

### PD-ACTOR-001 — Learner

**Learner** 是唯一主要最终用户：一个进行长期自主学习、提供自己的学习材料与目标、执行学习活动并产生学习证据的人。

### PD-ACTOR-002 — LocalOwner

**LocalOwner** 表示本地产品数据的归属主体。在 v1 中 Learner 与 LocalOwner 对应同一个自然人，但 `LocalOwner` 不是 Account、Login Identity 或 SaaS User。

### PD-ACTOR-003 — External AI Provider

外部 AI Provider 是可替换的外部能力提供方，而不是 canonical product-state owner。它可以提供生成、理解、评估辅助、embedding/extraction 等 AI 能力，但不能自行成为 Learning Goal、Learner State、Assessment、Plan、Teaching Decision 或 Review truth。

---

## 4. Core Product Objects

本节只定义**产品语义对象**。字段、schema、revision、event、DTO 与 storage semantics 由 `docs/specs/**` 定义。

| Product Object | Product Meaning | Not This |
|---|---|---|
| `Workspace` | 一个长期学习上下文与数据隔离范围 | route、frontend state、tenant |
| `LearningProject` | 在 Workspace 内围绕一个长期学习主题/目标组织材料与学习工作的产品对象 | team project、Linear Project |
| `Material` | 用户主动纳入 Askora、作为学习知识来源的资料 | retrieval chunk、embedding row |
| `UserNote` | 用户围绕学习材料或学习过程主动沉淀的个人笔记 | AI-generated knowledge truth |
| `LearningGoal` | 用户希望形成的长期能力目标及其成功条件 | 单次 prompt、聊天主题 |
| `LearningObjective` | 可被学习活动与评估验证的阶段性目标 | UI checklist item |
| `LearningPlan` | 为达成目标而形成、可根据新证据调整的学习活动组织 | 静态课程目录 |
| `LearningActivity` | 一次有明确学习目的、能够产生行为与证据的学习单元 | 单条 message |
| `LearningSession` | 用户在一段连续时间内围绕学习活动发生的学习过程 | authentication session、DialogSession 的同义词 |
| `Attempt` | 学习者对问题、任务或评估要求作出的实际尝试 | AI 对用户能力的猜测 |
| `LearningEvidence` | 能支持或限制 Learner State 判断的可审计学习行为证据 | conversation、阅读完成本身 |
| `LearnerState` | 基于证据形成的当前学习状态表达 | 单次 AssessmentResult、主观“我懂了” |
| `Review / Validation Obligation` | 因保持、迁移、受助或答案暴露等原因，需要未来重新验证能力的学习责任 | calendar reminder 本身 |
| `LearningHistory` | 可追溯的学习活动、证据与状态变化历史 | 第二份 canonical state |

产品对象之间的精确 cardinality、revision、single-writer、persistence 与 lifecycle state machine 不在本文件定义。

---

## 5. Product Capability Model

Capability 是 Askora 能够长期履行的**稳定产品能力**，不是页面、菜单、技术系统或短期 Feature List。

Capability taxonomy 必须满足：

```text
Strategy / Product Job
→ Capability
→ Feature / Scenario
→ Product Requirement
→ Product Acceptance
→ downstream Design / Specs
```

不得反向使用：

```text
Page / Component / SYSxx
→ Product Capability
```

### CAP-01 — Learning Context & Material Grounding

Askora 必须能够让用户建立受控的长期学习上下文，把自己提供的材料纳入学习范围，并保持来源可追溯。

当前 v1 包含：

- Workspace-scoped learning context；
- Material 导入、组织与生命周期管理；
- 文本型 EPUB、PDF、Markdown、TXT 作为正式 core import 范围；
- Material → 可学习内容/知识供给；
- source-grounded citation / provenance；
- 用户学习笔记作为辅助沉淀能力。

当前 v1 不要求：完整扫描 OCR、互联网自动探索、开放内容 marketplace、全局跨 Workspace Library。

### CAP-02 — Learning Goal & Success Definition

Askora 必须能够把材料与学习过程形成可持续维护、可验证的 Learning Goal / Objective，供规划、教学与验证使用。

产品必须支持：

- 从材料与（若有）自然语言意图形成目标；
- 明确目标能力、应用情境与成功条件；
- 由系统按产品规则采纳并维护 Goal，开始学习不以用户确认目标为前置；
- 目标暂停、调整、重规划与证据约束下的 achievement；
- 不把“完成活动”自动等同“目标已达成”；
- 不把目标管理做成用户主路径工作。

### CAP-03 — Readiness, Diagnosis & Learning Planning

Askora 必须能够判断学习是否具备开始条件、识别重要先备缺口，并产生当前最有价值的学习活动计划。

产品必须支持：

- 将材料、Goal 与可用学习状态组合为 readiness；
- 在必要时进行 prerequisite / diagnostic activity；
- 根据目标、知识结构、Learner State、时间与 review obligation 形成 LearningPlan；
- 选择下一 LearningActivity；
- 当新证据使原计划失效时能够 replan。

### CAP-04 — Adaptive Learning Activity

Askora 必须能够围绕当前 LearningActivity 提供 AI 辅助教学，并根据学习者状态、实际表现与帮助历史调整下一步教学行为。

产品必须支持：

- 讲解、提问、提示、反馈、练习等多种教学交互；
- 根据 evidence 调整支架强度与下一教学动作；
- 用户可以要求解释、答案、跳过或调整学习过程；
- 用户请求不能追溯性伪造 evidence semantics；
- AI 输出必须受产品与教学规则约束，而不是自由 LLM chat 决定核心状态。

### CAP-05 — Attempt, Assessment & Learning Evidence

Askora 必须能够从真实学习行为中形成可审计证据，并区分“系统帮助下成功”和“真正独立掌握”。

产品必须支持：

- 记录学习者实际 Attempt；
- 对 Attempt 形成 Assessment / diagnosis；
- 区分 independent / assisted / answer-exposed；
- 区分 immediate / delayed / transfer evidence；
- 基于 Learning Evidence 更新 Learner State；
- 系统故障或模型失败不得被记录为 learner failure。

### CAP-06 — Review, Retention & Transfer Validation

Askora 必须能够跨时间重新验证能力，而不是把一次即时成功视为长期掌握。

产品必须支持：

- 产生 review / validation obligation；
- 延迟后的独立 retrieval / performance validation；
- transfer challenge；
- 受助或答案暴露后重新要求 fresh independent validation；
- 根据保持与迁移结果调整 Learner State / Plan / Review。

### CAP-07 — Learning Continuity & Next-step Orientation

Askora 必须让用户能够在跨天、跨 session 的长期学习中知道：当前正在学什么、为什么做这一步、下一步是什么，以及历史如何支持当前判断。

产品必须支持：

- 恢复当前 Workspace / Project / LearningActivity 上下文；
- 解释当前推荐学习行动的产品级原因；
- 查看必要的 Goal / Plan / Evidence / History 信息；
- 保持 LearningHistory 可追溯；
- 不要求用户通过管理复杂内部系统状态才能继续学习。

具体“这些信息放在哪个页面、是否 drawer、是否常驻导航”等属于 Experience Design。

### CAP-08 — Local Data & AI Control

Askora 必须让个人能够在本地掌控核心学习数据和外部 AI 使用方式，同时不承担服务端运维负担。

当前 v1 包含：

- single-user / single-device Local Web；
- 无注册、登录、账号、Tenant / RBAC；
- 核心学习数据本地持有；
- backup / restore / export / erasure；
- Material Trash / Restore / Permanent Delete；
- BYOK AI Provider 配置与安全 credential handling；
- 外部 AI 不可用时保持诚实 failure semantics。

最终用户不得被要求运维 Docker、Redis、PostgreSQL 或 Askora 官方中心服务器才能正常使用核心产品。

---

## 6. Capability vs Feature vs Implementation

统一粒度：

```text
Capability
  = 长期稳定的产品能力

Feature
  = 为实现 capability 而提供的一组具体用户可观察行为

Scenario / Use Case
  = 用户在什么情境下使用 feature 达成什么结果

Product Requirement
  = 产品在该场景下必须满足的可观察条件

Product Acceptance Criteria
  = 如何判定该 requirement 在产品行为层成立

Implementation Contract
  = UX / Teaching / Architecture / Quality 如何具体实现和验证
```

示例：

```text
CAP-08 Local Data & AI Control
↓
Feature: Material Trash / Restore / Permanent Delete
↓
Scenario: 用户误删资料后希望恢复
↓
Requirement: 普通删除必须可恢复，永久删除必须明确且不可伪装成普通删除
↓
Product AC: 用户在普通删除后仍可从 Trash 恢复同一 Material identity
↓
MATLIFE-* / persistence / UX / tests
```

---

## 7. Product Requirement Hierarchy and IDs

正式层级：

```text
Product Strategy / Product Outcome
↓
Product Positioning / Boundary
↓
CAP-xx Capability
↓
Feature（复杂 capability 才需要独立 Feature Spec）
↓
Scenario / Use Case
↓
PD-REQ-* Product Requirement
↓
PD-AC-* Product Acceptance Criteria
↓
Design / ADR / Spec
↓
Linear Issue / EXEC
↓
Implementation
```

### 7.1 Product Requirement Rule

`PD-REQ-*` 必须描述用户或产品可观察行为，不得直接规定：

- React Component / Hook；
- API endpoint / payload；
- SQLite schema；
- Python class / module；
- queue / cache；
- concrete model algorithm。

### 7.2 Business / Product Rule

Business Rule 是横切约束，不强制成为层级中的独立“下一层”。使用 `PD-RULE-*`，可以约束多个 capability / requirement。

### 7.3 Feature Specs

只有满足以下任一条件才创建 `docs/product/features/<feature>.md`：

- 一个 feature 跨多个 capability；
- 独立包含多组 scenario / rules / Product AC；
- 经常独立演进；
- 单独作为多个 UX / Architecture / Engineering 工作的稳定上游输入。

简单 feature 继续留在本文件，不为“文档专业化”创建额外文件。

---

## 8. Canonical Product Rules

### PD-RULE-001 — Learning Outcome > Engagement

产品不能用 message count、session length、token usage、reading percentage、likes 或 activity completion 作为核心学习成功证明。

### PD-RULE-002 — Conversation != Learning Evidence

Conversation / Message 可以承载教学交互，但只有满足 evidence contract 的真实学习行为才能成为 Learning Evidence。

### PD-RULE-003 — Assistance / Exposure Semantics Are Irreversible Facts

系统必须保持 independent、assisted、answer-exposed 等证据语义。用户要求答案可以被允许，但不能把已暴露答案的表现重新标成无提示独立成功。

### PD-RULE-004 — Goals Are System-maintained Planning Facts

系统根据材料与学习过程生成并维护 Learning Goal / Objective。开始学习不以用户确认目标为前置。目标不是用户主路径上的管理对象。

这是 DOMAIN-010 所称的「显式产品规则」：SYS06 按本合同采纳的 Goal 即可成为 `active` planning fact，不要求单独的用户确认步骤。LLM 仍不得无约束拥有 Goal truth（`PD-RULE-005`）。系统在 mapping 存在 blocking ambiguity 时 MAY 做最小澄清，但不得把确认目标做成开始学习的必经步骤。

### PD-RULE-005 — LLM Is Not Canonical Product Authority

LLM / Agent 可以生成、解释、建议和执行受控工具，但不能无约束拥有 Learning Goal、Learner State、Assessment truth、LearningPlan、TeachingAction 或 ReviewSchedule。

### PD-RULE-006 — Source-grounded Claims Must Be Traceable

任何向用户宣称“来自你的材料”的事实必须可追溯到真实 source。模型外部知识与 source-grounded knowledge 必须保持可区分。

### PD-RULE-007 — Learning State Must Be Evidence-backed

“用户说懂了”“AI 认为懂了”“阅读完成”或“刚才做对”不能单独支持稳定掌握。

### PD-RULE-008 — Local Single-user Product

v1 无 Account / Login / Password / AuthSession / Tenant / RBAC。LocalOwner 只表示本地数据归属。

### PD-RULE-009 — Workspace Is a Real Product Scope

Workspace 切换必须改变相关学习材料、目标、活动、状态、检索与用户可见上下文的真实范围，不得只是 UI selected state。

### PD-RULE-010 — Failures Must Not Forge Learning Meaning

Provider、network、parsing、storage 或 runtime failure 不得伪造成 learner error、mastery change 或完成证据。

### PD-RULE-011 — Current Scope Is Explicit

历史代码、历史 Release、实验实现或 optional subsystem 的存在不得自动升级为当前 v1 Product Requirement。

---

## 9. Baseline Product Requirements

以下 requirement 是当前冻结产品语义的高层入口；更细技术 requirement 继续由 Specs 拥有。

### CAP-01 Requirements

- `PD-REQ-0101`：用户必须能够把受支持的本地学习材料纳入指定 Workspace，并在后续学习中持续引用同一 Material identity。上传可以先创建尚未归属 Workspace 的 Material；开始有依据的学习前，该 Material 必须已归属某一 Workspace。
- `PD-REQ-0102`：v1 core material import 至少覆盖 EPUB、文本型 PDF、Markdown、TXT；扫描 OCR 不属于 v1 core requirement。
- `PD-REQ-0103`：材料驱动的解释、引用和学习证据必须保持 source provenance。
- `PD-REQ-0104`：普通 Material 删除必须进入可恢复生命周期；永久删除必须是独立明确动作。

### CAP-02 Requirements

- `PD-REQ-0201`：系统必须能够从材料与（若有）自然语言意图形成 Goal，而不是要求用户提供内部 ID 或先填写目标表单。
- `PD-REQ-0202`：正式 Goal 必须包含足以判断学习成功的产品级能力/成功条件；不可验证的“了解/熟悉”不能作为唯一成功定义。
- `PD-REQ-0203`：开始学习不要求用户确认 Goal。Goal 由 SYS06 按 `PD-RULE-004` 采纳为 planning fact；主路径不出现目标管理。

### CAP-03 Requirements

- `PD-REQ-0301`：系统必须能够判断从 Material + Goal 到真实学习是否已具备必要 readiness，并诚实暴露阻塞原因。
- `PD-REQ-0302`：重要 prerequisite 未知时，系统应通过真实 diagnostic activity 获取证据，而不是直接猜测 mastery。
- `PD-REQ-0303`：LearningPlan / next activity 必须能够随着新的 Learner State、Review 或 Goal 变化而调整。

### CAP-04 Requirements

- `PD-REQ-0401`：每个 canonical LearningActivity 必须具有明确学习目的，而不是把自由聊天本身视为学习活动。
- `PD-REQ-0402`：系统必须能够依据当前 context 与新 evidence 调整教学支持和下一动作。
- `PD-REQ-0403`：用户显式请求直接解释或答案时，产品可以满足，但必须保持 exposure/evidence 语义并安排必要的后续验证。

### CAP-05 Requirements

- `PD-REQ-0501`：系统必须记录真实 Attempt 与实际 assistance/exposure，而不是只保存最终答案正确与否。
- `PD-REQ-0502`：AssessmentResult 与 LearnerState 必须在产品语义上保持不同；一次评分不能直接等同长期掌握。
- `PD-REQ-0503`：LearnerState 变化必须能够追溯到 Learning Evidence。

### CAP-06 Requirements

- `PD-REQ-0601`：即时独立成功不能自动关闭保持/迁移验证需求。
- `PD-REQ-0602`：assisted / answer-exposed success 必须产生 fresh independent validation obligation。
- `PD-REQ-0603`：系统必须能够进行 delayed 与 transfer validation，并让结果影响后续学习计划或状态。

### CAP-07 Requirements

- `PD-REQ-0701`：用户恢复 Askora 时必须能够确定当前学习上下文与可继续的下一学习行动。
- `PD-REQ-0702`：用户必须能够在需要时理解 Goal / Plan / Progress-Evidence / History，但产品不得要求把这些内部 truth 全部作为常驻管理工作。
- `PD-REQ-0703`：历史必须用于可追溯与恢复，不得建立第二份独立 learning-state truth。

### CAP-08 Requirements

- `PD-REQ-0801`：Askora v1 的核心使用不得要求注册、登录或 Askora 官方中心云。
- `PD-REQ-0802`：核心学习数据必须以本地数据为权威，并支持 backup / restore / export / erasure。
- `PD-REQ-0803`：BYOK secret 必须与普通业务数据、日志、默认 backup/export 分离。
- `PD-REQ-0804`：最终用户不得被要求维护 Docker / Redis / PostgreSQL / distributed infrastructure 才能正常使用核心产品。

---

## 10. Product-level NFR Boundary

Product Definition 只冻结**用户可以感知或产品承诺需要成立的质量属性**。具体 threshold、测试方法与实现属于 Quality Specs。

### PD-NFR-001 — Durability / Recoverability

长期学习状态不能因为普通重启、页面刷新或可恢复故障而被静默丢失；关键本地数据必须具有明确 backup / recovery 路径。

### PD-NFR-002 — Privacy / Ownership

核心学习数据默认本地持有；向外部 AI Provider 发送的数据必须服从明确的 AI 使用边界，不得把本地运行描述成绝对离线。

### PD-NFR-003 — Explainability / Auditability

高影响 Goal / Teaching / Assessment / Learner State / Review 决策应能够提供足够来源或 reason 信息，使用户与开发者可以理解为什么发生。

### PD-NFR-004 — Failure Honesty

系统必须区分 product/runtime failure 与 learning result；失败时不得伪造成功、掌握或用户错误。

### PD-NFR-005 — Accessibility / Usability

核心学习任务必须能够通过当前正式 Web UI 完成，并服从当前 Quality / UI Accessibility contracts；具体 WCAG、responsive threshold 与 test oracle 由下游定义。

---

## 11. Product Acceptance Model

Askora 使用分层 Acceptance，禁止把所有“完成”混为一个 PASS。

| Acceptance Layer | Question | Canonical Owner |
|---|---|---|
| **Product Acceptance** | 产品行为是否满足 Capability / Requirement / User Outcome？ | 本文件或对应 Product Feature Spec |
| **UX Acceptance** | 目标用户能否理解并完成任务？ | Canonical Experience Design / UI Specs |
| **Technical Acceptance** | Domain / State / API / Teaching / Persistence 合同是否成立？ | ADR / Implementation Specs |
| **Quality Acceptance** | Reliability / Security / Performance / Accessibility 是否达标？ | `docs/specs/quality/**` |
| **Learning Evidence** | 是否真的改善 independent / delayed / transfer learning outcome？ | Learning evidence / experiment framework |

### 11.1 Product Acceptance Rules

- Engineering PASS ≠ Product Acceptance PASS；
- Product task success ≠ Learning efficacy；
- UI 可点击 ≠ capability 成立；
- synthetic learner ≠ human learning evidence；
- historical Release PASS ≠ current checkout conformance。

### 11.2 Capability-level Product Acceptance

| Capability | Minimum Product Acceptance |
|---|---|
| CAP-01 | 用户的受支持材料能够进入真实 Workspace 学习上下文，并在学习时保持来源与生命周期语义 |
| CAP-02 | 系统能够从材料形成可验证 Goal 并用于规划；开始学习不要求用户确认目标 |
| CAP-03 | 系统能够从真实状态判断 readiness、诊断必要缺口并给出可执行 next activity |
| CAP-04 | LearningActivity 能依据新 evidence 改变教学行为，且不绕过 evidence/exposure rules |
| CAP-05 | Attempt → Assessment → Evidence → Learner State 的产品语义可追溯且不混淆 |
| CAP-06 | 系统能形成并执行 delayed / transfer / fresh-independent validation 闭环 |
| CAP-07 | 用户能跨 session 恢复当前学习方向并理解必要历史，而无需管理内部系统对象 |
| CAP-08 | 用户可在无账号/官方云/外部基础设施运维前提下控制本地数据与 BYOK AI |

具体 feature 的 `PD-AC-*` 在该 feature 被正式设计或重构时按需增加，不在本基线制造虚假完备清单。

---

## 12. v1 Scope / Version Model

Product Definition 使用以下状态；实时实施状态仍属于 Linear。

### `CURRENT / COMMITTED`

属于当前 v1 正式产品定义，Design / Architecture / Engineering 可以据此形成实施任务。

### `DEFERRED`

可能有长期价值，但当前 v1 不承诺；不得创建 placeholder、disabled page 或空系统来“预留”。

### `EXPERIMENTAL`

可以为了学习效果、产品验证或技术验证存在，但不能自动成为 v1 committed capability，也不能形成第二 canonical truth。

### `NON-GOAL`

由 Product Positioning 明确排除。改变此状态必须先修改 Positioning。

### `RETIRED / SUPERSEDED`

历史曾存在，但当前产品定义已被新的产品边界或设计取代。实现可暂时兼容迁移，但不得重新作为新 requirement。

### 12.1 Current v1 Committed Capability Scope

当前八个一级 Capability `CAP-01`～`CAP-08` 均属于 `CURRENT / COMMITTED` 产品能力骨架。

这不表示每个 capability 的所有可能 feature 都已实现或都属于 v1；具体 Feature inclusion 必须由本文件、未来 Product Feature Spec 或现有已冻结上游/下游 trace 明确支持。

### 12.2 Explicit Deferred / Non-core Candidates

当前以下方向不得仅因已有历史实现而升级为 v1 core：

- full OCR workflow；
- global cross-workspace library/search；
- AI Summary 作为常驻产品域；
- Flashcards 作为独立核心产品域；
- Knowledge Graph management UI；
- Progress dashboard 作为常驻管理中心；
- autonomous open-ended Agent；
- native desktop/mobile client；
- cloud sync / multi-device sync。

其中与 Product Positioning 的正式 Non-goal 重叠者，以 Positioning 为最高 authority。

---

## 13. Product Definition ↔ Experience / Teaching / Architecture

### 13.1 Product Information Model vs Information Architecture

本文件拥有：

```text
Workspace / Material / Goal / Plan / Activity / Evidence / History
是什么、为什么存在、产品关系与行为约束
```

Experience Design 拥有：

```text
用户在哪里看到它
如何导航
是否页面 / drawer / rail / task flow
如何 progressive disclose
```

因此 `Information Architecture` 一词在 Askora 中专指用户可见 Experience IA，不再用于命名 Product Object / Capability taxonomy。

### 13.2 Product Capability vs Teaching System

例如：

> “系统根据新的学习证据调整下一步学习活动”

属于 Product Capability / Requirement。

但具体：

- mastery estimation；
- TeachingStage；
- StrategyFamily；
- policy scoring；
- anti-oscillation；
- deterministic tie-break；

属于 Teaching / System Design。

### 13.3 Product Requirement vs Architecture

例如：

> “普通 Material 删除后必须可恢复”

属于 Product Requirement。

但：

- tombstone；
- SQLite column；
- transaction；
- API command；
- file deletion order；
- migration；

属于 Architecture / Specs。

---

## 14. GitHub ↔ Linear Mapping

GitHub 不维护第二套 Feature Backlog。

推荐 trace：

```text
GitHub Canonical Product Definition
CAP-xx / PD-REQ-* / PD-AC-*
        ↓ reference
Linear Initiative: Askora
        ↓
workflow-specific Project
        ↓
Milestone
        ↓
Issue
        ↓
EXEC when needed
        ↓
implementation / verification
```

Linear 拥有：priority、dependency、start/status、Milestone、Issue acceptance status。

GitHub 拥有：长期 Capability / Requirement / Rule / Acceptance meaning。

Linear Issue 可以引用 `CAP-*` / `PD-REQ-*` / `PD-AC-*`，但不得复制并维护第二份 Canonical Product Definition。

---

## 15. Change Control

### 15.1 Strategy Change

若变化涉及 Primary User、Problem、JTBD、Value、Success：回到 `PRODUCT-STRATEGY.md`。

### 15.2 Positioning Change

若变化涉及 Category、Product Shape、Hard Boundary、Non-goal：先修改 `PRODUCT-POSITIONING.md`。

### 15.3 Product Definition Change

以下变化属于本文件或 Product Feature Spec：

- 新增/删除一级 Capability；
- 改变 Core Product Object 的产品意义；
- v1 Feature inclusion / exclusion；
- 改变用户可观察 Product Rule；
- 改变 Product Requirement / Product Acceptance。

必须说明：

1. 上游依据；
2. 影响的 Capability / Requirement；
3. 对 UX / Teaching / Architecture / Quality 的 downstream impact；
4. 是否需要新 Linear Project / Milestone / Issue；
5. supersession / migration consequence。

### 15.4 Downstream Gap

- Definition 与 Experience Design 冲突：`DESIGN–DEFINITION GAP`；
- Definition 与 Architecture / Spec 冲突：`DEFINITION–SYSTEM GAP`；
- Definition 与 current code 冲突：`DEFINITION–IMPLEMENTATION GAP`。

下游不得为了现有实现方便修改 Product Definition。

---

## 16. Canonical Source-of-Truth Summary

| Information | Canonical Source |
|---|---|
| Why / User / Problem / Value / Success | `PRODUCT-STRATEGY.md` |
| Category / Product Shape / Hard Boundary / Non-goal | `PRODUCT-POSITIONING.md` |
| Product Actors / Objects / Capabilities | **本文件** |
| Product Rules / Product Requirements | **本文件或明确 Product Feature Spec** |
| Product Acceptance / v1 Feature Scope | **本文件或明确 Product Feature Spec** |
| Navigation / Flow / Screen / Interaction | Experience Design / `docs/specs/ui.md` |
| Teaching algorithm / Learner Model / Assessment mechanics | `docs/specs/systems/**` |
| Domain ownership / API / persistence / technical contracts | `docs/specs/**` |
| 决策选择理由 / 历史替代 | `docs/decisions/DECISIONS.md` + `docs/archive/adr/` |
| Quality thresholds / test oracle | `docs/specs/quality.md` |
| Current priority / milestone / task / dependency / status | Linear |
| Historical completion evidence | `docs/archive/` |

---

## 17. Working Rule

> **Strategy 决定为什么值得做；Positioning 决定 Askora 允许成为什么；Product Definition 决定产品必须具备什么能力和行为；Experience Design 决定用户如何使用；Specs 决定软件必须怎样表现；Decision Log 解释为什么这样选；Linear 决定现在做什么；实现与证据决定当前实际上做到了什么。**

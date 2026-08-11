# Askora 文档中心

> 状态：Current Documentation Authority Index  
> Product Strategy：`docs/product/PRODUCT-STRATEGY.md`  
> Product Boundary：`docs/product/PRODUCT-POSITIONING.md`  
> Product Definition：`docs/product/PRODUCT-DEFINITION.md`  
> Learning Core：v0.3 Adaptive Teaching Loop  
> 最近校准：2026-08-11

`docs/` 保存 Askora 的长期产品决策、正式设计、架构决策、实现合同、执行归档、研究与发布证据。核心规则是：

> **同一长期事实只能有一个当前 Canonical Owner；Research、历史快照、执行状态和实现不能形成并列的“项目真相”。**

## 1. Authority Chain

当前权威链：

```text
docs/product/PRODUCT-STRATEGY.md
        ↓ strategic intent
docs/product/PRODUCT-POSITIONING.md
        ↓ enforceable product boundary
docs/product/PRODUCT-DEFINITION.md
        ↓ capabilities / observable product behavior / product acceptance
docs/design/ Canonical Design / Design Delta
        ↓
docs/adr/ Accepted / non-superseded decisions
        ↓
docs/specs/ Canonical Implementation / Quality Contracts
        ↓
docs/exec-plans/ + Linear Implementation Task Contracts
        ↓
Code / Migration / Executable Tests
        ↓
Release Evidence / Research / Historical Records
```

### Product Strategy

[`product/PRODUCT-STRATEGY.md`](product/PRODUCT-STRATEGY.md) 是 Askora 最高产品战略意图来源，回答：

- 为什么做；
- 为谁做；
- 解决什么问题；
- 创造什么价值；
- 什么结果才算成功。

它不是直接实现合同。未验证的用户、JTBD、市场或价值判断必须显式标为 Assumption / Research Gap。

### Product Positioning

[`product/PRODUCT-POSITIONING.md`](product/PRODUCT-POSITIONING.md) 把 Strategy 转化为产品类别、v1 Product Shape、Strategic Constraints、Non-goals 与 Hard Boundaries。

它是 `PRODUCT-DEFINITION` 与所有下游 Design / ADR / Spec / EXEC / Code 的**最高可执行产品边界**。任何下游层不得自行 supersede 它。

### Product Definition

[`product/PRODUCT-DEFINITION.md`](product/PRODUCT-DEFINITION.md) 把已冻结的 Strategy / Positioning 转化为稳定的 Product WHAT，回答：

- Product Actors / Core Product Objects；
- Product Capability Model；
- Product Rules；
- Product Requirements；
- Product-level NFR；
- Product Acceptance；
- v1 Current / Deferred / Experimental / Retired scope semantics。

它不定义页面布局、Teaching Policy 算法、API、DB schema 或实时 backlog。

### Conflict Rule

- Strategy 与 Positioning 冲突：先在 Product 层解决；
- Definition 突破 Positioning：先处理 Product Definition / Positioning gap；
- Definition 与 Design / ADR / Spec 冲突：下游收敛，或先明确 Product Definition Delta；
- Spec 与 Code 冲突：默认 implementation drift；
- Research 与 Canonical Product / Design 冲突：Research 保留证据价值，但不覆盖当前正式结论；
- 历史 release / audit 只代表对应 commit/time，不自动代表 current `main`。

## 2. Product / Experience / System Boundary

Askora 按以下职责理解文档：

```text
Product Strategy
WHY / WHO / VALUE / SUCCESS

↓

Product Positioning
WHAT CATEGORY / HARD BOUNDARY

↓

Product Definition
WHAT CAPABILITIES / BEHAVIORS / REQUIREMENTS

↓

Experience Design
HOW USER UNDERSTANDS / NAVIGATES / INTERACTS

↓

Teaching / Architecture / Specs
HOW LEARNING AND SOFTWARE WORK
```

具体边界：

| 层级 | 拥有内容 | 不应拥有 |
|---|---|---|
| `product/PRODUCT-STRATEGY.md` | Problem、Target User、JTBD、Vision、Value、Principles、Assumptions、Risks、Success | Feature、UI、schema、API |
| `product/PRODUCT-POSITIONING.md` | Category、Is/Is Not、Product Shape、Constraints、Non-goals | Capability details、页面级 UX、技术 mechanics |
| `product/PRODUCT-DEFINITION.md` | Product Objects、Capabilities、Rules、Requirements、Product AC、v1 feature scope | route、component、algorithm、API、DB schema |
| `research/` | Product Discovery、用户问题、alternatives、assumption evidence | Canonical Product / Design / Spec |
| `design/` | Canonical Product-semantic / Learning / UX Design | 当前工程状态、实时 backlog |
| `adr/` | shared architectural/product-semantic decisions | Strategy、实时 task list |
| `specs/` | domain/interface/platform/quality/UI implementation contracts | Strategy / market assumptions / Product backlog |
| `exec-plans/` | frozen execution task contract | Product Discovery / Canonical Product Definition |
| `design/research/` | Learning Core evidence / synthesis / historical research | 第二套 Canonical Design |
| `releases/` | verification snapshot | current truth without re-verification |
| Linear | Project / Milestone / Issue / dependency / execution status | 长期产品/设计事实 |

### Product Object Model vs Information Architecture

Product Definition 中的 Workspace / Material / Goal / Activity / Evidence 等属于**产品对象与信息模型**。

`Information Architecture` 在 Askora 中专指用户可见的导航、信息空间、页面/任务流组织，由 Experience Design 与 `docs/specs/ui/**` 拥有。

## 3. Current v1 Product Boundary

当前 v1 Product Positioning 的高层产品形态：

```text
Browser
        ↓ loopback
Askora Local Server
        ↓
Local Product Data + Learning Core
        ↓ when needed
External AI APIs via BYOK
```

产品级不变量：

- Personal long-term AI learning system；
- single-user / single-device；
- Local Web Application；
- no Account / Login / Tenant / RBAC；
- LocalOwner 是本地数据归属主体；
- core learning data 由用户本地持有；
- no mandatory Askora central cloud；
- BYOK；
- user-provided learning materials 是主要知识边界；
- Learning Evidence 是 Learner State 的事实基础；
- Conversation ≠ Learning Evidence；
- LLM / Agent 不拥有 canonical learning state；
- Redis / PostgreSQL / Docker / distributed infrastructure 不得成为最终用户运行前提；
- SYS01～SYS08 Learning Core 继续保持 single-writer ownership。

当前 v1 Capability / Feature / Requirement scope 由 [`product/PRODUCT-DEFINITION.md`](product/PRODUCT-DEFINITION.md) 管理；SQLite、Workspace schema、Material lifecycle mechanics、SecretStore、RetrievalScope、migration、retry、jobs、logging、replay 等具体 mechanics 由当前 ADR / Specs 管理。

## 4. Current Product Capability Model

Product Definition 当前冻结 8 个一级 Capability：

```text
CAP-01 Learning Context & Material Grounding
CAP-02 Learning Goal & Success Definition
CAP-03 Readiness, Diagnosis & Learning Planning
CAP-04 Adaptive Learning Activity
CAP-05 Attempt, Assessment & Learning Evidence
CAP-06 Review, Retention & Transfer Validation
CAP-07 Learning Continuity & Next-step Orientation
CAP-08 Local Data & AI Control
```

Capability 是长期产品能力，不等于 L0 页面、Feature List 或 SYS01～SYS08 技术系统。

## 5. Current Learning Core

v0.3 Learning Core 的核心 ownership 继续有效：

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

并继续保持：

```text
TeachingStage != LearnerState
AssessmentResult != MasteryEstimate
DecisionTrace != OutcomeObservation
Conversation != LearningEvidence
SYS02/SYS08 only tighten TeachingAction envelope
LLM/Agent never directly writes canonical learning state
```

Product Definition 只冻结这些机制在用户/产品层必须产生的能力和行为，不重新实现算法或状态所有权。

## 6. Acceptance / Evidence Separation

Askora 必须始终分开：

```text
Research / Discovery Evidence
Product Acceptance
UX Acceptance
Technical / Engineering Evidence
Quality / Security Evidence
Learning Evidence
```

当前 Acceptance owner：

- Product Acceptance → `PRODUCT-DEFINITION` / future Product Feature Spec；
- UX Acceptance → Canonical Experience Design / UI Specs；
- Technical Acceptance → ADR / Specs；
- Quality Acceptance → `docs/specs/quality/**`；
- Learning Evidence → learning experiment / outcome evidence。

Research confidence、工程、架构或 Policy Correctness PASS 都不能自动替代真实 Product / Learning Evidence。

当前上位 Learning Outcome family：

- 无提示独立成功；
- 延迟保持；
- 独立迁移；
- 单位学习时间能力增益。

以下不得作为核心学习 KPI：

- engagement；
- 对话轮次；
- likes；
- session length；
- token usage；
- reading percentage；
- activity completion alone。

## 7. Directory / Lifecycle

| 路径 | 性质 | 更新规则 |
|---|---|---|
| [`product/`](product/README.md) | Canonical Product Strategy / Positioning / Definition | 产品级新证据或明确决策按职责层重新冻结 |
| [`research/`](research/README.md) | Product Discovery / supporting evidence | 可以随新证据演进；不直接改变 Canonical Product truth |
| [`design/`](design/README.md) | Canonical Design + historical/current audits | 必须服从 Product docs；不得隐式扩大 Scope |
| [`adr/`](adr/README.md) | Architecture Decision Records | accepted decisions 可被明确 supersede，但历史保留 |
| [`specs/`](specs/README.md) | Canonical Implementation / Quality Contracts | 直接约束实现；必须与 Product / Design / ADR 一致 |
| [`exec-plans/`](exec-plans/README.md) | Implementation Task Contracts | 实时工程任务必须服从当前 Product / Spec |
| [`releases/`](releases/README.md) | Release / Verification Evidence | snapshot only；不得自动当作 current verification |
| [`design/research/`](design/research/README.md) | Learning Core Research Evidence / Synthesis | 支持上位学习设计，不直接约束实现 |
| [`document-inventory.md`](document-inventory.md) | 文档 disposition | 文档治理后同步维护 |

## 8. Historical Supersession / Stale Snapshot Rule

历史 ADR、Design Delta、EXEC、Release Report、Gap Analysis 可以保留，但必须标明其 lifecycle。

> **Current repository index 不得把已经被后续 main closure 超越的 Gap Analysis 继续描述为 current failure。**

`docs/design/v1-Product-Positioning-Current-Main-Conformance-Gap-Analysis.md` 是基于旧 SHA 的历史审计快照；判断 current conformance 必须重新基于 current `main`、当前 Product Definition、Specs、测试与 CI。

历史 Electron / Account / OCR-as-core / service-infrastructure 相关实现和 evidence 可以保留，但不能重新提升为 v1 product requirement。

## 9. UI / Experience Boundary

顶层导航、首页职责、页面布局、页面级 IA、交互入口、控件与具体 UX Flow 不在 Product Strategy / Positioning / Definition 中冻结。

它们由：

```text
Product Definition
→ UX / Interactive Element Canonical Design
→ Accepted UI ADR
→ docs/specs/ui/**
→ Implementation
```

产品文档约束 UX 必须支持哪些 capability / requirement；UX 决定用户如何理解和操作，不反向决定 Product Scope。

## 10. Agent / Engineering Rules

新的设计或工程任务开始前：

1. MUST 读取 `docs/product/PRODUCT-STRATEGY.md` 以理解 Why / User / Success；
2. MUST 读取 `docs/product/PRODUCT-POSITIONING.md` 以检查产品边界；
3. MUST 读取 `docs/product/PRODUCT-DEFINITION.md` 以确认 Capability / Product Rule / Requirement / Product Acceptance；
4. MUST 读取目标相关 Canonical Design / Accepted ADR / Spec；
5. MUST 检查引用的 Gap Analysis / Release 是否为历史 snapshot；
6. Code 与 Spec 冲突时按 implementation drift 处理；
7. 下位设计需要突破 Product Positioning 或 Product Definition 时必须停止并报告上游 Gap；
8. 重大用户/价值/成功定义改变必须回到 Product Strategy，而不是由 Codex 决定；
9. Linear 负责当前任务状态，GitHub 负责长期有效事实。

## 11. GitHub ↔ Linear Rule

GitHub 不维护第二套 Feature Backlog。

```text
CAP-* / PD-REQ-* / PD-AC-* in GitHub
        ↓ reference
Linear Initiative: Askora
→ workflow-specific Project
→ Milestone
→ Issue
→ EXEC when needed
```

Priority、dependency、execution status 属于 Linear；Capability / Requirement / Product Acceptance 的长期意义属于 GitHub。

## 12. Documentation Gate

```bash
python3 .github/workflows/check_docs.py
```

该门禁验证链接与已知文档规则，但不能替代语义审查、产品验收、代码测试或真实 Learning Evidence。
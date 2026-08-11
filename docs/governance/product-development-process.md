# Askora Product Development Process

> Status: Current Governance Process  
> Scope: product discovery, definition, prioritization, design, implementation, review, release, and evidence  
> Product Strategy: [`product/PRODUCT-STRATEGY.md`](../product/PRODUCT-STRATEGY.md)
> Product Boundary: [`product/PRODUCT-POSITIONING.md`](../product/PRODUCT-POSITIONING.md)
> Product Definition: [`product/PRODUCT-DEFINITION.md`](../product/PRODUCT-DEFINITION.md)
> Work Management: Linear `Askora` Initiative

Askora 的流程必须同时避免三种失败：

1. **先实现，再反向解释为什么值得做；**
2. **只有 Strategy / Positioning，没有把上游意图转化为明确 Product Capability / Requirement；**
3. **只做上游研究，不把冻结结论转换成可验收工程任务。**

因此使用：

> **Research → Strategy → Positioning → Product Definition → Design / ADR → Spec → Linear / EXEC → PR → Verification → Product / Learning Evidence → Product Learning。**

---

## 1. End-to-end Flow

```text
Observed Problem / Opportunity / Research
→ Evidence & Assumptions
→ PRODUCT-STRATEGY check
→ PRODUCT-POSITIONING check / delta when needed
→ PRODUCT-DEFINITION check / delta
→ Canonical Experience / Teaching / Architecture Design when needed
→ ADR when shared technical/semantic choice must be recorded
→ Implementation / Quality Spec / Vertical Slice
→ Linear Project / Milestone / Issue
→ EXEC when implementation contract is needed
→ Pull Request
→ Askora CI / Required
→ Review
→ Merge
→ Release Evidence
→ Product / Usability Evidence
→ Learning Evidence when applicable
→ Retrospective / Product Learning
→ next Opportunity
```

流程是 evidence-driven，不是 document-count-driven。只有在需要冻结不同职责的事实时才增加文档。

---

## 2. Source-of-Truth Roles

### 2.1 GitHub — Long-term Product / Engineering Truth

GitHub 保存：

- Product Strategy / Positioning / Definition；
- Research evidence；
- Canonical Design；
- ADR；
- Specs；
- tests / CI / code；
- immutable EXEC / Release Evidence history。

GitHub 回答：

> **为什么这样做、产品必须是什么/具备什么、应该怎样设计和实现、当时验证了什么。**

### 2.2 Linear — Work Management Truth

Linear 保存：

- Initiative；
- Project；
- Milestone；
- Issue；
- priority；
- dependency；
- execution status；
- acceptance status。

Linear 回答：

> **现在应该做什么、做到哪一步、是否完成。**

不得继续用 GitHub 中的静态 P1/P2 清单或 Product Definition 维护第二套实时 backlog。

### 2.3 ChatGPT — Research / Product Definition / Design / Review Layer

ChatGPT 负责：

```text
research
→ judgment
→ product definition
→ design
→ freeze
→ task decomposition
→ acceptance review
```

重大 Product / Architecture / Interaction decisions 不能留给 Codex 在实现中临时决定。

### 2.4 TraeCode / Codex — Local Execution Layer

TraeCode / Codex 负责已冻结任务的：

- code / file modification；
- tests；
- build / lint / typecheck；
- local verification；
- execution report。

发现 Strategy / Positioning / Product Definition / Spec gap 时应停止扩大 Scope 并报告，而不是自行补产品决策。

---

## 3. Product Strategy — Why Work Should Exist

[`product/PRODUCT-STRATEGY.md`](../product/PRODUCT-STRATEGY.md) 回答：

- Why now；
- Problem；
- Primary User；
- JTBD；
- Vision；
- Value Proposition；
- Differentiation；
- Principles；
- Assumptions / Risks；
- Product / Learning Success Definition。

新的 Product Opportunity 必须先问：

1. 它服务哪个已知 Problem / JTBD？
2. 它强化哪个 Product Outcome / Learning Outcome？
3. 当前依据是 evidence 还是 assumption？
4. 如果不存在当前 Strategy 中，它是在验证新机会，还是正在偷偷扩大产品类别？

Strategy 不是 Implementation Spec；但如果工作改变 Primary User、核心 Problem、Value Proposition 或 Success Definition，必须先做 Product Strategy Delta。

---

## 4. Product Positioning — What Askora Is Allowed to Become

[`product/PRODUCT-POSITIONING.md`](../product/PRODUCT-POSITIONING.md) 是 Product Definition 与下游设计/实现的最高可执行产品边界。

任何 Opportunity、Product Definition、Design、ADR、Spec、EXEC、PR 或代码都不得默默突破：

- Category；
- v1 Product Shape；
- single-user / Local-first / BYOK boundaries；
- Non-goals；
- AI / Learning Evidence authority；
- Strategic Constraints。

如果一个机会确实值得突破现有边界：

```text
new evidence
→ Strategy check
→ Product Positioning Delta
→ user acceptance
→ re-freeze
→ Product Definition Delta
→ downstream work
```

不能因为历史代码或某个 library 已存在，就自动把它提升为 product requirement。

---

## 5. Product Definition — What the Product Must Do

[`product/PRODUCT-DEFINITION.md`](../product/PRODUCT-DEFINITION.md) 是 Strategy / Positioning 与下游 Experience / Teaching / Architecture 之间的 Canonical Product WHAT。

它拥有：

- Product Actors；
- Core Product Objects；
- Product Capability Model；
- Capability → Feature → Scenario → Product Requirement 层级；
- Product Rules；
- Product-level NFR；
- Product Acceptance；
- v1 Current / Deferred / Experimental / Retired scope semantics。

它不拥有：

- route / page / component / interaction pattern；
- Teaching Policy / mastery algorithm；
- API payload；
- DB schema；
- class / module；
- retry / queue / migration mechanics；
- realtime priority / status。

### Product Definition Intake Rule

新的产品工作在进入 UX / Architecture 前至少要能够回答：

1. 对应哪个 `CAP-*`？
2. 是已有 Feature，还是需要新增 Feature definition？
3. 哪个用户 Scenario / Use Case 触发它？
4. 产品层必须满足什么 `PD-REQ-*`？
5. Product Acceptance 如何判断？
6. 当前属于 `CURRENT/COMMITTED`、`DEFERRED`、`EXPERIMENTAL` 还是 `NON-GOAL`？

如果这些问题本身尚未解决，不应让 Codex 从 UI、Specs 或历史代码自行推导答案。

### Complex Feature Spec

只有一个 Feature 跨多个 capability、包含多组独立 rules / scenarios / Product AC，或需要长期独立演进时，才创建 `docs/product/features/<feature>.md`。

不为每个按钮、route、Linear Issue 创建 Product Feature Spec。

---

## 6. Research / Opportunity Intake

新的工作可以来自：

- user-observed problem；
- Product Discovery；
- Research；
- Product / Learning Evidence；
- bug / regression；
- conformance gap；
- security / reliability risk；
- required migration / maintenance。

### Product Opportunity 必须记录

- concrete user problem / scenario；
- observed evidence vs assumption；
- desired user outcome；
- relation to Product Strategy；
- related Product Capability when known；
- success evidence；
- confidence；
- important constraints；
- why now。

### Bug / Regression 必须记录

- current / expected behavior；
- severity by impact；
- reproducible evidence when possible；
- governing Product / Design / Spec；
- affected SHA/version；
- data/security/privacy/migration/learning risk。

进入实施后，这些工作以 **Linear Issue** 管理状态；Research / Canonical conclusions 仍沉淀在 GitHub。

---

## 7. Canonical Design / ADR — How Shared Semantics Should Work

当已冻结 Product Definition 需要转化为以下 shared semantics 时，需要 Canonical Design 和/或 ADR：

- user-visible information / interaction architecture；
- Teaching / learning semantics；
- domain ownership / single-writer；
- security / privacy boundary；
- durable persistence / recovery behavior；
- cross-system contract；
- production runtime architecture；
- reversal 会影响多个 EXEC 的决策。

不要为了记录已由 frozen Spec 唯一决定的 implementation detail 创建 ADR。

如果尚未解决的是用户价值、目标用户或产品类别问题，应回到 Strategy / Discovery；如果尚未解决的是 capability、Product Rule、Feature Scope 或 Product Acceptance，应回到 Product Definition，而不是继续向下建 ADR。

---

## 8. Spec / Vertical Slice — How Software Must Satisfy the Definition

Specs 定义：

- stable technical contract；
- invariant；
- state transition；
- interface；
- domain / platform ownership；
- quality / security / reliability constraint；
- technical acceptance semantics。

Vertical Slice 把多个合同组合成一个可以独立验证的 user/system capability implementation slice。

Product Definition 不重复：

- database schema；
- API fields；
- RetrievalScope fields；
- job state；
- retry；
- migration；
- logging；
- test mechanics。

一个 Vertical Slice 可以引用多个 `CAP-*` / `PD-REQ-*`，但不能自己把历史技术实现升级为新 Product Scope。

---

## 9. Acceptance Model

Askora 统一区分：

```text
Product Acceptance
UX Acceptance
Technical Acceptance
Quality Acceptance
Learning Evidence
```

### Product Acceptance

回答：

> **产品行为是否满足 Capability / Product Requirement / 用户目标？**

Canonical Owner：`PRODUCT-DEFINITION.md` 或明确 Product Feature Spec。

### UX Acceptance

回答：用户是否能够正确理解、找到并完成任务？

Canonical Owner：Experience Design / UI Specs。

### Technical Acceptance

回答：Domain / API / State / Teaching / Persistence contracts 是否成立？

Canonical Owner：ADR / Specs。

### Quality Acceptance

回答：Reliability / Security / Performance / Accessibility 等是否达标？

Canonical Owner：`docs/specs/quality/**`。

### Learning Evidence

回答：capability 是否真的改善 independent / delayed / transfer learning outcome？

Product / Engineering PASS 不能自动满足 Learning Evidence。

---

## 10. Linear Project / Issue — Current Work Control

Askora 顶层使用 **Initiative: Askora**。

不同性质工作应使用相对独立 Project，例如：

- Product Strategy & Discovery；
- Product Definition & Planning；
- UI Redesign；
- Quality；
- Architecture / Learning Core 等独立工作流。

不要把 Product Discovery、Product Definition、UI、CI 与 Learning Core 实现长期混在同一 Project。

推荐 trace：

```text
GitHub CAP-* / PD-REQ-* / PD-AC-*
        ↓ reference
Linear workflow Project
→ Milestone
→ Issue
→ EXEC when needed
```

一个 implementation-ready Issue 至少应包含：

- Objective；
- Context；
- Scope；
- Non-goals；
- Relevant Files / Docs；
- Product Capability / Requirement references when applicable；
- Requirements；
- Constraints；
- Acceptance Criteria；
- Verification；
- Dependencies。

理想状态：

> **TraeCode / Codex 读取 Issue + Repository 后可以执行，而不需要重新进行产品设计。**

---

## 11. EXEC — Frozen Engineering Task Contract

需要严格文件边界、迁移步骤或执行报告时使用 EXEC。

EXEC 不成为 general backlog，也不拥有 Product Discovery / Product Definition。

应继续包含：

- Objective；
- Dependencies；
- Required Product Strategy / Positioning / Definition；
- Required Design / ADR / Specs；
- Current Reality；
- Allowed Files；
- Forbidden Changes；
- Implementation Tasks；
- Acceptance Criteria；
- Required Tests；
- Completion Report Format。

如果实现暴露未冻结重大决策，报告：

- `STRATEGY GAP`；
- `POSITIONING GAP`；
- `PRODUCT DEFINITION GAP`；
- `DESIGN GAP`；
- `SPEC GAP`。

不要在 EXEC 内自行解决上位问题。

---

## 12. Definition of Ready

Implementation-ready work 至少满足：

- concrete problem / opportunity / defect 已明确；
- evidence confidence 显式；
- assumptions 没有被当作 validated facts；
- 与 Product Strategy 对齐；
- 与 Product Positioning / Non-goals 对齐；
- 对应 Product Capability / Requirement / Product Acceptance 已知，或任务明确属于纯 Engineering/Quality maintenance；
- expected product/user outcome 可以判断；
- Acceptance Criteria 与 dependencies 已知；
- shared product/architecture choices 已在正确层冻结；
- slice 足够小，可以独立 review / verify。

### Not Ready

以下情况不应交给 Codex 自主实现：

- 理由只有“这个功能有用”；
- Primary User / JTBD 尚未决定；
- Product Positioning 需要被突破但尚未更新；
- 当前 v1 是否应该包含该 Feature 尚未定义；
- Product Acceptance 尚不明确；
- EXEC 需要临时决定 domain ownership；
- success 只有“code merged”；
- known P0/P1 correctness/security contradiction 未解决。

---

## 13. Pull Request Gate

Prefer：

```text
one problem / vertical slice / EXEC
→ one independently reviewable PR
```

PR 必须回答：

### Why

- What user/system problem does this solve?
- Which Linear Issue / Product Opportunity originated it?
- Which `CAP-*` / `PD-REQ-*` is served when this is product work?

### Authority

- Which Product Strategy / Positioning / Definition / Design / ADR / Spec / EXEC govern it?
- Is authority intentionally changing? If yes, was the upper-level document changed first?

### Risk

至少考虑：

- product / learning semantics；
- owner / data isolation；
- secrets / privacy / security；
- persistence / migration / recovery / no-resurrection；
- Local Web runtime boundary；
- external provider failure；
- rollback / fail-closed behavior。

### Evidence

必须记录 candidate SHA 与实际执行的 gates，不只写“tests pass”。

---

## 14. Required CI and Merge Policy

`Askora CI / Required` 是工程合并门禁。

```text
Candidate SHA
→ Askora CI / Required GREEN
→ review P0/P1 resolved
→ merge
→ main remains GREEN
```

不得为了迁移便利把 Required check 降为 Optional，也不得删改失败测试来制造绿色状态。

---

## 15. Review Severity

### P0

Release blocker：

- data loss / corruption；
- critical security/privacy violation；
- broken recovery/no-resurrection；
- direct violation of frozen critical product boundary / Product Definition。

Known P0 必须解决后再合并。

### P1

重大 product behavior、correctness、user-flow、architecture ownership 或 security defect，会实质性否定当前 capability claim。

必须修复，或缩减/重新打开 capability claim。

### P2 / P3

在仍满足 frozen acceptance contract 的前提下可延期；若影响产品质量，应有可追踪 Linear Issue。

---

## 16. Definition of Done

### Engineering Done

- implementation matches frozen contracts；
- Required tests / CI pass on candidate SHA；
- review P0/P1 resolved；
- migration/recovery/security gates pass when applicable；
- current docs reconciled。

### Delivery Done

- candidate SHA recorded；
- completion / release evidence reflects actual results；
- completed EXEC archived correctly；
- historical evidence not rewritten as current evidence。

### Product Done

- relevant Product Acceptance satisfied；
- Product / Usability Evidence supports the claim；
- real browser / Local Web / provider evidence available when applicable；
- task success can be demonstrated for the intended scenario。

Engineering completion 不自动证明用户问题已解决。

### Learning Done

Learning effectiveness 是独立 claim。

除非有真实学习实验/结果，否则继续使用：

`LEARNING_EVIDENCE_INSUFFICIENT`

不得由以下内容推导 Learning PASS：

- successful model call；
- message count；
- session duration；
- activity completion alone；
- Product task success alone；
- Engineering PASS；
- Policy Correctness PASS。

---

## 17. Evidence Taxonomy

| Evidence | Answers | Typical Sources |
|---|---|---|
| Research / Discovery Evidence | Is the problem/user/JTBD/value assumption supported? | interviews, observation, alternative research, experiments |
| Product / Usability Evidence | Does product behavior satisfy intended user outcome? | real product use, task success, usability evidence |
| Engineering Evidence | Did implementation satisfy technical contract? | Required CI, tests, build, migration |
| Security / Privacy Evidence | Are ownership, secrets and recovery boundaries preserved? | threat-specific tests, audit |
| Learning Evidence | Does capability improve intended learning outcome? | independent/delayed/transfer real-user measures |

一个 evidence class 的 PASS 不能自动升级另一个 class。

---

## 18. Product Validation Loop

Release 后，相关 Opportunity / Assumption / Product Requirement 应在有足够证据时重新判断。

如果新证据推翻当前产品假设：

```text
Evidence
→ Research update
→ Product Strategy / Positioning Delta when needed
→ Product Definition Delta
→ re-freeze
→ next design / implementation cycle
```

Feature shipped 不是 Product Learning 的终点。

---

## 19. Working Rule

> **Research 说明我们为什么相信问题存在；Product Strategy 决定为什么值得做；Product Positioning 决定 Askora 允许成为什么；Product Definition 决定产品必须具备什么能力、行为和验收条件；Experience / Teaching / Architecture / Specs 冻结这些能力如何成立；Linear 管理当前应该做什么；EXEC / Codex 执行冻结任务；PR / CI / Review 判断能否合并；Product / Learning Evidence 决定最后能够声称什么。**

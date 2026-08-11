# Askora Product Development Process

> Status: Current Governance Process  
> Scope: product discovery, prioritization, design, implementation, review, release, and evidence  
> Product Strategy: [`product/PRODUCT-STRATEGY.md`](product/PRODUCT-STRATEGY.md)  
> Product Boundary: [`product/PRODUCT-POSITIONING.md`](product/PRODUCT-POSITIONING.md)  
> Work Management: Linear `Askora` Initiative

Askora 的流程必须同时避免两种失败：

1. **先实现，再反向解释为什么值得做；**
2. **只做上游研究，不把冻结结论转换成可验收工程任务。**

因此使用：

> **Research → Strategy → Positioning → Design / ADR → Spec → Linear / EXEC → PR → Verification → Product / Learning Evidence → Product Learning。**

---

## 1. End-to-end Flow

```text
Observed Problem / Opportunity / Research
→ Evidence & Assumptions
→ PRODUCT-STRATEGY check
→ PRODUCT-POSITIONING check / delta when needed
→ Canonical Design / ADR when shared semantics change
→ Spec / Vertical Slice
→ Linear Project / Issue
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

- Product Strategy / Positioning；
- Research evidence；
- Canonical Design；
- ADR；
- Specs；
- tests / CI / code；
- immutable EXEC / Release Evidence history。

GitHub 回答：

> **为什么这样设计、应该怎样设计和实现、当时验证了什么。**

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

不得继续用 GitHub 中的静态 P1/P2 清单维护第二套实时 backlog。

### 2.3 ChatGPT — Research / Design / Review Layer

ChatGPT 负责：

```text
research
→ judgment
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

发现 Strategy / Positioning / Spec gap 时应停止扩大 Scope 并报告，而不是自行补产品决策。

---

## 3. Product Strategy — Why Work Should Exist

[`product/PRODUCT-STRATEGY.md`](product/PRODUCT-STRATEGY.md) 回答：

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

[`product/PRODUCT-POSITIONING.md`](product/PRODUCT-POSITIONING.md) 是下游设计与实现的最高可执行产品边界。

任何 Opportunity、Design、ADR、Spec、EXEC、PR 或代码都不得默默突破：

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
→ downstream work
```

不能因为历史代码或某个 library 已存在，就自动把它提升为 product requirement。

---

## 5. Research / Opportunity Intake

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

## 6. Canonical Design / ADR — Shared Decisions

当工作改变以下 shared semantics 时，需要 Canonical Design 和/或 ADR：

- domain ownership / single-writer；
- learning semantics；
- user-visible information / interaction architecture；
- security / privacy boundary；
- durable persistence / recovery behavior；
- cross-system contract；
- production runtime architecture；
- reversal 会影响多个 EXEC 的决策。

不要为了记录已由 frozen Spec 唯一决定的 implementation detail 创建 ADR。

如果尚未解决的是用户价值、目标用户或产品类别问题，应回到 Product Strategy / Discovery，而不是继续向下建 ADR。

---

## 7. Spec / Vertical Slice — What Must Be True

Specs 定义：

- stable contract；
- invariant；
- state transition；
- interface；
- domain / platform ownership；
- quality / security / reliability constraint；
- acceptance semantics。

Vertical Slice 把多个合同组合成一个可以独立验证的 user/system capability。

Product Positioning 不再重复：

- database schema；
- API fields；
- RetrievalScope fields；
- job state；
- retry；
- migration；
- logging；
- test mechanics。

这些属于 Spec / Architecture / Quality。

---

## 8. Linear Project / Issue — Current Work Control

Askora 顶层使用 **Initiative: Askora**。

不同性质工作应使用相对独立 Project，例如：

- Product Strategy & Discovery；
- UI Redesign；
- Quality；
- Architecture / Learning Core 等独立工作流。

不要把 Product Discovery、UI、CI 与 Learning Core 实现长期混在同一 Project。

一个 implementation-ready Issue 至少应包含：

- Objective；
- Context；
- Scope；
- Non-goals；
- Relevant Files / Docs；
- Requirements；
- Constraints；
- Acceptance Criteria；
- Verification；
- Dependencies。

理想状态：

> **TraeCode / Codex 读取 Issue + Repository 后可以执行，而不需要重新进行产品设计。**

---

## 9. EXEC — Frozen Engineering Task Contract

需要严格文件边界、迁移步骤或执行报告时使用 EXEC。

EXEC 不成为 general backlog，也不拥有 Product Discovery。

应继续包含：

- Objective；
- Dependencies；
- Required Product Strategy / Positioning；
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
- `DESIGN GAP`；
- `SPEC GAP`。

不要在 EXEC 内自行解决上位问题。

---

## 10. Definition of Ready

Implementation-ready work 至少满足：

- concrete problem / opportunity / defect 已明确；
- evidence confidence 显式；
- assumptions 没有被当作 validated facts；
- 与 Product Strategy 对齐；
- 与 Product Positioning / Non-goals 对齐；
- expected product/user outcome 可以判断；
- Acceptance Criteria 与 dependencies 已知；
- shared product/architecture choices 已在正确层冻结；
- slice 足够小，可以独立 review / verify。

### Not Ready

以下情况不应交给 Codex 自主实现：

- 理由只有“这个功能有用”；
- Primary User / JTBD 尚未决定；
- Product Positioning 需要被突破但尚未更新；
- EXEC 需要临时决定 domain ownership；
- success 只有“code merged”；
- known P0/P1 correctness/security contradiction 未解决。

---

## 11. Pull Request Gate

Prefer：

```text
one problem / vertical slice / EXEC
→ one independently reviewable PR
```

PR 必须回答：

### Why

- What user/system problem does this solve?
- Which Linear Issue / Product Opportunity originated it?

### Authority

- Which Product Strategy / Positioning / Design / ADR / Spec / EXEC govern it?
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

## 12. Required CI and Merge Policy

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

## 13. Review Severity

### P0

Release blocker：

- data loss / corruption；
- critical security/privacy violation；
- broken recovery/no-resurrection；
- direct violation of frozen critical product boundary。

Known P0 必须解决后再合并。

### P1

重大 correctness、user-flow、architecture ownership 或 security defect，会实质性否定当前 capability claim。

必须修复，或缩减/重新打开 capability claim。

### P2 / P3

在仍满足 frozen acceptance contract 的前提下可延期；若影响产品质量，应有可追踪 Linear Issue。

---

## 14. Definition of Done

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

Engineering completion 不证明用户问题已解决。

需要单独记录：

- Product / Usability Evidence；
- real browser / Local Web / provider evidence；
- task success；
- qualitative user evidence；
- relevant product behavior metrics。

### Learning Done

Learning effectiveness 是独立 claim。

除非有真实学习实验/结果，否则继续使用：

`LEARNING_EVIDENCE_INSUFFICIENT`

不得由以下内容推导 Learning PASS：

- successful model call；
- message count；
- session duration；
- activity completion alone；
- Engineering PASS；
- Policy Correctness PASS。

---

## 15. Evidence Taxonomy

| Evidence | Answers | Typical Sources |
|---|---|---|
| Research / Discovery Evidence | Is the problem/user/JTBD/value assumption supported? | interviews, observation, alternative research, experiments |
| Engineering Evidence | Did implementation satisfy technical contract? | Required CI, tests, build, migration |
| Security / Privacy Evidence | Are ownership, secrets and recovery boundaries preserved? | threat-specific tests, audit |
| Product / Usability Evidence | Can target user obtain expected product outcome? | real product use, task success, usability evidence |
| Learning Evidence | Does capability improve intended learning outcome? | independent/delayed/transfer real-user measures |

一个 evidence class 的 PASS 不能自动升级另一个 class。

---

## 16. Product Validation Loop

Release 后，相关 Opportunity / Assumption 应在有足够证据时重新判断：

- **Validated**；
- **Partially validated**；
- **Not validated**；
- **Insufficient evidence**。

如果新证据推翻当前产品假设：

```text
Evidence
→ Research update
→ Product Strategy / Positioning Delta when needed
→ re-freeze
→ next design / implementation cycle
```

Feature shipped 不是 Product Learning 的终点。

---

## 17. Working Rule

> **Research 说明我们为什么相信问题存在；Product Strategy 决定为什么值得做；Product Positioning 决定 Askora 允许成为什么；Design / ADR / Specs 冻结如何成立；Linear 管理当前应该做什么；EXEC / Codex 执行冻结任务；PR / CI / Review 判断能否合并；Product / Learning Evidence 决定最后能够声称什么。**

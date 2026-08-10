# Askora Execution Plans

> 状态：既有 UI-02C、P1-01～07 等基线已完成；当前存在独立 active/blocked 队列
> Active / Frozen Queue：EXEC-048～051、EXEC-043～046、EXEC-052～058
> Local Identity chain：`EXEC-047 DONE → EXEC-048 → EXEC-049 → EXEC-050 → EXEC-051`
> UI-03 implementation chain：`EXEC-051 DONE → EXEC-043 → EXEC-044 → EXEC-045 → EXEC-046`
> CI v2 chain：`EXEC-052 → (EXEC-051 DONE) → EXEC-053 → EXEC-054 → EXEC-055 → {EXEC-056 after EXEC-046, EXEC-057} → EXEC-058`

本目录保存可直接交给 Codex 执行的工程任务合同，以及完成后的不可变归档。所有 EXEC 必须服从 [`../product/PRODUCT-POSITIONING.md`](../product/PRODUCT-POSITIONING.md)。EXEC 只能拆解已经冻结且不违反 Product Positioning 的 Spec/Vertical Slice，不能自行修改 Product Positioning、Design、ADR 或 Spec 语义。

```text
PRODUCT-POSITIONING
→ Canonical Design / Accepted ADR
→ Spec
→ Vertical Slice
→ EXEC
→ Code / Test
→ Release Evidence
```

如果既有 EXEC、Spec、ADR 或代码与 Product Positioning 冲突，应按 `AGENTS.md` 报告 `POSITIONING GAP` 并收敛下位治理；不得以既有 EXEC 已冻结为理由继续实现冲突语义。

## 1. Active / Frozen Queue

| EXEC | Task | Status | Dependency / Concurrency |
|---|---|---|---|
| [EXEC-048](active/EXEC-048-backend-no-auth-loopback-cutover.md) | Backend No-Auth & Loopback Cutover | FROZEN / ACTIVE | EXEC-047 DONE；dependency satisfied |
| [EXEC-049](active/EXEC-049-frontend-settings-onboarding-deaccounting.md) | Frontend / Settings / Onboarding De-accounting | FROZEN / BLOCKED_BY_DEPENDENCY_GATE | requires EXEC-048 DONE |
| [EXEC-050](active/EXEC-050-auth-persistence-configuration-cleanup.md) | Auth Persistence & Configuration Cleanup | FROZEN / BLOCKED_BY_DEPENDENCY_GATE | requires EXEC-049 DONE |
| [EXEC-051](active/EXEC-051-local-identity-release-closure.md) | Local Identity Acceptance & Release Closure | FROZEN / BLOCKED_BY_DEPENDENCY_GATE | requires EXEC-050 DONE；unlocks UI-03 and CI runtime cutover |
| [EXEC-043](active/EXEC-043-ui-03a-shell-routes-learning-domain.md) | UI-03A Shell, Routes and Learning Domain | FROZEN / BLOCKED_BY_DEPENDENCY_GATE | requires EXEC-051 DONE |
| [EXEC-044](active/EXEC-044-ui-03b-today-primary-hierarchy.md) | UI-03B Today Primary Hierarchy | FROZEN / BLOCKED_BY_DEPENDENCY_GATE | requires EXEC-043 DONE |
| [EXEC-045](active/EXEC-045-ui-03c-library-progressive-disclosure.md) | UI-03C Library Progressive Disclosure | FROZEN / BLOCKED_BY_DEPENDENCY_GATE | requires EXEC-044 DONE |
| [EXEC-046](active/EXEC-046-ui-03d-settings-legacy-release-closure.md) | UI-03D Settings / Legacy / Release Closure | FROZEN / BLOCKED_BY_DEPENDENCY_GATE | requires EXEC-045 DONE；unlocks CI browser E2E |
| [EXEC-052](active/EXEC-052-ci-governance-test-oracle-classification.md) | CI Governance & Test Oracle Classification | FROZEN / READY | documentation/governance only；MAY run now |
| [EXEC-053](active/EXEC-053-production-local-runtime-cutover.md) | Production Local Runtime Cutover | FROZEN / BLOCKED_BY_DEPENDENCY_GATE | requires EXEC-052 + EXEC-051 DONE |
| [EXEC-054](active/EXEC-054-required-core-test-realignment.md) | Required Core Test Realignment | FROZEN / BLOCKED_BY_DEPENDENCY_GATE | requires EXEC-053 DONE |
| [EXEC-055](active/EXEC-055-local-data-migration-recovery-rebuild-gate.md) | Local Data Migration, Recovery & Rebuild Gate | FROZEN / BLOCKED_BY_DEPENDENCY_GATE | requires EXEC-054 DONE |
| [EXEC-056](active/EXEC-056-local-web-chromium-e2e.md) | Local Web Chromium E2E | FROZEN / BLOCKED_BY_DEPENDENCY_GATE | requires EXEC-055 + EXEC-046 DONE |
| [EXEC-057](active/EXEC-057-ci-workflow-quality-supply-chain.md) | CI Workflow, Quality & Supply-chain Realignment | FROZEN / BLOCKED_BY_DEPENDENCY_GATE | requires EXEC-055 DONE |
| [EXEC-058](active/EXEC-058-required-gate-main-protection-closure.md) | Required Gate & Main Protection Closure | FROZEN / BLOCKED_BY_DEPENDENCY_GATE | requires EXEC-056 + EXEC-057 DONE |

### Concurrency Rule

`EXEC-042`（已归档 DONE）处理 backend Teaching Policy production closure，可并行文档治理，但不得扩大到 Local Identity、CI runtime cutover 或 frontend Interaction Architecture。

`EXEC-052` 只处理 CI governance / test-oracle classification / document lifecycle，可在当前实现链旁执行；不得修改 production runtime 或产品 UI。

涉及 identity / App / Settings / routes 的主链必须严格串行：

```text
EXEC-1062 DONE
    ↓
EXEC-047 DONE LocalOwner Foundation
    ↓
EXEC-048 Backend No-Auth / Loopback
    ↓
EXEC-049 Frontend De-accounting
    ↓
EXEC-050 Persistence Cleanup
    ↓
EXEC-051 Release Closure
    ↓
EXEC-043 Shell / Routes / Learning
    ↓
EXEC-044 Today
    ↓
EXEC-045 Library
    ↓
EXEC-046 Settings / Cleanup / Release
```

CI v2 的实现链：

```text
EXEC-052 Governance / Oracle Classification
    ↓
EXEC-051 DONE dependency gate
    ↓
EXEC-053 Production Local Runtime
    ↓
EXEC-054 Required Core Tests
    ↓
EXEC-055 Migration / Recovery / Rebuild
    ├──────────────→ EXEC-057 Workflow / Quality / Supply-chain
    │
    └→ EXEC-046 DONE dependency gate
             ↓
         EXEC-056 Chromium Local Web E2E
             │
             └──────────────┐
                            ↓
                         EXEC-058
                 Required Gate / Main Protection
```

`EXEC-056` 必须等待 UI-03 `EXEC-046 DONE`，避免在即将被替换的 route/shell 上冻结浏览器 E2E。

原因：P1-06、Authentication Removal 与 UI-03 在 `App.jsx`、Settings、routes、onboarding tests 上存在直接文件重叠；CI runtime/test重排又依赖 Local Identity 已完成的 no-auth truth。并行实现会形成不可审计覆盖。

## 2. Current Baseline

| Baseline | EXEC | Final status |
|---|---|---|
| v0.2 First Vertical Learning Loop | EXEC-001～006 | DONE |
| v0.3 Adaptive Teaching Loop historical implementation | EXEC-007～013 | DONE / historical snapshot |
| v0.3 Production Sequential Teaching Policy Closure | EXEC-042 | DONE / archived 2026-08-10 |
| v0.3.1 Rich Response Rendering | EXEC-014 | DONE |
| UI-01 Learning Shell and Compatibility Tutor Workspace | EXEC-015 | DONE |
| UI-02A Canonical Library and Scoped Knowledge Map | EXEC-016 | DONE |
| Book-to-Learning SPEC-D01～D06 | EXEC-017～024 | DONE |
| UI-02B1 Material-to-Learning Launch | EXEC-025 | DONE |
| UI-02B2 Guided Book Learning | EXEC-026 | DONE |
| UI-02B3 Real-model Guided Learning | EXEC-027 | DONE |
| Zhipu Development Model Integration | EXEC-028 | DONE |
| UI-02B Goals, Learning Path and Evidence | EXEC-029 | DONE |
| UI-02C Canonical Activity Lifecycle | EXEC-030 | DONE |
| P1-04A/B/C Library Management | EXEC-031～033 | DONE |
| P1-05 Identity / Recovery / Deletion | EXEC-034～036 + integration EXEC-037 | DONE / **historical, superseded by ADR-0015** |
| P1-07 Error Recovery Center | historical EXEC-037 task-domain file | DONE |
| P1-01 Goal Management | EXEC-038～039 | DONE |
| P1-02 Model Settings | EXEC-040～041 | DONE / desktop-specific release evidence historical where superseded |
| P1-03 Data Control and Recovery | EXEC-1031～1034 | DONE |
| P1-06 Onboarding Readiness Foundation | EXEC-1061 | DONE |
| P1-06 Onboarding Product Closure | EXEC-1062 | DONE / archived 2026-08-10 |
| Local Single-User Authentication Removal | EXEC-047 DONE → EXEC-048～051 | **EXEC-048 ACTIVE** |
| UI-03 Interactive Element System Refactor | EXEC-043～046 | FROZEN / BLOCKED_BY_EXEC_051 |
| CI v2 / Test Infrastructure Realignment | EXEC-052～058 | FROZEN / **EXEC-052 READY** |

## 3. Local Identity Governance Chain

```text
PRODUCT-POSITIONING
→ Local Single-User Identity Canonical Design Delta
→ ADR-0015 accepted
→ LID-* v2 frozen
→ Local Single-User Authentication Removal Vertical Slice
→ EXEC-047 → 048 → 049 → 050 → 051
→ Local Identity Release Evidence
```

本链只改变 identity resolution、authentication、network boundary、Settings/Onboarding 账号语义和相关 persistence。不得修改 SYS01～SYS08 canonical truth 或学习算法，也不得突破 Product Positioning 的 Single-user / no-login / Local Web / no-official-central-server 边界。

## 4. UI-03 Governance Chain

```text
PRODUCT-POSITIONING（只提供产品边界，不冻结页面级 UX）
→ Interactive Element System Canonical Design Delta
→ ADR-0014 accepted
→ UI-IES / UI-IA / UI-SCREEN / UI-VIS / UI-QUAL frozen
→ UI-03 Vertical Slice frozen
→ EXEC-051 DONE dependency gate
→ EXEC-043 → 044 → 045 → 046
→ UI-03 Release Evidence
```

UI-03 只改变 information architecture、interaction hierarchy、presentation exposure 与 route organization。顶层导航、首页职责、页面布局和页面级 IA 继续由 Interactive Elements 设计系统冻结；Product Positioning 不替代这些设计决策，但 UI-03 不得突破其产品边界。不得恢复 ADR-0015 已删除的 Account/Login/AuthSession 语义。

## 5. CI v2 Governance Chain

```text
PRODUCT-POSITIONING
→ CI Infrastructure Standard
→ v1 Local Web Quality Reconciliation
→ CI/Test Infrastructure Gap Analysis
→ EXEC-052～058
→ Workflow / Test / Runtime changes
→ Askora CI / Required
→ main Ruleset / Branch Protection
```

CI v2 只能改变测试、质量门禁、runtime infrastructure truth、workflow 和仓库治理；不得借 CI 重构修改 Teaching Policy、学习算法或 UI 信息架构。

PostgreSQL / Docker / real-provider compatibility MAY 保留为 Optional/Scheduled evidence，但不得拥有 v1 Required release veto 权。

## 6. v0.3 Current Conformance Closure

当前 v0.3 production conformance 已由 EXEC-042 关闭并归档 DONE（2026-08-10）：GAP-V03-001 / GAP-V03-002 CLOSED，见 [`../releases/v0.3-production-sequential-policy-closure.md`](../releases/v0.3-production-sequential-policy-closure.md)。Local Identity、UI-03 与 CI v2 不得借各自任务修复或改写 Teaching Policy。

Engineering、Policy Correctness 与 Learning Evidence 必须继续独立报告；身份/UI/CI 改善不得改变 `LEARNING_EVIDENCE_INSUFFICIENT`。

## 7. Book-to-Learning Historical Chain

```text
EXEC-016 DONE
→ EXEC-017
→ EXEC-018
→ EXEC-019
   ├→ EXEC-020 ─┐
   └→ EXEC-021 → EXEC-022
                 ↓
              EXEC-023
                 ↓
              EXEC-024
```

EXEC-017～024 均已完成并归档，保持历史原貌。

## 8. P1-06 → Local Identity → UI-03 Boundary

P1-06B 已完成首次用户 journey、default entry、deep-link preservation、Settings reopen 与真实 owner capability integration，并于 2026-08-10 归档。

因此 ADR-0015 的 EXEC-047 已解锁并完成（2026-08-10 归档）；必须完成 EXEC-047～051 后，UI-03 EXEC-043 才能开始全局 IA migration。

不得让 Local Identity 与 UI-03 并行修改同一 frontend shell。

## 9. CI v2 Dependency Boundary

`EXEC-052` 可立即执行，因为它只冻结治理和 test-oracle classification。

`EXEC-053` 必须等待 `EXEC-051 DONE`：Production Local runtime cutover 不能与 auth persistence cleanup 同时改 production startup/config/dependencies。

`EXEC-056` 必须等待 `EXEC-046 DONE`：浏览器 E2E 必须冻结在 v1 当前 UI routes/shell 上，而不是旧 UI-02/transition routes 上。

`EXEC-057` 在 `EXEC-055 DONE` 后可与 UI-03 后段并行，但若出现 `package.json` / frontend test config 直接冲突，应优先让 UI-03 完成后再继续，不允许混合 commit。

## 10. Queue Contract

- 每个 EXEC 只能在自身 dependency gate 满足后执行；
- 后序依赖未 DONE 时返回 `BLOCKED_BY_DEPENDENCY`；
- active EXEC 不得互相扩大 Allowed Files 或混合 commit；
- 任何任务开始前先检查 `docs/product/PRODUCT-POSITIONING.md`；
- 产品级边界冲突按 `AGENTS.md` 报告 `POSITIONING GAP`；
- 公共语义、owner、schema、生产依赖出现未冻结选择时按 `AGENTS.md` 报告 `SPEC GAP`；
- 每个 EXEC 完成后先满足自身 AC / Required Tests / DoD，再移入 `completed/`；
- completed EXEC 保持不可变历史证据。

## 11. New EXEC Requirements

每份新 EXEC 必须包含：Objective、Dependencies、Required Product Positioning、Required Specs、Current Reality、Allowed Files、Forbidden Changes、Implementation Tasks、Acceptance Criteria、Required Tests、Completion Report Format。

执行前必须读取根 `AGENTS.md`、`docs/product/PRODUCT-POSITIONING.md`、本 EXEC 引用的全部 Spec，并核对当前代码和 Git 状态。不得通过删除测试、弱化断言、frontend-only state、auto-login、demo-token、legacy shortcut、Required→Optional 偷换或外部服务依赖伪造完成。

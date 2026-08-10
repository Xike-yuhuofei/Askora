# Askora Execution Plans

> 状态：当前执行索引；已完成 EXEC 进入 `completed/` 作为不可变历史证据，未完成 EXEC 保留在 `active/`。
> 当前 active queue：EXEC-043～046、EXEC-054～058
> Local Identity：EXEC-047～051 DONE
> CI v2：EXEC-052～053 DONE → EXEC-054 → EXEC-055 → {EXEC-056 after EXEC-046, EXEC-057} → EXEC-058

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
| [EXEC-043](active/EXEC-043-ui-03a-shell-routes-learning-domain.md) | UI-03A Shell, Routes and Learning Domain | FROZEN / ACTIVE | Local Identity closure 已满足；按当前 EXEC completion gate 收口 |
| [EXEC-044](active/EXEC-044-ui-03b-today-primary-hierarchy.md) | UI-03B Today Primary Hierarchy | FROZEN / BLOCKED_BY_DEPENDENCY_GATE | requires EXEC-043 DONE |
| [EXEC-045](active/EXEC-045-ui-03c-library-progressive-disclosure.md) | UI-03C Library Progressive Disclosure | FROZEN / BLOCKED_BY_DEPENDENCY_GATE | requires EXEC-044 DONE |
| [EXEC-046](active/EXEC-046-ui-03d-settings-legacy-release-closure.md) | UI-03D Settings / Legacy / Release Closure | FROZEN / BLOCKED_BY_DEPENDENCY_GATE | requires EXEC-045 DONE；unlocks CI browser E2E |
| [EXEC-054](active/EXEC-054-required-core-test-realignment.md) | Required Core Test Realignment | FROZEN / READY | EXEC-053 DONE；dependency satisfied |
| [EXEC-055](active/EXEC-055-local-data-migration-recovery-rebuild-gate.md) | Local Data Migration, Recovery & Rebuild Gate | FROZEN / BLOCKED_BY_DEPENDENCY_GATE | requires EXEC-054 DONE |
| [EXEC-056](active/EXEC-056-local-web-chromium-e2e.md) | Local Web Chromium E2E | FROZEN / BLOCKED_BY_DEPENDENCY_GATE | requires EXEC-055 + EXEC-046 DONE |
| [EXEC-057](active/EXEC-057-ci-workflow-quality-supply-chain.md) | CI Workflow, Quality & Supply-chain Realignment | FROZEN / BLOCKED_BY_DEPENDENCY_GATE | requires EXEC-055 DONE |
| [EXEC-058](active/EXEC-058-required-gate-main-protection-closure.md) | Required Gate & Main Protection Closure | FROZEN / BLOCKED_BY_DEPENDENCY_GATE | requires EXEC-056 + EXEC-057 DONE |

### Newly archived baseline

| EXEC | Task | Final status |
|---|---|---|
| [EXEC-048](completed/EXEC-048-backend-no-auth-loopback-cutover.md) | Backend No-Auth & Loopback Cutover | DONE |
| [EXEC-049](completed/EXEC-049-frontend-settings-onboarding-deaccounting.md) | Frontend / Settings / Onboarding De-accounting | DONE |
| [EXEC-050](completed/EXEC-050-auth-persistence-configuration-cleanup.md) | Auth Persistence & Configuration Cleanup | DONE |
| [EXEC-051](completed/EXEC-051-local-identity-release-closure.md) | Local Identity Acceptance & Release Closure | DONE |
| [EXEC-052](completed/EXEC-052-ci-governance-test-oracle-classification.md) | CI Governance & Test Oracle Classification | DONE |
| [EXEC-053](completed/EXEC-053-production-local-runtime-cutover.md) | Production Local Runtime Cutover | DONE |

### Concurrency Rule

Local Identity implementation is closed through EXEC-051. UI-03 and CI v2 remain separate task domains and must not silently combine file ownership or change each other's frozen semantics.

UI-03 主链：

```text
EXEC-047～051 DONE
    ↓
EXEC-043 Shell / Routes / Learning
    ↓
EXEC-044 Today
    ↓
EXEC-045 Library
    ↓
EXEC-046 Settings / Cleanup / Release
```

CI v2 主链：

```text
EXEC-052 Governance / Oracle Classification DONE
    ↓
EXEC-053 Production Local Runtime DONE
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
| P1-05 Identity / Recovery / Deletion | EXEC-034～036 + integration EXEC-037 | DONE / historical, superseded by ADR-0015 |
| P1-07 Error Recovery Center | historical EXEC-037 task-domain file | DONE |
| P1-01 Goal Management | EXEC-038～039 | DONE |
| P1-02 Model Settings | EXEC-040～041 | DONE / Desktop-specific evidence historical；current Local Web capability reopened |
| P1-03 Data Control and Recovery | EXEC-1031～1034 | DONE |
| P1-06 Onboarding Readiness Foundation | EXEC-1061 | DONE / historical foundation |
| P1-06 Onboarding Product Closure | EXEC-1062 | historical DONE / **current Local Web model-config dependency reopened** |
| Local Single-User Authentication Removal | EXEC-047～051 | DONE |
| UI-03 Interactive Element System Refactor | EXEC-043～046 | ACTIVE / dependency-gated |
| CI v2 / Test Infrastructure Realignment | EXEC-052～058 | EXEC-052～053 DONE；EXEC-054 READY |

P1-06 的 `EXEC-1062` 与对应 Release Evidence 保留为生成时的历史完成快照，不得被解释为当前 Local Web 已具备可验证的模型配置闭环。当前 production onboarding 在 SYS08 canonical public model configuration summary 缺失时必须报告 dependency `PARTIAL` 且不得强制首次用户进入 `/welcome`；只有当前 `MODEL-CONFIG-*` Local Web capability 完成并提供真实 revision / verification / activation evidence 后，才能重新声明完整 P1-06 产品闭环。

## 3. Local Identity Governance Chain

```text
PRODUCT-POSITIONING
→ Local Single-User Identity Canonical Design Delta
→ ADR-0015 accepted
→ LID-* v2 frozen
→ Local Single-User Authentication Removal Vertical Slice
→ EXEC-047 → 048 → 049 → 050 → 051 DONE
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

## 8. Current Dependency Boundaries

- UI-03 必须按 EXEC-043 → 044 → 045 → 046 的完成门禁推进；不得让后序 EXEC 以“代码已部分出现”为由跳过 Completion Report。
- EXEC-054 已由 EXEC-053 DONE 解锁；完成后才允许 EXEC-055。
- EXEC-056 必须等待 EXEC-055 与 UI-03 EXEC-046 DONE。
- EXEC-057 在 EXEC-055 DONE 后可推进；若与 UI-03 后段存在直接文件冲突，优先保持独立 commit / PR。
- EXEC-058 是 Required Gate / main protection 的最终闭环，只有 EXEC-056 与 EXEC-057 均 DONE 后才可按原合同关闭。

## 9. Queue Contract

- 每个 EXEC 只能在自身 dependency gate 满足后执行；
- 后序依赖未 DONE 时返回 `BLOCKED_BY_DEPENDENCY`；
- active EXEC 不得互相扩大 Allowed Files 或混合 commit；
- 任何任务开始前先检查 `docs/product/PRODUCT-POSITIONING.md`；
- 产品级边界冲突按 `AGENTS.md` 报告 `POSITIONING GAP`；
- 公共语义、owner、schema、生产依赖出现未冻结选择时按 `AGENTS.md` 报告 `SPEC GAP`；
- 每个 EXEC 完成后先满足自身 AC / Required Tests / DoD，再移入 `completed/`；
- completed EXEC 保持不可变历史证据。

## 10. New EXEC Requirements

每份新 EXEC 必须包含：Objective、Dependencies、Required Product Positioning、Required Specs、Current Reality、Allowed Files、Forbidden Changes、Implementation Tasks、Acceptance Criteria、Required Tests、Completion Report Format。

执行前必须读取根 `AGENTS.md`、`docs/product/PRODUCT-POSITIONING.md`、本 EXEC 引用的全部 Spec，并核对当前代码和 Git 状态。不得通过删除测试、弱化断言、frontend-only state、auto-login、demo-token、legacy shortcut、Required→Optional 偷换或外部服务依赖伪造完成。

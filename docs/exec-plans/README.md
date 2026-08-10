# Askora Execution Plans

> 当前状态：Local Single-User / no-auth 基线与 CI v2 基础切换已合并；UI-03 代码已部分/大量提前落地，但 EXEC-043～046 尚未按冻结合同逐项验收归档。  
> Active / Frozen Queue：EXEC-043～046、EXEC-054～059  
> UI-03 acceptance chain：`EXEC-043 → EXEC-044 → EXEC-045 → EXEC-046`  
> Design System implementation：`EXEC-046 DONE → EXEC-059`  
> CI quality chain：`EXEC-053 DONE → EXEC-054 → EXEC-055 → {EXEC-056 after EXEC-046, EXEC-057} → EXEC-058`

本目录保存可直接交给 TraeCode / Codex 执行的工程任务合同，以及完成后的不可变归档。所有 EXEC 必须服从 [`../product/PRODUCT-POSITIONING.md`](../product/PRODUCT-POSITIONING.md)。EXEC 只能拆解已经冻结且不违反 Product Positioning 的 Spec / Vertical Slice，不能自行修改 Product Positioning、Canonical Design、ADR 或 Spec 语义。

```text
PRODUCT-POSITIONING
→ Canonical Design / Accepted ADR
→ Spec
→ Vertical Slice
→ EXEC
→ Code / Test
→ Release Evidence
```

如果既有 EXEC、Spec、ADR 或代码与 Product Positioning 冲突，应按 `AGENTS.md` 报告 `POSITIONING GAP`；不得以历史实现或 EXEC 已冻结为理由继续扩大冲突。

## 1. Current Main Reality

2026-08-10 的 `main` 已合并 PR #16（merge `658b4796`，implementation commit `f11859bf`）：

- EXEC-042、EXEC-048～053 已完成并归档；
- LocalOwner / no-auth / loopback Local Web baseline 已进入 `main`；
- CI v2 required/optional baseline 已进入 `main`；
- 同一 PR 还执行了 `CHAIN-A-UI-03` 的大量前端重构：Today/Learning/Library 三域、Learning shell/routes，以及 Today/Library/Settings progressive restructuring。

但 UI-03 的 EXEC-043～046 **没有按冻结合同逐项归档和形成独立 Acceptance Evidence**。因此当前真实状态不是“UI-03 尚未实现”，而是：

```text
Implementation present in main
+
EXEC lifecycle / acceptance evidence incomplete
```

处理原则：**先验收 main → 只修实际 Gap → 逐项归档 EXEC；禁止整套重做已有正确实现。**

## 2. Active / Frozen Queue

| EXEC | Task | Status | Dependency / Current handling |
|---|---|---|---|
| [EXEC-043](active/EXEC-043-ui-03a-shell-routes-learning-domain.md) | UI-03A Shell, Routes and Learning Domain | FROZEN / ACCEPTANCE_PENDING | 原 dependency 已满足；main 已有实现，先验收再补 Gap/归档 |
| [EXEC-044](active/EXEC-044-ui-03b-today-primary-hierarchy.md) | UI-03B Today Primary Hierarchy | FROZEN / BLOCKED_BY_EXEC_043_ACCEPTANCE | main 已有实现迹象；等待 EXEC-043 正式收口 |
| [EXEC-045](active/EXEC-045-ui-03c-library-progressive-disclosure.md) | UI-03C Library Progressive Disclosure | FROZEN / BLOCKED_BY_EXEC_044_ACCEPTANCE | main 已有实现迹象；等待 EXEC-044 正式收口 |
| [EXEC-046](active/EXEC-046-ui-03d-settings-legacy-release-closure.md) | UI-03D Settings / Legacy / Release Closure | FROZEN / BLOCKED_BY_EXEC_045_ACCEPTANCE | main 已有实现迹象；最终形成 UI-03 Release Evidence |
| [EXEC-054](active/EXEC-054-required-core-test-realignment.md) | Required Core Test Realignment | FROZEN | requires EXEC-053 DONE；dependency satisfied，仍须检查并发文件 |
| [EXEC-055](active/EXEC-055-local-data-migration-recovery-rebuild-gate.md) | Local Data Migration, Recovery & Rebuild Gate | FROZEN / BLOCKED_BY_EXEC_054 | serial CI quality chain |
| [EXEC-056](active/EXEC-056-local-web-chromium-e2e.md) | Local Web Chromium E2E | FROZEN / BLOCKED_BY_DEPENDENCY_GATE | requires EXEC-055 + EXEC-046 DONE |
| [EXEC-057](active/EXEC-057-ci-workflow-quality-supply-chain.md) | CI Workflow, Quality & Supply-chain Realignment | FROZEN / BLOCKED_BY_EXEC_055 | may proceed after 055 if no frontend-file conflict |
| [EXEC-058](active/EXEC-058-required-gate-main-protection-closure.md) | Required Gate & Main Protection Closure | FROZEN / BLOCKED_BY_DEPENDENCY_GATE | requires EXEC-056 + EXEC-057 DONE |
| [EXEC-059](active/EXEC-059-ui-design-system-component-foundation.md) | UI Design System & Component Foundation | FROZEN / BLOCKED_BY_EXEC_046 | execute only after UI-03 acceptance/release closure |

## 3. Completed Baseline Relevant to Current Work

| Baseline | EXEC | Final status |
|---|---|---|
| v0.2 First Vertical Learning Loop | EXEC-001～006 | DONE |
| v0.3 historical implementation | EXEC-007～013 | DONE / historical snapshot |
| v0.3 Production Sequential Teaching Policy Closure | EXEC-042 | DONE / archived 2026-08-10 |
| Rich Response / UI-01 / UI-02 / Book-to-Learning | EXEC-014～030 | DONE |
| P1 Library / Identity historical / Goal / Model / Data / Onboarding | EXEC-031～041, 1031～1034, 1061～1062 | DONE；部分旧 identity semantics 已被 ADR-0015 supersede |
| LocalOwner Foundation | EXEC-047 | DONE |
| Local Single-User Authentication Removal | EXEC-048～051 | DONE / archived via PR #16 |
| CI v2 Governance + Production Runtime Baseline | EXEC-052～053 | DONE / archived via PR #16 |

Completed EXEC 保持历史证据，不应为了“统一现状”回写其内容。

## 4. UI-03 Governance Chain

```text
PRODUCT-POSITIONING
→ Interactive Element System Canonical Design Delta
→ ADR-0014 accepted
→ UI-IES / UI-IA / UI-SCREEN / UI-VIS / UI-COMP / UI-QUAL frozen
→ UI-03 Vertical Slice frozen
→ main existing implementation (PR #16)
→ EXEC-043 acceptance
→ EXEC-044 acceptance
→ EXEC-045 acceptance
→ EXEC-046 release closure
→ UI-03 Release Evidence
```

四个 EXEC 仍必须按顺序验收。即使代码已在一次大 PR 中提前合并，也不得跳过逐项 AC；同样也不得因为文档仍写 `BLOCKED_BY_DEPENDENCY_GATE` 就重复实现已经正确的代码。

每个步骤采用：

```text
Read current main
→ Compare with frozen AC
→ Run targeted tests
→ Fix only proven gaps
→ Run required gates
→ Archive that EXEC
```

UI-03 只改变 information architecture、interaction hierarchy、presentation exposure 与 route organization；不得恢复 ADR-0015 已删除的 Account/Login/AuthSession 语义，不得改变 SYS01～SYS08 owner truth。

## 5. UI Design System Implementation Chain

`UI-VIS-*` 与 `UI-COMP-*` 已冻结。其工程落地由 EXEC-059 管理：

```text
EXEC-046 DONE
→ EXEC-059 Design System & Component Foundation
→ project-level responsive / keyboard / accessibility closure
```

EXEC-059 的目标是收敛现有 React + CSS 基础，不是新建独立 Design System 产品。禁止无收益引入 Storybook、token compiler、大型 UI framework 或第二套 component abstraction。

## 6. CI / Quality Chain

```text
EXEC-052 DONE Governance / Oracle Classification
    ↓
EXEC-053 DONE Production Local Runtime
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

`EXEC-056` 必须等待 UI-03 `EXEC-046 DONE`，避免在尚未正式验收的 route/shell 上冻结浏览器 E2E。

## 7. Concurrency Rules

- UI-03 EXEC-043～046 严格按 acceptance 顺序处理；
- EXEC-059 必须等待 EXEC-046 DONE，避免与 Shell/Today/Library/Settings 收口发生样式/组件覆盖；
- CI Quality EXEC 若修改 frontend test/runtime 配置，与 UI active files 有直接冲突时应暂停并返回 dependency/file-overlap，而不是混合 commit；
- active EXEC 不得互相扩大 Allowed Files；
- 一个 commit 不应同时宣告多个尚未独立满足 AC 的 EXEC DONE。

## 8. Queue Contract

- 每个 EXEC 只能在自身 dependency gate 满足后执行；
- 后序依赖未 DONE 时返回 `BLOCKED_BY_DEPENDENCY`；
- 当前已有代码时，先做 conformance review，禁止默认重写；
- 任何任务开始前先读取 `AGENTS.md` 与 `docs/product/PRODUCT-POSITIONING.md`；
- 产品边界冲突报告 `POSITIONING GAP`；
- 公共语义、owner、schema、生产依赖出现未冻结选择时报告 `SPEC GAP`；
- 每个 EXEC 完成后必须满足自身 AC / Required Tests / DoD，再移入 `completed/`；
- completed EXEC 保持不可变历史证据。

## 9. New EXEC Requirements

每份新 EXEC 必须包含：Objective、Dependencies、Required Product Positioning、Required Specs、Current Reality、Allowed Files、Forbidden Changes、Implementation Tasks、Acceptance Criteria、Required Tests、Completion Report Format。

执行前必须核对当前代码和 Git 状态。不得通过删除测试、弱化断言、frontend-only fake state、legacy shortcut、Required→Optional 偷换或外部服务依赖伪造完成。

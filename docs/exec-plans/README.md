# Askora Execution Plans

> 当前状态：Local Single-User / no-auth 与 CI v2 基线已进入 `main`；UI-03、Quality 与 v1 Product Architecture 为三个独立执行域。  
> UI-03 chain：`EXEC-043 DONE → 044 → 045 → 046 → 059`  
> Quality chain：`EXEC-053 DONE → 054 → 055 → {056 after 046, 057} → 058`  
> v1 Product Architecture：`060 → 061 → {062,063,065}`，且 `060 → 064`；之后 `066 → 067`

本目录保存可直接交给 TraeCode / Codex 执行的工程任务合同，以及完成后的不可变归档。所有 EXEC 必须服从 [`../product/PRODUCT-POSITIONING.md`](../product/PRODUCT-POSITIONING.md)。EXEC 只能拆解已经冻结且不违反 Product Positioning 的 Spec / ADR / Vertical Slice，不能自行修改上位产品、架构或领域语义。

```text
PRODUCT-POSITIONING
→ Canonical Design / Accepted ADR
→ Spec
→ EXEC / Linear Issue
→ Code / Test
→ Release Evidence
```

如果既有 EXEC、Spec、ADR 或代码与 Product Positioning 冲突，报告 `POSITIONING GAP`；公共 ownership/security/schema 仍有歧义时报告 `BLOCKED_BY_SPEC_GAP`。不得用历史实现或历史 DONE 反向覆盖当前产品边界。

## 1. Current Main Reality

2026-08-10 `main` 已具备：

- LocalOwner / no-auth / loopback Local Web baseline；
- v0.3 production sequential Teaching Policy closure；
- CI v2 Required/Optional workflow baseline；
- UI-03 大部分页面实现已提前进入代码，需要按 frozen AC 逐段验收；
- v1 Product Positioning conformance audit 已冻结，当前结论仍是 `FAIL`，主要缺口为 standalone runtime、durable Workspace/Project scope、Workspace-scoped learner/retrieval、Local Web BYOK、Material Trash lifecycle 与 non-v1 surface cleanup。

当前代码存在度不等于对应 EXEC DONE。统一处理原则：

```text
Read current main
→ Compare with frozen Product/ADR/Spec/AC
→ Preserve correct existing implementation
→ Fix only proven gaps
→ Run targeted + Required gates
→ Archive that EXEC
```

## 2. Active / Frozen Queue

### 2.1 UI / Design System

| EXEC | Task | Status | Dependency |
|---|---|---|---|
| [EXEC-043](completed/EXEC-043-ui-03a-shell-routes-learning-domain.md) | UI-03A Shell / Routes / Learning Domain | **DONE / ARCHIVED** | baseline |
| [EXEC-044](active/EXEC-044-ui-03b-today-primary-hierarchy.md) | UI-03B Today Primary Hierarchy | FROZEN / READY | 043 DONE |
| [EXEC-045](active/EXEC-045-ui-03c-library-progressive-disclosure.md) | UI-03C Library Progressive Disclosure | FROZEN / BLOCKED | 044 DONE |
| [EXEC-046](active/EXEC-046-ui-03d-settings-legacy-release-closure.md) | UI-03D Settings / Legacy / Release Closure | FROZEN / BLOCKED | 045 DONE |
| [EXEC-059](active/EXEC-059-ui-design-system-component-foundation.md) | UI Design System & Component Foundation | FROZEN / BLOCKED | 046 DONE |

### 2.2 Quality / CI

| EXEC | Task | Status | Dependency |
|---|---|---|---|
| [EXEC-054](active/EXEC-054-required-core-test-realignment.md) | Required Core Test Realignment | FROZEN / READY | 053 DONE |
| [EXEC-055](active/EXEC-055-local-data-migration-recovery-rebuild-gate.md) | Local Data Migration / Recovery / Rebuild Gate | FROZEN / BLOCKED | 054 DONE |
| [EXEC-056](active/EXEC-056-local-web-chromium-e2e.md) | Local Web Chromium E2E | FROZEN / BLOCKED | 055 + 046 DONE |
| [EXEC-057](active/EXEC-057-ci-workflow-quality-supply-chain.md) | CI Workflow / Quality / Supply-chain | FROZEN / BLOCKED | 055 DONE |
| [EXEC-058](active/EXEC-058-required-gate-main-protection-closure.md) | Required Gate / Main Protection Closure | FROZEN / BLOCKED | 056 + 057 DONE |

### 2.3 v1 Product Architecture

| EXEC | Linear | Task | Status | Dependency |
|---|---|---|---|---|
| [EXEC-060](active/EXEC-060-v1-standalone-local-runtime-closure.md) | XIK-167 | Standalone Local Runtime Closure | **FROZEN / READY** | current Product/Specs sufficient |
| [EXEC-061](active/EXEC-061-workspace-project-session-persistence-migration.md) | XIK-171 | Workspace / Project / Session Persistence & Migration | FROZEN / BLOCKED | 060 DONE |
| [EXEC-062](active/EXEC-062-workspace-scoped-learner-state-projection.md) | XIK-177 | Workspace-scoped Learner Evidence / Mastery / Review | FROZEN / BLOCKED | 061 DONE |
| [EXEC-063](active/EXEC-063-workspace-scoped-retrieval-cutover.md) | XIK-172 | Workspace-scoped Material / SYS02 Retrieval | FROZEN / BLOCKED | 061 DONE |
| [EXEC-064](active/EXEC-064-local-web-byok-secure-activation.md) | XIK-173 | Local Web BYOK / LocalSecretStore / Activation | FROZEN / BLOCKED | 060 DONE |
| [EXEC-065](active/EXEC-065-material-trash-restore-permanent-delete.md) | XIK-174 | Material Trash / Restore / Permanent Delete | FROZEN / BLOCKED | 061 DONE |
| [EXEC-066](active/EXEC-066-v1-noncore-runtime-surface-cleanup.md) | XIK-175 | Non-core OCR/DOCX/Auth/service-era Cleanup | FROZEN / BLOCKED | 062 + 063 + 064 + 065 DONE |
| [EXEC-067](active/EXEC-067-v1-product-positioning-conformance-release-gate.md) | XIK-176 | Product Positioning Conformance Release Gate | FROZEN / BLOCKED | 060..066 + relevant Quality gates |

## 3. v1 Product Architecture Governance Chain

Upstream design gaps are already frozen:

```text
PRODUCT-POSITIONING
→ current-main v1 conformance audit
→ ADR-0016 + WSP-*          Workspace/Project/Session
→ ADR-0017 + LSS-*          LocalSecretStore
→ MATLIFE-*                 Material lifecycle
→ EXEC-060..067
```

Frozen execution graph：

```text
EXEC-060 Standalone Local Runtime
    ├──────────────→ EXEC-064 Local Web BYOK
    ↓
EXEC-061 Workspace / Project / Session Foundation
    ├→ EXEC-062 Learner Evidence / Mastery / Review Scope
    ├→ EXEC-063 Material / Retrieval Scope
    └→ EXEC-065 Material Lifecycle

EXEC-062 + EXEC-063 + EXEC-064 + EXEC-065
    ↓
EXEC-066 Non-core Surface Cleanup
    ↓
EXEC-067 Product Positioning Acceptance
```

### 3.1 Why EXEC-060 precedes 061/064

Workspace migrations and secure model activation must be built against the actual production-local SQLite/runtime boundary, not service-era defaults. EXEC-060 therefore establishes the runtime substrate first.

### 3.2 Why 062 and 063 are separate

Workspace existence is insufficient if learner state or retrieval remains owner-global. They have different owners, migrations and test oracles and therefore close independently after EXEC-061.

### 3.3 Why 065 follows Workspace foundation

Trash/Permanent Delete preview and Data Control scope need exact Workspace/Material/Project relations. Material lifecycle must not be implemented on an owner-global schema that will immediately migrate again.

### 3.4 Why 066 runs last among implementations

OCR/DOCX/Auth/service-era cleanup is proof-driven. Delete/isolate only after the new runtime/Workspace/BYOK/Material paths are proven so migration/compatibility dependencies can be classified correctly.

## 4. Completed Baseline Relevant to Current Work

| Baseline | EXEC | Final status |
|---|---|---|
| v0.2 First Vertical Learning Loop | EXEC-001～006 | DONE |
| v0.3 historical implementation | EXEC-007～013 | DONE / historical snapshot |
| v0.3 Production Sequential Teaching Policy Closure | EXEC-042 | DONE / archived |
| Rich Response / UI-01 / UI-02 / Book-to-Learning | EXEC-014～030 | DONE / historical implemented baseline |
| P1 Library / historical Identity / Goal / Model / Data / Onboarding | EXEC-031～041, 1031～1034, 1061～1062 | DONE；部分 mechanics 已被 v1 Product Positioning supersede |
| LocalOwner Foundation | EXEC-047 | DONE |
| Local Single-User Authentication Removal | EXEC-048～051 | DONE |
| CI v2 Governance + historical Production Runtime baseline | EXEC-052～053 | DONE；EXEC-060 closes remaining Product Positioning drift found by later audit |
| UI-03A Shell / Routes / Learning Domain | EXEC-043 | DONE |

Completed EXEC 保持历史证据，不回写成“当时已经满足后来冻结的 v1 约束”。

## 5. UI-03 Chain

```text
EXEC-043 DONE
→ EXEC-044
→ EXEC-045
→ EXEC-046
→ EXEC-059
```

UI work changes navigation/interaction/presentation only. It must consume Workspace/BYOK/Trash domain contracts when those become available; it MUST NOT create frontend-only Workspace, secret or Material lifecycle truth.

## 6. Quality Chain and Cross-project Gates

```text
EXEC-054
→ EXEC-055
├→ EXEC-057
└→ EXEC-056 after EXEC-046
      ↓
EXEC-058
```

Product Architecture and Quality are separate Linear projects. Product EXEC may add feature-specific tests, but must not take over branch-protection/oracle governance. EXEC-067 requires current Required CI and relevant Quality release/regression evidence.

## 7. Concurrency Rules

- EXEC-060 should run before 061/064.
- After 061, EXEC-062/063/065 MAY run in parallel only if their Allowed Files do not overlap materially; otherwise serialize locally.
- EXEC-064 MAY run in parallel with 062/063/065 after 060 when provider/settings files do not conflict with active UI-03 Settings work; if EXEC-046/059 touches the same frontend files, pause and coordinate rather than mix commits.
- EXEC-066 waits for all P0 product implementations.
- EXEC-067 is acceptance only and never patches implementation except to return a specific gap upstream.
- UI-03 EXEC-044～046 remain serial.
- EXEC-059 waits for 046.
- Quality EXEC follow their own dependency chain.
- One commit must not claim multiple EXEC DONE unless every affected EXEC has separately evidenced AC and lifecycle transition.

## 8. Queue Contract

- dependency gate not satisfied → `BLOCKED_BY_DEPENDENCY`;
- existing correct code → preserve, do not rewrite for activity;
- Product Positioning conflict → `POSITIONING GAP`;
- unresolved owner/schema/security decision → `BLOCKED_BY_SPEC_GAP`;
- Required test failure → do not archive/claim PASS;
- do not weaken tests, convert Required→Optional, introduce frontend-only fake truth or external runtime dependency to manufacture completion;
- completed EXEC becomes immutable historical evidence under `completed/`.

## 9. New EXEC Requirements

Every new EXEC must contain Objective、Dependencies、Required Sources、Current Reality、Allowed Files、Forbidden Changes、Implementation Tasks、Acceptance Criteria、Required Tests and Completion Report format.

Execution starts by fetching current `main` and checking concurrent active work. GitHub remains the durable design/implementation fact source; Linear tracks work state; Codex implements frozen contracts; ChatGPT independently accepts current-main evidence.
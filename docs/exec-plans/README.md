# Askora Execution Plans

> 当前状态：Local Single-User / no-auth、CI v2、Canonical Product Definition 与 consolidated Experience/UI contracts 已进入治理链。  
> Current UI-04 chain：`EXEC-068 DONE → 069 DONE → 070 → 071 → 072 → 073 → 046 → 059`  
> `EXEC-045`：**SUPERSEDED / DO NOT EXECUTE**，Library current work 由 `EXEC-072 / XIK-165` 承担。  
> Quality chain：`EXEC-053 DONE → 054 → 055 → {056 after 046, 057} → 058`  
> v1 Product Architecture：`060 → 061 → {062,063,065}`，且 `060 → 064`；之后 `066 → 067`
> Learning Conversation Message System：`ADR-0020 + LCMS-* → EXEC-075 DONE`

本目录保存可直接交给 TraeCode / Codex 执行的工程任务合同，以及完成后的不可变归档。

所有 EXEC 必须服从：

```text
PRODUCT-STRATEGY
→ PRODUCT-POSITIONING
→ PRODUCT-DEFINITION
→ Current Canonical Design / Experience
→ Accepted ADR
→ Current Spec
→ EXEC / Linear Issue
→ Code / Test
→ Release Evidence
```

EXEC 只能拆解已经冻结的 Product / Design / Spec，不得自行修改上位产品、架构、学习语义或 v1 Scope。

如果冲突：

- Product Positioning conflict → `POSITIONING GAP`；
- Product Capability / Requirement / Acceptance missing or contradicted → `PRODUCT DEFINITION GAP`；
- Design / Spec / ownership / security ambiguity → `BLOCKED_BY_SPEC_GAP`；
- dependency 未满足 → `BLOCKED_BY_DEPENDENCY`。

不得用历史实现、历史 UI Spec 或历史 DONE 反向覆盖 current truth。

---

## 1. Current Main Execution Rule

每个 EXEC 开始前：

```text
Read current main
→ Read current Linear state
→ Identify Product Definition trace
→ Read current Design / ADR / Spec
→ Compare code with frozen AC
→ Preserve correct existing implementation
→ Fix only proven gaps
→ Run Required gates
→ Archive only after evidence PASS
```

静态 EXEC 文档的 `Current Reality` 不是实时状态源；实时状态属于 current `main` + Linear。

---

## 2. Active / Frozen Queue

### 2.1 Experience / UI / Design System

| EXEC | Task | Status | Dependency |
|---|---|---|---|
| [EXEC-043](completed/EXEC-043-ui-03a-shell-routes-learning-domain.md) | Historical UI-03A Shell / Routes | **DONE / ARCHIVED** | baseline |
| [EXEC-044](completed/EXEC-044-ui-03b-today-primary-hierarchy.md) | Today Primary Hierarchy | **DONE / ARCHIVED** | 043 DONE |
| [EXEC-045](active/EXEC-045-ui-03c-library-progressive-disclosure.md) | Historical UI-03C Library Progressive Disclosure | **SUPERSEDED / DO NOT EXECUTE** | replaced by 072 / XIK-165 |
| [EXEC-068](completed/EXEC-068-ui-04a-workspace-context-shell-routes.md) | Workspace Context / Shell / Routes | **DONE / ARCHIVED** | ADR-0018/0019 + product arch gate |
| [EXEC-069](completed/EXEC-069-ui-04b-learning-context-drawer.md) | Learning Context Drawer | **DONE / ARCHIVED** | 068 DONE |
| [EXEC-070](active/EXEC-070-ui-04c-usernote-current-material-right-rail.md) | UserNote + Current Material Right Rail | FROZEN / BLOCKED | 069 DONE + owner/spec gate |
| [EXEC-071](active/EXEC-071-ui-04d-learning-management-exposure-removal.md) | Learning Management Exposure Removal | FROZEN / BLOCKED | 070 DONE |
| [EXEC-072](active/EXEC-072-ui-04e-library-v1-no-ocr-exposure.md) | Library v1 Exposure / No OCR | FROZEN / BLOCKED | 071 DONE |
| [EXEC-073](active/EXEC-073-ui-04f-responsive-accessibility-release-acceptance.md) | UI-04 Responsive / A11y / Release Acceptance | FROZEN / BLOCKED | 072 DONE |
| [EXEC-046](active/EXEC-046-ui-03d-settings-legacy-release-closure.md) | Settings / Legacy UI Closure | FROZEN / BLOCKED | 073 DONE |
| [EXEC-059](active/EXEC-059-ui-design-system-component-foundation.md) | Design System & Component Foundation | FROZEN / BLOCKED | 046 DONE |

### Why this order

- `EXEC-045` 原 Library progressive-disclosure 意图已被 current `UI-LIB-*` 吸收；其 OCR compatibility exposure 与 current no-OCR normal UI 冲突，因此不再执行。
- `EXEC-070..073` 先完成 current Workspace/Learning/Library surfaces 及 UI-04 release acceptance。
- `EXEC-046` 随后只做 Settings / Legacy bounded closure，避免与 `EXEC-073` 的全前端 responsive/a11y 修复重叠。
- `EXEC-059` 最后做 reusable Design System normalization，避免在页面结构仍变动时先进行大范围 token/component 重构。

Current UI implementation 必须从：

- `docs/design/experience/**`；
- `docs/specs/ui/README.md` 的 current-only contracts；
- `docs/specs/frontend/ui-read-model-contracts.md`（技术 projection）

开始。旧 UI matrices 只作历史 trace。

---

### 2.2 Quality / CI

| EXEC | Task | Status | Dependency |
|---|---|---|---|
| [EXEC-054](active/EXEC-054-required-core-test-realignment.md) | Required Core Test Realignment | FROZEN / READY | 053 DONE |
| [EXEC-055](active/EXEC-055-local-data-migration-recovery-rebuild-gate.md) | Local Data Migration / Recovery / Rebuild Gate | FROZEN / BLOCKED | 054 DONE |
| [EXEC-056](active/EXEC-056-local-web-chromium-e2e.md) | Local Web Chromium E2E | FROZEN / BLOCKED | 055 + 046 DONE |
| [EXEC-057](active/EXEC-057-ci-workflow-quality-supply-chain.md) | CI Workflow / Quality / Supply-chain | FROZEN / BLOCKED | 055 DONE |
| [EXEC-058](active/EXEC-058-required-gate-main-protection-closure.md) | Required Gate / Main Protection Closure | FROZEN / BLOCKED | 056 + 057 DONE |

---

### 2.3 Engineering Maintenance

| EXEC | Task | Status | Dependency |
|---|---|---|---|
| [EXEC-074](completed/EXEC-074-postgresql-membership-constraint-reconciliation.md) | PostgreSQL Membership Constraint Reconciliation | **DONE / ARCHIVED** | historical compatibility baseline |

---

### 2.4 Learning Conversation Message System

| EXEC | Task | Status | Dependency |
|---|---|---|---|
| [EXEC-075](completed/EXEC-075-learning-conversation-message-system-vertical-slice.md) | Learning Conversation Message System Vertical Slice | **DONE / ARCHIVED** | ADR-0020 + LCMS Spec/Vertical Slice |

---

### 2.5 v1 Product Architecture

| EXEC | Linear | Task | Status | Dependency |
|---|---|---|---|---|
| [EXEC-060](active/EXEC-060-v1-standalone-local-runtime-closure.md) | XIK-167 | Standalone Local Runtime Closure | FROZEN / READY | current Product/Specs sufficient |
| [EXEC-061](active/EXEC-061-workspace-project-session-persistence-migration.md) | XIK-171 | Workspace / Project / Session Persistence & Migration | FROZEN / BLOCKED | 060 DONE |
| [EXEC-062](active/EXEC-062-workspace-scoped-learner-state-projection.md) | XIK-177 | Workspace-scoped Learner Evidence / Mastery / Review | FROZEN / BLOCKED | 061 DONE |
| [EXEC-063](active/EXEC-063-workspace-scoped-retrieval-cutover.md) | XIK-172 | Workspace-scoped Material / SYS02 Retrieval | FROZEN / BLOCKED | 061 DONE |
| [EXEC-064](active/EXEC-064-local-web-byok-secure-activation.md) | XIK-173 | Local Web BYOK / LocalSecretStore / Activation | FROZEN / BLOCKED | 060 DONE |
| [EXEC-065](active/EXEC-065-material-trash-restore-permanent-delete.md) | XIK-174 | Material Trash / Restore / Permanent Delete | FROZEN / BLOCKED | 061 DONE |
| [EXEC-066](active/EXEC-066-v1-noncore-runtime-surface-cleanup.md) | XIK-175 | Non-core OCR/DOCX/Auth/service-era Cleanup | FROZEN / BLOCKED | 062 + 063 + 064 + 065 DONE |
| [EXEC-067](active/EXEC-067-v1-product-positioning-conformance-release-gate.md) | XIK-176 | Product Positioning Conformance Release Gate | FROZEN / BLOCKED | 060..066 + relevant Quality gates |

---

## 3. v1 Product Architecture Governance Chain

```text
PRODUCT-POSITIONING
→ PRODUCT-DEFINITION
→ current-main conformance evidence
→ ADR-0016 + WSP-*          Workspace/Project/Session
→ ADR-0017 + LSS-*          LocalSecretStore
→ MATLIFE-*                 Material lifecycle
→ EXEC-060..067
```

Frozen graph：

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

Workspace migrations and secure model activation must be built against the actual production-local SQLite/runtime boundary, not service-era defaults。

### 3.2 Why 062 and 063 are separate

Workspace existence is insufficient if learner state or retrieval remains owner-global；两者有不同 owner、migration 与 test oracle。

### 3.3 Why 065 follows Workspace foundation

Trash/Permanent Delete preview 与 Data Control scope 依赖 exact Workspace/Material/Project relation。

### 3.4 Why 066 runs last among implementations

OCR/DOCX/Auth/service-era cleanup 是 proof-driven；必须先证明新 runtime/Workspace/BYOK/Material paths。

---

## 4. Completed Baseline Relevant to Current Work

| Baseline | EXEC | Final status |
|---|---|---|
| v0.2 First Vertical Learning Loop | EXEC-001～006 | DONE |
| v0.3 historical implementation | EXEC-007～013 | DONE / historical snapshot |
| v0.3 Production Sequential Teaching Policy Closure | EXEC-042 | DONE / archived |
| Rich Response / UI-01 / UI-02 / Book-to-Learning | EXEC-014～030 | DONE / historical implemented baseline |
| P1 Library / historical Identity / Goal / Model / Data / Onboarding | EXEC-031～041, 1031～1034, 1061～1062 | DONE；部分 mechanics 被 current v1 Product Definition supersede |
| LocalOwner Foundation | EXEC-047 | DONE |
| Local Single-User Authentication Removal | EXEC-048～051 | DONE |
| CI v2 Governance + historical Production Runtime baseline | EXEC-052～053 | DONE；后续 Product Architecture 负责 current v1 closure |
| UI-03A Shell / Routes | EXEC-043 | DONE / historical UI migration |
| Today Primary Hierarchy | EXEC-044 | DONE / still-current invariant |
| UI-04A Workspace Shell / Routes | EXEC-068 | DONE |
| UI-04B Learning Context Drawer | EXEC-069 | DONE |

Completed EXEC 是当时版本的 evidence，不自动证明后来冻结的 Product/Experience requirements。

---

## 5. Current UI Chain

```text
EXEC-068 DONE
→ EXEC-069 DONE
→ EXEC-070
→ EXEC-071
→ EXEC-072
→ EXEC-073
→ EXEC-046
→ EXEC-059
```

`EXEC-045` 已 superseded，不属于 current chain。

UI changes navigation/interaction/presentation only。必须消费 Workspace/BYOK/Material/Data contracts，不得创建 frontend-only owner truth。

---

## 6. Quality Chain and Cross-project Gates

```text
EXEC-054
→ EXEC-055
├→ EXEC-057
└→ EXEC-056 after EXEC-046
      ↓
EXEC-058
```

Product Architecture、UI Redesign、Quality/CI 是独立工作流。Feature EXEC 可以补 feature-specific tests，但不能接管 branch protection/oracle governance。

---

## 7. Concurrency Rules

- EXEC-060 should run before 061/064。
- After 061，EXEC-062/063/065 MAY 并行，仅当 Allowed Files 无实质 overlap。
- EXEC-064 可在 060 后与 product architecture tasks 并行，但如果与 active Settings/UI task 修改同一 frontend files，必须串行。
- EXEC-066 waits for all P0 product implementations。
- EXEC-067 是 acceptance，不自行扩大实现修复范围。
- UI current chain 070→071→072→073→046→059 串行；不得执行 045。
- Quality chain 保持自身依赖。
- 一个 commit 不得声称多个 EXEC DONE，除非每个 EXEC 均有独立 AC/evidence/lifecycle transition。

---

## 8. Queue Contract

- dependency gate not satisfied → `BLOCKED_BY_DEPENDENCY`；
- existing correct code → preserve；
- Product Positioning conflict → `POSITIONING GAP`；
- Product Definition missing/contradicted → `PRODUCT DEFINITION GAP`；
- unresolved owner/schema/security/design decision → `BLOCKED_BY_SPEC_GAP`；
- Required test failure → no archive / no PASS；
- 不得弱化测试、Required→Optional、引入 frontend fake truth 或外部 runtime dependency 来制造 completion；
- completed EXEC under `completed/` is immutable historical evidence；
- superseded EXEC 保留 supersession reason，但不得标 DONE。

---

## 9. New EXEC Requirements

每个新 EXEC 必须包含：

- Objective
- Product Definition traceability
- Dependencies
- Required Sources
- Current Reality（并声明执行时重新读取 current main）
- Allowed Files
- Forbidden Changes
- Implementation Tasks
- Acceptance Criteria
- Required Tests
- Completion Report

Execution starts by reading current `main` + Linear and checking concurrent active work。GitHub 保存 durable design/implementation truth；Linear 管理实时工作状态；Codex/TraeCode 执行冻结合同；ChatGPT 负责设计与验收。

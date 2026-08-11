# Askora Active Planning

> 状态：Current Execution Contract Index
> 实时状态来源：Linear + current `main`
> 最近核对：2026-08-11

`docs/planning/` 只保存**仍可能执行**的冻结 EXEC。它不是 Product Backlog，也不复制 Linear 的实时优先级和状态。

所有 EXEC 必须服从：

```text
PRODUCT-STRATEGY
→ PRODUCT-POSITIONING
→ PRODUCT-DEFINITION
→ Current Canonical Design
→ Accepted ADR
→ Current Spec
→ Linear / EXEC
→ Code / Test
```

执行前必须重新读取 current `main` 与 Linear；文件中的 `Current Reality`、Status 或 dependency 只是创建/最近维护时的快照。

## 1. Experience / UI

| EXEC | 任务 | 文档内依赖 |
|---|---|---|
| [EXEC-070](execs/EXEC-070-ui-04c-usernote-current-material-right-rail.md) | UserNote + Current Material Right Rail | EXEC-069 + owner/spec gate |
| [EXEC-071](execs/EXEC-071-ui-04d-learning-management-exposure-removal.md) | Learning Management Exposure Removal | EXEC-070 |
| [EXEC-072](execs/EXEC-072-ui-04e-library-v1-no-ocr-exposure.md) | Library v1 Exposure / No OCR | EXEC-071 |
| [EXEC-073](execs/EXEC-073-ui-04f-responsive-accessibility-release-acceptance.md) | Responsive / Accessibility / Release Acceptance | EXEC-072 |
| [EXEC-046](execs/EXEC-046-ui-03d-settings-legacy-release-closure.md) | Settings / Legacy UI Closure | EXEC-073 |
| [EXEC-059](execs/EXEC-059-ui-design-system-component-foundation.md) | Design System & Component Foundation | EXEC-046 |

新的 UI 实现从 `docs/design/experience/**`、`docs/specs/ui/README.md` 的 current-only contracts 与 `docs/specs/frontend/ui-read-model-contracts.md` 开始。旧 UI Delta / matrices 已在 `docs/archive/`，只用于追溯。

## 2. Quality / CI

| EXEC | 任务 | 文档内依赖 |
|---|---|---|
| [EXEC-054](execs/EXEC-054-required-core-test-realignment.md) | Required Core Test Realignment | EXEC-053 |
| [EXEC-055](execs/EXEC-055-local-data-migration-recovery-rebuild-gate.md) | Local Data Migration / Recovery / Rebuild Gate | EXEC-054 |
| [EXEC-056](execs/EXEC-056-local-web-chromium-e2e.md) | Local Web Chromium E2E | EXEC-055 + EXEC-046 |
| [EXEC-057](execs/EXEC-057-ci-workflow-quality-supply-chain.md) | CI Workflow / Quality / Supply-chain | EXEC-055 |
| [EXEC-058](execs/EXEC-058-required-gate-main-protection-closure.md) | Required Gate / Main Protection Closure | EXEC-056 + EXEC-057 |

## 3. v1 Product Architecture

| EXEC | Linear | 任务 | 2026-08-11 Linear snapshot |
|---|---|---|---|
| [EXEC-064](execs/EXEC-064-local-web-byok-secure-activation.md) | XIK-173 | Local Web BYOK / LocalSecretStore / Activation | Backlog |
| [EXEC-066](execs/EXEC-066-v1-noncore-runtime-surface-cleanup.md) | XIK-175 | Non-core OCR/DOCX/Auth/service-era Cleanup | Backlog |
| [EXEC-077](execs/EXEC-077-course-workspace-selection-platform.md) | XIK-189 | Course Workspace Selection / Activity Projection Platform | Blocked until XIK-188 merge |

已完成或 superseded 的 EXEC-045、060、061、062、063、065、067 已根据 Linear/current history 移至 [`archive/exec-plans/`](../archive/exec-plans/)。Archive path 不改变当时合同内容，也不代表当前 checkout 已重新验收。

## 4. Queue Contract

- Product Positioning conflict → `POSITIONING GAP`；
- Product Capability / Requirement / Acceptance 缺失或冲突 → `PRODUCT DEFINITION GAP`；
- Design / owner / schema / security 决策不完整 → `BLOCKED_BY_SPEC_GAP`；
- dependency 不满足 → `BLOCKED_BY_DEPENDENCY`；
- Required gate failure → 不得归档为完成；
- completed / canceled / superseded EXEC → 移至 `docs/archive/exec-plans/`；
- 实时状态只在 Linear 维护，GitHub index 只提供长期可审阅的任务合同入口。

## 5. 新 EXEC 最低要求

每个新 EXEC 必须包含 Objective、Product Definition traceability、Dependencies、Required Sources、Current Reality、Allowed Files、Forbidden Changes、Implementation Tasks、Acceptance Criteria、Required Tests 与 Completion Report 格式。

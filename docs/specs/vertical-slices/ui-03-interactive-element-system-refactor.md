# UI-03 — Interactive Element System Refactor

> Status: **FROZEN / BLOCKED_BY_DEPENDENCY_GATE**  
> Governing: `ADR-0014`, `UI-IES-*`, `UI-IA-*`, `UI-SCREEN-*`, `UI-VIS-*`, `UI-QUAL-*`  
> Dependency: `EXEC-1062 DONE`  
> Scope type: presentation / information architecture / interaction architecture

## 1. Objective

把当前已经实现但层级过度 domain-object-driven 的 UI：

```text
Today / Goals / Path / Library / Evidence / History / Settings
```

重构为：

```text
L0 Product Domains: Today / Learning / Library
Learning L1: Goals / Plan / Progress / History
App Utility: Settings / Recovery
```

同时完成 Today single-primary-task、Library progressive disclosure、Settings hierarchical navigation、legacy route migration 与 legacy chat-first component retirement。

本 Slice 不改变任何 SYS01～SYS08 owner、API domain semantics、Teaching Policy、LearningPlan、LearnerState、ReviewSchedule 或 data/security truth。

## 2. Dependency Gate

MUST 满足：

- `ADR-0014` accepted；
- `UI-IES/UI-IA/UI-SCREEN/UI-VIS/UI-QUAL` 当前版本 FROZEN；
- `EXEC-1062` 已归档 DONE，P1-06 `/welcome` / default route / Settings reopen / deep-link contract 有最终实现证据；
- 当前 main 的 frontend tests/build baseline 已记录；
- 无其他 active EXEC 同时修改本 Slice Allowed Files，或已显式拆分 non-overlap scope。

未满足时状态：`BLOCKED_BY_DEPENDENCY_GATE`。

`EXEC-042` backend policy closure 可独立执行，但 UI-03 不得借此修改 policy semantics。

## 3. User Jobs

UI-03 必须优化而不改变以下 jobs：

1. 打开 Askora 立即知道下一项学习任务；
2. 理解为什么现在学习它；
3. 开始/继续 canonical LearningActivity；
4. 查看/管理长期 Goal；
5. 查看 Plan、Progress、History；
6. 查找/导入/管理资料；
7. 在需要时进入 Settings/Recovery，而不是让 utility 抢占学习导航。

## 4. In Scope

### 4.1 Global Shell

- Sidebar / responsive navigation 收敛为 Today/Learning/Library；
- Settings/Recovery 移到 utility group / platform-equivalent command；
- Product Domain 与 Utility 的视觉层级分离。

### 4.2 Learning Domain

- 新 `/learning` route / local shell；
- Goals/Plan/Progress/History L1 navigation；
- 复用现有 pages/data/actions；
- 新 canonical route 与旧 route redirects。

### 4.3 Today

- canonical current/next activity 为 sole Primary Task；
- goal/reason/validation 为 supporting information；
- review/upcoming 为 secondary；
- Quick Start 只在无 canonical activity 时 fallback，或进入 secondary/overflow。

### 4.4 Library

- 默认保留 search/filter/import/document list/selected context；
- batch controls 只在 selection 后出现；
- duplicate/OCR/metadata/reinspection/destructive actions contextualize；
- 保留全部 P1-04 owner command/error/idempotency semantics。

### 4.5 Settings

- landing 变为 category navigation；
- model/data/account/recovery/destructive flows 进入对应 secondary destination；
- 不复制现有 business/security logic；
- normal runtime status 降低视觉权重，action-required 才提升。

### 4.6 Legacy Cleanup

- 证明 `Chat.jsx` 无 canonical route/import 后删除；
- 清理只服务旧 7-item IA 的 dead CSS/components；
- 不删除 compatibility `TutorWorkspace` / `/quick/:sessionId`，除非另有退休合同。

## 5. Out of Scope

- TeachingAction / teaching strategy changes；
- Plan manual reorder/edit；
- LearnerState direct edit/retest flow；
- new persistent notes；
- new global search backend；
- new telemetry；
- new database schema；
- P1-02/03/05/07 business/security rewrite；
- Focus mode 新能力；
- iOS/native implementation 本身（只验证 semantic portability）。

## 6. Route Contract

Canonical：

```text
/today
/learning
/learning/goals
/learning/goals/new
/learning/goals/drafts/:draftId
/learning/goals/:goalId
/learning/goals/:goalId/edit
/learning/plan
/learning/progress
/learning/history
/library
/settings...
/learn/:activityId
/quick/:sessionId
/welcome
```

Legacy redirects：

```text
/goals/**  → /learning/goals/**
/path      → /learning/plan
/evidence  → /learning/progress
/profile   → /learning/progress
/history   → /learning/history
```

所有 redirect 无业务副作用。

## 7. Semantic Element Gate

实现新增/修改的核心交互必须可归入：

```text
Navigation
Action
Control
Selection
Disclosure
InteractiveContent
StatusFeedback
```

不得新增 `Entry/Card/Button` 作为并列 semantic category。

普通 Goal/Document/Activity/History collection 默认 row/list。

## 8. Acceptance Criteria

- `UI03-AC-001`：L0 Product Domain 只有 Today/Learning/Library；
- `UI03-AC-002`：Settings/Recovery 与 L0 Product Navigation 明确分组；
- `UI03-AC-003`：Learning 四 facets 可通过 keyboard/pointer/touch 完成导航，且切换无 business write；
- `UI03-AC-004`：旧 Goals/Path/Evidence/History deep links 无副作用 redirect 到新 route；
- `UI03-AC-005`：Goal create/edit/lifecycle 在新 route 保持现有 owner/version/idempotency semantics；
- `UI03-AC-006`：Today canonical activity 可执行时只有一个 Primary Task；
- `UI03-AC-007`：Quick Start 不与 canonical activity 同层竞争；
- `UI03-AC-008`：Library 无 selection 时不显示永久 batch management panel；
- `UI03-AC-009`：Library contextual actions 保留 P1-04 功能和安全语义；
- `UI03-AC-010`：Settings landing 是 category navigation，高风险/复杂 flow 分层但功能无回归；
- `UI03-AC-011`：P1-02 model credential、P1-03 erasure/recovery、P1-05 account、P1-07 recovery security gates 无回归；
- `UI03-AC-012`：legacy `Chat.jsx` 仅在证明无使用者后删除，`TutorWorkspace` compatibility 保留；
- `UI03-AC-013`：1440×900、1024×768、768×1024、360×800、200% zoom、keyboard primary paths PASS；
- `UI03-AC-014`：contextual action 非 hover-only，touch/keyboard 有等价入口；
- `UI03-AC-015`：frontend unit/integration/E2E/build/audit/docs/diff gates PASS；
- `UI03-AC-016`：Engineering / Contract / Accessibility-Security Gate 与 Learning Evidence 分开报告。

## 9. Required Tests

至少新增/更新：

- route resolver / redirect tests；
- Sidebar/global nav tests；
- Learning facet shell tests；
- Today hierarchy tests；
- Goal new-route behavior tests；
- Library selection/contextual action tests；
- Settings category/secondary route tests；
- legacy Chat import/route absence test or static proof；
- keyboard/focus/accessibility assertions；
- narrow-screen E2E。

默认命令：

```bash
cd apps/frontend
npm test -- --run
npm run build
npm audit --audit-level=high

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

若修改 backend，必须执行对应 backend full/targeted gates；本 Slice 默认不需要 backend schema/API change。

## 10. Migration / Rollback

迁移采用 presentation-only forward migration：

1. 新 route + redirect；
2. 3-domain navigation；
3. Learning local shell；
4. move existing page components；
5. Today hierarchy；
6. Library contextualization；
7. Settings hierarchy；
8. legacy cleanup；
9. full gates。

不得产生数据库 migration。

若出现阻断性 presentation regression，可 forward-fix shell/route rendering；不得恢复 chat-first default 或建立第二 truth。

## 11. Completion Claim

UI-03 DONE 只允许声明：

```text
UI Engineering Gate: PASS
UI Contract Correctness Gate: PASS
Accessibility / Security Gate: PASS
Learning Evidence Gate: unchanged
```

禁止把点击减少、UI 更简洁、视觉更 Apple-like 或 engagement 变化解释为学习效果证明。

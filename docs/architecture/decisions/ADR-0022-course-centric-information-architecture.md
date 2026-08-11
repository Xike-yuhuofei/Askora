# ADR-0022 — Course-centric Information Architecture

Status: accepted
Date: 2026-08-11
Decision owners: user-authorized Askora product governance
Decision authority: user-delegated Codex；用户明确要求执行 Course-centric IA 正式变更并授权选择最佳安全执行方式
Upper authority:

- `docs/product/PRODUCT-POSITIONING.md`
- `docs/product/PRODUCT-DEFINITION.md`

Product trace: `CAP-01`、`CAP-04`、`CAP-07`、`PD-REQ-0401`、`PD-REQ-0701..0703`、`PD-RULE-002`、`PD-RULE-009`
Current design input: `docs/design/features/course-centric-information-architecture-canonical-design-delta.md`
Affected specs: current Experience Design、`docs/specs/ui/**`；后续 technical delta 需扩展 Workspace/Activity query-command contract
Supersedes (partial): ADR-0014、ADR-0018、ADR-0106；amends ADR-0019 的 `SINGLE_WORKSPACE` presentation assumption，但不自行定义新 API/schema

## Context

ADR-0014 将 Askora 的 L0 收敛为 `Today / Learning / Library`；ADR-0018 保留该 L0，并把 Workspace 加入三栏共享上下文；ADR-0019 为当前单一 default Workspace 冻结只读 projection，明确未来多 Workspace switch 需要独立 command contract。

新的正式 Experience 决策要求：

- 移除 Today / Learning 一级入口；
- 以用户可理解的“课程”表达 canonical Workspace；
- 课程列表与 `＋ 新课程` 成为 Left / Where 的主线；
- 一个 Course 包含多个 LearningActivity；
- Library 与 Utilities 保持原职责；
- Learning Workspace 保持 `Where / Learn / Reference & Notes`；
- Conversation 继续只是 LearningActivity 的交互形式。

这不改变 Product Capability 或 Workspace domain identity，但会改变长期 IA、route migration 与多 Workspace 暴露方式，因此需要新 ADR 记录 supersession 与 implementation gate。

## Decision

### 1. Course is the user-facing Workspace vocabulary

正常用户界面统一使用“课程”。Canonical product/domain/API/persistence 继续使用 `Workspace`，`course_id` 不成为第二 identity；user-facing route 中的 `:workspaceId` 仍引用同一 canonical Workspace。

`LearningProject` 保持 Workspace 内的可选组织对象，不与 Course 同义，不因本 ADR 被删除或提升为一级导航。

### 2. Course-centric L0

Left / Where 冻结为：

```text
＋ 新课程                  Action
课程列表 / 当前课程          Navigation / InteractiveContent
资料库                     Stable Product Domain Navigation
Settings / Recovery        Utility Navigation
```

Today / Learning 不再是 stable Product Domain、L0 Navigation 或默认 mental entry。不得创建替代 Today 的 Dashboard。

### 3. Course is the long-term navigation context

Course switch 必须落到 canonical Workspace scope，并同时影响 Activity、Session、Material、Retrieval、Notes、Current Material、Goal/Plan/LearnerState/Review projections 与 History/resumable context。

Route、selected style、React state 或 localStorage 不得冒充成功切换。Selection 与 switch Action 分离；冲突恢复由 owner command 决定。

### 4. Activity is the unit below Course

体验层级为：

```text
Course / Workspace
→ LearningActivity
→ LearningSession
→ Conversation / Attempt / Feedback / Events
```

每个 Course 提供 Activity Switcher / Recent Learning。Activity 使用学习目的标题；禁止用 Chat 1/2/3 建立 thread-manager 心智模型。

### 5. Startup and route migration

`/` 按 canonical read state side-effect-free 解析：

- 最近 Course 有 resumable Activity → 恢复该 Course/Activity；
- 有 Course、无 resumable Activity → 最近 Course orientation / Activity Switcher；
- 无 Course → Course Empty State，Primary Action 为“新课程”。

Canonical user-facing route family 为：

```text
/courses/new
/courses/:workspaceId
/courses/:workspaceId/activities/:activityId
```

`/today`、`/learning`、`/workspaces/:workspaceId/**`、`/learn/:activityId`、`/quick/:sessionId` 在 retirement evidence 具备前保留兼容。Redirect/navigation 不得创建 Course、Activity、Session、Evidence，不得修改 Workspace truth，也不得清空未提交工作。

### 6. Course creation is a real flow

`＋ 新课程` 启动：

```text
创建课程
→ 添加/选择资料（适用时）
→ 明确目标
→ 建立首个可执行 Activity
→ Course-scoped Learning Workspace
```

进入 route 不产生业务写入。每一步必须由真实 owner command/readiness 支持；不得暴露 placeholder、fake success 或 frontend-only Workspace。

### 7. Three-column Learning Workspace remains

ADR-0018 的 `Left / Where | Center / Learn | Right / Reference & Notes`、Learning Context Drawer、Right Rail、Learning de-management、Library no-OCR consequence 保持。

其解释从：

```text
Learning Product Domain → Workspace
```

调整为：

```text
Course Context → Learning Workspace
```

### 8. Technical implementation gate

本 ADR 冻结 Experience/IA，不自行修改 API/schema。ADR-0019 的 current read-only default Workspace query 可以继续作为 compatibility projection，但 `SINGLE_WORKSPACE` 不再是目标 Experience 的充分合同。

在实现 Course create/list/current/switch 与 Activity Switcher 前，必须先冻结：

- Platform Workspace Registry 的 list/create/current/switch command/query；
- `current_workspace_id` 的 canonical preference/selection owner；
- draft/stream/note/session/material-position switch conflict/recovery；
- Course-scoped recent/resumable Activity projection；
- idempotency、version conflict、error、security 与 cross-Workspace fail-closed。

在该 technical delta accepted 前，相应 frontend implementation 为 `BLOCKED_BY_SPEC_GAP`。

## Alternatives Considered

### A. Keep Today/Learning and add a Course selector

Rejected。它保留旧入口模型，并容易让 Workspace 退化为视觉 selector，而不是长期学习主上下文。

### B. Rename Workspace to Course across domain/API/database

Rejected。本次只需要 user vocabulary 与 IA；全栈重命名会引入不必要的 schema/API/migration 风险并改变 Product Definition 层职责。

### C. Treat LearningProject as Course

Rejected。ADR-0016 已冻结 Workspace 是真实隔离与长期 scope，LearningProject 只是其内组织 aggregate。映射到 Project 会留下第二长期上下文并破坏 scope clarity。

### D. Use Conversation threads below Course

Rejected。它违反 Conversation 非产品一级对象与 LearningActivity primary-unit 规则，并使 Askora 向通用 AI Chat 漂移。

## Consequences

### Positive

- 用户心智与真实长期 Workspace scope 对齐；
- 多课程、多 Activity 的恢复路径清晰；
- Learning Workspace 核心学习职责不再依赖抽象 L0“学习”；
- Library、Notes、Material、History 继续服从同一 scope；
- Conversation 不会借 IA 变更升级为 thread manager。

### Cost / Risk

- 现有 Sidebar、Today、Learning landing、Welcome 与 route tests 需要迁移；
- ADR-0019、API/frontend read-model contracts 必须通过后续技术 ADR/Spec Delta 扩展；
- Course 与 LearningProject 的术语必须持续区分；
- redirect/deep link 与 switch conflict 需要严格无副作用和恢复测试。

## Ownership / Truth / Security

- Workspace writer 保持 Platform Workspace Registry；
- LearningActivity/Plan 保持 SYS06；
- LearningSession 保持 Platform Learning Session Registry；
- Transcript/Message 保持 SYS08；
- Material/Notes/Goal/LearnerState/Review owner 不变；
- 不建立 Course table、Course DTO 或第二 `current_workspace_id` truth；
- cross-Workspace refs fail closed，不泄露外部 Workspace metadata；
- route/deep-link refresh/retry 幂等且无业务副作用；
- Product/UX/Engineering/Policy/Learning Evidence 继续分层声明。

## Migration / Rollback

顺序：

```text
Design Delta + ADR-0022
→ current Experience consolidation
→ current UI Spec migration
→ Workspace/Activity technical command-query ADR/Spec
→ frontend course-centric shell and flow
→ legacy route compatibility
→ regression/accessibility acceptance
→ retirement evidence
```

Rollback/forward-fix：在实现期可临时保留 legacy routes/presentation compatibility，但不得恢复 Today/Learning 为 canonical L0、不得建立双 Workspace truth、不得用 mock Course 代替真实 owner contract。

## Validation

至少验证：

- L0 不再显示 Today / Learning；
- `＋ 新课程` 是 Action；
- user-facing Workspace 文案为“课程”；
- Course switch 改变真实 scope 并处理冲突恢复；
- Course 下多个 Activity 可按学习语义恢复/切换；
- Conversation 不成为 L0/thread manager；
- `/`、`/today`、`/learning`、deep links 无业务副作用；
- Course Empty State 与 create flow 无 placeholder/fake success；
- Library 与 Utilities 职责不变；
- three-column Learning Workspace、Drawer、Right Rail 不回归；
- keyboard/touch/focus/360px/200% zoom 与 cross-Workspace fail-closed 可验证。

## Supersedes / Superseded By

本 ADR：

- **partially supersedes ADR-0014**：§2 三 L0、§5 Today primary destination 与对应 route mental model；7 primitives、progressive disclosure、Chat non-L0、Settings hierarchy 继续有效；
- **partially supersedes ADR-0018**：§1 Left rail 的 Today/Learning/Library navigation list 与 `Learning Domain → Workspace` 解释；三栏职责、shared canonical Workspace、Drawer、Right Rail、de-management、Library no-OCR 继续有效；
- **amends ADR-0019**：`SINGLE_WORKSPACE` 仍描述 current implementation compatibility，但不再是目标 Experience；新 command/query 由独立 technical ADR/Spec 冻结；
- **partially supersedes ADR-0106**：`/today` 不再是 default entry；fact-driven onboarding、presentation preference、explicit deep-link preservation 与 owner boundaries 继续有效。

Superseded by: none.

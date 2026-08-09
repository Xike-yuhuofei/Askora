# Askora UI Quality and Migration Specification

> Spec ID：`UI-QUAL-*`、`UI-MIG-*`
> 状态：`FROZEN`
> 依赖：`TEST-*`、`SEC-*`、`DOD-*`、`UI-IA-*`、`UI-SCREEN-*`、`UI-DATA-*`、`UI-VIS-*`

## 1. 实施前置条件

### UI-MIG-001 — Spec Approval Gate

本 Spec Set 已于 2026-08-08 获用户明确批准并冻结。实施必须：

- 仅通过对应 frozen Vertical Slice 与 active EXEC 修改代码；
- UI-01 达到 DONE 后才能创建/执行 UI-02；
- 不修改未被本 Spec Set 授权的 domain/command contract；
- 只有真实完成并通过门禁的路由或 Query 才能描述成已实现。

### UI-MIG-002 — Current Worktree Preservation

当前工作区存在大量未提交修改。后续 EXEC MUST 先记录 scope、`git status` 和相关文件 diff；不得覆盖、重置、格式化或顺手提交与 UI Slice 无关的用户修改。

### UI-MIG-003 — Login Runtime Blocker

`Login.jsx` 当前引用未导入的 `User` icon，导致登录页运行时白屏。UI-01 的第一项实现任务必须修复该 blocker，并增加登录页 smoke/render test。修复只证明页面恢复，不证明新 UI 已完成。

### UI-MIG-004 — Baseline Capture

每个 UI Slice 实施前必须记录：

- candidate commit / worktree 状态；
- frontend `npm test -- --run` 与 `npm run build` 基线；
- 相关 backend targeted tests；
- 现有路由、页面截图或 DOM evidence；
- 当前 API response fixture；
- 与本 Slice 无关的既有失败。

## 2. 推荐 Vertical Slice 顺序

下列内容只定义冻结后的推荐拆分，不是 active EXEC。

### UI-MIG-010 — UI-01 Learning Shell and Tutor Workspace

范围：

- 登录 blocker 与 auth shell；
- design tokens、global shell、navigation、route compatibility；
- `/today` 学习驾驶舱；
- `/learn/:activityId` canonical route guard 与不可启动诚实状态；
- `/quick/:sessionId` 兼容导师工作台，显著标记 legacy source；
- `/history` 与现有 dialog history；
- `/settings` 合并原 account；
- `/workspace/today` 只读 Query；
- 复用 RichMessage、dialog normal/history/SSE final；
- 现有 `/users/profile` canonical mastery source 不回归。

退出条件：UI-01 所需接口、页面、状态、route migration、360px/desktop、keyboard、build/test 全部通过；兼容快速学习入口有清晰标识和 retirement condition；未绑定 session 的 canonical activity 保持不可启动而非走 legacy shortcut。

### UI-MIG-011 — UI-02 Library, Knowledge Map and Evidence Profile

范围：

- `/library` 文档列表、上传与处理状态；
- KnowledgeUnit/relation map 与 SourceSpan detail；
- `/evidence` canonical evidence profile；
- `/goals`、`/path` 只读视图；
- `/workspace/goals`、`/workspace/path`、`/workspace/knowledge-map`、`/workspace/evidence` Queries；
- legacy profile 主视觉退役。

退出条件：document/KnowledgeUnit/source distinctions、map scope、canonical evidence/uncertainty/legacy labels、auth ownership 和 empty/partial/stale paths 全部验证。

### UI-MIG-014 — Approved UI-02 Split

用户于 2026-08-08 采纳 Canonical 资料库 MVP，并批准把 `UI-MIG-011` umbrella 串行拆分：

```text
UI-02A: /library + durable document processing + scoped knowledge map + SourceSpan Inspector
→ UI-02A DONE
→ UI-02B: /goals + /path + /evidence and remaining workspace queries
```

该拆分不改变 UI-MIG-011 最终总范围；UI-02A 不得以 deferred Goals/Path/Evidence 数据伪造 UI-02 umbrella DONE。

### UI-MIG-015 — Approved UI-02B1 Launch Slice

用户于 2026-08-08 授权在 UI-02A 与完整 UI-02B 之间增加独立 bounded Slice：

```text
UI-02A DONE
→ UI-02B1: single-document material-to-learning launch
→ UI-02B1 DONE
→ UI-02B: /goals + /path + /evidence
```

UI-02B1 只复用 Book-to-Learning façade 闭合 Goal/diagnostic/plan/teaching launch，不改变 UI-MIG-011 的完整 UI-02B 范围，也不冻结 durable activity/session link。

### UI-MIG-012 — UI-03 Focus and Adaptive Presentation Polish

范围：

- `/focus/:activityId` 同 activity identity 的专注模式；
- assistance/validation/citation 在 Focus 下保持可访问；
- dark theme；
- 360/768/1024/1440 响应式验收；
- reduced motion、zoom、contrast、keyboard 全量验收；
- 性能与 bundle 回归。

退出条件：Focus 不形成第二业务链；light/dark/responsive/accessibility gates 全部通过。

### UI-MIG-013 — Strict Serial Execution

UI-01 未满足全部 Acceptance Criteria 时不得进入 UI-02；UI-02 未满足时不得进入 UI-03。每个 Slice 必须有独立 EXEC 和独立本地 commit；未经用户明确要求不得 push。

## 3. Legacy Route and Component Migration

### UI-MIG-020 — Route Mapping

| Current | Target | Migration |
|---|---|---|
| `/` Chat | `/today` | `/` redirect；chat 迁入 `/learn/:activityId` 或兼容 quick start |
| `/knowledge` placeholder | `/library` | redirect；复用 document API，新增 knowledge query |
| `/profile` | `/evidence` | redirect；canonical fields first，legacy collapsed |
| `/account` | `/settings` | redirect；保留 auth/runtime事实 |

### UI-MIG-021 — Sidebar

现有 Sidebar MAY 渐进改造为 AppShell navigation，但不得长期保留两套全局导航。新 Shell 覆盖所有 target pages 后，旧 nav items 和 CSS 必须删除或明确 compatibility retirement。

### UI-MIG-022 — RichMessage

`RichMessage`、`SafeMarkdown`、KaTeX、typed cards/citations MUST 复用；不得为新工作台创建第二富文本协议或 duplicate renderer。

### UI-MIG-023 — Profile

当前 Profile 的四张 process/legacy stats card、subject mastery bar 和 metacognition ring MUST 从主证据页面移除或降级到明确 compatibility 区。迁移不能修改 `/users/profile` 的 canonical query boundary，也不能通过前端 threshold 替代。

### UI-MIG-024 — Subject Picker

当前硬编码 subject/knowledge point picker MAY 暂作兼容 quick start。它必须从主首页降级，并在 canonical goal/activity start command 后退休；不得扩展为第二 planner。

## 4. Test Strategy

### UI-QUAL-001 — Spec Traceability

新增关键测试必须引用对应 `UI-*-AC-*` 或已冻结上游 Spec ID。不得仅通过 snapshot 证明业务语义。

### UI-QUAL-002 — Frontend Unit / Component

至少覆盖：

- route mapping 与 protected routes；
- loading/empty/ready/partial/stale/error/unauthorized；
- canonical vs legacy evidence；
- missing/null/confidence；
- planned vs actual assistance；
- ReviewDue candidate vs planned review activity；
- RichMessage fallback/security；
- focus mode same identity；
- auth/development auto-login boundaries；
- keyboard/focus/accessible labels。

### UI-QUAL-003 — API Contract

新 workspace endpoint 必须有 strict response schema、unknown major、auth ownership、partial source、stable ordering、stable error、timezone-aware datetime 与 source/version trace tests。

### UI-QUAL-004 — Architecture

必须验证：

- API handler 无 planner/mastery/review/policy algorithm；
- query assembler 无业务 write；
- frontend 无 mastery threshold、next_due calculation 或 hint/exposure expansion；
- workspace response 不形成第二 canonical truth；
- legacy chat仍走 canonical facade。

### UI-QUAL-005 — Integration

使用真实 SQLite 和本地后端 fixture 验证：

- today owner refs 聚合；
- partial/stale source；
- document→knowledge map query；
- `/users/profile` canonical evidence；
- dialog normal/history/SSE final payload equivalence；
- auth ownership；
- route deep link/reload。

### UI-QUAL-006 — End-to-End

每个 Slice 至少有一个用户路径：

```text
UI-01: 登录 → 今天 → 兼容快速学习/恢复已有 session → 工作台消息 → history/reload
UI-02: 资料库 → 文档状态 → 知识节点 → 学习证据
UI-03: 工作台 → Focus → 获取允许帮助 → 返回同一 activity
```

E2E SHOULD 使用 deterministic fixture；UI 改造不需要每次调用真实模型。若报告“真实模型交互可用”，仍必须单独完成现有真实模型 gate，且不能把它称为学习效果。

### UI-QUAL-007 — Responsive / Visual

至少验证 1440×900、1024×768、768×1024、360×800；light/dark；100%/200% zoom；中文长标题；空数据、最大合理列表、长公式、长引用与 stable error。不得只验 happy-path desktop screenshot。

### UI-QUAL-008 — Accessibility

至少执行：

- semantic/accessible-name assertions；
- keyboard-only primary path；
- focus order 与 focus return；
- contrast；
- reduced motion；
- screen-reader live error/status；
- drawer/sheet focus containment 与 Escape close。

### UI-QUAL-009 — Security

继续覆盖 raw HTML、unsafe URL、remote image、citation trace、prompt injection、grader-only leakage、unauthorized document/evidence、secret/log leakage。UI 错误详情不得暴露 stack trace、内部路径或敏感规则。

## 5. Engineering Commands

各 EXEC 按范围至少运行：

```bash
cd apps/frontend
npm test -- --run
npm run build
npm audit --audit-level=high
```

涉及 backend Query/API 时：

```bash
cd apps/backend
uv run pytest <targeted query/api/architecture/security tests>
uv run pytest
uv run ruff check app tests
uv run mypy app --no-error-summary
uv run alembic check
```

提交前：

```bash
git diff --check
python3 .github/workflows/check_docs.py
```

若全量命令因既有问题失败，必须区分本次新增失败与预存失败；不得删除测试、弱化断言、扩大 ignore 或越界格式化。

## 6. Performance Budgets

### UI-QUAL-020

正式 Vertical Slice 应在 EXEC 中冻结具体基线与预算。本 Spec 建议至少记录：

- frontend production bundle total 与 route chunk；
- first usable shell render；
- long history render；
- knowledge map node/edge cap；
- RichMessage KaTeX/Markdown lazy-load；
- memory growth across route/focus switching。

具体数值不得在无当前 measurement 的情况下写成硬门槛。EXEC 必须先测 baseline，再冻结不回归或明确预算。

### UI-QUAL-021

知识地图必须限定 scope、节点和边数量；长 history SHOULD 分页/虚拟化评估。不得为视觉效果一次性加载全部私人文档、消息或 evidence history。

## 7. Release and Claim Boundaries

### UI-QUAL-030

UI Slice 的完成只能声明：

```text
UI Engineering Gate
UI Contract Correctness Gate
Accessibility / Security Gate
```

UI 可用、视觉改善、会话完成或活跃度变化不得改写 `Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT`。

### UI-QUAL-031

任何以下情况阻断 Slice DONE：

- 页面依赖假数据或占位数据完成主路径；
- 新 Query 无 owner/source/version；
- Profile 继续默认展示 legacy mastery；
- Focus 形成第二执行链；
- 360px/keyboard/auth/error path 未验证；
- Login runtime blocker 仍存在；
- unknown/partial/stale 被伪装 READY；
- 未声明公共 API/schema 变化。

## 8. SPEC GAP / Deferred Register

### UI-MIG-030 — No Blocking Gap for UI-01 Bounded Scope

UI-01 使用显式 compatibility workspace，避免把 session 伪装为 LearningActivity，因此当前 bounded scope 无 blocking gap。以下事项被明确延后，不能在 UI-01～03 中猜测实现：

| Item | Status | Reason / Required next decision |
|---|---|---|
| LearningGoal create/confirm commands | DEFERRED | 需独立 command/API/idempotency/version contract |
| Plan edit/reorder/replan controls | DEFERRED | 需 SYS06 command 与 conflict contract |
| Canonical activity launch command | DEFERRED | 需定义 activity/session/run identity 和 canonical facade mapping |
| Learner-state dispute/retest command | DEFERRED | 需 SYS03/SYS04 workflow contract |
| Persistent notes | DEFERRED | 尚无 owner、schema、retention/privacy contract |
| Stable mastery product labels | DEFERRED | 必须由 versioned SYS03 rule 产生，不由 UI 定义 |

若后续实施发现必须依赖其中任一项完成当前 Acceptance Criteria，应标记 `BLOCKED_BY_SPEC_GAP`，不得以 frontend-only state 或 legacy shortcut 绕过。

## 9. Acceptance Criteria

- `UI-MIG-AC-001`：产品代码修改全部受 frozen Vertical Slice 与 active EXEC 约束。
- `UI-MIG-AC-002`：UI-01→UI-02→UI-03 严格串行，每项独立 EXEC/commit。
- `UI-MIG-AC-003`：旧路由和兼容入口有明确 mapping、source label 与 retirement condition。
- `UI-MIG-AC-004`：当前未提交用户修改不被覆盖或混入 Slice commit。
- `UI-QUAL-AC-001`：frontend tests/build/audit 与适用 backend tests/lint/type/migration/docs gates 有真实结果。
- `UI-QUAL-AC-002`：component/contract/integration/E2E/accessibility/security 测试覆盖对应关键行为。
- `UI-QUAL-AC-003`：1440/1024/768/360、light/dark、200% zoom、keyboard 通过验收。
- `UI-QUAL-AC-004`：UI Engineering/Contract/Accessibility gates 与 Learning Evidence Gate 分开报告。
- `UI-QUAL-AC-005`：Deferred items 未被 frontend-only state 或 legacy shortcut 隐式实现。

## 10. Forbidden Completion Claims

禁止把以下情况称为 UI DONE：

- 只有静态 mockup；
- 只有 CSS 重构，没有真实 Query/route/action；
- build 通过但页面运行时白屏；
- 仅 mock API 而声称端到端可用；
- 桌面截图正常但窄屏、键盘、错误、空态未验；
- Profile 看起来更漂亮但仍误导 mastery；
- RichMessage 或 Focus 绕过已有安全与 canonical execution；
- UI 指标改善被描述为人类学习效果改善。

## 11. P1-06 Migration and Quality Gate

### UI-MIG-040

P1-06 在 UI-02C DONE 后，通过 EXEC-1061→1062 串行实施。P1-02/P1-03/P1-07 未形成真实 owner
capability/action 前不得以 placeholder/disabled button 关闭集成 gate；shared dirty worktree 继续按
UI-MIG-002 保护。

### UI-QUAL-040

除现有 frontend/build/audit/backend/docs gates 外，必须验证 default route/deep-link/reload/relogin/App
restart、dismiss/reopen、owner-fact rollback、P1-07 action、360/768/1024/1440、200% zoom、keyboard/
focus/live region、deterministic/real-provider E2E 与首次用户体验。

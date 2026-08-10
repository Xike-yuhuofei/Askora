# Askora UI Quality and Migration Specification

> Spec ID：`UI-QUAL-*`、`UI-MIG-*`
> 状态：`FROZEN`
> Governing：`ADR-0014`、`UI-IES-*`、`UI-IA-*`、`UI-SCREEN-*`、`UI-DATA-*`、`UI-VIS-*`、`TEST-*`、`SEC-*`、`DOD-*`

## 1. Current Baseline

### UI-MIG-001 — Implemented UI Baseline

以下历史 UI/product slices 已实现并作为迁移起点，而不是新的设计权威：

- UI-01 Learning Shell / Compatibility Tutor Workspace；
- UI-02A Library / Knowledge Map；
- UI-02B1/2/3 Material-to-Learning / Guided / Real-model；
- UI-02B Goals / Path / Evidence；
- UI-02C Canonical Activity Lifecycle；
- P1-01 Goal Management；
- P1-02 Model Settings；
- P1-03 Data Control / Recovery；
- P1-04 Library Management；
- P1-05 Account Lifecycle；
- P1-07 Recovery Center。

本次 ADR-0014 只重构 IA / interaction / presentation，不改变上述 owner/domain truth。

### UI-MIG-002 — Active Work Preservation

当前 active EXEC 包含：

- `EXEC-042`：v0.3 Teaching Policy production closure；
- `EXEC-1062`：P1-06B Onboarding Product Closure。

新的 Interaction Architecture frontend refactor MUST NOT 与 `EXEC-1062` 并行执行，因为二者共享：

- `apps/frontend/src/App.jsx`；
- Settings；
- route tests；
- `docs/specs/ui/information-architecture.md`；
- `docs/specs/ui/screen-contracts.md`。

因此新 UI refactor 的 implementation dependency 固定为：

```text
EXEC-1062 DONE
→ Interactive Element System Refactor EXEC
```

`EXEC-042` 属于独立 backend/policy task，可在不扩大文件范围时并行。

### UI-MIG-003 — Spec Approval Gate

产品代码修改必须：

```text
ADR-0014 accepted
→ UI-IES/UI-IA/UI-SCREEN/UI-VIS/UI-QUAL frozen
→ Interaction Architecture Vertical Slice frozen
→ dedicated EXEC dependency gate satisfied
→ Code/Test
```

不得直接依据 Design Delta 修改 React。

### UI-MIG-004 — Worktree Preservation

执行代理开始前必须记录 `git status`、相关 diff 与 base commit；不得 reset、format、覆盖或顺手提交 scope 外用户修改。

## 2. Interaction Architecture Migration Scope

### UI-MIG-010 — L0 Navigation Migration

Current：

```text
今天 / 学习目标 / 学习路径 / 资料库 / 学习证据 / 历史记录 / 设置
```

Target：

```text
Product Domains: 今天 / 学习 / 资料库
App Utility: Settings / Recovery / Search（存在时）
```

不得长期保留两套全局导航。

### UI-MIG-011 — Learning Facet Migration

Goals/Path/Evidence/History 页面现有业务组件 MAY 复用，但必须迁入：

```text
/learning/goals
/learning/plan
/learning/progress
/learning/history
```

实现 SHOULD 优先复用现有 query/action component，而不是重写第二套 domain presentation logic。

### UI-MIG-012 — Legacy Route Mapping

| Current | Target | Migration |
|---|---|---|
| `/` | `/today` | 受 onboarding contract 约束的 redirect |
| `/goals` | `/learning/goals` | no-side-effect redirect |
| `/goals/**` | `/learning/goals/**` | preserve params/draft/edit semantics |
| `/path` | `/learning/plan` | preserve goal scope query when applicable |
| `/evidence` | `/learning/progress` | no-side-effect redirect |
| `/profile` | `/learning/progress` | legacy redirect |
| `/history` | `/learning/history` | no-side-effect redirect |
| `/knowledge` | `/library` | legacy redirect |
| `/account` | `/settings` | utility redirect |

Route redirect 不得创建 Goal/Activity/Session 或修改 focused state。

### UI-MIG-013 — Today Migration

保留现有 Today canonical read model 和 activity lifecycle action；只改变 interaction hierarchy：

1. canonical current/next activity → sole Primary Task；
2. reason/goal/validation → supporting information；
3. upcoming/review → secondary region；
4. compatibility quick start → fallback/overflow。

不得通过修改 Query 伪造新的 recommendation data。

### UI-MIG-014 — Library Migration

保留 P1-04A/B/C owner command 与 data contract。

迁移只改变 action exposure：

- Search/filter/import 常驻；
- multi-select 后出现 batch toolbar；
- OCR/duplicate/metadata/reinspection 进入 selected document context/Inspector/Menu；
- destructive actions 保留原 confirmation/error/idempotency contract。

### UI-MIG-015 — Settings Migration

保留 P1-02/P1-03/P1-05/P1-07 所有安全和 owner command contract。

Settings 从 giant control grid 拆为 category navigation + secondary destinations。拆分过程中 MUST NOT：

- 复制 model/data/recovery logic；
- 改变 secret lifetime；
- 弱化 destructive confirmation；
- 重新实现第二套 erasure/recovery truth。

### UI-MIG-016 — Legacy Chat Component

若 `apps/frontend/src/pages/Chat.jsx` 在 canonical route graph 中已无入口且没有测试/兼容 import 依赖，应在 dedicated refactor 中删除；不得保留第二套 chat-first product entry。

删除前必须通过 static import/search + route tests 证明无使用者。

## 3. Test Strategy

### UI-QUAL-001 — Spec Traceability

新增关键测试必须引用对应 `UI-IES-*`、`UI-IA-*`、`UI-SCREEN-*` 或上游 Spec ID。不得仅通过 snapshot 证明业务语义。

### UI-QUAL-002 — Frontend Unit / Component

至少覆盖：

- L0 只有 Today/Learning/Library；
- utility 与 Product Navigation 分组；
- `/learning/*` local facets；
- legacy route redirect 无 command side effect；
- Today single Primary Task；
- Quick Start fallback/secondary；
- Goal action 保留现有 owner command；
- plan/evidence/history semantics 不回归；
- Library selection → contextual batch actions；
- Settings category navigation；
- RichMessage fallback/security；
- loading/empty/ready/partial/stale/error/unauthorized；
- keyboard/focus/accessible labels。

### UI-QUAL-003 — API / Data Contract

本次 IA refactor SHOULD 不新增 domain API。

若确实需要新的 presentation-only query，必须有 strict response schema、auth ownership、stable error、source/version trace tests，并证明不会形成第二 canonical truth。

### UI-QUAL-004 — Architecture

必须验证：

- Navigation/facet switch 无业务 write；
- frontend 无 mastery threshold、next_due calculation 或 hint/exposure expansion；
- new Learning shell 不复制 Goal/Plan/Evidence owners；
- Quick Start 仍走 canonical compatibility facade；
- Settings relocation 不复制 model/data/recovery state；
- UI semantic primitives 不被 component variant 反向决定。

### UI-QUAL-005 — Integration

使用真实 SQLite / local backend fixture 验证：

- today owner refs 聚合保持；
- activity start/resume 仍进入 canonical lifecycle；
- Goal create/edit/lifecycle 在新 route 可用；
- Plan/Progress/History 在新 route 使用原 read models；
- document/library owner actions 在 contextual UI 后仍正确；
- auth ownership；
- deep link/reload/legacy redirect。

### UI-QUAL-006 — End-to-End

至少覆盖：

```text
首次引导 → Today → canonical activity → Workspace → 返回 Today
Today → Learning → Goals → Goal Detail/Edit → Plan → Progress → History
Library → Search → Select → contextual action → Document/Knowledge context
Settings utility → category → Model/Data/Recovery flow → 返回
Legacy deep link → canonical route without side effect
```

E2E SHOULD 使用 deterministic fixture。真实模型 gate 独立报告，不得把 UI 完成称为学习效果。

### UI-QUAL-007 — Responsive / Visual

至少验证：

- 1440×900；
- 1024×768；
- 768×1024；
- 360×800；
- 100% / 200% zoom；
- light/dark（若当前 baseline 已启用）；
- 中文长标题；
- empty/max reasonable list；
- long formula/citation/error。

不得只验 desktop happy-path screenshot。

### UI-QUAL-008 — Accessibility

至少：

- semantic role / accessible-name assertions；
- keyboard-only primary path；
- focus order / focus return；
- contextual action keyboard/touch fallback；
- contrast；
- reduced motion；
- live error/status；
- drawer/sheet focus containment 与 Escape close。

### UI-QUAL-009 — Security

继续覆盖 raw HTML、unsafe URL、remote image、citation trace、prompt injection、grader-only leakage、unauthorized document/evidence、secret/log leakage。

Settings 重构必须继续覆盖 credential 不回填、web storage/DOM 泄漏、double submit、revision conflict、probe/apply/rollback/clear/erasure/recovery 安全路径。

## 4. Engineering Commands

Dedicated UI refactor EXEC 至少运行：

```bash
cd apps/frontend
npm test -- --run
npm run build
npm audit --audit-level=high

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

若修改 backend query/API，再运行对应 backend targeted + full gates：

```bash
cd apps/backend
uv run pytest <targeted tests>
uv run pytest
uv run ruff check app tests
uv run mypy app --no-error-summary
uv run alembic check
```

若全量命令因既有问题失败，必须区分本次新增失败与预存失败；不得删除测试、弱化断言、扩大 ignore 或越界格式化。

## 5. Performance Budgets

### UI-QUAL-020

EXEC 必须先记录 baseline，再冻结不回归或明确预算。至少记录：

- frontend production bundle total / route chunk；
- first usable shell render；
- Learning facet switching；
- long history render；
- Library document list / knowledge map；
- RichMessage KaTeX/Markdown lazy-load；
- memory growth across route/workspace switching。

无 measurement 不得发明硬数值门槛。

### UI-QUAL-021

知识地图必须限定 scope/node/edge；长 History SHOULD 分页/虚拟化评估。不得为了新聚合页一次性加载全部私人文档、消息或 evidence history。

## 6. Release and Claim Boundaries

### UI-QUAL-030

Interaction Architecture Slice 完成只能声明：

```text
UI Engineering Gate
UI Contract Correctness Gate
Accessibility / Security Gate
```

UI 可用、视觉改善、点击减少或会话完成不得改写：

```text
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
```

### UI-QUAL-031 — Blocking Conditions

以下任一阻断 Slice DONE：

- EXEC-1062 未 DONE 即修改重叠 frontend files；
- L0 仍保留 Goal/Path/Evidence/History/Settings 平级结构；
- 通过四个等权 Card 伪装 Learning 聚合；
- Today canonical activity 与 Quick Start 同级；
- Library 无 selection 时永久显示 batch control panel；
- Settings relocation 复制或弱化 model/data/recovery security；
- legacy route redirect 有业务副作用；
- 360px/keyboard/error path 未验证；
- unknown/partial/stale 被伪装 READY；
- 未声明公共 API/schema 变化。

## 7. Remaining SPEC GAP / Deferred Register

以下仍明确延后，不得在 Interaction Architecture refactor 中顺手实现：

| Item | Status | Reason |
|---|---|---|
| Plan manual edit/reorder | DEFERRED | 需 SYS06 owner command/conflict contract |
| Learner-state dispute/retest | DEFERRED | 需 SYS03/SYS04 workflow contract |
| Persistent notes | DEFERRED | 无 owner/schema/retention contract |
| Stable mastery product labels | DEFERRED | 必须由 versioned SYS03 rule 产生 |
| New global search/command palette | DEFERRED | 本 Slice 只保留 utility slot，不新增跨域 search contract |

Goal create/edit/lifecycle 与 canonical activity start/resume 已有正式 contract，不再列为 deferred。

## 8. Acceptance Criteria

- `UI-MIG-AC-001`：ADR-0014 → UI Specs → Vertical Slice → EXEC 链完整；
- `UI-MIG-AC-002`：dedicated UI refactor 等待 EXEC-1062 DONE 后执行；
- `UI-MIG-AC-003`：旧 routes 有 mapping、source label/retirement（适用时）且无副作用；
- `UI-MIG-AC-004`：无第二全局 nav、第二 chat-first entry 或第二 domain truth；
- `UI-QUAL-AC-001`：frontend tests/build/audit/docs/diff gates 有真实结果；
- `UI-QUAL-AC-002`：component/integration/E2E/accessibility/security 覆盖关键 semantic behavior；
- `UI-QUAL-AC-003`：1440/1024/768/360、200% zoom、keyboard 通过验收；
- `UI-QUAL-AC-004`：Engineering/Contract/Accessibility gates 与 Learning Evidence 分开报告；
- `UI-QUAL-AC-005`：Deferred items 未被 frontend-only state 隐式实现。

## 9. Forbidden Completion Claims

禁止把以下称为 DONE：

- 只改 Sidebar labels；
- 只有静态 mockup；
- 只有 CSS 重构；
- build 通过但 route/state/runtime path 未验；
- 通过 Dashboard Cards 重新包装旧 IA；
- 桌面截图正常但窄屏/键盘/错误/空态未验；
- Settings 看起来更简洁但安全逻辑被复制或删除；
- UI 指标改善被描述为真实学习效果改善。

## 11. UX Architecture Migration and Quality Gates (ADR-0018)

本节冻结 `UX-Architecture-Canonical-Design-Delta.md` 经 `ADR-0018` 吸收后的迁移与质量 gate。凡与本节冲突的旧条款按 [Supersession Matrix](#12-uxa-supersession-matrix-ui-ia) 处置。

### UXA-MIG-00 — Implementation Approval Chain

产品代码修改必须：

```text
PRODUCT-POSITIONING 不冲突
→ ADR-0018 accepted
→ UI Specs（UXA-* 条款）frozen
→ UI-04 Vertical Slice frozen
→ serial EXEC dependency gate（XIK-171/172/177/175/179/165 适用）satisfied
→ Code/Test
```

不得直接依据 UX Architecture Delta 修改 React。不得用前端 mock 绕过未完成的 Workspace 产品架构。

### UXA-MIG-01 — Workspace Context / Shell Migration

- 三栏解析同一 canonical `current_workspace_id`；
- 不得把 route/subject/session/local state 冒充 Workspace truth；
- Workspace 切换不静默丢弃 draft/stream/note/session/material；
- 单一 Workspace 不显示虚假 selector。

若 Workspace switch command / UserNote owner 未由现有上位合同唯一确定，对应 EXEC 为 `BLOCKED_BY_SPEC_GAP`。

### UXA-MIG-02 — Learning De-management Migration

- Goals/Path/Progress/History 不再作为常驻管理 facet；
- 不删除 LearningGoal/LearningPlan/LearnerState/Evidence/ReviewSchedule/History canonical truth；
- 必要创建/纠正/确认/恢复/审计进入 contextual task flow，不恢复长期管理中心；
- 旧 `/learning/**` 路由保留 no-side-effect 迁移（见 `UXA-IA-030`）。

### UXA-MIG-03 — Library No-OCR Migration

- Library v1 正常 UI 不暴露 OCR 入口/状态/review/publish/confidence/bbox/hash；
- 扫描 PDF 诚实显示 `unsupported / partial extraction` 并建议文本型资料；
- 历史/optional OCR runtime 的保留由 v1 Product Architecture cleanup 决定，v1 正常 UI 不可达。

### UXA-MIG-04 — Deferred Candidates

大纲、Evidence、知识图谱、Progress、AI Summary、Flashcards、错题本不进入 V1，不建立 placeholder/disabled tab/空页面。

### UXA-MIG-05 — Route / Deep-link Migration Gate

- 旧 route redirect 无业务副作用（不创建 session/activity、不触发 command）；
- deep link 保留；删除旧 route 前满足 retirement condition 并完成历史 deep-link 验证；
- 迁移后 focus 移到新页面语义起点。

### UXA-QUAL-00 — No Silent Data Loss

Workspace 切换、右栏收起、Drawer 关闭、route 迁移、autosave 失败 MUST 呈现 `saved / saving / failed / recoverable`。浏览器内存不构成 durable recovery；未持久化时不得显示"已保存"。

### UXA-QUAL-01 — Responsive / Accessibility Gate

至少验证 1440×900、1024×768、768×1024、360×800 与 200% zoom：

- 三栏职责在各 breakpoint 成立；
- 无页面横向滚动；
- 右栏/Drawer/选项在窄屏为可访问 sheet，不永久消失；
- keyboard/touch/screen reader 可操作三栏、Drawer、tab、Workspace switch，focus 返回触发点；
- 无 critical 三层嵌套滚动。

### UXA-QUAL-02 — Engineering Commands

UI-04 EXEC 至少运行：

```bash
cd apps/frontend
npm test -- --run
npm run build
npm audit --audit-level=high

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

若修改 backend query/API，再运行 backend targeted + full gates。全量命令因既有问题失败时区分本次新增失败与预存失败。

### UXA-QUAL-03 — Claim Boundary

UI-04 完成只能声明 `UI Engineering Gate`、`UI Contract Correctness Gate`、`Accessibility / Security Gate`。不得把文档冻结或 UI 可用描述为产品已实现或真人学习效果改善。

### UXA-QUAL-04 — Blocking Conditions

以下任一阻断 UI-04 DONE：

- 未满足 Workspace Product Architecture 依赖即用前端 mock 实现 Workspace；
- 三栏不同步解析同一 current_workspace_id；
- Drawer 内容由前端从 chat/heading/probability 推断；
- 右栏/autosave 有静默数据丢失；
- Library v1 正常 UI 暴露 OCR；
- 建立 placeholder/disabled tab 代表 deferred candidates；
- 旧 route redirect 有业务副作用；
- 360px/keyboard/error path 与 200% zoom 未验证；
- MISSING/PARTIAL/STALE 被伪装 READY。

## 12. P1-06 Compatibility Gate

### UI-MIG-040

P1-06B `EXEC-1062` 继续按其冻结合同完成 `/welcome`、default entry、dismiss/reopen/deep-link/restart 和真实四步闭环。

由于 ADR-0014 已更新 UI IA，EXEC-1062 执行时 MUST 以最新 `UI-IA-*` / `UI-SCREEN-*` 为直接合同，并保持：

- `/welcome` supporting route 不成为 L0；
- complete 后进入 `/today`；
- explicit deep link preservation；
- Settings reopen 入口仍属于 App Utility；
- 不恢复旧 7-item L0 navigation。

Interaction Architecture implementation 必须等待 EXEC-1062 DONE，避免 shared frontend files 并行变更。

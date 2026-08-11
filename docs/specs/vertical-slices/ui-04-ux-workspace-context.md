# UI-04 — UX Workspace Context and Three-Column Learning Architecture

> Status: **FROZEN**  
> Product Traceability: `CAP-01`、`CAP-04`、`CAP-07`；`PD-REQ-0101..0103`、`PD-REQ-0401`、`PD-REQ-0701..0702`；`PD-RULE-006/009/011`；`PD-NFR-005`  
> Governing: `PRODUCT-DEFINITION.md`、`ADR-0018`、`ADR-0014`、`UXA-IA-*`、`UXA-SCREEN-*`、`UXA-DATA-*`、`UXA-IES-*`、`UXA-COMP-*`、`UXA-VIS-*`、`UXA-QUAL-*`  
> Historical execution refs: `EXEC-068 → 069 → 070 → 071 → 072 → 073`；实时状态以 Linear 与 current `main` 为准  
> Scope type: presentation / information architecture / interaction architecture / data-query boundary absorption

## 0. Acceptance Ownership

本 Vertical Slice 把已冻结 Product Definition 转化为 UX / UI implementation contract；它不拥有 Product Scope。

- 本文件 `In Scope / Out of Scope` 只表示 UI-04 implementation-slice scope，不等同 v1 Feature inclusion / exclusion；
- `UXA04-AC-*` 属于 **UX / Vertical Slice Acceptance**，不得自动升级为 `PD-AC-*`；
- Product Capability / Requirement / Rule / v1 Scope 以 `docs/product/PRODUCT-DEFINITION.md` 为上游 authority；
- 若 UI-04 需要改变 Product Scope、UserNote 的产品意义、Workspace 产品语义或 Product Acceptance，必须先报告 `PRODUCT DEFINITION GAP`；
- UI Engineering / Contract / Accessibility PASS 不自动证明 Product Acceptance，更不证明 Learning Evidence。

## 1. Objective

把 `UX-Architecture-Canonical-Design-Delta.md` 经 `ADR-0018` 吸收后的三栏学习架构与 Workspace 上下文转化为可机械执行的实现合同：

```text
Left (Where)      Center (Learn)                    Right (Reference / Notes)
Global Nav        Teaching content                  User-authored notes
Current Workspace Questions                          Current source material
Workspace switch  Learner answers                   Citation / source context
                  Feedback
                  Learning Context Drawer
                  Composer
```

同时完成：

- Learning Context Drawer（默认收起，stage / stage goal / next 1..3）；
- Learning 去管理化（Goal/Plan/Progress/History 不再常驻）；
- Library v1 no-OCR exposure；
- 旧 `/learning/**` route 无副作用迁移；
- deferred candidates 不建 placeholder。

其中 no-OCR / deferred candidate 的 **Product Scope** 来自 Product Definition；本 Slice 只冻结相应 UI 呈现与迁移行为。

本 Slice 不改变任何 SYS01～SYS08 owner、Teaching Policy、LearningPlan、LearnerState、ReviewSchedule、ADT 或 data/security truth。不实现 Workspace / Notes / Context Drawer 的 owner 或 command。ADR-0019 已冻结 current Workspace 与 Drawer 的 read-only query composition；UserNote owner/command 必须由对应 current owner/spec 明确，UI 不得以前端 state 冒充 durable note truth。

## 2. Dependency Gate

执行本 Slice 的任何新工作 MUST 在开始时按 current truth 重新验证：

- `ADR-0018`、`ADR-0019` 仍为 applicable accepted decisions；
- `UI` Spec set（`UXA-*` 与既有 `UI-*`）仍为 current contract；
- Workspace / UserNote / Material / Drawer 所需 owner/query/command contracts 已冻结；
- current `main` 的 frontend tests/build baseline 可确定；
- Linear 中不存在未处理的 blocking dependency 或重叠实施工作。

历史 EXEC / Product Architecture issue 的完成状态只能作为历史证据引用，不在本 frozen Slice 中维护实时 dependency truth。未满足 current dependency 时返回适用 `PRODUCT DEFINITION GAP` / `SPEC GAP` / dependency block，不得用 frontend mock 绕过。

## 3. User Jobs

UI-04 支持以下 jobs；这些 jobs 是对 Product Definition 的体验实现，不创建新的 Product Capability：

1. 打开 Askora 立即进入当前 Workspace 中最值得完成的学习任务；
2. 知道当前阶段与接下来做什么，而不被管理页淹没；
3. 在同一学习画布中完成教学、作答、反馈与下一轮；
4. 在需要时查看当前资料与自己的笔记，而不离开学习；
5. 保持个人学习数据与 Workspace 隔离。

## 4. In Scope

本节只定义 UI-04 implementation scope。

### 4.1 Three-Column Shell

- Left = Where：稳定产品导航 + canonical current Workspace + 多 Workspace 切换入口；
- Center = Learn：唯一 Primary Learning Canvas（含 Context Drawer + composer）；
- Right = Reference / Notes：可隐藏，V1 仅学习笔记与当前资料；
- 三栏解析同一 canonical `current_workspace_id`。

### 4.2 Workspace Context

- current Workspace 列表/current/switch 状态（LOADING/EMPTY/READY/PARTIAL/STALE/ERROR/UNAUTHORIZED，切换含 SAVING/SAVED/FAILED/RECOVERABLE）；
- 切换处理 draft / stream / note / session / material-tab；
- 不静默丢弃；不以下拉/本地 state 冒充 Workspace truth。

### 4.3 Learning Context Drawer

- 固定在中栏 composer 正上方，默认收起；
- 收起显示一行 `当前阶段 · 接下来`；
- 展开只显示 stage / stage goal / next 1..3；
- 内容来自 canonical/versioned query 或 MISSING/PARTIAL/STALE；前端不推断。

### 4.4 Notes + Current Material Right Rail

- UserNote durable、Workspace-scoped、anchored、versioned；autosave/conflict/recovery；
- Current Material 来自 citation / "view source" 的当前 Workspace 资料；
- SourceSpan / cross-Workspace fail-closed。

### 4.5 Learning De-management

- Goal/Plan/Progress/History 不再常驻管理 facet；
- domain truth 保留；contextual task-flow 仅在明确 user job 下进入。

### 4.6 Library v1 No-OCR

- 正常 UI 不暴露 OCR 入口/状态/review/confidence/bbox/hash；
- 扫描 PDF 诚实显示 unsupported / partial。

## 5. Historical Serial EXEC Decomposition

以下序列保留为 UI-04 实施分解与历史证据索引，不承担实时工作状态：

### EXEC-068 — Workspace Context / Shell / Route Migration

范围：三栏 shell、current Workspace 可见性、Workspace switch 状态、旧 `/learning/**` route 无副作用迁移、deferred candidates 不建 placeholder。

退出条件：`UXA04-AC-001..004` + route/no-side-effect + shell responsive tests PASS。

### EXEC-069 — Learning Context Drawer Query and UI

范围：Drawer canonical query 消费、collapsed/expanded/missing/error 状态、presentation-only toggle。

退出条件：`UXA04-AC-005..006` + Drawer state/accessibility tests PASS。

### EXEC-070 — UserNote + Current Material Right Rail

范围：右栏 hide/show、Notes 状态（SAVING/SAVED/FAILED/CONFLICT/RECOVERABLE）、Current Material tabs、SourceSpan、cross-Workspace fail-closed。

退出条件：`UXA04-AC-007..009` + Notes/Material state tests PASS。

### EXEC-071 — Learning Management Exposure Removal

范围：去除常驻 Goal/Plan/Progress/History 管理 facet；保留 domain truth；contextual task-flow 仅在明确 user job 下进入。

退出条件：`UXA04-AC-010` + Learning de-management tests PASS。

### EXEC-072 — Library v1 No-OCR Exposure

范围：正常 UI 移除 OCR 入口/状态/review/confidence/bbox/hash；扫描 PDF 诚实显示 unsupported/partial。

退出条件：`UXA04-AC-011` + Library no-OCR tests PASS。

### EXEC-073 — Responsive / Accessibility / Release Acceptance

范围：1440/1024/768/360、200% zoom、keyboard/touch/screen-reader、focus return、no horizontal scroll、no critical nested scroll、no silent data loss、release evidence。

退出条件：`UXA04-AC-012..015` 全部 PASS。

如未来仍需继续实施或修复，实际顺序与 blocking dependencies 以 current Linear / frozen follow-up EXEC 为准。

## 6. Out of Scope

本节只约束 UI-04 Slice，不定义 Askora v1 总体 Product Scope。

- 实现 Workspace 产品架构本身（owner/command/迁移）；
- 实现 UserNote 或 Context Drawer 的 owner command / schema；
- 删除旧 `/learning/**` 路由或删除 Goal/Plan/Evidence/History 数据；
- 修改 Teaching Policy / mastery / review 算法；
- 建立第二 Tutor / Material / Note / Workspace truth；
- 实现 Product Definition 当前 deferred candidates；
- 扩展 OCR；
- 顺带清理无关技术债。

## 7. Route Contract

本次 route 迁移是无副作用 redirect / compatibility / task-flow（见 `UXA-IA-030`）。旧 `/learning/goals|plan|progress|history` 不再作为常驻管理页面，但保留迁移与 deep-link 兼容。删除旧 route 前必须满足 retirement condition 并完成历史 deep-link 验证。

## 8. Semantic Element Gate

实现新增/修改的核心交互必须可归入既有 7 类 primitive（Navigation / Action / Control / Selection / Disclosure / InteractiveContent / StatusFeedback），见 `UXA-IES-*`。不新增顶层 primitive。

## 9. UX / Vertical Slice Acceptance Criteria

以下 AC 不创建新的 Product Acceptance：

- `UXA04-AC-001`：三栏解析同一 canonical `current_workspace_id`；
- `UXA04-AC-002`：Workspace switch 处理 draft/stream/note/session/material-tab 且呈现 saved/saving/failed/recoverable；
- `UXA04-AC-003`：旧 `/learning/**` route 无副作用迁移，deep link 保留；
- `UXA04-AC-004`：单一 Workspace 不显示虚假 selector；deferred candidates 不建 placeholder；
- `UXA04-AC-005`：Drawer 默认收起，展开只显示 stage/stage goal/next 1..3，失败不阻断主任务；
- `UXA04-AC-006`：Drawer 内容来自 canonical/versioned query，前端不推断 next；
- `UXA04-AC-007`：右栏可隐藏且重开恢复上下文，无静默数据丢失；
- `UXA04-AC-008`：Notes 区分 SAVING/SAVED/FAILED/CONFLICT/RECOVERABLE；
- `UXA04-AC-009`：Current Material / SourceSpan 来自 canonical Workspace refs，跨 Workspace fail closed；
- `UXA04-AC-010`：Learning 不建立常驻 Goal/Plan/Progress/History 管理中心；
- `UXA04-AC-011`：Library v1 正常 UI 无 OCR 暴露，扫描 PDF 诚实显示 unsupported/partial；
- `UXA04-AC-012`：1440/1024/768/360 与 200% zoom 下主任务可完成且无横向滚动；
- `UXA04-AC-013`：keyboard/touch/screen reader 可操作三栏与 Drawer，focus 返回触发点；
- `UXA04-AC-014`：no critical nested scroll、no silent data loss；
- `UXA04-AC-015`：frontend unit/integration/E2E/build/audit/docs/diff gates PASS；Engineering / Contract / Accessibility 与 Learning Evidence 分开报告。

## 10. Required Tests

至少新增/更新：

- Workspace shell / current / switch 状态测试；
- route 迁移无副作用测试；
- Drawer collapsed/expanded/missing/error 测试；
- Notes autosave/conflict/recovery 测试；
- Current Material tab / SourceSpan / cross-Workspace fail-closed 测试；
- Learning de-management 测试；
- Library no-OCR 测试；
- keyboard/focus/accessibility 断言；
- 1440/1024/768/360 与 200% zoom 响应式验收。

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

若修改 backend query/API，再运行 backend targeted + full gates。本 Slice 默认不新增 owner command / schema；所需 owner contract 缺失时按正确 gap 类型阻断。

## 11. Migration / Rollback

迁移采用 presentation-only forward migration：

1. 三栏 shell；
2. Workspace context；
3. Drawer；
4. Notes + Material rail；
5. 去管理化；
6. Library no-OCR；
7. responsive / a11y / release gate。

不得产生 owner command 或数据库 migration，除非对应 Product Definition / Spec gap 被显式接受并在正确层冻结。rollback/forward-fix 为 presentation-only；不得恢复 chat-first default、Account/Login、双 Workspace truth 或永久四-facet管理中心。

## 12. Completion Claim

UI-04 completion 必须分层声明：

```text
Product Acceptance: separately evaluated against applicable PD-REQ / PD-AC
UX / UI Contract Gate: PASS | FAIL
UI Engineering Gate: PASS | FAIL
Accessibility / Security Gate: PASS | FAIL
Learning Evidence Gate: unchanged
```

禁止把文档冻结、UI 可用、点击减少、视觉改善或 UXA04 AC PASS 自动解释为 Product Acceptance 或学习效果证明。

# UI-04 — UX Workspace Context and Three-Column Learning Architecture

> Status: **FROZEN / SERIAL EXECUTION ACTIVE**
> Governing: `ADR-0018`, `ADR-0014`, `UXA-IA-*`, `UXA-SCREEN-*`, `UXA-DATA-*`, `UXA-IES-*`, `UXA-COMP-*`, `UXA-VIS-*`, `UXA-QUAL-*`
> Dependency: `EXEC-1062 DONE` + Workspace Product Architecture issues（XIK-171 / XIK-172 / XIK-177 / XIK-175 / XIK-179 / XIK-165 where applicable）
> Implementation chain: `EXEC-068 → 069 → 070 → 071 → 072 → 073`
> Scope type: presentation / information architecture / interaction architecture / data-query boundary absorption

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

本 Slice 不改变任何 SYS01～SYS08 owner、Teaching Policy、LearningPlan、LearnerState、ReviewSchedule、ADT 或 data/security truth。不实现 Workspace / Notes / Context Drawer 的 owner 或 command。ADR-0019 已冻结 current Workspace 与 Drawer 的 read-only query composition；UserNote owner/command 仍由对应 EXEC 独立执行 gap gate。

## 2. Dependency Gate

MUST 满足：

- `ADR-0018`、`ADR-0019` accepted 并登记于 `docs/adr/README.md`；
- `UI` Spec set（`UXA-*` 与既有 `UI-*`）FROZEN；
- `EXEC-1062` DONE（shared frontend files non-overlap）；
- Workspace Product Architecture dependency gate：XIK-171（Workspace/Project/Session persistence）、XIK-172（Workspace-scoped retrieval）、XIK-177（Workspace-scoped learner evidence）、XIK-175（non-core cleanup）、XIK-179、XIK-165 where applicable。UI-04 不得用前端 mock 绕过未完成的 Workspace 产品架构；
- 当前 main 的 frontend tests/build baseline 已记录；
- 无其他 active EXEC 同时修改本 Slice EXEC 的 Allowed Files，或已显式证明 non-overlap。

截至 EXEC-068/069 执行起点，上述依赖的 current-main implementation 已存在，ADR-0019 已关闭本两项 read-query gap。后续 EXEC 仍逐项重新验证自己的 owner/dependency gate；未满足时返回 `BLOCKED_BY_DEPENDENCY_GATE`。

## 3. User Jobs

UI-04 必须支持而不改变以下 jobs：

1. 打开 Askora 立即进入当前 Workspace 中最值得完成的学习任务；
2. 知道当前阶段与接下来做什么，而不被管理页淹没；
3. 在同一学习画布中完成教学、作答、反馈与下一轮；
4. 在需要时查看当前资料与自己的笔记，而不离开学习；
5. 保持个人学习数据与 Workspace 隔离。

## 4. In Scope

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

## 5. Serial EXEC Decomposition

### EXEC-068 — Workspace Context / Shell / Route Migration

范围：三栏 shell、current Workspace 可见性、Workspace switch 状态、旧 `/learning/**` route 无副作用迁移、deferred candidates 不建 placeholder。

依赖：ADR-0018 + UI Specs FROZEN；`EXEC-1062 DONE`；Workspace 产品架构 entry gate（若 Workspace switch command owner 未冻结则标记 `BLOCKED_BY_SPEC_GAP`）。

退出条件：`UXA04-AC-001..004` + route/no-side-effect + shell responsive tests PASS。

### EXEC-069 — Learning Context Drawer Query and UI

范围：Drawer canonical query 消费、collapsed/expanded/missing/error 状态、presentation-only toggle。

依赖：EXEC-068 DONE；Drawer canonical query contract 冻结（否则 `BLOCKED_BY_SPEC_GAP`）。

退出条件：`UXA04-AC-005..006` + Drawer state/accessibility tests PASS。

### EXEC-070 — UserNote + Current Material Right Rail

范围：右栏 hide/show、Notes 状态（SAVING/SAVED/FAILED/CONFLICT/RECOVERABLE）、Current Material tabs、SourceSpan、cross-Workspace fail-closed。

依赖：EXEC-069 DONE；UserNote / Current Material canonical refs 与 owner 冻结（否则 `BLOCKED_BY_SPEC_GAP`）。

退出条件：`UXA04-AC-007..009` + Notes/Material state tests PASS。

### EXEC-071 — Learning Management Exposure Removal

范围：去除常驻 Goal/Plan/Progress/History 管理 facet；保留 domain truth；contextual task-flow 仅在明确 user job 下进入。

依赖：EXEC-070 DONE。

退出条件：`UXA04-AC-010` + Learning de-management tests PASS。

### EXEC-072 — Library v1 No-OCR Exposure

范围：正常 UI 移除 OCR 入口/状态/review/confidence/bbox/hash；扫描 PDF 诚实显示 unsupported/partial。

依赖：EXEC-071 DONE。

退出条件：`UXA04-AC-011` + Library no-OCR tests PASS。

### EXEC-073 — Responsive / Accessibility / Release Acceptance

范围：1440/1024/768/360、200% zoom、keyboard/touch/screen-reader、focus return、no horizontal scroll、no critical nested scroll、no silent data loss、release evidence。

依赖：EXEC-072 DONE + `UXA-QUAL-*` gates。

退出条件：`UXA04-AC-012..015` 全部 PASS。

六个 EXEC MUST 串行，除非新的 Spec/EXEC revision 明确批准。

## 6. Out of Scope

- 实现 Workspace 产品架构本身（owner/command/迁移）；
- 实现 UserNote 或 Context Drawer 的 owner command / schema；
- 删除旧 `/learning/**` 路由或删除 Goal/Plan/Evidence/History 数据；
- 修改 Teaching Policy / mastery / review 算法；
- 建立第二 Tutor / Material / Note / Workspace truth；
- 实现 deferred candidates（大纲 / Evidence / 知识图谱 / Progress / AI Summary / Flashcards / 错题本）；
- 扩展 OCR；
- 顺带清理无关技术债。

## 7. Route Contract

本次 route 迁移是无副作用 redirect / compatibility / task-flow（见 `UXA-IA-030`）。旧 `/learning/goals|plan|progress|history` 不再作为常驻管理页面，但保留迁移与 deep-link 兼容。删除旧 route 前必须满足 retirement condition 并完成历史 deep-link 验证。

## 8. Semantic Element Gate

实现新增/修改的核心交互必须可归入既有 7 类 primitive（Navigation / Action / Control / Selection / Disclosure / InteractiveContent / StatusFeedback），见 `UXA-IES-*`。不新增顶层 primitive。

## 9. Acceptance Criteria

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

若修改 backend query/API，再运行 backend targeted + full gates。本 Slice 默认不新增 owner command / schema；对应 EXEC 冻结前标记 `BLOCKED_BY_SPEC_GAP`。

## 11. Migration / Rollback

迁移采用 presentation-only forward migration：

1. 三栏 shell；
2. Workspace context；
3. Drawer；
4. Notes + Material rail；
5. 去管理化；
6. Library no-OCR；
7. responsive / a11y / release gate。

不得产生 owner command 或数据库 migration（除非对应 EXEC 的 SPEC GAP 被显式接受并冻结）。rollback/forward-fix 为 presentation-only；不得恢复 chat-first default、Account/Login、双 Workspace truth 或永久四-facet 管理中心。

## 12. Completion Claim

UI-04 DONE 只允许声明：

```text
UI Engineering Gate: PASS
UI Contract Correctness Gate: PASS
Accessibility / Security Gate: PASS
Learning Evidence Gate: unchanged
```

禁止把文档冻结、UI 可用、点击减少或视觉改善解释为学习效果证明。

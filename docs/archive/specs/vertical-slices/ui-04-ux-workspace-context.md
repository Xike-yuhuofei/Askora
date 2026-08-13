# UI-04 — UX Workspace Context and Three-Column Learning Architecture

> Status: **FROZEN / SERIAL EXECUTION ACTIVE**  
> Product Traceability: `CAP-01`、`CAP-04`、`CAP-07`、`PD-NFR-005` + applicable `PD-REQ-*`  
> Governing Experience: `docs/design/experience/EXPERIENCE-ARCHITECTURE.md`、`LEARNING-EXPERIENCE.md`、`INTERACTION-MODEL.md`  
> Governing UI Contracts: `docs/specs/ui/screen-and-navigation-contracts.md`、`learning-interaction-contracts.md`、`design-system.md`、`quality-and-regression.md`  
> Technical UI Contract: `docs/specs/frontend/ui-read-model-contracts.md`  
> Governing ADR: ADR-0018、ADR-0019  
> Implementation chain: `EXEC-068 → 069 → 070 → 071 → 072 → 073`

---

## 1. Objective

把当前已冻结的 Workspace Experience 转化为机械可执行实现：

```text
Left / Where       Center / Learn                Right / Reference & Notes
Navigation         Teaching content              User-authored notes
Workspace context  Questions / tasks             Current source material
Workspace switch   Learner answers               Citation/source context
                   Feedback
                   Learning Context Drawer
                   Composer
```

并完成：

- shared canonical Workspace context；
- Learning Context Drawer；
- Notes + Current Material Right Rail；
- Learning 去管理化；
- Library v1 no-OCR exposure；
- compatibility route / deep-link migration；
- responsive / accessibility / release acceptance。

本 Slice 不改变 SYS01～SYS08 owner、Teaching Policy、LearningPlan、LearnerState、ReviewSchedule、Assessment/Evidence semantics，也不允许 frontend mock 冒充未冻结 owner truth。

---

## 2. Dependency Gate

执行任何未完成子 EXEC 前必须重新读取 current `main` + Linear，确认：

- Product Definition / Experience / UI Contracts current；
- ADR-0018 / ADR-0019 accepted；
- 前序 EXEC DONE；
- 所需 Workspace/UserNote/Material/read-model owner contract 已存在；
- 无重叠 active EXEC 修改同一 Allowed Files。

如果 Product capability/requirement 不明确：`BLOCKED_BY_PRODUCT_DEFINITION_GAP`。  
如果 owner/query/command contract 不明确：`BLOCKED_BY_SPEC_GAP`。  
不得以前端 local state 绕过 gate。

实时完成状态属于 Linear 与 `docs/planning/` current index，本 Vertical Slice 不维护第二套实时状态。

---

## 3. User Jobs

UI-04 必须支持：

1. 用户知道自己在哪个长期学习 Workspace；
2. 用户进入当前最值得完成的 LearningActivity；
3. 在同一 Learning Canvas 中理解、思考、作答并得到反馈；
4. 需要时查看当前资料与自己的笔记而不离开学习；
5. 在轻量 Context Drawer 中理解当前阶段与下一方向；
6. 中断、切换、窄屏或恢复时不静默丢失学习上下文。

---

## 4. In Scope

### UI04-SCOPE-001 — Three-column Shell

- Left = Where：Product Navigation + current Workspace；
- Center = Learn：唯一 Primary Learning Canvas；
- Right = Reference / Notes：可隐藏，v1 仅 Learning Notes + Current Material；
- Drawer 在 Center Composer 上方；
- 所有区域使用同一 canonical Workspace scope。

### UI04-SCOPE-002 — Workspace Context

- current Workspace 可见；
- multi-Workspace selection/switch 只在真实候选存在时出现；
- switch 处理 draft/stream/note/session/material position；
- saved/saving/failed/recoverable 诚实呈现；
- route/local state 不冒充 persisted Workspace truth。

### UI04-SCOPE-003 — Learning Context Drawer

- 默认收起；
- collapsed：轻量 stage + next；
- expanded：stage / stage goal / next 1..3；
- MISSING/PARTIAL/STALE/ERROR 不伪装 READY；
- frontend 不从 chat/heading/probability 推断 next；
- expand/collapse 不触发 owner command。

### UI04-SCOPE-004 — Right Rail

- hide/show 是 presentation Control；
- Notes 是 durable UserNote；
- Notes states：SAVING/SAVED/FAILED/CONFLICT/RECOVERABLE；
- Current Material 由 citation/view-source 打开；
- SourceSpan 可追踪；
- cross-Workspace source fail closed；
- 无 generic extension host / deferred placeholder tab。

### UI04-SCOPE-005 — Learning De-management

- `/learning` 不再是 Goal/Plan/Progress/History 常驻管理中心；
- domain truth 保留；
- 创建/纠正/确认/恢复/审计只在明确 user job 下进入 contextual task flow；
- compatibility routes/deep links 保留 bounded migration 且无业务副作用。

### UI04-SCOPE-006 — Library v1 Exposure

- normal UI 不暴露 OCR action/status/review/confidence/bbox/hash；
- scanned PDF 无可靠文本时诚实显示 unsupported/partial；
- Product Definition 当前 deferred candidates 不建 placeholder。

### UI04-SCOPE-007 — Responsive / Accessibility

验证 1440/1024/768/360、200% zoom、keyboard、touch、screen reader、focus return、no horizontal scroll、no critical nested scroll、no silent data loss。

---

## 5. Serial EXEC Decomposition

### EXEC-068 — Workspace Context / Shell / Route Migration

范围：三栏 shell、current Workspace、switch 状态、route migration、deferred placeholder prevention。

当前实现证据保留于 completed EXEC/release；后续任务不得重新打开已验收范围，除非 current-main regression evidence 证明需要修复。

### EXEC-069 — Learning Context Drawer

范围：Drawer current projection、collapsed/expanded/missing/error、presentation-only toggle。

当前实现证据保留于 completed EXEC；后续只在 regression 时回修。

### EXEC-070 — UserNote + Current Material Right Rail

范围：Right Rail、durable Notes、Material tabs、SourceSpan、cross-Workspace fail closed。

主要 current contracts：

- `UI-LRN-080..105`；
- `UI-SHELL-001..005`；
- technical UI read model projections。

### EXEC-071 — Learning Management Exposure Removal

范围：移除 Goal/Plan/Progress/History 常驻管理 exposure；保留 contextual task flows 与 compatibility deep links。

主要 current contracts：

- `UI-NAV-003`；
- `UI-ROUTE-003..005`；
- `UI-LEARN-001..003`。

### EXEC-072 — Library v1 No-OCR Exposure

范围：normal UI no-OCR、scanned-PDF honest fallback、historical optional runtime unreachable。

主要 current contracts：`UI-LIB-001..004`。

### EXEC-073 — Responsive / Accessibility / Release Acceptance

范围：current UI-04 全链 responsive/a11y/regression/release evidence。

主要 current contracts：

- `UI-RESP-*`；
- `UI-LRN-130..132`；
- `UI-DS-A11Y-*`；
- `UI-QR-*`。

六个 EXEC 保持串行；完成状态以 current Linear/EXEC index 为准。

---

## 6. Out of Scope

- 改变 Product Capability / v1 Scope；
- 实现/重构 Workspace owner 本身；
- 在 UI Slice 中发明 UserNote/Material owner schema；
- 修改 Teaching Policy / mastery / assessment / review algorithm；
- 删除 Goal/Plan/Evidence/History domain truth；
- 建立第二 Tutor/Material/Note/Workspace truth；
- 扩展 OCR；
- 实现 deferred candidates；
- 无关技术债清理。

---

## 7. Route / Compatibility Rule

current routes 与 compatibility behavior 以 `screen-and-navigation-contracts.md` 为准。

旧 Goal/Plan/Progress/History deep link 可以保留为 bounded contextual/compatibility route，但：

- 不成为常驻 navigation；
- redirect/navigation 不产生 owner command；
- retirement 前保留 reload/back/deep-link evidence；
- 不通过删除 route 删除 canonical domain truth。

---

## 8. Semantic Interaction Gate

所有新增/修改交互必须映射到：

```text
Navigation
Action
Control
Selection
Disclosure
InteractiveContent
StatusFeedback
```

Button/Card/Tab/Drawer/Sheet 是 component/pattern，不新增顶层 semantic primitive。

---

## 9. Acceptance Criteria

- `UI04-AC-001`：Left/Center/Right/Drawer 共享 canonical Workspace；
- `UI04-AC-002`：Workspace switch 无静默 draft/stream/note/session/material loss；
- `UI04-AC-003`：route/deep-link migration 无业务副作用；
- `UI04-AC-004`：单一 Workspace 无虚假 selector；无 deferred placeholder；
- `UI04-AC-005`：Drawer 默认收起且只呈现合法 orientation；
- `UI04-AC-006`：Drawer current/next 不由 frontend 推断；
- `UI04-AC-007`：Right Rail 可隐藏/恢复，主任务仍可完成；
- `UI04-AC-008`：Notes save/conflict/recovery 诚实；
- `UI04-AC-009`：Current Material/SourceSpan Workspace-scoped 且 fail closed；
- `UI04-AC-010`：Learning 无常驻管理中心；
- `UI04-AC-011`：Library v1 normal UI 无 OCR exposure；
- `UI04-AC-012`：1440/1024/768/360 + 200% zoom 主任务可完成；
- `UI04-AC-013`：keyboard/touch/screen-reader/focus behavior 合格；
- `UI04-AC-014`：no critical nested scroll、no silent data loss；
- `UI04-AC-015`：current `UI-QR-*` gates PASS；
- `UI04-AC-016`：Product Acceptance / UX / Engineering / Accessibility / Learning Evidence 分开报告。

---

## 10. Required Tests

每个子 EXEC 至少运行：

```bash
cd apps/frontend
npm test -- --run
npm run build
npm audit --audit-level=high

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

如修改 backend query/API，则追加 current backend Required gates。

最终 EXEC-073 需要覆盖：

- Workspace shell/switch；
- Drawer；
- Notes/Material rail；
- Learning de-management；
- Library no-OCR；
- route/deep-link；
- 1440/1024/768/360 + 200%；
- keyboard/screen-reader/focus；
- failure/recovery/no-silent-loss。

---

## 11. Completion Claim

UI-04 完成最多可以声明：

```text
UX Contract Gate: PASS
UI Engineering Gate: PASS
Accessibility / Security Gate: PASS
```

只有在上游 Product Acceptance 有独立证据时才能声明相应 Product Acceptance。

不得由 UI-04 推导：

```text
Learning Evidence Gate: PASS
Retention improved
Transfer improved
Mastery improved
```

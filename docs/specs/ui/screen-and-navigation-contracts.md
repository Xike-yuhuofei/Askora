# Askora Screen & Navigation Contracts

> 状态：**Canonical UI/UX Implementation Contract — Current Only**  
> 冻结日期：2026-08-11  
> 上游产品定义：`docs/product/PRODUCT-DEFINITION.md`  
> Governing Experience：`docs/design/experience/EXPERIENCE-ARCHITECTURE.md`、`docs/design/experience/INTERACTION-MODEL.md`  
> Governing ADR：ADR-0014、ADR-0015、ADR-0018、ADR-0022
> 技术上游：Workspace / Goal / Activity / Recovery / Onboarding current Specs

---

## 1. Purpose

本文件定义 Askora 当前有效的：

- user-facing Information Architecture；
- Navigation hierarchy；
- route / deep-link behavior；
- shell / screen responsibility；
- page-level loading / empty / error / recovery；
- responsive screen behavior。

本文件只保存**当前有效规则**，不包含已被 ADR-0018 supersede 的旧 Learning four-facet 常驻管理模型。

本文件不拥有 Product Capability、domain ownership、API schema、persistence、Teaching Policy 或 component visual tokens。

---

## 2. Product Definition Traceability

主要映射：

| Area | Product Definition |
|---|---|
| Workspace / Library | `CAP-01`、`CAP-07`、`PD-REQ-0101..0104`、`PD-RULE-006/009/011` |
| Goal / Next Activity | `CAP-02`、`CAP-03`、`CAP-07`、`PD-REQ-0201..0203`、`PD-REQ-0301..0303` |
| Learning Canvas | `CAP-04`、`CAP-05`、`PD-REQ-0401..0403`、`PD-REQ-0501..0503` |
| Review / Validation return | `CAP-06`、`CAP-07`、`PD-REQ-0601..0603`、`PD-REQ-0701..0703` |
| Local data / settings | `CAP-08`、`PD-REQ-0801..0804`、`PD-RULE-008/010/011` |
| Accessibility / usability | `PD-NFR-005` |

UI Acceptance 不自动等同 Product Acceptance 或 Learning Evidence。

---

## 3. Required Screen State Vocabulary

所有依赖 canonical data 的 screen / region 必须区分适用状态：

```text
LOADING
EMPTY
READY
PARTIAL
STALE
ERROR
UNAUTHORIZED
```

附加规则：

- `PARTIAL` / `STALE` 不得显示成完整 READY；
- `MISSING` 可用于特定 optional projection，例如 Context Drawer；
- 局部数据失败优先局部降级，不应无条件让整个学习画布白屏；
- Empty 必须说明“缺什么”和“下一步能做什么”；
- Error 必须基于 stable error / retryability / recovery contract，而不是匹配自由文本；
- 不得用 fake data 填补 Goal、Activity、Evidence、Material 或 Workspace 空态。

---

## 4. Canonical User-facing IA

### UI-NAV-001 — Course-centric IA

稳定用户侧结构只允许：

```text
＋ 新课程                  Action
课程列表 / 当前课程          Navigation / InteractiveContent
资料库                     Stable Product Domain Navigation
Settings / Recovery        Utility Navigation
```

Today / Learning 不得作为 stable Product Domain、L0 Navigation 或默认 destination 出现。

### UI-NAV-002 — Utilities

以下属于 App Utility，不与 Product Domain 等权：

```text
设置
恢复中心
Search / Command（仅正式 capability 存在时）
```

Askora v1 无 Login / Register / Account shell。

### UI-NAV-003 — Course Is Not a Management Center

Course context 不提供 Goal / Plan / Progress / History 的常驻管理 navigation。

这些 domain truth 继续存在；仅在明确 user job 下通过 contextual task flow / Disclosure / compatibility deep link 进入。

### UI-NAV-004 — Chat Is Not Navigation

Chat / Tutor 不得成为 L0 Product Domain。Conversation 是当前 LearningActivity 的 interaction mode。

### UI-NAV-005 — User-facing Course Vocabulary

正常 UI 使用“课程”“当前课程”“切换课程”。`Workspace`、`current_workspace_id` 只在 engineering/diagnostic/audit context 出现。Course route id 仍是 canonical `workspace_id`；不得创建第二 Course identity。

### UI-NAV-006 — New Course Action

`＋ 新课程` 是 Primary `Action`。打开 `/courses/new` 是 Navigation 且无业务副作用；只有提交正式 Workspace create command 才可显示成功。Owner command 不可用时不得用 disabled placeholder、localStorage 或 React object 冒充已创建课程。

---

## 5. Workspace Shell

### UI-SHELL-001 — Shared Workspace Context

Workspace variant 中：

```text
Left = Where
Center = Learn
Right = Reference / Notes
```

三部分必须解析同一 canonical current Workspace。

### UI-SHELL-002 — Left / Where

左侧只承担：

- `＋ 新课程` Action；
- 当前课程、课程列表与 Course / Workspace switch；
- 当前课程 Activity Switcher / Recent Learning；
- Library Navigation；
- Utility group。

不得放置常驻 Goal/Plan/Progress/Evidence 管理结构。

### UI-SHELL-003 — Center / Learn

中央区域是唯一 Primary Learning Canvas。进入真实学习后不得同时呈现多个等权 Dashboard 或第二套 Tutor surface。

### UI-SHELL-004 — Right / Reference & Notes

右栏可隐藏；v1 只允许：

- Learning Notes；
- Current Material / citation source context。

隐藏后必须仍能完成主任务；重新打开时恢复当前可恢复上下文。

### UI-SHELL-005 — Learning Context Drawer

Drawer 固定在 Composer/输入区域上方，默认收起。

收起：当前阶段 + 接下来的一行方向信息。  
展开：仅 stage / stage goal / next 1..3。

不得加入 Goal editor、完整 Plan、Progress Dashboard、Evidence 管理、mastery / ReviewSchedule / TeachingAction 控制。

---

## 6. Route Contract

### UI-ROUTE-001 — Stable Destinations

稳定用户侧目的地：

```text
/courses/new
/courses/:workspaceId
/courses/:workspaceId/activities/:activityId
/library
/settings
/settings/recovery
/welcome            # supporting route, not L0
```

兼容 Workspace route 可以提供：

```text
/workspaces/:workspaceId
/workspaces/:workspaceId/learn
/workspaces/:workspaceId/library
```

其中 `:workspaceId` 保持 canonical Workspace identity；`courses` 只是 user-facing route vocabulary。

具体 router implementation（hash/history/native bridge）不是本合同 Authority。

### UI-ROUTE-002 — Learning Activity Deep Links

现有 activity/session deep link 可以保留兼容：

```text
/learn/:activityId
/quick/:sessionId
```

但必须进入对应 Course scope 下同一 canonical LearningActivity / dialog facade，不得创建第二 transcript / Attempt / TeachingAction truth。无法证明 Activity 属于目标 Course 时 fail closed。

### UI-ROUTE-003 — Legacy Today / Learning Compatibility

`/today`、`/learning` 与 `/` 必须按 canonical read state side-effect-free 解析：

```text
最近 Course + resumable Activity
→ /courses/:workspaceId/activities/:activityId

有 Course、无 resumable Activity
→ /courses/:workspaceId

无 Course
→ Course Empty State
```

`/today`、`/learning` 只作为 compatibility entry，UI/analytics/Sidebar 不再把它们描述为 Product Domain。

### UI-ROUTE-004 — Contextual Learning Management Routes

以下旧/兼容路径可以在迁移期保留：

```text
/learning/goals/**
/learning/plan
/learning/progress
/learning/history
/goals/**
/path
/evidence
/history
/profile
```

它们不得再构成 Learning 常驻管理 IA。

允许用途：

- explicit goal create / correction / audit；
- plan explanation；
- evidence/progress explanation；
- history recovery / audit；
- bounded compatibility deep link。

### UI-ROUTE-005 — No-side-effect Navigation

Redirect / route change / facet-like presentation change不得自动：

- 创建 Goal / Activity / Session；
- 修改 focused/persisted business state；
- 写 Evidence；
- 触发 replan；
- 清空未提交工作。

### UI-ROUTE-006 — Deep-link Preservation

历史 deep link 在 retirement condition 满足前必须可解释地迁移。删除兼容 route 前需有测试证明：

- no business side effect；
- back / reload 行为正确；
- active/resumable learning 不丢失；
- focus 落到新页面语义起点。

---

## 7. Course Entry / Empty / Creation Contract

### UI-COURSE-001 — Course Empty State

没有 canonical Course/Workspace 时，`/` 与 course shell 显示 Course Empty State：

- 明确当前还没有课程；
- Primary Action 只有“新课程”；
- 可以解释课程是长期学习空间；
- 不生成默认课程、Goal、Plan、Activity 或示例数据。

### UI-COURSE-002 — Course Creation Flow

```text
创建课程
→ 添加/选择资料（适用时）
→ 明确目标
→ 建立首个可执行 Activity
→ Course-scoped Learning Workspace
```

每一步必须表达 LOADING/READY/PARTIAL/ERROR/RECOVERABLE 等真实状态。Course create success 只来自 Platform Workspace Registry command result；Material、Goal、Activity readiness 分别来自其 owner，不得打包成 frontend fake transaction。

### UI-COURSE-003 — Course Landing

`/courses/:workspaceId` 展示当前 Course context 与 Activity Switcher / Recent Learning。存在 resumable Activity 时可提供一个 Primary resume Action；无 Activity 时显示缺失原因和真实可用的下一步，不生成假 Activity。

### UI-COURSE-004 — Activity Switcher

- 只显示当前 Course 内 exact LearningActivity refs；
- title 使用学习语义，不使用 Chat 1/2/3；
- current/active state 明确；
- 打开已 active/resumable Activity 是 Navigation / InteractiveContent；
- 启动 available Activity 使用 `StartLearningActivity` Action；
- 切换 presentation 不复制 transcript、Attempt 或 TeachingAction。

### UI-COURSE-GAP-001 — Technical Command/Query Gate

**CLOSED by ADR-0023 / `CWSP-*`**。Course list/create/current/switch、switch conflict recovery 与 Course-scoped recent/resumable Activity projection 的 owner、strict v1 schema、version、idempotency、error、migration 与 recovery 已冻结。Frontend implementation MUST consume that contract and remains blocked only by XIK-189 platform implementation dependency；不得重新发明 schema/owner。

---

## 8. Course-scoped Learning Contract

### UI-LEARN-001 — Learning Workspace Under Course

Learning Workspace 位于 Course context 之下，不再由 `/learning` L0 拥有。没有可恢复 Activity 时返回 Course landing / Activity Switcher，不得前端自行创建 Session/Goal/Plan。

### UI-LEARN-002 — Same Activity Across Presentation Changes

Course-scoped Learning Workspace、兼容 Tutor、Focus/窄屏 presentation 只允许改变呈现，不得重新生成 canonical Activity / Attempt / TeachingAction / transcript。

### UI-LEARN-003 — Required Learning State

中央学习画布必须能够呈现：

- current task / teaching content；
- learner input / Attempt；
- feedback；
- streaming / completed / failed / recoverable state；
- 必要 citation / assistance / validation obligation。

学习消息与具体行为由 `learning-interaction-contracts.md` 管理。

---

## 9. Library Contract

### UI-LIB-001 — Purpose

Library 让用户管理当前产品支持的 Material、理解来源状态，并进入 material-grounded learning。

### UI-LIB-002 — Default Hierarchy

默认优先：

```text
Import
Search / Filter
Material list
Selected material context
```

重复 Material 默认 row/list；批量/低频操作只在 selection/context 下出现。

### UI-LIB-003 — No OCR Exposure in v1 Normal UI

正常 v1 UI 不暴露：

- OCR action；
- OCR engine/status；
- OCR candidate / review / publish；
- OCR confidence/bbox/hash 等实现细节。

扫描 PDF 无可靠文本时显示 `unsupported / partial extraction` 和可行动建议。

### UI-LIB-004 — Deferred Candidates

大纲、Evidence 管理中心、知识图谱管理 UI、Progress Dashboard、AI Summary、Flashcards、错题本不得建立 placeholder/disabled tab。

若 Product Definition 未来纳入，先更新上游 Product/Experience，再进入 UI Spec。

---

## 10. Settings / Recovery Contract

### UI-SET-001 — Utility Hierarchy

Settings 使用 category navigation / secondary destination，而不是 giant control grid。

### UI-SET-002 — Current Product Boundary

不得恢复已退役的 Account/Login/Password/AuthSession UI。

Local data、BYOK、Recovery 的用户行为必须服从 current Product Definition 与 security/data-control contracts。

### UI-SET-003 — Recovery Presentation

Recovery 不新增 Product Domain。存在 action-required issue 时可显示紧凑全局状态/入口；恢复 action 必须使用 owner 提供的合法 RecoveryAction，不得由 frontend 发明 command。

---

## 11. First-use / Welcome

### UI-WELCOME-001

`/welcome` 是 supporting route，不是 L0。

first-use 只呈现用户必须完成/理解的事实步骤，例如模型能力、课程、材料、目标、首次 Activity；内部 diagnostic/planner/system stage 不得成为用户必须学习的工程流程。完成 onboarding 后使用 UI-ROUTE-003 startup resolution，不再固定跳转 `/today`。

### UI-WELCOME-002

显式 deep link 应尽量保留；Welcome redirect / dismiss 不产生额外业务副作用，也不得依赖 localStorage 冒充 readiness truth。

---

## 12. Responsive / Input Screen Rules

至少验证：

```text
1440×900
1024×768
768×1024
360×800
200% zoom
```

### UI-RESP-001

窄屏允许：Sidebar → drawer/compact rail；Right Rail → accessible sheet/section；Drawer → compact disclosure/sheet。

语义职责不得改变。

### UI-RESP-002

页面不得出现阻断任务的横向滚动。公式/代码等局部内容 MAY 自身滚动，但页面整体必须保持可用。

### UI-RESP-003

避免页面 + conversation + drawer 三层关键嵌套滚动。

### UI-RESP-004

关键 Navigation、Drawer、Right Rail、Workspace switch、Material tabs 必须有 keyboard/touch 等价路径；关闭 transient surface 后恢复合理 focus。

---

## 13. Forbidden Implementations

禁止：

- Domain object count → navigation count；
- 恢复 Goal/Plan/Progress/History 常驻管理中心；
- 恢复 Today / Learning L0 或用新 Dashboard 替代；
- `/`、`/today` 或 `/learning` 直接退化为 chat-first picker；
- 用 frontend/localStorage 创建或切换 Course/Workspace；
- route change 产生隐藏 business write；
- 用 frontend state 冒充 Workspace/Plan/Evidence/UserNote truth；
- 新增第二 Tutor / transcript；
- 为 deferred capability 建空页面/disabled tab；
- 用 OCR pipeline 复杂度占据 v1 Library；
- 用 Account/Auth UI 反向改变 Local Single-User 产品定义；
- 因窄屏隐藏完成任务所需唯一 citation/error/assistance/validation 信息。

---

## 14. Acceptance Criteria

- `UI-SN-AC-001`：Today / Learning 不再是 L0；`＋ 新课程`、课程列表、Library 与 Utility 语义分组正确；
- `UI-SN-AC-002`：Course 无常驻 Goal/Plan/Progress/History 管理导航；
- `UI-SN-AC-003`：Workspace shell 三栏解析同一 current Course/Workspace；
- `UI-SN-AC-004`：Course Empty State、Course creation 与 Activity Switcher 无 fake data/placeholder；
- `UI-SN-AC-005`：`/`、`/today`、`/learning` 与 deep links 无业务副作用且不会创建第二 truth；
- `UI-SN-AC-006`：Library normal v1 UI 无 OCR 暴露且 deferred candidates 无 placeholder；
- `UI-SN-AC-007`：Settings/Recovery 保持 Utility 语义且无 Account/Auth residue；
- `UI-SN-AC-008`：LOADING/EMPTY/PARTIAL/STALE/ERROR 等不会伪装 READY；
- `UI-SN-AC-009`：1440/1024/768/360 与 200% zoom 下主要用户任务可完成；
- `UI-SN-AC-010`：keyboard/touch/focus/deep-link/back/reload 的关键路径可验证；
- `UI-SN-AC-011`：无静默丢失 draft/stream/note/session/material context；
- `UI-SN-AC-012`：UI Acceptance 不被描述为 Product Acceptance 或 Learning Evidence。
- `UI-SN-AC-013`：用户界面使用“课程”，但 route/API/domain/persistence 仍解析同一 Workspace identity。
- `UI-SN-AC-014`：Course switch 改变真实 scope，并在 draft/stream/note/session/material 冲突时使用 owner-defined recovery。
- `UI-SN-AC-015`：一个 Course 下多个 Activity 可恢复/切换，Conversation 不成为 thread manager。

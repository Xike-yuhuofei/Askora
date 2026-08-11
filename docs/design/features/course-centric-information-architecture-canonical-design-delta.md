# Askora Course-centric Information Architecture — Canonical Design Delta

> 状态：**FROZEN — Canonical Experience Design Delta Record**
> 冻结日期：2026-08-11
> 决策权限：user-delegated Codex；用户明确要求按正式 Course-centric IA 变更提示词执行，并授权选择最佳安全执行方式
> 上位约束：`PRODUCT-STRATEGY.md`、`PRODUCT-POSITIONING.md`、`PRODUCT-DEFINITION.md`
> Product trace：`CAP-01`、`CAP-04`、`CAP-07`、`PD-REQ-0401`、`PD-REQ-0701..0703`、`PD-RULE-002`、`PD-RULE-009`
> Current-state evidence：[`../../archive/audits/course-centric-ia-current-state-gap-analysis.md`](../../archive/audits/course-centric-ia-current-state-gap-analysis.md)
> 下游：ADR-0022、current Experience、current UI Specs、Linear implementation decomposition
> 基线：`origin/main@6a94cf7b`

## 1. Purpose

本 Delta 将 Askora 从 `今天 / 学习 / 资料库` 的入口模型调整为以长期课程上下文为中心的 Information Architecture，同时保持 Askora 仍是个人长期 AI 学习系统，而不是 LMS、Chat Thread Manager 或课程管理后台。

它回答：

> 用户如何围绕多个长期课程进入、恢复和切换真实 LearningActivity，同时让资料、笔记、历史与学习上下文始终服从同一个 canonical Workspace？

本 Delta 不重命名 canonical `Workspace`，不修改 API/database/schema，不改变 `LearningProject`、Teaching Policy、LearnerState、Evidence、Review 或 SYS01～SYS08 ownership。

## 2. Product and Vocabulary Boundary

### COURSE-CD-001 — Course is the user-facing Workspace vocabulary

冻结：

```text
User-facing vocabulary: 课程
Canonical product/domain identity: Workspace
```

“课程”表示用户可理解的长期学习空间；其真实 scope、identity、version、lifecycle 与隔离仍由 canonical `Workspace` 提供。

`LearningProject` 保持 Workspace 内的可选组织对象，不与“课程”互换。本变更不把 Askora 重新定义为 LMS，也不引入教学班、教师、选课、课表或课程发布语义。

### COURSE-CD-002 — Vocabulary must not leak implementation language

正常用户界面使用“课程”“当前课程”“切换课程”。`Workspace`、`current_workspace_id`、SYS/DTO/version ref 只在工程、诊断或必要审计层出现。

## 3. Frozen Product IA

### COURSE-CD-010 — Course-centric structure

```text
Askora
│
├── ＋ 新课程
│
├── 课程
│   ├── 机器学习
│   ├── 英语
│   └── Askora 产品设计
│
├── 资料库
│
└── Utilities
    ├── Settings
    └── Recovery
```

- `＋ 新课程` 是 Primary `Action`，不是 Navigation；
- 课程项是 `Navigation / InteractiveContent`；
- `资料库` 是稳定 Product Domain Navigation；
- Settings / Recovery 是 Utility；
- `今天` 与 `学习` 不再是稳定 Product Domain 或 L0 Navigation。

### COURSE-CD-011 — No replacement dashboard

删除 Today/Learning 入口不得被另一个 Dashboard 替代。禁止新增 Goal、Plan、Progress、Knowledge Graph、Agent Console、Chat History 或 Course Management Console 作为 L0。

## 4. Left / Where Responsibility

### COURSE-CD-020

Left / Where 只承担：

```text
Create Course Action
Current Course / Workspace Context
Course Switching
Library Navigation
Utilities
```

课程列表优先使用紧凑 row/list；不使用 Card ocean，不把每个 course 做成带统计 Dashboard 的管理卡片。

## 5. Course / Workspace Switching

### COURSE-CD-030 — Real scope switch

课程切换必须切换同一个 canonical Workspace scope 下的：

- `current_workspace_id`；
- LearningActivity / resumable LearningSession；
- Materials / retrieval；
- UserNotes；
- Current Material / SourceSpan；
- Goal / Plan / LearnerState / Review projections；
- LearningHistory 与可恢复 presentation context。

只改变 Sidebar selected state、route、React context 或 localStorage 属于禁止实现。

### COURSE-CD-031 — Safe switch sequence

选择候选课程是 `Selection`；真正切换是显式 `Action`。当 draft、stream、note、Material position 或 active/resumable session 存在冲突时，必须先进入 owner-defined save/recovery result，成功后才能宣布切换完成。

Deep link 本身是 Navigation，不得隐式写 `current_workspace_id`；需要切换时必须调用同一个正式 switch command，并处理冲突。

## 6. Course, Activity, Session and Events

### COURSE-CD-040 — Experience hierarchy

```text
Course（Workspace）
    ↓
LearningActivity
    ↓
LearningSession
    ↓
Conversation / Attempt / Feedback / Learning Events
```

一个 Course 可以包含多个 LearningActivity。Conversation 继续只是 LearningActivity 的 interaction mode，不成为一级对象、独立 Chat Thread 或 course switch substitute。

### COURSE-CD-041 — Activity Switcher / Recent Learning

每个 Course 提供 Activity Switcher / Recent Learning，用于恢复或切换当前课程内的 LearningActivity：

- 标题优先使用明确学习目的，例如“比较监督学习与无监督学习”；
- 禁止默认命名为“Chat 1 / Chat 2 / Chat 3”；
- 打开已存在且可恢复的 Activity 是 Navigation / InteractiveContent；
- `Start / Resume / Retry` 等会改变 lifecycle 的行为是 Action；
- Activity Switcher 不展示第二份 plan、mastery 或 review truth。

## 7. Course Creation Journey

### COURSE-CD-050

```text
＋ 新课程
→ 创建课程
→ 添加 / 选择学习资料（适用时）
→ 明确学习目标
→ 建立首个可执行 LearningActivity
→ 进入 Course-scoped Learning Workspace
```

约束：

- flow 只使用学习者可理解语言；
- 不暴露 Workspace registry、SYS、DTO、migration 或 learner-state internal step；
- 创建 Course 不自动证明 material、goal、plan 或 activity 已就绪；
- route visit / opening flow 不创建 Workspace/Activity/Session；
- 没有真实 owner command/readiness 的步骤不得以 placeholder 或假成功出现。

## 8. Default Entry and Empty State

### COURSE-CD-060 — Startup resolution

```text
存在最近活动课程 + resumable Activity
→ 恢复该 Course / Activity

存在 Course 但无 resumable Activity
→ 打开最近 Course 的 honest orientation / Activity Switcher

没有 Course
→ Course Empty State
→ Primary Action: 新课程
```

启动解析与 redirect 必须 side-effect free；不得因访问 `/`、`/today` 或 `/learning` 创建 Activity/Session、修改 Workspace truth 或丢失可恢复状态。

## 9. Learning Workspace Retention

### COURSE-CD-070

三栏学习职责保持：

```text
Course Context
    ↓
Left / Where | Center / Learn | Right / Reference & Notes
```

删除“学习”L0 入口不删除 Learning Workspace。Center 继续是唯一 Primary Learning Canvas；Right 继续只承担 Notes 与 Current Material；Learning Context Drawer 继续提供轻量方向。

## 10. Route Design Direction

Canonical user-facing route family：

```text
/
/courses/new
/courses/:workspaceId
/courses/:workspaceId/activities/:activityId
/library
/settings
/settings/recovery
```

`workspaceId` 明确是 canonical Workspace identity；route 使用 `courses` 只表达用户词汇，不创建 Course domain object。

兼容：

- `/today`、`/learning`：只做 context-aware、side-effect-free resolution；
- `/learn/:activityId`、`/quick/:sessionId`：保持可解释 deep link；
- `/workspaces/:workspaceId/**`：可迁移到对应 `/courses/:workspaceId/**`，identity 不变；
- Goal/Plan/Progress/History legacy routes 继续仅承担 bounded contextual/audit compatibility。

## 11. Alternatives Considered

### A. Keep Today/Learning and add Course selector

Rejected。Course 仍会退化为 cosmetic selector，用户继续需要先理解两个抽象入口，且无法建立“长期课程 → 当前活动”的稳定心智模型。

### B. Rename canonical Workspace to Course everywhere

Rejected。本次目标是 Experience IA 与 user vocabulary；全栈重命名会触发 Product Definition、API、schema、migration 与 compatibility 变化，风险远高于用户价值。

### C. Map Course to LearningProject

Rejected。当前 Product Definition 与 ADR-0016 已冻结 Workspace 作为真实长期 scope，LearningProject 是其内可选组织对象。将 Course 映射到 Project 会留下 Workspace 作为用户不可理解的第二长期 scope，并产生歧义。

### D. Make Conversation the item below Course

Rejected。它会把 Askora 退化为 Chat Thread Manager，并违反 `PD-RULE-002` 与 LearningActivity primary-unit 语义。

## 12. Consequences and Implementation Gate

正向结果：

- 长期学习上下文成为导航主线；
- 多 Activity 恢复不再依赖 Today/Learning 抽象入口；
- Workspace scope 与用户心智更一致；
- Learning Workspace、Library 与 Utilities 的职责保持稳定。

成本与风险：

- ADR-0019 的 `SINGLE_WORKSPACE` presentation/query contract 不能支撑完整实现；
- 需要真实 Workspace list/create/current/switch + conflict recovery contract；
- 需要 Course-scoped Activity list/recent/resume projection；
- Sidebar、default redirect、Welcome、Today、Learning 与大量 route tests 都需要迁移；
- “课程”与 LearningProject 的文案/信息呈现必须持续避免混用。

因此：本 Delta 可以冻结 Experience，但前端不得在 technical contract 缺失时用 mock、localStorage 或 disabled placeholder 实现多课程。

## 13. Acceptance

- Today / Learning 不再是 stable Product Domain；
- `＋ 新课程` 是 Primary Action；
- 用户界面统一使用“课程”，canonical Workspace identity 不变；
- 多 Course 与多 LearningActivity hierarchy 完整；
- Conversation 未升级为一级产品对象；
- Course switch 改变真实 canonical scope；
- default entry / empty state / route compatibility 已冻结；
- Library 保持稳定导航，Settings/Recovery 保持 Utility；
- 三栏 Learning Workspace 保持；
- Product / UX / Engineering / Learning Evidence 声明继续分离。

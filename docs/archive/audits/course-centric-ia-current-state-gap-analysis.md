# Askora Course-centric IA — Current-state Gap Analysis

> 状态：Historical Audit Snapshot / Design Input
> 审计日期：2026-08-11
> 审计基线：`origin/main@6a94cf7b`
> 适用范围：Course-centric Information Architecture 正式变更
> 非 Authority：本文件只记录变更前差异；current truth 以 Product、Experience、ADR 与 UI Specs 为准

## 1. Current Authority Findings

变更前 current Canonical Experience 仍明确冻结：

```text
今天
学习
资料库
```

并冻结三栏责任：

```text
Left = Where
Center = Learn
Right = Reference / Notes
```

其中三栏责任、LearningActivity 主体验单元、Conversation 非一级产品对象、资料库稳定职责与 Utility 分组仍与新决策兼容；`Today / Learning` 作为 L0、单 Workspace 暴露假设与默认 `/today` 心智入口不再兼容。

## 2. Product / Definition Check

本变更服务：

- `CAP-01` Learning Context & Material Grounding；
- `CAP-04` Adaptive Learning Activity；
- `CAP-07` Learning Continuity & Next-step Orientation；
- `PD-REQ-0401`、`PD-REQ-0701..0703`；
- `PD-RULE-002` Conversation != Learning Evidence；
- `PD-RULE-009` Workspace Is a Real Product Scope。

结论：无 `STRATEGY GAP`、`POSITIONING GAP` 或一级 Capability 变化。

`Workspace` 已在 Product Definition 中作为正式 Product Object 暴露，`LearningProject` 也独立存在。因此必须冻结以下语言边界：

```text
用户界面词汇：课程
canonical product/domain/API/persistence identity：Workspace
LearningProject：Workspace 内可选的组织对象，不与“课程”互换、不被本 IA 删除
```

这属于 Experience vocabulary 与 IA 变化，不改变 Core Product Object meaning，因此不需要修改 `PRODUCT-DEFINITION.md`。若未来要求数据库/API/domain 将 `Workspace` 重命名为 `Course`，将形成独立 `PRODUCT DEFINITION GAP` / system migration，不属于本次授权。

## 3. Gap Matrix

| Area | Current before change | Frozen direction | Disposition |
|---|---|---|---|
| L0 navigation | Today / Learning / Library | Course list/context + Library | `Today` REMOVE；`Learning` REMOVE；Library KEEP |
| Primary create entry | 无一级 Course action | `＋ 新课程` | ADD as primary `Action`, never Navigation |
| Workspace vocabulary | UI 显示 Workspace / 默认工作区 | 用户侧统一「课程」 | AMEND vocabulary only |
| Default entry | `/today` / Today continuation | recent Course + Activity；无 Course 时 Course Empty State | SUPERSEDE mental entry |
| Learning workspace | Learning L0 之下 | Course context 之下 | KEEP three-column responsibilities |
| Activity organization | current activity + plan/context flows | one Course → many LearningActivity | ADD Activity Switcher / Recent Learning |
| Conversation | Activity interaction mode | unchanged | KEEP；不得成为 chat-thread manager |
| Library | L0 Product Domain | stable navigation | KEEP |
| Settings / Recovery | Utility | Utility | KEEP |
| Workspace switching | canonical context；UI 当前 `SINGLE_WORKSPACE` | real multi-Course switch | DESIGN FROZEN；technical command/query `SPEC GAP` |
| Course creation | WSP permits Workspace create surface, UI 未冻结 flow | create Course → material → goal → first Activity | DESIGN FROZEN；real command/readiness dependency |
| Legacy routes | `/today`、`/learning` stable | compatibility only | MIGRATE without business side effect |

## 4. Current Implementation Evidence

当前 frontend 仍包含明显旧 IA：

- `Sidebar.jsx` 仍把 `/today`、`/learning`、`/library` 作为三个一级导航；
- `Today.jsx`、`LearningWorkspace.jsx`、`TutorWorkspace.jsx`、`Welcome.jsx` 仍把 Today 作为默认返回/继续入口；
- `Learning.jsx` 仍跳转 `/learning/goals`；
- `LearningNavigation.jsx` 仍暴露 Goal / Path / Progress / History 四个学习域导航；
- `ActivityLearning.jsx`、`Unavailable.jsx` 与多项测试仍把 `/learning/plan` 或 `/today` 作为回退；
- `WorkspaceContext` / ADR-0019 query 仍只支持单一 default Workspace，尚无真实 Course list/create/switch UI contract。

这些是 `DESIGN–IMPLEMENTATION GAP`，不能用现有代码反向保留旧 IA。

## 5. Closure Required Before Implementation

1. 创建并接受 Course-centric IA ADR；
2. 将 current Experience 与 current-only UI Specs 收敛为单一 truth；
3. 为 Workspace list/create/current/switch、冲突恢复与 Activity list/resume 冻结 owner-safe technical contract；
4. 在 Linear 中将设计冻结、平台前置、前端实现、route migration、regression/accessibility 分开；
5. 只有真实 create/switch command 可用后，前端才可暴露 `＋ 新课程` 与多课程切换，禁止 placeholder 或 frontend-only truth。

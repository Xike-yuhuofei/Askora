# UI-01 Learning Shell and Compatibility Tutor Workspace Vertical Slice

> 状态：Frozen
> 实现入口：EXEC-015
> 冻结日期：2026-08-08
> 范围：登录修复、全局 Shell、今天、兼容导师工作台、历史、设置、只读 Today Query

## 1. Objective

在不新增 LearningGoal/Activity command、不伪造 activity/session link、不改变八系统 ownership 的前提下，把 Askora 从 chat-first 首页迁移为 learning-loop-first Shell，并让现有 dialog session 作为明确标记的兼容快速学习工作台继续通过 canonical dialog facade 可用。

## 2. End-to-End Path

```text
phone auth / explicit dev auto-login
→ GET /api/v1/workspace/today
→ honest SYS06 unavailable + SYS07 due projection + legacy session summary
→ compatibility quick start / resume existing dialog session
→ /quick/:sessionId tutor workspace
→ existing canonical dialog normal/history/SSE path
→ RichMessageV1 rendering
→ /history reload and resume
```

`/learn/:activityId` 在没有 canonical activity/session link 时只显示不可启动状态。它 MUST NOT 创建 legacy session 或把 `activityId` 当 `sessionId`。

## 3. Current Reality and Baseline

- 当前 `/` 直接进入硬编码 subject picker/chat；一级导航是对话、知识点、画像、账号。
- 当前 dialog session 有 current-user ownership、持久化消息和 canonical dialog facade，但没有 canonical LearningActivity/session link。
- `LearningPlanRecord`/`LearningActivityRecord` 当前没有可供 UI Query 安全绑定当前用户的公开 Goal/Activity query contract；UI-01 不读取这些表并猜测 ownership。
- ReviewSchedule 与 MasteryEstimate 已有 current-user owner key，可只读查询；Today 当前没有关联 activity，因此不选择某个 mastery entry 作为“当前证据”。
- `Login.jsx` 引用了未导入的 `User` icon，登录页运行时会白屏。
- 冻结前基线：frontend 11 tests PASS、production build PASS、npm high audit 0；backend 249 passed / 1 skipped。

## 4. Scope

IN：

- 修复 login render blocker，并增加 render/validation test；
- light design tokens、Standard/Workspace Shell、responsive navigation；
- canonical routes `/today`、`/history`、`/settings`、`/learn/:activityId`；
- compatibility route `/quick/:sessionId` 与显式 source/retirement label；
- `/goals`、`/path`、`/library`、`/evidence` 的 honest not-yet-available 状态，不实现 UI-02 数据能力；
- legacy redirects `/`、`/profile`、`/knowledge`、`/account`；
- `GET /api/v1/workspace/today` v1.0 strict read envelope；
- Today 展示 ReviewDue candidate 与 compatibility recent sessions；
- existing dialog session create/list/detail/messages/send/SSE 与 RichMessage 复用；
- History 与 Settings 迁移；
- desktop、768px、360px、keyboard/focus/accessibility tests。

OUT：

- LearningGoal create/confirm/pause/resume；
- canonical activity launch/link command/query；
- LearningPlan edit/reorder/replan；
- Focus mode、dark theme、knowledge map、evidence profile；
- mastery product label、front-end mastery threshold；
- database migration、新生产依赖、外部 telemetry；
- TeachingAction/Assessment/LearnerState/ReviewSchedule 写语义变化。

## 5. Today Query Contract

`GET /api/v1/workspace/today?timezone=<IANA timezone>` MUST：

- 绑定当前授权用户；
- 返回 `schema_version=1.0`、timezone-aware `generated_at`、`correlation_id`；
- 对 SYS06 返回 `MISSING + OWNER_QUERY_UNAVAILABLE`，不得跨用户扫描 plan/activity；
- 只把 SYS07 `next_due_at <= now` 的 latest schedule 投影为 due candidate，不修改 schedule；
- 对没有 current activity 的 SYS03 evidence summary 返回 null + reason，而非任意挑选 mastery entry；
- compatibility recent sessions 只来自当前用户，明确 `LEGACY_COMPATIBILITY`；
- 使用稳定排序与 `Cache-Control: private, no-store`。

## 6. Ownership and Security

- Workspace API handler 只做 auth、timezone validation、query invocation、serialization 与 cache header。
- `app.queries.workspace` 是只读 application query，不写 owner state，不创建第二 workspace truth。
- UI 不读取/显示 legacy dialog mastery、strategy、hint level 作为 canonical evidence/action。
- `/quick/:sessionId` 的 detail/messages/send 继续依赖现有后端 ownership check。
- 客户端 cache 在 logout/401 时清除，不保存 canonical learning state。

## 7. Failure and Empty Semantics

- 无 Goal/Plan/Activity：Today 显示诚实空态与兼容快速学习，不生成假计划。
- 无到期复习：显示“暂无到期复习”，不表示无需复习或已掌握。
- Today query 局部 source missing：保留其他可用区，显示 PARTIAL。
- `/learn/:activityId` 无 link：显示 `REQUIRES_START_COMMAND`，无副作用。
- dialog session 不存在/无权限/ended：沿用稳定错误与只读/恢复语义，不将系统错误记为学习失败。

## 8. Acceptance Criteria

- `UI01-VSLICE-AC-001`：一级导航为今天、学习目标、学习路径、资料库、学习证据、历史记录、设置，不含“对话学习”。
- `UI01-VSLICE-AC-002`：legacy routes 无副作用跳转到 canonical routes。
- `UI01-VSLICE-AC-003`：Today Query 只读、current-user scoped、严格 v1.0、source/version/availability 可审计。
- `UI01-VSLICE-AC-004`：SYS06 unavailable、ReviewDue candidate 与 compatibility session 语义不混淆。
- `UI01-VSLICE-AC-005`：`/quick/:sessionId` 复用 canonical dialog/history/RichMessage，且不伪造 LearningActivity/TeachingAction/evidence。
- `UI01-VSLICE-AC-006`：`/learn/:activityId` 无 link 时不可启动且无 legacy shortcut。
- `UI01-VSLICE-AC-007`：登录页可渲染，正式手机号登录与 explicit dev auto-login 边界保持。
- `UI01-VSLICE-AC-008`：历史与设置可用；退出只清除本地 session，不声称删除服务端学习数据。
- `UI01-VSLICE-AC-009`：1440/1024/768/360、keyboard/focus、loading/empty/partial/error/unauthorized 关键状态通过验证。
- `UI01-VSLICE-AC-010`：frontend tests/build/audit、backend targeted/full/ruff/mypy/alembic、docs/diff gates 通过。
- `UI01-VSLICE-AC-011`：无新 production dependency、DB migration、cross-owner write、blocking SPEC GAP。
- `UI01-VSLICE-AC-012`：UI 工程/合同/可访问性声明与 Learning Evidence Gate 分开，保持 `LEARNING_EVIDENCE_INSUFFICIENT`。

## 9. Gate

只有 `UI01-VSLICE-AC-001..012` 全部满足时 UI-01 为 DONE。若 canonical activity link 被当作当前 Slice 的必需能力，则必须 `BLOCKED_BY_SPEC_GAP`；不得通过 session/activity ID 混用绕过。

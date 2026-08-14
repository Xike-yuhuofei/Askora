# 学习活动（`/courses/:workspaceId/activities/:activityId`）

> **页面职责**：空间内一段具体 `LearningActivity` 的执行画布——定向 → 作答 → 反馈 → 帮助/来源 → 完成/下一步。是 `EXP-JOURNEY-003` 的主载体（与右栏 Notes/Material 构成三栏画布）。
> **对应旅程**：`EXP-JOURNEY-003`（在对话里学习）
> **对应契约**：`UI-LEARN-001~003`、`UI-LRN-010/020~042/050~064`、`UI-SHELL-003/004`、`LEARNING-EXPERIENCE.md` 全部
> **现状基准**：`apps/frontend/src/pages/ActivityLearning.jsx`（已中文、教学语义基本完整）

---

## 1. 页面目标

1. 用户进入即知道：在哪个空间、这个活动要完成什么、为什么现在做（`LEXP-010`）。
2. 提供真实作答路径（Attempt），Feedback 与系统错误明确分离（`LEXP-FB-001`）。
3. 需要时请求帮助 / 查看原文；帮助状态（独立/已用帮助/已暴露/待验证）可读（`LEXP-AST-002`）。
4. 完成后诚实进入下一步：下一项 / 完成本项 ≠ 已掌握（`LEXP-NEXT-003`）。

**不做什么**：不让「看完解释/点懂了」充当证据（`LEXP-012`）；不把系统故障显示成「你答错了」（`UI-LRN-051`）。

## 2. 布局区划（三栏画布中的中央 Learn）

```
┌───────────────────────────────────────────────┐
│ [返回学习路径] eyebrow「学习活动」+ h1 活动标题 · 约 N 分钟 │
├───────────────────────────────────────────────┤
│ 教学/问题区：Teaching content + Question（明确 task boundary）│
│ Learner 作答区：[写你的理解…] + [发送]                    │
│ Feedback / 帮助状态（独立作答 · 已使用帮助 · 待独立验证）        │
│ 引用/来源（Disclosure）                            │
│ Learning Context Drawer（收起一行方向 → 展开 stage/next）│
├───────────────────────────────────────────────┤
│ [开始学习] [完成本项] [进入下一项]                       │
│ [刷新]                                           │
└───────────────────────────────────────────────┘
右栏：学习笔记 / 当前资料（见 RightRail 规划，归属 workspace-context/RightRail）
```

## 3. 元素清单

### 3.1 头部与定向

| # | 元素 | 类型 | 文案 | 交互语义 | 层级 | 组件/Token | 状态 |
|---|---|---|---|---|---|---|---|
| AL-01 | 返回 | 链接 | 学习路径（aria「返回学习路径」） | Navigation | — | Link | — |
| AL-02 | eyebrow | 文本 | 学习活动 | — | — | text-muted | — |
| AL-03 | 主标题 | 文本 h1 | 活动标题 | — | — | text-primary | — |
| AL-04 | 时长 | 文本 | 约 N 分钟 | — | — | text-muted | — |
| AL-05 | 开始学习 | 按钮 | 开始学习 / 进入本次学习 | **Action**（launch 该 Activity） | Primary（未开始时） | Button primary | LOADING/DISABLED+原因 |

### 3.2 学习内容区（`UI-LRN-010` Required Regions）

| # | 元素 | 类型 | 文案 | 交互语义 | 层级 | 组件/Token | 状态 |
|---|---|---|---|---|---|---|---|
| AL-10 | 教学/问题 | 内容块 | 当前教学内容；问题有明确 task boundary（`UI-LRN-030`） | InteractiveContent | — | Rich content（`UI-DS-RICH-001`） | READY/STREAMING(部分帧不作 final) |
| AL-11 | 作答输入 | 输入 | label「写下你的想法」placeholder「写下你的理解…」 | Control | — | Composer（`UI-DS-COMP-051`） | DEFAULT/READ_ONLY/DISABLED |
| AL-12 | 发送 | 按钮 | 发送 | **Action**（提交 Attempt，`UI-LRN-041`） | Primary（作答上下文） | Button secondary | DISABLED(空)/LOADING(single-flight) |
| AL-13 | Feedback | 内容块 | 哪部分成立 / 哪部分要改 / 为什么 / 下一步 | StatusFeedback/Content | — | Feedback block | 文本+语义，非仅对错色 |
| AL-14 | 帮助请求 | 按钮 | 给一点提示 / 解释概念 / 给例子 / 拆成步骤 | **Action**（request，`UI-LRN-062`） | Contextual | Button ghost | 帮助状态随之更新 |
| AL-15 | 帮助状态 | 状态标签 | 独立作答 / 已使用帮助 / 已看到关键步骤 / 已暴露答案 / 待独立验证 | StatusFeedback | — | Badge（`UI-DS-COMP-040`） | 来自 actual，不推断（`UI-LRN-061`） |
| AL-16 | 引用/来源 | Disclosure | 查看原文 / 依据 N 处 | Disclosure/Navigation | Contextual | Disclosure → Right Rail Current Material | LOADING/不可用「来源不可用」（`UI-LRN-083`） |
| AL-17 | 复制 | 按钮 | 复制 / 已复制（Copy/Check icon，aria 补齐） | Control | Contextual | Button ghost | DEFAULT/SUCCESS |
| AL-18 | 系统错误 vs 学习反馈 | Alert | 教学服务暂时不可用，活动仍保持原状态。可重试。 | StatusFeedback(ERROR) | — | Alert tone=error | 系统错误专用，不与「答错」混淆 |

### 3.3 Learning Context Drawer（`UI-LRN-110~115`）

| # | 元素 | 类型 | 文案 | 交互语义 | 层级 | 组件/Token | 状态 |
|---|---|---|---|---|---|---|---|
| AL-20 | 收起态 | 一行文本 | 当前阶段 · 接下来：…… | Disclosure | — | Drawer collapsed | LOADING/READY/MISSING/PARTIAL/STALE/ERROR |
| AL-21 | 展开态 | 内容 | 当前阶段 / 阶段目标 / 接下来 1–3 个方向 | Disclosure | — | Drawer expanded | 内容来自 canonical query，前端不推断（`UI-LRN-114`） |

### 3.4 完成/下一步

| # | 元素 | 类型 | 文案 | 交互语义 | 层级 | 组件/Token | 状态 |
|---|---|---|---|---|---|---|---|
| AL-30 | 完成本项 | 按钮 | 完成本项（CheckCircle2） | **Action**（`CompleteLearningActivityV1`） | Secondary | Button secondary | LOADING/失败可重试 |
| AL-31 | 完成提示 | 文本 | 本项已完成。这不会自动更新掌握度或目标达成状态。 | StatusFeedback | — | text-muted | 完成后显示 |
| AL-32 | 进入下一项 / 返回学习路径 | 按钮 | 进入下一项 / 返回学习路径 | Navigation | Secondary | Button secondary | 按 owner 是否给真实下一步 |

## 4. 状态矩阵

| 区域 | LOADING | EMPTY/未开始 | READY | PARTIAL | STALE | ERROR |
|---|---|---|---|---|---|---|
| 活动加载 | 正在恢复这项学习活动… | 从一个聚焦问题开始 | 可作答 | 活动状态变化已刷新 | 计划已更新，返回学习路径查看 | 无法打开学习活动 + 重试 |
| 作答提交 | 发送 LOADING | — | 新 Attempt 保留 | — | — | 提交失败不丢输入，可重试（`UI-LRN-041`） |
| 流式回应 | streaming 帧 | — | final payload 校验后渲染 | 半成品结构化不作 final（`UI-LRN-071`） | — | 教学回应未完成，活动保持进行中，可重试 |
| 完成 | 完成 LOADING | — | 完成态 + 真实下一步 | — | — | 完成状态没有保存；活动保持进行中，可重试 |
| 不可执行 | — | 当前活动不可执行 | — | — | — | 请返回学习路径查看最新安排 |

## 5. 无障碍

| # | 要求 |
|---|---|
| A-01 | 阅读顺序：Activity 上下文 → 教学/问题 → 作答输入 → Feedback/状态 → Composer/动作 → Drawer → 右栏（`UI-LRN-130`）。 |
| A-02 | 流式更新用受限 live region，避免逐 token 播报（`UI-LRN-131`）。 |
| A-03 | icon-only（复制/发送）有 accessible name（`UI-DS-A11Y-004`）。 |
| A-04 | Drawer/右栏/弹层键盘可达，Escape 关闭，关闭后 focus 返回（`UI-LRN-132`）。 |
| A-05 | 帮助/暴露/验证状态有文本表达，非仅颜色（`UI-DS-TOK-004`）。 |
| A-06 | 上下文帮助请求不依赖 hover；focus-visible 等价可达。 |

## 6. 禁止事项（`UI-LRN-016` / `UI-LRN-` Forbidden 精简）

- 「我懂了/完成本项」不得当作 LearningEvidence（`LEXP-012`）。
- 系统错误（模型/工具/检索/网络）不得显示成「你答错了」（`UI-LRN-051`）。
- 不得用 frontend threshold 推断 mastery/assistance（`UI-LRN-061/064`）。
- 流式半成品不得当最终卡/评估；断线重连不重复消息/Attempt（`UI-LRN-073`）。
- 缺原文时不得用 filename/summary 伪装原文（`UI-LRN-083`）；跨空间 source fail closed（`UI-LRN-084`）。
- 中途离开/切换空间不得静默丢 draft/stream/note（`LEXP-CONT-004`）。

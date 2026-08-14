# 学习路径（`/learning/plan`，兼容/上下文页）

> **页面职责**：在明确 user job 下查看当前学习路径（目标下的活动序列、路径依据、版本事实）。按规划器发布顺序只读展示；不在前端重新规划。
> **对应契约**：`UI-ROUTE-004`（plan explanation）、`UI-DATA-041/042`、`INT-MAP-003`、`UI-DATA-003`
> **现状基准**：`apps/frontend/src/pages/LearningPath.jsx`（已中文、诚实）

---

## 1. 页面目标

1. 选择一个目标（存在多个当前 plan 时**不替你猜选**，`UI-DATA-042`），查看其活动序列。
2. 诚实呈现路径状态与缺失（objective 元数据未发布时保留 ref、不做推断）。
3. 活动「继续学习 / 开始学习」进入对应 Activity（`StartLearningActivityV1`，available 不自动 start）。

**不做什么**：不在前端重新排序/规划（服务端顺序是展示基线）；不是核心旅程常驻页。

## 2. 布局区划

```
┌──────────────────────────────────────────────┐
│ [LearningNavigation 常驻分面 — 冲突，见 §6]          │
├──────────────────────────────────────────────┤
│ eyebrow「当前计划」+ h1「学习路径」                  │
├──────────────────────────────────────────────┤
│ 请选择要查看的目标 [select]                      │
│ 路径依据（fact-grid：计划状态/学习者状态版本/图谱版本/复习版本）│
├──────────────────────────────────────────────┤
│ h2 学习活动（活动 rows：标题 · 时长 · 状态）         │
│   [继续学习 / 开始学习]                        │
│ 空态：还没有可展示的学习路径                       │
└──────────────────────────────────────────────┘
```

## 3. 元素清单

| # | 元素 | 类型 | 文案 | 交互语义 | 层级 | 组件/Token | 状态 |
|---|---|---|---|---|---|---|---|
| LP-01 | eyebrow | 文本 | 当前计划 | — | — | text-muted | — |
| LP-02 | 主标题 | 文本 h1 | 学习路径 | — | — | text-primary | — |
| LP-03 | 目标选择 | select | label「学习目标」；默认 option「选择目标」 | Selection | — | Select | DEFAULT |
| LP-04 | 多计划提示 | 文本 | 存在多个当前计划，Askora 不会替你猜选其中一个。 | StatusFeedback | — | text-muted | 多 plan 时显示 |
| LP-05 | 路径状态 pill | 状态标签 | 路径可用 / 部分信息可用 / 暂无路径 | StatusFeedback | — | Badge | READY/PARTIAL/EMPTY |
| LP-06 | 路径依据 | 事实网格 | 计划状态 / 学习者状态版本 / 知识图谱版本 / 复习计划版本 | StatusFeedback | — | Fact list | MISSING 诚实 |
| LP-07 | 说明 | 文本 | 按规划器发布的顺序查看活动；这里不会在前端重新规划。 | — | — | text-muted | — |
| LP-08 | 区域标题 | 文本 h2 | 学习活动 | — | — | text-primary | — |
| LP-09 | 活动行 | row | 活动标题 · 约 N 分钟 · 状态 | InteractiveContent | — | Row（`UI-DS-COMP-024`） | DEFAULT/HOVER/FOCUS |
| LP-10 | 继续学习 / 开始学习 | 按钮（ArrowRight） | 继续学习 / 开始学习 | **Action**（resume / `StartLearningActivityV1`） | Secondary | Button secondary | available 不自动 start；LOADING |
| LP-11 | 元数据缺失说明 | 文本 | 学习目标的细分能力与认知过程尚未由规划系统发布；当前保留可追踪关系，不做推断。 | StatusFeedback | — | text-muted | objective 元数据缺失 |
| LP-12 | 空态 | 文本+按钮 | 还没有可展示的学习路径 +「这不表示目标已完成；当前没有 owner 发布的活动计划。」+ [查看学习目标] | StatusFeedback(EMPTY)+Navigation | — | Empty pattern | EMPTY |
| LP-13 | 活动空态 | 文本 | 计划存在，但当前没有可展示的活动。 | StatusFeedback | — | 文本 | plan 有、activities 空 |

## 4. 状态矩阵

| 区域 | LOADING | EMPTY | READY | PARTIAL | STALE | ERROR |
|---|---|---|---|---|---|---|
| 路径加载 | 正在读取学习路径… | 还没有可展示的学习路径 | 活动序列 | 部分信息可用（objective 缺失） | 版本过期提示 | 学习路径暂时无法读取。+ 重试 |
| 目标选择 | — | 选择目标 | 单选目标 | 多 plan 需明确选择 | — | — |
| 活动启动 | 启动 LOADING | — | 进入活动 | — | — | 启动失败，可重试 |

## 5. 无障碍

| # | 要求 |
|---|---|
| A-01 | 目标 select 有 label；活动行主点击与「继续学习」独立 focus target。 |
| A-02 | 路径状态非仅颜色；缺失项文本表达。 |
| A-03 | available 活动不因点击行自动 start（start 需显式按钮，`UI-DS-COMP-024`）。 |

## 6. 禁止事项与现状 GAP

| GAP | 处理 |
|---|---|
| LearningShell 常驻「目标/路径/进展/历史」分面导航 | 同 goals.md：改为上下文入口或移除常驻分面（`EXP-IA-003`）。 |
| 产品名「Askora」出现于多 plan 提示 | 改为中性表达，如「存在多个当前计划，系统不会替你猜选其中一个。」 |

禁止：按 priority 前端重排并称为 canonical plan（`UI-DATA-042`）；从章节顺序推断 prerequisite；从 chat/轮次推断进度（`UI-DATA-003`）；导航隐式改 plan（`UI-ROUTE-005`）。

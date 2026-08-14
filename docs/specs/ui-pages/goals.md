# 学习目标（`/learning/goals`，兼容/上下文页）

> **页面职责**：**兼容/上下文**入口——在明确 user job 下查看、创建、确认可测学习目标（`UI-ROUTE-004` 允许 explicit goal create/correct/audit）。**不是空间常驻管理，也不在核心旅程主路径**（`EXP-IA-003`）。
> **对应契约**：`UI-NAV-003`、`UI-ROUTE-004`、`INT-MAP-003`、`UI-DATA-040`
> **现状基准**：`apps/frontend/src/pages/Goals.jsx`（已中文、文案诚实；含 LearningShell 常驻导航冲突，见 §6）

---

## 1. 页面目标

1. 用户明确要「查看/创建学习目标」时可达：列表当前目标，状态与事实诚实（`UI-DATA-040`）。
2. 目标由系统按 `PD-RULE-004` 维护；本页只做**明确的**目标创建/查看，不进入核心旅程。
3. 空态/缺失不伪装 READY。

**不做什么**：不成为空间 landing 的常驻 facet；主路径不要求用户确认目标（`EXP-JOURNEY-001`）。

## 2. 布局区划

```
┌──────────────────────────────────────────────┐
│ [LearningNavigation 常驻分面：目标/路径/进展/历史 — 冲突，见 §6]│
├──────────────────────────────────────────────┤
│ eyebrow「目标管理」+ h1「学习目标」+ 一句说明          │
├──────────────────────────────────────────────┤
│ h2「当前目标」                                  │
│   · 目标行：标题 + 状态 pill + 事实网格              │
│   · [查看目标] [查看路径]                        │
│   · 空态：还没有学习目标 + [创建目标][前往资料库]       │
└──────────────────────────────────────────────┘
```

## 3. 元素清单

| # | 元素 | 类型 | 文案 | 交互语义 | 层级 | 组件/Token | 状态 |
|---|---|---|---|---|---|---|---|
| GO-01 | eyebrow | 文本 | 目标管理 | — | — | text-muted | — |
| GO-02 | 主标题 | 文本 h1 | 学习目标 | — | — | text-primary | — |
| GO-03 | 说明 | 文本 | 定义可测目标，明确资料与学习重点，再安全生成学习路径。 | — | — | text-secondary | — |
| GO-04 | 创建目标 | 按钮（Plus） | 创建目标 | Navigation（→ 目标编辑器） | Primary | Button primary | DEFAULT |
| GO-05 | 区域标题 | 文本 h2 | 当前目标 | — | — | text-primary | — |
| GO-06 | 目标行 | row | 目标标题 | InteractiveContent | — | Row | DEFAULT/HOVER/FOCUS |
| GO-07 | 状态 pill | 状态标签 | 待确认 / 已确认 / 进行中 / 已达成 / 已暂停 / 已归档 | StatusFeedback | — | Badge | 文本+语义 |
| GO-08 | 事实网格 | 文本 | 目标能力 / 成功标准 / 时间安排 / 当前版本；每周 N 分钟 · 未设置每周时间 · 未设置截止时间 | StatusFeedback | — | Fact list | MISSING 诚实显示「未设置」 |
| GO-09 | 查看目标 | 按钮 | 查看目标 | Navigation（→ 目标详情） | Secondary | Button secondary | — |
| GO-10 | 查看路径 | 按钮（ArrowRight） | 查看路径 | Navigation | Secondary | Button secondary | — |
| GO-11 | 空态 | 文本+按钮 | 还没有学习目标 +「从已有资料定义一个可测目标；未就绪资料仍可保存到草稿。」+ [创建目标][前往资料库] | StatusFeedback(EMPTY)+Action | — | Empty pattern | EMPTY |
| GO-12 | 计数 | 文本 | N 个目标 | — | — | text-muted | — |

## 4. 状态矩阵

| 区域 | LOADING | EMPTY | READY | PARTIAL | STALE | ERROR |
|---|---|---|---|---|---|---|
| 目标列表 | 正在读取学习目标… | 还没有学习目标 | 目标 rows | — | 未就绪资料标「可存草稿」 | 学习目标暂时无法读取。+ 重试 |

## 5. 无障碍

| # | 要求 |
|---|---|
| A-01 | 目标行与「查看目标」独立 focus target。 |
| A-02 | 状态 pill 非仅颜色；事实网格缺失项有「未设置」文本。 |
| A-03 | 空态动作可达；错误 `role="alert"`。 |

## 6. 禁止事项与现状 GAP

| GAP | 处理 |
|---|---|
| LearningShell 常驻「目标/路径/进展/历史」分面导航 | 违反 `EXP-IA-003`（Goal/Plan/Progress 常驻管理）。**规划**：这四个页面仅作为兼容/上下文入口可达，顶部改为上下文面包屑或目标流内部步骤，不做常驻 product facet；否则删除常驻导航。 |
| 主路径出现目标 | 目标只在这类明确 job 下进入；核心旅程（Welcome→资料→对话）不出现。 |

禁止：由导航/route 变化触发隐式目标创建/确认（`UI-ROUTE-005`）；用前端推断填充目标字段（`UI-DATA-003`）；把空态伪装成无目标 ≠ 已完成。

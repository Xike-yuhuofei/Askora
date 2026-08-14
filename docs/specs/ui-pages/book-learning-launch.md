# 用资料开始学习（`/book-learning/:documentId`）

> **页面职责**：从某份已就绪资料进入首段学习的准备流程——确认起点（不计分诊断）→ 给出本次学习安排 → 开始首段对话。对应 `EXP-JOURNEY-001` 的收尾段。
> **对应旅程**：`EXP-JOURNEY-001`（用资料开始学习）、`EXP-JOURNEY-003`（进入对话）
> **对应契约**：`UI-COURSE-002`、`LEXP-010`（Orientation）、`LEXP-011/012`（真实作答、Attempt 先于证据）
> **现状基准**：`apps/frontend/src/pages/BookLearningLaunch.jsx`（已中文、结构完整）

---

## 1. 页面目标

1. 恢复/准备该资料的 readiness（资料、目标、起点检查、本次学习）。
2. 用**不计分的起点诊断**调整学习起点，不要求用户理解 Goal/Plan 内部对象。
3. 呈现「本次学习」的聚焦问题与下一步，用户可**真实作答**后「开始本次学习」进入对话。

**不做什么**：不把「明确学习目标」写成用户步骤（`UI-COURSE-002`）；「采纳学习目标」是系统流程的诚实呈现，不是目标管理页；诊断不计分（`INT-STATE-001`）。

## 2. 布局区划

```
┌──────────────────────────────────────────┐
│ [返回资料库]  eyebrow「资料学习」+ h1 本次主题      │
│ 进度步骤：准备 → 起点 → 本次学习                    │
├──────────────────────────────────────────┤
│ 起点诊断（不计分 · 用于调整学习起点）                │
│   问题「选择一个答案」+ 单选 / 你的回答 [input]       │
│   [提交并继续]                                  │
├──────────────────────────────────────────┤
│ 本次学习                                     │
│   聚焦问题 + 教学区 [写下你的想法或问题…] + [发送]    │
│   依据资料 · N 处（Disclosure） · 约 N 分钟         │
├──────────────────────────────────────────┤
│ [开始本次学习 · primary]                        │
│ [重新检查] [技术详情]                            │
└──────────────────────────────────────────┘
```

## 3. 元素清单

| # | 元素 | 类型 | 文案 | 交互语义 | 层级 | 组件/Token | 状态 |
|---|---|---|---|---|---|---|---|
| BL-01 | 返回 | 链接 | 资料库（aria「返回资料库」） | Navigation | — | Link | — |
| BL-02 | eyebrow | 文本 | 资料学习 | — | — | text-muted | — |
| BL-03 | 主标题 | 文本 h1 | 学习主题 /「开始一段有目标的学习」 | — | — | text-primary | — |
| BL-04 | 进度步骤 | 文本 | 准备 / 起点 / 本次学习 | StatusFeedback | — | Steps | current 态清晰 |
| BL-05 | 诊断说明 | 文本 | 不计分 · 用于调整学习起点 | StatusFeedback | — | text-muted | — |
| BL-06 | 诊断问题 | 单选 | 选择一个答案（legend） | Selection | — | Radio（`UI-DS-COMP-060`） | DEFAULT/SELECTED |
| BL-07 | 你的回答 | 输入 | 你的回答 | Control | — | Input | DEFAULT |
| BL-08 | 提交并继续 | 按钮 | 提交并继续 / 提交中 | **Action** | Secondary | Button secondary | DISABLED(未答)/LOADING |
| BL-09 | 本次学习标题 | 文本 h2 | 本次学习 | — | — | text-primary | — |
| BL-10 | 教学输入 | 输入 | label「写下你的想法或问题」placeholder「写下你的想法或问题…」 | Control | — | Composer（`UI-DS-COMP-050/051`） | DEFAULT/READ_ONLY |
| BL-11 | 发送 | 按钮（Send icon） | 发送 | Action | Secondary | Button secondary | DISABLED(空)/LOADING |
| BL-12 | 依据资料 | Disclosure | 依据资料 · N 处 | Disclosure | Contextual | Disclosure | LOADING/READY/不可用时「来源不可用」 |
| BL-13 | 时长 | 文本 | 约 N 分钟 | — | — | text-muted | — |
| BL-14 | 开始本次学习 | 按钮 | 开始本次学习 / 开始中 | **Action**（进入首段对话） | Primary | Button primary | LOADING/disabled+原因 |
| BL-15 | 重新检查 | 按钮 | 重新检查 | Action（重跑 readiness） | Secondary | Button ghost | LOADING |
| BL-16 | 技术详情 | Disclosure | 技术详情（readiness.state 等，Advanced） | Disclosure | Advanced | Disclosure（`INT-H-004`） | — |
| BL-17 | 持久化提示 | 文本 | 学习记录已保存，刷新页面也可以继续。 | StatusFeedback | — | text-muted | 进入可恢复状态后显示 |

## 4. 状态矩阵（各准备步骤）

| 步骤 | LOADING | READY | PARTIAL/恢复 | ERROR |
|---|---|---|---|---|
| 恢复进度 | 正在恢复你的学习进度… | 正常 | — | 暂时无法打开这份资料 |
| 目标 | 正在恢复你的目标… | — | — | 步骤失败：准备步骤没有在预期范围内完成。你的进度已经保留，请重试。 |
| 起点检查 | 正在恢复基础检查… | 诊断可作答 | — | 学习准备暂时没有完成。已完成的进度不会丢失。 |
| 本次学习 | 正在为你准备下一步… | 聚焦问题可作答 | 正在根据资料安排学习 / 正在安排学习起点 | 暂时无法继续 |

stateMeta 诚实表达（`EXP-PARSE-003`）：正在准备这份资料 / 这份资料还不能开始学习 / 正在根据资料安排学习 / 正在采纳学习目标 / 正在安排学习起点 / 先看看你的起点 / 正在安排第一节学习 / 本次学习已经准备好 / 暂时无法继续。

## 5. 无障碍

| # | 要求 |
|---|---|
| A-01 | 进度步骤有 `aria-current="step"`；诊断单选为 fieldset/legend。 |
| A-02 | 教学区 Composer label 完整（可 visually-hidden 但不得仅用 placeholder，`UI-DS-COMP-050`）。 |
| A-03 | 每一步 loading/error 有 live 播报；error 附重试且不丢已保存进度。 |
| A-04 | 「开始本次学习」pending 时 single-flight、`aria-busy`；成功后 focus 落到对话 h1。 |
| A-05 | 依据资料/技术详情为 Disclosure，键盘可展开。 |

## 6. 禁止事项

- 不得把「明确学习目标」变成用户步骤（`UI-COURSE-002`）。
- 诊断不得计入分数、不得伪装成已掌握；「采纳学习目标」是系统流程，不是目标管理（`INT-MAP-003`）。
- 缺模型时不得用 mock 对话冒充学习（`EXP-PARSE-003`）。
- 中途失败不得静默丢进度；刷新可继续（`LEXP-CONT-004`）。
- 不伪造 plan/evidence；下一步只能来自 owner 发布的真实状态（`UI-DATA-003`）。

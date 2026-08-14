# 目标详情（`/learning/goals/:id`，兼容/上下文页）

> **页面职责**：查看单个目标定义、成功标准、达成证据与验证义务；在明确 user job 下执行修订/暂停/恢复/归档/复制/验证动作。
> **对应契约**：`UI-ROUTE-004`（explicit goal audit）、`INT-MAP-003`、`LEXP-015`（独立验证）、`UI-DATA-040`
> **现状基准**：`apps/frontend/src/pages/GoalDetail.jsx`（已中文、证据语义诚实）

---

## 1. 页面目标

1. 诚实呈现目标定义版本、成功标准与达成证据状态（`MISSING/低置信`不伪装）。
2. 提供验证义务入口：安排验证 → 提交独立回答 → 检查达成门禁 → **由用户最终确认达成**（系统不自行宣布）。
3. 修订/暂停/归档/复制等目标动作仅在明确 job 下出现（`INT-H-003` Contextual）。

**不做什么**：「目标已确认达成」不等同 mastery 或真人学习效果证明（现状已有诚实声明，保留）；主路径不出现。

## 2. 布局区划

```
┌──────────────────────────────────────────────┐
│ [返回]  eyebrow「目标定义 vN」+ h1 目标标题           │
│   [修订目标][暂停/恢复][归档][复制为新目标]（Contextual）  │
├──────────────────────────────────────────────┤
│ 事实网格：目标能力/应用场景/每周预算/截止时间              │
├──────────────────────────────────────────────┤
│ h2 成功标准                                    │
│ h2 达成证据 · 状态（等待延迟验证/可以作答/评分已接纳/…）    │
│   验证任务：[安排成功标准验证] [提交验证]              │
│   [检查达成门禁] [由我确认目标达成]                   │
└──────────────────────────────────────────────┘
```

## 3. 元素清单

| # | 元素 | 类型 | 文案 | 交互语义 | 层级 | 组件/Token | 状态 |
|---|---|---|---|---|---|---|---|
| GD-01 | 返回 | 链接 | 返回 | Navigation | — | Link | — |
| GD-02 | eyebrow | 文本 | 目标定义 vN | — | — | text-muted | — |
| GD-03 | 主标题 | 文本 h1 | 目标标题 | — | — | text-primary | — |
| GD-04 | 修订目标 | 按钮（Edit3） | 修订目标 | Navigation（→ 编辑器） | Contextual | Button ghost | — |
| GD-05 | 暂停/恢复 | 按钮（Pause/Play） | 暂停 / 恢复 | **Action** | Contextual | Button ghost | LOADING/失败可重试 |
| GD-06 | 归档 | 按钮（Archive） | 归档 | **Action**（destructive，需确认） | Contextual | Button ghost | 归档后提示「目标已归档，可复制为新目标。」 |
| GD-07 | 复制为新目标 | 按钮（Copy） | 复制为新目标 | Navigation | Contextual | Button ghost | — |
| GD-08 | 事实网格 | 文本 | 目标能力 / 应用场景 / 每周预算 / 截止时间 | StatusFeedback | — | Fact list | MISSING 显示「未设置」 |
| GD-09 | 成功标准 | 内容 | 成功标准列表 | InteractiveContent | — | List | — |
| GD-10 | 达成证据 | 状态区 | 评分绑定当前目标、资料、rubric 和 policy；低置信、评分分歧或模型失败只进入复核/失败状态。 | StatusFeedback | — | 文本 | 诚实 |
| GD-11 | 验证任务状态 | 状态标签 | 等待延迟验证 / 可以作答 / 评分已接纳 / 等待复核 / 评分服务失败 / 已取消；确定性评分 / 开放题双重评分 | StatusFeedback | — | Badge | 不伪装 READY |
| GD-12 | 你的独立回答 | 输入 | label「你的独立回答」 | Control | — | Textarea | DEFAULT/DISABLED(未到验证点) |
| GD-13 | 安排成功标准验证 | 按钮 | 安排成功标准验证 | **Action** | Secondary | Button secondary | LOADING |
| GD-14 | 提交验证 | 按钮 | 提交验证 | **Action** | Secondary | Button secondary | DISABLED(空)/LOADING |
| GD-15 | 检查达成门禁 | 按钮 | 检查达成门禁 | **Action** | Secondary | Button secondary | LOADING |
| GD-16 | 由我确认目标达成 | 按钮 | 由我确认目标达成 | **Action**（最终确认权在用户） | Primary（达成路径） | Button primary | DISABLED(门禁未满足)/LOADING |
| GD-17 | 门禁提示 | 文本 | 证据门禁已满足，请由你最终确认达成。/ 仍有成功标准或独立验证义务未满足。 | StatusFeedback | — | 文本 | 按门禁状态 |

## 4. 状态矩阵

| 区域 | LOADING | EMPTY | READY | PARTIAL | STALE | ERROR |
|---|---|---|---|---|---|---|
| 详情加载 | 正在读取目标… | — | 目标定义 | — | 已归档提示 | 目标详情暂时无法读取。+ 重试 |
| 验证提交 | 提交 LOADING | — | 回答已提交。系统失败或低置信不会记作学习失败。 | — | — | 回答提交失败，可稍后重试。 |
| 达成确认 | 确认 LOADING | — | 目标已由你确认达成。该状态不等于一般化 mastery 或真人学习效果证明。 | — | — | 达成确认失败，请重新评估证据。 |
| 证据评估 | 评估 LOADING | — | 门禁判定 | — | — | 证据评估失败。 |

## 5. 无障碍

| # | 要求 |
|---|---|
| A-01 | 验证输入有 label；提交 single-flight、`aria-busy`。 |
| A-02 | 归档等 destructive 动作需确认并保语义（`UI-DS-COMP-004`）。 |
| A-03 | 状态非仅颜色；门禁提示 `role="status"`。 |

## 6. 禁止事项

- 系统不得自行宣布目标达成；最终确认权归用户（现状「由我确认目标达成」正确）。
- 「达成」不等于 mastery/学习效果证明（现状声明保留）。
- 不暴露评分 rubric、内部 id 或算法细节给普通 UI。
- 由导航/route 变化自动触发验证/确认（`UI-ROUTE-005`）。

# 目标编辑器（`/learning/goals/new`、`/drafts/:id`、`/:id/edit`，上下文任务流）

> **页面职责**：明确的「创建/修订可测学习目标」任务流——定义能力、选择资料、生成成功标准、确认学习重点、审阅计划影响后启用。仅作为兼容/上下文 task flow 进入（`UI-ROUTE-004`）。
> **对应契约**：`UI-ROUTE-004`、`INT-MAP-003`、`UI-DS-COMP-050/060`、`UI-DATA-003`
> **现状基准**：`apps/frontend/src/pages/GoalEditor.jsx`（已中文、验证语义诚实）

---

## 1. 页面目标

1. 引导用户定义**可测**目标（拒绝「了解/熟悉/看完」等不可测表述）。
2. 选择资料并生成成功标准；来源可用性诚实（可存草稿 vs 暂不能确认）。
3. 审阅「目标与计划影响」预览后启用（立即生效 / 当前活动完成后切换）。

**不做什么**：不在核心旅程出现；不暴露内部计划算法；`eyebrow` 移除内部编号「P1-01」。

## 2. 布局区划

```
┌──────────────────────────────────────────────┐
│ [返回目标]  eyebrow「目标定义」+ h1 创建/编辑标题      │
├──────────────────────────────────────────────┤
│ 1) 定义你要获得的能力：目标名称/学习主题/目标能力/应用场景    │
│    截止日期/每周预算 [生成候选·Sparkles]             │
│ 2) 选择一份或多份资料（checkbox + 来源可用性标签）      │
│ 3) 成功标准（textarea + 证据要求）                  │
│ 4) 学习重点卡片（checkbox）· [确认所选重点]            │
│ 5) 目标与计划影响（preview fact-grid）· [生成变更预览]  │
├──────────────────────────────────────────────┤
│ [保存为草稿]  [确认并启用目标 · primary]  [结束本项并切换(danger)]│
└──────────────────────────────────────────────┘
```

## 3. 元素清单

### 3.1 定义区

| # | 元素 | 类型 | 文案 | 交互语义 | 层级 | 组件/Token | 状态 |
|---|---|---|---|---|---|---|---|
| GE-01 | 返回 | 链接 | 返回目标 | Navigation | — | Link | — |
| GE-02 | eyebrow | 文本 | 目标定义（移除现状「P1-01 ·」） | — | — | text-muted | — |
| GE-03 | 主标题 | 文本 h1 | 创建学习目标 / 编辑目标草稿 | — | — | text-primary | — |
| GE-04 | 目标名称 | 输入 | label「目标名称」 | Control | — | Input | DEFAULT/ERROR |
| GE-05 | 学习主题 | 输入 | label「学习主题」 | Control | — | Input | DEFAULT/ERROR(必填) |
| GE-06 | 目标能力 | 输入 | label「目标能力（用顿号分隔）」 | Control | — | Input | DEFAULT/ERROR |
| GE-07 | 应用场景 | 输入 | label「应用场景」 | Control | — | Input | DEFAULT |
| GE-08 | 截止日期 | 输入 | label「截止日期」 | Control | — | Input(date) | DEFAULT |
| GE-09 | 每周预算 | 输入 | label「每周预算（分钟）」 | Control | — | Input(number) | DEFAULT |
| GE-10 | 生成候选 | 按钮（Sparkles） | 生成候选 | **Action**（生成能力/成功标准候选） | Secondary | Button secondary | LOADING「正在生成…」 |

### 3.2 资料 / 成功标准 / 学习重点

| # | 元素 | 类型 | 文案 | 交互语义 | 层级 | 组件/Token | 状态 |
|---|---|---|---|---|---|---|---|
| GE-11 | 资料选择 | checkbox 组 | 选择一份或多份资料 | Selection | — | Checkbox（`UI-DS-COMP-060`） | SELECTED/disabled |
| GE-12 | 来源可用性标签 | 状态标签 | 可用于目标 / 可存草稿，暂不能确认 / 尚无已发布知识，暂不能确认 / 已归档 / 不可用于新目标 | StatusFeedback | — | Badge | 文本+语义 |
| GE-13 | 成功标准 | 输入 | label「成功标准」+ 证据要求：… | Control | — | Textarea | DEFAULT/ERROR |
| GE-14 | 可测性提示 | 文本 | 生成后可以逐条修改；含「了解、熟悉、看完」等不可测表述时无法确认。 | StatusFeedback | — | text-muted | — |
| GE-15 | 学习重点卡片 | checkbox 组 | 名称 / 来源 / 摘要 / 推荐理由 | Selection | — | Card+Checkbox | SELECTED |
| GE-16 | 确认所选重点 | 按钮（Check） | 确认所选重点 | **Action** | Secondary | Button secondary | DISABLED(未勾选)/LOADING |
| GE-17 | 已选计数 | 文本 | N 已选 | — | — | text-muted | — |

### 3.3 计划影响与启用

| # | 元素 | 类型 | 文案 | 交互语义 | 层级 | 组件/Token | 状态 |
|---|---|---|---|---|---|---|---|
| GE-18 | 生成变更预览 | 按钮 | 生成变更预览 | **Action** | Secondary | Button secondary | LOADING |
| GE-19 | 预览事实网格 | 文本 | 资料 / 学习重点 / 计划影响 / 字段变更 | StatusFeedback | — | Fact list | 来自 owner 预览，不推断 |
| GE-20 | 计划切换说明 | 文本 | 创建新 mapping 与新 plan；新计划准备好后旧计划才会 supersede。 | — | — | text-muted | — |
| GE-21 | 保存为草稿 | 按钮 | 保存为草稿 / 保存草稿更改 | **Action** | Secondary | Button secondary | LOADING |
| GE-22 | 确认并启用目标 | 按钮 | 确认并启用目标 / 当前活动完成后切换 | **Action**（Primary） | Primary | Button primary | DISABLED(校验未过)/LOADING |
| GE-23 | 结束本项并切换 | 按钮 | 结束本项并切换 | **Action**（danger） | Contextual | Button danger | 需确认；LOAdING |
| GE-24 | 生效方式 pill | 状态标签 | 立即生效 / 活动边界生效 | StatusFeedback | — | Badge | — |

## 4. 校验与状态文案（`Control` ERROR / `StatusFeedback`）

| 场景 | 文案 |
|---|---|
| 缺主题 | 请先填写学习主题。 |
| 缺资料/成功标准 | 至少选择一份资料并生成一条可测成功标准。 |
| 草稿未确认重点 | 草稿已保存。请明确勾选学习重点。/ 请至少勾选一个学习重点。 |
| 确认成功 | 学习重点已明确确认。 |
| 切换批准 | 变更已批准，将在当前活动正常完成后切换。 |
| 启用失败 | 目标应用失败，请重新预览。 |
| 修订失败 | 无法创建修订草稿。 |
| 资料库为空 | 资料库为空，请先上传资料。 |
| 页面加载 | 正在准备目标编辑器… / 目标编辑器暂时无法读取。+ 重试 |

## 5. 无障碍

| # | 要求 |
|---|---|
| A-01 | 全部输入有真实 label；错误与输入 `aria-describedby` 关联。 |
| A-02 | checkbox 组用 fieldset/legend；选择状态语义化。 |
| A-03 | 「确认并启用」pending single-flight、`aria-busy`。 |
| A-04 | danger 动作需确认；确认弹层 focus 管理与 Escape（`UI-DS-COMP-072`）。 |

## 6. 禁止事项

- 核心旅程不出现目标编辑器（`EXP-IA-003`）。
- 不暴露计划/评估算法；预览只能来自 owner，不得前端重新规划（`UI-DATA-003`）。
- 含不可测表述不得确认启用（现状校验正确）。
- 启用目标不得隐式改写/覆盖当前 plan，需用户审阅影响（现状 preview 正确）。

# 导师工作台（`/quick/:sessionId`，兼容 Tutor 会话）

> **页面职责**：打开**遗留 dialog 兼容会话**（来自旧 Today/History 入口）的只读/续聊工作台。诚实标注为兼容层：兼容会话 ≠ `LearningActivity`，不生成计划或掌握结论。
> **对应旅程**：`EXP-JOURNEY-002` 的兼容分支（恢复既有 session）；`UI-ROUTE-002`（deep-link 兼容）
> **对应契约**：`UI-LRN-003`（compatibility source）、`LEXP-AST-002`（诚实帮助状态）、`UI-ROUTE-004`
> **现状基准**：`apps/frontend/src/pages/TutorWorkspace.jsx`（已中文、已诚实标注兼容、结构合理）

---

## 1. 页面目标

1. 打开兼容会话时明确告知来源（「兼容快速学习」kicker）与记录边界（`UI-LRN-003`）。
2. 允许继续这一轮的兼容对话；计划关联、帮助状态、独立验证等**缺 canonical 数据时显示「当前记录不可用」**，不推断（`LEXP-AST-002`）。
3. 提供返回 Welcome、查看历史的导航；不伪装成 LearningActivity。

**不做什么**：不从前端推断 TeachingAction/证据/掌握（现状已有诚实声明，保留）；不让兼容入口创建第二 transcript truth（`UI-LRN-002`）。

## 2. 布局区划

```
┌──────────────────────────────────────────────┐
│ [返回 · 今天→改为「欢迎」]  eyebrow「只读上下文」+ h1 会话主题 │
│ status pill「兼容快速学习」                        │
├──────────────────────────────────────────────┤
│ 学习状态 h2：来源/计划关联/帮助状态/独立验证（诚实缺失态）     │
├──────────────────────────────────────────────┤
│ 消息流（开放内容，非强制气泡）+ 建议 chips            │
│ Composer [学习输入] + [发送消息]                  │
├──────────────────────────────────────────────┤
│ rail「最近会话」+「查看历史」                        │
└──────────────────────────────────────────────┘
```

## 3. 元素清单

| # | 元素 | 类型 | 文案 | 交互语义 | 层级 | 组件/Token | 状态 |
|---|---|---|---|---|---|---|---|
| TW-01 | 返回 | 按钮 | 欢迎（现状「今天」→ 规划改为「欢迎」，`UI-NAV-001`） | Navigation | — | Button ghost | — |
| TW-02 | eyebrow | 文本 | 只读上下文 | — | — | text-muted | — |
| TW-03 | 主标题 | 文本 h1 | 知识点/主题/科目 /「学习会话」 | — | — | text-primary | — |
| TW-04 | 兼容标记 | 状态标签 | 兼容快速学习 | StatusFeedback | — | Badge | 常驻 |
| TW-05 | 学习状态 | 事实列表 | 来源「兼容会话」· 计划关联「当前不可用」· 帮助状态「当前记录不可用」· 独立验证「当前记录不可用」 | StatusFeedback | — | Fact list | MISSING 态诚实（不转 READY） |
| TW-06 | 边界声明 | 文本 | 这里不会从旧 hint level、strategy 或会话轮数推断 canonical TeachingAction、证据或掌握状态。兼容会话不等于 LearningActivity；不会生成学习计划或掌握结论。 | — | — | text-muted | 常驻 |
| TW-07 | 建议 chips | 按钮组 | 请帮我理解这个知识点 / 给我一道例题 / 我卡住了，给点提示 / 这和我的薄弱点有什么关系？ | Action（request） | Contextual | Chip | 按当前请求语义 |
| TW-08 | Composer | 输入 | label「学习输入」placeholder「写下你的问题或思路…」/「会话已结束」 | Control | — | Composer | DEFAULT/READ_ONLY(会话结束) |
| TW-09 | 发送消息 | 按钮 | 发送消息（Send icon） | **Action** | Primary | Button secondary | DISABLED(空/会话结束)/LOADING |
| TW-10 | 会话状态 | 状态标签 | 进行中 / 只读历史 | StatusFeedback | — | Badge | 按 session status |
| TW-11 | 最近会话 | 列表 | 最近会话 rows | Navigation | — | Row | LOADING/EMPTY/READY |
| TW-12 | 查看历史 | 链接 | 查看历史（→ `/learning/history`） | Navigation | Secondary | Link | — |
| TW-13 | 历史只读提示 | 文本 | 该会话已结束，仅可查看历史内容。 | StatusFeedback | — | text-muted | 会话结束后 |

## 4. 状态矩阵

| 区域 | LOADING | EMPTY | READY | PARTIAL | STALE | ERROR |
|---|---|---|---|---|---|---|
| 工作台加载 | 正在打开学习工作台… | 空态「输入你的问题或想法，开始这一轮兼容学习。」 | 消息流 | — | — | 404「这个兼容会话不存在或已经被删除。」/403「你无权访问这个会话。」/「工作台暂时无法读取，请检查后端服务。」 |
| 回应 | Askora 正在回应… | — | 消息 | 部分可用（仅本机） | — | 消息发送失败，可重试 |
| 状态面板 | 加载 | — | 来源「兼容会话」 | 帮助/验证「当前记录不可用」 | — | — |

## 5. 无障碍

| # | 要求 |
|---|---|
| A-01 | Composer label 完整；icon-only 发送有 accessible name。 |
| A-02 | 兼容标记与状态非仅颜色；帮助/验证缺失态有文本表达。 |
| A-03 | 消息顺序可读（`UI-LRN-021`）；stream 不逐 token 播报。 |
| A-04 | 返回/查看历史键盘可达。 |

## 6. 禁止事项

- 「今天」称谓 → 规划改为「欢迎」（`UI-NAV-001`：Today 非 L0）。
- 不推断 canonical TeachingAction / 证据 / 掌握（现状声明保留）。
- 兼容入口不创建/复制第二 Activity/transcript truth（`UI-LRN-002/003`）。
- 会话结束仍允许发送；`BIZ-0003` 类提示用「该会话已结束，仅可查看」而非鼓励新开无限 chat。
- 不把兼容会话包装成 LearningActivity 或生成计划/掌握结论。

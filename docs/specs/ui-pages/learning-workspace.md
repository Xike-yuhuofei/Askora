# 学习空间 / 空间落地页（`/courses/:workspaceId`）

> **页面职责**：空间级 landing。展示当前空间上下文、可恢复对话列表；主 Action 是**对空间「继续学习」**（新开一段对话）。空空间时诚实呈现还缺资料、还不能开始有依据的学习。
> **对应旅程**：`EXP-JOURNEY-002`（回来继续）、`EXP-JOURNEY-004`（建立/扩充空间）
> **对应契约**：`UI-COURSE-003/004`、`UI-SHELL-001~004`、`UI-NAV-003`
> **现状基准**：`apps/frontend/src/pages/LearningWorkspace.jsx`（已中文、已空间语义、空态诚实）

---

## 1. 页面目标

1. 进入空间即明确：**当前在哪个空间**（与 Sidebar/右侧栏解析同一 current Workspace，`UI-SHELL-001`）。
2. 有可恢复对话 → 打开它们是 **Navigation**（不复制 transcript/Activity，`UI-COURSE-004`）。
3. 主 Action = **继续学习**：必须调用 `StartLearningActivityV1` 新开对话，不得前端自建（`UI-COURSE-003`、`UI-LEARN-001`）。
4. 空空间诚实：可加资料，但现在还不能开始有依据的学习（`EXP-JOURNEY-004`）。

**不做什么**：不做成空间管理 Dashboard；不常驻 Goal/Plan/Progress/History 导航（`UI-NAV-003`）；无对话时不生成假对话。

## 2. 布局区划

```
┌──────────────────────────────────────────────┐
│ eyebrow「空间」+ h1 空间 + 右侧当前空间名/「还没有当前空间」│
├──────────────────────────────────────────────┤
│ [继续学习 · primary]                           │
│   说明：在该空间新开一段对话，继承学习进度           │
├──────────────────────────────────────────────┤
│ h2 打开一段已有对话（可恢复对话 rows，Navigation）   │
│   · 对话标题（学习语义，非 Chat 1/2/3）            │
│   · 进行中 / 可开始 状态                         │
├──────────────────────────────────────────────┤
│ 空空间提示（无对话且无资料时）                     │
└──────────────────────────────────────────────┘
真正三栏学习画布（中央 Learn + 右栏 Notes/Material）见学习活动/对话页。
```

## 3. 元素清单

| # | 元素 | 类型 | 文案 | 交互语义 | 层级 | 组件/Token | 状态 |
|---|---|---|---|---|---|---|---|
| LW-01 | eyebrow | 文本 | 空间 | — | — | text-muted | — |
| LW-02 | 主标题 | 文本 h1 | 空间 | — | — | text-primary | — |
| LW-03 | 当前空间名 | 文本 | 空间名 /「还没有当前空间」 | StatusFeedback | — | text-secondary | LOADING「加载中…」/EMPTY/READY/PARTIAL「部分信息可用」/STALE「信息可能已过期」 |
| LW-04 | 继续学习 | 按钮 | 继续学习 / 继续中「正在继续…」 | **Action**（新开对话，`UI-COURSE-003` Primary） | Primary | Button primary | DEFAULT/DISABLED(无可启动活动并说明)/LOADING |
| LW-05 | 继续学习说明 | 文本 | 在该空间新开一段对话，接续学习进度。 | — | — | text-muted | — |
| LW-06 | 区域标题 | 文本 h2 | 打开一段已有对话 | — | — | text-primary | — |
| LW-07 | 对话行 | row | 对话标题（学习语义）+ 状态（进行中 / 可开始） | Navigation/InteractiveContent | — | Row（`UI-DS-COMP-020/024`） | DEFAULT/HOVER/FOCUS |
| LW-08 | 对话列表加载 | 状态 | 正在读取对话… | StatusFeedback(LOADING) | — | 骨架 | LOADING |
| LW-09 | 对话空态 | 文本/Alert | 当前没有可恢复的对话 +「对空间继续学习需要可启动的活动，本页不会自行开聊。」 | StatusFeedback(EMPTY) | — | Alert | EMPTY |
| LW-10 | 对话列表错误 | Alert | 对话列表暂时无法读取 +「不会从前端生成占位对话。」 | StatusFeedback(ERROR) | — | Alert tone=error | ERROR |
| LW-11 | 空空间提示 | 文本 | 这是一个空空间。可以加入资料，但现在还不能开始有依据的学习。打开此页不会创建对话。 | StatusFeedback(EMPTY) | — | Empty pattern | 无资料+无对话 |
| LW-12 | 继续学习失败 | 文本 | 继续学习失败，不会从前端创建对话。 | StatusFeedback(ERROR) | — | Alert tone=error | Action 失败 |

## 4. 状态矩阵

| 区域 | LOADING | EMPTY | READY | PARTIAL | STALE | ERROR |
|---|---|---|---|---|---|---|
| 当前空间 | 加载中… | 还没有当前空间 | 空间名 | 部分信息可用 | 信息可能已过期 | 暂时不可用 |
| 对话列表 | 正在读取对话… | 没有可恢复对话 | 对话 rows | — | — | 对话列表暂时无法读取 |
| 继续学习 | 按钮 LOADING | — | 新开对话成功 | — | — | 继续学习失败；不生成假对话 |

## 5. 无障碍

| # | 要求 |
|---|---|
| A-01 | 对话行是独立 focus target；「继续学习」按钮独立，两者语义不混（`UI-DS-COMP-021`）。 |
| A-02 | 对话状态（进行中/可开始）有文本表达，非仅颜色。 |
| A-03 | 切换空间后重新解析；focus 落到空间 h1 或语义起点。 |
| A-04 | 空态/错误 Alert `role="alert"`（错误时）。 |

## 6. 禁止事项

- 不常驻 Goal/Plan/Progress/History 管理（`UI-NAV-003`）；无 Today 替代 Dashboard（`UI-NAV-001`）。
- 打开已有对话不得复制 Activity/Session/transcript（`LEXP-CONT-001`）；「继续学习」必须新开（`EXP-WSP-005`）。
- 无可启动活动时不得前端自建对话/Session/Goal（`UI-LEARN-001`）。
- 空空间不编造资料/目标；不自动开聊（`EXP-JOURNEY-004`）。
- 对话标题不用 Chat 1/2/3，不用轮次计数（`UI-LRN-005`）。

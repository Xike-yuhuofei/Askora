# 欢迎页（`/`、`/welcome`）

> **页面职责**：打开 App 的默认目的地。回答「我打开 Askora 后先到哪里」——上传资料、选择空间并「继续学习」、看到已有对话入口。
> **对应旅程**：`EXP-JOURNEY-001`（用资料开始学习）、`EXP-JOURNEY-002`（回来继续）
> **对应契约**：`UI-WELCOME-001/002`、`UI-COURSE-001`、`UI-COURSE-003`、`UI-NAV-001`
> **现状基准**：`apps/frontend/src/pages/Welcome.jsx`（已中文、已空间中心；「继续学习」行内 Action 与「前往设置」入口已实现）

---

## 1. 页面目标

1. 用户一到就明白：这是个人本地学习工具，入口是**上传资料**或**打开空间**。
2. 有空间时，能在欢迎页**选空间 → 「继续学习」**（新开一段对话，`EXP-JOURNEY-002`）。
3. 首次使用只呈现用户必须理解的步骤：数据边界说明、模型状态、资料、空间。不出现目标/计划管理。

**不做什么**：不自动进入上一段对话；不自动创建空间/对话/Session；不确认学习目标；不做成 Dashboard。

## 2. 布局区划

```
┌──────────────────────────────────────────────┐
│ 顶部：eyebrow「欢迎」 + h1「从这里开始」 + 一句引导      │
├──────────────────────────────────────────────┤
│ [数据与模型说明]（首次未确认时）                        │
│ [模型尚未就绪]（模型不可用时）                         │
├──────────────────────────────────────────────┤
│ 开始区： [上传资料·primary]  [新建空间·secondary]       │
│         辅助说明「上传只会保存资料…」                    │
├──────────────────────────────────────────────┤
│ 空间区：h2「空间」                                  │
│   · 空：还没有空间 + 可做动作                         │
│   · 列表：空间行 = 名称 + 「继续学习」+「打开空间」        │
└──────────────────────────────────────────────┘
「已有对话」列表由 Sidebar（Left = Where）承担，见 sidebar.md。
```

## 3. 元素清单

### 3.1 顶部标题区

| # | 元素 | 类型 | 文案 | 交互语义 | 层级 | 组件/Token | 状态 |
|---|---|---|---|---|---|---|---|
| W-01 | eyebrow | 文本 | 欢迎 | — | — | text-muted | — |
| W-02 | 主标题 | 文本 h1 | 从这里开始 | — | — | text-primary | — |
| W-03 | 引导句 | 文本 | 上传资料，或打开一个空间。不会自动进入上一段对话，也不会确认学习目标。 | — | — | text-secondary | — |

### 3.2 首次使用 / 状态提示区

| # | 元素 | 类型 | 文案 | 交互语义 | 层级 | 组件/Token | 状态 |
|---|---|---|---|---|---|---|---|
| W-10 | 数据与模型说明 | 文本块 | 标题「数据与模型说明」+ 正文「学习记录与模型调用只保存在本机；不会上传到任何服务端账户。」 | StatusFeedback | — | surface + Alert | 仅首次未确认时显示 |
| W-11 | 我已了解 | 按钮 | 我已了解 / 确认中「正在确认…」 | Action（acknowledge） | Secondary | Button secondary | DISABLED(确认中)/DEFAULT |
| W-12 | 模型未就绪 | 提示条 | 标题「模型尚未就绪」+ 正文「可以先建空间或导入资料。开始有依据的学习前，需要在设置里配置并验证模型。」 | StatusFeedback | — | Alert tone=warning | 模型未就绪时显示；附「前往设置」入口 |
| W-13 | 前往设置 | 按钮 | 前往设置 | Navigation | Contextual | Button secondary | — |

> 说明：`W-12` 与 `W-13` 已同组实现（`.welcome-model`），模型未就绪的反馈可行动（`INT-STATE-003 Failure Is Actionable`）。

### 3.3 开始区

| # | 元素 | 类型 | 文案 | 交互语义 | 层级 | 组件/Token | 状态 |
|---|---|---|---|---|---|---|---|
| W-20 | 上传资料 | 按钮（brand） | 上传资料 | Navigation（进入 Library 上传路径；只创建 Material） | Primary | Button primary/brand | LOADING/DEFAULT |
| W-21 | 新建空间 | 按钮 | 新建空间 | Navigation（进入创建流程，无业务副作用） | Secondary | Button secondary | DEFAULT |
| W-22 | 辅助说明 | 文本 | 上传只会保存资料，不会自动创建空间或对话。 | — | — | text-muted | — |

### 3.4 空间区

| # | 元素 | 类型 | 文案 | 交互语义 | 层级 | 组件/Token | 状态 |
|---|---|---|---|---|---|---|---|
| W-30 | 区域标题 | 文本 h2 | 空间 | — | — | text-primary | — |
| W-31 | 空间行（主点击） | row | 空间显示名 | Navigation（进入空间 landing `/courses/:workspaceId`） | InteractiveContent | Row（`UI-DS-COMP-020/023`） | DEFAULT/HOVER/FOCUS |
| W-32 | 继续学习 | 按钮 | 继续学习 | **Action**（新开对话，`UI-COURSE-003` Primary） | Primary（行内） | Button secondary | LOADING/DISABLED(无模型时说明)/DEFAULT |
| W-33 | 打开空间 | 文本/行尾 | 打开空间 | Navigation | Secondary | Row trailing | — |
| W-34 | 空间空态 | 文本 | 还没有空间。可以先上传资料，或新建一个空空间。 | StatusFeedback(EMPTY) | — | Empty pattern | EMPTY |

> **现状**：空间行为「主点击打开空间（`welcome-space-row`）+ 行尾独立「继续学习」Action（`welcome-space-continue`）」，均为独立 focus target，主点击语义不混淆（`UI-DS-COMP-021`）。

## 4. 状态矩阵

| 区域 | LOADING | EMPTY | READY | PARTIAL | STALE | ERROR |
|---|---|---|---|---|---|---|
| 页面整体 | 骨架 + Loader2 + 文案「正在读取空间与对话…」 | — | 正常渲染 | 空间就绪但 journey 读取失败：仍渲染空间区，忽略说明块 | — | 「无法读取空间列表」+ [重新尝试] |
| 开始区 | 按钮 LOADING（若受模型门控） | — | 可用 | — | — | 随页面错误 |
| 空间区 | 随页面 loading | 空态 W-34 | 空间行 | — | — | 随页面错误 |

错误文案三要素（`INT-STATE-003`）：发生了什么（如「无法读取空间列表」）→ 数据是否安全（本地数据不受影响）→ 现在能做什么（重新尝试 / 去资料库）。

## 5. 无障碍

| # | 要求 |
|---|---|
| A-01 | 页面 h1 唯一语义标题；区域用 `aria-labelledby` 关联 h2（空间区）。 |
| A-02 | 空间行整行可点：主点击区「打开空间」有独立 focus target；「继续学习」按钮是独立 focus target（`UI-DS-COMP-021/022`，不依赖 hover）。 |
| A-03 | Loader2 是装饰性 spinner，配对 `role="status"` 文字「正在读取空间与对话…」；announcement 用 `aria-live="polite"`。 |
| A-04 | 错误区 `role="alert"`；重试按钮可达。 |
| A-05 | 「数据与模型说明」按钮 focus 状态清晰；确认成功有 live 反馈「已确认数据与模型说明」。 |
| A-06 | 键盘路径：Tab 顺序 = 顶部标题 → 提示区 → 开始区 → 空间区；focus 不丢失。 |

## 6. 禁止事项

- 不自动 resume 上一段对话、不自动创建对话/Session（`LEXP-CONT-003`）。
- 不出现 Goal/Plan/Progress 管理、Today 语义、工程阶段展示。
- 「上传资料」不因模型未就绪而禁用——本机解析始终可用（`EXP-PARSE-001`）。
- 不用 localStorage 冒充模型/空间 readiness（`UI-WELCOME-002`）。
- 空间空态不生成默认空间/示例数据（`UI-COURSE-001`）。

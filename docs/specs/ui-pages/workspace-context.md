# 空间上下文（`WorkspaceContext`，全局 shell 组件）

> **页面职责**：向全局 shell（标题栏/右侧 rail/空态）提供「当前空间」的来源、状态与标签。空间加载失败、缺失、过期均诚实呈现。
> **对应契约**：`EXP-IA-001`、`UI-SHELL-001~005`、`INT-STATE-001~003`
> **现状基准**：`apps/frontend/src/components/WorkspaceContext.jsx`（侧边栏呈现为 TraeWork row 语义：分组标签「当前空间」+ 单行水平 `ds-nav-row`，状态 meta/重试行尾右对齐）

---

## 1. 页面目标

1. 全局可见的当前空间身份与状态（LOADING/EMPTY/UNAVAILABLE/PARTIAL/STALE）。
2. 空间不可用时，壳层动作（学习、上传、新建）降级为诚实 disabled 或跳转可用页。
3. 「部分信息可用」「信息可能已过期」等状态不伪装 READY。

**不做什么**：不隐藏失败原因；不把无空间当成已加载。

## 2. 布局区划

```
标题栏（壳层）：[返回]  label「当前空间」+ 空间标题 + 状态 pill
右侧 rail / 空态：使用空间状态做诚实降级
```

## 3. 元素清单

| # | 元素 | 类型 | 文案 | 交互语义 | 层级 | 组件/Token | 状态 |
|---|---|---|---|---|---|---|---|
| WC-01 | 分组标签 | 文本 | 当前空间 | — | — | label（row 上方分组标签，与「已有对话」同构） | — |
| WC-02 | 空间标题 | 文本（row 主标签） | 空间标题 | Navigation（ready 时链接至空间页） | — | ds-nav-row / text-primary | — |
| WC-03 | 状态 pill | 状态标签 | 加载中… / 暂时不可用 / 尚无可用空间 / 部分信息可用 / 信息可能已过期 | StatusFeedback | — | Badge | 对应状态 |
| WC-04 | 重试 | 按钮（RefreshCw） | 重试 | **Action** | Contextual | Button ghost | ERROR 时 |
| WC-05 | 动作降级 | disabled/跳转 | 上传/学习等按状态降级：无空间→引导新建空间；过期→提示后仍可操作 | StatusFeedback | — | 按钮/链接 | DISABLED/READY |

## 4. 状态矩阵

| 状态 | 标题栏呈现 | 壳层动作 |
|---|---|---|
| LOADING | 加载中… | 动作等待/禁用 |
| EMPTY | 尚无可用空间 | 引导「新建空间」「上传资料」 |
| UNAVAILABLE | 暂时不可用 + 重试 | 动作禁用，诚实说明 |
| PARTIAL | 部分信息可用 | 保留可操作，标注缺失 |
| STALE | 信息可能已过期 | 提示后仍可操作（不自动刷新/丢弃） |

## 5. 无障碍

| # | 要求 |
|---|---|
| A-01 | 状态 pill 有文本（非仅颜色）；加载 `aria-busy`。 |
| A-02 | 重试按钮 reachable；动作降级保留 focus 语义（disabled 需理由）。 |

## 6. 禁止事项

- 无空间/失败时不显示伪造成功或空跑动作（`INT-STATE-001`）。
- 过期信息不自动静默丢弃；不把系统错误当成用户错误（`INT-STATE-002`）。

# Resize Stress Test — Figma Implementation Evidence

> 状态：Research / Supporting，Phase 7 已完成  
> 证据日期：2026-08-12  
> Authority：当前 Figma Auto Layout 实现的压力测试；不是 TraeCode 官方窗口合同，也不是 Askora implementation contract

## 1. 目的与证据边界

本实验回答一个受限问题：

> 当前 `TC-UI-001` Screen / Application Shell 在不同 Frame 尺寸下，现有 Figma Auto Layout 会怎样压缩、裁切和产生 overflow？

它不回答：

- TraeCode 官方支持的 window min/default/max `[U]`；
- TraeCode 真实 panel collapse、resize priority、divider persistence `[U]`；
- 哪个尺寸已经达到可用 UX minimum `[U]`；
- Askora 是否应采用 Desktop IDE Shell。

因此本文使用两层证据语义：

- `[C implementation]`：Figma Plugin API、scenegraph audit 或截图明确证明当前设计文件行为；
- `[U TraeCode behavior]`：仍缺真实应用、多窗口截图或交互录屏，不能外推为官方行为。

## 2. Figma 资产

| Asset | Node | 结果 |
|---|---|---|
| Resize Hypothesis Board | `86:3214` | 1880 × 1140，Vertical Auto Layout，绑定官方 color / spacing / radius variables `[C implementation]` |
| Reference sample | `81:2` → `81:3` | 1717 × 1299；Screen instance 指向 `71:2` `[C implementation]` |
| Horizontal samples | `81:672`、`81:886`、`81:2080`、`81:2508`、`81:2722`、`82:3364`、`82:3792`、`82:4006` | 1024–1600 宽度与 threshold probes `[C implementation]` |
| Vertical samples | `81:2294`、`82:2936`、`82:3150`、`82:3578` | 500–900 高度与 threshold probe `[C implementation]` |

13 个样本 Frame 均只有一个 linked Screen instance，全部指向 Screen Component `71:2`；没有复制或 detach Screen / Shell。

## 3. 当前 Shell 的水平压缩行为

当前组件约束为：

```text
Agent Dock = fixed 775
├── Task Rail = fixed 255
└── Agent Main = fill inside fixed Agent Dock

Workbench = window remainder
├── Editor Column = fixed 642
└── Resource Sidebar = absorbs horizontal compression
```

| Window W | Workbench W | Resource Sidebar W | Scenegraph overflow | 可见结果 |
|---:|---:|---:|---:|---|
| 1717 | 942 | 300 | 0 | Reference geometry |
| 1600 | 825 | 183 | 0 | Resource Sidebar 首先压缩 |
| 1564 | 789 | 147 | 0 | 首个无 overflow threshold；Sidebar 已明显偏窄 |
| 1560 | 785 | 143 | 1 | `theme.css` label 底部约 3px overflow |
| 1508 | 733 | 91 | 4 | Tree Item labels 开始换行 |
| 1500 | 725 | 83 | 5 | Tree readability 失效 |
| 1440 | 665 | 23 | 21 | Resource Sidebar 接近窄条 |
| 1280 | 505 | 1 | 28 | Resource Sidebar 结构性塌缩 |
| 1024 | 249 | 1 | 28 | 固定 Editor Column 被 Workbench clip |

结论：

1. `1564px` 是当前 Figma Shell 的水平 **no-overflow threshold** `[C implementation]`；
2. 它不是 usable UX min：此时 Resource Sidebar 只有 147px `[C implementation]`；
3. 总宽度低于 `775 + 642 = 1417px` 时，Workbench 小于固定 Editor Column，结构进入硬失效 `[C implementation]`；
4. 当前组件没有真实 collapse / priority contract `[C implementation]`，TraeCode 是否这样处理仍为 `[U]`。

## 4. 当前 Shell 的垂直压缩行为

当前主要固定高度为：

```text
Title Bar 40
Status Bar 24
Editor Tab 40
Bottom Panel 330
Change Review 42
Prompt Composer 184
```

| Window H | Editor Content H | Agent Stream H | Scenegraph overflow | 可见结果 |
|---:|---:|---:|---:|---|
| 900 | 466 | 634 | 0 | 两个主滚动区保持完整 |
| 618 | 184 | 352 | 0 | 首个无 overflow threshold |
| 600 | 166 | 334 | 1 | Code block 底部约 18px overflow |
| 500 | 66 | 234 | 4 | Agent footer/evidence 与 code block overflow |

结论：当前 Figma Shell 的垂直 no-overflow threshold 为 `618px` `[C implementation]`。这不证明 TraeCode 的官方最小窗口高度 `[U]`。

## 5. 候选策略，不是结论

### Candidate A — Resource Sidebar collapse

在 Tree 可读性失效前折叠 Resource Sidebar，优先保持 Editor 工作区 `[U]`。

### Candidate B — Agent Dock / Task Rail collapse

先折叠 Task Rail 或整个 Agent Dock，避免 Workbench 低于固定 Editor Column `[U]`。

两者会形成不同的信息优先级和工作流语义。没有真实 collapse 前后证据时，不选择、不冻结，也不制作成声称“官方”的 Prototype。

## 6. Live Audit

Figma Plugin API audit 结果：

| Check | Result |
|---|---|
| Phase 7 authored nodes | 169 |
| Placeholder | 0 |
| Missing sharedPluginData key | 0 |
| Duplicate authored key | 0 |
| Resize sample Frames | 13 |
| Linked Screen instances | 13 / 13 → `71:2` |
| Board layout | Vertical Auto Layout |
| Board text families | Inter only |
| Board variable bindings | official background / border / spacing / radius |

视觉检查覆盖 `1564×1299`、`1440×1299`、`1024×1299`、`1717×618`、`1717×500` 和完整 Resize Hypothesis Board。Board 未发现文本裁切、重叠或残留 placeholder。

## 7. 补证要求

要把 `[U]` 提升为可接受的 TraeCode interaction evidence，至少需要：

1. 同一真实窗口的 3 个宽度与 2 个高度截图；
2. Panel divider 拖拽的开始、过程、结束状态；
3. Resource Sidebar、Task Rail、Agent Dock 的 collapse / expand 前后状态；
4. resize 后 selected / running / review state 是否持久；
5. Status Bar overflow、Tree label、Editor content 的真实处理；
6. display scale / screenshot scale factor。

在上述证据到达前，Figma no-overflow threshold 只用于暴露当前组件约束，不得命名为 `windowMinWidth`、`windowMinHeight` 或 production breakpoint。

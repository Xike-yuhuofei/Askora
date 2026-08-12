# Responsive / Resize Rules

> 状态：Research / Supporting，Figma implementation stress test 已完成  
> 适用范式：Desktop workspace resize，不采用 mobile breakpoint 思维  
> 当前证据：1 张 1717 × 1299 真实截图 + 13 个 Figma linked-instance stress samples；没有真实应用的多窗口截图或录屏

## 1. 已确认与未确认

| 项目 | 结论 | Evidence |
|---|---|---|
| Reference window | 1717 × 1299 image px | `[C screenshot]` |
| 当前四列宽度 | 255 / 520 / 642 / 300 | `[C screenshot]` |
| 当前 Bottom Panel | 330 H，仅在 Editor 下方 | `[C screenshot]` |
| 当前 Status Bar | 21 H screenshot / 24 H official Figma component | `[C screenshot]` / `[C implementation]` |
| Figma horizontal no-overflow threshold | 1564 px | `[C implementation]` |
| Figma vertical no-overflow threshold | 618 px | `[C implementation]` |
| TraeCode window min width/height | Unknown | `[U]` |
| TraeCode 各 panel min/default/max | Unknown | `[U]` |
| divider drag hit area / persistence | Unknown | `[U]` |
| real shrink priority / auto-collapse order | Unknown | `[U]` |
| real content reflow vs horizontal scroll | Unknown | `[U]` |

`[C implementation]` 只说明当前 Figma scenegraph；不能升级为 TraeCode 官方交互事实。

## 2. 当前 Figma 水平约束

```text
Agent Dock = fixed 775
├── Task Rail = fixed 255
└── Agent Main = fill inside fixed Agent Dock

Workbench = window remainder
├── Editor Column = fixed 642
└── Resource Sidebar = absorbs horizontal compression
```

| Window W | Workbench W | Resource Sidebar W | Overflow nodes | 结果 |
|---:|---:|---:|---:|---|
| 1717 | 942 | 300 | 0 | Reference geometry |
| 1600 | 825 | 183 | 0 | Resource Sidebar 首先压缩 |
| 1564 | 789 | 147 | 0 | No-overflow threshold；仍非可用 UX min |
| 1560 | 785 | 143 | 1 | `theme.css` label 底部约 3px overflow |
| 1508 | 733 | 91 | 4 | Tree Item labels 换行 |
| 1500 | 725 | 83 | 5 | Tree readability 失效 |
| 1440 | 665 | 23 | 21 | Resource Sidebar 接近窄条 |
| 1280 | 505 | 1 | 28 | Resource Sidebar 结构性塌缩 |
| 1024 | 249 | 1 | 28 | 固定 Editor Column 被 Workbench clip |

关键边界：

- `1564px` 是几何 no-overflow threshold，不是 usable UX minimum；Sidebar 只有 147px `[C implementation]`；
- 总宽度低于 `775 + 642 = 1417px` 时，Workbench 小于固定 Editor Column，结构进入硬失效 `[C implementation]`；
- 当前组件没有 collapse rule；TraeCode 是否先折叠 Sidebar、Task Rail 或 Agent Dock 仍为 `[U]`。

## 3. 当前 Figma 垂直约束

当前主要固定高度：Title Bar 40、Status Bar 24、Editor Tab 40、Bottom Panel 330、Change Review 42、Prompt Composer 184 `[C implementation]`。

| Window H | Editor Content H | Agent Stream H | Overflow nodes | 结果 |
|---:|---:|---:|---:|---|
| 900 | 466 | 634 | 0 | 两个主滚动区保持完整 |
| 618 | 184 | 352 | 0 | No-overflow threshold |
| 600 | 166 | 334 | 1 | Code block 底部约 18px overflow |
| 500 | 66 | 234 | 4 | Agent footer/evidence 与 code block overflow |

`618px` 只描述当前 Figma 的垂直 no-overflow threshold，不证明 TraeCode 官方最小窗口高度 `[U]`。

## 4. Resize Model Candidates

### Candidate A — Resource Sidebar collapse

在 Tree 可读性失效前折叠 Resource Sidebar，优先保持 Editor 主工作区 `[U]`。

优点：直接消除当前最先出现的压缩点。  
风险：若 Resource Sidebar 是主任务上下文，提前隐藏会改变工作流优先级。

### Candidate B — Agent Dock / Task Rail collapse

先折叠 Task Rail 或整个 Agent Dock，避免 Workbench 低于固定 Editor Column `[U]`。

优点：保护 Editor 与 Resource 共存。  
风险：Agent 是当前截图的主要工作流，隐藏它可能破坏任务连续性。

### 当前选择

不冻结 A 或 B `[U]`。Figma Board 只记录候选与失效点，不用常见 IDE 模式替代真实 TraeCode 证据。

## 5. Panel Constraint Register

| Panel | Screenshot geometry | Current Figma constraint | TraeCode min/default/max | Candidate behavior |
|---|---:|---|---|---|
| Task Rail | 255 W `[C]` | fixed 255 `[C implementation]` | `[U]` | collapse / title truncation `[U]` |
| Agent Main | 520 W `[C]` | fills fixed 775 Agent Dock remainder `[C implementation]` | `[U]` | scroll / reflow `[U]` |
| Editor | 642 W `[C]` | fixed 642 `[C implementation]` | `[U]` | flex or min-clamp `[U]` |
| Resource Sidebar | 300 W `[C]` | absorbs horizontal compression `[C implementation]` | `[U]` | first collapse candidate `[U]` |
| Bottom Panel | 330 H `[C]` | fixed 330 `[C implementation]` | `[U]` | vertical resize / collapse `[U]` |
| Status Bar | 21 H `[C screenshot]` | official 24 `[C implementation]` | `[U]` | priority hide / overflow `[U]` |

当前 Figma 约束是实验实现，不是 production token 或 official resize contract。

## 6. Content Overflow Candidates

| Content | Preferred candidate | Evidence |
|---|---|---|
| Task title | single-line ellipsis；metadata 保持第二行 | `[I]` |
| Tree label | single-line ellipsis + tooltip / reveal | `[I]` |
| Editor tab title | ellipsis；close affordance protected | `[I]` |
| Product Mode | label compression / overflow | `[U]` |
| Markdown Preview | content reflow；code/table horizontal scroll | `[I]` |
| Agent table | column reflow or horizontal scroll | `[I]` |
| Output log | preserve monospaced lines，scroll/wrap preference | `[U]` |
| Status Bar | priority-based hide/overflow | `[I]` |

## 7. Divider Behavior Contract — Unverified

真正的实现合同至少需要：

```text
visual thickness [U]
pointer hit target [U]
hover/focus indicator [U]
drag cursor [U]
keyboard step [U]
min/max clamp [U]
double-click reset [U]
collapse threshold [U]
workspace persistence [U]
screen-reader role/value [U]
```

当前只确认 seam 的位置，不把上述行为提前写入组件实现。

## 8. Figma Experiment Assets

- Resize Hypothesis Board：`86:3214`，1880 × 1140；
- 13 个 Resize sample Frames：1024–1717 宽、500–1299 高；
- 13 / 13 样本均只有一个 linked Screen `71:2` instance；
- Phase 7 audit：169 authored nodes、0 placeholder、0 missing key、0 duplicate key；
- Board 为 Vertical Auto Layout，字体仅 Inter fallback，并绑定官方 background / border / spacing / radius variables。

完整证据见 [Resize Stress Test](15-resize-stress-test.md)。这些 canvas 不代表 TraeCode 的正式 supported window sizes。

## 9. Resize Validation Checklist

- 一级 panel 不重叠，除非真实 evidence 明确 overlay；
- Bottom Panel 不延伸到 Resource Sidebar 下方；
- Status Bar 不侵入 Agent Dock；
- Task List、Agent Stream、Editor、Tree、Output 各自滚动 ownership 明确；
- composer 与关键 review action 在可支持尺寸内不被挤出；
- icon-only state 有 tooltip/focus/accessibility strategy；
- resize 后 selected / running / review state 不丢失；
- 区分 geometry no-overflow threshold 与 usable UX minimum；
- Figma stress test 只能验证当前实现结构，不能代替真实前端 resize 证据。

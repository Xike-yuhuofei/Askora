# Layout System

> 状态：Research / Supporting  
> 测量基线：`TC-UI-001`，1717 × 1299 image pixels  
> 注意：未确认 display scale；以下 `px` 是截图像素，不自动等于 CSS/Figma logical px

## 1. 测量方法

本轮以可见边界、连续背景色、divider、panel chrome 和截图坐标进行近似测量。由于 anti-aliasing、1px border 与取整，主要边界允许 ±1px；文本和内部 padding 允许 ±2px。没有用单一文字 baseline 反推容器尺寸。

## 2. Window 与一级边界

| 区域 | 起点 | 终点 | Observed size | 证据 |
|---|---:|---:|---:|---|
| Window | x=0, y=0 | x=1717, y=1299 | 1717 × 1299 | `[C]` |
| Top Region | y=0 | y≈41 | ≈41 H | `[C]` |
| Task Rail | x=0 | x≈255 | ≈255 W | `[C]` |
| Agent Main | x≈255 | x≈775 | ≈520 W | `[C]` |
| Agent Dock | x=0 | x≈775 | ≈775 W | `[C]` |
| Workbench | x≈775 | x=1717 | ≈942 W | `[C]` |
| Editor Column | x≈775 | x≈1417 | ≈642 W | `[C]` |
| Resource Sidebar | x≈1417 | x=1717 | ≈300 W | `[C]` |
| Bottom Panel | y≈949 | y≈1278；仅 Editor Column | ≈330 H | `[C]` |
| Status Bar | y≈1278 | y=1299；仅 Workbench | ≈21 H | `[C]` |

横向核算：`255 + 520 + 642 + 300 = 1717` `[C]`。这说明主要竖向边界在当前截图中能形成完整分区，但不证明这些数值来自固定 token `[U]`。

## 3. Secondary Measurements

| 元素 | Observed measurement | 证据 | 说明 |
|---|---:|---|---|
| Editor Tab Bar | ≈35 H | `[C]` | y≈41–76 |
| Editor Breadcrumb / View Control Row | ≈41–48 H | `[I]` | 控件和 breadcrumb 可能共享或叠加 chrome |
| Resource Tool Strip | ≈35 H | `[C]` | 与 Editor Tab Bar 顶部大致对齐 |
| Bottom Panel Tab Strip | ≈36–38 H | `[C]` | 含 tabs、filter 与 server selector |
| Task new-action row | ≈38 H | `[C]` | 不含 section label |
| Task item | ≈61–63 H | `[I]` | 两行信息；不同内容可能改变高度 |
| Task item gap | ≈8 H | `[C]` | 多个条目重复 |
| Task Rail outer padding | ≈12 | `[C]` | 左右边缘与卡片之间 |
| Agent content horizontal padding | ≈16 | `[I]` | 主要内容块重复对齐 |
| Editor document content inset | ≈72 from editor left | `[I]` | 包含 gutter / menu affordance，不是纯 padding token |
| Panel border/divider | ≈1 | `[C]` image pixel | logical thickness `[U]` |

## 4. Spacing Rhythm

截图中可重复观察到约 8、12、16、24px 的间距组 `[C]`，但同一视觉距离可能同时包含 padding、border 与文字 line box。最小可维护假设是 4px base grid，保留 6px 作为紧凑控件例外 `[I]`：

```text
2  — optical correction / icon micro gap [I]
4  — compact inline gap [I]
6  — dense control padding [I]
8  — standard compact gap [I]
12 — panel inset / card padding [I]
16 — content block spacing [I]
24 — section spacing [I]
32 — large section separation [I]
```

不能从单张截图排除 2px 或 6px 基准系统 `[U]`。下一阶段应通过更多组件的边界采样检查公约数，而不是先建立完整 Spacing Variable collection。

## 5. Panel Size Register

| Panel | Min | Default | Observed at 1717px | Max | Resize behavior |
|---|---:|---:|---:|---:|---|
| Task Rail | `[U]` | `[U]` | 255 `[C]` | `[U]` | `[U]` |
| Agent Main | `[U]` | `[U]` | 520 `[C]` | `[U]` | horizontal drag `[I]` |
| Agent Dock total | `[U]` | `[U]` | 775 `[C]` | `[U]` | 与 Workbench 竞争宽度 `[I]` |
| Editor | `[U]` | fill remaining `[I]` | 642 `[C]` | fill remaining `[I]` | 优先弹性区 `[I]` |
| Resource Sidebar | `[U]` | `[U]` | 300 `[C]` | `[U]` | horizontal drag `[I]` |
| Bottom Panel | `[U]` | `[U]` | 330 H `[C]` | `[U]` | vertical drag `[I]` |
| Status Bar | 21 H `[I]` | 21 H `[I]` | 21 H `[C]` | 21 H `[I]` | 当前看来固定 `[I]` |

`Observed` 列可以用于 Figma reference reconstruction；其余列不得用截图值代填。

## 6. Content Padding 与 Row Height 假设

| Token candidate | Candidate value | 证据 | 用途 |
|---|---:|---|---|
| `layout/panel-inset-compact` | 8 | `[I]` | toolbar / dense rows |
| `layout/panel-inset` | 12 | `[I]` | Task Rail 与 panel content |
| `layout/content-inset` | 16 | `[I]` | Agent content block |
| `layout/row-compact` | 28–32 | `[I]` | tree / toolbar control |
| `layout/row-default` | 36–40 | `[I]` | tabs / panel header |
| `layout/task-row` | 61–63 | `[I]` | 两行 Task List Item |

这些值仍是 candidate，不应在下一阶段直接全部变成 Variables。优先创建最小实验集并与 overlay comparison 对齐。

## 7. Figma Constraint Strategy

| Layer | Width / Height | Auto Layout behavior | 证据 |
|---|---|---|---|
| Window | reference 1717 × 1299 | vertical | `[I]` |
| Body | fill / fill | horizontal | `[I]` |
| Task Rail | 255 at reference | fixed in reference; variable in experiments | `[I]` |
| Agent Main | 520 at reference | fixed in reference; variable in experiments | `[I]` |
| Workbench | fill remaining | vertical | `[I]` |
| Workbench Body | fill / fill | horizontal | `[I]` |
| Editor Column | fill remaining | vertical | `[I]` |
| Resource Sidebar | 300 at reference | fixed in reference; variable in experiments | `[I]` |
| Editor Content | fill / fill | scroll-content wrapper | `[I]` |
| Bottom Panel | fill / 330 at reference | fixed in reference; variable in experiments | `[I]` |
| Status Bar | fill / 21 at reference | horizontal, fixed height | `[I]` |

## 8. Pixel Comparison Plan

1. 在 `01 References` 放置原始 1717 × 1299 图片，保持 100% scale。
2. 在 `05 Application Shell` 建立同尺寸 reference shell，只放容器与 divider。
3. 将 reconstruction 以 50% opacity 叠加或使用 difference visual check。
4. 先修正一级 x/y boundary，再检查 chrome height、row height、padding。
5. 记录每个系统性偏差；若视觉局部值破坏 token consistency，保留系统值并在 `08 Experiments` 留差异说明。
6. 在确认 display scale 前，不把测量结果导出为 CSS px contract。


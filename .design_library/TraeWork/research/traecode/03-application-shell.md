# Application Shell 与 Panel Architecture

> 状态：Research / Supporting  
> 证据：`TC-UI-001` 单张完整窗口截图

## 1. Shell 结论

当前截图最符合“两大一级区域、内部再分 dock”的结构 `[I]`：

```text
Window [C]
├── Top Region [C]
│   ├── Workspace / Window Segment [C]
│   └── Workbench Mode Segment [C]
└── Body [C]
    ├── Agent Dock — 775px observed [C]
    │   ├── Task Rail — 255px observed [C]
    │   └── Agent Main — 520px observed [C]
    └── Workbench — 942px observed [C]
        ├── Workspace Row [C]
        │   ├── Editor — 642px observed [C]
        │   │   ├── Editor Tab / Breadcrumb / Content [C]
        │   │   └── Bottom Panel — 330px observed height [C]
        │   └── Resource Sidebar — 300px observed [C]
        └── Status Bar — 21px observed height [C]
```

这里的 `observed` 只描述 `TC-UI-001`，不等于 default、min 或 max。

## 2. 顶部结构

顶部约 41px 高 `[C]`，但不是单一用途的传统 Title Bar：

- 左侧含 macOS window controls、SOLO 标识与 workspace selector `[C]`；
- Agent Main 上方保留窗口级/任务级动作区域 `[C]`；
- Workbench 上方是 Editor / Browser / Settings / Code Changes 模式切换与窗口动作 `[C]`；
- 顶部各段与下方主要 dock 的 x 边界大致对齐 `[C]`。

因此 Figma 中不应把整个顶部做成不可分割的单层绝对定位画布；应以共享高度、分区内容的 Auto Layout 组合 `[I]`。

## 3. Panel 属性矩阵

| Panel | 当前 Dock | 当前尺寸 | Fixed | Flexible | Resizable | Collapsible | Scrollable | Overlay | 证据说明 |
|---|---|---:|---|---|---|---|---|---|---|
| Task Rail | Left / Agent Dock | 255px W `[C]` | 当前宽度 `[C]` | `[U]` | `[U]` | `[U]` | `[I]` | 否 `[C]` | 任务列表密度暗示滚动，但无可见 scrollbar |
| Agent Main | Left-center / Agent Dock | 520px W `[C]` | `[U]` | `[I]` | `[I]` | `[U]` | `[I]` | 否 `[C]` | 有明确 divider 与长内容流；拖拽未直接观察 |
| Editor | Center / Workbench | 642px W `[C]` | 否 `[I]` | `[I]` | 由相邻 panel 共同决定 `[I]` | `[U]` | `[I]` | 否 `[C]` | 中心内容通常承担剩余空间，但单图不能确认算法 |
| Resource Sidebar | Right / Workbench | 300px W `[C]` | 当前宽度 `[C]` | `[U]` | `[I]` | `[I]` | `[I]` | 否 `[C]` | 有独立 header/tree/sections；行为仍待录屏 |
| Bottom Panel | Bottom / Editor | 330px H `[C]` | 当前高度 `[C]` | `[U]` | `[I]` | `[I]` | `[I]` | 否 `[C]` | Output 内容区发生裁切；滚动 ownership 与高度变更未直接观察 |
| Status Bar | Bottom / Workbench | 21px H `[C]` | `[I]` | 横向填充 `[C]` | 否 `[I]` | `[U]` | 否 `[I]` | 否 `[C]` | 跨 Editor + Resource Sidebar，不跨 Agent Dock `[C]` |

## 4. Docked 与 Overlay

当前所有主要区域都通过稳定边界占据布局空间 `[C]`，没有 modal、popover、context menu、command palette 或 floating panel 可见 `[C]`。因此：

- 现有主要区域应建模为 Docked Panel `[I]`；
- Overlay layer 的存在与层级 `[U]`；
- 不应从“当前没显示”推断产品不支持 Overlay；
- 下一阶段 Figma Shell 可预留 Overlay Slot，但不能提前定义其尺寸和状态合同 `[I]`。

## 5. Divider 与嵌套关系

可见的主要分隔位置：

| Divider | 坐标/位置 | 当前结论 |
|---|---|---|
| Task Rail / Agent Main | x ≈ 255 | 边界 `[C]`；drag target `[U]` |
| Agent Dock / Workbench | x ≈ 775 | 边界 `[C]`；主 resize seam `[I]` |
| Editor / Resource Sidebar | x ≈ 1417 | 边界 `[C]`；resizable seam `[I]` |
| Editor / Bottom Panel | y ≈ 949，限于 Editor 宽度 | 边界 `[C]`；vertical resize `[I]` |
| Workbench / Status Bar | y ≈ 1278，跨 Workbench | 边界 `[C]`；固定状态区 `[I]` |

Bottom Panel 只嵌套在 Editor 下方，而不是覆盖 Resource Sidebar `[C]`；Status Bar 则位于 Workbench 的共同底部 `[C]`。这是本轮最重要的容器 ownership 结论之一。

## 6. Figma Auto Layout 建议

```text
Window / Vertical [I]
├── TopRegion / Horizontal / fixed observed height [I]
└── Body / Horizontal / fill [I]
    ├── AgentDock / Horizontal [I]
    │   ├── TaskRail / fixed observed width [I]
    │   └── AgentMain / fixed-at-reference, variable-in-experiments [I]
    └── Workbench / Vertical / fill [I]
        ├── WorkbenchBody / Horizontal / fill [I]
        │   ├── EditorColumn / Vertical / fill [I]
        │   │   ├── EditorChrome / hug or fixed token [I]
        │   │   ├── EditorContent / fill [I]
        │   │   └── BottomPanel / fixed-at-reference, variable-in-experiments [I]
        │   └── ResourceSidebar / fixed-at-reference, variable-in-experiments [I]
        └── StatusBar / fixed observed height [I]
```

说明：Figma 的 `fixed-at-reference` 只是重建截图时的约束；Resize Experiments 应为每个候选断点建立独立 Shell Variant 或 interactive component property，不把截图值误命名为 default token。

## 7. Split / Collapse / Expand

| 能力 | 当前证据 | 结论 |
|---|---|---|
| Editor 与 Resource 并排 | 当前画面明确可见 | `[C]` |
| Editor 与 Bottom Panel 上下 split | 当前画面明确可见 | `[C]` |
| 用户拖拽 divider | 未见 pointer / before-after | `[U]` |
| Panel collapse / expand | 存在可能的图标与 panel chrome | 支持能力 `[I]`，具体规则 `[U]` |
| 多 Editor group split | 未见第二 editor group | `[U]` |
| Panel 改 dock 方向 | 未见 | `[U]` |
| Overlay panel | 当前未见 | `[U]` |

## 8. Shell 风险

1. 把 255/520/642/300 当作产品默认值，会把单一窗口快照误写成系统规则。
2. 把 Status Bar 放到全窗口底部，会错误覆盖 Agent Dock 的 Composer 区域。
3. 把 Bottom Panel 作为 Workbench 全宽子层，会错误压缩 Resource Sidebar。
4. 把 Task Rail 误当成普通 Activity Bar，会丢失任务历史的内容密度与状态语义。
5. 直接复制 Desktop IDE Shell 到 Askora，会突破 Askora current Local Web 产品形态和 canonical experience boundary。

## 9. Figma Application Shell 实现状态

当前 Figma Design File 已完成 reference-only Shell Component：

| 节点 | Figma ID | 当前几何 / 状态 | 证据 |
|---|---|---|---|
| Application Shell | `57:6` | 1717 × 1299；0 placeholder | Figma live audit `[C]` |
| Titlebar | `57:239` | 1717 × 40；official instance | Figma live audit `[C]` |
| Agent Dock | `58:46` | 775 × 1259 | Figma live audit `[C]` |
| Task Rail | `58:47` | 255 × 1259 | Figma live audit `[C]` |
| Agent Main | `58:48` | 520 × 1259；Stream + Review + Composer | Figma live audit `[C implementation]` |
| Workbench | `58:49` | 942 × 1259 | Figma live audit `[C]` |
| Editor Column | `58:51` | 642 × 1235 | Figma live audit `[C]` |
| Resource Sidebar | `58:52` | 300 × 1235 | Figma live audit `[C]` |
| Bottom Panel | `59:128` | 642 × 330 | Figma live audit `[C]` |
| Status Bar | `58:268` | 942 × 24；只跨 Workbench | official component geometry `[C]` |

截图中 Status Bar 约 21 image px `[C]`，而 Figma 使用官方 `Status Bar` component 的 24px 几何 `[C official]`。这是明确记录的 system-consistency exception，不应反向把截图测量改写为 24px，也不应把 Figma 的 24px 声称为应用运行时已验证值。

Shell audit：212 个节点、61 个 linked instances、0 个 placeholder、0 个失联 instance、171 个 variable-bound nodes；关键结构容器全部使用 Auto Layout `[C]`。Agent Main 中的完成态、待审阅和 Composer 布局与截图状态一致 `[C]`，但内部示例总结文案与验证块只用于 reference composition `[I]`。

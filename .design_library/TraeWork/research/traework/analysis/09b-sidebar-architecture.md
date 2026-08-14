# 09b — Sidebar Architecture（本轮重点）

**Phase**: 1 · **Generated**: 2026-08-12
**Evidence**: 主截图几何测量 [S] + dev-explorer [L] + task-tree contract [L]

---

## Sidebar 分区拆解

```
Sidebar (301px × 1299px, bg #f5f5f5)
├── Window Controls          y≈0..40   traffic lights (红35/黄55/绿75)
├── Global Controls (搜索)    y≈64..95  bg #e6e6e6 ≈ bg-base-tertiary
├── Mode Switcher            y≈116..149 (Work/Code/Design)
├── Primary Actions          14px 行 ×4+ (新建任务/插件市场/自动化/办公助理/模板库)
├── Pinned                   14px 行
├── Workspace Navigation     可展开分组
├── Task List                Workspace → Project → Task
└── Account                  y≈1259..1282 (h24 用户行)
```

## 行为特性分析

| 特性 | 判定 | Evidence |
|---|---|---|
| Fixed | 是（截图固定 301px 列） | [C][S] |
| Scrollable | 是（中间内容区滚动，account 固定底部） | [I][L] dev-explorer .content scroll |
| Resizable | **未知** | [U] 单张截图无法确认；无拖拽证据 |
| Collapsible | **未知** | [U] 无折叠证据（shell 有 left 折叠 48px，但那是三栏 shell） |
| Sticky | Window controls / account 疑似 sticky | [I] |
| Section Collapse | 疑似（Workspace 分组可折叠） | [I][L] task-tree expanded/collapsed |
| Tree Expand | 是（task-tree 三级展开） | [C][L] |

## 行高测量

- 实测文本行高 14px，行距约 40px（y=166/206/246/286...）[S]
- 但 14px 可能是文字部分；整行高度可能 28~40px。[I]
- dev-explorer 参考：quick-actions 行 34px；task-row 约 34px；user-row 56px。[L]
- task-tree contract：item-height 28px、group-title-height 24px。[L]

## Sidebar 宽度

| 项 | 值 | Evidence |
|---|---|---|
| Observed Width | **301 px** | [C][S] |
| Default Width | 未知（需多窗口尺寸确认） | [U] |
| Min Width | 未知 | [U] |
| Max Width | 未知 | [U] |
| Resize Rule | 未知（无拖拽证据） | [U] |

> ⚠️ 只将 Observed Width 标记为 Confirmed，不视为 Default Width。[文档第十九节要求]

## 与 dev-explorer 差异

dev-explorer 的 task-list-panel 为 300px + 56px user-row + 64px topbar + mode-switch，与截图 Sidebar 结构高度一致，但**宽度设定（300px）与实测（301px）接近但不相等**，不能直接套用。[I]

## 结论

1. [C][S] Sidebar 为固定宽 301px 列，bg-base-secondary。
2. [C][L] Sidebar 内部是分区结构：Window/Mode/Navigation/Task/Account。
3. [C][L] 任务树三级（Workspace→Project→Task），item 28px。
4. [U] Resizable / Collapsible / Default Width 均无证据，Phase 1 保持 Unknown。
5. [I] Account 固定底部，内容区滚动（参考 dev-explorer）。

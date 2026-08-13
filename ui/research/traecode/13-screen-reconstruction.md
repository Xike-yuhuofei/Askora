# Screen Reconstruction — TC-UI-001

> 状态：Research / Supporting  
> Figma Page：`06 Screens` (`1:7`)  
> Authority：single-screenshot reconstruction；不是 Askora Canonical Design 或 TraeCode 完整交互合同

## 1. 结果

| 资产 | Node ID | 结果 |
|---|---|---|
| Screen Component | `71:2` | `TraeCode RE / Screen / TC-UI-001 / Completed Review`，1717 × 1299 |
| Linked Shell | `71:3` | `57:6` 的 instance；Screen 的唯一直接子节点 |
| Reconstruction Board | `73:458` | 1880 × 1935；Header、并排对照、Overlay、Known Deviations |
| Side-by-side | `74:458` | Reference 与 Reconstruction 均为 858.5 × 649.5（50%） |
| Overlay | `75:673` | linked reconstruction + 50% opacity reference |
| Deviations | `77:882` | 证据边界与 system-consistency exception |

Screen 没有复制或 detach Application Shell；完整复用链为：

```text
TC-UI-001 Screen Component 71:2
└── Application Shell Instance 71:3
    └── Main Component 57:6
```

Board 中的两个 reconstruction 视图继续指向 Screen Component `71:2`，而不是重建独立 Shell。

## 2. Evidence Boundary

- `[C]` 原始图片尺寸为 1717 × 1299；当前一级 panel 组合与主要分割来自截图测量。
- `[C]` Reference 图层复用 `14:289` 的 imageHash `3253b47b8a2fcbecc55d489684fce171336bed51`。
- `[C]` Status Bar 在截图中约为 21px；Figma Screen 采用官方 24px component。
- `[I]` Agent 结果文案、代码和终端内容用于表达结构，不是官方 data/state contract。
- `[U]` Resize、Collapse、Split、Hover、Focus、Error 与完整 Agent lifecycle。

## 3. Validation

| 检查 | 结果 |
|---|---|
| Screen size | 1717 × 1299，PASS |
| Screen direct children | 1 个 Shell instance，PASS |
| Shell main component | `57:6`，PASS |
| Board authored nodes | 29；另有 2 个 instance virtual descendants，PASS |
| Placeholder | 0，PASS |
| Reference imageHash | 两个图层均与 `14:289` 相同，PASS |
| Fonts | Inter fallback + JetBrains Mono，PASS |
| Key containers | Screen、Board、Header、Legend、Comparison、Cards、Overlay、Deviation 均使用 Auto Layout；overlay frame 因图层叠加使用明确绝对定位，PASS |
| Visual QA | full Screen、Board、Header 截图已检查；默认白色结构 fill 问题已修复，PASS |

验证截图：

- `/tmp/traecode-tc-ui-001-screen.png`
- `/tmp/traecode-tc-ui-001-board-fixed.png`
- `/tmp/traecode-tc-ui-001-header.png`

## 4. Known Deviations

1. 重构优先保持官方组件和 token 一致性，不复制截图中的每段业务内容。
2. Reference 与 Reconstruction 的内容密度不同；对照板不构成 pixel-perfect 完成证明。
3. Status Bar 采用官方 24px，而不是截图测得的约 21px；这是已记录的 system-consistency exception。
4. 单截图不能证明跨窗口尺寸和交互状态，相关结论继续保持 `[I]` / `[U]`。

## 5. 下一阶段

`07 Prototype` 已完成 Editor Tab selection A/B 往返验证，`08 Experiments` 已完成明确标记为 Figma implementation evidence 的 Resize stress test。下一步等待真实 resize/collapse、Agent running/error/approval、Context Menu 与 keyboard focus 截图或录屏，不用原型反向制造产品事实。

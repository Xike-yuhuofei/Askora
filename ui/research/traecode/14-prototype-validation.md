# Prototype Validation — Editor Tab Selection

> 状态：Research / Supporting  
> Figma Page：`07 Prototype` (`1:8`)  
> Authority：evidence-backed interaction model probe；不是 TraeCode 真实运行行为证明或 Askora implementation contract

## 1. Prototype Scope

本阶段只验证官方 `Editor Tabs` contract 已定义的 selection state composition：

```text
State A — 79:1227
App.tsx = Active + Icon+Label+Close
styles.css = Default + Icon+Label
        │ click styles.css
        ▼
State B — 79:1441
App.tsx = Default + Icon+Label
styles.css = Active + Icon+Label+Close
        │ click App.tsx
        └──────────────────────► State A
```

两个 frame 都是 `TC-UI-001` Screen Component `71:2` 的 linked instance；没有复制或 detach Shell。

## 2. Figma Assets

| 资产 | Node ID | 说明 |
|---|---|---|
| State A | `79:1227` | Prototype start；App.tsx active |
| State A Screen | `79:1228` | `71:2` linked instance |
| State B | `79:1441` | styles.css active |
| State B Screen | `79:1442` | `71:2` linked instance |
| Evidence Note | `79:1672` | 点击路径、证据来源与 deferred scope |

## 3. Reactions

| Source | Trigger | Destination | Transition |
|---|---|---|---|
| State A / styles.css | `ON_CLICK` | `79:1441` | `null` |
| State B / App.tsx | `ON_CLICK` | `79:1227` | `null` |

Prototype 起点为 `79:1227`，名称为 `Editor Tab Selection / Evidence-backed`。

未使用 Smart Animate 或其他 transition，因为静态合同没有提供 motion timing/easing 证据。

## 4. Validation

| 检查 | 结果 |
|---|---|
| State frames | 2 × 1717 × 1299，PASS |
| Screen linkage | 两个 instance 的 main component 均为 `71:2`，PASS |
| Variant overrides | A/B 的 Active / Default 与 Close anatomy 互换正确，PASS |
| Reactions | 2 条，目的地闭合，PASS |
| Flow start | `79:1227`，PASS |
| Authored nodes | 9，0 missing / duplicate key，PASS |
| Placeholder | 0，PASS |
| Key containers | State A / B 与 Evidence Note 使用 Auto Layout，PASS |
| Visual QA | A/B 全屏与 Evidence Note 截图已检查，PASS |

验证截图：

- `/tmp/traecode-prototype-tab-a.png`
- `/tmp/traecode-prototype-tab-b.png`
- `/tmp/traecode-prototype-note.png`

## 5. Evidence Boundary

- `[C]` 官方 contract 定义 Default / Hover / Active / Active Hover 和 Icon+Label(+Close) anatomy。
- `[C]` 当前 Figma 原型的 variant composition、reaction 与 flow start 已通过 live API audit。
- `[I]` “点击 tab 切换 selection”是由通用 tab semantics 与静态结构共同支持的交互候选。
- `[U]` 真实应用是否保留编辑器内容、如何同步 Resource Sidebar、关闭按钮行为、keyboard order、hover timing 与 motion。
- `[C implementation]` `08 Experiments` 已测得当前 Figma Auto Layout 的 Resize 压缩与失效点；`[U]` TraeCode 真实 Resize、Collapse、Split、Agent Start / Running / Approval / Error、Context Menu / Dropdown / Popover。

## 6. 下一阶段 Gate

在补充真实录屏或连续截图前，不新增 Resize 或 Agent lifecycle prototype。当前允许的无语义扩张工作已经完成：

1. `08 Experiments` 已记录 Resize Candidate A/B，二者保持 `[U]`；
2. 13 个 linked Screen samples 已完成 responsive stress test；
3. 后续只在收集 Pack A / B / C 证据后，把 hypothesis 晋升为 prototype contract。

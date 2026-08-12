# TraeCode Official Button Components

> 状态：Research / Supporting，Phase 10 Figma evidence  
> Source：`TraeCode Copy/components/buttons.json`、`preview/component-buttons.html`、`components.css` 与 bundled SVG icons  
> Authority：TraeCode 外部静态组件合同；不是 Askora Canonical Design System、production state machine 或 accessibility implementation

## 1. 证据结论

官方来源内部存在一处需要显式保留的差异：

- `buttons.json.variantDimensions.intent` 只列出 `brand / primary / ghost / danger` `[C source]`；
- 同一 JSON 的 `domAnatomy`、官方 CSS 与 preview 实际渲染 `Primary / Secondary / Tertiary / Danger Strong / Danger Subtle / Warning / Brand / Link` 共 8 个 intent `[C source]`；
- preview 明确写明 `Eight variants × three sizes × four states` `[C source]`。

Phase 10 采用真实 DOM / CSS / preview 渲染作为 Figma variant truth，同时把 JSON 列表差异保留为 source conflict，不静默合并或删除 intent。

## 2. Figma 资产

### 2.1 Text Button

| Intent | Component Set ID | Variants |
|---|---|---:|
| Primary | `137:5207` | 12 |
| Secondary | `143:1056` | 12 |
| Tertiary | `144:1068` | 12 |
| Danger Strong | `145:1080` | 12 |
| Danger Subtle | `147:1140` | 12 |
| Warning | `148:1200` | 12 |
| Brand | `149:1236` | 12 |
| Link | `151:1260` | 12 |

每个 set 使用相同的变体轴：

```text
Size = SM / MD / LG
State = Default / Hover / Active / Disabled
```

总计 `8 × 3 × 4 = 96` variants `[C implementation]`。非 Link intent 的几何高度为 24 / 28 / 32px；Link 遵循官方 `height:auto; padding:0`，不被强制做成填充按钮高度。

Text Button component property API：

- `Label` — `TEXT`；
- `Leading Icon` / `Trailing Icon` — `BOOLEAN`；
- `Leading Icon Swap` / `Trailing Icon Swap` — `INSTANCE_SWAP`；
- `Size` / `State` — `VARIANT`。

Link 的 3 个 Hover label（`151:1268`、`151:1288`、`151:1308`）均已按官方 CSS 设置 `UNDERLINE`，并继续绑定 `text-default-hover` `[C implementation]`。

### 2.2 Icon Button

| Intent | Component Set ID | Variants | Property API |
|---|---|---:|---|
| Primary | `156:1272` | 12 | `Icon INSTANCE_SWAP` + `Size` + `State` |
| Secondary | `157:5464` | 12 | 同上 |
| Tertiary | `158:5488` | 12 | 同上 |

总计 `3 × 3 × 4 = 36` variants `[C implementation]`。SM / MD / LG 为 24 / 28 / 32px 正方形；图标通过单一 `INSTANCE_SWAP` 暴露，没有为每个 icon 创建 variant。

Phase 10 新增 3 个官方 SVG supporting components：

- Check `134:5149`；
- Trash `134:5156`；
- Alert `134:5161`。

Brand 的 Zap、Secondary 的 Settings 与 Tertiary 的 Close 继续复用已有 linked icon components；没有 detach 或手绘替代图标。

## 3. Token 与状态边界

Figma 组件直接消费 `TraeCode Official / Color Core`、`Spacing`、`Radius` 与官方 UI text style。代表性映射包括：

| Intent / State | Source-backed token relationship |
|---|---|
| Primary Default / Hover / Active | `text-default` / `text-default-hover` / `text-secondary` |
| Secondary Default / Hover / Active | `bg-overlay-l2` / `bg-overlay-l3` / `bg-overlay-l1` |
| Tertiary Default / Hover / Active | transparent / `bg-overlay-l2` / `bg-overlay-l1` |
| Danger Strong | `status-error-default` + brightness state treatment |
| Danger Subtle | `status-error-surface-l1 / l2` |
| Warning | `status-warning-default` + brightness state treatment |
| Brand Default / Hover | `bg-brand` / `bg-brand-hover` |
| Link Default / Hover / Active / Disabled | `text-default` / `text-default-hover` / `text-secondary` / `text-tertiary` |

这些是静态 source-backed representations：

- `[C]` Figma 中存在 Default / Hover / Active / Disabled 四种视觉 variants；
- `[U]` TraeCode runtime 的 pointer、keyboard、focus、loading、spinner、tooltip、transition timing 与 disabled semantics；
- `[U]` 组件是否在当前唯一截图的每个按钮位置使用同一官方 intent；
- Figma 的 `INSTANCE_SWAP` 不提供 runtime accessible name；真实 Icon Button 仍必须有可感知名称。

Askora 正式 Button 必须继续遵守 [Askora Design System](../specs/ui/design-system.md) 的 Action / Control、single-flight loading、accessible name 与状态语义；不得把 TraeCode 四态矩阵直接覆盖为 Askora 的长期状态合同。

## 4. Documentation Board

`03 Components` 中的 `Phase 10 / Buttons` Board `160:1320` 为 1200 × 1248，包含：

1. 8 intent hierarchy；
2. SM / MD / LG 与四个静态 state representatives；
3. Primary / Secondary / Tertiary Icon Button；
4. 由 3 个 linked Secondary Button instances 组成的 Button Group；
5. 每页最多一个 Brand CTA 的官方 composition rule。

Board 共使用 27 个 linked Button instances，其中 Brand instance 恰好 1 个；Board 内无 `COMPONENT` / `COMPONENT_SET` 复制，完成后 `placeholder=false`。

## 5. Live Audit

| Audit | Result |
|---|---:|
| Text Button sets / variants | 8 / 96 |
| Icon Button sets / variants | 3 / 36 |
| Invalid Size / State combinations | 0 |
| Documentation Button samples | 27 linked |
| Documentation Brand samples | 1 |
| Phase 10 real authored nodes | 632 |
| Variable-bound authored nodes | 400 |
| Bound variables | 31，0 missing |
| Placeholder | 0 |
| Missing / duplicate authored `dsb.key` | 0 / 0 |
| Run ID / phase prefix mismatch | 0 / 0 |
| Broken variable aliases | 0 |
| Authored font families | Inter only |

Figma 另返回 258 个 linked-instance 虚拟内部节点（ID 形式为 `I…;…`）。它们继承源组件 metadata，但不是自建 scene roots，因此不写 metadata，也不计入 authored key 重复审计。

## 6. Implementation Handoff

- Text Button 应以 intent 分组或等价可维护 API 暴露 8 个官方 intent，不把 Danger / Warning 当成 hierarchy level；
- `Brand` 是额外品牌强调，每个页面最多一个；普通主操作使用 neutral Primary；
- Icon Button 维持 icon slot + accessible name 的双合同，不能只交付图标；
- Button Group 使用相邻 Secondary Button composition、共享 1px seam 与首尾圆角，不需要独立复制一套按钮视觉；
- runtime 必须单独定义 Focus、Loading、keyboard activation、disabled behavior 与 event semantics；静态 Figma state 不构成这些行为的测试证据。

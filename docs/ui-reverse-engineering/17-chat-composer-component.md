# Official Chat Composer — Figma Component Evidence

> 状态：Research / Supporting，Phase 8 已完成  
> Source：`TraeCode Copy/components/chat-composer.json`、`preview/component-chat-composer.html`、`components.css`、bundled SVG icons  
> Authority：TraeCode official component representation；不是 Agent lifecycle、keyboard 或 Askora interaction contract

## 1. Source-backed Contract

官方合同确认：

- multiline input 位于 toolbar 上方；
- toolbar 左侧为 tools + model chip，右侧为 mic + brand send；
- root 使用 `bg-overlay-l1`、`border-neutral-l2`、`radius-10`、12px padding、8px gap；
- `:focus-within` 使用 `border-brand`；
- tool button 为 32 × 32，send 为 36 × 36，model chip 高 28；
- Empty / Filled 与 Claude / GPT-4o 是官方 variant dimensions；
- disabled send 与 attachment preview 明确为 unknown。

Figma 额外把 CSS `:focus-within` 表示为 `Focus=Default / Focused` 设计变体 `[C source-backed representation]`。它便于视觉评审，不证明真实 focus order 或 runtime behavior。

## 2. Foundations 增量

在既有 `TraeCode Official / Color Core` 中补入：

| Variable | ID | Source value | Scope |
|---|---|---|---|
| `bg-brand-hover` | `VariableID:95:2` | `#0FDC78` | Frame / Shape fill |
| `border-brand` | `VariableID:95:3` | `#32F08C` | Stroke color |

两者保留官方 CSS 名称与 Web code syntax；没有建立 portable alias。

## 3. Bundled SVG Components

新增 8 个 supporting icon components：

| Icon | Component ID | Source |
|---|---|---|
| Plus | `96:100` | `plus.svg` |
| Link | `96:104` | `link.svg` |
| Image | `96:108` | `image.svg` |
| File Text | `96:113` | `file-text.svg` |
| Sparkles | `96:119` | `sparkles.svg` |
| Zap | `96:123` | `zap.svg` |
| Mic | `96:126` | `mic.svg` |
| Send Onbrand | `96:131` | `send.0c0c0d.svg` |

默认 icons 绑定 `icon-default`；Send Onbrand 绑定 `text-onbrand`。没有手绘图标或 detached SVG。

## 4. Component Architecture

```text
Chat Composer Set 99:508
├── Tool Button Set 97:110
│   ├── Default
│   └── Hover
│   └── Icon INSTANCE_SWAP
├── Model Chip Set 98:140
│   ├── Claude / GPT-4o
│   └── Default / Hover
├── Send Button Set 97:119
│   ├── Default
│   └── Hover
└── Composer variants
    ├── Input
    └── Toolbar
        ├── Tools
        └── Actions
```

主 Component Set `99:508`：

| Property | Values |
|---|---|
| `Content` | Empty / Filled |
| `Model` | Claude / GPT-4o |
| `Focus` | Default / Focused |
| `Prompt` | TEXT property |

共 8 个 720 × 124 Vertical Auto Layout variants。`Content` 控制工具 anatomy；`Prompt` 是显式 TEXT property，因此实例切换 Content 时需要由使用者设置实际文案，不能假设 Figma 自动更换 TEXT property default。

## 5. Documentation Board

Board `100:332`：1600 × 606，包含 4 个 linked representative instances：

1. Empty / Claude / Default；
2. Empty / Claude / Focused；
3. Filled / GPT-4o / Default；
4. Filled / GPT-4o / Focused。

Board 使用官方 `bg-base-default` 展示 overlay surface 的真实合成；代表实例已显式设置 Empty placeholder 或 Filled prompt。视觉检查未发现文本裁切、工具行错位、model chip 溢出或默认白色 Auto Layout fill。

## 6. Live Audit

| Check | Result |
|---|---|
| Phase 8 authored nodes | 177 |
| Variable-bound authored nodes | 145 |
| Placeholder | 0 |
| Missing sharedPluginData key | 0 |
| Duplicate authored key | 0 |
| Main Composer variants | 8 |
| Linked nested instances | 44 / 44 |
| Nested component roots | Tool `97:110` / Model `98:140` / Send `97:119` |
| Board representative instances | 4 / 4 linked to `99:508` |
| Phase 8 text families | Inter fallback only |

Figma Library 在该阶段后为：14 Component Sets、80 Component nodes、7 user standalone components、20 supporting standalone components。

## 7. Evidence Boundary

已确认：official anatomy、Empty/Filled、Claude/GPT-4o、default/hover subcomponent visuals、focus-within border、source tokens 与 bundled icons。

仍未知：

- disabled send；
- attachment preview row；
- keyboard submit / line break；
- focus order 与 focus-visible；
- running 时可否编辑或 queue；
- model switch persistence；
- actual Agent state / data owner。

上述未知项不进入 Component Set，也不能由该 Figma 资产反向定义 Askora 的 Prompt Composer 行为。
